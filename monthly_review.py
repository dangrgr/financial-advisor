#!/usr/bin/env python3
"""
Monthly Budget Review Tool

Loads a Rocket Money CSV export, compares actuals to the Balanced Scenario budget,
tracks the annual bonus pool, and outputs a markdown report.

Usage:
    python3 monthly_review.py --month 2026-01 --csv /path/to/transactions.csv
    python3 monthly_review.py --month 2026-01 --csv /path/to/transactions.csv --draw-car-repair
"""

import argparse
import sqlite3
import pandas as pd
import os
from datetime import date

DB_PATH = "budget_analysis.db"
BASE_SALARY_PAYCHECK = 5_400.00  # Expected bi-weekly paycheck (±$5)
BASE_MONTHLY_INCOME = 10_800.00

# ---------------------------------------------------------------------------
# Liquidity configuration — update these when the picture changes materially
# ---------------------------------------------------------------------------

# Emergency fund
EMERGENCY_FUND_TARGET        = 81_690.00   # 6 months at Balanced Scenario
EMERGENCY_BROKERAGE_ALLOC    = 40_000.00   # Brokerage portion designated as emergency backstop (VFIAX/VOO)
EMERGENCY_SAVINGS_FLOOR      = EMERGENCY_FUND_TARGET - EMERGENCY_BROKERAGE_ALLOC  # ~$41,690 in savings

# Brokerage (Vanguard taxable) — update monthly when running review
BROKERAGE_HOLDINGS = {
    'VFIAX': 'Vanguard 500 Index Admiral',
    'VOO':   'Vanguard S&P 500 ETF',
    'GOOGL': 'Alphabet Inc.',
    'VGT':   'Vanguard Info Tech ETF',
    'VMFXX': 'Federal Money Market',
}

# Retirement estimate (not counted in liquidity pool — awareness only)
RETIREMENT_EST = 1_000_000.00

# ---------------------------------------------------------------------------
# Bonus pool — actual 2025 Dec bonus reconciliation
# ---------------------------------------------------------------------------
# Bonus received Dec 19, 2025:              $77,340.57
# Emergency fund transfer to savings:      -$50,000.00
# Operational pool (stayed in checking):    $27,340.57
# Dec bonus spend (parking/SW/mattress):    -$5,767.06
# Pool entering Jan 2026 (opening bal):     $21,573.51

BONUS_RECEIVED        = 77_340.57
SAVINGS_TRANSFER      = 50_000.00   # to emergency fund
POOL_OPENING_2026     = 21_573.51   # after Dec bonus spend

# December bonus spend line items (pre-2026, seeded at init)
DEC_BONUS_SPEND = [
    ('2025-12-03', 'DEN PUBLIC PARKING (early bird parking)',    90.00),
    ('2025-12-10', 'SWA Early Bird upgrade',                     82.00),
    ('2025-12-29', 'Mattress Firm (main purchase)',           5_595.06),
]

# ---------------------------------------------------------------------------
# Transaction classification rules
# ---------------------------------------------------------------------------

# Excluded entirely — not real spending (transfers, business pass-through)
EXCLUDE_CATEGORIES = {
    'Credit Card Payment',
    'Work Expense',
    'Reimbursement',
    'Company Travel',       # business travel, reimbursed
    'Internal Transfers',
}

# Tracked against bonus pool, not monthly budget
BONUS_SPEND_CATEGORIES = {'Bonus Spend'}

# Shown above-the-line as exceptional / one-time items
EXCEPTIONAL_CATEGORIES = {'Unexpected'}

# Income sources (Bonus Income is a pool credit, handled separately)
INCOME_CATEGORIES = {'Income', 'Bonus Income'}

# Categories not in the Balanced Scenario target list — shown as actuals only
UNBUDGETED_CATEGORIES = {
    'Medical', 'Travel & Vacation', 'Fees', 'Taxes', 'Legal',
    'Cash & Checks', 'Kids Activities',
}


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def setup_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bonus_pool_ledger (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date      TEXT,
            month           TEXT,
            description     TEXT,
            category        TEXT,
            amount          REAL,
            running_balance REAL,
            status          TEXT DEFAULT 'confirmed'
        );

        CREATE TABLE IF NOT EXISTS monthly_actuals_2026 (
            month           TEXT,
            category        TEXT,
            actual_amount   REAL,
            budget_target   REAL,
            variance        REAL,
            variance_pct    REAL,
            PRIMARY KEY (month, category)
        );

        -- Static liquidity configuration (emergency fund split, retirement est, etc.)
        CREATE TABLE IF NOT EXISTS pool_config (
            key         TEXT PRIMARY KEY,
            value       REAL,
            description TEXT
        );

        -- Monthly snapshot of account balances (manual input each review)
        CREATE TABLE IF NOT EXISTS liquidity_snapshots (
            month           TEXT PRIMARY KEY,
            savings         REAL,
            checking_net    REAL,
            brokerage_total REAL,
            bonus_pool      REAL,
            notes           TEXT
        );
    """)
    conn.commit()


def init_pool_config(conn):
    """Seed static liquidity config if not present."""
    defaults = [
        ('emergency_fund_target',     EMERGENCY_FUND_TARGET,     '6 months Balanced Scenario expenses'),
        ('emergency_brokerage_alloc', EMERGENCY_BROKERAGE_ALLOC, 'Brokerage portion designated as emergency backstop'),
        ('retirement_est',            RETIREMENT_EST,            'Combined retirement accounts estimate (awareness only)'),
    ]
    for key, value, desc in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO pool_config (key, value, description) VALUES (?,?,?)",
            (key, value, desc)
        )
    conn.commit()


def get_pool_config(conn):
    rows = conn.execute("SELECT key, value FROM pool_config").fetchall()
    return {row[0]: row[1] for row in rows}


def save_liquidity_snapshot(conn, month, savings, checking_net, brokerage_total, bonus_pool):
    conn.execute("""
        INSERT OR REPLACE INTO liquidity_snapshots
            (month, savings, checking_net, brokerage_total, bonus_pool)
        VALUES (?,?,?,?,?)
    """, (month, savings, checking_net, brokerage_total, bonus_pool))
    conn.commit()


def get_last_liquidity_snapshot(conn, before_month=None):
    if before_month:
        row = conn.execute(
            "SELECT * FROM liquidity_snapshots WHERE month < ? ORDER BY month DESC LIMIT 1",
            (before_month,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM liquidity_snapshots ORDER BY month DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    cols = ['month', 'savings', 'checking_net', 'brokerage_total', 'bonus_pool', 'notes']
    return dict(zip(cols, row))


def init_bonus_pool(conn):
    """Seed the bonus pool ledger with the actual 2025 bonus breakdown if not already present."""
    row = conn.execute(
        "SELECT id FROM bonus_pool_ledger WHERE description = '2025 Bonus received (net)'"
    ).fetchone()
    if row:
        return  # already seeded

    entries = [
        ('2025-12-19', '2025-12', '2025 Bonus received (net)',           'Bonus Credit',      BONUS_RECEIVED,        'confirmed'),
        ('2025-12-23', '2025-12', 'Emergency fund transfer to savings',  'Savings Allocation', -SAVINGS_TRANSFER,     'confirmed'),
    ]
    for entry_date, month, desc, cat, amount, status in entries:
        bal = conn.execute(
            "SELECT COALESCE(running_balance,0) FROM bonus_pool_ledger WHERE status='confirmed' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        new_bal = (bal[0] if bal else 0) + amount
        conn.execute("""
            INSERT INTO bonus_pool_ledger (entry_date, month, description, category, amount, running_balance, status)
            VALUES (?,?,?,?,?,?,?)
        """, (entry_date, month, desc, cat, amount, new_bal, status))

    # December bonus spend line items
    for entry_date, desc, amount in DEC_BONUS_SPEND:
        bal = conn.execute(
            "SELECT running_balance FROM bonus_pool_ledger WHERE status='confirmed' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        new_bal = bal[0] - amount
        conn.execute("""
            INSERT INTO bonus_pool_ledger (entry_date, month, description, category, amount, running_balance, status)
            VALUES (?,?,?,?,?,?,?)
        """, (entry_date, '2025-12', desc, 'Bonus Spend', -amount, new_bal, 'confirmed'))

    conn.commit()


def get_pool_balance(conn, confirmed_only=True):
    status_filter = "WHERE status = 'confirmed'" if confirmed_only else ""
    row = conn.execute(f"""
        SELECT running_balance FROM bonus_pool_ledger
        {status_filter}
        ORDER BY id DESC LIMIT 1
    """).fetchone()
    return row[0] if row else 0


def get_pool_balance_before_month(conn, month):
    """Return the confirmed pool balance at the end of the previous month (opening balance for month)."""
    row = conn.execute(
        "SELECT running_balance FROM bonus_pool_ledger WHERE status='confirmed' AND month < ? ORDER BY id DESC LIMIT 1",
        (month,)
    ).fetchone()
    return row[0] if row else 0


def record_pool_draw(conn, entry_date, month, description, category, amount, pending=False):
    """
    Record a draw (negative) or credit (positive) against the bonus pool.
    Pending entries are tracked but not included in the confirmed balance.
    """
    status = 'pending' if pending else 'confirmed'
    # Calculate running balance from confirmed entries only
    confirmed_balance = get_pool_balance(conn, confirmed_only=True)
    if not pending:
        new_balance = confirmed_balance + amount  # amount is negative for draws
    else:
        new_balance = confirmed_balance  # pending don't move confirmed balance

    conn.execute("""
        INSERT INTO bonus_pool_ledger
            (entry_date, month, description, category, amount, running_balance, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (entry_date, month, description, category, amount, new_balance, status))
    conn.commit()
    return new_balance


def month_already_reviewed(conn, month):
    row = conn.execute(
        "SELECT 1 FROM bonus_pool_ledger WHERE month = ? AND category = 'Monthly Gap'",
        (month,)
    ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Transaction loading & classification
# ---------------------------------------------------------------------------

def load_csv(csv_path, month):
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    target = pd.Period(month, freq='M')
    df = df[df['Date'].dt.to_period('M') == target].copy()
    return df


def classify(df):
    """Split the month's transactions into logical buckets."""
    # Income: negative amounts in the Income category
    income_mask = df['Category'].isin(INCOME_CATEGORIES) & (df['Amount'] < 0)
    income_df = df[income_mask].copy()

    # Interest income (subset of income — savings interest)
    interest_mask = income_mask & df['Name'].str.contains('Interest', case=False, na=False)
    interest_df = df[interest_mask].copy()

    # Base salary paychecks: Income transactions close to $5,400
    salary_mask = income_mask & ~interest_mask & (df['Amount'].abs().between(5_200, 5_600))
    salary_df = df[salary_mask].copy()

    # Other income: income that's not salary and not interest
    other_income_mask = income_mask & ~salary_mask & ~interest_mask
    other_income_df = df[other_income_mask].copy()

    # Excluded categories (transfers, business)
    excluded_df = df[df['Category'].isin(EXCLUDE_CATEGORIES)].copy()

    # Bonus spend
    bonus_df = df[df['Category'].isin(BONUS_SPEND_CATEGORIES) & (df['Amount'] > 0)].copy()

    # Exceptional one-time items
    exceptional_df = df[df['Category'].isin(EXCEPTIONAL_CATEGORIES) & (df['Amount'] > 0)].copy()

    # Regular expenses: positive amounts, none of the above categories
    skip = EXCLUDE_CATEGORIES | BONUS_SPEND_CATEGORIES | EXCEPTIONAL_CATEGORIES | INCOME_CATEGORIES
    regular_df = df[(df['Amount'] > 0) & (~df['Category'].isin(skip))].copy()

    # Refunds: negative amounts in expense categories (returns, credits)
    refunds_df = df[(df['Amount'] < 0) & (~df['Category'].isin(INCOME_CATEGORIES | EXCLUDE_CATEGORIES))].copy()

    return {
        'salary': salary_df,
        'other_income': other_income_df,
        'interest': interest_df,
        'excluded': excluded_df,
        'bonus_spend': bonus_df,
        'exceptional': exceptional_df,
        'regular': regular_df,
        'refunds': refunds_df,
    }


# ---------------------------------------------------------------------------
# Budget comparison
# ---------------------------------------------------------------------------

def get_budget_targets(conn):
    return pd.read_sql(
        "SELECT category, target_2026 FROM scenarios_2026 WHERE scenario_name='Balanced'",
        conn
    ).set_index('category')['target_2026']


def build_comparison(regular_df, refunds_df, budget_targets):
    """Return a DataFrame comparing net actuals to budget targets."""
    expense_by_cat = regular_df.groupby('Category')['Amount'].sum()
    refund_by_cat  = refunds_df.groupby('Category')['Amount'].sum().abs()

    all_cats = sorted(set(expense_by_cat.index) | set(budget_targets.index))

    rows = []
    for cat in all_cats:
        actual  = expense_by_cat.get(cat, 0.0)
        refund  = refund_by_cat.get(cat, 0.0)
        net     = actual - refund
        budget  = budget_targets.get(cat, None)

        if budget is not None:
            variance     = net - budget
            variance_pct = (variance / budget * 100) if budget > 0 else 0.0
            budgeted     = True
        else:
            variance     = None
            variance_pct = None
            budgeted     = False

        rows.append({
            'category':     cat,
            'actual':       net,
            'refunds':      refund,
            'budget':       budget,
            'variance':     variance,
            'variance_pct': variance_pct,
            'budgeted':     budgeted,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def fmt(amount, prefix='$'):
    if amount is None:
        return '—'
    sign = '-' if amount < 0 else ''
    return f"{sign}{prefix}{abs(amount):,.2f}"


def variance_icon(variance, variance_pct):
    if variance is None:
        return '—'
    if variance <= 0:
        return '✅'
    if variance_pct <= 10:
        return '🟡'
    return '🔴'


def get_pending_pool_entries(conn):
    """Return all pending bonus pool entries (reservations not yet confirmed)."""
    rows = conn.execute(
        "SELECT entry_date, description, category, amount FROM bonus_pool_ledger WHERE status='pending' ORDER BY entry_date"
    ).fetchall()
    return [{'date': r[0], 'description': r[1], 'category': r[2], 'amount': r[3]} for r in rows]


def generate_report(month, buckets, comparison_df, pool_before, pool_draws, pool_after,
                    liquidity=None, config=None, conn=None):
    month_label = pd.Period(month, freq='M').strftime('%B %Y')
    today = date.today().isoformat()

    lines = []
    a = lines.append

    a(f"# {month_label} Budget Review")
    a(f"_Generated {today} · Scenario: Balanced_")
    a("")

    # ---- Income -------------------------------------------------------
    a("## Income")
    a("")
    a("| Source | Amount |")
    a("|--------|-------:|")

    salary_total = buckets['salary']['Amount'].abs().sum()
    a(f"| Base Salary ({len(buckets['salary'])} paychecks) | {fmt(salary_total)} |")

    for _, row in buckets['other_income'].iterrows():
        a(f"| Other — {row['Name']} | {fmt(abs(row['Amount']))} |")

    interest_total = buckets['interest']['Amount'].abs().sum()
    if interest_total > 0:
        a(f"| Savings Interest _(not counted as income)_ | {fmt(interest_total)} |")

    total_base = salary_total
    a(f"| **Total Base Income** | **{fmt(total_base)}** |")
    a("")

    # ---- Budget vs Actuals -------------------------------------------
    a("## Budget vs. Actuals")
    a("")

    budgeted_df   = comparison_df[comparison_df['budgeted']].sort_values('variance', ascending=False)
    unbudgeted_df = comparison_df[~comparison_df['budgeted'] & (comparison_df['actual'] > 0)]

    a("### Budgeted Categories")
    a("")
    a("| Category | Budget | Actual | Variance | |")
    a("|----------|-------:|-------:|---------:|:-:|")

    for _, row in budgeted_df.iterrows():
        icon = variance_icon(row['variance'], row['variance_pct'])
        refund_note = f" _(−{fmt(row['refunds'])} refunds)_" if row['refunds'] > 0 else ""
        a(f"| {row['category']}{refund_note} | {fmt(row['budget'])} | {fmt(row['actual'])} | {fmt(row['variance'])} | {icon} |")

    budgeted_total_budget = budgeted_df['budget'].sum()
    budgeted_total_actual = budgeted_df['actual'].sum()
    budgeted_total_var    = budgeted_total_actual - budgeted_total_budget
    a(f"| **Total** | **{fmt(budgeted_total_budget)}** | **{fmt(budgeted_total_actual)}** | **{fmt(budgeted_total_var)}** | |")
    a("")

    if len(unbudgeted_df) > 0:
        a("### Unbudgeted / Pass-through Categories")
        a("_These categories don't have targets in the Balanced Scenario — shown for awareness._")
        a("")
        a("| Category | Actual |")
        a("|----------|-------:|")
        for _, row in unbudgeted_df.iterrows():
            a(f"| {row['category']} | {fmt(row['actual'])} |")
        unbudgeted_total = unbudgeted_df['actual'].sum()
        a(f"| **Total** | **{fmt(unbudgeted_total)}** |")
        a("")

    total_regular = comparison_df[comparison_df['actual'] > 0]['actual'].sum()

    # ---- Exceptional items -------------------------------------------
    a("## Above-the-Line Exceptional Items")
    a("_One-time or irregular expenses — not counted against monthly budget._")
    a("")

    if len(buckets['exceptional']) > 0:
        a("| Date | Description | Amount | Pool Decision |")
        a("|------|-------------|-------:|---------------|")
        for _, row in buckets['exceptional'].iterrows():
            a(f"| {row['Date'].date()} | {row['Name']} | {fmt(row['Amount'])} | ⏳ Pending |")
        exceptional_total = buckets['exceptional']['Amount'].sum()
        a(f"| | **Total** | **{fmt(exceptional_total)}** | |")
    else:
        a("_None this month._")
    a("")

    # ---- Bonus spend -------------------------------------------------
    a("## Bonus Spend (Pool-Funded)")
    a("_Discretionary bonus-funded purchases — tracked against pool, not monthly budget._")
    a("")

    if len(buckets['bonus_spend']) > 0:
        a("| Date | Description | Amount |")
        a("|------|-------------|-------:|")
        for _, row in buckets['bonus_spend'].iterrows():
            a(f"| {row['Date'].date()} | {row['Name']} | {fmt(row['Amount'])} |")
        bonus_spend_total = buckets['bonus_spend']['Amount'].sum()
        a(f"| | **Total** | **{fmt(bonus_spend_total)}** |")
    else:
        a("_None this month._")
    a("")

    # ---- Bonus pool --------------------------------------------------
    a("## Bonus Pool Status")
    a("")
    a("| | Amount |")
    a("|--|-------:|")
    a(f"| Opening Balance | {fmt(pool_before)} |")

    for desc, amt, status in pool_draws:
        label = f"_{desc}_ ⏳ pending" if status == 'pending' else desc
        a(f"| {label} | {fmt(amt)} |")

    a(f"| **Confirmed Closing Balance** | **{fmt(pool_after)}** |")
    a("")

    # Annual planned draws (dynamic from DB)
    a("### Planned Pool Draws")
    a("_Pending reservations not yet drawn from confirmed balance._")
    a("")
    pending = get_pending_pool_entries(conn) if conn else []
    if pending:
        a("| Due | Description | Amount |")
        a("|-----|-------------|-------:|")
        for p in pending:
            a(f"| {p['date']} | {p['description']} | {fmt(p['amount'])} |")
        pending_total = sum(p['amount'] for p in pending)
        a(f"| | **Total pending** | **{fmt(pending_total)}** |")
        a(f"| | **Pool if all confirmed** | **{fmt(pool_after + pending_total)}** |")
    else:
        a("_No pending reservations._")
    a("")

    # ---- Monthly gap -------------------------------------------------
    unbudgeted_total = unbudgeted_df['actual'].sum() if len(unbudgeted_df) > 0 else 0.0
    gap = total_base - budgeted_total_actual - unbudgeted_total
    a("## Monthly Cash Flow Summary")
    a("")
    a("| | Amount |")
    a("|--|-------:|")
    a(f"| Base Income | {fmt(total_base)} |")
    a(f"| Regular Expenses (budgeted) | {fmt(budgeted_total_actual)} |")
    if unbudgeted_total > 0:
        a(f"| Unbudgeted Expenses | {fmt(unbudgeted_total)} |")
    a(f"| **Net (before pool draw)** | **{fmt(gap)}** |")
    a("")
    if gap < 0:
        a(f"> **Monthly shortfall of {fmt(abs(gap))} drawn from bonus pool.**")
    else:
        a(f"> **Monthly surplus of {fmt(gap)} — no pool draw needed for gap.**")
    a("")

    # ---- Recommendations --------------------------------------------
    a("## Recommendations for Next Month")
    a("")

    over_budget = budgeted_df[budgeted_df['variance'] > 0].sort_values('variance', ascending=False)
    under_budget = budgeted_df[budgeted_df['variance'] < 0].sort_values('variance')

    if len(over_budget) > 0:
        a("### Watch Categories (over budget)")
        a("")
        for _, row in over_budget.iterrows():
            pct = f"{row['variance_pct']:.0f}%"
            a(f"- **{row['category']}**: {fmt(row['variance'])} over ({pct}) — budget {fmt(row['budget'])}, actual {fmt(row['actual'])}")
        a("")

    if len(under_budget) > 0:
        a("### Headroom (under budget)")
        a("")
        for _, row in under_budget.iterrows():
            a(f"- **{row['category']}**: {fmt(abs(row['variance']))} under — budget {fmt(row['budget'])}, actual {fmt(row['actual'])}")
        a("")

    # ---- Full Liquidity Picture --------------------------------------
    if liquidity and config:
        a("## Full Liquidity Picture")
        a(f"_Account balances as of end of {month_label}. Brokerage is equities — value fluctuates._")
        a("")

        ef_target      = config.get('emergency_fund_target',     EMERGENCY_FUND_TARGET)
        ef_brokerage   = config.get('emergency_brokerage_alloc', EMERGENCY_BROKERAGE_ALLOC)
        ef_savings     = ef_target - ef_brokerage

        savings        = liquidity.get('savings', 0)
        checking_net   = liquidity.get('checking_net', 0)
        brokerage      = liquidity.get('brokerage_total', 0)
        retirement     = config.get('retirement_est', RETIREMENT_EST)

        freed_savings      = max(0, savings - ef_savings)
        brokerage_growth   = max(0, brokerage - ef_brokerage)
        total_pool         = pool_after + freed_savings

        a("### Tier 1 — Cash (immediate access)")
        a("")
        a("| Account | Balance | Role |")
        a("|---------|--------:|------|")
        a(f"| Capital One Savings | {fmt(savings)} | Emergency fund (primary floor: {fmt(ef_savings)}) |")
        a(f"| &nbsp;&nbsp;→ Above emergency floor | {fmt(freed_savings)} | Available as extended bonus pool |")
        a(f"| Checking (net of cards) | {fmt(checking_net)} | Day-to-day operations |")
        a(f"| Bonus Pool (confirmed) | {fmt(pool_after)} | Gap coverage & discretionary |")
        a(f"| **Total Tier 1** | **{fmt(savings + checking_net + pool_after)}** | _(pool overlaps with checking)_ |")
        a("")

        a("### Tier 2 — Brokerage / Freedom Fund (Vanguard taxable)")
        a("")
        a("| Bucket | Value | Notes |")
        a("|--------|------:|-------|")
        a(f"| Emergency backstop (VFIAX + VOO) | {fmt(ef_brokerage)} | Designated; S&P 500 index, market risk |")
        a(f"| Freedom / Growth Fund | {fmt(brokerage_growth)} | Stay invested; business seed |")
        a(f"| **Total Brokerage** | **{fmt(brokerage)}** | All equities — tech-heavy (VGT 41%) |")
        a("")

        a("### Tier 3 — Retirement (awareness only, not counted)")
        a("")
        a("| | Est. Value |")
        a("|--|----------:|")
        a(f"| Combined IRAs + 401k(s) | ~{fmt(retirement)} |")
        a("")

        a("### Summary")
        a("")
        a("| | Amount |")
        a("|--|-------:|")
        a(f"| Bonus pool (confirmed) | {fmt(pool_after)} |")
        a(f"| Freed savings (above emergency floor) | {fmt(freed_savings)} |")
        a(f"| **Total available pool (2026)** | **{fmt(total_pool)}** |")
        a(f"| Brokerage emergency backstop | {fmt(ef_brokerage)} |")
        a(f"| Brokerage freedom/growth | {fmt(brokerage_growth)} |")
        a(f"| Retirement (not in plan) | ~{fmt(retirement)} |")
        a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(month, csv_path, draw_car_repair=False, savings=None, checking_net=None, brokerage=None):
    conn = sqlite3.connect(DB_PATH)
    setup_tables(conn)
    init_bonus_pool(conn)
    init_pool_config(conn)

    if month_already_reviewed(conn, month):
        print(f"⚠️  Month {month} has already been recorded in the bonus pool ledger.")
        print("    Re-generating report from existing data. Re-run with --reset to redo.")

    df = load_csv(csv_path, month)
    print(f"Loaded {len(df)} transactions for {month}")

    buckets = classify(df)
    budget_targets = get_budget_targets(conn)
    comparison_df = build_comparison(buckets['regular'], buckets['refunds'], budget_targets)

    # Save actuals to DB
    for _, row in comparison_df.iterrows():
        conn.execute("""
            INSERT OR REPLACE INTO monthly_actuals_2026
                (month, category, actual_amount, budget_target, variance, variance_pct)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (month, row['category'], row['actual'], row['budget'], row['variance'], row['variance_pct']))
    conn.commit()

    # Capture reviewed state once — before any writes, so all draws record or none do
    already_reviewed = month_already_reviewed(conn, month)

    pool_before = get_pool_balance_before_month(conn, month)
    pool_draws = []
    month_end = pd.Period(month, freq='M').end_time.date().isoformat()

    budgeted_actual   = comparison_df[comparison_df['budgeted']]['actual'].sum()
    unbudgeted_actual = comparison_df[~comparison_df['budgeted'] & (comparison_df['actual'] > 0)]['actual'].sum()
    salary_total      = buckets['salary']['Amount'].abs().sum()

    # Monthly income gap: income minus all real expenses (budgeted + legitimate unbudgeted)
    # Excludes: credit card payments, work expense, bonus spend, exceptional — handled separately
    total_real_expenses = budgeted_actual + unbudgeted_actual
    gap = salary_total - total_real_expenses   # negative = shortfall

    if total_real_expenses > salary_total and not already_reviewed:
        record_pool_draw(conn, month_end, month, 'Monthly income gap', 'Monthly Gap', gap)
        pool_draws.append(('Monthly income gap', gap, 'confirmed'))

    # Bonus spend — always drawn from pool
    bonus_spend_total = buckets['bonus_spend']['Amount'].sum()
    if bonus_spend_total > 0 and not already_reviewed:
        record_pool_draw(conn, month_end, month, 'Bonus spend', 'Bonus Spend', -bonus_spend_total)
        pool_draws.append(('Bonus spend', -bonus_spend_total, 'confirmed'))

    # Exceptional / car repair
    exceptional_total = buckets['exceptional']['Amount'].sum()
    if exceptional_total > 0:
        # Check if already confirmed in ledger (e.g. manually recorded)
        existing_draw = conn.execute(
            "SELECT id FROM bonus_pool_ledger WHERE month=? AND category='Exceptional' AND status='confirmed'",
            (month,)
        ).fetchone()
        if existing_draw:
            pool_draws.append(('Car repair — exceptional (drawn from pool)', -exceptional_total, 'confirmed'))
        elif draw_car_repair and not already_reviewed:
            record_pool_draw(conn, month_end, month, 'Car repair (exceptional)', 'Exceptional', -exceptional_total)
            pool_draws.append(('Car repair — exceptional (drawn from pool)', -exceptional_total, 'confirmed'))
        else:
            pool_draws.append(('Car repair — exceptional (pending pool decision)', -exceptional_total, 'pending'))

    pool_after = get_pool_balance(conn)

    # Save liquidity snapshot if balances were provided
    liquidity = None
    config = get_pool_config(conn)
    if savings is not None or checking_net is not None or brokerage is not None:
        snap = get_last_liquidity_snapshot(conn) or {}
        s = savings      if savings      is not None else snap.get('savings', 0)
        c = checking_net if checking_net is not None else snap.get('checking_net', 0)
        b = brokerage    if brokerage    is not None else snap.get('brokerage_total', 0)
        save_liquidity_snapshot(conn, month, s, c, b, pool_after)
        liquidity = {'savings': s, 'checking_net': c, 'brokerage_total': b}
    else:
        # Use last known snapshot if available
        snap = get_last_liquidity_snapshot(conn)
        if snap:
            liquidity = snap

    report = generate_report(month, buckets, comparison_df, pool_before, pool_draws, pool_after,
                             liquidity=liquidity, config=config, conn=conn)

    os.makedirs('reviews', exist_ok=True)
    report_path = f'reviews/{month}-review.md'
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Report written to {report_path}")
    print(f"\n{'='*60}")
    print(report)

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monthly budget review vs. Balanced Scenario')
    parser.add_argument('--month',        required=True,  help='Month to review, e.g. 2026-01')
    parser.add_argument('--csv',          required=True,  help='Path to Rocket Money CSV export')
    parser.add_argument('--draw-car-repair', action='store_true',
                        help='Draw the exceptional car repair from the bonus pool')
    # Optional balance inputs — saved to DB and used in liquidity picture
    parser.add_argument('--savings',      type=float, help='Capital One Savings balance (end of month)')
    parser.add_argument('--checking-net', type=float, help='Checking balance minus outstanding card balance')
    parser.add_argument('--brokerage',    type=float, help='Vanguard taxable brokerage total value')
    args = parser.parse_args()

    run(args.month, args.csv,
        draw_car_repair=args.draw_car_repair,
        savings=args.savings,
        checking_net=args.checking_net,
        brokerage=args.brokerage)

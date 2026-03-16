# Financial Advisor — Project Context

## What This Is
A personal financial analysis pipeline for Dan Grindall. It ingests Rocket Money CSV exports,
analyzes spending against a 2026 Balanced Scenario budget, tracks a bonus pool, and generates
monthly markdown review reports. It also tracks full liquidity picture across savings, brokerage, and retirement.

## Key Financial Facts (as of Jan 2026 review, updated Mar 2026)

### Income
- Base salary: $10,800/month (2× ~$5,400 bi-weekly paychecks from LOCALLY COMPACT)
- Annual bonuses: April (~$5,600) + August (~$5,600) + December (variable, 2025 was $77,340.57 net)
- Monthly base income deficit vs. expenses: ~$200–$2,800/month depending on spending (covered by bonus pool)

### 2025 Bonus — Actual Reconciliation
- Bonus received: **$77,340.57** (Dec 19, 2025 — category "Bonus Income" in Rocket Money)
- Savings transfer (Dec 23): **$50,000** moved to savings (still bonus money, earning interest)
- Dec bonus spend: $5,767.06 (Mattress Firm $5,595 + parking $90 + SWA $82)
- Full bonus pool = **$77,340.57** (includes $50k in savings)
- Note: The $50k is NOT an emergency fund draw — emergency fund is backed by pre-existing savings ($30k) + brokerage backstop ($40k)

### Bonus Pool (after Mar 2026 review)
- Pool entering Jan: $21,573.51
- Jan monthly gap draw: -$199.64
- Jan bonus spend (Mattress Firm, Girl Scouts): -$850.66
- Jan car repair (Groove Subaru, exceptional): -$4,746.15 ← confirmed drawn
- Jan closing: $15,777.06
- Feb monthly gap draw: -$994.04
- Feb bonus spend (travel, Girl Scouts, parking): -$3,224.55
- Feb closing: $11,558.47
- Mar monthly gap draw (partial month): -$792.05
- **Confirmed closing balance: $10,766.42**
- IRS payment (~$5,000): pending, planned for April 2026
- Tracked in `bonus_pool_ledger` table in `budget_analysis.db`

### Account Balances (as of Jan 2026 snapshot)
- Capital One Savings: $80,773
- Checking (net of outstanding cards): $9,401
- Vanguard Taxable Brokerage: $147,480 (VFIAX, VOO, GOOGL, VGT, VMFXX)
- Retirement (IRAs + 401k): ~$1,000,000 (not counted in monthly plan)
- Note: Feb and Mar balances not yet captured — update when running next review

### Liquidity Tiers
1. **Cash**: Savings ($80,773) + Checking net ($9,401) + Bonus pool ($15,777)
2. **Brokerage**: $40,000 designated as emergency backstop (VFIAX/VOO); remainder is Freedom Fund
3. **Retirement**: ~$1M — not counted in spending plan

### Emergency Fund
- Target: ~$70,000
- Structure: ~$30,000 pre-existing savings + $40,000 brokerage backstop
- The $50k savings transfer is bonus money earning interest, NOT emergency fund
- Brokerage backstop is flexible — can trim to preserve investing

## Budget Scenario
- **Active scenario: Balanced** (recommended from 2025 analysis)
- Targets are in `scenarios_2026` table in `budget_analysis.db`
- Key cuts vs. 2025: Shopping -25%, Dining -25%, Entertainment -20%, Groceries -10%, Personal Care -15%, Software -20%, Home & Garden -15%

## Transaction Classification Rules (monthly_review.py)
| Category | Treatment |
|----------|-----------|
| Credit Card Payment | Excluded (transfer) |
| Work Expense | Excluded (reimbursed) |
| Reimbursement | Excluded |
| Company Travel | Excluded (reimbursed business travel) |
| Internal Transfers | Excluded |
| Bonus Spend | Pool draw (not in monthly budget) |
| Bonus Income | Pool credit (not regular income) |
| Unexpected | Above-the-line exceptional item |
| Income | Regular income (base salary) |

## Monthly Review Tool
```bash
# Basic run
python3 monthly_review.py --month 2026-02 --csv /path/to/export.csv

# With current balances (saves to DB, shows liquidity picture)
python3 monthly_review.py --month 2026-02 --csv /path/to/export.csv \
  --savings 80773 --checking-net 9401 --brokerage 147480

# If drawing car repair from bonus pool
python3 monthly_review.py --month 2026-01 --csv /path/to/export.csv --draw-car-repair
```

Reports are written to `reviews/YYYY-MM-review.md`.

## Database: budget_analysis.db
| Table | Contents |
|-------|----------|
| transactions | All 2025 Rocket Money transactions |
| monthly_summary | 2025 monthly cashflow summary |
| category_summary | 2025 spending by category |
| projected_2026_budget | 2026 projections with inflation |
| scenarios_2026 | Conservative / Balanced / Aggressive scenario targets |
| inflation_impact | Category-level inflation rates |
| vehicle_maintenance_2026 | 2-vehicle maintenance budget |
| bonus_allocation | Scenario bonus allocation plans |
| bonus_pool_ledger | **Running bonus pool ledger (all 2026 draws)** |
| monthly_actuals_2026 | **Monthly actuals vs. budget by category** |
| pool_config | Emergency fund split config |
| liquidity_snapshots | Monthly account balance snapshots |
| recurring_expense_profile | **Recurring bill profile (auto-built from 2025 data, 18 merchants)** |

## Vanguard Brokerage Holdings
- VFIAX: Vanguard 500 Index Admiral (~20%)
- VOO: Vanguard S&P 500 ETF (~25%)
- GOOGL: Alphabet Inc. (~13%)
- VGT: Vanguard Info Tech ETF (~41%) ← heavy tech concentration
- VMFXX: Federal Money Market (~0%)
- Note: VOO and VFIAX are duplicative (both S&P 500). VGT/GOOGL add significant tech tilt.
- Dividends reinvested automatically

## Data Sources
- Spending: Rocket Money CSV export (from `/mnt/c/Users/dangr/Downloads/`)
- Brokerage: Vanguard CSV export (VanguardBrokerage.csv in Downloads)
- Format: Vanguard CSVs have a 2-section format — holdings (rows 1–5), then transactions (skip 8 rows)

## Review Status
- **Jan 2026**: ✅ Complete — `reviews/2026-01-review.md` + `reviews/2026-01-family-summary.md`
- **Feb 2026**: ✅ Complete — `reviews/2026-02-review.md` + `reviews/2026-02-family-dashboard.html`
- **Mar 2026**: ✅ Complete (partial, through Mar 15) — `reviews/2026-03-review.md` + `reviews/2026-03-family-dashboard.html`
- Annual re-forecast: Not yet done for 2026 (original projections were pre-Jan actuals)

## Dependencies
- Python 3 with `pandas` (only non-stdlib dependency)
- SQLite3 (stdlib)
- Rocket Money CSV export from `/mnt/c/Users/dangr/Downloads/`

## Key Decisions Made
- Emergency fund: $30k pre-existing savings + $40k brokerage backstop = $70k
- $50k savings transfer = bonus money earning interest (NOT emergency fund)
- "If no emergency, we invest" — brokerage freedom fund stays invested
- Budget scenario: Balanced (not Conservative, not Aggressive)
- Bonus pool = full $77,340.57 (includes $50k in savings)
- Car repair ($4,746): drawn from pool in Jan 2026 review (confirmed)
- IRS payment (~$5,000): planned for April 2026 (pending in ledger)
- April + August bonuses (~$5,600 each) will replenish pool mid-year
- Terri's income transfers categorized as "Income" — triggers celebration in dashboard
- Green shield: bonus spend eats monthly gap savings first before growing amber bar
- Partial month green shield: projected from daily discretionary burn rate, not raw ledger gap

## Dashboard Architecture (generate_dashboard.py)
- **No external JS dependencies** — pure HTML/CSS, stdlib Python only
- **Progress meters** replace scorecard: spend meter + three-level split mirror bonus pool
- **Three-level split mirror**: spendable (dark blue + green) | reserved (light blue) | spent (amber + dark amber)
- **Green shield**: monthly savings absorb bonus spend; overflow becomes dark amber
- **Stars & streaks**: per-category in Budget Performance table (gold star + x2/x3 badges)
- **Bill tracker**: auto-detected from `recurring_expense_profile` (18 merchants, 10+ month history)
- **Collapsible sections**: Budget Performance, Bill Tracker use `<details>` elements
- **Gamification**: green pills for savings, amber pills for bonus spend, purple for extra income
- **`--csv` flag**: enables bill tracker + projected green shield; without it, retrospective only

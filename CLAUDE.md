# Financial Advisor — Project Context

## What This Is
A personal financial analysis pipeline for Dan Grindall. It ingests Rocket Money CSV exports,
analyzes spending against a 2026 Balanced Scenario budget, tracks a bonus pool, and generates
monthly markdown review reports. It also tracks full liquidity picture across savings, brokerage, and retirement.

## Key Financial Facts (as of Feb 2026)

### Income
- Base salary: $10,800/month (2× ~$5,400 bi-weekly paychecks from LOCALLY COMPACT)
- Annual bonuses: April (~$5,600) + August (~$5,600) + December (variable, 2025 was $77,340.57 net)
- Monthly base income deficit vs. expenses: ~$200–$2,800/month depending on spending (covered by bonus pool)

### 2025 Bonus — Actual Reconciliation
- Bonus received: **$77,340.57** (Dec 19, 2025 — category "Bonus Income" in Rocket Money)
- Savings transfer (Dec 23): **-$50,000** (emergency fund top-up)
- Operational pool entering 2026: **$21,573.51** (after Dec bonus spend)
- Note: The old scripts had $90,642 hardcoded — that was wrong. Use $77,340.57.

### Bonus Pool (as of Feb 2026)
- Pool entering Jan: $21,573.51
- Jan draws (gap + bonus spend): -$1,050.30
- Feb draws to date (travel + Girl Scouts): -$2,681.90
- **Current confirmed balance: ~$17,841**
- Car repair ($4,746.15) is still a pending pool decision
- Tracked in `bonus_pool_ledger` table in `budget_analysis.db`

### Account Balances (Feb 21, 2026)
- Capital One Savings: $80,773
- Checking (net of outstanding cards): $9,401
- Vanguard Taxable Brokerage: $147,480 (VFIAX, VOO, GOOGL, VGT, VMFXX)
- Retirement (IRAs + 401k): ~$1,000,000 (not counted in monthly plan)

### Liquidity Tiers
1. **Cash**: Savings ($80,773) + Checking net ($9,401) + Bonus pool ($17,841)
2. **Brokerage**: $40,000 designated as emergency backstop (VFIAX/VOO); remainder is Freedom Fund
3. **Retirement**: ~$1M — not counted in spending plan

### Emergency Fund
- Target: ~$81,690 (6 months at Balanced Scenario)
- Structure: ~$41,690 in savings (floor) + $40,000 brokerage backstop (flexible — can trim to preserve investing)
- Savings above the floor ($80,773 - $41,690 = ~$39,083) is available as extended bonus pool

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

## Key Decisions Made
- Emergency fund: flexible split (~$41k savings floor + $40k brokerage backstop)
- "If no emergency, we invest" — brokerage freedom fund stays invested
- Budget scenario: Balanced (not Conservative, not Aggressive)
- Bonus pool: operational money only (savings transfer is emergency fund, not pool)
- Car repair ($4,746): pending pool decision as of Feb 2026
- IRS payment (~$5,000): planned for April 2026
- April + August bonuses (~$5,600 each) will replenish pool mid-year

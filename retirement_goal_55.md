# Retirement Goal: Dan's 55th Birthday — July 18, 2034

**The goal:** both retired by **July 18, 2034** (Dan 55, Terri 57), spending **$12,000–$14,000/month** in today's dollars, comfortable with travel, and money that lasts to age 95.

**The verdict:** On plan, this is a **low-risk, comfortable target.** Retiring at 55 you'd have ~$2.9M invested, never dip below ~$2.6M even mid-retirement, and—if returns merely cooperate—die with $7M+. Even a poor-returns world (4% real) still works at the $12k/mo level.

---

## Where things stand now (May 2026)

| Bucket | Balance | Notes |
|---|---|---|
| Tax-deferred (401ks, rollover/trad IRAs) | $794,274 | taxed as income on withdrawal |
| Roth (tax-free) | $327,070 | |
| Taxable brokerage | $172,992 | Vanguard joint 7157 |
| **Total investable** | **$1,294,336** | the number we track |
| Cash | ~$84k (+$50k gift incoming) | buffer, not counted |
| 529 college | $115,370 + $500/mo | funds kids' college, off-balance-sheet |

**Income:** $222k base + ~$150k bonus (~$372k gross). **Mortgage:** $340,657 @ 2.75%.
**Social Security at 67:** Dan $4,223/mo, Terri ~$2,815/mo = **~$84k/yr** — covers ~60–70% of the spend goal once it starts.

## The savings engine (per year)
- 401k: $24k employee + $8,880 match (catch-up bumps it at 50) = ~$32.9k
- Two backdoor Roth IRAs: $14k *(action: move Terri from non-deductible Traditional to backdoor Roth)*
- Surplus bonus → taxable brokerage: ~$50k **(the #1 lever — protect this)**
- **~$96k/yr total going to work.**

---

## Can we hit $12–14k/mo? Yes, with this nuance

| Monthly spend | Base case (5% real) | Stress (4% real, smaller bonus) |
|---|---|---|
| **$12,000** | ✅ dies with ~$4.2M | ✅ just makes it |
| **$13,000** | ✅ dies with ~$2.6M | ⚠️ needs ~5% real or upside |
| **$14,000** | ✅ dies with ~$1.0M | ⚠️ relies on upside buffers |

**Plan around $12k/mo as guaranteed-safe, treat $13–14k/mo as the reward if returns cooperate** — and they likely will, because none of the upside below is counted: 529s already cover college, ~$170k cash, a parental inheritance (paying off the mortgage), the mortgage dropping off ~2049 anyway, and the option to delay SS to 70 ($5,266/mo).

---

## The trajectory to watch (check actual vs target each Jan 1)

| Jan 1 | Dan / Terri | Target investable |
|---|---|---|
| 2026 | 47 / 49 | $1.29M (baseline) |
| 2027 | 48 / 50 | $1.46M |
| 2028 | 49 / 51 | $1.64M |
| 2029 | 50 / 52 | $1.82M |
| 2030 | 51 / 53 | $2.02M |
| 2031 | 52 / 54 | $2.24M |
| 2032 | 53 / 55 | $2.46M |
| 2033 | 54 / 56 | $2.70M |
| 2034 | 54 / 56 | $2.94M → **retire July 18** |

If your real balance is **at or above** the target line each Jan 1, you're on track. Below it two years running = we revisit spend, savings, or date.

---

## The real risks (what would move the date)
1. **Sequence-of-returns** in the first ~5 retirement years — the biggest threat. The $12k floor is the cushion.
2. **The ~$50k/yr taxable savings** holding up (it rides on the bonus). Drops to ~$30k? Roughly 1 year later, or trim to $12k/mo.
3. **Health costs pre-65** — budgeted $15k/person/yr; revisit closer to the date.
4. **Social Security policy** — if benefits get trimmed, lean to the $12k end.

## The annual ritual (each Jan 1)
1. Open `retirement_plan.yaml`, fill that year's checkpoint with real numbers (AGI, balances by bucket, contributions, latest SS estimate, mortgage balance).
2. Compare `total_investable` to `target_total_investable`.
3. Re-run `python3 retirement_projection.py` (and stress it: `--return 0.04 --taxable 30000`).
4. We confirm on-track or adjust spend / savings / date.

*Model: `retirement_projection.py`. Tracking data: `retirement_plan.yaml`. All figures today's dollars.*

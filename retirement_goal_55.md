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
- Dan backdoor Roth IRA: $7k (clean — Dan has $0 traditional-IRA basis)
- Terri: **not** backdoor-eligible (her large pre-tax IRA triggers the pro-rata rule) — route her $7k to taxable for now; convert the IRA later (see below)
- Surplus bonus → taxable brokerage: ~$57k **(the #1 lever — protect this)**
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

## Roth conversion strategy (Terri's IRA + the pre-tax pile)

Terri can't do a clean backdoor Roth — her two Charles Schwab traditional IRAs (**$226,489**) trigger the **pro-rata rule**, taxing most of any conversion. The fix is **scheduled Roth conversions in your low-income early-retirement years**, not a backdoor.

**Why bother:** your combined pre-tax pile (~$794k now — Terri's $226k IRAs plus your eBay $344k + Empower $127k + Voleon $97k 401ks) compounds into large RMDs at age 75 (Terri ~2052 / Dan ~2054), stacked on ~$84k of Social Security — that pushes you into 32%+ brackets, triggers IRMAA Medicare surcharges, and creates a brutal "widow's penalty" for whichever of you is left filing single. Converting early smooths all of that.

Note: **Voleon (7960) is your current 401k** — pre-tax, but convertible only after you separate at retirement in 2034. eBay and Empower are former-employer 401ks (rollable now). So in the window, convert Terri's IRAs first, then your 401k money once it's rolled to an IRA.

| Phase | Years | Action |
|---|---|---|
| **Working** | 2026–2033 | **Don't convert** — you're in the 24–32% bracket. Route Terri's $7k to taxable (or roll her IRA into a 401k to unlock a clean backdoor). |
| **Golden window** | **2034–2043** | After retiring, income collapses. **Convert each year up to the top of the 22% bracket (~$207k MFJ taxable, today's $)** — Terri's IRA first, then Dan's rollovers. ~$190k/yr at a ~13–17% federal rate. |
| **Post-SS** | 2044+ | SS raises your income floor — slow/stop conversions to avoid 32%+; finish any remainder before RMDs at 75. |

**Bracket map (today's $, MFJ taxable):** 12% top ≈ $96,950 · **22% top ≈ $206,700 (the target)** · 24% top ≈ $394,600 · avoid 32%+.

**One trade-off:** big conversions raise MAGI and can forfeit ACA health subsidies pre-65. Given the size of your pre-tax pile and that you've budgeted full-freight health, filling the 22% bracket beats chasing subsidies — but if you'd rather keep premiums subsidized, cap conversions at the top of 12% (~$97k/yr) instead. Watch IRMAA (2-year lookback) and Colorado's ~4.4% state tax on each conversion.

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

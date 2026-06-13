# Model Validation Report — June 2026

**Why this exists:** the retirement model was built in one modeling session; nothing
protected it from silent drift, and several plan features existed only in prose
(YAML/markdown) with no code behind them. This audit (a) re-verified every number
the plan documents cite, (b) added a regression suite so the model is *checkable
ground* at every annual review — by you, with no AI in the loop — and (c) closed
the gaps between what the plan says and what the code computes.

**The one-line workflow change:** before trusting any retirement number, run

```bash
python3 -m unittest        # 29 checks, <1 second; green = the model still says
                           # exactly what retirement_plan.yaml / retirement_goal_55.md say
```

---

## 1. What was audited and confirmed correct

Every headline figure in `retirement_goal_55.md` / `retirement_plan.yaml` was
re-derived from the code and matched:

| Claim in the docs | Model output | Status |
|---|---|---|
| Jan-1 target trajectory 2027–2034 ($1.62M → $3.17M) | matches to the dollar | ✅ pinned in tests |
| Retire at 55, $13k/mo base: dies with ~$4.0M | $4,023,750 | ✅ pinned |
| $12k/mo base / stress: ~$5.8M / ~$0.9M | $5,839,185 / $910,881 | ✅ pinned |
| $14k/mo base: ~$2.4M | $2,412,969 | ✅ pinned |
| Max sustainable spend: ~$15,500 base / ~$12,750 stress | $15,498 / $12,731 (new bisection solver) | ✅ pinned |
| Earliest feasible age grid (sensitivity table) | matches | ✅ pinned |
| Accumulation math | independently re-derived loop + closed-form annuity agree to <$1 | ✅ |
| `_draw` tax gross-up | conserves value exactly; priority order correct | ✅ |

**Verdict on the original build: arithmetically sound.** The risk was never the
math — it was the absence of guardrails and the unquantified simplifications below.

## 2. Discrepancies found and fixed

1. **Stale bridge figures.** Docs said taxable ≈ **$707k** at retirement
   (bridge "to ~60") and **$497k** in the $30k-savings case. The model actually
   produces **$835,651** (exhausts during the Dan-59 year) and **$635,120**
   (exhausts during the Dan-58 year). Direction is favorable, but note the
   nuance: the bridge runs out *during* the year Dan turns 59 — a few months
   **before** his Jan-2039 59½ date. Not a problem (Terri is 61 by then, so
   pre-tax draws can come from her accounts; Roth basis and Rule of 55 also
   backstop), but the docs now state it precisely.
2. **`ss_benefit_haircut` existed in the YAML but not in the code.** The plan
   said "set 0.20 to stress a Social Security cut"; the script had no such
   knob. Now `--ss-haircut 0.20`.
3. **Max-sustainable-spend numbers had no generating function** — the
   $12,750/$15,500 figures were quoted in the docs but nothing in the repo
   computed them. Now `--solve-spend` (and they verified correct).
4. **Roth-conversion taxes** (watchlist item #1) were acknowledged but never
   modeled. Now `--conversions` — quantified below.

## 3. New scenario layers (all OFF by default — the pinned baseline never moves)

```bash
python3 retirement_projection.py                         # unchanged baseline
python3 retirement_projection.py --conversions           # Roth conversion drag
python3 retirement_projection.py --ss-haircut 0.20       # SS benefit cut stress
python3 retirement_projection.py --ss-claim-age 70       # delay SS (benefit auto-adjusts)
python3 retirement_projection.py --survivor-at 75        # first-death scenario
python3 retirement_projection.py --side-income 50000     # gap-year side hustle (upside only)
python3 retirement_projection.py --solve-spend           # max sustainable spend
python3 retirement_projection.py --monte-carlo 2000      # sequence-risk probability
```

### 3a. Roth-conversion drag — the single biggest correction to the base case

The baseline taxes pre-tax withdrawals at a flat **12% forever** and ignores
conversion taxes. That 12% is only achievable *because* of the conversion
strategy — so the baseline was quietly double-counting the benefit while
skipping the cost. Modeling $190k/yr conversions at a 19% blended rate
(watchlist's realistic estimate) during 2034–2043:

| World ($13k/mo, retire 55, 5% real) | Dies with |
|---|---|
| Naive baseline (12% forever, no conversion cost) | $4.02M |
| **With conversions modeled (19% cost, then tax-free)** | **$3.43M** |
| No conversions, withdrawals realistically taxed 18% | $3.24M |
| No conversions, withdrawals + RMDs at 22% | $2.71M |

Three takeaways: (1) the honest base case is **~$3.4M, not ~$4.0M** — use
`--conversions` as the default lens going forward; (2) the conversion strategy
is confirmed **value-positive** by $0.2–0.7M vs realistic no-conversion worlds,
and it fully drains the pre-tax pile by 67 (RMD problem eliminated — answers
watchlist #2); (3) the **$12k floor survives even the stress case with
conversion drag included** (ends +$549k), so the plan's core verdict stands.
Conversions pull bridge exhaustion forward ~1 year (during Dan-58); Roth
basis/Rule of 55 cover the gap.

### 3b. Sequence-of-returns risk, finally quantified (Monte Carlo)

The old proxy ("4% real = stress") is a *trend* stress, not a *sequence*
stress. The Monte Carlo layer draws lognormal real returns with the **median
path equal to the deterministic 5% path**, so failure probability isolates
volatility/sequence risk around the same long-run trend. Seeded —
reproducible run-to-run, and the baseline result is pinned in the tests.

| Retire 55, vol 16% (≈all-equity), 2000 paths | Success | Median ending |
|---|---|---|
| $12k/mo | 68% | $4.6M |
| $13k/mo | 61% | $2.8M |
| $14k/mo | 55% | $1.4M |
| $13k/mo at vol 12% (≈70/30 portfolio) | 66% | $3.3M |
| $13k/mo at vol 10% (≈60/40 portfolio) | 71% | $3.6M |
| $13k/mo with a permanent −10% spend cut | 70% | — |

Median depletion age among failures: **Dan ~72** — failures are concentrated in
the first ~15 retirement years, the classic sequence-risk window.

**How to read this honestly — it is NOT "the plan is 61% likely to work":**
- The MC assumes **rigidly static spending** — no human cuts $0 of a $156k
  budget while watching their portfolio die for 15 straight years. The
  −10%-cut row shows even crude flexibility buys ~9 points; real guardrail
  behavior (cut when below trajectory, restore when above) buys far more.
- **None of the uncounted buffers participate**: delaying SS to 70, the
  mortgage dropping off ~2049, inheritance, $134k cash, part-time income.
- i.i.d. draws ignore mean reversion, which historically softens long-horizon
  tails — i.i.d. is the pessimistic convention.

What it IS telling you, and the two real decisions it sharpens:
1. **Volatility is now a first-class lever.** Moving from all-equity (16%)
   toward 60/40 (10%) in the years around 2034 is worth roughly as much
   success probability as cutting spend $1k/mo — this is the quantitative
   case for a glidepath/bond-tent before and just after retirement, which the
   plan currently doesn't have. Worth designing at the next annual review.
2. **The $12k floor + willingness to flex is what makes the plan robust** —
   exactly the original verdict, but now with a number on *why* the
   flexibility matters (rigid $13k: 61%; flexible: comfortably 75%+ before
   counting any buffer).

### 3c. Other stresses (all pass)

| Scenario | Result |
|---|---|
| SS cut 20%, $13k/mo base | OK — ends $2.98M |
| SS cut 20%, $12k/mo, 4% real + $30k savings (kitchen sink) | OK — ends $33k (razor-thin: this is the true edge of the plan) |
| First death at Dan 70 / 75 / 80 ($13k base; survivor keeps larger SS, single brackets, 75% spend) | OK — ending ≈ unchanged (~$4.0M); spend drop ≈ offsets SS + tax loss |
| Survivor at 75 under stress (4%, $12k) | OK — ends $1.0M |

The survivor result partially answers watchlist #4: the plan is robust to a
first death under these crude assumptions. (Terri's actual SSA estimate is
still worth pulling — it feeds the non-survivor base case too.)

### 3d. Gap-year side income (`--side-income`) — upside, never load-bearing

Added to *factor* a possible age-55–65 side hustle (see
`preretirement_income_strategy.md`), explicitly **not** to depend on one — so
it is off by default and the pinned baseline is untouched. Gross earned income
in a window (default Dan 55–60 = 2034–2039, the bridge years) is netted for
tax (default 25% effective: SE tax + modest federal + CO) and used to offset
that year's portfolio draw — first the conversion-tax drag, then living costs.
This directly answers strategy-doc §8 Q1.

| Scenario (retire 55, $13k/mo) | Result |
|---|---|
| Base case, **$50k/yr** side income 2034–39 | bridge exhausts a year later (Dan 60 vs 59); ends **$5.69M vs $4.02M** (+$1.66M) |
| Stress (4% real, $30k savings) **+ conversions**, no side income | **FAILS** (depletes) |
| Same stress **+ $50k/yr side income** | **survives**, ends +$288k |

The takeaway matches the strategy doc's thesis: income *during the
sequence-risk window* is worth far more than its face value — a failing stress
path becomes a surviving one. Two honest limits, by design: (1) any side income
beyond the year's need is **not** reinvested (conservative — keeps it from
flattering the plan); (2) it does **not** auto-throttle Roth conversions to
stay in-bracket — that annual tax-optimization is the §8/CPA question, not
something a flat-rate model should fake. Tune the tax rate and window with the
CPA when real numbers exist.

### 3e. SS claim age (`--ss-claim-age`) — longevity hedge, not fragility hedge

The model now scales the Social Security benefit by claim age using the
standard SSA actuarial rules, applied to the canonical age-67 (FRA) figures
(so no separately-sourced number is needed per age): **+8%/yr delayed credit
past FRA, capped at 70 (1.24×); 5/9%/mo then 5/12%/mo early reduction (0.70× at
62).** Default is 67 (factor 1.0 → baseline untouched). Both spouses claim at
the same age; the conversion window auto-extends to the claim age.

| Path (retire 55, honest base) | Claim 62 | Claim 67 | Claim 70 |
|---|--:|--:|--:|
| Ends at 95 with | $3.18M | $3.43M | **$3.53M** |

**The non-obvious finding:** delaying to 70 helps the base case (+~$104k) but
does **not** rescue the failing stress path (it still depletes at 88). Reason:
delaying means three extra years (67–70) of drawing the portfolio with *no* SS,
which lands exactly when a stress-case portfolio is most fragile and roughly
cancels the larger later checks. So the backstops sort into two kinds:
**fragility hedges** that fix a bad-returns decade (the ~$35k/yr side hustle,
the $12k floor — both rescue the stress case) and **longevity hedges** that pay
off only with a long life and protect the survivor (delayed SS — does not).
Caveats: Terri's age-70 benefit is an actuarial estimate (her ssa.gov figure
isn't on file), and the textbook-optimal move is often to delay only the higher
earner; the model delays both to one age for simplicity.

## 4. The regression suite (`test_retirement_model.py`)

| Layer | What turns red if… |
|---|---|
| Golden numbers | …any code change alters a number the plan documents cite |
| Plan consistency | …`retirement_plan.yaml` targets/assumptions drift from what the code computes (parses the YAML directly) |
| Cross-validation | …the engine disagrees with independent closed-form/hand-rolled re-derivations of the same spec |
| Properties | …a change breaks directional sanity (more return ⇒ retire earlier; draws conserve value; overlays move results the right way) |
| Monte Carlo | …the RNG stream or engine changes (pinned seeded result) |

**Annual check-in ritual, v2** (each Jan 1):
1. `python3 -m unittest` → must be green *before* you look at any number.
2. Fill the year's checkpoint in `retirement_plan.yaml`; compare actual vs target.
3. `python3 retirement_projection.py --conversions` (honest base) and
   `--monte-carlo 2000` (risk view); stress with `--return 0.04 --taxable 30000`.
4. When facts change (balances, salary, SS estimate): edit the constants in
   `retirement_projection.py`, regenerate the YAML trajectory, and update the
   pinned goldens **in the same commit** — a red suite is the reminder.

## 5. Still simplified, in (rough) order of materiality

1. **Flat effective tax rates** (no brackets). The `--conversions` overlay
   bounds the error, but a real bracket engine (fed + CO + NIIT + IRMAA) is
   the next-biggest upgrade if you want one. Watchlist #1's "build a
   conversion-year tax worksheet at first retired review" still stands.
2. **ACA/health**: $15k/person is a placeholder (watchlist #3) — `--health`
   now lets you stress it (e.g. `--health 22000`).
3. **No glidepath**: the model grows every bucket at one rate; the MC vol
   findings above argue for modeling a bond tent eventually.
4. **Annual timing, i.i.d. returns, no mean reversion** — conservative-leaning
   conventions, fine for purpose.
5. **RMDs**: irrelevant in the `--conversions` world (pile is drained by 67);
   only the naive baseline ignores them — one more reason to prefer
   `--conversions` as the default lens.

#!/usr/bin/env python3
"""Retirement projection for Dan & Terri Grindall.

Solves for the EARLIEST feasible retirement age and stress-tests the answer
against investment-return and savings-rate assumptions.

Everything is in TODAY'S DOLLARS (real terms): returns are real (nominal minus
inflation), spending is constant real, Social Security estimates from ssa.gov
are already quoted in today's dollars. This keeps the output readable without
an inflation lens.

The DEFAULT run is deterministic and reproduces the numbers pinned in
retirement_plan.yaml and test_retirement_model.py (run `python3 -m unittest`
to verify — green tests mean the model still says what the plan documents say).

Optional layers (off by default so the pinned baseline never moves):
  --monte-carlo N    sequence-of-returns risk as a success probability
                     (lognormal real returns; median path = deterministic path)
  --conversions      explicit Roth-conversion tax drag (watchlist item #1)
  --ss-haircut X     benefit cut stress (plan assumption knob, e.g. 0.20)
  --ss-claim-age AGE claim Social Security at AGE (62-70); benefit adjusts for
                     delayed credits / early reduction (default 67 = FRA)
  --survivor-at AGE  first-death scenario: one SS benefit, single brackets
  --side-income $    factor (never depend on) gap-year side-hustle income;
                     offsets bridge draws in the window (default ages 55-60)
  --solve-spend      bisect the max sustainable spend for the given knobs
  --savings-table    print the year-by-year itemized contribution schedule
                     (per-vessel dials: --base-salary, --k401-pct, --match-pct,
                     --k401-topoff, --dan-roth, --terri-taxable,
                     --terri-solo-401k, --terri-trad-ira)
"""

import argparse
import math
import random
from dataclasses import dataclass, replace
from typing import Optional

# ---------------------------------------------------------------------------
# INPUTS — edit these as facts change
# ---------------------------------------------------------------------------

CURRENT_YEAR = 2026
DAN_AGE = 47
TERRI_AGE = 49
PLAN_TO_DAN_AGE = 95          # model through Dan age 95 (Terri 97)

# Starting investable balances by tax treatment (May 2026 screenshots).
# Excludes: 529s ($115k), kids' UTMA ($3.6k), and ~$134k cash buffer
# (~$84k now + incoming $50k gift). All of those are UPSIDE not modeled here.
START_TAX_DEFERRED = 946_496   # old 401ks + rollover/trad IRAs (taxed at withdrawal)
                               # = $794,274 (Rocket Money) + $152,222 Terri IRA (...36, off-RM)
START_ROTH         = 327_070   # Roth IRAs (tax-free)
START_TAXABLE      = 172_992   # Vanguard joint brokerage 7157

# Annual contributions while working (real $) — see annual_contributions() and
# the per-vessel dials on Params. The defaults below reproduce the prior
# hardcoded schedule exactly (so the validated baseline never moves):
#   Dan 401k employee maxed (24k, ->31.5k catch-up at 50) via 4%-of-base + bonus
#   top-off; employer match 4% of base; Dan backdoor Roth 7k (->8k at 50);
#   Terri's would-be IRA ($7-8k) redirected to TAXABLE (she's not backdoor-clean).
BASE_SALARY_DEFAULT  = 222_000   # current annualized base (update on raises/job change)
K401_EMPLOYEE_PCT    = 0.04      # % of base withheld to the 401k from paychecks
K401_MATCH_PCT       = 0.04      # employer match, % of base
K401_LIMIT_UNDER50   = 24_000    # IRS elective-deferral limit (model figure)
K401_LIMIT_50PLUS    = 31_500    # with age-50 catch-up
IRA_LIMIT_UNDER50    = 7_000
IRA_LIMIT_50PLUS     = 8_000
MATCH_401K = 8_880               # legacy constant (= 4% of $222k); kept for reference
TAXABLE_SAVINGS = 50_000       # surplus bonus invested/yr (Terri's ~$7-8k IRA
                               # redirect is added automatically -> ~$57-58k total).
                               # KEY LEVER: also sizes the penalty-free 55-59.5 bridge.

# Growth (REAL = nominal ~7-8% minus ~3% inflation).
REAL_RETURN = 0.05

# Spending in retirement (real $/yr, ALL-IN including the 2.75% mortgage,
# which per your note stays until an inheritance windfall pays it off — that
# payoff is treated as upside, not assumed here).
SPEND = 156_000   # $13k/mo — the planning midpoint of the $12-14k goal.
                  # $12k and $14k are stress-tested in the spend table below.
HEALTH_BRIDGE_PER_PERSON = 15_000   # private health insurance until age 65

# Social Security (today's $, benefit at Full Retirement Age = 67).
# Dan from ssa.gov: $2,851 @62, $4,223 @67 (FRA), $5,266 @70.
DAN_SS_ANNUAL_AT_67   = 50_676      # $4,223/mo (ssa.gov)
TERRI_SS_ANNUAL_AT_67 = 33_784      # ~2/3 of Dan, $2,815/mo
SS_FRA = 67                         # Full Retirement Age (the canonical figures above)
SS_CLAIM_AGE = 67                   # default claim age = FRA (benefit factor = 1.0)

# Retirement tax approximation (effective rates on withdrawals/SS).
TAX_DEFERRED_RATE  = 0.12     # ordinary income on pre-tax withdrawals
TAXABLE_GAINS_RATE = 0.075    # ~15% LTCG on ~50% embedded gains
SS_TAX_RATE        = 0.10     # ~85% of SS taxable, low bracket

# Roth-conversion drag (used only with --conversions). The plan converts
# ~$190k/yr in 2034-2043 filling the 22% bracket; the watchlist (#1) puts the
# realistic blended cost at ~18-22% (fed + NIIT in big years + CO ~4.4%).
CONV_AMOUNT_DEFAULT   = 190_000
CONV_TAX_RATE_DEFAULT = 0.19

# Survivor scenario (used only with --survivor-at). Crude but parameterized:
# household keeps the LARGER SS benefit, spending drops (one person), and
# tax rates rise (single filer brackets — the "widow's penalty").
SURVIVOR_SPEND_FACTOR   = 0.75
SURVIVOR_DEFERRED_RATE  = 0.20
SURVIVOR_SS_TAX_RATE    = 0.12

# Monte Carlo defaults (used only with --monte-carlo). Log-return sigma ~0.16
# approximates a heavily-equity portfolio. mu = ln(1+real_return), so the
# MEDIAN Monte Carlo path equals the deterministic path — failure probability
# then isolates sequence-of-returns / volatility risk around the same trend.
MC_VOL_DEFAULT  = 0.16
MC_SEED_DEFAULT = 42

# Side-hustle income (used only with --side-income). DELIBERATELY OFF BY
# DEFAULT: the plan must never DEPEND on a side hustle — this only lets you
# FACTOR it if it happens. Gross earned income (today's $) during the gap
# years; the model nets it for taxes and uses it to offset portfolio draws
# (and any conversion-tax drag) in those years — directly extending the
# 55-59.5 bridge and hedging sequence-of-returns risk, exactly when it helps
# most. The default window 55-60 = calendar 2034-2039 (the bridge).
SIDE_INCOME_START_AGE = 55
SIDE_INCOME_END_AGE   = 60          # inclusive; Dan 55=2034 ... Dan 60=2039
SIDE_INCOME_TAX_RATE  = 0.25        # SE tax (~15.3%, half deductible) + modest
                                    # federal ordinary + CO ~4.4%, blended. A
                                    # deliberately conservative effective rate;
                                    # real net is likely higher. Tune w/ CPA.


# ---------------------------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Params:
    """Everything simulate() needs. Defaults reproduce the pinned baseline."""
    real_return: float = REAL_RETURN
    taxable_savings: float = TAXABLE_SAVINGS
    spend: float = SPEND
    health_per_person: float = HEALTH_BRIDGE_PER_PERSON
    ss_claim_age: int = SS_CLAIM_AGE
    ss_haircut: float = 0.0            # 0.20 = benefits cut 20% (plan stress knob)
    # starting balances (overridable for tests / what-ifs)
    start_tax_deferred: float = START_TAX_DEFERRED
    start_roth: float = START_ROTH
    start_taxable: float = START_TAXABLE
    # effective tax rates
    tax_deferred_rate: float = TAX_DEFERRED_RATE
    taxable_gains_rate: float = TAXABLE_GAINS_RATE
    ss_tax_rate: float = SS_TAX_RATE
    # Roth-conversion drag (off by default)
    conversions: bool = False
    conv_amount: float = CONV_AMOUNT_DEFAULT
    conv_tax_rate: float = CONV_TAX_RATE_DEFAULT
    # survivor scenario (off by default). At this Dan-age, drop to one person.
    survivor_at_dan_age: int = 0       # 0 = both live to plan horizon
    survivor_spend_factor: float = SURVIVOR_SPEND_FACTOR
    survivor_deferred_rate: float = SURVIVOR_DEFERRED_RATE
    survivor_ss_tax_rate: float = SURVIVOR_SS_TAX_RATE
    # side-hustle income (off by default — pure upside, never depended on)
    side_income: float = 0.0           # gross earned income/yr in the window
    side_income_start_age: int = SIDE_INCOME_START_AGE
    side_income_end_age: int = SIDE_INCOME_END_AGE
    side_income_tax_rate: float = SIDE_INCOME_TAX_RATE
    # ---- SAVINGS DIALS (year-over-year planning) -------------------------
    # Each contribution vessel is its own knob. Defaults reproduce the prior
    # schedule exactly. `None` on a dial means "use the built-in default
    # schedule" (incl. age-50 catch-ups); a number pins that vessel flat.
    base_salary: float = BASE_SALARY_DEFAULT       # drives 401k % and match %
    k401_employee_pct: float = K401_EMPLOYEE_PCT   # of base, from paychecks
    k401_match_pct: float = K401_MATCH_PCT         # employer match, of base
    k401_topoff: Optional[float] = None            # $ from bonus; None = fill to IRS max
    dan_roth_ira: Optional[float] = None           # None = 7k/8k schedule (backdoor)
    terri_taxable: Optional[float] = None          # her redirect -> TAXABLE; None = 7k/8k
    terri_solo_401k: float = 0.0                   # DEDUCTIBLE pre-tax -> tax-deferred bucket
    terri_trad_ira: float = 0.0                    # NON-deductible -> own basis-tracked bucket


# ---------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------

def ss_benefit_factor(claim_age, fra=SS_FRA):
    """Multiplier on the FRA (age-67) benefit for claiming at `claim_age`.

    Uses the standard SSA actuarial adjustments, applied to the canonical
    age-67 figures so we never need a separately-sourced number per claim age:

      * Delayed Retirement Credits: +8%/yr for each year past FRA, capped at
        age 70 (no further credit after 70). Claim at 70 = 1.24x.
      * Early-claiming reduction: 5/9 of 1%/mo for the first 36 months early,
        then 5/12 of 1%/mo beyond that. Claim at 62 = 0.70x.

    Claim age is clamped to SSA's 62-70 window. (The model uses the textbook
    8%/yr DRC, marginally conservative vs Dan's actual ssa.gov $5,266 @70.)
    """
    claim_age = max(62, min(70, claim_age))
    if claim_age >= fra:
        return 1.0 + 0.08 * (claim_age - fra)
    months_early = (fra - claim_age) * 12
    first = min(months_early, 36)
    beyond = max(0, months_early - 36)
    reduction = first * (5/9) / 100 + beyond * (5/12) / 100
    return 1.0 - reduction


def annual_contributions(p, dan_age, terri_age):
    """Itemized contributions for one working year, by VESSEL (not bucket).

    Returns a dict keyed by vessel; `bucketize()` collapses it to the
    (tax_deferred, roth, taxable, nondeduct_ira) the engine grows. Every value
    derives from the dials on `p`; the defaults reproduce the prior schedule.
    """
    k401_limit = K401_LIMIT_UNDER50 if dan_age < 50 else K401_LIMIT_50PLUS
    from_base = p.base_salary * p.k401_employee_pct
    topoff = (max(0.0, k401_limit - from_base) if p.k401_topoff is None
              else p.k401_topoff)
    dan_401k_employee = min(k401_limit, from_base + topoff)   # can't exceed IRS limit
    actual_from_base = min(from_base, dan_401k_employee)

    dan_ira_limit   = IRA_LIMIT_UNDER50 if dan_age   < 50 else IRA_LIMIT_50PLUS
    terri_ira_limit = IRA_LIMIT_UNDER50 if terri_age < 50 else IRA_LIMIT_50PLUS
    dan_roth      = dan_ira_limit   if p.dan_roth_ira  is None else p.dan_roth_ira
    terri_tax     = terri_ira_limit if p.terri_taxable is None else p.terri_taxable

    return {
        "dan_401k_from_base":   actual_from_base,
        "dan_401k_topoff":      dan_401k_employee - actual_from_base,
        "employer_match":       p.base_salary * p.k401_match_pct,
        "dan_backdoor_roth":    dan_roth,
        "terri_solo_401k":      p.terri_solo_401k,        # deductible pre-tax
        "terri_trad_ira":       p.terri_trad_ira,         # non-deductible
        "terri_taxable":        terri_tax,                # her redirect to taxable
        "taxable_surplus":      p.taxable_savings,        # bonus surplus
    }


def bucketize(items):
    """Collapse the itemized vessels into the four engine buckets."""
    tax_deferred = (items["dan_401k_from_base"] + items["dan_401k_topoff"]
                    + items["employer_match"] + items["terri_solo_401k"])
    roth = items["dan_backdoor_roth"]
    taxable = items["taxable_surplus"] + items["terri_taxable"]
    nondeduct_ira = items["terri_trad_ira"]
    return tax_deferred, roth, taxable, nondeduct_ira


def savings_schedule(p, ret_dan_age=55):
    """Year-by-year itemized contributions (today's $) for the working years.

    Returns (rows, totals): each row is a dict with the year, ages, every
    vessel amount, and the four bucket subtotals; `totals` sums each vessel and
    bucket across all working years. Pure reporting — used by --savings-table
    and as the data source for any dashboard.
    """
    rows = []
    dan, terri, year = DAN_AGE, TERRI_AGE, CURRENT_YEAR
    while dan < ret_dan_age:
        items = annual_contributions(p, dan, terri)
        td, roth, tax, nd = bucketize(items)
        row = {"year": year, "dan": dan, "terri": terri,
               **items,
               "_tax_deferred": td, "_roth": roth, "_taxable": tax,
               "_nondeduct_ira": nd, "_total": td + roth + tax + nd}
        rows.append(row)
        dan += 1; terri += 1; year += 1
    keys = list(rows[0].keys()) if rows else []
    totals = {k: sum(r[k] for r in rows) for k in keys
              if k not in ("year", "dan", "terri")}
    return rows, totals


def _draw(need_net, buckets):
    """Draw `need_net` (after-tax dollars) from buckets in priority order.

    buckets: list of dicts {name, bal, net_factor}. net_factor is the after-tax
    value of $1 withdrawn. Mutates balances. Returns unmet shortfall (>0 = fail).
    """
    remaining = need_net
    for b in buckets:
        if remaining <= 1e-6:
            break
        net_possible = b["bal"] * b["net_factor"]
        take_net = min(remaining, net_possible)
        b["bal"] -= take_net / b["net_factor"]
        remaining -= take_net
    return remaining


def simulate(ret_dan_age, real_return=None, taxable_savings=None, record=False,
             params=None, returns=None):
    """Run one life path. Returns (survived: bool, ending_balance, history).

    `params` is a Params; `real_return`/`taxable_savings` are kept as
    positional conveniences and override the corresponding Params fields.
    `returns` is an optional per-year sequence of real returns indexed by
    (year - CURRENT_YEAR); when given it overrides the constant return
    (used by monte_carlo).
    """
    p = params or Params()
    if real_return is not None:
        p = replace(p, real_return=real_return)
    if taxable_savings is not None:
        p = replace(p, taxable_savings=taxable_savings)

    td, roth, tax = p.start_tax_deferred, p.start_roth, p.start_taxable
    nd_ira, nd_basis = 0.0, 0.0     # Terri's non-deductible trad IRA (+ its basis)
    dan, terri, year = DAN_AGE, TERRI_AGE, CURRENT_YEAR
    history = []
    survived = True

    # Benefit scales with claim age (delayed credits / early reduction), then
    # the optional policy haircut. Both spouses claim at the same AGE, so each
    # benefit simply starts in the year that person reaches p.ss_claim_age.
    ss_factor = ss_benefit_factor(p.ss_claim_age)
    dan_ss   = DAN_SS_ANNUAL_AT_67   * ss_factor * (1 - p.ss_haircut)
    terri_ss = TERRI_SS_ANNUAL_AT_67 * ss_factor * (1 - p.ss_haircut)

    while dan <= PLAN_TO_DAN_AGE:
        retired = dan >= ret_dan_age
        survivor = bool(p.survivor_at_dan_age) and dan >= p.survivor_at_dan_age
        td_rate = p.survivor_deferred_rate if survivor else p.tax_deferred_rate
        ss_tax  = p.survivor_ss_tax_rate  if survivor else p.ss_tax_rate

        if not retired:
            c_td, c_roth, c_tax, c_nd = bucketize(annual_contributions(p, dan, terri))
            td += c_td; roth += c_roth; tax += c_tax
            nd_ira += c_nd; nd_basis += c_nd        # non-deductible -> all basis going in
        else:
            need = p.spend * (p.survivor_spend_factor if survivor else 1.0)
            if survivor:
                # one person left; one health bridge if they're still pre-65
                if dan < 65:
                    need += p.health_per_person
            else:
                if dan < 65:   need += p.health_per_person
                if terri < 65: need += p.health_per_person

            ss = 0.0
            if survivor:
                # survivor keeps the larger of the two benefits
                if dan >= p.ss_claim_age:
                    ss = max(dan_ss, terri_ss)
            else:
                if dan >= p.ss_claim_age:   ss += dan_ss
                if terri >= p.ss_claim_age: ss += terri_ss
            ss_net = ss * (1 - ss_tax)

            net_need = max(0.0, need - ss_net)

            # Roth-conversion drag: move pre-tax -> Roth during the pre-SS
            # window and pay the conversion tax out of the portfolio (it joins
            # the year's draw, so it is itself grossed-up for cap-gains when
            # funded by selling taxable shares — matching reality).
            if p.conversions and dan < p.ss_claim_age and td > 0:
                conv = min(td, p.conv_amount)
                td -= conv
                roth += conv
                net_need += conv * p.conv_tax_rate

            # Side-hustle income (off by default). Net of tax, it offsets the
            # year's draw — first the conversion-tax drag, then living costs.
            # Floored at 0: any excess beyond the year's need is NOT modeled as
            # reinvested (conservative, so the plan never leans on it). This
            # does NOT auto-throttle conversions to stay in-bracket — that
            # tax-optimization is the CPA/§8 question, not something a flat-rate
            # model should fake.
            if p.side_income and p.side_income_start_age <= dan <= p.side_income_end_age:
                net_need = max(0.0, net_need -
                               p.side_income * (1 - p.side_income_tax_rate))

            # Non-deductible IRA: basis comes back tax-free, only the growth is
            # taxed at the ordinary (deferred) rate. Net factor is dynamic with
            # the basis fraction. (Default nd_ira=0 -> this bucket is inert, so
            # every validated number is unchanged.)
            nd_growth_frac = max(0.0, nd_ira - nd_basis) / nd_ira if nd_ira > 1e-9 else 0.0
            nd_factor = 1 - nd_growth_frac * td_rate
            buckets = [
                {"name": "taxable",  "bal": tax,    "net_factor": 1 - p.taxable_gains_rate},
                {"name": "nd_ira",   "bal": nd_ira, "net_factor": nd_factor},
                {"name": "deferred", "bal": td,     "net_factor": 1 - td_rate},
                {"name": "roth",     "bal": roth,   "net_factor": 1.0},
            ]
            nd_before = nd_ira
            shortfall = _draw(net_need, buckets)
            tax, nd_ira, td, roth = (buckets[0]["bal"], buckets[1]["bal"],
                                     buckets[2]["bal"], buckets[3]["bal"])
            if nd_before > 1e-9:           # shrink basis in proportion to balance drawn
                nd_basis *= nd_ira / nd_before
            if shortfall > 1e-6:
                survived = False

        # Year-end growth on remaining balances (basis does not grow).
        r = returns[year - CURRENT_YEAR] if returns is not None else p.real_return
        td   *= (1 + r)
        roth *= (1 + r)
        tax  *= (1 + r)
        nd_ira *= (1 + r)

        total = td + roth + tax + nd_ira
        if record:
            history.append((year, dan, terri, total, td, roth, tax))
        if total <= 0 or not survived:
            return False, max(0.0, total), history

        dan += 1; terri += 1; year += 1

    return True, total, history


def earliest_age(real_return=None, taxable_savings=None, params=None):
    for age in range(DAN_AGE + 1, SS_CLAIM_AGE + 1):
        ok, _, _ = simulate(age, real_return, taxable_savings, params=params)
        if ok:
            return age
    return None


def max_sustainable_spend(ret_age, params=None, lo=60_000, hi=400_000):
    """Bisect the largest annual spend that survives to the plan horizon."""
    p = params or Params()
    for _ in range(60):
        mid = (lo + hi) / 2
        ok, _, _ = simulate(ret_age, params=replace(p, spend=mid))
        if ok:
            lo = mid
        else:
            hi = mid
    return lo


def spend_feasibility_rows(retire_age=55, params=None):
    """For each monthly spend goal, test age-`retire_age` survival under base &
    stress, plus the earliest feasible age."""
    p = params or Params()
    rows = []
    for annual in (144_000, 156_000, 168_000):
        base   = replace(p, spend=annual, real_return=0.05, taxable_savings=50_000)
        stress = replace(p, spend=annual, real_return=0.04, taxable_savings=30_000)
        ok_b, end_b, _ = simulate(retire_age, params=base)
        ok_s, end_s, _ = simulate(retire_age, params=stress)
        rows.append((annual, ok_b, end_b, ok_s, end_s, earliest_age(params=base)))
    return rows


def monte_carlo(ret_age, params=None, n_paths=2_000, vol=MC_VOL_DEFAULT,
                seed=MC_SEED_DEFAULT):
    """Sequence-of-returns risk via i.i.d. lognormal real returns.

    mu = ln(1 + real_return), so the MEDIAN path compounds at exactly the
    deterministic rate — failure probability isolates volatility/sequence
    risk around the same long-run trend (the arithmetic mean return is then
    slightly higher, ~ real_return + vol^2/2).

    Returns dict: success_rate, ending-balance percentiles (p10/p50/p90 over
    ALL paths, failures counted as $0), median failure age among failures.
    """
    p = params or Params()
    rng = random.Random(seed)
    mu = math.log(1 + p.real_return)
    horizon = PLAN_TO_DAN_AGE - DAN_AGE + 1

    endings, fail_ages = [], []
    successes = 0
    for _ in range(n_paths):
        seq = [math.exp(rng.gauss(mu, vol)) - 1 for _ in range(horizon)]
        ok, end, hist = simulate(ret_age, params=p, returns=seq, record=True)
        if ok:
            successes += 1
            endings.append(end)
        else:
            endings.append(0.0)
            fail_ages.append(hist[-1][1])   # Dan's age in the depletion year
    endings.sort()

    def pct(q):
        return endings[min(len(endings) - 1, int(q * len(endings)))]

    fail_ages.sort()
    return {
        "n": n_paths,
        "success_rate": successes / n_paths,
        "p10": pct(0.10), "p50": pct(0.50), "p90": pct(0.90),
        "median_fail_age": fail_ages[len(fail_ages) // 2] if fail_ages else None,
    }


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def fmt(n):
    return f"${n:,.0f}"


def print_savings_table(p, ret_dan_age=55):
    """Itemized year-by-year savings schedule — the year-over-year planning view."""
    rows, totals = savings_schedule(p, ret_dan_age)
    print("=" * 92)
    print(f"SAVINGS SCHEDULE — by vessel, today's $ — base ${p.base_salary:,.0f}, "
          f"retire at Dan {ret_dan_age}")
    print("=" * 92)
    cols = [("dan_401k_from_base", "401k(base)"), ("dan_401k_topoff", "401k(topoff)"),
            ("employer_match", "match"), ("dan_backdoor_roth", "Dan Roth"),
            ("terri_solo_401k", "T solo401k"), ("terri_trad_ira", "T tradIRA"),
            ("terri_taxable", "T taxable"), ("taxable_surplus", "tax surplus")]
    hdr = f"{'Year':<6}{'Dan':<4}" + "".join(f"{label:>15}" for _, label in cols) + f"{'TOTAL':>13}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        line = f"{r['year']:<6}{r['dan']:<4}" + "".join(f"{r[k]:>15,.0f}" for k, _ in cols)
        print(line + f"{r['_total']:>13,.0f}")
    print("-" * len(hdr))
    tline = f"{'TOTAL':<10}" + "".join(f"{totals[k]:>15,.0f}" for k, _ in cols)
    print(tline + f"{totals['_total']:>13,.0f}")
    print()
    print("By tax bucket (where each dollar lands, and how it's taxed at withdrawal):")
    print(f"  Tax-deferred (401k+match+T solo-401k): {fmt(totals['_tax_deferred'])}"
          f"   — DEDUCTIBLE now; taxed as income at withdrawal")
    print(f"  Roth (Dan backdoor):                   {fmt(totals['_roth'])}"
          f"   — after-tax now; tax-FREE forever")
    print(f"  Taxable (surplus + T redirect):        {fmt(totals['_taxable'])}"
          f"   — after-tax; LTCG on gains; step-up at death")
    print(f"  Non-deductible IRA (T trad IRA):       {fmt(totals['_nondeduct_ira'])}"
          f"   — after-tax basis; growth taxed as income")
    print(f"  {'-'*70}")
    print(f"  TOTAL saved over {len(rows)} working years:    {fmt(totals['_total'])}")
    print()
    print("NOTES / caveats for the year-over-year conversation:")
    print("  • Terri's TRADITIONAL IRA is NON-deductible at your income (over the MFJ")
    print("    phase-out) — no deduction now, and it triggers the pro-rata rule. The model")
    print("    credits its basis back tax-free but CANNOT see pro-rata, step-up, or the")
    print("    contribution-time deduction. Taxable usually wins for Terri; the genuinely")
    print("    deductible pre-tax route is her SOLO-401(k) off consulting income.")
    print("  • The model differentiates vessels only at WITHDRAWAL (it doesn't tax")
    print("    contributions), so use it for allocation/longevity — not deductible-vs-not")
    print("    tax arbitrage. Confirm the tax specifics with the CPA.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--return", dest="ret", type=float, default=REAL_RETURN,
                    help="real return assumption (default 0.05)")
    ap.add_argument("--taxable", type=float, default=TAXABLE_SAVINGS,
                    help="annual taxable savings (default 50000)")
    ap.add_argument("--spend", type=float, default=SPEND,
                    help="annual retirement spend, today's $ (default 156000 = $13k/mo)")
    ap.add_argument("--health", type=float, default=HEALTH_BRIDGE_PER_PERSON,
                    help="pre-65 health cost per person/yr (default 15000)")
    ap.add_argument("--ss-haircut", type=float, default=0.0,
                    help="Social Security benefit cut, e.g. 0.20 (default 0)")
    ap.add_argument("--ss-claim-age", type=int, default=SS_CLAIM_AGE,
                    help="age both claim SS, 62-70; benefit adjusts for delayed "
                         "credits/early reduction (default 67 = FRA)")
    ap.add_argument("--retire-age", type=int, default=55,
                    help="Dan retirement age for --solve-spend / --monte-carlo (default 55)")
    ap.add_argument("--conversions", action="store_true",
                    help="model Roth-conversion tax drag during the pre-SS window")
    ap.add_argument("--conv-amount", type=float, default=CONV_AMOUNT_DEFAULT,
                    help="annual Roth conversion, today's $ (default 190000)")
    ap.add_argument("--conv-tax", type=float, default=CONV_TAX_RATE_DEFAULT,
                    help="blended tax rate on conversions (default 0.19)")
    ap.add_argument("--survivor-at", type=int, default=0,
                    help="Dan age at first death; survivor keeps larger SS, "
                         "single brackets, spend x%.2f (default off)" % SURVIVOR_SPEND_FACTOR)
    ap.add_argument("--side-income", type=float, default=0.0,
                    help="gross side-hustle income/yr, today's $ (default 0 = "
                         "not modeled; pure upside, never depended on)")
    ap.add_argument("--side-income-start", type=int, default=SIDE_INCOME_START_AGE,
                    help="Dan age side income starts (default 55 = 2034)")
    ap.add_argument("--side-income-end", type=int, default=SIDE_INCOME_END_AGE,
                    help="Dan age side income ends, inclusive (default 60 = 2039)")
    ap.add_argument("--side-income-tax", type=float, default=SIDE_INCOME_TAX_RATE,
                    help="blended effective tax rate on side income (default 0.25)")
    ap.add_argument("--solve-spend", action="store_true",
                    help="bisect max sustainable annual spend at --retire-age")
    ap.add_argument("--monte-carlo", type=int, default=0, metavar="N",
                    help="run N random-return paths at --retire-age")
    ap.add_argument("--vol", type=float, default=MC_VOL_DEFAULT,
                    help="Monte Carlo log-return volatility (default 0.16)")
    ap.add_argument("--seed", type=int, default=MC_SEED_DEFAULT,
                    help="Monte Carlo random seed (default 42)")
    # ---- savings dials (year-over-year planning) ----
    ap.add_argument("--base-salary", type=float, default=BASE_SALARY_DEFAULT,
                    help="annual base salary, today's $ (drives 401k %% + match; default 222000)")
    ap.add_argument("--k401-pct", type=float, default=K401_EMPLOYEE_PCT,
                    help="401k employee deferral as %% of base (default 0.04)")
    ap.add_argument("--match-pct", type=float, default=K401_MATCH_PCT,
                    help="employer 401k match as %% of base (default 0.04)")
    ap.add_argument("--k401-topoff", type=float, default=None,
                    help="$ topped off from bonus to the 401k; default = fill to IRS max")
    ap.add_argument("--dan-roth", type=float, default=None,
                    help="Dan backdoor Roth IRA, today's $; default = 7k/8k schedule")
    ap.add_argument("--terri-taxable", type=float, default=None,
                    help="Terri's savings routed to TAXABLE, today's $; default = 7k/8k")
    ap.add_argument("--terri-solo-401k", type=float, default=0.0,
                    help="Terri solo-401k (DEDUCTIBLE pre-tax) off consulting income (default 0)")
    ap.add_argument("--terri-trad-ira", type=float, default=0.0,
                    help="Terri traditional IRA (NON-deductible at your income; default 0)")
    ap.add_argument("--savings-table", action="store_true",
                    help="print the year-by-year itemized contribution schedule and exit")
    args = ap.parse_args()

    p = Params(real_return=args.ret, taxable_savings=args.taxable,
               spend=args.spend, health_per_person=args.health,
               ss_haircut=args.ss_haircut, ss_claim_age=args.ss_claim_age,
               conversions=args.conversions, conv_amount=args.conv_amount,
               conv_tax_rate=args.conv_tax, survivor_at_dan_age=args.survivor_at,
               side_income=args.side_income,
               side_income_start_age=args.side_income_start,
               side_income_end_age=args.side_income_end,
               side_income_tax_rate=args.side_income_tax,
               base_salary=args.base_salary, k401_employee_pct=args.k401_pct,
               k401_match_pct=args.match_pct, k401_topoff=args.k401_topoff,
               dan_roth_ira=args.dan_roth, terri_taxable=args.terri_taxable,
               terri_solo_401k=args.terri_solo_401k, terri_trad_ira=args.terri_trad_ira)

    if args.savings_table:
        print_savings_table(p, args.retire_age)
        return

    start_total = START_TAX_DEFERRED + START_ROTH + START_TAXABLE
    print("=" * 70)
    print("RETIREMENT PROJECTION — Dan (47) & Terri (49) — today's dollars")
    print("=" * 70)
    print(f"Starting investable: {fmt(start_total)}")
    print(f"  Tax-deferred {fmt(START_TAX_DEFERRED)} | "
          f"Roth {fmt(START_ROTH)} | Taxable {fmt(START_TAXABLE)}")
    print(f"Spending goal: {fmt(p.spend)}/yr all-in  "
          f"(+{fmt(p.health_per_person)}/person health pre-65)")
    ssf = ss_benefit_factor(p.ss_claim_age)
    print(f"Social Security at {p.ss_claim_age}: Dan {fmt(DAN_SS_ANNUAL_AT_67 * ssf)} + "
          f"Terri {fmt(TERRI_SS_ANNUAL_AT_67 * ssf)} = "
          f"{fmt((DAN_SS_ANNUAL_AT_67 + TERRI_SS_ANNUAL_AT_67) * ssf)}/yr"
          + (f"  ({ssf:.2f}x FRA)" if p.ss_claim_age != SS_FRA else ""))
    print(f"Assumptions: {args.ret:.0%} real return, "
          f"{fmt(args.taxable)}/yr taxable savings")
    extras = []
    if p.ss_claim_age != SS_FRA: extras.append(f"SS claimed at {p.ss_claim_age} ({ss_benefit_factor(p.ss_claim_age):.2f}x)")
    if p.ss_haircut:            extras.append(f"SS haircut {p.ss_haircut:.0%}")
    if p.conversions:           extras.append(f"Roth conversions {fmt(p.conv_amount)}/yr @ {p.conv_tax_rate:.0%}")
    if p.survivor_at_dan_age:   extras.append(f"survivor scenario from Dan age {p.survivor_at_dan_age}")
    if p.side_income:
        extras.append(f"side income {fmt(p.side_income)}/yr (Dan {p.side_income_start_age}-"
                      f"{p.side_income_end_age}) @ {p.side_income_tax_rate:.0%} tax — UPSIDE, not depended on")
    if extras:
        print("Scenario overlays: " + "; ".join(extras))
    print()

    age = earliest_age(params=p)
    if age:
        years_away = age - DAN_AGE
        print(f">>> EARLIEST FEASIBLE RETIREMENT: Dan age {age} "
              f"(year {CURRENT_YEAR + years_away}, {years_away} yrs away). "
              f"Terri {TERRI_AGE + years_away}.")
    else:
        print(">>> No feasible age <= 67 under these assumptions.")
    print()

    # Outcome table for a range of retirement ages.
    print("Retire at | Portfolio at Dan-95 (real) | Result")
    print("-" * 55)
    for a in range(52, 63):
        ok, ending, _ = simulate(a, params=p)
        flag = "OK, dies with " + fmt(ending) if ok else "DEPLETES"
        print(f"  Dan {a}   | {flag}")
    print()

    # Sensitivity grid: earliest age by return x taxable savings.
    print("Sensitivity — EARLIEST retirement age (Dan):")
    print("                taxable savings/yr")
    print("  real ret |  $30k   $50k   $80k")
    print("  " + "-" * 36)
    for r in (0.04, 0.05, 0.06):
        row = [f"{r:.0%}".rjust(7) + "  |"]
        for t in (30_000, 50_000, 80_000):
            a = earliest_age(params=replace(p, real_return=r, taxable_savings=t))
            row.append(f"  {a if a else '>67'}".rjust(7))
        print("  " + "".join(row))
    print()
    print("Spend-goal feasibility retiring at 55 (today's $):")
    print("  per mo |  base (5% real,$50k)  | stress (4% real,$30k) | earliest age")
    print("  " + "-" * 64)
    for annual, ok_b, end_b, ok_s, end_s, ea in spend_feasibility_rows(55, params=p):
        b = ("OK " + fmt(end_b)) if ok_b else "FAIL"
        s = ("OK " + fmt(end_s)) if ok_s else "FAIL"
        print(f"  ${annual/12:>5,.0f} |  {b:<20} | {s:<20} | {ea}")
    print()

    if p.side_income:
        # Show the side-income effect as a DELTA against the same plan with no
        # side income — so it reads as upside, never as load-bearing.
        no_side = replace(p, side_income=0.0)
        ok0, end0, h0 = simulate(args.retire_age, params=no_side, record=True)
        ok1, end1, h1 = simulate(args.retire_age, params=p, record=True)
        net_yr = p.side_income * (1 - p.side_income_tax_rate)

        def bridge_exhaust_age(hist):
            drained = [d for (_, d, _, _, _, _, t) in hist
                       if d >= args.retire_age and t < 1]
            return min(drained) if drained else None

        ex0, ex1 = bridge_exhaust_age(h0), bridge_exhaust_age(h1)
        print(f"Side-hustle income effect (retire at Dan {args.retire_age}) — "
              f"UPSIDE ONLY, the plan does not depend on it:")
        print(f"  {fmt(p.side_income)}/yr gross, Dan {p.side_income_start_age}-"
              f"{p.side_income_end_age} → {fmt(net_yr)}/yr net @ "
              f"{p.side_income_tax_rate:.0%} tax")
        print(f"  Taxable bridge exhausts: Dan {ex0 or 'never'} (no side income)"
              f"  →  Dan {ex1 or 'never'} (with)")
        print(f"  Portfolio at Dan-95: {fmt(end0)} (no side income)  →  "
              f"{fmt(end1)} (with)   [+{fmt(end1 - end0)}]")
        print()

    if args.solve_spend:
        ms = max_sustainable_spend(args.retire_age, params=p)
        print(f"Max sustainable spend retiring at Dan {args.retire_age} "
              f"(these knobs): {fmt(ms)}/yr = {fmt(ms/12)}/mo")
        print()

    if args.monte_carlo:
        mc = monte_carlo(args.retire_age, params=p, n_paths=args.monte_carlo,
                         vol=args.vol, seed=args.seed)
        print(f"Monte Carlo — retire at Dan {args.retire_age}, "
              f"{mc['n']} paths, vol {args.vol:.0%}, seed {args.seed}")
        print(f"  (median path = the deterministic {args.ret:.0%}-real path; "
              f"failures count as $0 in percentiles)")
        print(f"  Success rate: {mc['success_rate']:.1%}")
        print(f"  Ending balance at Dan-95: p10 {fmt(mc['p10'])} | "
              f"p50 {fmt(mc['p50'])} | p90 {fmt(mc['p90'])}")
        if mc["median_fail_age"]:
            print(f"  Median depletion age among failures: Dan {mc['median_fail_age']}")
        print()

    print("Not modeled (all upside): $115k 529s, ~$134k cash (incl $50k gift),")
    print("mortgage payoff (~2049 or at inheritance), parental inheritance,")
    print("Social Security claimed later than 67, post-retirement part-time work.")
    print()
    print("Known simplifications (revisit at check-ins): RMDs not modeled;")
    print("Roth-conversion taxes OFF by default (quantify with --conversions);")
    print("flat retirement tax rates; annual begin-of-year timing; SS taxed at")
    print("a flat rate. Validate anytime: python3 -m unittest -v")


if __name__ == "__main__":
    main()

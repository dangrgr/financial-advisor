#!/usr/bin/env python3
"""Retirement projection for Dan & Terri Grindall.

Solves for the EARLIEST feasible retirement age and stress-tests the answer
against investment-return and savings-rate assumptions.

Everything is in TODAY'S DOLLARS (real terms): returns are real (nominal minus
inflation), spending is constant real, Social Security estimates from ssa.gov
are already quoted in today's dollars. This keeps the output readable without
an inflation lens.

Deterministic (not Monte Carlo). The conservative-return scenario (4% real) is
the proxy for sequence-of-returns risk. Re-run with --help to see knobs.
"""

import argparse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# INPUTS — edit these as facts change
# ---------------------------------------------------------------------------

CURRENT_YEAR = 2026
DAN_AGE = 47
TERRI_AGE = 49
PLAN_TO_DAN_AGE = 95          # model through Dan age 95 (Terri 97)

# Starting investable balances by tax treatment (May 2026 screenshots).
# Excludes: 529s ($115k), kids' UTMA ($3.6k), and ~$120k cash buffer
# (incl. incoming $50k gift). All of those are UPSIDE not modeled here.
START_TAX_DEFERRED = 794_274   # old 401ks + rollover/trad IRAs (taxed at withdrawal)
START_ROTH         = 327_070   # Roth IRAs (tax-free)
START_TAXABLE      = 172_992   # Vanguard joint brokerage 7157

# Annual contributions while working (real $).
# 401k: employee max + employer match (4% of $222k base = $8,880).
# Catch-up contributions kick in automatically at age 50 ("always max").
MATCH_401K = 8_880
TAXABLE_SAVINGS = 50_000       # surplus bonus invested/yr — KEY ASSUMPTION

# Growth (REAL = nominal ~7-8% minus ~3% inflation).
REAL_RETURN = 0.05

# Spending in retirement (real $/yr, ALL-IN including the 2.75% mortgage,
# which per your note stays until an inheritance windfall pays it off — that
# payoff is treated as upside, not assumed here).
SPEND = 120_000
HEALTH_BRIDGE_PER_PERSON = 15_000   # private health insurance until age 65

# Social Security (today's $, benefit at Full Retirement Age = 67).
# Dan from ssa.gov: $2,851 @62, $4,223 @67 (FRA), $5,266 @70.
DAN_SS_ANNUAL_AT_67   = 50_676      # $4,223/mo (ssa.gov)
TERRI_SS_ANNUAL_AT_67 = 33_784      # ~2/3 of Dan, $2,815/mo
SS_CLAIM_AGE = 67

# Retirement tax approximation (effective rates on withdrawals/SS).
TAX_DEFERRED_RATE  = 0.12     # ordinary income on pre-tax withdrawals
TAXABLE_GAINS_RATE = 0.075    # ~15% LTCG on ~50% embedded gains
SS_TAX_RATE        = 0.10     # ~85% of SS taxable, low bracket


# ---------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------

def annual_contributions(dan_age, terri_age, taxable_savings):
    """Return (tax_deferred, roth, taxable) contributions for one working year."""
    dan_401k_employee = 24_000 if dan_age < 50 else 31_500   # +catch-up at 50
    dan_ira  = 7_000 if dan_age  < 50 else 8_000
    terri_ira = 7_000 if terri_age < 50 else 8_000
    tax_deferred = dan_401k_employee + MATCH_401K
    roth = dan_ira + terri_ira                                # both backdoor Roth
    return tax_deferred, roth, taxable_savings


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


def simulate(ret_dan_age, real_return=REAL_RETURN, taxable_savings=TAXABLE_SAVINGS,
             record=False):
    """Run one life path. Returns (survived: bool, ending_balance, history)."""
    td, roth, tax = START_TAX_DEFERRED, START_ROTH, START_TAXABLE
    dan, terri, year = DAN_AGE, TERRI_AGE, CURRENT_YEAR
    history = []
    survived = True

    while dan <= PLAN_TO_DAN_AGE:
        retired = dan >= ret_dan_age

        if not retired:
            c_td, c_roth, c_tax = annual_contributions(dan, terri, taxable_savings)
            td += c_td; roth += c_roth; tax += c_tax
        else:
            need = SPEND
            if dan < 65:   need += HEALTH_BRIDGE_PER_PERSON
            if terri < 65: need += HEALTH_BRIDGE_PER_PERSON

            ss = 0.0
            if dan >= SS_CLAIM_AGE:   ss += DAN_SS_ANNUAL_AT_67
            if terri >= SS_CLAIM_AGE: ss += TERRI_SS_ANNUAL_AT_67
            ss_net = ss * (1 - SS_TAX_RATE)

            net_need = max(0.0, need - ss_net)
            buckets = [
                {"name": "taxable", "bal": tax,  "net_factor": 1 - TAXABLE_GAINS_RATE},
                {"name": "deferred", "bal": td,  "net_factor": 1 - TAX_DEFERRED_RATE},
                {"name": "roth",    "bal": roth, "net_factor": 1.0},
            ]
            shortfall = _draw(net_need, buckets)
            tax, td, roth = buckets[0]["bal"], buckets[1]["bal"], buckets[2]["bal"]
            if shortfall > 1e-6:
                survived = False

        # Year-end growth on remaining balances.
        td   *= (1 + real_return)
        roth *= (1 + real_return)
        tax  *= (1 + real_return)

        total = td + roth + tax
        if record:
            history.append((year, dan, terri, total, td, roth, tax))
        if total <= 0 or not survived:
            return False, max(0.0, total), history

        dan += 1; terri += 1; year += 1

    return True, td + roth + tax, history


def earliest_age(real_return=REAL_RETURN, taxable_savings=TAXABLE_SAVINGS):
    for age in range(DAN_AGE + 1, SS_CLAIM_AGE + 1):
        ok, _, _ = simulate(age, real_return, taxable_savings)
        if ok:
            return age
    return None


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def fmt(n):
    return f"${n:,.0f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--return", dest="ret", type=float, default=REAL_RETURN,
                    help="real return assumption (default 0.05)")
    ap.add_argument("--taxable", type=float, default=TAXABLE_SAVINGS,
                    help="annual taxable savings (default 50000)")
    args = ap.parse_args()

    start_total = START_TAX_DEFERRED + START_ROTH + START_TAXABLE
    print("=" * 70)
    print("RETIREMENT PROJECTION — Dan (47) & Terri (49) — today's dollars")
    print("=" * 70)
    print(f"Starting investable: {fmt(start_total)}")
    print(f"  Tax-deferred {fmt(START_TAX_DEFERRED)} | "
          f"Roth {fmt(START_ROTH)} | Taxable {fmt(START_TAXABLE)}")
    print(f"Spending goal: {fmt(SPEND)}/yr all-in  "
          f"(+{fmt(HEALTH_BRIDGE_PER_PERSON)}/person health pre-65)")
    print(f"Social Security at 67: Dan {fmt(DAN_SS_ANNUAL_AT_67)} + "
          f"Terri {fmt(TERRI_SS_ANNUAL_AT_67)} = "
          f"{fmt(DAN_SS_ANNUAL_AT_67 + TERRI_SS_ANNUAL_AT_67)}/yr")
    print(f"Assumptions: {args.ret:.0%} real return, "
          f"{fmt(args.taxable)}/yr taxable savings")
    print()

    age = earliest_age(args.ret, args.taxable)
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
        ok, ending, _ = simulate(a, args.ret, args.taxable)
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
            a = earliest_age(r, t)
            row.append(f"  {a if a else '>67'}".rjust(7))
        print("  " + "".join(row))
    print()
    print("Not modeled (all upside): $115k 529s, ~$120k cash buffer + $50k gift,")
    print("mortgage payoff (~2049 or at inheritance), parental inheritance,")
    print("Social Security claimed later than 67, post-retirement part-time work.")


if __name__ == "__main__":
    main()

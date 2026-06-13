#!/usr/bin/env python3
"""Validation suite for retirement_projection.py — run: python3 -m unittest -v

Purpose: make the model SOLID GROUND for annual check-ins. If this suite is
green, then (a) the engine still produces exactly the numbers written into
retirement_plan.yaml and retirement_goal_55.md, (b) the engine's arithmetic
agrees with independent closed-form re-derivations, and (c) the model's
qualitative behaviors (monotonicity, conservation) still hold. Any future
edit — by any person or any model — that silently changes the projection
will turn this suite red.

Layers:
  1. GOLDEN NUMBERS   — pin every headline figure the plan documents cite.
  2. PLAN CONSISTENCY — retirement_plan.yaml targets/assumptions must match
                        what the code actually computes/assumes (no drift
                        between the plan document and the model).
  3. CROSS-VALIDATION — independent re-implementations (closed-form annuity
                        math, a hand-rolled accumulation loop) must agree
                        with the simulation engine.
  4. PROPERTIES       — directional sanity (more return -> retire earlier,
                        more spend -> less ending wealth, draws conserve
                        value, scenario overlays move results the right way).
  4b. SIDE INCOME     — overlay is pure upside; default-off leaves the pinned
                        baseline untouched; never load-bearing.
  4c. SS CLAIM AGE    — benefit scales with claim age per SSA rules; default
                        (67 = FRA) leaves the baseline untouched.
  4d. SAVINGS DIALS   — per-vessel contribution knobs; defaults reproduce the
                        prior schedule exactly; vessels route to the right bucket.
  5. MONTE CARLO      — seeded reproducibility + pinned baseline result.
"""

import re
import unittest
from pathlib import Path
from dataclasses import replace

import retirement_projection as rp
from retirement_projection import Params, simulate, earliest_age, \
    max_sustainable_spend, spend_feasibility_rows, monte_carlo, _draw, \
    ss_benefit_factor, annual_contributions, bucketize, savings_schedule

HERE = Path(__file__).parent
YAML = (HERE / "retirement_plan.yaml").read_text()

TOL = 2  # dollars — engine is float math; pinned values are exact-to-$1


# ---------------------------------------------------------------------------
# 1. GOLDEN NUMBERS — the figures quoted in retirement_goal_55.md
# ---------------------------------------------------------------------------

class TestGoldenNumbers(unittest.TestCase):

    def test_earliest_feasible_age_base_case(self):
        self.assertEqual(earliest_age(), 54)

    def test_earliest_age_sensitivity_grid(self):
        # (real_return, taxable_savings) -> earliest Dan age, as printed
        # in the report's sensitivity table.
        expected = {
            (0.04, 30_000): 56, (0.04, 50_000): 55, (0.04, 80_000): 54,
            (0.05, 30_000): 54, (0.05, 50_000): 54, (0.05, 80_000): 53,
            (0.06, 30_000): 53, (0.06, 50_000): 53, (0.06, 80_000): 52,
        }
        for (r, t), age in expected.items():
            self.assertEqual(earliest_age(r, t), age, msg=f"grid ({r}, {t})")

    def test_retire_at_55_base_case_dies_with_4M(self):
        ok, end, _ = simulate(55)
        self.assertTrue(ok)
        self.assertAlmostEqual(end, 4_023_750, delta=TOL)

    def test_retire_at_54_base_case(self):
        ok, end, _ = simulate(54)
        self.assertTrue(ok)
        self.assertAlmostEqual(end, 1_825_790, delta=TOL)

    def test_retire_at_53_depletes(self):
        ok, _, _ = simulate(53)
        self.assertFalse(ok)

    def test_spend_feasibility_table(self):
        # ($/yr, base ok, base ending, stress ok, stress ending, earliest age)
        rows = spend_feasibility_rows(55)
        expected = [
            (144_000, True, 5_839_185, True,  910_881, 53),
            (156_000, True, 4_023_750, False, None,    54),
            (168_000, True, 2_412_969, False, None,    54),
        ]
        for row, exp in zip(rows, expected):
            annual, ok_b, end_b, ok_s, end_s, ea = row
            self.assertEqual(annual, exp[0])
            self.assertEqual(ok_b, exp[1], msg=f"base @{annual}")
            self.assertAlmostEqual(end_b, exp[2], delta=TOL, msg=f"base end @{annual}")
            self.assertEqual(ok_s, exp[3], msg=f"stress @{annual}")
            if exp[4] is not None:
                self.assertAlmostEqual(end_s, exp[4], delta=TOL)
            self.assertEqual(ea, exp[5], msg=f"earliest @{annual}")

    def test_max_sustainable_spend_base_and_stress(self):
        # retirement_goal_55.md: "~$12,750/mo in the conservative world and
        # ~$15,500/mo in the base case"
        base = max_sustainable_spend(55, Params(real_return=0.05, taxable_savings=50_000))
        stress = max_sustainable_spend(55, Params(real_return=0.04, taxable_savings=30_000))
        self.assertAlmostEqual(base / 12, 15_498, delta=5)
        self.assertAlmostEqual(stress / 12, 12_731, delta=5)

    def test_taxable_bridge_lasts_to_dan_59(self):
        # The 55-59.5 penalty bridge: taxable must cover spending until at
        # least the year Dan turns 59 (it exhausts during 2038, Dan 59;
        # pre-tax draws then begin months before Dan's Jan-2039 59.5 date —
        # covered by Terri's age-61 accounts / Roth basis per the plan).
        _, _, hist = simulate(55, record=True)
        by_age = {dan: tax for (_, dan, _, _, _, _, tax) in hist}
        self.assertGreater(by_age[58], 100_000)   # still solidly funded at 58
        self.assertLess(by_age[59], 1)            # exhausted during the 59 year
        # taxable at the start of retirement (end-of-2033 balance)
        self.assertAlmostEqual(by_age[54], 835_651, delta=TOL)


# ---------------------------------------------------------------------------
# 2. PLAN CONSISTENCY — retirement_plan.yaml must match the code
# ---------------------------------------------------------------------------

class TestPlanConsistency(unittest.TestCase):

    def test_target_trajectory_matches_model(self):
        # Every Jan-1 target in the YAML must equal the model's end-of-prior-
        # year total on the base path (5% real, $50k taxable, retire at 55).
        targets = {int(y): int(v) for y, v in
                   re.findall(r"^\s+(\d{4})-01-01:\s+(\d+)", YAML, re.M)}
        self.assertGreaterEqual(len(targets), 9, "trajectory not found in YAML")
        _, _, hist = simulate(55, record=True)
        model = {year + 1: total for (year, _, _, total, _, _, _) in hist}
        for jan_year, target in targets.items():
            if jan_year == 2026:
                self.assertEqual(target, rp.START_TAX_DEFERRED +
                                 rp.START_ROTH + rp.START_TAXABLE)
            elif jan_year in model:
                self.assertAlmostEqual(model[jan_year], target, delta=TOL,
                                       msg=f"trajectory drift at Jan {jan_year}")

    def test_yaml_checkpoint_targets_match_model(self):
        targets = {int(y): int(v) for y, v in
                   re.findall(r"date:\s+(\d{4})-01-01.*?target_total_investable:\s+(\d+)",
                              YAML, re.S)}
        _, _, hist = simulate(55, record=True)
        model = {year + 1: total for (year, _, _, total, _, _, _) in hist}
        for jan_year, target in targets.items():
            if jan_year > 2026:
                self.assertAlmostEqual(model[jan_year], target, delta=TOL,
                                       msg=f"checkpoint drift at Jan {jan_year}")

    def _yaml_number(self, pattern):
        m = re.search(pattern, YAML, re.M)
        self.assertIsNotNone(m, f"pattern not found in YAML: {pattern}")
        return float(m.group(1))

    def test_assumptions_match_code(self):
        self.assertEqual(self._yaml_number(r"real_return_base:\s+([\d.]+)"),
                         rp.REAL_RETURN)
        self.assertEqual(self._yaml_number(
            r"health_insurance_bridge_per_person_pre65:\s+([\d.]+)"),
            rp.HEALTH_BRIDGE_PER_PERSON)
        self.assertEqual(self._yaml_number(r"tax_deferred_withdrawal:\s+([\d.]+)"),
                         rp.TAX_DEFERRED_RATE)
        self.assertEqual(self._yaml_number(r"taxable_gains:\s+([\d.]+)"),
                         rp.TAXABLE_GAINS_RATE)
        self.assertEqual(self._yaml_number(r"social_security:\s+([\d.]+)"),
                         rp.SS_TAX_RATE)

    def test_starting_balances_match_yaml_baseline(self):
        self.assertEqual(self._yaml_number(r"^\s+tax_deferred:\s+(\d+)"),
                         rp.START_TAX_DEFERRED)
        self.assertEqual(self._yaml_number(r"^\s+roth:\s+(\d+)"), rp.START_ROTH)
        self.assertEqual(self._yaml_number(r"^\s+taxable:\s+(\d+)"), rp.START_TAXABLE)
        self.assertEqual(self._yaml_number(r"^\s+total_investable:\s+(\d+)"),
                         rp.START_TAX_DEFERRED + rp.START_ROTH + rp.START_TAXABLE)

    def test_ss_benefits_match_yaml(self):
        self.assertAlmostEqual(self._yaml_number(r"at_67_FRA:\s+(\d+)") * 12,
                               rp.DAN_SS_ANNUAL_AT_67, delta=1)


# ---------------------------------------------------------------------------
# 3. CROSS-VALIDATION — independent math must agree with the engine
# ---------------------------------------------------------------------------

class TestCrossValidation(unittest.TestCase):

    def test_accumulation_phase_independent_rederivation(self):
        # Hand-rolled re-derivation of the working years 2026-2033 (Dan 47-54)
        # with retirement at 55: contributions at start of year, growth at end.
        td, roth, tax = 946_496.0, 327_070.0, 172_992.0
        for dan in range(47, 55):                  # 2026 .. 2033
            terri = dan + 2
            k401 = (24_000 if dan < 50 else 31_500) + 8_880
            ira = 7_000 if dan < 50 else 8_000
            redirect = 7_000 if terri < 50 else 8_000
            td += k401
            roth += ira
            tax += 50_000 + redirect
            td *= 1.05; roth *= 1.05; tax *= 1.05
        expected_2034 = td + roth + tax

        _, _, hist = simulate(55, record=True)
        model_2034 = {y + 1: t for (y, _, _, t, _, _, _) in hist}[2034]
        self.assertAlmostEqual(model_2034, expected_2034, delta=0.01)
        self.assertAlmostEqual(model_2034, 3_166_464, delta=TOL)

    def test_decumulation_matches_closed_form_annuity(self):
        # Single taxable bucket, no SS, no health: balance follows
        #   B' = (B - W/f) * (1+r)
        # which after n years has the closed form
        #   B_n = B*(1+r)^n - (W/f) * (1+r) * ((1+r)^n - 1) / r
        B, W, r, g = 2_000_000.0, 80_000.0, 0.05, 0.075
        p = Params(start_tax_deferred=0, start_roth=0, start_taxable=B,
                   spend=W, health_per_person=0, ss_haircut=1.0,
                   real_return=r, taxable_gains_rate=g)
        ok, end, _ = simulate(rp.DAN_AGE, params=p)   # retired from day one
        n = rp.PLAN_TO_DAN_AGE - rp.DAN_AGE + 1
        f = 1 - g
        closed = B * (1 + r) ** n - (W / f) * (1 + r) * ((1 + r) ** n - 1) / r
        self.assertTrue(ok)
        self.assertAlmostEqual(end, closed, delta=1.0)

    def test_draw_conserves_value(self):
        # Withdrawing $1 gross from a bucket yields exactly net_factor after
        # tax; _draw must satisfy: net delivered == sum(bal_reduction * f).
        buckets = [
            {"name": "taxable", "bal": 10_000.0, "net_factor": 0.925},
            {"name": "deferred", "bal": 50_000.0, "net_factor": 0.88},
            {"name": "roth", "bal": 30_000.0, "net_factor": 1.0},
        ]
        before = [b["bal"] for b in buckets]
        need = 40_000.0
        shortfall = _draw(need, buckets)
        delivered = sum((b0 - b["bal"]) * b["net_factor"]
                        for b0, b in zip(before, buckets))
        self.assertAlmostEqual(shortfall, 0.0, delta=1e-6)
        self.assertAlmostEqual(delivered, need, delta=1e-6)
        # priority order: taxable fully drained before deferred is touched
        self.assertAlmostEqual(buckets[0]["bal"], 0.0, delta=1e-6)
        self.assertGreater(buckets[2]["bal"], 29_999)   # roth untouched

    def test_draw_reports_shortfall(self):
        buckets = [{"name": "only", "bal": 1_000.0, "net_factor": 0.9}]
        shortfall = _draw(5_000.0, buckets)
        self.assertAlmostEqual(shortfall, 5_000.0 - 900.0, delta=1e-6)


# ---------------------------------------------------------------------------
# 4. PROPERTIES — directional sanity of the engine and scenario overlays
# ---------------------------------------------------------------------------

class TestProperties(unittest.TestCase):

    def test_higher_return_never_delays_retirement(self):
        ages = [earliest_age(r, 50_000) for r in (0.03, 0.04, 0.05, 0.06)]
        for earlier, later in zip(ages, ages[1:]):
            if earlier is not None and later is not None:
                self.assertGreaterEqual(earlier, later)

    def test_higher_spend_lowers_ending_wealth(self):
        ends = []
        for spend in (144_000, 156_000, 168_000):
            ok, end, _ = simulate(55, params=Params(spend=spend))
            ends.append(end if ok else -1)
        self.assertEqual(ends, sorted(ends, reverse=True))

    def test_ss_haircut_hurts(self):
        ok0, end0, _ = simulate(55, params=Params())
        ok1, end1, _ = simulate(55, params=Params(ss_haircut=0.20))
        self.assertLess(end1, end0)

    def test_conversions_shift_deferred_to_roth(self):
        _, _, h0 = simulate(55, params=Params(), record=True)
        _, _, h1 = simulate(55, params=Params(conversions=True), record=True)
        td0 = {dan: td for (_, dan, _, _, td, _, _) in h0}
        td1 = {dan: td for (_, dan, _, _, td, _, _) in h1}
        roth0 = {dan: ro for (_, dan, _, _, _, ro, _) in h0}
        roth1 = {dan: ro for (_, dan, _, _, _, ro, _) in h1}
        self.assertLess(td1[66], td0[66] * 0.25)        # pre-tax mostly drained
        self.assertGreater(roth1[66], roth0[66])        # ...into Roth
        # and the drag is a real cost vs the naive 12%-forever baseline
        _, end0, _ = simulate(55, params=Params())
        _, end1, _ = simulate(55, params=Params(conversions=True))
        self.assertLess(end1, end0)

    def test_survivor_scenario_changes_outcome(self):
        ok0, end0, _ = simulate(55, params=Params())
        ok1, end1, _ = simulate(55, params=Params(survivor_at_dan_age=75))
        self.assertTrue(ok1)              # plan should survive a first death at 75
        self.assertNotAlmostEqual(end0, end1, delta=1000)

    def test_solver_brackets_the_failure_boundary(self):
        ms = max_sustainable_spend(55)
        ok_lo, _, _ = simulate(55, params=Params(spend=ms - 500))
        ok_hi, _, _ = simulate(55, params=Params(spend=ms + 500))
        self.assertTrue(ok_lo)
        self.assertFalse(ok_hi)


# ---------------------------------------------------------------------------
# 4b. SIDE INCOME — overlay must be pure upside, never load-bearing, and the
#     default (off) must leave every pinned baseline number untouched.
# ---------------------------------------------------------------------------

class TestSideIncome(unittest.TestCase):

    def test_default_is_off_and_baseline_unchanged(self):
        # The whole point: factor it if it happens, never depend on it. With
        # side_income=0 the result must equal the pinned base case exactly.
        ok, end, _ = simulate(55, params=Params(side_income=0.0))
        self.assertTrue(ok)
        self.assertAlmostEqual(end, 4_023_750, delta=TOL)

    def test_side_income_is_pure_upside(self):
        _, end0, _ = simulate(55, params=Params())
        _, end1, _ = simulate(55, params=Params(side_income=50_000))
        self.assertGreater(end1, end0)
        # §8 Q1 answer, pinned: $50k/yr gross 2034-39 in the base case
        self.assertAlmostEqual(end1, 5_687_534, delta=TOL)

    def test_more_side_income_never_hurts(self):
        ends = [simulate(55, params=Params(side_income=s))[1]
                for s in (0, 25_000, 50_000, 100_000)]
        self.assertEqual(ends, sorted(ends))

    def test_side_income_extends_the_bridge(self):
        # Taxable bucket should survive at least as long with side income.
        def exhaust_age(side):
            _, _, h = simulate(55, params=Params(side_income=side), record=True)
            drained = [d for (_, d, _, _, _, _, t) in h if d >= 55 and t < 1]
            return min(drained)
        self.assertGreaterEqual(exhaust_age(50_000), exhaust_age(0))

    def test_only_applies_inside_the_window(self):
        # Income entirely outside the window must change nothing.
        _, base, _ = simulate(55, params=Params())
        _, outside, _ = simulate(55, params=Params(
            side_income=50_000, side_income_start_age=40, side_income_end_age=45))
        self.assertAlmostEqual(outside, base, delta=TOL)

    def test_net_of_tax_offsets_the_draw_one_for_one(self):
        # Cross-validation: $X gross at rate r reduces the year's net draw by
        # exactly X*(1-r) — i.e. side income and an equal net SS inflow are
        # interchangeable. Build an isolated 1-year-window case and check the
        # taxable balance moves by net/(1-gains_rate) relative to no income.
        common = dict(start_tax_deferred=0, start_roth=0, start_taxable=5_000_000,
                      spend=100_000, health_per_person=0, ss_haircut=1.0,
                      side_income_start_age=55, side_income_end_age=55)
        _, _, h0 = simulate(55, params=Params(side_income=0.0, **common), record=True)
        _, _, h1 = simulate(55, params=Params(side_income=40_000,
                             side_income_tax_rate=0.25, **common), record=True)
        tax0 = {d: t for (_, d, _, _, _, _, t) in h0}[55]
        tax1 = {d: t for (_, d, _, _, _, _, t) in h1}[55]
        net = 40_000 * 0.75
        # both grew one year at 5%; the only difference is a smaller draw of
        # `net` after-tax dollars, i.e. net/(1-gains) fewer shares sold, grown.
        expected_gap = (net / (1 - 0.075)) * 1.05
        self.assertAlmostEqual(tax1 - tax0, expected_gap, delta=1.0)

    def test_can_rescue_a_failing_stress_case_but_only_as_upside(self):
        # The stress+conversions case fails on its own; side income can carry
        # it — demonstrating value WITHOUT the baseline ever relying on it.
        stress = Params(conversions=True, real_return=0.04,
                        taxable_savings=30_000, spend=156_000)
        ok0, _, _ = simulate(55, params=stress)
        ok1, end1, _ = simulate(55, params=replace(stress, side_income=50_000))
        self.assertFalse(ok0)               # plan does NOT depend on side income
        self.assertTrue(ok1)                # ...but it helps a lot if it happens
        self.assertGreater(end1, 0)


# ---------------------------------------------------------------------------
# 4c. SS CLAIM AGE — benefit must scale with claim age (SSA actuarial rules);
#     default (67 = FRA) leaves the pinned baseline untouched.
# ---------------------------------------------------------------------------

class TestSSClaimAge(unittest.TestCase):

    def test_benefit_factor_matches_ssa_rules(self):
        self.assertAlmostEqual(ss_benefit_factor(67), 1.00, places=4)   # FRA
        self.assertAlmostEqual(ss_benefit_factor(70), 1.24, places=4)   # +8%/yr x3
        self.assertAlmostEqual(ss_benefit_factor(68), 1.08, places=4)
        self.assertAlmostEqual(ss_benefit_factor(62), 0.70, places=4)   # 30% cut
        # Independent re-derivation at 64 (36 mo early): 36 * 5/9 % = 20% cut.
        self.assertAlmostEqual(ss_benefit_factor(64), 0.80, places=4)
        # 63 = 48 mo early: 36*(5/9)% + 12*(5/12)% = 20% + 5% = 25% cut.
        self.assertAlmostEqual(ss_benefit_factor(63), 0.75, places=4)

    def test_factor_clamps_to_62_70_window(self):
        self.assertEqual(ss_benefit_factor(75), ss_benefit_factor(70))  # no DRC past 70
        self.assertEqual(ss_benefit_factor(58), ss_benefit_factor(62))

    def test_default_claim_age_leaves_baseline_unchanged(self):
        ok, end, _ = simulate(55, params=Params(ss_claim_age=67))
        self.assertTrue(ok)
        self.assertAlmostEqual(end, 4_023_750, delta=TOL)

    def test_delaying_helps_the_base_case_pinned(self):
        # Naive base: claim 70 should beat claim 67 (bigger lifetime checks win
        # at a plan-to-95 horizon), and claim 62 should trail it.
        _, e62, _ = simulate(55, params=Params(ss_claim_age=62))
        _, e67, _ = simulate(55, params=Params(ss_claim_age=67))
        _, e70, _ = simulate(55, params=Params(ss_claim_age=70))
        self.assertLess(e62, e67)
        self.assertGreater(e70, e67)
        self.assertAlmostEqual(e70, 4_127_361, delta=TOL)   # §pinned

    def test_delaying_does_not_rescue_the_failing_stress_case(self):
        # The key finding: delayed SS is a LONGEVITY hedge, not a FRAGILITY
        # hedge. It must NOT flip the failing stress path to survival (the
        # 67-70 no-SS gap forces extra early draws that offset the bigger
        # later checks). Contrast: side income and the $12k floor DO rescue it.
        base = Params(conversions=True, real_return=0.04, taxable_savings=30_000)
        self.assertFalse(simulate(55, params=base)[0])              # fails @67
        self.assertFalse(simulate(55, params=replace(base, ss_claim_age=70))[0])


# ---------------------------------------------------------------------------
# 4d. SAVINGS DIALS — per-vessel contribution knobs. Defaults must reproduce
#     the prior hardcoded schedule exactly; each dial routes to the right bucket.
# ---------------------------------------------------------------------------

class TestSavingsDials(unittest.TestCase):

    def test_default_year1_buckets_match_prior_schedule(self):
        td, roth, tax, nd = bucketize(annual_contributions(Params(), 47, 49))
        self.assertEqual((td, roth, tax, nd), (32_880, 7_000, 57_000, 0))

    def test_default_schedule_totals(self):
        _, totals = savings_schedule(Params(), 55)
        self.assertEqual(totals["_total"], 824_540)
        self.assertEqual(totals["_tax_deferred"], 300_540)
        self.assertEqual(totals["_roth"], 61_000)
        self.assertEqual(totals["_taxable"], 463_000)
        self.assertEqual(totals["_nondeduct_ira"], 0)

    def test_default_dials_leave_baseline_unchanged(self):
        ok, end, _ = simulate(55, params=Params())   # all dials at default
        self.assertTrue(ok)
        self.assertAlmostEqual(end, 4_023_750, delta=TOL)

    def test_base_salary_drives_match_and_from_base_401k(self):
        items = annual_contributions(Params(base_salary=260_000), 47, 49)
        self.assertAlmostEqual(items["employer_match"], 260_000 * 0.04, delta=TOL)
        self.assertAlmostEqual(items["dan_401k_from_base"], 260_000 * 0.04, delta=TOL)
        # employee total still capped at the IRS limit
        self.assertAlmostEqual(items["dan_401k_from_base"] + items["dan_401k_topoff"],
                               24_000, delta=TOL)

    def test_topoff_cannot_exceed_irs_limit(self):
        items = annual_contributions(Params(k401_topoff=999_999), 47, 49)
        self.assertAlmostEqual(items["dan_401k_from_base"] + items["dan_401k_topoff"],
                               24_000, delta=TOL)            # under 50
        items50 = annual_contributions(Params(k401_topoff=999_999), 50, 52)
        self.assertAlmostEqual(items50["dan_401k_from_base"] + items50["dan_401k_topoff"],
                               31_500, delta=TOL)            # catch-up limit

    def test_terri_solo_401k_routes_to_tax_deferred(self):
        td0, _, tax0, _ = bucketize(annual_contributions(Params(), 47, 49))
        td1, _, tax1, nd1 = bucketize(annual_contributions(
            Params(terri_taxable=0.0, terri_solo_401k=8_000), 47, 49))
        self.assertAlmostEqual(td1 - td0, 8_000, delta=TOL)   # added to tax-deferred
        self.assertAlmostEqual(tax0 - tax1, 7_000, delta=TOL) # removed from taxable
        self.assertEqual(nd1, 0)

    def test_terri_trad_ira_routes_to_nondeduct_bucket(self):
        _, _, _, nd = bucketize(annual_contributions(
            Params(terri_taxable=0.0, terri_trad_ira=8_000), 47, 49))
        self.assertAlmostEqual(nd, 8_000, delta=TOL)

    def test_nondeduct_ira_basis_returns_tax_free_pinned(self):
        # Routing Terri's $8k/yr into the non-deductible IRA vs leaving it in
        # taxable changes the outcome (basis returns tax-free, growth taxed at
        # ordinary). Pinned so the basis-tracking math can't silently drift.
        _, base, _ = simulate(55, params=Params())
        _, nd, _ = simulate(55, params=Params(terri_taxable=0.0, terri_trad_ira=8_000))
        _, solo, _ = simulate(55, params=Params(terri_taxable=0.0, terri_solo_401k=8_000))
        self.assertAlmostEqual(nd, 4_053_876, delta=TOL)
        self.assertAlmostEqual(solo, 4_007_171, delta=TOL)
        # nd-IRA (basis free) beats solo-401k (fully taxed at withdrawal) in the
        # model's withdrawal-only view — the documented blind spot (no deduction
        # credited going in, no pro-rata/step-up). Asserted so the caveat stays true.
        self.assertGreater(nd, solo)

    def test_more_taxable_savings_helps(self):
        _, lo, _ = simulate(55, params=Params(taxable_savings=30_000))
        _, hi, _ = simulate(55, params=Params(taxable_savings=70_000))
        self.assertLess(lo, hi)

    def test_zero_spend_always_survives(self):
        ok, end, _ = simulate(55, params=Params(spend=0, health_per_person=0))
        self.assertTrue(ok)
        self.assertGreater(end, 10_000_000)

    def test_legacy_positional_args_still_work(self):
        # simulate(age, real_return, taxable_savings) — the calling convention
        # used by older scripts/notes — must keep working.
        ok, end, _ = simulate(55, 0.04, 30_000)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# 5. MONTE CARLO — seeded reproducibility (pinned baseline)
# ---------------------------------------------------------------------------

# $13k/mo, retire 55, vol 16%, seed 42, 500 paths — verified at suite creation
# (Jun 2026); see MODEL_VALIDATION.md for the full Monte Carlo discussion.
PINNED_MC_SUCCESS = 0.626


class TestMonteCarlo(unittest.TestCase):

    def test_seeded_run_is_reproducible(self):
        a = monte_carlo(55, n_paths=200, seed=7)
        b = monte_carlo(55, n_paths=200, seed=7)
        self.assertEqual(a, b)

    def test_different_seed_differs(self):
        a = monte_carlo(55, n_paths=200, seed=7)
        b = monte_carlo(55, n_paths=200, seed=8)
        self.assertNotEqual(a, b)

    def test_baseline_success_rate_pinned(self):
        # Pinned so any change to the engine or RNG stream is caught.
        mc = monte_carlo(55, n_paths=500, seed=42)
        self.assertAlmostEqual(mc["success_rate"], PINNED_MC_SUCCESS, delta=1e-9)

    def test_zero_vol_matches_deterministic(self):
        mc = monte_carlo(55, n_paths=3, vol=0.0, seed=1)
        self.assertEqual(mc["success_rate"], 1.0)
        ok, end, _ = simulate(55)
        # with vol=0 every path IS the deterministic path... almost: lognormal
        # mu = ln(1+r) with sigma=0 gives exactly r each year.
        self.assertAlmostEqual(mc["p50"], end, delta=1.0)


if __name__ == "__main__":
    unittest.main()

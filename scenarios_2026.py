#!/usr/bin/env python3
"""
Generate 2026 budget scenarios: Conservative, Balanced, Aggressive cuts
Show path to reduce or eliminate gap vs. base income
"""
import sqlite3
import pandas as pd

DB_PATH = "budget_analysis.db"
TARGET_MONTHLY_INCOME = 10800.00

def generate_2026_scenarios():
    """Create budget reduction scenarios"""

    print("="*100)
    print("2026 BUDGET SCENARIOS")
    print("="*100)

    conn = sqlite3.connect(DB_PATH)

    # Load 2026 projections
    proj_df = pd.read_sql("SELECT * FROM projected_2026_budget", conn)

    baseline_total = proj_df['projected_2026'].sum()
    baseline_gap = baseline_total - TARGET_MONTHLY_INCOME

    print(f"\nBaseline 2026 (No Changes):")
    print(f"  Monthly expenses: ${baseline_total:,.2f}")
    print(f"  Target income:    ${TARGET_MONTHLY_INCOME:,.2f}")
    print(f"  Monthly gap:      ${baseline_gap:,.2f}")
    print(f"  Annual gap:       ${baseline_gap * 12:,.2f}")

    # Define scenarios
    scenarios = {
        'Conservative': {
            'description': 'Modest cuts in high discretionary spending',
            'target_reduction': baseline_gap * 0.40,  # Reduce gap by 40%
            'cuts': {
                'Shopping': 0.15,  # 15% cut
                'Dining & Drinks': 0.15,
                'Entertainment & Rec.': 0.10,
                'Charitable Donations': 0.10,
            }
        },
        'Balanced': {
            'description': 'Moderate cuts across discretionary categories',
            'target_reduction': baseline_gap - 2000,  # Reduce gap to ~$2k/month
            'cuts': {
                'Shopping': 0.25,  # 25% cut
                'Dining & Drinks': 0.25,
                'Entertainment & Rec.': 0.20,
                'Groceries': 0.10,
                'Personal Care': 0.15,
                'Software & Tech': 0.20,
                'Home & Garden': 0.15,
            }
        },
        'Aggressive': {
            'description': 'Deep cuts to live within base salary',
            'target_reduction': baseline_gap,  # Eliminate gap entirely
            'cuts': {
                'Shopping': 0.35,  # 35% cut
                'Dining & Drinks': 0.35,
                'Entertainment & Rec.': 0.30,
                'Groceries': 0.15,
                'Personal Care': 0.20,
                'Software & Tech': 0.25,
                'Home & Garden': 0.20,
                'Auto & Transport': 0.10,
                'Charitable Donations': 0.20,
                'Uncategorized': 0.20,
            }
        }
    }

    all_scenario_data = []

    for scenario_name, scenario_config in scenarios.items():
        print("\n" + "="*100)
        print(f"SCENARIO: {scenario_name.upper()}")
        print(f"{scenario_config['description']}")
        print("="*100)

        total_reduction = 0

        print(f"\n{'Category':<25} {'Current 2026':>12} {'Cut %':>8} {'Reduction':>12} {'New Target':>12}")
        print("-"*100)

        scenario_data = []

        for _, row in proj_df.iterrows():
            category = row['category']
            current_2026 = row['projected_2026']

            # Apply cuts if category is in scenario
            if category in scenario_config['cuts']:
                cut_pct = scenario_config['cuts'][category]
                reduction = current_2026 * cut_pct
                new_target = current_2026 - reduction
                total_reduction += reduction

                print(f"{category:<25} ${current_2026:>11,.2f} {cut_pct*100:>7.0f}% ${reduction:>11,.2f} ${new_target:>11,.2f}")
            else:
                # No cut
                reduction = 0
                new_target = current_2026

            scenario_data.append({
                'scenario_name': scenario_name,
                'category': category,
                'current_2026': current_2026,
                'target_2026': new_target,
                'reduction_pct': scenario_config['cuts'].get(category, 0.0),
                'reduction_amount': reduction
            })

        # Calculate new gap
        new_total = baseline_total - total_reduction
        new_gap = new_total - TARGET_MONTHLY_INCOME

        print("-"*100)
        print(f"{'TOTAL REDUCTIONS':<25} {'':>12} {'':>8} ${total_reduction:>11,.2f}")

        print(f"\n{scenario_name} Scenario Results:")
        print(f"  New monthly expenses:  ${new_total:,.2f} (down ${total_reduction:,.2f})")
        print(f"  Target income:         ${TARGET_MONTHLY_INCOME:,.2f}")
        print(f"  Remaining gap:         ${new_gap:,.2f}")
        print(f"  Annual gap:            ${new_gap * 12:,.2f}")

        # How much bonus needed?
        bonus_for_gap = new_gap * 12
        irs_payment = 5000.00
        total_bonus_needed = bonus_for_gap + irs_payment

        # 6 months emergency fund
        emergency_fund = new_total * 6
        available_bonus = 90642  # From 2025 actuals

        bonus_for_discretionary = available_bonus - total_bonus_needed - (emergency_fund * 0.10)  # 10% of EF per year

        print(f"\nBonus Allocation ({scenario_name}):")
        print(f"  Bonus available:             ${available_bonus:,.2f}")
        print(f"  - Cover monthly gap:         ${bonus_for_gap:,.2f}")
        print(f"  - IRS tax payment:           ${irs_payment:,.2f}")
        print(f"  - Emergency fund (10%):      ${emergency_fund * 0.10:,.2f}")
        print(f"  = Remaining for discretionary: ${bonus_for_discretionary:,.2f}")

        if bonus_for_discretionary < 0:
            print(f"  ⚠️  WARNING: Bonus insufficient by ${abs(bonus_for_discretionary):,.2f}")
        else:
            print(f"  ✓ Leaves ${bonus_for_discretionary:,.2f} for travel & extras")

        print(f"\nEmergency Fund Target: ${emergency_fund:,.2f} (6 months expenses)")

        all_scenario_data.extend(scenario_data)

    # Save to database
    print("\n" + "="*100)
    print("LOADING SCENARIOS INTO DATABASE")
    print("="*100)

    scenario_df = pd.DataFrame(all_scenario_data)
    scenario_df.to_sql('scenarios_2026', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(scenario_df)} scenario entries into scenarios_2026 table")

    # Bonus allocation summary
    print("\n" + "="*100)
    print("BONUS ALLOCATION SUMMARY")
    print("="*100)

    bonus_summary = []
    for scenario_name, scenario_config in scenarios.items():
        scenario_subset = scenario_df[scenario_df['scenario_name'] == scenario_name]
        new_total = scenario_subset['target_2026'].sum()
        new_gap = new_total - TARGET_MONTHLY_INCOME

        bonus_for_gap = max(0, new_gap * 12)
        irs_payment = 5000.00
        emergency_fund_contribution = new_total * 6 * 0.10
        available_bonus = 90642

        bonus_for_discretionary = available_bonus - bonus_for_gap - irs_payment - emergency_fund_contribution

        bonus_summary.append({
            'scenario_name': scenario_name,
            'monthly_shortfall': new_gap,
            'annual_gap': new_gap * 12,
            'bonus_for_gap': bonus_for_gap,
            'bonus_for_emergency': emergency_fund_contribution,
            'bonus_for_discretionary': bonus_for_discretionary,
            'total_bonus_needed': bonus_for_gap + irs_payment + emergency_fund_contribution,
            'recommendation': f"{scenario_name}: {scenario_config['description']}"
        })

    bonus_df = pd.DataFrame(bonus_summary)
    bonus_df.to_sql('bonus_allocation', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(bonus_df)} bonus allocation scenarios")

    conn.close()

    # Recommendation
    print("\n" + "="*100)
    print("RECOMMENDATION")
    print("="*100)
    print("\nBased on the analysis:")
    print("\n1. **Conservative Scenario** - Minimal lifestyle impact")
    print(f"   - Reduces gap to ${baseline_gap - scenarios['Conservative']['target_reduction']:,.2f}/month")
    print(f"   - Leaves ~${bonus_summary[0]['bonus_for_discretionary']:,.2f} for discretionary spending")
    print(f"   - Easiest to implement, still relies heavily on bonus")

    print("\n2. **Balanced Scenario** (RECOMMENDED) - Moderate changes")
    print(f"   - Reduces gap to ~$2,000/month")
    print(f"   - Leaves ~${bonus_summary[1]['bonus_for_discretionary']:,.2f} for discretionary spending")
    print(f"   - Good balance between cutting expenses and maintaining lifestyle")

    print("\n3. **Aggressive Scenario** - Financial independence from bonuses")
    print(f"   - Achieves goal of living within base salary")
    print(f"   - Leaves ~${bonus_summary[2]['bonus_for_discretionary']:,.2f} for discretionary spending")
    print(f"   - Most financial security, requires significant lifestyle changes")

    print("\n" + "="*100)
    print("2026 SCENARIOS COMPLETE")
    print("="*100)

    return scenario_df


if __name__ == "__main__":
    generate_2026_scenarios()

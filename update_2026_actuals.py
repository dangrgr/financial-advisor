#!/usr/bin/env python3
"""
Update 2026 model with early actuals (Jan 1-18, 2026)
"""

print("="*100)
print("2026 EARLY ACTUALS UPDATE (as of Jan 18, 2026)")
print("="*100)

# Baseline adjustments from 2025 changes
planet_fitness_savings = 36.00  # Per month

# New 2026 changes (not in 2025 baseline)
google_one_cancellation = 20.00  # Per month
car_repair_jan_8 = 4746.15  # One-time

# Vehicle budget analysis
annual_vehicle_budget = 4800.00  # $400/month * 12
car_repair_pct = (car_repair_jan_8 / annual_vehicle_budget) * 100

print("\n" + "="*100)
print("SUBSCRIPTION CHANGES")
print("="*100)
print(f"\n✅ Canceled Planet Fitness (was in 2025 baseline):")
print(f"   Monthly savings: ${planet_fitness_savings:.2f}")
print(f"   Annual impact: ${planet_fitness_savings * 12:.2f}")
print(f"   Category: Health & Wellness")

print(f"\n✅ Canceled Google One/Gemini (new in Jan 2026, immediate cancel):")
print(f"   Monthly savings: ${google_one_cancellation:.2f}")
print(f"   Annual impact: ${google_one_cancellation * 12:.2f}")
print(f"   Category: Software & Tech")

print(f"\n📊 Total Monthly Subscription Savings: ${planet_fitness_savings + google_one_cancellation:.2f}")
print(f"   Annual: ${(planet_fitness_savings + google_one_cancellation) * 12:.2f}")

print("\n" + "="*100)
print("VEHICLE MAINTENANCE REALITY CHECK")
print("="*100)
print(f"\n💰 Actual Car Repair (Jan 8, 2026): ${car_repair_jan_8:,.2f}")
print(f"   Annual vehicle budget: ${annual_vehicle_budget:,.2f}")
print(f"   % of annual budget used: {car_repair_pct:.1f}%")
print(f"   Remaining vehicle budget for 2026: ${annual_vehicle_budget - car_repair_jan_8:,.2f}")
print(f"   Months of budget remaining: {(annual_vehicle_budget - car_repair_jan_8) / 400:.1f} months")

print(f"\n⚠️  CRITICAL INSIGHT:")
print(f"   This single repair validates our conservative $400/month estimate!")
print(f"   One major repair can consume nearly the entire annual budget.")
print(f"   Emergency fund is essential for covering these spikes.")

print("\n" + "="*100)
print("IMPACT ON 2026 PROJECTIONS")
print("="*100)

# Original 2026 projection
baseline_monthly_expenses = 14952.86
baseline_gap = baseline_monthly_expenses - 10800

# Adjusted with Planet Fitness cancellation (affects baseline)
adjusted_expenses = baseline_monthly_expenses - planet_fitness_savings
adjusted_gap = adjusted_expenses - 10800

# Additional Google One savings (doesn't affect baseline, but reduces 2026 gap)
total_2026_savings = planet_fitness_savings + google_one_cancellation
final_gap = baseline_monthly_expenses - planet_fitness_savings - google_one_cancellation - 10800

print(f"\nOriginal 2026 Projection:")
print(f"   Monthly expenses: ${baseline_monthly_expenses:,.2f}")
print(f"   Monthly gap: ${baseline_gap:,.2f}")

print(f"\nWith Planet Fitness cancellation (2025 baseline change):")
print(f"   Monthly expenses: ${adjusted_expenses:,.2f}")
print(f"   Monthly gap: ${adjusted_gap:,.2f}")
print(f"   Improvement: ${baseline_gap - adjusted_gap:,.2f}/month")

print(f"\nWith ALL subscription cuts (Planet Fitness + Google One):")
print(f"   Monthly expenses: ${baseline_monthly_expenses - total_2026_savings:,.2f}")
print(f"   Monthly gap: ${final_gap:,.2f}")
print(f"   Total improvement: ${baseline_gap - final_gap:,.2f}/month (${(baseline_gap - final_gap)*12:,.2f}/year)")

print("\n" + "="*100)
print("EMERGENCY FUND VALIDATION")
print("="*100)
print(f"\n✅ Car repair covered by:")
print(f"   Option 1: Emergency fund (recommended)")
print(f"   Option 2: Bonus allocation")
print(f"   Option 3: Vehicle maintenance budget (depleted for year)")

balanced_scenario_emergency_fund = 81690  # 6 months expenses
emergency_fund_contribution_2025 = balanced_scenario_emergency_fund * 0.10  # 10% per year

print(f"\nRecommended Emergency Fund: ${balanced_scenario_emergency_fund:,.2f} (6 months)")
print(f"   If funded at 10% from 2025 bonus: ${emergency_fund_contribution_2025:,.2f}")
print(f"   $4,746 repair = {(car_repair_jan_8 / balanced_scenario_emergency_fund) * 100:.1f}% of target fund")
print(f"   This validates the need for robust emergency savings!")

print("\n" + "="*100)
print("UPDATED 2026 BUDGET SCENARIOS")
print("="*100)

scenarios = {
    'Baseline (Updated)': {
        'monthly_gap': final_gap,
        'changes': f'Includes Planet Fitness (-${planet_fitness_savings:.0f}) + Google One (-${google_one_cancellation:.0f})'
    },
    'Conservative': {
        'monthly_gap': final_gap - 647.14,  # Original conservative cuts
        'changes': 'Baseline + 15% cuts on shopping/dining'
    },
    'Balanced': {
        'monthly_gap': final_gap - 1337.94,  # Original balanced cuts
        'changes': 'Baseline + 25% cuts + groceries optimization'
    },
    'Aggressive': {
        'monthly_gap': final_gap - 1968.35,  # Original aggressive cuts
        'changes': 'Baseline + 35% cuts across board'
    }
}

print(f"\n{'Scenario':<25} {'Monthly Gap':<15} {'Annual Gap':<15} {'Changes'}")
print("-"*100)
for name, data in scenarios.items():
    monthly = data['monthly_gap']
    annual = monthly * 12
    marker = "⭐" if name == "Balanced" else ""
    print(f"{name:<25} ${monthly:<14,.2f} ${annual:<14,.2f} {data['changes']} {marker}")

print("\n" + "="*100)
print("JANUARY 2026 FINANCIAL SUMMARY")
print("="*100)
print(f"\n💸 Expenses (Jan 1-18):")
print(f"   Car repair: ${car_repair_jan_8:,.2f}")
print(f"   Normal expenses: ~${baseline_monthly_expenses * (18/30):,.2f} (18 days worth)")
print(f"   Total: ~${car_repair_jan_8 + baseline_monthly_expenses * (18/30):,.2f}")

print(f"\n💰 Income:")
print(f"   Base salary (Jan 1-15): ${5400:,.2f}")
print(f"   Expected (Jan 15-31): ${5400:,.2f}")
print(f"   Total January: ${10800:,.2f}")

print(f"\n📊 January Projection:")
print(f"   Income: ${10800:,.2f}")
print(f"   Expenses (estimated): ${car_repair_jan_8 + baseline_monthly_expenses:,.2f}")
print(f"   Gap: ${10800 - (car_repair_jan_8 + baseline_monthly_expenses):,.2f}")
print(f"   This month will need bonus/emergency fund coverage")

print("\n" + "="*100)
print("ACTION ITEMS")
print("="*100)
print(f"\n1. ✅ DONE: Canceled Planet Fitness")
print(f"2. ✅ DONE: Canceled Google One")
print(f"3. ⚠️  URGENT: Allocate emergency fund for $4,746 car repair")
print(f"4. 📋 TODO: Continue with Balanced Scenario spending cuts")
print(f"5. 📋 TODO: Build emergency fund to ${balanced_scenario_emergency_fund:,.0f} target")
print(f"6. 📊 TODO: Track remaining vehicle maintenance budget (${annual_vehicle_budget - car_repair_jan_8:,.2f} left)")

print("\n" + "="*100)
print("UPDATE COMPLETE")
print("="*100)
print(f"\n✅ Your subscription cuts improved the gap by ${total_2026_savings:,.0f}/month")
print(f"✅ Your vehicle maintenance budget just proved its value (99% used in week 1!)")
print(f"⚠️  Emergency fund is critical - this is exactly what it's for")
print(f"\nNext: Continue with Balanced Scenario cuts to reduce monthly gap to ~${final_gap - 1337.94:,.2f}")

if __name__ == "__main__":
    pass

#!/usr/bin/env python3
"""
Define category-specific inflation rates for 2026 projections
Based on research: conservative estimates for Colorado household
"""

# Conservative inflation estimates for 2026
# Based on economic forecasts and Colorado regional factors
INFLATION_RATES = {
    # Food
    'Groceries': 0.035,  # 3.5% (USDA 3.0% + Colorado factor)
    'Dining & Drinks': 0.040,  # 4.0% (USDA 3.3% + tariff buffer)

    # Housing & Utilities
    'Bills & Utilities': 0.100,  # 10.0% (weighted avg: electric 12%, gas 16%, other 4%)
    'Home & Garden': 0.035,  # 3.5% (general CPI)

    # Transportation
    'Auto & Transport': 0.040,  # 4.0% (insurance 4.5% + fuel 3.5%)

    # Healthcare
    'Medical': 0.090,  # 9.0% (conservative mid-range 8.5-9.6%)
    'Health & Wellness': 0.090,  # 9.0% (track with medical)

    # Discretionary
    'Shopping': 0.025,  # 2.5% (nondurable goods 1.7% + buffer)
    'Software & Tech': 0.020,  # 2.0% (durable goods 1.5% + buffer)
    'Entertainment & Rec.': 0.035,  # 3.5% (general CPI)
    'Personal Care': 0.035,  # 3.5% (general CPI)

    # Family
    'Pets': 0.040,  # 4.0% (vet costs trend high)
    'Kids Activities': 0.035,  # 3.5% (general CPI)
    'Education': 0.030,  # 3.0% (2.3-3.25% range, high end)

    # Other
    'Charitable Donations': 0.000,  # 0.0% (discretionary, no inflation)
    'Uncategorized': 0.035,  # 3.5% (default CPI)
    'Cash & Checks': 0.035,  # 3.5% (default CPI)
    'Taxes': 0.000,  # 0.0% (specific amounts, not inflated)
    'Fees': 0.035,  # 3.5% (default CPI)
    'Legal': 0.035,  # 3.5% (default CPI)
}

# Vehicle maintenance budget for 2026 (NEW)
VEHICLE_MAINTENANCE_2026 = {
    '2014 Subaru Impreza': {
        'monthly': 137.50,  # $1,650/year conservative
        'annual': 1650.00,
        'notes': '12 years old, 60k miles, includes 60k service + age buffer'
    },
    '2020 Subaru Ascent': {
        'monthly': 137.50,  # $1,650/year conservative
        'annual': 1650.00,
        'notes': '6 years old, 60k miles, primary vehicle, 60k major service'
    },
    'Emergency Repair Fund': {
        'monthly': 125.00,  # $1,500/year
        'annual': 1500.00,
        'notes': 'Buffer for unexpected repairs, tires, breakdowns'
    }
}

# Total vehicle maintenance monthly budget
TOTAL_VEHICLE_MONTHLY = sum(v['monthly'] for v in VEHICLE_MAINTENANCE_2026.values())  # $400/month

# Additional 2026 expenses
ADDITIONAL_2026_EXPENSES = {
    'IRS Tax Payment': {
        'amount': 5000.00,
        'frequency': 'one-time',
        'month': 'April 2026',
        'notes': 'Outstanding tax liability from 2025'
    }
}

def get_inflation_rate(category):
    """Get inflation rate for a category, default to 3.5% if not found"""
    return INFLATION_RATES.get(category, 0.035)


def print_inflation_summary():
    """Print summary of inflation rates"""
    print("="*80)
    print("2026 INFLATION RATES (Conservative Estimates)")
    print("="*80)

    # Group by rate
    by_rate = {}
    for category, rate in sorted(INFLATION_RATES.items(), key=lambda x: x[1], reverse=True):
        rate_pct = f"{rate*100:.1f}%"
        if rate_pct not in by_rate:
            by_rate[rate_pct] = []
        by_rate[rate_pct].append(category)

    for rate_pct, categories in sorted(by_rate.items(), key=lambda x: float(x[0].strip('%')), reverse=True):
        print(f"\n{rate_pct} Inflation:")
        for cat in categories:
            print(f"  - {cat}")

    print("\n" + "="*80)
    print("VEHICLE MAINTENANCE BUDGET (NEW for 2026)")
    print("="*80)
    for vehicle, details in VEHICLE_MAINTENANCE_2026.items():
        print(f"\n{vehicle}:")
        print(f"  Monthly: ${details['monthly']:.2f}")
        print(f"  Annual: ${details['annual']:.2f}")
        print(f"  Notes: {details['notes']}")

    print(f"\nTotal Vehicle Budget: ${TOTAL_VEHICLE_MONTHLY:.2f}/month (${TOTAL_VEHICLE_MONTHLY*12:.2f}/year)")

    print("\n" + "="*80)
    print("ADDITIONAL 2026 EXPENSES")
    print("="*80)
    for expense, details in ADDITIONAL_2026_EXPENSES.items():
        print(f"\n{expense}:")
        print(f"  Amount: ${details['amount']:.2f}")
        print(f"  Frequency: {details['frequency']}")
        print(f"  Timing: {details['month']}")
        print(f"  Notes: {details['notes']}")


if __name__ == "__main__":
    print_inflation_summary()

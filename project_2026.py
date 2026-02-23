#!/usr/bin/env python3
"""
Project 2026 budget based on 2025 actuals + inflation + new vehicle costs
"""
import sqlite3
import pandas as pd
from inflation_rates import get_inflation_rate, TOTAL_VEHICLE_MONTHLY, ADDITIONAL_2026_EXPENSES

DB_PATH = "budget_analysis.db"
TARGET_MONTHLY_INCOME = 10800.00  # Base monthly income goal

def project_2026_budget():
    """Generate 2026 budget projections"""

    print("="*100)
    print("2026 BUDGET PROJECTION")
    print("="*100)

    conn = sqlite3.connect(DB_PATH)

    # Load 2025 category spending
    category_df = pd.read_sql("SELECT * FROM category_summary", conn)

    print(f"\nTarget Monthly Income: ${TARGET_MONTHLY_INCOME:,.2f}")
    print(f"Vehicle Maintenance (NEW): ${TOTAL_VEHICLE_MONTHLY:,.2f}/month\n")

    # Calculate 2026 projections
    projections = []

    total_2025_monthly = 0
    total_inflation_impact = 0
    total_2026_monthly = 0

    print(f"{'Category':<25} {'2025 Avg':>12} {'Inflation':>10} {'Impact':>12} {'2026 Proj':>12}")
    print("-"*100)

    for _, row in category_df.iterrows():
        category = row['category']
        avg_2025 = row['monthly_average']
        inflation_rate = get_inflation_rate(category)
        inflation_amount = avg_2025 * inflation_rate
        projected_2026 = avg_2025 + inflation_amount

        total_2025_monthly += avg_2025
        total_inflation_impact += inflation_amount
        total_2026_monthly += projected_2026

        print(f"{category:<25} ${avg_2025:>11,.2f} {inflation_rate*100:>9.1f}% ${inflation_amount:>11,.2f} ${projected_2026:>11,.2f}")

        projections.append({
            'category': category,
            'avg_2025': avg_2025,
            'inflation_rate': inflation_rate,
            'inflation_amount': inflation_amount,
            'projected_2026': projected_2026,
            'notes': ''
        })

    # Add vehicle maintenance as new category
    print(f"{'Vehicle Maintenance (NEW)':<25} ${'0.00':>11} {'N/A':>10} ${TOTAL_VEHICLE_MONTHLY:>11,.2f} ${TOTAL_VEHICLE_MONTHLY:>11,.2f}")

    projections.append({
        'category': 'Vehicle Maintenance',
        'avg_2025': 0.00,
        'inflation_rate': 0.00,
        'inflation_amount': TOTAL_VEHICLE_MONTHLY,
        'projected_2026': TOTAL_VEHICLE_MONTHLY,
        'notes': 'NEW: 2 vehicles + emergency fund'
    })

    total_2026_monthly += TOTAL_VEHICLE_MONTHLY

    # Totals
    print("-"*100)
    print(f"{'TOTAL':<25} ${total_2025_monthly:>11,.2f} {'':>10} ${total_inflation_impact + TOTAL_VEHICLE_MONTHLY:>11,.2f} ${total_2026_monthly:>11,.2f}")

    # Gap analysis
    print("\n" + "="*100)
    print("GAP ANALYSIS")
    print("="*100)

    gap_2026 = total_2026_monthly - TARGET_MONTHLY_INCOME
    gap_2025 = total_2025_monthly - TARGET_MONTHLY_INCOME

    print(f"\n2025 Actual:")
    print(f"  Monthly expenses:      ${total_2025_monthly:>12,.2f}")
    print(f"  Target income:         ${TARGET_MONTHLY_INCOME:>12,.2f}")
    print(f"  Gap:                   ${gap_2025:>12,.2f}")

    print(f"\n2026 Projected:")
    print(f"  Monthly expenses:      ${total_2026_monthly:>12,.2f}")
    print(f"  Target income:         ${TARGET_MONTHLY_INCOME:>12,.2f}")
    print(f"  Gap:                   ${gap_2026:>12,.2f}")

    print(f"\nChange from 2025 to 2026:")
    print(f"  Inflation impact:      ${total_inflation_impact:>12,.2f}")
    print(f"  Vehicle costs (NEW):   ${TOTAL_VEHICLE_MONTHLY:>12,.2f}")
    print(f"  Total increase:        ${gap_2026 - gap_2025:>12,.2f}")

    # Annual impact
    print(f"\nAnnual 2026:")
    print(f"  Projected expenses:    ${total_2026_monthly * 12:>12,.2f}")
    print(f"  Target income:         ${TARGET_MONTHLY_INCOME * 12:>12,.2f}")
    print(f"  Annual gap:            ${gap_2026 * 12:>12,.2f}")

    # Add one-time expenses
    one_time_total = sum(exp['amount'] for exp in ADDITIONAL_2026_EXPENSES.values())
    print(f"\n  One-time expenses:     ${one_time_total:>12,.2f} (IRS tax payment)")
    print(f"  TOTAL 2026 SHORTFALL:  ${gap_2026 * 12 + one_time_total:>12,.2f}")

    # Categories with highest inflation impact
    print("\n" + "="*100)
    print("TOP 10 CATEGORIES BY INFLATION IMPACT")
    print("="*100)

    inflation_sorted = sorted(projections, key=lambda x: x['inflation_amount'], reverse=True)
    for i, proj in enumerate(inflation_sorted[:10], 1):
        if proj['category'] == 'Vehicle Maintenance':
            print(f"{i:>2}. {proj['category']:<25} +${proj['inflation_amount']:>10,.2f}/month (NEW EXPENSE)")
        else:
            pct = proj['inflation_rate'] * 100
            print(f"{i:>2}. {proj['category']:<25} +${proj['inflation_amount']:>10,.2f}/month ({pct:.1f}% inflation)")

    # Save to database
    print("\n" + "-"*100)
    print("LOADING INTO DATABASE")
    print("-"*100)

    proj_df = pd.DataFrame(projections)
    proj_df.to_sql('projected_2026_budget', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(proj_df)} categories into projected_2026_budget table")

    # Inflation impact table
    inflation_df = proj_df[['category', 'inflation_rate', 'inflation_amount']].copy()
    inflation_df['monthly_impact'] = inflation_df['inflation_amount']
    inflation_df['annual_impact'] = inflation_df['inflation_amount'] * 12
    inflation_df['rank'] = inflation_df['monthly_impact'].rank(ascending=False, method='min').astype(int)
    inflation_df = inflation_df.sort_values('monthly_impact', ascending=False)

    inflation_df.to_sql('inflation_impact', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(inflation_df)} categories into inflation_impact table")

    # Vehicle maintenance details
    vehicle_data = []
    from inflation_rates import VEHICLE_MAINTENANCE_2026
    for vehicle, details in VEHICLE_MAINTENANCE_2026.items():
        vehicle_data.append({
            'vehicle_name': vehicle,
            'monthly_budget': details['monthly'],
            'annual_budget': details['annual'],
            'description': details['notes']
        })

    vehicle_df = pd.DataFrame(vehicle_data)
    vehicle_df.to_sql('vehicle_maintenance_2026', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(vehicle_df)} vehicles into vehicle_maintenance_2026 table")

    conn.close()

    print("\n" + "="*100)
    print("2026 PROJECTION COMPLETE")
    print("="*100)
    print(f"\nKEY TAKEAWAY:")
    print(f"  You need to reduce spending by ${gap_2026:,.2f}/month (${gap_2026*12:,.2f}/year)")
    print(f"  Plus one-time IRS payment of ${one_time_total:,.2f}")
    print(f"  Total 2026 funding needed: ${gap_2026*12 + one_time_total:,.2f}")

    return proj_df


if __name__ == "__main__":
    project_2026_budget()

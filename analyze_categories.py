#!/usr/bin/env python3
"""
Analyze 2025 category spending breakdown
Calculate totals, averages, and percentages for each category
"""
import sqlite3
import pandas as pd

DB_PATH = "budget_analysis.db"

def analyze_categories():
    """Generate category spending breakdown"""

    print("="*100)
    print("CATEGORY SPENDING BREAKDOWN - 2025")
    print("="*100)

    conn = sqlite3.connect(DB_PATH)

    # Get expense transactions only (Amount > 0)
    df = pd.read_sql("SELECT * FROM transactions WHERE Amount > 0", conn)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    # Calculate category statistics
    total_expenses = df['Amount'].sum()

    category_stats = []

    for category in sorted(df['Category'].unique()):
        cat_df = df[df['Category'] == category]

        total_2025 = cat_df['Amount'].sum()
        monthly_avg = total_2025 / 12
        pct_of_total = (total_2025 / total_expenses) * 100
        transaction_count = len(cat_df)

        # Monthly min/max
        monthly_totals = cat_df.groupby('Month')['Amount'].sum()
        min_monthly = monthly_totals.min() if len(monthly_totals) > 0 else 0
        max_monthly = monthly_totals.max() if len(monthly_totals) > 0 else 0

        # Assign discretion level
        discretion_level = assign_discretion_level(category)

        category_stats.append({
            'category': category,
            'total_2025': total_2025,
            'monthly_average': monthly_avg,
            'pct_of_total': pct_of_total,
            'transaction_count': transaction_count,
            'min_monthly': min_monthly,
            'max_monthly': max_monthly,
            'discretion_level': discretion_level
        })

    # Sort by monthly average (descending)
    category_stats.sort(key=lambda x: x['monthly_average'], reverse=True)

    # Display
    print(f"\nTotal 2025 Expenses: ${total_expenses:,.2f}")
    print(f"Average Monthly: ${total_expenses/12:,.2f}\n")

    print(f"{'Category':<25} {'Total 2025':>12} {'Monthly Avg':>12} {'% of Total':>10} {'Transactions':>12} {'Discretion':>15}")
    print("-"*100)

    for cat in category_stats:
        print(f"{cat['category']:<25} ${cat['total_2025']:>11,.2f} ${cat['monthly_average']:>11,.2f} "
              f"{cat['pct_of_total']:>9.1f}% {cat['transaction_count']:>12} {cat['discretion_level']:>15}")

    # Summary by discretion level
    print("\n" + "="*100)
    print("SPENDING BY DISCRETION LEVEL")
    print("="*100)

    discretion_summary = {}
    for cat in category_stats:
        level = cat['discretion_level']
        if level not in discretion_summary:
            discretion_summary[level] = 0
        discretion_summary[level] += cat['total_2025']

    for level in ['Essential', 'Low Discretion', 'Medium Discretion', 'High Discretion']:
        if level in discretion_summary:
            amount = discretion_summary[level]
            pct = (amount / total_expenses) * 100
            print(f"{level:<20} ${amount:>12,.2f} ({pct:>5.1f}%) - ${amount/12:>10,.2f}/month")

    # Top spending categories
    print("\n" + "="*100)
    print("TOP 10 SPENDING CATEGORIES (By Monthly Average)")
    print("="*100)

    for i, cat in enumerate(category_stats[:10], 1):
        print(f"{i:>2}. {cat['category']:<25} ${cat['monthly_average']:>10,.2f}/month "
              f"(${cat['total_2025']:>10,.2f}/year, {cat['pct_of_total']:>5.1f}%)")

    # Save to database
    print("\n" + "-"*100)
    print("LOADING INTO DATABASE")
    print("-"*100)

    category_df = pd.DataFrame(category_stats)
    category_df.to_sql('category_summary', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(category_df)} categories into category_summary table")

    conn.close()

    print("\n" + "="*100)
    print("CATEGORY ANALYSIS COMPLETE")
    print("="*100)

    return category_df


def assign_discretion_level(category):
    """Assign discretion level to category for scenario planning"""

    high_discretion = [
        'Dining & Drinks',
        'Shopping',
        'Entertainment & Rec.',
        'Charitable Donations'
    ]

    medium_discretion = [
        'Groceries',
        'Personal Care',
        'Auto & Transport',
        'Software & Tech',
        'Home & Garden',
        'Cash & Checks',
        'Uncategorized'
    ]

    low_discretion = [
        'Bills & Utilities',
        'Pets',
        'Kids Activities',
        'Education',
        'Fees'
    ]

    essential = [
        'Medical',
        'Health & Wellness',
        'Taxes',
        'Legal',
        'Loan Payment'
    ]

    if category in high_discretion:
        return 'High Discretion'
    elif category in medium_discretion:
        return 'Medium Discretion'
    elif category in low_discretion:
        return 'Low Discretion'
    elif category in essential:
        return 'Essential'
    else:
        return 'Medium Discretion'  # Default


if __name__ == "__main__":
    analyze_categories()

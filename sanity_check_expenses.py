#!/usr/bin/env python3
"""
Sanity check expenses - look for anomalies, spikes, and one-time purchases
"""
import pandas as pd
import sqlite3

DB_PATH = "budget_analysis.db"

def sanity_check_expenses():
    """Analyze expenses for anomalies"""

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM transactions WHERE Amount > 0", conn)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    print("="*100)
    print("EXPENSE SANITY CHECK - LOOKING FOR ANOMALIES")
    print("="*100)

    # 1. Find largest individual transactions
    print("\n" + "="*100)
    print("TOP 20 LARGEST EXPENSE TRANSACTIONS")
    print("="*100)
    top_expenses = df.nlargest(20, 'Amount')[['Date', 'Name', 'Amount', 'Category', 'Description']]
    print(top_expenses.to_string(index=False))

    # 2. Monthly spending by category - look for spikes
    print("\n" + "="*100)
    print("MONTHLY SPENDING BY CATEGORY - LOOKING FOR SPIKES")
    print("="*100)

    monthly_cat = df.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
    pivot = monthly_cat.pivot(index='Month', columns='Category', values='Amount').fillna(0)

    # For each category, show months with unusually high spending
    print("\nCategories with monthly spikes (>2x monthly average):\n")

    for category in pivot.columns:
        monthly_avg = pivot[category].mean()
        monthly_max = pivot[category].max()

        if monthly_max > monthly_avg * 2 and monthly_avg > 100:  # Only show if significant
            spike_months = pivot[pivot[category] > monthly_avg * 2][category]
            if len(spike_months) > 0:
                print(f"\n{category}:")
                print(f"  Average: ${monthly_avg:>8,.2f}/month")
                print(f"  Maximum: ${monthly_max:>8,.2f}/month")
                print(f"  Spike months:")
                for month, amount in spike_months.items():
                    pct = (amount / monthly_avg - 1) * 100
                    print(f"    {month}: ${amount:>8,.2f} ({pct:>5.0f}% above average)")

    # 3. Check for categories that might be one-time or irregular
    print("\n" + "="*100)
    print("TRANSACTION FREQUENCY BY CATEGORY")
    print("="*100)
    print("(Categories with few transactions might be one-time expenses)\n")

    cat_stats = df.groupby('Category').agg({
        'Amount': ['sum', 'count', 'mean', 'max']
    }).round(2)
    cat_stats.columns = ['Total', 'Count', 'Avg', 'Max']
    cat_stats['Monthly_Avg'] = cat_stats['Total'] / 12
    cat_stats = cat_stats.sort_values('Total', ascending=False)

    print(f"{'Category':<25} {'Total 2025':>12} {'Count':>6} {'Avg Trans':>10} {'Max Trans':>10} {'Monthly':>12}")
    print("-"*100)
    for cat, row in cat_stats.iterrows():
        print(f"{cat:<25} ${row['Total']:>11,.2f} {int(row['Count']):>6} ${row['Avg']:>9,.2f} ${row['Max']:>9,.2f} ${row['Monthly_Avg']:>11,.2f}")

    # 4. Look for large single transactions that might skew averages
    print("\n" + "="*100)
    print("CATEGORIES WITH LARGE SINGLE TRANSACTIONS")
    print("="*100)
    print("(Single transaction > 50% of category total might indicate one-time expense)\n")

    for category in df['Category'].unique():
        cat_df = df[df['Category'] == category]
        total = cat_df['Amount'].sum()
        max_trans = cat_df['Amount'].max()

        if max_trans > total * 0.5 and total > 500:  # Large transaction dominates category
            print(f"\n{category}:")
            print(f"  Total 2025: ${total:,.2f}")
            print(f"  Largest transaction: ${max_trans:,.2f} ({max_trans/total*100:.1f}% of total)")
            print(f"  Transaction details:")
            largest = cat_df.nlargest(3, 'Amount')[['Date', 'Name', 'Amount']]
            for _, row in largest.iterrows():
                print(f"    {row['Date']}: {row['Name']:<40} ${row['Amount']:>10,.2f}")

    # 5. December spike analysis (we saw large deficit there)
    print("\n" + "="*100)
    print("DECEMBER 2025 DETAILED ANALYSIS")
    print("="*100)
    print("(December had largest deficit: -$10,219)\n")

    dec_df = df[df['Month'] == '2025-12']
    dec_by_cat = dec_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)

    print(f"{'Category':<25} {'December Total':>15}")
    print("-"*45)
    for cat, amount in dec_by_cat.items():
        print(f"{cat:<25} ${amount:>14,.2f}")

    print(f"\nTop 10 December transactions:")
    dec_top = dec_df.nlargest(10, 'Amount')[['Date', 'Name', 'Amount', 'Category']]
    print(dec_top.to_string(index=False))

    conn.close()

    print("\n" + "="*100)
    print("SANITY CHECK COMPLETE")
    print("="*100)

if __name__ == "__main__":
    sanity_check_expenses()

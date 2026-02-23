#!/usr/bin/env python3
"""
Analyze 2025 monthly cashflow
Calculate month-by-month income vs expenses with cumulative position
"""
import sqlite3
import pandas as pd

DB_PATH = "budget_analysis.db"
CSV_PATH = "/mnt/c/Users/dangr/Downloads/2026-01-03T19_06_39.183Z-transactions.csv"

def analyze_monthly_cashflow():
    """Generate month-by-month cashflow analysis"""

    print("="*80)
    print("MONTHLY CASHFLOW ANALYSIS - 2025")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)

    # Load included transactions from database
    df = pd.read_sql("SELECT * FROM transactions", conn)
    df['Date'] = pd.to_datetime(df['Date'])

    # Also load original CSV to check for bonus income in excluded categories
    df_all = pd.read_csv(CSV_PATH)
    df_all['Date'] = pd.to_datetime(df_all['Date'])
    df_all_2025 = df_all[(df_all['Date'] >= '2025-01-01') & (df_all['Date'] <= '2025-12-31')]

    # Group by month
    df['Month'] = df['Date'].dt.to_period('M').astype(str)

    monthly_data = []

    for month in sorted(df['Month'].unique()):
        month_df = df[df['Month'] == month]

        # Income is negative in the data (convert to positive)
        income_df = month_df[month_df['Amount'] < 0]
        base_income = income_df['Amount'].sum() * -1

        # Expenses are positive
        expense_df = month_df[month_df['Amount'] > 0]
        expenses = expense_df['Amount'].sum()

        # Check if this month had bonus income (from excluded categories)
        bonus_df = df_all_2025[(df_all_2025['Date'].dt.to_period('M').astype(str) == month) &
                               (df_all_2025['Category'] == 'Bonus Income')]
        has_bonus = len(bonus_df) > 0
        bonus_amount = (bonus_df['Amount'].sum() * -1) if has_bonus else 0.0

        # Net cashflow
        net_cashflow = base_income - expenses

        monthly_data.append({
            'month': month,
            'base_income': base_income,
            'other_income': 0.0,  # We can refine this later
            'total_income': base_income,
            'expenses': expenses,
            'net_cashflow': net_cashflow,
            'has_bonus': 1 if has_bonus else 0,
            'bonus_amount': bonus_amount,
            'cumulative_cashflow': 0.0  # Calculate after loop
        })

    # Calculate cumulative cashflow
    cumulative = 0.0
    for row in monthly_data:
        cumulative += row['net_cashflow']
        row['cumulative_cashflow'] = cumulative

    # Create DataFrame
    monthly_df = pd.DataFrame(monthly_data)

    print("\nMONTH-BY-MONTH BREAKDOWN:")
    print("-"*120)
    print(f"{'Month':<10} {'Base Income':>12} {'Expenses':>12} {'Net Cashflow':>14} {'Cumulative':>14} {'Bonus?':<8}")
    print("-"*120)

    for _, row in monthly_df.iterrows():
        bonus_marker = f"${row['bonus_amount']:>8,.0f}" if row['has_bonus'] else "-"
        print(f"{row['month']:<10} ${row['base_income']:>11,.2f} ${row['expenses']:>11,.2f} "
              f"${row['net_cashflow']:>13,.2f} ${row['cumulative_cashflow']:>13,.2f} {bonus_marker:<8}")

    # Summary stats
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    avg_income = monthly_df['base_income'].mean()
    avg_expenses = monthly_df['expenses'].mean()
    avg_net = monthly_df['net_cashflow'].mean()

    deficit_months = len(monthly_df[monthly_df['net_cashflow'] < 0])
    surplus_months = len(monthly_df[monthly_df['net_cashflow'] > 0])

    print(f"\nAverage monthly base income:  ${avg_income:>12,.2f}")
    print(f"Average monthly expenses:     ${avg_expenses:>12,.2f}")
    print(f"Average monthly net cashflow: ${avg_net:>12,.2f}")

    print(f"\nMonths with deficit:  {deficit_months}")
    print(f"Months with surplus:  {surplus_months}")

    total_bonus = monthly_df['bonus_amount'].sum()
    print(f"\nTotal bonus income (excluded from analysis): ${total_bonus:,.2f}")

    # Months with bonuses
    bonus_months = monthly_df[monthly_df['has_bonus'] == 1]
    if len(bonus_months) > 0:
        print(f"\nMonths with bonus income ({len(bonus_months)}):")
        for _, row in bonus_months.iterrows():
            print(f"  {row['month']}: ${row['bonus_amount']:>10,.2f}")

    # Insert into database
    print("\n" + "-"*80)
    print("LOADING INTO DATABASE")
    print("-"*80)

    monthly_df_db = monthly_df[['month', 'base_income', 'other_income', 'total_income',
                                  'expenses', 'net_cashflow', 'has_bonus', 'cumulative_cashflow']]

    monthly_df_db.to_sql('monthly_summary', conn, if_exists='replace', index=False)
    print(f"✓ Loaded {len(monthly_df_db)} months into monthly_summary table")

    conn.close()

    print("\n" + "="*80)
    print("MONTHLY ANALYSIS COMPLETE")
    print("="*80)

    return monthly_df

if __name__ == "__main__":
    analyze_monthly_cashflow()

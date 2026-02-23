#!/usr/bin/env python3
"""
Load and validate 2025 transaction data from Rocket Money CSV
Filters data, applies exclusion rules, and loads into SQLite database
"""
import pandas as pd
import sqlite3
from datetime import datetime

CSV_PATH = "/mnt/c/Users/dangr/Downloads/2026-01-03T19_06_39.183Z-transactions.csv"
DB_PATH = "budget_analysis.db"

# Categories to EXCLUDE from analysis
EXCLUDED_CATEGORIES = [
    'Bonus Income',
    'Bonus Spend',
    'Home Renovation',
    'Unexpected',
    'Company Travel',
    'Work Expense',
    'Credit Card Payment',
    'Internal Transfers',
    'Reimbursement',
    'Investment'  # One-time investment liquidations, not recurring income
]

def load_and_validate_data():
    """Load CSV, filter to 2025, apply exclusions, and insert into database"""

    print("="*80)
    print("LOADING TRANSACTION DATA")
    print("="*80)

    # Load CSV
    print(f"\nReading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"✓ Loaded {len(df):,} total transactions")

    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Show date range
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")

    # Filter to 2025 only
    print("\n" + "-"*80)
    print("FILTERING TO 2025 (Jan 1 - Dec 31, 2025)")
    print("-"*80)

    df_2025 = df[(df['Date'] >= '2025-01-01') & (df['Date'] <= '2025-12-31')].copy()

    # Apply manual corrections
    # $4,200 loan payment was actually bonus-funded debt paydown
    df_2025.loc[(df_2025['Date'] == '2025-01-06') &
                (df_2025['Name'] == 'JPMorgan Chase') &
                (df_2025['Amount'] == 4200.0), 'Category'] = 'Bonus Spend'
    print("✓ Applied manual categorization corrections")
    print(f"✓ Filtered to 2025: {len(df_2025):,} transactions")

    # Apply category exclusions
    print("\n" + "-"*80)
    print("APPLYING CATEGORY EXCLUSIONS")
    print("-"*80)

    print(f"\nExcluding {len(EXCLUDED_CATEGORIES)} categories:")
    for cat in EXCLUDED_CATEGORIES:
        count = len(df_2025[df_2025['Category'] == cat])
        print(f"  - {cat:<30} ({count:>4} transactions)")

    df_included = df_2025[~df_2025['Category'].isin(EXCLUDED_CATEGORIES)].copy()
    df_excluded = df_2025[df_2025['Category'].isin(EXCLUDED_CATEGORIES)].copy()

    print(f"\n✓ Included transactions: {len(df_included):,}")
    print(f"✓ Excluded transactions: {len(df_excluded):,}")

    # Show included categories
    print("\n" + "-"*80)
    print("INCLUDED CATEGORIES")
    print("-"*80)
    included_cats = df_included['Category'].value_counts().sort_index()
    print(f"\nTotal unique categories: {len(included_cats)}\n")
    for cat, count in included_cats.items():
        print(f"  {cat:<30} ({count:>5,} transactions)")

    # Income vs Expense breakdown
    print("\n" + "-"*80)
    print("INCOME VS EXPENSE BREAKDOWN (Included Transactions Only)")
    print("-"*80)

    # Income is negative, expense is positive in the data
    income_transactions = df_included[df_included['Amount'] < 0]
    expense_transactions = df_included[df_included['Amount'] > 0]

    total_income = income_transactions['Amount'].sum() * -1  # Convert to positive
    total_expenses = expense_transactions['Amount'].sum()
    net = total_income - total_expenses

    print(f"\nIncome transactions:   {len(income_transactions):>5,} (${total_income:>12,.2f})")
    print(f"Expense transactions:  {len(expense_transactions):>5,} (${total_expenses:>12,.2f})")
    print(f"Net cashflow:                            ${net:>12,.2f}")

    # Break down income by category
    print("\n" + "-"*80)
    print("INCOME SOURCES (2025)")
    print("-"*80)
    income_by_cat = income_transactions.groupby('Category')['Amount'].sum() * -1
    for cat, amount in income_by_cat.sort_values(ascending=False).items():
        print(f"  {cat:<30} ${amount:>12,.2f}")

    # Sample transactions
    print("\n" + "-"*80)
    print("SAMPLE INCLUDED TRANSACTIONS (First 10)")
    print("-"*80)
    sample = df_included.head(10)[['Date', 'Name', 'Amount', 'Category']]
    print(sample.to_string(index=False))

    print("\n" + "-"*80)
    print("SAMPLE EXCLUDED TRANSACTIONS (First 10)")
    print("-"*80)
    sample_excluded = df_excluded.head(10)[['Date', 'Name', 'Amount', 'Category']]
    print(sample_excluded.to_string(index=False))

    # Load into database
    print("\n" + "="*80)
    print("LOADING DATA INTO DATABASE")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)

    # Insert included transactions
    df_included.to_sql('transactions', conn, if_exists='replace', index=False,
                       dtype={'date': 'DATE'})

    print(f"✓ Loaded {len(df_included):,} transactions into database")

    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]
    print(f"✓ Verified: {count:,} records in database")

    conn.close()

    print("\n" + "="*80)
    print("DATA LOADING COMPLETE")
    print("="*80)
    print(f"✓ {len(df_included):,} transactions ready for analysis")
    print(f"✓ Date range: 2025-01-01 to 2025-12-31")
    print(f"✓ {len(included_cats)} spending categories")
    print(f"✓ Total income: ${total_income:,.2f}")
    print(f"✓ Total expenses: ${total_expenses:,.2f}")
    print(f"✓ Net cashflow: ${net:,.2f}")

    return df_included

if __name__ == "__main__":
    load_and_validate_data()

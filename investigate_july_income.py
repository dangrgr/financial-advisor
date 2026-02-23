#!/usr/bin/env python3
"""
Investigate July 2025 income spike
"""
import pandas as pd
import sqlite3

DB_PATH = "budget_analysis.db"

def investigate_july():
    conn = sqlite3.connect(DB_PATH)

    # Get all income transactions (negative amounts) from July 2025
    query = """
        SELECT Date, Name, "Institution Name", Amount, Category, Description
        FROM transactions
        WHERE Date >= '2025-07-01' AND Date <= '2025-07-31'
          AND Amount < 0
        ORDER BY Amount
    """

    df = pd.read_sql(query, conn)
    df['Amount_Positive'] = df['Amount'] * -1

    print("="*80)
    print("JULY 2025 INCOME TRANSACTIONS")
    print("="*80)

    print(f"\nTotal income transactions: {len(df)}")
    print(f"Total income amount: ${df['Amount_Positive'].sum():,.2f}\n")

    print("All transactions:")
    print("-"*80)
    for _, row in df.iterrows():
        print(f"{row['Date']}: {row['Name']:<40} ${row['Amount_Positive']:>12,.2f}  ({row['Category']})")
        if pd.notna(row['Institution Name']):
            print(f"           Institution: {row['Institution Name']}")

    # Check for Vanguard transactions
    print("\n" + "="*80)
    print("VANGUARD TRANSACTIONS")
    print("="*80)
    vanguard = df[df['Name'].str.contains('Vanguard', case=False, na=False) |
                  df['Institution Name'].str.contains('Vanguard', case=False, na=False)]

    if len(vanguard) > 0:
        print(f"\nFound {len(vanguard)} Vanguard transaction(s):")
        print(f"Total from Vanguard: ${vanguard['Amount_Positive'].sum():,.2f}\n")
        for _, row in vanguard.iterrows():
            print(f"  {row['Date']}: {row['Name']:<40} ${row['Amount_Positive']:>12,.2f}")
    else:
        print("\nNo Vanguard transactions found by name")

    # Check Investment category
    print("\n" + "="*80)
    print("INVESTMENT CATEGORY TRANSACTIONS")
    print("="*80)
    investment = df[df['Category'] == 'Investment']

    if len(investment) > 0:
        print(f"\nFound {len(investment)} Investment category transaction(s):")
        print(f"Total from Investment category: ${investment['Amount_Positive'].sum():,.2f}\n")
        for _, row in investment.iterrows():
            print(f"  {row['Date']}: {row['Name']:<40} ${row['Amount_Positive']:>12,.2f}")
            if pd.notna(row['Description']):
                print(f"           Description: {row['Description']}")

    conn.close()

    return df

if __name__ == "__main__":
    investigate_july()

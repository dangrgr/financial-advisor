#!/usr/bin/env python3
"""
Find the typical bi-monthly base income amount
"""
import pandas as pd

# Read the CSV file
csv_path = "/mnt/c/Users/dangr/Downloads/2026-01-03T19_06_39.183Z-transactions.csv"
df = pd.read_csv(csv_path)
df['Date'] = pd.to_datetime(df['Date'])

# Filter to 2025 and Income category only (excluding Bonus Income)
df_2025 = df[(df['Date'] >= '2025-01-01') & (df['Date'] <= '2025-12-31')]
income_2025 = df_2025[(df_2025['Category'] == 'Income') & (df_2025['Amount'] < 0)].copy()

# Income is negative in the data, so convert to positive
income_2025['Amount'] = income_2025['Amount'] * -1

# Show all income transactions
print("="*80)
print("ALL 2025 BASE INCOME TRANSACTIONS (Category = 'Income')")
print("="*80)
print(income_2025[['Date', 'Name', 'Amount']].sort_values('Date').to_string(index=False))

# Find the most common income amount (rounded to nearest 100 for grouping)
print("\n" + "="*80)
print("INCOME AMOUNT FREQUENCY")
print("="*80)
income_2025['Amount_Rounded'] = income_2025['Amount'].round(-2)  # Round to nearest 100
amount_freq = income_2025['Amount_Rounded'].value_counts().sort_values(ascending=False)
print(amount_freq.head(10))

# Calculate most common bi-monthly amount
most_common = income_2025['Amount_Rounded'].mode()[0]
print(f"\nMost common bi-monthly income: ${most_common:,.2f}")
print(f"Target monthly income (x2): ${most_common * 2:,.2f}")

# Check for Bonus Income separately
bonus_income = df_2025[(df_2025['Category'] == 'Bonus Income') & (df_2025['Amount'] < 0)].copy()
bonus_income['Amount'] = bonus_income['Amount'] * -1
print("\n" + "="*80)
print("BONUS INCOME TRANSACTIONS (Category = 'Bonus Income')")
print("="*80)
if len(bonus_income) > 0:
    print(bonus_income[['Date', 'Name', 'Amount']].to_string(index=False))
    print(f"\nTotal Bonus Income 2025: ${bonus_income['Amount'].sum():,.2f}")
else:
    print("No bonus income found")

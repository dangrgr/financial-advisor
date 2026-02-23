#!/usr/bin/env python3
"""
Explore Rocket Money transaction data
"""
import pandas as pd
from datetime import datetime
import sys

# Read the CSV file
csv_path = "/mnt/c/Users/dangr/Downloads/2026-01-03T19_06_39.183Z-transactions.csv"
print(f"Reading {csv_path}...")
df = pd.read_csv(csv_path)

# Convert Date to datetime
df['Date'] = pd.to_datetime(df['Date'])

# Basic data info
print("\n" + "="*80)
print("DATA OVERVIEW")
print("="*80)
print(f"Total transactions: {len(df):,}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Columns: {', '.join(df.columns)}")

# Show unique categories
print("\n" + "="*80)
print("UNIQUE CATEGORIES IN YOUR DATA")
print("="*80)
categories = df['Category'].value_counts().sort_index()
print(f"\nTotal unique categories: {len(categories)}\n")
for cat, count in categories.items():
    print(f"  {cat:<30} ({count:>6,} transactions)")

# Filter to 2025 only
df_2025 = df[(df['Date'] >= '2025-01-01') & (df['Date'] <= '2025-12-31')]
print("\n" + "="*80)
print("2025 DATA ONLY")
print("="*80)
print(f"Total 2025 transactions: {len(df_2025):,}")
print(f"Date range: {df_2025['Date'].min()} to {df_2025['Date'].max()}")

# Categories in 2025
categories_2025 = df_2025['Category'].value_counts().sort_index()
print(f"\nCategories in 2025 data ({len(categories_2025)} unique):\n")
for cat, count in categories_2025.items():
    print(f"  {cat:<30} ({count:>6,} transactions)")

# Show sample transactions from 2025
print("\n" + "="*80)
print("SAMPLE 2025 TRANSACTIONS")
print("="*80)
sample = df_2025.head(20)[['Date', 'Name', 'Amount', 'Category']]
print(sample.to_string(index=False))

# Income vs Expense summary for 2025
print("\n" + "="*80)
print("2025 INCOME VS EXPENSE SUMMARY")
print("="*80)
income = df_2025[df_2025['Amount'] < 0]['Amount'].sum() * -1  # Income is negative
expense = df_2025[df_2025['Amount'] > 0]['Amount'].sum()
net = income - expense

print(f"Total Income:  ${income:,.2f}")
print(f"Total Expense: ${expense:,.2f}")
print(f"Net:           ${net:,.2f}")

#!/usr/bin/env python3
"""
Setup SQLite database for budget analysis
Creates all necessary tables for 2025 analysis and 2026 projections
"""
import sqlite3
import os

DB_PATH = "budget_analysis.db"

def setup_database():
    """Create SQLite database with all required tables"""

    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

    print(f"Creating new database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: transactions - filtered 2025 transaction data
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            original_date DATE,
            account_type TEXT,
            account_name TEXT,
            account_number TEXT,
            institution_name TEXT,
            name TEXT,
            custom_name TEXT,
            amount REAL NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            note TEXT,
            ignored_from TEXT,
            tax_deductible TEXT,
            transaction_tags TEXT
        )
    """)
    print("✓ Created table: transactions")

    # Table 2: monthly_summary - 2025 monthly cashflow
    cursor.execute("""
        CREATE TABLE monthly_summary (
            month TEXT PRIMARY KEY,
            base_income REAL NOT NULL,
            other_income REAL NOT NULL,
            total_income REAL NOT NULL,
            expenses REAL NOT NULL,
            net_cashflow REAL NOT NULL,
            has_bonus INTEGER NOT NULL DEFAULT 0,
            cumulative_cashflow REAL NOT NULL
        )
    """)
    print("✓ Created table: monthly_summary")

    # Table 3: category_summary - 2025 category spending
    cursor.execute("""
        CREATE TABLE category_summary (
            category TEXT PRIMARY KEY,
            total_2025 REAL NOT NULL,
            monthly_average REAL NOT NULL,
            pct_of_total REAL NOT NULL,
            transaction_count INTEGER NOT NULL,
            min_monthly REAL NOT NULL,
            max_monthly REAL NOT NULL,
            discretion_level TEXT NOT NULL
        )
    """)
    print("✓ Created table: category_summary")

    # Table 4: projected_2026_budget - 2026 projections
    cursor.execute("""
        CREATE TABLE projected_2026_budget (
            category TEXT PRIMARY KEY,
            avg_2025 REAL NOT NULL,
            inflation_rate REAL NOT NULL,
            inflation_amount REAL NOT NULL,
            projected_2026 REAL NOT NULL,
            notes TEXT
        )
    """)
    print("✓ Created table: projected_2026_budget")

    # Table 5: inflation_impact - inflation breakdown
    cursor.execute("""
        CREATE TABLE inflation_impact (
            category TEXT PRIMARY KEY,
            inflation_rate REAL NOT NULL,
            monthly_impact REAL NOT NULL,
            annual_impact REAL NOT NULL,
            rank INTEGER NOT NULL
        )
    """)
    print("✓ Created table: inflation_impact")

    # Table 6: vehicle_maintenance_2026 - new vehicle costs
    cursor.execute("""
        CREATE TABLE vehicle_maintenance_2026 (
            vehicle_name TEXT PRIMARY KEY,
            monthly_budget REAL NOT NULL,
            annual_budget REAL NOT NULL,
            description TEXT
        )
    """)
    print("✓ Created table: vehicle_maintenance_2026")

    # Table 7: scenarios_2026 - budget scenarios
    cursor.execute("""
        CREATE TABLE scenarios_2026 (
            scenario_name TEXT,
            category TEXT,
            current_2026 REAL NOT NULL,
            target_2026 REAL NOT NULL,
            reduction_pct REAL NOT NULL,
            reduction_amount REAL NOT NULL,
            PRIMARY KEY (scenario_name, category)
        )
    """)
    print("✓ Created table: scenarios_2026")

    # Table 8: bonus_allocation - bonus usage recommendations
    cursor.execute("""
        CREATE TABLE bonus_allocation (
            scenario_name TEXT PRIMARY KEY,
            monthly_shortfall REAL NOT NULL,
            annual_gap REAL NOT NULL,
            bonus_for_gap REAL NOT NULL,
            bonus_for_emergency REAL NOT NULL,
            bonus_for_discretionary REAL NOT NULL,
            total_bonus_needed REAL NOT NULL,
            recommendation TEXT
        )
    """)
    print("✓ Created table: bonus_allocation")

    # Create indices for faster queries
    cursor.execute("CREATE INDEX idx_transactions_date ON transactions(date)")
    cursor.execute("CREATE INDEX idx_transactions_category ON transactions(category)")
    cursor.execute("CREATE INDEX idx_monthly_summary_month ON monthly_summary(month)")
    print("✓ Created indices")

    conn.commit()
    conn.close()

    print(f"\n✓ Database setup complete: {DB_PATH}")
    print(f"  Total tables: 8")
    print(f"  Total indices: 3")

    return DB_PATH

if __name__ == "__main__":
    setup_database()

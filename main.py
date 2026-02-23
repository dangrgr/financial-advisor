#!/usr/bin/env python3
"""
Main orchestrator for budget analysis
Runs all analysis steps in sequence and generates final report
"""
import os
import sys

# Import all analysis modules
from setup_database import setup_database
from load_data import load_and_validate_data
from analyze_monthly import analyze_monthly_cashflow
from analyze_categories import analyze_categories
from inflation_rates import print_inflation_summary
from project_2026 import project_2026_budget
from scenarios_2026 import generate_2026_scenarios
from generate_report import generate_report

def main():
    """Run complete budget analysis pipeline"""

    print("="*100)
    print(" "*30 + "BUDGET ANALYSIS SYSTEM")
    print("="*100)
    print("\nThis analysis will:")
    print("  1. Set up SQLite database")
    print("  2. Load and validate 2025 transaction data")
    print("  3. Analyze 2025 monthly cashflow")
    print("  4. Analyze spending by category")
    print("  5. Project 2026 budget with inflation")
    print("  6. Generate budget reduction scenarios")
    print("  7. Create comprehensive report")
    print("\n" + "="*100)

    input("\nPress ENTER to begin analysis...")

    try:
        # Step 1: Setup database
        print("\n" + "="*100)
        print("STEP 1: SETTING UP DATABASE")
        print("="*100)
        setup_database()

        # Step 2: Load data
        print("\n" + "="*100)
        print("STEP 2: LOADING TRANSACTION DATA")
        print("="*100)
        load_and_validate_data()

        # Step 3: Monthly analysis
        print("\n" + "="*100)
        print("STEP 3: ANALYZING MONTHLY CASHFLOW")
        print("="*100)
        analyze_monthly_cashflow()

        # Step 4: Category analysis
        print("\n" + "="*100)
        print("STEP 4: ANALYZING CATEGORY SPENDING")
        print("="*100)
        analyze_categories()

        # Step 5: Show inflation rates
        print("\n" + "="*100)
        print("STEP 5: INFLATION RATES FOR 2026")
        print("="*100)
        print_inflation_summary()

        # Step 6: 2026 projection
        print("\n" + "="*100)
        print("STEP 6: PROJECTING 2026 BUDGET")
        print("="*100)
        project_2026_budget()

        # Step 7: Scenarios
        print("\n" + "="*100)
        print("STEP 7: GENERATING BUDGET SCENARIOS")
        print("="*100)
        generate_2026_scenarios()

        # Step 8: Final report
        print("\n" + "="*100)
        print("STEP 8: GENERATING FINAL REPORT")
        print("="*100)
        report_path = generate_report()

        # Summary
        print("\n" + "="*100)
        print(" "*35 + "ANALYSIS COMPLETE!")
        print("="*100)
        print(f"\n✓ Database created: budget_analysis.db")
        print(f"✓ Report generated: {report_path}")
        print(f"\nNext steps:")
        print(f"  1. Read the report: {report_path}")
        print(f"  2. Review recommended scenario (Balanced)")
        print(f"  3. Implement spending cuts")
        print(f"  4. Track progress monthly")
        print("\n" + "="*100)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: Analysis failed")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

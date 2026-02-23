#!/usr/bin/env python3
"""
Generate comprehensive markdown report with all findings and recommendations
"""
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "budget_analysis.db"
REPORT_PATH = "budget_report.md"

def generate_report():
    """Create comprehensive budget analysis report"""

    conn = sqlite3.connect(DB_PATH)

    # Load data
    monthly_df = pd.read_sql("SELECT * FROM monthly_summary", conn)
    category_df = pd.read_sql("SELECT * FROM category_summary", conn)
    proj_df = pd.read_sql("SELECT * FROM projected_2026_budget", conn)
    scenarios_df = pd.read_sql("SELECT * FROM scenarios_2026", conn)
    bonus_df = pd.read_sql("SELECT * FROM bonus_allocation", conn)

    # Calculate summaries
    total_2025_income = monthly_df['total_income'].sum()
    total_2025_expenses = monthly_df['expenses'].sum()
    net_2025 = total_2025_income - total_2025_expenses

    avg_monthly_income = monthly_df['total_income'].mean()
    avg_monthly_expenses = monthly_df['expenses'].mean()
    avg_monthly_deficit = avg_monthly_income - avg_monthly_expenses

    total_2026_baseline = proj_df['projected_2026'].sum()

    report = []

    # Header
    report.append(f"# Budget Analysis & 2026 Projection Report")
    report.append(f"")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Analysis Period:** 2025 (Jan 1 - Dec 31)")
    report.append(f"**Projection Period:** 2026")
    report.append(f"")
    report.append(f"---")
    report.append(f"")

    # Executive Summary
    report.append(f"## Executive Summary")
    report.append(f"")
    report.append(f"### 2025 Performance")
    report.append(f"- **Net Base Income:** ${total_2025_income:,.2f} (base salary + misc)")
    report.append(f"- **Total Expenses:** ${total_2025_expenses:,.2f}")
    report.append(f"- **Net Cashflow:** ${net_2025:,.2f} (deficit)")
    report.append(f"- **Average Monthly Income:** ${avg_monthly_income:,.2f}")
    report.append(f"- **Average Monthly Expenses:** ${avg_monthly_expenses:,.2f}")
    report.append(f"- **Average Monthly Deficit:** ${avg_monthly_deficit:,.2f}")
    report.append(f"")
    report.append(f"**Note:** Excludes bonuses ($90,642), investment sales ($54,152), and bonus-funded spending")
    report.append(f"")

    # January 2026 Actuals
    report.append(f"### January 2026 Actuals (as of Jan 18)")
    report.append(f"- **Subscription Cancellations:** Planet Fitness (-$36/month), Google One (-$20/month)")
    report.append(f"- **Vehicle Expenses:** $5,246 (car repair $4,746 + windshield $500)")
    report.append(f"- **Vehicle Budget Status:** 109% of annual budget used in 18 days")
    report.append(f"- **January Gap:** -$9,343 (covered by bonus/emergency fund)")
    report.append(f"")
    report.append(f"**Key Insight:** Early 2026 experience validates conservative planning and emergency fund importance.")
    report.append(f"")

    report.append(f"### 2026 Projection (Updated with Actuals)")
    # Update vehicle budget to $500/month and subtract subscription savings
    updated_vehicle_budget = 500.00  # Increased from $400 based on January actuals
    subscription_savings = 56.00  # Planet Fitness + Google One
    vehicle_increase = 100.00  # Difference from original $400 to new $500

    adjusted_2026_baseline = total_2026_baseline - subscription_savings + vehicle_increase

    report.append(f"- **Original Projection:** ${total_2026_baseline:,.2f}/month")
    report.append(f"- **Subscription Savings:** -${subscription_savings:,.2f}/month (Planet Fitness + Google One)")
    report.append(f"- **Vehicle Budget Increase:** +${vehicle_increase:,.2f}/month (realistic $500/month vs. $400)")
    report.append(f"- **Updated Monthly Expenses:** ${adjusted_2026_baseline:,.2f}")
    report.append(f"- **Target Monthly Income:** $10,800.00 (base salary)")
    report.append(f"- **Projected Monthly Gap:** ${adjusted_2026_baseline - 10800:,.2f}")
    report.append(f"- **Annual Funding Needed:** ${(adjusted_2026_baseline - 10800) * 12 + 5000:,.2f} (includes $5k IRS tax)")
    report.append(f"")

    # Key Findings
    report.append(f"## Key Findings")
    report.append(f"")
    report.append(f"### 1. **You're Currently Living $2,819/month Above Base Income**")
    report.append(f"In 2025, your recurring expenses ($13,752/month) exceeded your base income ($10,933/month) by $2,819/month. This $33,830 annual gap was covered by bonuses and investment sales.")
    report.append(f"")

    report.append(f"### 2. **2026 Will Be More Expensive (Updated: +$1,245/month)**")
    report.append(f"Due to inflation, vehicle costs, and early 2026 learnings:")
    report.append(f"- **Inflation impact:** +$801/month (avg 5.8% weighted)")
    report.append(f"- **Vehicle maintenance:** +$500/month (UPDATED from $400 based on Jan actuals)")
    report.append(f"- **Subscription savings:** -$56/month (Planet Fitness + Google One canceled)")
    report.append(f"- **Net increase:** +$1,245/month")
    report.append(f"")
    report.append(f"This brings the 2026 gap to **${adjusted_2026_baseline - 10800:,.2f}/month** (${(adjusted_2026_baseline - 10800)*12:,.2f}/year) before additional spending cuts.")
    report.append(f"")
    report.append(f"**January 2026 Reality Check:** Vehicle expenses were $5,246 in just 18 days (109% of original annual budget), validating the need for increased vehicle budgeting.")
    report.append(f"")

    report.append(f"### 3. **Biggest Cost Drivers**")
    report.append(f"Top 5 categories by monthly average:")
    top5 = category_df.nlargest(5, 'monthly_average')[['category', 'monthly_average', 'pct_of_total']]
    for _, row in top5.iterrows():
        report.append(f"- **{row['category']}**: ${row['monthly_average']:,.2f}/month ({row['pct_of_total']:.1f}%)")
    report.append(f"")

    report.append(f"### 4. **Inflation Hotspots for 2026**")
    inflation_impact = proj_df.nlargest(5, 'inflation_amount')[['category', 'inflation_amount', 'inflation_rate']]
    for _, row in inflation_impact.iterrows():
        if row['category'] == 'Vehicle Maintenance':
            report.append(f"- **{row['category']}**: +${row['inflation_amount']:,.2f}/month (NEW)")
        else:
            report.append(f"- **{row['category']}**: +${row['inflation_amount']:,.2f}/month ({row['inflation_rate']*100:.1f}% inflation)")
    report.append(f"")

    # Current Financial Position
    report.append(f"### 5. **Current Financial Position (as of Jan 18, 2026)**")
    report.append(f"")
    report.append(f"**Assets:**")
    report.append(f"- **Capital One Savings:** $80,544")
    report.append(f"- **Checking (net):** $21,063")
    report.append(f"- **Joint Taxable Brokerage:** $150,000")
    report.append(f"- **Total Liquid Assets:** $251,607")
    report.append(f"")
    report.append(f"**Emergency Fund Status:**")
    report.append(f"- Target (6 months): $89,982")
    report.append(f"- Current (Savings): $80,544")
    report.append(f"- Funded: 89.5%")
    report.append(f"- Shortfall: $9,438 (top up from next bonus)")
    report.append(f"")
    report.append(f"**Key Insight:** You're in MUCH better financial shape than it may appear. With $251k in liquid assets, you're not in crisis mode. The $28k annual shortfall (Balanced scenario) represents only 18.7% of your brokerage, giving you ~5 years to gradually adjust spending while preserving your emergency fund.")
    report.append(f"")

    # Account Structure Strategy
    report.append(f"## Account Structure Strategy")
    report.append(f"")
    report.append(f"### Recommended Separation of Purposes")
    report.append(f"")
    report.append(f"#### 🏦 Capital One Savings ($80,544) → **Emergency Fund ONLY**")
    report.append(f"- **Purpose:** Sacred reserve for TRUE emergencies only (job loss, major medical, critical home repair)")
    report.append(f"- **Target:** $89,982 (6 months of 2026 expenses)")
    report.append(f"- **Action:** Top up with $9,438 from next bonus (April or August)")
    report.append(f"- **Rule:** Once funded, DON'T touch unless facing genuine emergency")
    report.append(f"- **NOT for:** Car repairs, travel, discretionary spending, or cashflow gaps")
    report.append(f"")
    report.append(f"#### 📈 Joint Taxable Brokerage ($150,000) → **Freedom Fund**")
    report.append(f"- **Purpose:** Flexible wealth fund for multiple uses")
    report.append(f"  1. **Cashflow bridge** - Cover the $28,107 annual gap in 2026 (Balanced scenario)")
    report.append(f"  2. **Major discretionary** - Travel, home projects, large purchases")
    report.append(f"  3. **Lifestyle buffer** - Gives you ~5 years to gradually implement spending cuts")
    report.append(f"  4. **Long-term wealth** - Continues growing for eventual retirement")
    report.append(f"- **Strategy:** Draw $28,107 in 2026 to cover gap while implementing Balanced cuts gradually")
    report.append(f"- **Advantage:** Preserves emergency fund for actual emergencies while staying invested")
    report.append(f"")
    report.append(f"#### 💳 Checking ($21,063) → **Monthly Operating Cash**")
    report.append(f"- **Purpose:** Day-to-day expenses and bill payment")
    report.append(f"- **Target:** 1-2 months expenses ($15k-$30k)")
    report.append(f"- **Status:** Perfect level - maintain this buffer")
    report.append(f"")
    report.append(f"**Why This Separation Matters:**")
    report.append(f"- **Psychological:** Keeping emergency fund separate prevents slow erosion")
    report.append(f"- **Strategic:** Brokerage stays invested and grows while you draw strategically")
    report.append(f"- **Practical:** You're not in crisis - use structure to preserve your strong position")
    report.append(f"")

    # Monthly Breakdown
    report.append(f"## 2025 Monthly Cashflow Breakdown")
    report.append(f"")
    report.append(f"| Month | Income | Expenses | Net | Cumulative | Bonus? |")
    report.append(f"|-------|--------|----------|-----|------------|--------|")
    for _, row in monthly_df.iterrows():
        bonus_marker = "✓" if row['has_bonus'] else ""
        report.append(f"| {row['month']} | ${row['total_income']:,.0f} | ${row['expenses']:,.0f} | "
                     f"${row['net_cashflow']:,.0f} | ${row['cumulative_cashflow']:,.0f} | {bonus_marker} |")
    report.append(f"")
    report.append(f"**Key Observations:**")
    report.append(f"- Only 2 surplus months (February and one other)")
    report.append(f"- 10 deficit months averaging ${abs(avg_monthly_deficit):,.0f}/month")
    report.append(f"- Bonuses received in April ($1,818), August ($9,383), and December ($79,441)")
    report.append(f"")

    # Category Spending
    report.append(f"## 2025 Category Spending")
    report.append(f"")
    report.append(f"### By Discretion Level")
    report.append(f"")

    discretion_summary = category_df.groupby('discretion_level').agg({
        'total_2025': 'sum',
        'monthly_average': 'sum'
    }).sort_values('total_2025', ascending=False)

    for level, row in discretion_summary.iterrows():
        pct = (row['total_2025'] / total_2025_expenses) * 100
        report.append(f"- **{level}**: ${row['monthly_average']:,.0f}/month (${row['total_2025']:,.0f}/year, {pct:.1f}%)")
    report.append(f"")

    report.append(f"### All Categories")
    report.append(f"")
    report.append(f"| Category | Monthly Avg | Annual | % of Total | Discretion |")
    report.append(f"|----------|-------------|--------|------------|------------|")
    for _, row in category_df.sort_values('monthly_average', ascending=False).iterrows():
        report.append(f"| {row['category']} | ${row['monthly_average']:,.0f} | "
                     f"${row['total_2025']:,.0f} | {row['pct_of_total']:.1f}% | {row['discretion_level']} |")
    report.append(f"")

    # 2026 Scenarios
    report.append(f"## 2026 Budget Scenarios")
    report.append(f"")
    report.append(f"### Scenario Comparison (Updated with Vehicle Budget & Subscription Savings)")
    report.append(f"")
    report.append(f"| Scenario | Monthly Gap | Annual Gap | Bonus for Discretionary | Key Changes |")
    report.append(f"|----------|-------------|------------|-------------------------|-------------|")

    # Update scenarios to reflect new baseline
    updated_baseline_gap = float(adjusted_2026_baseline - 10800)
    conservative_cuts = 647.14
    balanced_cuts = 1337.94
    aggressive_cuts = 1968.35

    # Recalculate bonus available for each scenario
    available_bonus = 90642
    irs_tax = 5000
    jan_vehicle = 5246  # January actuals

    scenarios_summary = [
        ('Baseline (Updated)', updated_baseline_gap, updated_baseline_gap * 12,
         available_bonus - (updated_baseline_gap * 12) - irs_tax - jan_vehicle,
         'Includes +$100 vehicle, -$56 subscriptions'),
        ('Conservative', updated_baseline_gap - conservative_cuts,
                        (updated_baseline_gap - conservative_cuts) * 12,
                        available_bonus - ((updated_baseline_gap - conservative_cuts) * 12) - irs_tax - jan_vehicle,
                        '15% cuts on shopping/dining'),
        ('Balanced', updated_baseline_gap - balanced_cuts,
                    (updated_baseline_gap - balanced_cuts) * 12,
                    available_bonus - ((updated_baseline_gap - balanced_cuts) * 12) - irs_tax - jan_vehicle,
                    '25% cuts + groceries'),
        ('Aggressive', updated_baseline_gap - aggressive_cuts,
                      (updated_baseline_gap - aggressive_cuts) * 12,
                      available_bonus - ((updated_baseline_gap - aggressive_cuts) * 12) - irs_tax - jan_vehicle,
                      '35% cuts across board'),
    ]

    for scenario_name, monthly_gap, annual_gap, bonus_disc, changes in scenarios_summary:
        marker = "⭐" if scenario_name == "Balanced" else ""
        report.append(f"| {scenario_name} {marker} | ${monthly_gap:,.0f} | ${annual_gap:,.0f} | "
                     f"${bonus_disc:,.0f} | {changes} |")

    report.append(f"")
    report.append(f"**Note:** Bonus for discretionary accounts for:")
    report.append(f"- Annual gap coverage")
    report.append(f"- $5,000 IRS tax payment")
    report.append(f"- $5,246 January vehicle expenses (already spent)")
    report.append(f"- Remaining from $90,642 total bonus")
    report.append(f"")

    # Recommendations
    report.append(f"## Recommendations")
    report.append(f"")
    report.append(f"### Primary Recommendation: **Balanced Scenario**")
    report.append(f"")
    report.append(f"This scenario offers the best balance between reducing expenses and maintaining lifestyle:")
    report.append(f"")
    report.append(f"**What to Cut:**")

    balanced_scenario_cuts = scenarios_df[scenarios_df['scenario_name'] == 'Balanced'][scenarios_df['reduction_amount'] > 0]
    balanced_scenario_cuts = balanced_scenario_cuts.sort_values('reduction_amount', ascending=False)

    for _, row in balanced_scenario_cuts.iterrows():
        report.append(f"- **{row['category']}**: Cut {row['reduction_pct']*100:.0f}% "
                     f"(from ${row['current_2026']:,.0f} to ${row['target_2026']:,.0f}/month)")
    report.append(f"")

    report.append(f"**Results:**")
    report.append(f"- Reduces annual gap from $49,834 to $33,779 (-$16,055)")
    report.append(f"- Frees up ~$44k in bonus for travel and discretionary spending")
    report.append(f"- Requires moderate but achievable lifestyle changes")
    report.append(f"")

    # Rocket Money Budget Targets
    report.append(f"### Rocket Money Budget Targets (Balanced Scenario)")
    report.append(f"")
    report.append(f"Set these monthly budgets in the Rocket Money app to get alerts when approaching thresholds:")
    report.append(f"")
    report.append(f"| Category | 2026 Target | Notes |")
    report.append(f"|----------|-------------|-------|")

    # Get Balanced scenario targets
    balanced_targets = scenarios_df[scenarios_df['scenario_name'] == 'Balanced'][['category', 'target_2026']].sort_values('target_2026', ascending=False)

    # Add category-specific notes
    category_notes = {
        'Bills & Utilities': 'Fixed costs - monitor for rate increases',
        'Shopping': 'Down 25% - use 48-hour rule for purchases',
        'Dining & Drinks': 'Down 25% - reduce to 2-3x/week dining out',
        'Groceries': 'Down 10% - meal plan, generic brands',
        'Vehicle Maintenance': '$500/month buffer (includes emergency repairs)',
        'Education': 'Fixed - tuition and school costs',
        'Pets': 'Fixed - food, vet, medications',
        'Health & Wellness': 'Gym, wellness (minus Planet Fitness)',
        'Medical': 'Insurance, copays, prescriptions',
        'Auto & Transport': 'Fuel, insurance, registration',
        'Personal Care': 'Down 15% - haircuts, personal items',
        'Home & Garden': 'Down 15% - home maintenance',
        'Entertainment & Rec.': 'Down 20% - selective activities',
        'Kids Activities': 'Fixed - after-school programs',
        'Software & Tech': 'Down 20% (already canceled Google One)',
        'Uncategorized': 'Misc expenses',
        'Cash & Checks': 'Cash withdrawals',
        'Charitable Donations': 'Discretionary giving',
        'Taxes': 'Quarterly estimates if needed',
    }

    for _, row in balanced_targets.iterrows():
        category = row['category']
        target = row['target_2026']
        note = category_notes.get(category, 'Monitor spending')
        report.append(f"| {category} | ${target:,.0f} | {note} |")

    report.append(f"")
    report.append(f"**Total Monthly Budget:** ${balanced_targets['target_2026'].sum():,.0f}")
    report.append(f"")
    report.append(f"**How to Use:**")
    report.append(f"1. Log into Rocket Money app")
    report.append(f"2. Go to Budget settings")
    report.append(f"3. Set each category limit to the Target amount above")
    report.append(f"4. Enable alerts for when you reach 80% and 100% of budget")
    report.append(f"5. Review weekly to stay on track")
    report.append(f"")

    # January 2026 Case Study
    report.append(f"### January 2026 Case Study: Why Emergency Planning Matters")
    report.append(f"")
    report.append(f"**What Happened in the First 18 Days:**")
    report.append(f"")
    report.append(f"| Item | Amount | Impact |")
    report.append(f"|------|--------|--------|")
    report.append(f"| Base Income (Jan 1-15) | $5,400 | Regular paycheck |")
    report.append(f"| Expected Income (Jan 15-31) | $5,400 | Regular paycheck |")
    report.append(f"| Car Repair | -$4,746 | Exceeded 99% of annual vehicle budget |")
    report.append(f"| Windshield Deductible | -$500 | Comprehensive insurance claim |")
    report.append(f"| Normal Expenses | ~-$14,897 | Regular monthly spending |")
    report.append(f"| **January Gap** | **-$9,343** | **Covered by bonus/emergency fund** |")
    report.append(f"")
    report.append(f"**Key Lessons:**")
    report.append(f"1. **Vehicle costs are unpredictable** - $5,246 in 18 days validated our conservative approach")
    report.append(f"2. **Emergency fund is essential** - Without it, this would have been a financial crisis")
    report.append(f"3. **Bonuses provide critical cushion** - Enables handling unexpected expenses without panic")
    report.append(f"4. **Budget adjustments needed** - Increased vehicle budget from $400 to $500/month")
    report.append(f"5. **Subscription cuts help** - Planet Fitness + Google One = $56/month savings already in effect")
    report.append(f"")

    # Action Plan
    report.append(f"### Action Plan (Next 90 Days)")
    report.append(f"")
    report.append(f"#### Month 1-3: Immediate Steps")
    report.append(f"1. ✅ **COMPLETED: Subscription Cancellations** (Saves $56/month)")
    report.append(f"   - Canceled Planet Fitness ($36/month)")
    report.append(f"   - Canceled Google One/Gemini ($20/month)")
    report.append(f"   - Annual savings: $672")
    report.append(f"")
    report.append(f"2. **Shopping** - Set monthly budget of $1,863 (down from $2,484)")
    report.append(f"   - Review Amazon Subscribe & Save subscriptions")
    report.append(f"   - Implement 48-hour rule for non-essential purchases")
    report.append(f"   - Use shopping lists, avoid impulse buying")
    report.append(f"")
    report.append(f"3. **Dining Out** - Set monthly budget of $1,215 (down from $1,620)")
    report.append(f"   - Reduce restaurant visits from ~4x/week to 2-3x/week")
    report.append(f"   - Plan meals weekly to reduce food waste")
    report.append(f"   - Pack lunches 2-3 days/week")
    report.append(f"")
    report.append(f"4. **Groceries** - Set monthly budget of $1,313 (down from $1,459)")
    report.append(f"   - Meal plan and use grocery list")
    report.append(f"   - Buy generic brands where possible")
    report.append(f"   - Reduce food waste")
    report.append(f"")

    report.append(f"#### Month 4-6: Medium-term Adjustments")
    report.append(f"5. **Bills & Utilities** - Investigate savings opportunities")
    report.append(f"   - Consider budget billing for natural gas (16% inflation)")
    report.append(f"   - Review insurance policies for better rates")
    report.append(f"   - Energy audit for home efficiency")
    report.append(f"")
    report.append(f"6. **Subscriptions & Software** - Continue audit")
    report.append(f"   - Review remaining subscriptions (Claude, ChatGPT, etc.)")
    report.append(f"   - Consider consolidating AI tools if not using all features")
    report.append(f"   - Cancel unused services")
    report.append(f"")

    report.append(f"#### Month 7-12: Long-term Strategies")
    report.append(f"7. **Emergency Fund** - Build to 6 months expenses")
    report.append(f"   - Target: $81,690 (6 months of projected 2026 expenses)")
    report.append(f"   - Allocate ~$8,169 from 2025 bonus")
    report.append(f"   - January's $5,246 vehicle expense validates this priority")
    report.append(f"   - Continue building 10% of bonus annually")
    report.append(f"")
    report.append(f"8. **Vehicle Maintenance** - Monitor closely")
    report.append(f"   - Already spent $5,246 in January (109% of original annual budget)")
    report.append(f"   - Budget now $500/month ($6,000/year) for realistic planning")
    report.append(f"   - Any additional repairs draw from emergency fund")
    report.append(f"   - Consider vehicle replacement timeline (2014 Impreza is 12 years old)")
    report.append(f"")
    report.append(f"9. **Track & Adjust**")
    report.append(f"   - Monthly review of spending vs. budget")
    report.append(f"   - Quarterly check-ins on progress")
    report.append(f"   - Adjust categories as needed based on actuals")
    report.append(f"")

    # Bonus Allocation
    report.append(f"## 2026 Funding Strategy")
    report.append(f"")
    report.append(f"### The Reality: Normal Bonus Year")
    report.append(f"")
    report.append(f"2025's December bonus ($77,340) was out-of-band and won't repeat. Expected 2026 bonuses:")
    report.append(f"- **April bonus:** ~$5,600")
    report.append(f"- **August bonus:** ~$5,600")
    report.append(f"- **Total annual bonuses:** ~$11,201")
    report.append(f"")
    report.append(f"### Balanced Scenario Funding (Recommended)")
    report.append(f"")
    report.append(f"| Need | Amount | Source |")
    report.append(f"|------|--------|--------|")

    # Calculate updated balanced scenario
    balanced_monthly_gap = float(updated_baseline_gap) - float(balanced_cuts)
    balanced_annual_gap = balanced_monthly_gap * 12
    irs_payment = 5000.00
    emergency_fund_topup = 9438  # To reach full 6 months

    normal_bonus = 11201.00
    total_annual_needs = balanced_annual_gap + irs_payment
    shortfall_vs_bonus = total_annual_needs - normal_bonus
    brokerage_draw = shortfall_vs_bonus

    report.append(f"| Cover annual gap (12 months) | ${balanced_annual_gap:,.0f} | Bonus + Brokerage |")
    report.append(f"| IRS tax payment | ${irs_payment:,.0f} | Bonus |")
    report.append(f"| Top up emergency fund | ${emergency_fund_topup:,.0f} | Bonus (one-time) |")
    report.append(f"| **Total 2026 needs** | **${total_annual_needs:,.0f}** | |")
    report.append(f"")
    report.append(f"| **Income Source** | **Amount** | **Notes** |")
    report.append(f"|-------------------|------------|-----------|")
    report.append(f"| Normal bonuses (Apr + Aug) | ${normal_bonus:,.0f} | Recurring annual |")
    report.append(f"| Brokerage draw (Freedom Fund) | ${brokerage_draw:,.0f} | Bridge the gap |")
    report.append(f"| **Total funding** | **${normal_bonus + brokerage_draw:,.0f}** | |")
    report.append(f"")
    report.append(f"### Why This Works")
    report.append(f"")
    report.append(f"**Brokerage as Freedom Fund:**")
    report.append(f"- Current balance: $150,000")
    report.append(f"- Annual draw: ${brokerage_draw:,.0f} ({brokerage_draw/150000*100:.1f}% of brokerage)")
    report.append(f"- Years covered: ~{150000/brokerage_draw:.1f} years at current spending")
    report.append(f"- Stays invested while you gradually implement spending cuts")
    report.append(f"- Preserves $80k emergency fund for TRUE emergencies")
    report.append(f"")
    report.append(f"**This gives you ~5 years to:**")
    report.append(f"- Gradually implement Balanced scenario cuts at comfortable pace")
    report.append(f"- Seek base salary increases through raises/promotions")
    report.append(f"- Adjust lifestyle sustainably without panic")
    report.append(f"- Keep emergency fund intact for job loss, major medical, etc.")
    report.append(f"")
    report.append(f"**Alternative: Aggressive approach (not recommended)**")
    report.append(f"- Make all cuts immediately to live within base + normal bonuses")
    report.append(f"- Preserve all $150k in brokerage")
    report.append(f"- Requires major lifestyle changes NOW")
    report.append(f"- Higher risk of burnout and unsustainable cuts")
    report.append(f"")

    # Appendix
    report.append(f"## Appendix")
    report.append(f"")
    report.append(f"### Data Sources")
    report.append(f"- **Rocket Money CSV Export:** 2026-01-03T19_06_39.183Z-transactions.csv")
    report.append(f"- **Analysis Period:** 2025-01-01 to 2025-12-31")
    report.append(f"- **Total Transactions:** 6,453 (2,233 included in analysis)")
    report.append(f"")

    report.append(f"### Assumptions & Methodology")
    report.append(f"1. **Excluded Categories:** Bonus Income, Bonus Spend, Home Renovation, Unexpected, Company Travel, Work Expense, Credit Card Payment, Internal Transfers, Reimbursement, Investment")
    report.append(f"2. **Manual Corrections:** $4,200 loan payment recategorized as Bonus Spend (debt paydown)")
    report.append(f"3. **Inflation Rates:** Conservative estimates based on 2026 forecasts (CPI, EIA, USDA)")
    report.append(f"4. **Vehicle Maintenance:** $400/month for two Subarus (60k service, age buffer, emergency fund)")
    report.append(f"5. **Base Income:** $10,800/month (bi-monthly $5,400 payments)")
    report.append(f"")

    report.append(f"### Tools & Database")
    report.append(f"- **Database:** SQLite (budget_analysis.db)")
    report.append(f"- **Tables:** transactions, monthly_summary, category_summary, projected_2026_budget, inflation_impact, vehicle_maintenance_2026, scenarios_2026, bonus_allocation")
    report.append(f"- **Analysis Scripts:** Python 3 with pandas, sqlite3")
    report.append(f"")

    report.append(f"---")
    report.append(f"")
    report.append(f"*Report generated by financial-advisor budget analysis system*")

    # Write report
    report_text = '\n'.join(report)
    with open(REPORT_PATH, 'w') as f:
        f.write(report_text)

    print(f"✓ Report generated: {REPORT_PATH}")
    print(f"  Lines: {len(report)}")
    print(f"  File size: {len(report_text)} bytes")

    conn.close()

    return REPORT_PATH


if __name__ == "__main__":
    generate_report()
    print(f"\n✓ Report complete!")
    print(f"  Open budget_report.md to view the full analysis")

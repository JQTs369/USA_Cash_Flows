# process: Main goal helping other understand a progressive tax system vs regressive.
# get standard deduction based on year - pull from the IRS if possible
# get user gross income input
# get marriage status and year for filing
# process taxable income in "buckets" show visual image for user-keep it simple but effective so a 6th grader can learn it
    # need to show simple details like what a personal exemption is, or a standard deduction too.
# out put totals
# then show regressive flat tax of 20% - easier but worse for the middle class
# imports
from os import write

import streamlit as st
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Get the path to the 'USA_Cash_Flows' root directory
# parent is: USA_Cash_Flows/pages - two levels back
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the root to sys.path
if project_root not in sys.path:
    sys.path.append(project_root)
# bring in our classes - setup to help streamlit failures
try:
    from AmericanRealityClasses.Tax_Calculator.tax_logic import TaxDataManager
except ImportError as e:
    st.error(f"Could not find tax_logic.py. Error: {e}")

# instance creation
tax_manager = TaxDataManager()

# marriage mapping for JSON dict key files
status_options = {
    "Single": "single",
    "Married Filing Jointly": "married_joint",
    "Head of Household": "head_of_household",
    "Married Filing Separately": "married_separate",
}

# Setup page configs
st.set_page_config(page_title="Tax Calculator",
                   layout="wide",
                   page_icon='https://cdn-icons-png.flaticon.com/128/8984/8984354.png')

# Page Header
st.info("🚧Still Under Construction🚧")
st.title("🇺🇸 American Reality: Tax Calculator")
st.markdown("### Understanding Progressive vs. Regressive Taxation")

# Update Status Toggle
with st.expander("🔄 Page Status & Updates"):
    is_updated = False  # You can toggle this manually
    if is_updated:
        st.success("Current Status: **Live & Updated** (Data reflects 2024 IRS Brackets)")
        st.caption("Last Update: December 31, 2025")
    else:
        st.warning("Current Status: **Under Maintenance**")
        st.write("We are currently in the processing of creating this page. Things may be wonky for a bit but we will get there.")
        st.write("Will work on a separate business side where you can add total deductions instead of standard sections")
with st.expander("⚖️ Legal Disclaimer"):
    st.info(
        """
        **Educational Purposes Only** This tool is designed to demonstrate how tax systems work. I am not a 
        certified tax professional or tax attorney. 

        Tax laws are complex and change frequently. Please consult with a 
        qualified professional for your specific tax situation.
        """
    )
    st.caption("Created for the American Reality Project.")

st.divider() # Separate the header from the calculator

# --- MISSION STATEMENT ---
st.markdown(
    """
    This calculator helps you visualize how the **Progressive Tax System** has evolved in the United States since 1862. 

    By entering your income and a historical year, you can see how much of 
    your money was 'shielded' by deductions and how the remaining income 
    fell into different tax 'buckets'.
    """
)

# Containers
with st.container(border=True):
    st.subheader("📋 Taxpayer Information")

    # setup 4 columns - 2 of 2 side by side
    # Containers
    with st.container(border=True):
        st.subheader("📋 Taxpayer Information")

        # We define the Year first so the rest of the code knows what it is
        col1, col2 = st.columns(2)

        with col1:
            # 1. Define the Year
            tax_year = st.number_input("Enter Tax Year", min_value=1862, max_value=2024, value=1955,
                                       help='Pick a year to see what you would pay in taxes!')

        with col2:
            # 2. Define the Income
            gross_income = st.number_input("Enter Gross Annual Income", min_value=0, value=4400, step=1000,
                                           help='Total income before deductions')

        # Now that both exist, we can show the expander safely
        with st.expander("🎈 Why does my income look different in the past?"):
            st.warning(f"**Inflation Alert:** A dollar in {tax_year} bought much more than a dollar today!")
            st.write(f"""
                In {tax_year}, the prices of houses, cars, and candy were much lower. 
                If you are entering a 'modern' salary (like $60,000) into an old year, 
                the calculator will think you are incredibly rich!
            """)
            st.link_button("Official BLS Inflation Calculator", "https://data.bls.gov/cgi-bin/cpicalc.pl")

        col3, col4 = st.columns(2)
        with col3:
            marriage_status_selection = st.selectbox("Marriage Status", options=list(status_options.keys()))
            marriage_status = status_options[marriage_status_selection]

        with col4:
            number_of_dependents = st.number_input("Number of Dependents", min_value=0, value=0, step=1,
                                                   help="Number of Dependents may have min or max based on state.")
    # TODO make style file and move these there
    st.markdown("""
        <style>
        /* This targets the container for the tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }

        /* This targets the individual tabs */
        .stTabs [data-baseweb="tab"] {
            height: 60px; /* Makes them taller */
            width: 100%;  /* Distributes them evenly */
            white-space: pre-wrap;
            background-color: #262730; /* Dark background to pop against the page */
            border-radius: 8px 8px 8px 8px; /* Rounded corners */
            color: #ffffff;
            font-weight: bold;
            font-size: 18px; /* Bigger font */
            border: 1px solid #444;
        }

        /* This targets the tab when it is HOVERED */
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #3e404a;
            border-color: #FF4B4B; /* Streamlit Red border on hover */
        }

        /* This targets the ACTIVE tab */
        .stTabs [aria-selected="true"] {
            background-color: #FF4B4B !important; /* Bright red/orange background */
            color: white !important;
            border: none !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3); /* Adds a little depth */
        }
        </style>
    """, unsafe_allow_html=True)



    # Now your tabs will look like big, bold buttons
    tab1, tab2 = st.tabs(["🧮 TAX CALCULATOR", "📖 FAQ & SOURCES"])

    with tab1:
        # 1. Logic calls:
        income_tax_bracket = tax_manager.get_clean_income_tax_data(year=tax_year, status=marriage_status)
        standard_deduction_amount = tax_manager.get_standard_deduction(year=tax_year, status=marriage_status)

        # 2. Find the names of columns (Low, High, Rate)
        cols = income_tax_bracket.columns.tolist()
        low_col = next((c for c in cols if any(x in c.lower() for x in ['low', 'min', 'start'])), None)
        high_col = next((c for c in cols if any(x in c.lower() for x in ['high', 'max', 'end', 'upper'])), None)
        rate_col = next((c for c in cols if any(x in c.lower() for x in ['rate', 'tax', 'perc'])), None)

        # 3. Handle Personal Exemptions (Historical Logic)
        if 1913 <= tax_year <= 2017:
            personal_exemption, dependents_rate, note = tax_manager.get_personal_exemption(year=tax_year,
                                                                                           status=marriage_status)
        else:
            personal_exemption = 0
            dependents_rate = 0
            note = 'Personal exemptions were suspended starting in 2018 under the Tax Cuts and Jobs Act.'

        # 4. Calculate the "Tax Shield" (Money you don't pay tax on)
        total_exemption_amount = personal_exemption + (dependents_rate * number_of_dependents)
        total_tax_shield = standard_deduction_amount + total_exemption_amount
        taxable_income = max(0, gross_income - total_tax_shield)

        # 5. Display the Metrics
        st.subheader(f"Calculation for {tax_year}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Standard Deduction", f"${standard_deduction_amount:,}",
                  help="This is a flat amount deducted from your income before taxes are calculated.")

        c2.metric("Personal Exemptions", f"${total_exemption_amount:,}",
                  help="A dollar amount allowed for yourself and each dependent.")

        c3.metric("Total Taxable Income", f"${taxable_income:,}",
                  help="This is the 'Bucket' money. Only this portion is subject to tax rates.")

        # --- NEW: TAX RATE RANGE ---
        if not income_tax_bracket.empty and rate_col:
            min_rate = income_tax_bracket[rate_col].min() * 100
            max_rate = income_tax_bracket[rate_col].max() * 100

            c4, c5 = st.columns(2)
            c4.metric(f"Lowest Rate ({tax_year})", f"{min_rate:,.1f}%",
                      help="The rate applied to your first dollar of taxable income.")
            c5.metric(f"Highest Rate ({tax_year})", f"{max_rate:,.1f}%",
                      help="The top marginal rate for this year.")

        # 6. THE PROGRESSIVE "BUCKET" CALCULATION
        remaining_taxable = taxable_income
        total_progressive_tax = 0
        buckets = []

        # Logic to iterate through brackets and fill the buckets
        for i, row in income_tax_bracket.iterrows():
            lower = row[low_col]
            upper = row[high_col] if (high_col and not pd.isna(row[high_col])) else 1e15
            rate = row[rate_col]

            bracket_width = upper - lower

            if remaining_taxable > 0:
                amount_in_bracket = min(remaining_taxable, bracket_width)
                tax_for_bracket = amount_in_bracket * rate
                total_progressive_tax += tax_for_bracket
                remaining_taxable -= amount_in_bracket

                buckets.append({
                    "Bracket": f"{rate * 100:.1f}%",
                    "Amount": amount_in_bracket,
                    "Tax": tax_for_bracket
                })

        effective_rate = (total_progressive_tax / gross_income) * 100 if gross_income > 0 else 0

        # 7. THE REGRESSIVE (FLAT) COMPARISON
        flat_rate = 0.20
        total_flat_tax = gross_income * flat_rate

        st.divider()
        st.subheader("🪣 The 'Bucket' Breakdown (Progressive)")

        # 8. Create the visual Chart
        if buckets:
            df_buckets = pd.DataFrame(buckets)
            bar_labels = [f"${row['Amount']:,.0f}<br>Tax: ${row['Tax']:,.0f}" for _, row in df_buckets.iterrows()]

            fig_buckets = go.Figure()
            fig_buckets.add_trace(go.Bar(
                x=df_buckets["Bracket"],
                y=df_buckets["Amount"],
                text=bar_labels,
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(size=20, color="black"),
                marker=dict(color='#FFD700', line=dict(color='white', width=1)),
                hovertemplate="Income in this bucket: %{y:$.2f}<extra></extra>"
            ))

            fig_buckets.update_layout(
                title=dict(text="Your Income Buckets", font=dict(size=26)),
                template="plotly_dark",
                yaxis_title="Dollars in Bucket",
                xaxis_title="Tax Rate",
                height=600,
                uniformtext=dict(minsize=14, mode='hide')
            )
            st.plotly_chart(fig_buckets, use_container_width=True)

        # 9. FINAL COMPARISON (Progressive vs Regressive)
        st.subheader("⚖️ Progressive vs. Regressive (Flat)")
        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.markdown(f"#### **Progressive System ({tax_year})**")
            st.metric("Total Federal Tax", f"${total_progressive_tax:,.2f}")
            st.metric("Effective Tax Rate", f"{effective_rate:.2f}%")
            st.caption("✅ Better for: Lower and Middle class.")

        with col_res2:
            st.markdown("#### **Regressive System (20% Flat)**")
            st.metric("Total Federal Tax", f"${total_flat_tax:,.2f}")
            st.metric("Effective Tax Rate", "20.00%")

            diff = total_flat_tax - total_progressive_tax
            if diff > 0:
                st.error(f"You would pay **${abs(diff):,.2f} MORE** under a flat tax.")
            else:
                st.success(f"You would pay **${abs(diff):,.2f} LESS** under a flat tax.")

        # 10. Educational Section for the 6th Grader
        st.divider()
        st.header("🎓 Learning the Systems")

        edu_col1, edu_col2 = st.columns(2)
        with edu_col1:
            st.info("### 1. The Progressive 'Buckets'")
            st.write(
                "In America, we use a Progressive system. Think of it like a video game where levels get harder only after you finish the easy ones.")

        with edu_col2:
            st.warning("### 2. The Regressive 'Flat Tax'")
            st.write(
                "A Flat tax sounds fair because everyone pays 20%. But 20% of a poor person's money is their rent and food. 20% of a rich person's money is just less savings.")

        # Take-Home Pay Metric
        take_home = gross_income - total_progressive_tax
        st.metric("💰 Your Annual Take-Home Pay", f"${take_home:,.2f}")

    with tab2:
        st.header("Frequently Asked Questions & Data Sources")

        with st.expander("📝 What happened to Personal Exemptions in 2018?"):
            st.info("""
            **Historical Context:** Historically, the IRS allowed a "Personal Exemption"—a flat dollar amount you could subtract from your income for yourself, your spouse, and each dependent.

            **The Change:** This was suspended (set to $0) when President Trump signed the **Tax Cuts and Jobs Act (TCJA)** on December 22, 2017. 

            **The Trade-off:** To simplify the code and offset the loss of exemptions, the TCJA:
            1. Nearly **doubled** the Standard Deduction.
            2. Significantly increased the **Child Tax Credit**.

            *Note: Under current law, these changes are scheduled to 'sunset' (expire) after 2025, meaning exemptions could return in 2026 unless Congress acts.*
            """)

        st.divider()

        st.subheader("📚 Primary Data Sources")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### **The Tax Foundation**")
            st.write("The primary source for historical bracket thresholds and inflation-adjusted parameters.")
            st.markdown(
                "- [Historical Income Tax Brackets](https://taxfoundation.org/data/all/federal/historical-income-tax-rates-brackets/)")
            st.markdown(
                "- [Standard Deduction History](https://taxpolicycenter.org/sites/default/files/statistics/pdf/standard_deduction_4.pdf)")
            st.markdown(
                "- [Personal Exemptions Post-TCJA](https://taxfoundation.org/research/all/federal/state-personal-exemptions-post-tcja/)")

        with col2:
            st.markdown("#### **Internal Revenue Service (IRS)**")
            st.write("Raw Statistics of Income (SOI) data used to verify statutory changes.")
            st.markdown(
                "- [SOI Historic Table 2 (Tax Brackets)](https://www.irs.gov/statistics/soi-tax-stats-historic-table-2)")
            st.markdown(
                "- [Individual Statistical Tables (Deductions)](https://www.irs.gov/statistics/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income)")
            st.markdown(
                "- [IRS Publication 02 (Historical Rates & Exemptions)](https://www.irs.gov/pub/irs-soi/02inpetr.pdf)")

        st.markdown("---")

        st.markdown("#### **Federal Reserve Bank of St. Louis (FRED)**")
        st.write("Used for verifying economic trends and historical exemption values.")
        st.markdown("- [FRED Main Database](https://fred.stlouisfed.org/)")
        st.markdown("- [Historical Personal Exemptions Series (Single)](https://fred.stlouisfed.org/series/IITPESP)")

        st.caption(
            "Disclaimer: This calculator is for historical educational purposes only and does not constitute official tax advice.")
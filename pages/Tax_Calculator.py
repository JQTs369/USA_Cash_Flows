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
    col1, col2 = st.columns(2)
    with col1:
        gross_income = st.number_input("Enter Gross Annual Income", min_value=0, value=60000, step=1000,help='Total income after standard deduction')

    with col2:
        tax_year = st.number_input("Enter Tax Year", min_value=1862, max_value=2024,help='Pick a year to see what you would pay in taxes! inflation needs to be taken into account*')

    col3, col4 = st.columns(2)
    with col3:
        marriage_status_selection = st.selectbox("Marriage Status",options=list(status_options.keys()))
        marriage_status = status_options[marriage_status_selection]

    with col4:
        number_of_dependents = st.number_input("Number of Dependents", min_value=0, value=0, step=1,help="Number of Dependents may have min or max based on state.")

    tab1, tab2 = st.tabs(["🧮 Calculator", "📖 FAQ and Sources"])

    with tab1:
        # Logic calls
        income_tax_bracket = tax_manager.get_clean_income_tax_data(year=tax_year, status=marriage_status)
        standard_deduction_amount = tax_manager.get_standard_deduction(year=tax_year, status=marriage_status)

        # Determine if exemptions apply
        if 1913 <= tax_year <= 2017:
            personal_exemption, dependents_rate, note = tax_manager.get_personal_exemption(year=tax_year,
                                                                                           status=marriage_status)
        else:
            personal_exemption = 0
            dependents_rate = 0
            note = 'Personal exemptions were suspended starting in 2018 under the Tax Cuts and Jobs Act.'

        # pre tax deductions (Tax Shield)
        # Math Fix: Multiplying the rate by the number of dependents
        total_exemption_amount = personal_exemption + (dependents_rate * number_of_dependents)
        total_tax_shield = standard_deduction_amount + total_exemption_amount

        # Ensure taxable income doesn't go below zero
        taxable_income = max(0, gross_income - total_tax_shield)

        # display the results
        st.subheader(f"Calculation for {tax_year}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Standard Deduction", f"${standard_deduction_amount:,}",
                  help="This is a flat amount deducted from your income before taxes are calculated.")

        c2.metric("Personal Exemptions", f"${total_exemption_amount:,}",
                  help="A dollar amount allowed for yourself and each dependent. This was removed (suspended to $0) by President Trump signing the Tax Cuts and Jobs Act of 2017.")

        c3.metric("Total Taxable Income", f"${taxable_income:,}",
                  help="This is the 'Bucket' money. Only this portion of your income is subject to tax rates.")

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
# --- Imports ---
import streamlit as st
import plotly.graph_objects as go
from AmericanRealityClasses import TreasuryApi as TA
import pandas as pd
import math


# 1. Helper Functions
def format_large_number(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "No Data"
    sign = '-' if value < 0 else ""
    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{sign}${abs_val / 1e12:,.2f} Trillion"
    elif abs_val >= 1e9:
        return f"{sign}${abs_val / 1e9:,.2f} Billion"
    elif abs_val >= 1e6:
        return f"{sign}${abs_val / 1e6:,.2f} Million"
    else:
        return f"{sign}${abs_val:,.2f}"


# 2. Data Loading
@st.cache_data # so we do not load the data on every click
def load_data():
    dfInstance = TA.Treasury()
    BaseUrl = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
    debt = dfInstance.getHistoricalDebtAPIData(BaseUrl)
    presidents = pd.read_json('AmericanRealityClasses/resources/USAPresidents.json')
    path = 'AmericanRealityClasses/resources/TaxPolicyCentrHistoricRevenues.xlsx'
    deficit = pd.read_excel(path, engine='openpyxl', skiprows=6)
    deficit = deficit.drop(0)
    deficit.rename(columns={
        "Unnamed: 0": "Fiscal Year",
        "Total": "Receipts Total",
        "Total.1": "Outlays Total",
        "Total.2": "Surplus or Deficit(-) Total"
    }, inplace=True)
    # Filter out estimates and clean TQ
    mask = deficit['Fiscal Year'].astype(str).str.contains('Estimates', case=False, na=False)
    estimateIndex = deficit[mask].index[0]
    deficit = deficit.iloc[:estimateIndex - 2]
    deficit = deficit[deficit['Fiscal Year'] != 'TQ']
    deficit['Fiscal Year'] = deficit['Fiscal Year'].astype(int)
    deficit['Surplus or Deficit(-) Total'] = deficit['Surplus or Deficit(-) Total'] * 1_000_000
    return debt, presidents, deficit


dfDebt, dfPresidents, dfDeficit = load_data()

# 3. Page Config
st.set_page_config(page_title="USA Reality Project", layout="wide")
st.title("USA Reality Project")
st.caption("Visualizing America's National Debt and Fiscal History")

# 4. Navigation
viewType = st.pills("Analysis View", ["President", "Year"], selection_mode="single", default="President")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Data Analysis", "🔄 Combined View", "📖 Get Learnt (FAQ)"])

with tab1:
    if viewType == "President":
        st.subheader("Presidential Fiscal Analysis")
        # Selector on the main page
        president = st.selectbox("Choose a President", dfPresidents['name'],
                                 index=dfPresidents['name'].tolist().index("Bill Clinton"))

        president_data = dfPresidents[dfPresidents['name'] == president].iloc[0]
        start_year, end_year = int(president_data['start_year']), int(president_data['end_year'])

        debt_data = dfDebt[(dfDebt['record_fiscal_year'] >= start_year) & (dfDebt['record_fiscal_year'] <= end_year)]
        deficit_data = dfDeficit[(dfDeficit['Fiscal Year'] >= start_year) & (dfDeficit['Fiscal Year'] <= end_year)]

        merger = pd.merge(debt_data, deficit_data, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
        combined_data = pd.DataFrame({
            'Year': merger['record_fiscal_year'].astype(int),
            'Debt': merger['debt_outstanding_amt'],
            'Deficit': merger['Surplus or Deficit(-) Total']
        })

        # Metrics
        st.markdown(f"### {president}'s Fiscal Snapshot ({start_year} - {end_year})")

        beginning_debt = combined_data[combined_data['Year'] == start_year]['Debt'].iloc[0] if not combined_data[
            combined_data['Year'] == start_year].empty else 0
        ending_debt = combined_data[combined_data['Year'] == end_year]['Debt'].iloc[0] if not combined_data[
            combined_data['Year'] == end_year].empty else 0

        # ADD THIS LINE:
        total_debt_change = ending_debt - beginning_debt

        # Cumulative = the total amount of overspending over the whole term
        cumulative_deficit = combined_data['Deficit'].sum()
        beginning_deficit = combined_data[combined_data['Year'] == start_year]['Deficit'].iloc[0] if not combined_data[
            combined_data['Year'] == start_year].empty else 0
        ending_deficit = combined_data[combined_data['Year'] == end_year]['Deficit'].iloc[0] if not combined_data[
            combined_data['Year'] == end_year].empty else 0
        deficit_growth = ending_deficit - beginning_deficit

        # Row 1: The Debt (The "Total Bill")
        st.write("**National Debt Progress**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Debt at Start", format_large_number(beginning_debt))
        m2.metric("Debt at End", format_large_number(ending_debt))
        m3.metric("Total Debt Increase", format_large_number(total_debt_change),
                  delta=format_large_number(total_debt_change), delta_color="inverse")

        # Row 2: The Deficit (The "Annual Overspending")
        st.write("**Annual Deficit & Cumulative Spending**")
        m4, m5, m6 = st.columns(3)
        m4.metric("Annual Deficit (Start)", format_large_number(beginning_deficit))
        m5.metric("Annual Deficit (End)", format_large_number(ending_deficit),
                  delta=format_large_number(deficit_growth), delta_color="inverse")
        m6.metric("Total Term Overspending", format_large_number(cumulative_deficit))

        st.divider()

        # Plot
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=combined_data['Year'], y=combined_data['Debt'], name='Total Debt', line=dict(color='#FFD700', width=4),
                       yaxis='y1'))
        fig.add_trace(
            go.Bar(x=combined_data['Year'], y=combined_data['Deficit'], name='Annual Deficit/Surplus', marker=dict(color='#2E86C1'),
                   opacity=0.6, yaxis='y2'))
        fig.update_layout(template='plotly_dark', hovermode='x unified', height=500,
                          yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

    else:
        # --- YEAR VIEW SIDEBAR LOGIC ---
        # The slider only appears when "Year" is selected
        st.sidebar.subheader("Year Range Settings")
        min_y, max_y = int(dfDebt['record_fiscal_year'].min()), int(dfDebt['record_fiscal_year'].max())
        y_range = st.sidebar.slider("Select Range", min_y, max_y, (1982, 2022))

        st.subheader(f"Historical Analysis: {y_range[0]} - {y_range[1]}")

        debt_data = dfDebt[(dfDebt['record_fiscal_year'] >= y_range[0]) & (dfDebt['record_fiscal_year'] <= y_range[1])]
        deficit_data = dfDeficit[(dfDeficit['Fiscal Year'] >= y_range[0]) & (dfDeficit['Fiscal Year'] <= y_range[1])]

        merger = pd.merge(debt_data, deficit_data, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
        combined_data = pd.DataFrame({
            'Year': merger['record_fiscal_year'].astype(int),
            'Debt': merger['debt_outstanding_amt'],
            'Deficit': merger['Surplus or Deficit(-) Total']
        })

        try:
            b_val = combined_data[combined_data['Year'] == y_range[0]]['Debt'].iloc[0]
            e_val = combined_data[combined_data['Year'] == y_range[1]]['Debt'].iloc[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Starting Debt", format_large_number(b_val))
            m2.metric("Ending Debt", format_large_number(e_val))
            m3.metric("Change", format_large_number(e_val - b_val), delta=format_large_number(e_val - b_val),
                      delta_color="inverse")
        except:
            st.info("Expand year range for metrics")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=combined_data['Year'], y=combined_data['Debt'], name='Debt', line=dict(color='yellow'), yaxis='y1'))
        fig.add_trace(
            go.Bar(x=combined_data['Year'], y=combined_data['Deficit'], name='Deficit', marker=dict(color='#2E86C1'), yaxis='y2'))
        fig.update_layout(template='plotly_dark', hovermode='x unified', height=500,
                          yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("The Full Picture")
    st.info("Combined view logic goes here!")

with tab3:
    st.header("Frequently Asked Questions")
    st.write("Sourced from Treasury API.")
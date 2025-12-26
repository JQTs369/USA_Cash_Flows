# --- Imports ---
import streamlit as st
import plotly.graph_objects as go
from AmericanRealityClasses import TreasuryApi as TA
import pandas as pd
import math


# --- Helper Function (Must be at the top) ---
def format_large_number(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "No Data"
    sign = '-' if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1e12:
        return f"{sign}${abs_value / 1e12:,.2f} Trillion"
    elif abs_value >= 1e9:
        return f"{sign}${abs_value / 1e9:,.2f} Billion"
    elif abs_value >= 1e6:
        return f"{sign}${abs_value / 1e6:,.2f} Million"
    else:
        return f"{sign}${abs_value:,.2f}"


# --- Data Loading ---
@st.cache_data
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
    estimateIndex = deficit[deficit['Fiscal Year'].astype(str).str.contains('Estimates', case=False, na=False)].index[0]
    deficit = deficit.iloc[:estimateIndex - 2]
    deficit = deficit[deficit['Fiscal Year'] != 'TQ']
    deficit['Fiscal Year'] = deficit['Fiscal Year'].astype(int)
    deficit['Surplus or Deficit(-) Total'] = deficit['Surplus or Deficit(-) Total'] * 1_000_000
    return debt, presidents, deficit


dfDebt, dfPresidents, dfDeficit = load_data()

# --- Page Config ---
st.set_page_config(page_title="USA Reality Project", layout="wide")

st.title("USA Reality Project")
st.caption("Visualizing America's National Debt and Fiscal History")

# --- Navigation ---
viewType = st.pills("Analysis View", ["President", "Year"], selection_mode="single", default="President")
st.divider()

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Data Analysis", "🔄 Combined View", "📖 Get Learnt (FAQ)"])

with tab1:
    if viewType == "President":
        st.subheader("Presidential Fiscal Analysis")
        default_president = "Bill Clinton"
        president = st.selectbox(
            "Choose a President",
            dfPresidents['name'],
            index=dfPresidents['name'].tolist().index(default_president)
        )

        # Data Processing
        pData = dfPresidents[dfPresidents['name'] == president].iloc[0]
        sYear, eYear = int(pData['start_year']), int(pData['end_year'])

        dData = dfDebt[(dfDebt['record_fiscal_year'] >= sYear) & (dfDebt['record_fiscal_year'] <= eYear)]
        defData = dfDeficit[(dfDeficit['Fiscal Year'] >= sYear) & (dfDeficit['Fiscal Year'] <= eYear)]

        merger = pd.merge(dData, defData, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
        chartData = pd.DataFrame({
            'Year': merger['record_fiscal_year'].astype(int),
            'Debt': merger['debt_outstanding_amt'],
            'Deficit': merger['Surplus or Deficit(-) Total']
        })

        # Metrics Snapshot
        st.markdown(f"### {president}'s Fiscal Snapshot ({sYear} - {eYear})")
        b_debt = chartData[chartData['Year'] == sYear]['Debt'].iloc[0] if not chartData[
            chartData['Year'] == sYear].empty else 0
        e_debt = chartData[chartData['Year'] == eYear]['Debt'].iloc[0] if not chartData[
            chartData['Year'] == eYear].empty else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Debt at Start", format_large_number(b_debt))
        m2.metric("Debt at End", format_large_number(e_debt))
        m3.metric("Total Change", format_large_number(e_debt - b_debt), delta=format_large_number(e_debt - b_debt),
                  delta_color="inverse")

        # Graph
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=chartData['Year'], y=chartData['Debt'], name='Total Debt', line=dict(color='#FFD700', width=4),
                       yaxis='y1'))
        fig.add_trace(go.Bar(x=chartData['Year'], y=chartData['Deficit'], name='Annual Deficit/Surplus',
                             marker=dict(color='#2E86C1'), opacity=0.6, yaxis='y2'))
        fig.update_layout(template='plotly_dark', hovermode='x unified', height=500,
                          yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.subheader("Historical Yearly Analysis")
        min_y, max_y = int(dfDebt['record_fiscal_year'].min()), int(dfDebt['record_fiscal_year'].max())
        y_range = st.slider("Select Year Range", min_y, max_y, (1982, 2022))

        dData = dfDebt[(dfDebt['record_fiscal_year'] >= y_range[0]) & (dfDebt['record_fiscal_year'] <= y_range[1])]
        defData = dfDeficit[(dfDeficit['Fiscal Year'] >= y_range[0]) & (dfDeficit['Fiscal Year'] <= y_range[1])]

        merger = pd.merge(dData, defData, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
        chartData = pd.DataFrame({
            'Year': merger['record_fiscal_year'].astype(int),
            'Debt': merger['debt_outstanding_amt'],
            'Deficit': merger['Surplus or Deficit(-) Total']
        })

        st.markdown(f"### Fiscal Overview: {y_range[0]} to {y_range[1]}")
        try:
            b_d = chartData[chartData['Year'] == y_range[0]]['Debt'].iloc[0]
            e_d = chartData[chartData['Year'] == y_range[1]]['Debt'].iloc[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Debt at Start", format_large_number(b_d))
            m2.metric("Debt at End", format_large_number(e_d))
            m3.metric("Total Change", format_large_number(e_d - b_d), delta=format_large_number(e_d - b_d),
                      delta_color="inverse")
        except:
            st.warning("Adjust range to see metrics.")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=chartData['Year'], y=chartData['Debt'], name='Total Debt', line=dict(color='yellow', width=3),
                       yaxis='y1'))
        fig.add_trace(go.Bar(x=chartData['Year'], y=chartData['Deficit'], name='Deficit', marker=dict(color='#2E86C1'),
                             opacity=0.6, yaxis='y2'))
        fig.update_layout(template='plotly_dark', hovermode='x unified', height=550,
                          yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("The Full Picture")
    st.info("Coming soon: A combined view of the entire US history.")

with tab3:
    st.header("Frequently Asked Questions")
    st.write("Data sourced from the US Treasury API.")
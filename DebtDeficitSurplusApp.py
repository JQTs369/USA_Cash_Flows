
# TODO: Make a web app with docker and use streamlit or PyQT(advanced)
# --- Imports ---
import streamlit as st
import plotly.graph_objects as go
from AmericanRealityClasses import TreasuryApi as TA
import pandas as pd
import math


# --- Data Loading (Keep your existing logic) ---
@st.cache_data  # This prevents the API from hitting every time you click a tab!
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

# Function to format large numbers with appropriate labels (Million, Billion, Trillion)
def format_large_number(value):

    if value is None or math.isnan(value):
        return "No Data"

    sign = '-' if value < 0 else ""
    value = abs(value)

    if value >= 1e12:
        return f"{sign}${value / 1e12:,.2f} Trillion"
    elif value >= 1e9:
        return f"{sign}${value / 1e9:,.2f} Billion"
    elif value >= 1e6:
        return f"{sign}${value / 1e6:,.2f} Million"
    else:
        return f"{sign}${value:,.2f}"


dfDebt, dfPresidents, dfDeficit = load_data()

# --- Page Config ---
st.set_page_config(page_title="USA Reality Project", layout="wide")

# --- Header Section ---
st.title("USA Reality Project")
st.caption("Visualizing America's National Debt and Fiscal History")

# --- Main Navigation (Replaces Sidebar) ---
# We use a segmented control for a professional "switch" look
viewType = st.pills("Analysis View", ["President", "Year"], selection_mode="single", default="President")

st.divider()

# --- Tab Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Data Analysis", "🔄 Combined View", "📖 Get Learnt (FAQ)"])

with tab1:
    if viewType == "President":
        st.subheader("Presidential Fiscal Analysis")
        # 1. Selector
        default_president = "Bill Clinton"
        president = st.selectbox(
            "Choose a President",
            dfPresidents['name'],
            index=dfPresidents['name'].tolist().index(default_president)
        )

        # --- Data Processing ---
        presidentData = dfPresidents[dfPresidents['name'] == president].iloc[0]
        startYear, endYear = int(presidentData['start_year']), int(presidentData['end_year'])

        debtData = dfDebt[(dfDebt['record_fiscal_year'] >= startYear) & (dfDebt['record_fiscal_year'] <= endYear)]
        deficitData = dfDeficit[(dfDeficit['Fiscal Year'] >= startYear) & (dfDeficit['Fiscal Year'] <= endYear)]

        mergerdf = pd.merge(debtData, deficitData, left_on='record_fiscal_year',
                            right_on='Fiscal Year', how='outer', suffixes=('_debt', '_deficit'))

        chartData = pd.DataFrame({
            'Year': mergerdf['record_fiscal_year'].astype(int),
            'Debt': mergerdf['debt_outstanding_amt'],
            'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']
        })

        # --- Metrics Snapshot ---
        st.markdown(f"### {president}'s Fiscal Snapshot ({startYear} - {endYear})")
        beg_debt = chartData[chartData['Year'] == startYear]['Debt'].iloc[0] if not chartData[
            chartData['Year'] == startYear].empty else 0
        end_debt = chartData[chartData['Year'] == endYear]['Debt'].iloc[0] if not chartData[
            chartData['Year'] == endYear].empty else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Debt at Start", format_large_number(beg_debt))
        m2.metric("Debt at End", format_large_number(end_debt))
        m3.metric("Total Change", format_large_number(end_debt - beg_debt),
                  delta=format_large_number(end_debt - beg_debt), delta_color="inverse")

        # --- Graph ---
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=chartData['Year'], y=chartData['Debt'], name='Total Debt', line=dict(color='#FFD700', width=4),
                       yaxis='y1'))
        fig.add_trace(go.Bar(x=chartData['Year'], y=chartData['Deficit/Surplus'], name='Annual Deficit/Surplus',
                             marker=dict(color='#2E86C1'), opacity=0.6, yaxis='y2'))

        fig.update_layout(template='plotly_dark', hovermode='x unified', height=500,
                          yaxis=dict(title='Total Debt'), yaxis2=dict(title='Deficit', overlaying='y', side='right'))

        st.plotly_chart(fig, use_container_width=True)


    else:

        st.subheader("Historical Yearly Analysis")

        # 1. Main Page Slider (Easier for thumbs on mobile!)

        min_y, max_y = int(dfDebt['record_fiscal_year'].min()), int(dfDebt['record_fiscal_year'].max())

        selected_years = st.slider("Select Year Range", min_y, max_y, (1982, 2022))

        # 2. Filter the data

        debtData = dfDebt[
            (dfDebt['record_fiscal_year'] >= selected_years[0]) & (dfDebt['record_fiscal_year'] <= selected_years[1])]

        deficitData = dfDeficit[
            (dfDeficit['Fiscal Year'] >= selected_years[0]) & (dfDeficit['Fiscal Year'] <= selected_years[1])]

        mergerdf = pd.merge(debtData, deficitData, left_on='record_fiscal_year',

                            right_on='Fiscal Year', how='outer', suffixes=('_debt', '_deficit'))

        chartData = pd.DataFrame({

            'Year': mergerdf['record_fiscal_year'].astype(int),

            'Debt': mergerdf['debt_outstanding_amt'],

            'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']

        })

        # 3. Snapshot Metrics (Consistent with President view)

        st.markdown(f"### Fiscal Overview: {selected_years[0]} to {selected_years[1]}")

        # Get start/end values for metrics

        try:

            beg_d = chartData[chartData['Year'] == selected_years[0]]['Debt'].iloc[0]

            end_d = chartData[chartData['Year'] == selected_years[1]]['Debt'].iloc[0]

            d_change = end_d - beg_d

            m1, m2, m3 = st.columns(3)

            m1.metric("Debt at Start", format_large_number(beg_d))

            m2.metric("Debt at End", format_large_number(end_d))

            m3.metric("Total Change", format_large_number(d_change),

                      delta=format_large_number(d_change), delta_color="inverse")

        except:

            st.warning("Select a wider range to see metrics.")

        st.divider()

        # 4. Graphs (Responsive width)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=chartData['Year'], y=chartData['Debt'], name='Total Debt',

                                 line=dict(color='yellow', width=3), yaxis='y1'))

        fig.add_trace(go.Bar(x=chartData['Year'], y=chartData['Deficit/Surplus'], name='Deficit/Surplus',

                             marker=dict(color='#2E86C1'), opacity=0.6, yaxis='y2'))

        fig.update_layout(

            template='plotly_dark',

            hovermode='x unified',

            height=550,

            yaxis=dict(title='Total Debt'),

            yaxis2=dict(title='Annual Deficit', overlaying='y', side='right'),

            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)

        )

        st.plotly_chart(fig, use_container_width=True)


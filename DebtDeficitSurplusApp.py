# --- Imports ---
import streamlit as st
from streamlit_gsheets import GSheetsConnection
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
    # TODO make a timer to download this once tax policy updates their site
    # getTaxPolicyDownload() in TA class
    dfInstance = TA.Treasury()
    BaseUrl = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
    debt = dfInstance.getHistoricalDebtAPIData(BaseUrl)
    presidents = pd.read_json('AmericanRealityClasses/resources/USAPresidents.json')

    historic_revenues_path = 'AmericanRealityClasses/resources/TaxPolicyCentrHistoricRevenues.xlsx'
    deficit = pd.read_excel(historic_revenues_path, engine='openpyxl', skiprows=6)
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

# 3. Page Config
st.set_page_config(page_title="USA Reality Project", layout="wide")
st.title("USA Cash Flows")
st.caption("Visualizing America's National Debt and Fiscal History")

# bring in our data
dfDebt, dfPresidents, dfDeficit = load_data()


# 4. LIVE DONATION & EXPENSE TRACKER ---
# Replace this URL with your actual Google Sheet Share Link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1Cma1Wdk4yYLq5fiPDG5YCythxEwYnqBPh0Zplro3mD4/edit?usp=sharing"

# Create the connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the two tabs (Donations and Expenses)
# We set ttl=3600 so it only checks for new money once an hour (saves API calls)
try:
    df_donations_live = conn.read(spreadsheet=spreadsheet_url, worksheet="Donations", ttl=3600)
    df_expenses_live = conn.read(spreadsheet=spreadsheet_url, worksheet="Expenses", ttl=3600)

    total_donations = df_donations_live['Amount'].sum()
    total_expenses = df_expenses_live['Amount'].sum()
except Exception:
    # Fallback if the sheet is empty or link is broken
    total_donations = 0.00
    total_expenses = 0.00

net_balance = total_donations - total_expenses

    # --- THE HEADER DISPLAY ---
head_col1, head_col2, head_col3 = st.columns([4, 1, 1])

with head_col1:
    # Use your custom logo here later!
    st.title("The American Reality Project")

with head_col2:
    st.metric("Total Donations", f"${total_donations:,.2f}")

with head_col3:
    # 'Inverse' means red is bad and green is good.
    # Since this is a balance, it'll show your 'burn rate' as the delta.
    st.metric("Project Balance", f"${net_balance:,.2f}",
              delta=f"-${total_expenses:,.2f} costs", delta_color="normal")

st.divider()


# 5. Navigation
viewType = st.pills("Analysis View", ["President", "Year"], selection_mode="single", default="President")
st.divider()

tab1, tab2 = st.tabs(["📊 Data Analysis", "📖 Get Learnt (FAQ)"])

with tab1:
    if viewType == "President":
        # --- 1. MEMORY INITIALIZATION ---
        # This sets the very first person the user sees when they open the site
        if 'selected_pres' not in st.session_state:
            st.session_state.selected_pres = "Bill Clinton"

        # --- 2. THE SELECTOR ---
        st.subheader("Presidential Fiscal Analysis")

        # We calculate the index based on whatever is currently in memory
        pres_list = dfPresidents['name'].tolist()
        current_index = pres_list.index(st.session_state.selected_pres)

        # We use the 'key' to let Streamlit handle the saving automatically
        president = st.selectbox(
            "Choose a President",
            pres_list,
            index=current_index,
            key="pres_selector_key"
        )

        # Immediately update the memory so the next time the app runs, it stays here
        st.session_state.selected_pres = president

        # --- 3. DATA FILTERING ---
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

        # --- 4. CALCULATIONS ---
        st.markdown(f"### {president}'s Fiscal Snapshot ({start_year} - {end_year})")

        # Safety checks for empty data
        beginning_debt = combined_data[combined_data['Year'] == start_year]['Debt'].iloc[0] if not combined_data[
            combined_data['Year'] == start_year].empty else 0
        ending_debt = combined_data[combined_data['Year'] == end_year]['Debt'].iloc[0] if not combined_data[
            combined_data['Year'] == end_year].empty else 0
        total_debt_change = ending_debt - beginning_debt

        beginning_deficit = combined_data[combined_data['Year'] == start_year]['Deficit'].iloc[0] if not combined_data[
            combined_data['Year'] == start_year].empty else 0
        ending_deficit = combined_data[combined_data['Year'] == end_year]['Deficit'].iloc[0] if not combined_data[
            combined_data['Year'] == end_year].empty else 0
        deficit_growth = ending_deficit - beginning_deficit
        cumulative_deficit = combined_data['Deficit'].sum()

        # --- 4.5 'WHAT IF' CALCULATION ---
        term_length = end_year - start_year

        # If they stayed at the 'Inherited' deficit level every year:
        hypothetical_total_deficit = beginning_deficit * term_length
        hypothetical_ending_debt = beginning_debt - hypothetical_total_deficit
        # (Note: we subtract because deficit is a negative number in your data)

        # The "Responsibility Gap" (Difference between reality and the inherited path)
        responsibility_gap = ending_debt - hypothetical_ending_debt

        # --- 5. METRICS (The Fix for Red/Green logic) ---
        st.write("**National Debt Progress**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Debt at Start", format_large_number(beginning_debt))
        m2.metric("Debt at End", format_large_number(ending_debt))
        m3.metric("Total Debt Increase", format_large_number(total_debt_change),
                  delta=format_large_number(total_debt_change), delta_color="inverse")

        st.write("**Annual Deficit & Cumulative Spending**")
        # Dynamic label: says 'Surplus' if the number is positive
        def_label = "Annual Surplus (End)" if ending_deficit > 0 else "Annual Deficit (End)"

        m4, m5, m6 = st.columns(3)
        m4.metric("Annual Deficit (Start)", format_large_number(beginning_deficit))
        m5.metric(def_label,
                  format_large_number(ending_deficit),
                  delta=format_large_number(deficit_growth),
                  delta_color="normal")  # Green if move toward surplus
        m6.metric("Total Term Overspending", format_large_number(cumulative_deficit))

        # Calculate the absolute difference for display
        abs_diff = abs(responsibility_gap)
        comparison_word = "lower" if responsibility_gap < 0 else "higher"

        st.write("---")
        st.markdown("### ⚖️ The Inherited Path")
        c1, c2 = st.columns(2)

        with c1:
            st.write(
                f"If {president} maintained the **inherited** deficit of {format_large_number(beginning_deficit)}/year:")
            st.metric("Hypothetical Debt", format_large_number(hypothetical_ending_debt))

        with c2:
            # This dynamic text fixes the Bill Clinton "Double Negative" issue
            st.write(
                f"Actual debt ended up **{format_large_number(abs_diff)} {comparison_word}** than the inherited path.")

            # We use "normal" delta color here because for Clinton, a negative number is SUCCESS
            st.metric("Policy/Economy Impact",
                      format_large_number(responsibility_gap),
                      delta="Beat the Path" if responsibility_gap < 0 else "Added to Path",
                      delta_color="normal" if responsibility_gap < 0 else "inverse")

        st.divider()

        # --- 6. PLOTTING ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=combined_data['Year'], y=combined_data['Debt'], name='Total Debt',
                                 line=dict(color='#FFD700', width=4), yaxis='y1'))
        fig.add_trace(go.Bar(x=combined_data['Year'], y=combined_data['Deficit'], name='Deficit/Surplus',
                             marker=dict(color='#2E86C1'), opacity=0.6, yaxis='y2'))

        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=500,
            margin=dict(l=10, r=10, t=20, b=10),
            yaxis2=dict(overlaying='y', side='right')
        )
        st.plotly_chart(fig, use_container_width=True)


    else:
        # --- YEAR VIEW CONTROLS ---
        st.subheader("Historical Analysis: Custom Range")

        # 1. Setup bounds
        min_selectable = int(dfDebt['record_fiscal_year'].min())
        max_selectable = int(dfDebt['record_fiscal_year'].max())

        # 2. Initialize Session State
        if 'start_y' not in st.session_state:
            st.session_state.start_y = 1993

        if 'end_y' not in st.session_state:
            st.session_state.end_y = 2001

        if 'y_slider' not in st.session_state:
            st.session_state.y_slider = (1993, 2001)

        # 3. Synchronizing Functions
        def update_slider():
            st.session_state.y_slider = (st.session_state.start_y, st.session_state.end_y)

        def update_inputs():
            st.session_state.start_y = st.session_state.y_slider[0]
            st.session_state.end_y = st.session_state.y_slider[1]

        # 4. UI Controls
        col_left, col_mid, col_right = st.columns([1, 3, 1])
        with col_left:
            st.number_input("Start Year", min_selectable, max_selectable, key="start_y", on_change=update_slider)

        with col_mid:
            st.slider("Range", min_selectable, max_selectable, key="y_slider", on_change=update_inputs,
                      label_visibility="hidden")

        with col_right:
            st.number_input("End Year", min_selectable, max_selectable, key="end_y", on_change=update_slider)

        st.divider()

        # 5. Data Logic
        y_low, y_high = st.session_state.y_slider
        debt_data = dfDebt[(dfDebt['record_fiscal_year'] >= y_low) & (dfDebt['record_fiscal_year'] <= y_high)]
        deficit_data = dfDeficit[(dfDeficit['Fiscal Year'] >= y_low) & (dfDeficit['Fiscal Year'] <= y_high)]
        merger = pd.merge(debt_data, deficit_data, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
        combined_data = pd.DataFrame({
            'Year': merger['record_fiscal_year'].astype(int),
            'Debt': merger['debt_outstanding_amt'],
            'Deficit': merger['Surplus or Deficit(-) Total']
        })

        # --- Metrics Section ---
        st.markdown(f"#### Fiscal Snapshot: {y_low} - {y_high}")
        try:
            beginning_debt = combined_data[combined_data['Year'] == y_low]['Debt'].iloc[0]
            ending_debt = combined_data[combined_data['Year'] == y_high]['Debt'].iloc[0]
            total_debt_change = ending_debt - beginning_debt
            cumulative_deficit = combined_data['Deficit'].sum()
            beginning_deficit = combined_data[combined_data['Year'] == y_low]['Deficit'].iloc[0]
            ending_deficit = combined_data[combined_data['Year'] == y_high]['Deficit'].iloc[0]
            deficit_growth = ending_deficit - beginning_deficit
            m_col1, m_col2, m_col3 = st.columns(3)

            with m_col1:
                st.metric("Debt at Start", format_large_number(beginning_debt))
                st.metric("Annual Deficit (Start)", format_large_number(beginning_deficit))

            with m_col2:
                st.metric("Debt at End", format_large_number(ending_debt))
                st.metric("Annual Deficit (End)", format_large_number(ending_deficit),
                          delta=format_large_number(deficit_growth), delta_color="normal")
            with m_col3:
                st.metric("Total Debt Increase", format_large_number(total_debt_change),
                          delta=format_large_number(total_debt_change), delta_color="inverse")
                st.metric("Cumulative Overspending", format_large_number(cumulative_deficit))

        except:
            st.info("Adjust range for metrics.")

        st.divider()

        # --- Graph Section ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=combined_data['Year'], y=combined_data['Debt'], name='Debt',
                                 line=dict(color='#FFD700', width=3), yaxis='y1'))
        fig.add_trace(
            go.Bar(x=combined_data['Year'], y=combined_data['Deficit'], name='Deficit', marker=dict(color='#2E86C1'),
                   opacity=0.6, yaxis='y2'))
        fig.update_layout(template='plotly_dark', hovermode='x unified', height=450,
                          margin=dict(l=10, r=10, t=20, b=10), yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Data Sources & FAQ")

    st.markdown("""
        ### 📚 Official Resources
        This project pulls live data from official government and policy research institutions:

        * **[Treasury Fiscal Data API](https://fiscaldata.treasury.gov/api-documentation/)**: Provides the historical debt outstanding from 1789 to present.
        * **[Historical Debt Dataset](https://fiscaldata.treasury.gov/datasets/historical-debt-outstanding/historical-debt-outstanding)**: Direct source for government debt summaries.
        * **[Tax Policy Center](https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx)**: Used for deficit and outlay data that supplements the Treasury's records.

        ---
        ### 💡 FAQ
        **Why does the Treasury only have records back to 1995 for some sets?**
        As noted in our sources, while debt totals are tracked back to 1789, detailed digital breakdowns of receipts and outlays often require external historical research (like the Tax Policy Center) to "make it make sense" for earlier decades.

        **How often is this data updated?**
        The Treasury API is updated daily, but historical annual debt is finalized at the end of each fiscal year.
        """)
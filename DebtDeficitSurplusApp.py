
# TODO: Make a web app with docker and use streamlit or PyQT(advanced)

# #imports
import streamlit as st
import plotly.graph_objects as go
from AmericanRealityClasses import TreasuryApi as TA
import pandas as pd
import math

# needed for numbers to display without scientific notation
# pd.options.display.float_format = '{:,.2f}'.format

#Create isntance to get data
dfInstance = TA.Treasury()
BaseUrl = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
dfDebt = dfInstance.getHistoricalDebtAPIData(BaseUrl)
dfPresidents = pd.read_json('AmericanRealityClasses/resources/USAPresidents.json')

# this will dL the info on every click
# dfDeficit = dfInstance.getTaxPolicyDownload() 

# manual dfDeficit comment out when a new download is needed -Start #TODO: put a yearly time into this method!
path = 'AmericanRealityClasses/resources/TaxPolicyCentrHistoricRevenues.xlsx'

#start on main headers
dfDeficit = pd.read_excel(path,engine='openpyxl',skiprows=6)
# drop first row is empty
dfDeficit = dfDeficit.drop(0)
# resname lost columns
dfDeficit.rename(columns={"Unnamed: 0":"Fiscal Year","Total":"Receipts Total","Total.1":"Outlays Total","Total.2":"Surplus or Deficit(-) Total"},inplace=True)
# get rid of dat at the end of table dealing wiith estimating data
estimateIndex = dfDeficit[dfDeficit['Fiscal Year'].str.contains('Estimates',case=False,na=False)].index[0]
dfDeficit = dfDeficit.iloc[:estimateIndex-2]
dfDeficit = dfDeficit[dfDeficit['Fiscal Year']!='TQ']
dfDeficit['Fiscal Year'] = dfDeficit['Fiscal Year'].astype(int)
dfDeficit['Surplus or Deficit(-) Total'] = dfDeficit['Surplus or Deficit(-) Total'] * 1_000_000
# manual dfDeficit comment out when a new download is needed -Finsih comment 


# page defaults:
st.set_page_config(layout="wide")

st.title("USA Reality Project")

# Make tabs containers so it views better on mobile phones
tab1, tab2, tab3, = st.tabs(["📊 National Debt", "📉 Annual Deficit", "📖 Get Learnt (FAQ)"])

# Create a custom container with a different background color
# st.markdown(
#     """
#     <div style="background-color:#f2f2f2; padding: 20px; border-radius: 10px; text-align: center;">
#         <h1 style="color: #1f77b4;">Welcome To JQTs369 First App!</h1>
#         <h2 style="color: #ff6347;">History of America's Debt & Surplus/Deficits.</h2>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# Add vertical space after the container
st.markdown("<br>", unsafe_allow_html=True)

# Add some vertical space before the next section
st.markdown("<br>", unsafe_allow_html=True)

# User Selection Opitions
# viewType = st.selectbox('President/Year Selection:', ['President','Year'])
viewType = st.sidebar.radio('President/Year Selection:', ['President','Year'])

st.markdown(
    f"""
    <h1 style='text-align: center;'>President Selected: {viewType}</h1>
    """, 
    unsafe_allow_html=True
)
if viewType == "President":
    # 1. Main Page Selector (Better for Mobile)
    st.subheader("Select a President to Analyze")
    default_president = "Bill Clinton"
    president = st.selectbox(
        "Choose a President",
        dfPresidents['name'],
        index=dfPresidents['name'].tolist().index(default_president),
        label_visibility="collapsed"  # Keeps it clean
    )

    # --- Data Processing (Keep your existing logic) ---
    presidentData = dfPresidents[dfPresidents['name'] == president].iloc[0]
    startYear = int(presidentData['start_year'])
    endYear = int(presidentData['end_year'])
    debtData = dfDebt[(dfDebt['record_fiscal_year'] >= startYear) & (dfDebt['record_fiscal_year'] <= endYear)]
    deficitData = dfDeficit[(dfDeficit['Fiscal Year'] >= startYear) & (dfDeficit['Fiscal Year'] <= endYear)]

    mergerdf = pd.merge(debtData, deficitData, left_on='record_fiscal_year',
                        right_on='Fiscal Year', how='outer', suffixes=('_debt', '_deficit'))

    chartData = pd.DataFrame({
        'Year': mergerdf['record_fiscal_year'].astype(int),
        'Debt': mergerdf['debt_outstanding_amt'],
        'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']
    })

    # --- 2. THE "SNAPSHOT" HEADER (Replaces your HTML table) ---
    # This automatically stacks vertically on mobile!
    st.markdown(f"### {president}'s Fiscal Snapshot ({startYear} - {endYear})")

    beg_debt = chartData[chartData['Year'] == startYear]['Debt'].iloc[0] if not chartData[
        chartData['Year'] == startYear].empty else 0
    end_debt = chartData[chartData['Year'] == endYear]['Debt'].iloc[0] if not chartData[
        chartData['Year'] == endYear].empty else 0

    # Calculate the change during the term
    debt_change = end_debt - beg_debt

    m1, m2, m3 = st.columns(3)
    m1.metric("Debt at Start", format_large_number(beg_debt))
    m2.metric("Debt at End", format_large_number(end_debt))
    m3.metric("Total Change", format_large_number(debt_change), delta=format_large_number(debt_change),
              delta_color="inverse")

    st.divider()

    # --- 3. THE GRAPH (Mobile Fix) ---
    # We remove the fixed width=2200 so it fits the screen automatically
    fig = go.Figure()

    # Add Debt Line
    fig.add_trace(go.Scatter(x=chartData['Year'], y=chartData['Debt'], name='Total Debt',
                             line=dict(color='#FFD700', width=4), yaxis='y1'))

    # Add Deficit Bar (Easier to see "yearly flow" vs "total balance")
    fig.add_trace(go.Bar(x=chartData['Year'], y=chartData['Deficit/Surplus'], name='Annual Deficit/Surplus',
                         marker=dict(color='#2E86C1'), opacity=0.6, yaxis='y2'))

    fig.update_layout(
        hovermode='x unified',
        template='plotly_dark',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(title='Total Debt', side='left'),
        yaxis2=dict(title='Annual Deficit/Surplus', overlaying='y', side='right'),
        height=500  # Fixed height, but width is responsive
    )

    # IMPORTANT: use_container_width=True is the key for mobile!
    st.plotly_chart(fig, use_container_width=True)

elif viewType == 'Year':
    # Add a range slider for the user to pick a range of years
    min_year = int(dfDebt['record_fiscal_year'].min())
    max_year = int(dfDebt['record_fiscal_year'].max())
    # selected_years = st.slider("Select Year Range", min_year, max_year, (1993, 2001))
    st.sidebar.subheader("Year Range Selector")
    selected_years = st.sidebar.slider("",min_year, max_year, (1982, 2002))

    # Filter the data for the selected year range
    debtData = dfDebt[(dfDebt['record_fiscal_year'] >= selected_years[0]) & (dfDebt['record_fiscal_year'] <= selected_years[1])]
    deficitData = dfDeficit[(dfDeficit['Fiscal Year'] >= selected_years[0]) & (dfDeficit['Fiscal Year'] <= selected_years[1])]

    mergerdf = pd.merge(
        debtData,
        deficitData,
        left_on='record_fiscal_year',
        right_on='Fiscal Year',
        how='outer',
        suffixes=('_debt', '_deficit')
    )
    mergerdf['record_fiscal_year'] = mergerdf['record_fiscal_year'].astype(str)

    # Data Setup for easy plotting
    chartData = pd.DataFrame({
        'Year': mergerdf['record_fiscal_year'],
        'Debt': mergerdf['debt_outstanding_amt'],
        'Deficit/Surplus': mergerdf['Surplus or Deficit(-) Total']
    })
    chartData['Year'] = chartData['Year'].astype(int)

    # Display the selected year range
    st.write(f"Selected Year Range: {selected_years[0]} - {selected_years[1]}")

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

    # Function to format the table with alternating row colors (dark blue and white text)
    def color_alternating_rows(df):
        html = df.to_html(index=False, escape=False)
        
        # Adding CSS for alternating row colors
        html = html.replace('<thead>', '<thead style="background-color:#003366; color: white;">')  # Dark blue header
        rows = html.split('<tr>')
        
        for i in range(1, len(rows)):
            if i % 2 == 0:  # Even rows: dark blue background, white text
                rows[i] = f'<tr style="background-color: #003366; color: white;">' + rows[i]
            else:  # Odd rows: keep white background and default color
                rows[i] = f'<tr style="background-color: #ffffff; color: black;">' + rows[i]
        
        return ''.join(rows)

    # Table summary for the selected year range
    try:
        beginningDebt = chartData[(chartData['Year'] == selected_years[0])]['Debt'].iloc[0]
        endingDebt = chartData[(chartData['Year'] == selected_years[1])]['Debt'].iloc[0]
    except:
        beginningDebt = None
        endingDebt = None

    try:
        beginningDeficit = chartData[(chartData['Year'] == selected_years[0])]['Deficit/Surplus'].iloc[0]
        endingDeficit = chartData[(chartData['Year'] == selected_years[1])]['Deficit/Surplus'].iloc[0]
    except:
        beginningDeficit = None
        endingDeficit = None

    summaryData = {
        "Start/End": [
            'Starting Debt', 'Starting Deficit',
            'Ending Debt', 'Ending Deficit/Surplus'
        ],
        "$ Amounts": [
            format_large_number(beginningDebt), format_large_number(beginningDeficit),
            format_large_number(endingDebt), format_large_number(endingDeficit)
        ]
    }
    summaryDf = pd.DataFrame(summaryData)
    # st.markdown(color_alternating_rows(summaryDf), unsafe_allow_html=True)
        # Display the table with alternating row colors - Centered
    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.markdown(color_alternating_rows(summaryDf), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Graphs
    fig = go.Figure()

    # Add Debt Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Debt'],
        mode='lines',
        name='Debt',
        line=dict(color='yellow'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y1'
    ))

    # Add Deficit/Surplus Linechart
    fig.add_trace(go.Scatter(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        mode='lines',
        name='Deficit/Surplus',
        line=dict(color="red"),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2'
    ))

    # Add a bar chart
    fig.add_trace(go.Bar(
        x=chartData['Year'],
        y=chartData['Deficit/Surplus'],
        name='Deficit/Surplus',
        marker=dict(color='blue'),
        hovertemplate='%{x}: $%{y} <extra></extra>',
        yaxis='y2',
        opacity=0.4
    ))

    fig.update_layout(
        title=f"Debt and Deficit/Surplus from {selected_years[0]} to {selected_years[1]}",
        title_x=0.5,  # Center the title horizontally
        title_xanchor='center',  # Ensure the title is anchored at the center
        title_font=dict(size=24, color="white"),
        xaxis_title='Year',
        yaxis=dict(
            title='Debt ($)',
            # titlefont=dict(color='yellow'),
            tickfont=dict(color='yellow')
        ),
        yaxis2=dict(
            title='Deficit/Surplus ($)',
            # titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_dark',
        barmode='group',
        width=2200,
        height=625
    )

    # Show the Plotly figure in Streamlit
    st.plotly_chart(fig)



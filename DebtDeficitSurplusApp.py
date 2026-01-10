# --- Imports ---
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import math
# personal Classes
from AmericanRealityClasses import TreasuryApi as TA
from AmericanRealityClasses.Tax_Calculator import tax_logic as TL

# --- ANNOUNCEMENT TOGGLE ---
show_announcement = True  # Set too False to hide it
announcement_text ="📊 **COMING SOON:** Yearly Budget Reports! We're currently mapping historical spending categories (Defense, Healthcare, etc.) to give you a full picture of where the money went."


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
    # instances
    df_instance = TA.Treasury()
    tax_manager = TL.TaxDataManager()

    base_url = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
    debt, data_flag = df_instance.getHistoricalDebtAPIData(base_url)
    presidents = pd.read_json('AmericanRealityClasses/resources/USAPresidents.json')
    deficits = deficit = df_instance.getTaxPolicyDownload()

    # Get the min/max rates from your new logic
    tax_extremes = tax_manager.get_annual_rate_extremes(status='single')

    if debt.empty or deficits.empty:
        return pd.DataFrame(),presidents,pd.DataFrame(), data_flag

    # MERGE TAX DATA INTO DEBT
    # This ensures every year in 'debt' now knows its High/Low tax rates
    debt = pd.merge(debt, tax_extremes, left_on='record_fiscal_year', right_on='Year', how='left')

    return debt, presidents, deficits, data_flag


# 3. Page Config
st.set_page_config(
    page_title="USA Reality Project",
    page_icon="https://cdn-icons-png.flaticon.com/128/1973/1973588.png",  # This shows the icon in the browser tab! https://www.flaticon.com/
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- ANNOUNCEMENT Placement
if show_announcement:
    st.info(announcement_text, icon="🚀")


    # Visually "popping" header
st.markdown(
    """
    <div style="text-align: left;">
        <h1 style="color: #FFD700; margin-bottom: 0;">USA <span style="color: #ffffff;">CASH FLOWS</span></h1>
        <p style="color: #888; font-size: 1.2em; margin-top: 0;">The American Reality Project</p>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Visualizing America's National Debt and Fiscal History")



# --- 4. LIVE DONATION & EXPENSE TRACKER --- Google Sheets for now
# Use the export format to get the data directly as a CSV
sheet_id = "1Cma1Wdk4yYLq5fiPDG5YCythxEwYnqBPh0Zplro3mD4"
donations_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Donations"
expenses_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Expenses"


@st.cache_data(ttl=60)  # Only check the sheet once per minute
def get_ledger_data():
    try:
        df_donations = pd.read_csv(donations_url)
        df_expenses = pd.read_csv(expenses_url)

        # Clean column names (removes spaces/quotes)
        df_donations.columns = df_donations.columns.str.strip()
        df_expenses.columns = df_expenses.columns.str.strip()

        d_total = pd.to_numeric(df_donations['Amount']).sum()
        e_total = pd.to_numeric(df_expenses['Amount']).sum()

        return df_donations, df_expenses, d_total, e_total
    except Exception as e:
        # If it fails, return empty frames and $0
        return pd.DataFrame(), pd.DataFrame(), 0.0, 0.0


# Execute the loading
df_donations_live, df_expenses_live, total_donations, total_expenses = get_ledger_data()
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

tab1, tab2, tab3 = st.tabs(["📊 Data Analysis", "💸 Transparency Ledger" ,"📖 Get Learnt (FAQ)"])

# 6. Bring in our data
debt_df, df_presidents, df_deficit, data_flag = load_data()

with tab1:
    if data_flag != 'API':
        st.info('Current Debt Data is from Treasury Back up - API must be down ')

    if debt_df.empty:
        # This ONLY triggers if the API is 503 AND the 'resources/debt_backup' file is missing
        st.error("🔌 Treasury Data Source Unavailable - Current Error: 503 Service Temporarily Unavailable")

        st.warning("""
                    **Status:** API Connection Failed & No Local Backup Found.

                    The Treasury servers are likely down for New Year maintenance. Since no local 
                    backup was detected, the interactive charts are disabled.
                """)
    else:
        if viewType == "President":
            # --- 1. MEMORY INITIALIZATION ---
            # This sets the very first person the user sees when they open the site
            if 'selected_pres' not in st.session_state:
                st.session_state.selected_pres = "Bill Clinton"

            # --- 2. THE SELECTOR ---
            st.subheader("Presidential Fiscal Analysis")

            # We calculate the index based on whatever is currently in memory
            pres_list = df_presidents['name'].tolist()
            current_index = pres_list.index(st.session_state.selected_pres)

            # We use the 'key' to let Streamlit handle the saving automatically
            president = st.selectbox(
                "Choose a President",
                pres_list,
                index=current_index,
                key="selectbox_key",
                help="Tip: You can type the name to search quickly!"
            )

            # Immediately update the memory so the next time the app runs, it stays here
            st.session_state.selected_pres = president

            # --- 3. DATA FILTERING ---
            president_data = df_presidents[df_presidents['name'] == president].iloc[0]
            start_year, end_year = int(president_data['start_year']), int(president_data['end_year'])

            # Check if the dataframe actually has data before filtering

            debt_data = debt_df[(debt_df['record_fiscal_year'] >= start_year) & (debt_df['record_fiscal_year'] <= end_year)]
            deficit_data = df_deficit[(df_deficit['Fiscal Year'] >= start_year) & (df_deficit['Fiscal Year'] <= end_year)]
            merger = pd.merge(debt_data, deficit_data, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
            combined_data = pd.DataFrame({
                'Year': merger['record_fiscal_year'].astype(int),
                'Debt': merger['debt_outstanding_amt'],
                'Deficit': merger['Surplus or Deficit(-) Total'],
                # add the tax rates
                'Low_Tax': merger.get('Lowest_Rate', 0),
                'High_Tax': merger.get('Highest_Rate', 0)
            })
            # get surplus of deficit status
            combined_data['Def_Label'] = combined_data['Deficit'].apply(lambda x: "Surplus" if x > 0 else "Deficit")

            # --- 4. CALCULATIONS ---
            st.markdown(f"### {president}'s Fiscal Snapshot ({start_year} - {end_year})")

            # debt info
            beginning_debt = combined_data[combined_data['Year'] == start_year]['Debt'].iloc[0] if not combined_data[
                combined_data['Year'] == start_year].empty else 0

            ending_debt = combined_data[combined_data['Year'] == end_year]['Debt'].iloc[0] if not combined_data[
                combined_data['Year'] == end_year].empty else 0

            total_debt_change = ending_debt - beginning_debt

            # deficit info
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

            # The "Responsibility Gap" (Difference between reality and the inherited path)
            responsibility_gap = ending_debt - hypothetical_ending_debt

            # --- 5. METRICS ---
            st.write("**National Debt Progress**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Debt at Start", format_large_number(beginning_debt))
            m2.metric("Debt at End", format_large_number(ending_debt))
            m3.metric("Total Debt Increase", format_large_number(total_debt_change),
                      delta=format_large_number(total_debt_change), delta_color="inverse",
            help = "This is the 'Bottom Line'—it includes all new spending PLUS the interest paid on debt inherited from previous Presidents."
            )

            st.write("**Annual Deficit & Cumulative Spending**")
            # Dynamic label: says 'Surplus' if the number is positive
            def_label = "Annual Surplus (End)" if ending_deficit > 0 else "Annual Deficit (End)"

            # Check if it's a deficit or surplus while it's still a raw number
            deficit_surplus_comparison_word = 'Deficit' if beginning_deficit < 0 else 'Surplus'

            # NOW format it for the display
            formatted_beginning_deficit = format_large_number(beginning_deficit)

            m4, m5, m6 = st.columns(3)
            m4.metric(f"Annual {deficit_surplus_comparison_word} (Start)", format_large_number(beginning_deficit))
            m5.metric(def_label,
                      format_large_number(ending_deficit),
                      delta=format_large_number(deficit_growth),
                      delta_color="normal")  # Green if move toward surplus
            # m6.metric("Total Term Overspending", format_large_number(cumulative_deficit))
            # Flip the sign for the 'overspending' to make it a positive 'Debt Added' number
            debt_added_by_term = cumulative_deficit * -1

            m6.metric(
                label="New Policy Spending",
                value=format_large_number(debt_added_by_term),
                help="This is the 'Term Deficit'—the total amount spent on programs/wars minus taxes collected."
            )

            # Calculate the absolute difference for display
            abs_diff = abs(responsibility_gap)
            comparison_word = "lower" if responsibility_gap < 0 else "higher"

            st.write("---")
            st.markdown("### ⚖️ The Inherited Momentum")
            st.caption(
                "No President starts at zero. This section compares the path they were handed vs. what actually happened.")

            c1, c2 = st.columns(2)

            with c1:
                # 1. Determine if they inherited a hole (deficit) or a mountain (surplus)
                inherited_type = "overspending (deficit)" if beginning_deficit < 0 else "saving (a surplus)"

                # 2. Get the formatted amount for the text
                inherited_amt = format_large_number(abs(beginning_deficit))  # Use abs() so we don't say 'deficit of -200B'

                st.write(f"**The 'Stay the Course' Path**")

                # 3. The 6th-grade explanation
                st.info(f"""
                    When {president} took office, the government was already {inherited_type} by 
                    **{inherited_amt}** every year. 
    
                    If they had changed nothing and just 'stayed the course' for their {term_length} years in office:
                """)

                st.metric("Predicted Debt", format_large_number(hypothetical_ending_debt))

            with c2:
                # Explain the 'Result'
                st.write(f"**The Reality**")

                # Simple logic for the comparison sentence
                if responsibility_gap < 0:
                    outcome_text = f"ended up **{format_large_number(abs_diff)} LOWER**"
                    delta_label = "Improved the Path"
                else:
                    outcome_text = f"ended up **{format_large_number(abs_diff)} HIGHER**"
                    delta_label = "Added to the Path"

                st.write(f"Under {president}, the national debt {outcome_text} than if they had just 'stayed the course.'")

                st.metric("Net Fiscal Impact",
                          format_large_number(responsibility_gap),
                          delta=delta_label,
                          delta_color="normal" if responsibility_gap < 0 else "inverse")

            st.divider()

            # --- 6. PLOTTING ---
            fig = go.Figure()

            # 1. THE ACTUAL DEBT (Gold)
            fig.add_trace(go.Scatter(
                x=combined_data['Year'],
                y=combined_data['Debt'],
                name='Actual Debt',
                line=dict(color='#FFD700', width=4),
                yaxis='y1',
                # Add Def_Label to customdata here too!
                customdata=combined_data[['Low_Tax', 'High_Tax', 'Def_Label']],
                hovertemplate=(
                        "<span style='font-size:22px;'><b>📅 %{x}</b></span><br><br>" +
                        "<span style='font-size:20px;'>💰 <b>Debt:</b> %{y}</span><br>" +
                        "<span style='font-size:20px;'>📊 <b>%{customdata[2]}:</b> %{customdata[1]}</span><br>" +
                        "<span style='font-size:20px;'>📉 <b>Min Tax:</b> %{customdata[0]:.1f}%</span><br>" +
                        "<span style='font-size:20px;'>📈 <b>Max Tax:</b> %{customdata[1]:.1f}%</span>" +
                        "<extra></extra>"
                )
            ))

            # 2. THE INHERITED PATH (Silver Dashed)
            fig.add_trace(go.Scatter(
                x=[start_year, end_year],
                y=[beginning_debt, hypothetical_ending_debt],
                name='Inherited Path',
                line=dict(color='#C0C0C0', width=2, dash='dot'),
                yaxis='y1'
            ))

            # 3. THE DEFICIT BARS (Blue)
            fig.add_trace(go.Bar(
                x=combined_data['Year'],
                y=combined_data['Deficit'],
                name='Annual Fiscal Status',
                customdata=combined_data['Def_Label'],  # Pass the labels here
                hovertemplate="<b>%{customdata}:</b> %{y}<extra></extra>",  # Use the label
                marker=dict(color='#2E86C1'),
                opacity=0.4,
                yaxis='y2'
            ))

            fig.update_layout(
                template='plotly_dark',
                hovermode='x unified',
                height=500,
                showlegend=True,  # Make sure users can see which line is which
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=20, b=10),
                yaxis2=dict(overlaying='y', side='right', showgrid=False)
            )


            fig.update_layout(
                template='plotly_dark',
                hovermode='x unified',
                height=600,  # Made it taller
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=20, b=10),
                yaxis2=dict(overlaying='y', side='right', showgrid=False),
                # THE BIGGER BOX SETTINGS:
                hoverlabel=dict(
                    bgcolor="#1e1e1e",
                    font_size=24,
                    bordercolor="#FFD700",
                    namelength=-1
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- 7. SPENDING BREAKDOWN (THE PIE) ---
            st.divider()

            # Fix: We define the label using only 'president' since we are in the President block
            pie_label = f"the {president} Administration"

            st.subheader(f"🏛️ Budget Breakdown: Where did the money go?")
            st.info("🚧Still Under Construction🚧")
            st.caption(f"Estimated average spending categories for {pie_label}")

            # Placeholder data (to be linked to your data source later)
            sample_spending = pd.DataFrame({
                "Category": ["Social Security", "Health (Medicare/Medicaid)", "National Defense", "Interest on Debt",
                             "Other Services"],
                "Amount": [21, 15, 13, 11, 40]
            })

            fig_pie = px.pie(
                sample_spending,
                values='Amount',
                names='Category',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig_pie.update_layout(
                template="plotly_dark",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )

            # Display with columns
            p_col1, p_col2 = st.columns([2, 1])
            with p_col1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with p_col2:
                st.markdown("#### **Budgetary Insights**")
                st.write(f"""
                                This breakdown illustrates how tax dollars were allocated during {pie_label}. 

                                **Note on Interest:** The 'Interest on Debt' slice represents the cost of 
                                servicing existing debt. This is mandatory spending that does not fund 
                                current programs or infrastructure.
                            """)

        else:
            # --- YEAR VIEW CONTROLS ---
            st.subheader("Historical Analysis: Custom Range")

            # 1. Setup bounds
            min_selectable = int(debt_df['record_fiscal_year'].min())
            max_selectable = int(debt_df['record_fiscal_year'].max())

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
            debt_data = debt_df[(debt_df['record_fiscal_year'] >= y_low) & (debt_df['record_fiscal_year'] <= y_high)]
            deficit_data = df_deficit[(df_deficit['Fiscal Year'] >= y_low) & (df_deficit['Fiscal Year'] <= y_high)]
            merger = pd.merge(debt_data, deficit_data, left_on='record_fiscal_year', right_on='Fiscal Year', how='outer')
            combined_data = pd.DataFrame({
                'Year': merger['record_fiscal_year'].astype(int),
                'Debt': merger['debt_outstanding_amt'],
                'Deficit': merger['Surplus or Deficit(-) Total'],
                # add the tax rates
                'Low_Tax': merger.get('Lowest_Rate', 0),
                'High_Tax': merger.get('Highest_Rate', 0)
            })
            # get surplus of deficit status
            combined_data['Def_Label'] = combined_data['Deficit'].apply(lambda x: "Surplus" if x > 0 else "Deficit")

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

            # Year View:
            fig.add_trace(go.Scatter(
                x=combined_data['Year'],
                y=combined_data['Debt'],
                name='Actual Debt',
                line=dict(color='#FFD700', width=4),
                yaxis='y1',
                # We feed it 3 things: Low Tax, High Tax, and the Label (Surplus/Deficit)
                customdata=combined_data[['Low_Tax', 'High_Tax', 'Def_Label']],
                hovertemplate=(
                        "<span style='font-size:26px;'><b>📅 %{x}</b></span><br><br>" +
                        "<span style='font-size:20px;'>💰 <b>Debt:</b> %{y}</span><br>" +
                        "<span style='font-size:20px;'>📊 <b>%{customdata[2]}:</b> %{customdata[1]}</span><br>" +
                        "<span style='font-size:20px;'>📉 <b>Min Tax:</b> %{customdata[0]:.1f}%</span><br>" +
                        "<span style='font-size:20px;'>📈 <b>Max Tax:</b> %{customdata[1]:.1f}%</span>" +
                        "<extra></extra>"
                )
            ))

            # --- Year View: Bar Trace Fix ---
            fig.add_trace(
                go.Bar(
                    x=combined_data['Year'],
                    y=combined_data['Deficit'],
                    name='Annual Fiscal Status',
                    customdata=combined_data['Def_Label'],
                    hovertemplate="<b>%{customdata}:</b> %{y}<extra></extra>",
                    marker=dict(color='#2E86C1'),
                    opacity=0.6,
                    yaxis='y2'
                )
            )

            # --- YEAR VIEW LAYOUT ---
            fig.update_layout(
                template='plotly_dark',
                hovermode='x unified',
                height=600,
                margin=dict(l=10, r=10, t=20, b=10),
                yaxis2=dict(overlaying='y', side='right'),
                hoverlabel=dict(
                    bgcolor="#1e1e1e",
                    font_size=24,
                    font_family="Arial Black",
                    bordercolor="#FFD700"
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # 7. SPENDING BREAKDOWN
            st.divider()

            # Use the variables already defined in your Year View
            pie_label_year = f"the {y_low} - {y_high} Period"

            st.subheader(f"🏛️ Budget Breakdown: Where did the money go?")
            st.caption(f"Estimated average spending categories for {pie_label_year}")

            # Placeholder data (we can make this dynamic later)
            sample_spending_year = pd.DataFrame({
                "Category": ["Social Security", "Health (Medicare/Medicaid)", "National Defense", "Interest on Debt",
                             "Other Services"],
                "Amount": [21, 15, 13, 11, 40]
            })

            fig_pie_year = px.pie(
                sample_spending_year,
                values='Amount',
                names='Category',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig_pie_year.update_layout(
                template="plotly_dark",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )

            py_col1, py_col2 = st.columns([2, 1])
            with py_col1:
                st.plotly_chart(fig_pie_year, use_container_width=True)
            with py_col2:
                st.markdown("#### **Budgetary Insights**")
                st.write(f"This represents the average distribution of federal spending across {pie_label_year}.")
                st.info(
                    "The **Interest on Debt** slice is particularly important when looking at long year ranges, as it shows the growing cost of borrowing.")


with tab2:
    st.header("Project Transparency & Resources")

    # This creates a colored 'Announcement' style box
    st.markdown(
        """
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #3d3d3d; text-align: center;">
            <h3 style="color: #FFD700; margin-top: 0;">☕ Support the Mission</h3>
            <p style="color: #ffffff; font-size: 1.1em;">
                This project is 100% independent. No ads, no corporate sponsors. Just raw data.
            </p>
            <p style="color: #888; font-style: italic;">
                (Donation portal currently under maintenance while we finalize connections)
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # 2. The Detailed Ledger with Error Handling
    st.subheader("Live Project Ledger")

    try:
        # We check if the dataframes exist and aren't just empty 'None' objects
        if 'df_donations_live' in locals() and 'df_expenses_live' in locals():
            col_led1, col_led2 = st.columns(2)

            with col_led1:
                st.write("**Recent Donations**")
                if not df_donations_live.empty:
                    st.dataframe(df_donations_live, use_container_width=True, hide_index=True)
                else:
                    st.caption("No donations recorded yet.")

            with col_led2:
                st.write("**Operating Expenses**")
                if not df_expenses_live.empty:
                    st.dataframe(df_expenses_live, use_container_width=True, hide_index=True)
                else:
                    st.caption("No expenses recorded yet.")
        else:
            raise NameError  # Trigger the exception if data isn't loaded

    except Exception:
        # "Finally/Fallback" view while the GSheets connection is WIP
        st.markdown("""
        > 🛠️ **Ledger Status: Connection Pending** > The live transparency ledger is currently being linked to the project's data-tracking sheet. 
        > Once live, this section will show real-time audits of every dollar received and spent.
        """)

with tab3:
    st.header("📖 The Mission: Clarity Over Conflict")

    st.markdown("""
    ### Why I built this
    Fiscal data is often weaponized to support a specific narrative. My goal with the **USA Reality Project** is to provide a tool that lets the numbers speak for themselves, without the "spin."

    ### The Methodology
    * **Hybrid Data Approach:** To ensure 100% accuracy, we pull the **Total National Debt** directly from the [Treasury's Fiscal Data API](https://fiscaldata.treasury.gov/). However, because official digital records for annual spending are fragmented prior to 1995, we utilize the **Tax Policy Center’s** historical datasets for **Receipts and Outlays**.
    * **Fair Comparison:** By using the **Inherited Path** metric, we acknowledge that no President starts with a clean slate. Every leader is handed a "momentum" of debt and deficit that they must manage.
    * **Independent:** This project is self-funded and user-supported. We don't answer to any party or organization.

    ### How to read the charts
    * **Gold Line:** Total National Debt Outstanding (The "Credit Card Balance").
    * **Blue Bars:** Annual Surplus or Deficit (The "Monthly Overspending" or "Savings").
    """)

    st.divider()

    st.header("Data Sources & FAQ")

    st.markdown("""
        ### 📚 Official Resources
        This project pulls live data from official government and policy research institutions:

        * **[Treasury Fiscal Data API](https://fiscaldata.treasury.gov/api-documentation/)**: Provides the historical debt outstanding from 1789 to present.
        * **[Tax Policy Center (TPC)](https://taxpolicycenter.org/statistics/federal-receipt-and-outlay-summary)**: A non-partisan joint venture of the Urban Institute and Brookings Institution. We use their curated historical receipts and outlays to bridge the gap in official digital records.

        ---
        ### 💡 FAQ
        **Why not use the Treasury for everything?**
        While the Treasury is the source of truth for total debt, their modern digital API for annual "Receipts and Outlays" (the budget breakdown) is primarily focused on the years 1995 to the present. The Tax Policy Center provides the necessary historical research to "make it make sense" for earlier decades.

        **Is there a difference between "Debt" and "Deficit"?**
        Yes! The **Deficit** is the amount of money the government overspends in a single year (the Blue Bars). The **Debt** is the total accumulated amount owed over time (the Gold Line).

        **How often is this data updated?**
        The Treasury API is updated daily, but historical annual debt is typically finalized at the end of each fiscal year (Sept 30th).
        """)
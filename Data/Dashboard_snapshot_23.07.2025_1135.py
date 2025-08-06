#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

from st_aggrid import AgGrid, GridOptionsBuilder

# Establishing database connection
from db_connection import fetch_one
from db_connection import run_query


#######################

# Dummy data
table_1 = pd.DataFrame({
    'S No.': [1, 2],
    'Item Code': ['D001', 'D002'],
    'Item Name': ['Paracetamol', 'Ibuprofen'],
    'Stock on Hand': [100, 150],
    'Pending Supply': [50, 0],
    'RC Status': ['Available', 'Pending'],
    'Stock Suff. Months': [2, 1],
    'Stock + Pending Supply Suff. Months': [3, 1]
})

table_2 = pd.DataFrame({
    'S No.': [1, 2],
    'Item Code': ['D010', 'D011'],
    'Item Name': ['Amoxicillin', 'Ciprofloxacin'],
    'Stock on Hand': [200, 100],
    'Pending Supply': [100, 50],
    'RC Status': ['Available', 'Available'],
    'Stock Suff. Months': [4, 2],
    'Stock + Pending Supply Suff. Months': [5, 3]
})

# Dummy data for table
dummy_data = {
    "S No.": [1, 2, 3, 4, 5],
    "Item Code": ["D001", "D002", "D003", "D004", "D005"],
    "Item Name": ["Paracetamol", "Amoxicillin", "Ciprofloxacin", "Ibuprofen", "Azithromycin"],
    "Stock on Hand": [2500, 1300, 800, 1600, 400],
    "Pending Supply": [500, 200, 0, 400, 600],
    "RC Status": ["Active", "Pending", "Expired", "Active", "Pending"],
    "Stock Suff. Months": [3.2, 1.5, 0.8, 2.0, 0.6],
    "Stock + Pending Supply Suff. Months": [4.0, 1.8, 0.8, 2.5, 1.4]
}
df_dummy = pd.DataFrame(dummy_data)

# Initialize session state
if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = "None"

def format_indian_number(number):
    """Format number with commas as per Indian numbering system"""
    if number is None:
        return "0"
    
    s = str(int(number))
    if len(s) <= 3:
        return s

    # Split last 3 digits
    last_three = s[-3:]
    rest = s[:-3]

    # Process rest in reverse, adding comma every 2 digits
    rest = rest[::-1]
    chunks = [rest[i:i+2][::-1] for i in range(0, len(rest), 2)]
    formatted = ','.join(chunks[::-1]) + ',' + last_three

    return formatted


####################### QUERIES ####################### 

query = "SELECT count(item_code) FROM stock_data;"
total_drugs = fetch_one(query) or 0  # fallback to 0 if None
total_drugs = format_indian_number(total_drugs)

#######################
# Page configuration
st.set_page_config(
    page_title="Dashboard for Drugs",
    # page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")


alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.metric-box {
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 10px;
    text-align: center;
    font-weight: bold;
    font-size: 18px;
}
.lightblue { background-color: #E5E4E2; }
.lightgreen { background-color: #D5F5E3; }
.lightyellow { background-color: #FCF3CF; }
.lightred { background-color: #F5B7B1; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
details > summary {
    font-size: 32px !important;
    font-weight: 800 !important;
    color: #000000 !important;
    line-height: 1.6;
    padding: 10px 0px;
}

details summary::-webkit-details-marker {
    display: none;
}
</style>
""", unsafe_allow_html=True)


def clickable_metric(label, value, color, key):
    with st.form(key=key):
        st.markdown(f"""
            <div style='
                background-color: {color};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 1px 1px 5px rgba(0,0,0,0.2);
                cursor: pointer;
            '>
                <div style="font-size: 18px; color: black;">{label}</div>
                <div style="font-size: 24px; font-weight: bold; color: black;">{value}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Invisible submit button to capture the click
        if st.form_submit_button(label="View list", use_container_width=True):
            st.session_state.selected_metric = key


#######################
# Load data
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')


#######################
# Sidebar
with st.sidebar:
    st.title('Custom Options')
    
    cons_ref = ['Consumption/Demand', 'Only Consumption']
    selected_cons_ref = st.selectbox('Select Reference Quantity', cons_ref)

    options_list = ['All Drugs', 'Priority Drugs']
    selected_category = st.selectbox('Option to select', options_list)


#######################
# Dashboard Main Panel 

st.markdown("<h1 style='font-size: 42px;'>Dashboard for Drugs</h1>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('### Stock Position of Drugs')

# Layout of metric blocks
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    clickable_metric("Total Drugs", str(total_drugs), "#E5E4E2", "t_all")  # Light blue
with col2:
    clickable_metric("> 3 months", "85", "#90EE90", "t_above_3")  # Light green
with col3:
    clickable_metric("1-3 Months", "42", "#FFFACD", "t_mid_1_3")    # Light yellow
with col4:
    clickable_metric("< 1 Month", "18", "#FFFACD", "t_below_1")     # Light yellow
with col5:
    clickable_metric("Zero Stock", "29", "#FF7F7F", "t_zero")  # Light red

if st.session_state.selected_metric != "None":

    base_query = '''SELECT 
                ROW_NUMBER() OVER () as "S No.", 
                item_code as "Item Code", 
                item_name as "Item Name", 
                eml_aml_type as "EML/AML", 
                priority_item as "Priority Status", 
                stock_quantity as "Stock Qty",
                stock_quantity as "Pending Supply"
                
                FROM stock_data 
                WHERE warehouse_name='Grand Total'
                '''
    condition = ""

    # Based on click, show table
    #st.write(f"### Selected Metric: {st.session_state.selected_metric}")
    if st.session_state.selected_metric == "t_all":
        st.write("Showing all drugs")
        #No condition needed

    elif st.session_state.selected_metric == "t_above_3":
        st.write("Showing drugs with stock > 3 months")
        condition = "AND stock_quantity > 180"

    elif st.session_state.selected_metric == "t_mid_1_3":
        st.write("Showing drugs with stock of 1-3 months")
        condition = "AND stock_quantity > 180"

    elif st.session_state.selected_metric == "t_below_1":
        st.write("Showing drugs with stock < 1 month")
        condition = "AND stock_quantity > 180"

    elif st.session_state.selected_metric == "t_zero":
        st.write("Showing drugs with zero stock")
        condition = "AND stock_quantity > 180"

    else:
        st.write("")

    # Final query
    final_query = f"{base_query} {condition};"

    # Fetch and display
    data = run_query(final_query)
    if not data.empty:
        df = pd.DataFrame(data, columns=[
            "S No.", "Item Code", "Item Name",
            "EML/AML", "Priority Status", "Stock Qty", "Pending Supply"
        ])

        # Apply formatting to the "Stock Qty" column
        df["Stock Qty"] = df["Stock Qty"].apply(format_indian_number)

        st.dataframe(df, hide_index=True)
    else:
        st.warning("No records found.")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('### Insights')

# Your insight content as a list
st.markdown('''
- **Drugs with low stock and RC available (POs to be issued):** 55  

- **Gains/Losses:** States with high inbound/outbound migration for selected year  

- **States Migration:** % of states with annual inbound/outbound migration > 50,000  
''')






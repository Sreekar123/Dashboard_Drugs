#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px


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
    html_str = f"""
    <form action="/?metric={key}" method="get">
        <button type="submit"
        style="
            background-color: {color};
            border: none;
            color: black;
            padding: 15px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 18px;
            width: 100%;
            border-radius: 10px;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.2);
            cursor: pointer;
        ">
            <div>{label}</div>
            <div style="font-size: 24px; font-weight: bold;">{value}</div>
        </button>
    </form>
    """
    st.markdown(html_str, unsafe_allow_html=True)







#######################
# Load data
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')


#######################
# Sidebar
with st.sidebar:
    st.title('Dashboard for Drugs')
    
    year_list = list(df_reshaped.year.unique())[::-1]
    
    selected_year = st.selectbox('Select a year', year_list)
    df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

    options_list = ['All Drugs', 'Priority Drugs']
    selected_category = st.selectbox('Option to select', options_list)


#######################
# Dashboard Main Panel (Updated to 3 Rows)

st.markdown('### Stock Position of Drugs')

# Layout of metric blocks
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    clickable_metric(">3 Months", "120", "#ADD8E6", "t_above_3")  # Light blue
with col2:
    clickable_metric("1-3 Months", "85", "#90EE90", "t_mid_1_3")  # Light green
with col3:
    clickable_metric("<1 Month", "42", "#FFFACD", "t_below_1")    # Light yellow
with col4:
    clickable_metric("Zero Stock", "18", "#FFFACD", "t_zero")     # Light yellow
with col5:
    clickable_metric("Pending Supply", "29", "#FF7F7F", "t_pending")  # Light red

# Based on click, show table
st.write(f"### Selected Metric: {st.session_state.selected_metric}")
if st.session_state.selected_metric == "t_above_3":
    st.write("Showing drugs with stock > 3 months")
    # st.dataframe(table_1)
elif st.session_state.selected_metric == "t_below_1":
    st.write("Showing drugs with stock < 1 month")
    # st.dataframe(table_2)
else:
    st.write("Select a metric to show table")

st.markdown("<br>", unsafe_allow_html=True)

# Visualizations Row (Row 2)
st.markdown("### Showing ____ drugs")

# Use st.dataframe for scrollable table with smaller size
st.dataframe(
    df_dummy,
    use_container_width=True,
    hide_index=True,
    height=230  # adjust height to your layout
)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('### Insights')

# Your insight content as a list
st.markdown('''
- **Drugs with low stock and RC available (POs to be issued):** 55  
- **Gains/Losses:** States with high inbound/outbound migration for selected year  
- **States Migration:** % of states with annual inbound/outbound migration > 50,000  
''')   

# Table + About (Row 3)
with st.expander('POs to be issued', expanded=True):
    st.write('''
        - :orange[**Drugs with low stock and RC available (POs to be issued):**  ][55](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
        - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
        - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
    ''')

with st.expander('Tenders to be processed', expanded=True):
    st.write('''
        - :orange[**Drugs with low stock and RC available (POs to be issued):**  ][55](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
        - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
        - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
    ''')

selected = st.session_state.selected_metric

if selected == "None":
    st.write("Showing drugs with stock > 3 months")
    st.dataframe(table_1)

if selected == "above_2":
    st.write("Showing drugs with stock > 3 months")
    st.dataframe(table_1)

elif selected == "below_1":
    st.write("Showing drugs with stock < 1 month")
    st.dataframe(table_2)




col1, col2, col3 = st.columns(3)

with col1:
    if st.button('>3 Months', key="above_3"):
        st.session_state.selected_metric = "above_3"

    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #ADD8E6;
        color: black;
        font-size: 20px;
        width: 100%;
        height: 80px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style="background-color:#ADD8E6; padding:15px; border-radius:10px; text-align:center">
            <div style="font-size:16px;">>3 Months</div>
            <div style="font-size:24px; font-weight:bold;">120</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button(" ", key="above_2"):
        st.session_state.selected_metric = "above_2"

with col3:
    st.markdown("""
        <div style="background-color:#ADD8E6; padding:15px; border-radius:10px; text-align:center">
            <div style="font-size:16px;">>3 Months</div>
            <div style="font-size:24px; font-weight:bold;">120</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button(" ", key="above_1"):
        st.session_state.selected_metric = "above_3"




# Metrics Row (Row 1)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    clickable_metric(">3 Months", "120", "#ADD8E6", "above_2")  # Light blue

with col2:
    clickable_metric("1-3 Months", "85", "#90EE90", "mid_1_3")  # Light green

with col3:
    clickable_metric("<1 Month", "42", "#FFFACD", "below_1")    # Light yellow

with col4:
    clickable_metric("Zero Stock", "18", "#FFFACD", "zero")     # Light yellow

with col5:
    clickable_metric("Pending Supply", "29", "#FF7F7F", "pending")  # Light red
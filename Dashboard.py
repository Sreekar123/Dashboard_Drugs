#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import io

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Establishing database connection
from db_connection_updated import fetch_one
from db_connection_updated import run_query


#######################

# Initialize session state
if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = "None"

def format_indian_number(number):
    """Format number with commas as per Indian numbering system"""
    if number is None or pd.isna(number):
        return "0"

    try:
        s = str(int(number))
    except (ValueError, TypeError):
        return "0"

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


def format_date_dd_mmm_yyyy(date_value):
    """Format a datetime object or string to 'dd-MMM-yyyy' format."""
    try:
        date_obj = pd.to_datetime(date_value)
        return date_obj.strftime("%d-%b-%Y")
    except:
        return ""

def highlight_pending(val):
    try:
        val = float(val)
        if val > 10:
            return 'background-color: tomato; color: white; font-weight: bold'
        elif val > 0:
            return 'background-color: lightyellow; font-weight: bold'
        else:
            return ''
    except:
        return ''

def highlight_low_supply(row):
    try:
        if float(row["Supply %"]) < 90:
            return ['color: red'] * len(row)  # Red text, normal background
    except:
        pass
    return [''] * len(row)

def get_metrics():
    base_query = """
        SELECT 
            item_code, 
            stock_pos_cons, 
            stock_pos_con_dem, 
            (SELECT priority_item FROM item_master WHERE item_code = stock_data.item_code) AS priority_item,
            warehouse_name,
            stock_quantity
        FROM stock_data
        WHERE 1=1
    """
    conditions = []

    # Apply drug type filter
    if selected_category == "Priority Drugs":
        conditions.append("item_code IN (SELECT item_code FROM item_master WHERE priority_item = 'Yes')")

    # Apply warehouse filter
    if selected_cms != "State Total":
        conditions.append(f"warehouse_name = '{selected_cms}'")
    else:
        conditions.append("warehouse_name = 'State Total'")

    # Choose the appropriate stock column
    if selected_cons_ref == "Only Consumption":
        stock_col = "stock_pos_cons"
    else:
        stock_col = "stock_pos_con_dem"

    # Final query
    final_query = f"{base_query} AND {' AND '.join(conditions)};"
    data = run_query(final_query)

    # Build DataFrame
    df = pd.DataFrame(data, columns=[
        "item_code", "stock_pos_cons", "stock_pos_con_dem", "priority_item", "warehouse_name", "stock_quantity"
    ])
    if df.empty:
        return 0, 0, 0, 0, 0

    # Choose relevant stock position column
    df["stock_pos"] = df[stock_col].fillna(0)
    df["stock_quantity"] = df["stock_quantity"].fillna(0)

    # Metrics
    total = df["item_code"].nunique()
    above_3 = df[df["stock_pos"] > 3].shape[0]
    mid_1_3 = df[(df["stock_pos"] > 1) & (df["stock_pos"] <= 3)].shape[0]
    below_1 = df[(df["stock_pos"] <= 1) & (df["stock_pos"] > 0)].shape[0]

    # Only consider as zero if both stock_pos = 0 AND stock_quantity = 0
    zero = df[(df["stock_pos"] == 0) & (df["stock_quantity"] == 0)].shape[0]

    # Adjust below_1 to include those with stock_pos = 0 but stock_quantity > 0
    below_1 += df[(df["stock_pos"] == 0) & (df["stock_quantity"] > 0)].shape[0]

    return total, above_3, mid_1_3, below_1, zero


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
# Sidebar
with st.sidebar:
    st.title('Custom Options')
    
    cons_ref = ['Consumption/Demand', 'Only Consumption']
    selected_cons_ref = st.selectbox('Select Reference Quantity', cons_ref)

    options_list = ['All Drugs', 'Priority Drugs']
    selected_category = st.selectbox('Select Drugs', options_list)  

    cms_query = "SELECT DISTINCT warehouse_name FROM stock_data ORDER BY warehouse_name"
    cms_result = run_query(cms_query)  # assuming run_query returns a list of tuples or a DataFrame
    cms_list = cms_result['warehouse_name'].tolist()
    cms_list.insert(0, "State Total")  # Add manually to top
    selected_cms = st.selectbox('Select CMS', cms_list)


#######################
# Dashboard Main Panel 

st.markdown("<h1 style='font-size: 42px;'>Dashboard for Drugs</h1>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown('### Stock Position of Drugs')

# Layout of metric blocks
total_drugs, above_3, mid_1_3, below_1, zero = get_metrics()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    clickable_metric("Total Drugs", str(total_drugs), "#E5E4E2", "t_all")

with col2:
    clickable_metric("> 3 months", str(above_3), "#90EE90", "t_above_3")

with col3:
    clickable_metric("1-3 Months", str(mid_1_3), "#FFFACD", "t_mid_1_3")

with col4:
    clickable_metric("< 1 Month", str(below_1), "#FFFACD", "t_below_1")

with col5:
    clickable_metric("Zero Stock", str(zero), "#FF7F7F", "t_zero")

if st.session_state.selected_metric != "None":

    # Decide which stock position to use
    stock_pos_col = "stock_pos_cons" if selected_cons_ref == "Only Consumption" else "stock_pos_con_dem"

    # Base query with subqueries
    base_query = f'''
        SELECT 
            ROW_NUMBER() OVER () as "S No.", 
            a.item_code as "Item Code", 
            (SELECT item_name FROM item_master WHERE item_code = a.item_code) as "Item Name", 
            (SELECT eml_aml_type FROM item_master WHERE item_code = a.item_code) as "EML/AML", 
            (SELECT priority_item FROM item_master WHERE item_code = a.item_code) as "Priority Status",
            (SELECT type_cons_dem FROM item_master WHERE item_code = a.item_code) as "Cons/Dem Type",
            SUM(COALESCE(stock_quantity, 0)) as "Stock Qty",
            ROUND(AVG(COALESCE(a.{stock_pos_col}, 0)), 2) as "Stock Position",
            (SELECT (SUM(COALESCE(po_qty,0)) - SUM(COALESCE(received_qty,0))) 
             FROM purchase_order_data 
             WHERE item_code = a.item_code) as "Pending Supply"
        FROM stock_data a
        WHERE 1=1
    '''

    # Filters
    filters = []

    if selected_category == "Priority Drugs":
        filters.append("a.item_code IN (SELECT item_code FROM item_master WHERE priority_item = 'Yes')")

    if selected_cms != "State Total":
        filters.append(f"a.warehouse_name = '{selected_cms}'")
    else:
        filters.append("a.warehouse_name = 'State Total'")

    # Metric filter logic (based on stock position)
    if st.session_state.selected_metric == "t_above_3":
        st.write("**Showing drugs with stock > 3 months**")
        filters.append(f"COALESCE({stock_pos_col}, 0) > 3")
    elif st.session_state.selected_metric == "t_mid_1_3":
        st.write("**Showing drugs with stock between 1 and 3 months**")
        filters.append(f"COALESCE({stock_pos_col}, 0) > 1 AND COALESCE({stock_pos_col}, 0) <= 3")
    elif st.session_state.selected_metric == "t_below_1":
        st.write("**Showing drugs with stock < 1 month**")
        filters.append(f"(({stock_pos_col} > 0 AND {stock_pos_col} <= 1) OR ((COALESCE(stock_quantity, 0)) > 0 AND COALESCE({stock_pos_col}, 0) = 0))")
    elif st.session_state.selected_metric == "t_zero":
        st.write("**Showing drugs with zero stock position**")
        filters.append("(COALESCE(stock_quantity, 0)) = 0")
    else:
        st.write("**Showing all drugs**")

    # Combine the filters
    if filters:
        base_query += " AND " + " AND ".join(filters)

    # Grouping
    base_query += " GROUP BY a.item_code"

    # Final query
    final_query = base_query + ";"

    # Fetch data
    data = run_query(final_query)

    # Display table
    if not data.empty:
        df = pd.DataFrame(data, columns=[
            "S No.", "Item Code", "Item Name", "EML/AML", "Priority Status",
            "Cons/Dem Type", "Stock Qty", "Stock Position", "Pending Supply"
        ])

        # Format number columns (keep numeric types for AgGrid)
        df["Stock Qty"] = pd.to_numeric(df["Stock Qty"], errors="coerce").fillna(0)
        df["Stock Position"] = pd.to_numeric(df["Stock Position"], errors="coerce").fillna(0)
        df["Pending Supply"] = pd.to_numeric(df["Pending Supply"], errors="coerce").fillna(0)

        # Build AgGrid config
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(sortable=True, resizable=True, filter=False, wrapHeaderText=True, autoHeaderHeight=True)
        gb.configure_column("Item Code", filter=True)
        gb.configure_column("S No.", width = 100, filter=False)
        gb.configure_column("Item Name", filter=True, width = 500)
        gb.configure_column("Stock Qty", type=["numericColumn", "customNumericFormat"], precision=0)
        gb.configure_column("Pending Supply", type=["numericColumn", "customNumericFormat"], precision=0)
        gb.configure_column("Stock Position", type=["numericColumn", "customNumericFormat"], precision=2)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        gb.configure_grid_options(floatingFilter=False)
        grid_options = gb.build()

        # Render table
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            height=350,
            width='100%',
            enable_enterprise_modules=False,
            fit_columns_on_grid_load=True
        )

        # Download Table Button
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        col1, col2 = st.columns([4,1])

        with col2:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name="filtered_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    else:
        st.warning("No records found for the selected filters.")


    # Access selected row (if needed)
    selected = grid_response['selected_rows']

    if selected is not None and len(selected) > 0:
        selected_row = selected.iloc[0]
        item_code = selected_row["Item Code"]
        item_name = selected_row["Item Name"]
        
        st.markdown(f"**Showing PO Details for: {item_name}**")

        # Sample query or logic
        detail_query = f"""
        SELECT 
        po_number as "PO No.",
        po_date as "PO Date",
        supplier as "Supplier Name",
        po_qty as "PO Qty",
        received_qty as "Received Qty",
        supply_status as "Supply %",
        (po_qty - received_qty) as "Pending Qty",
        scheduled_delivery_date as "Scheduled Delivery Date"                
        FROM purchase_order_data 
        WHERE item_code = '{item_code}'
        ORDER BY po_date DESC
        """
        po_data = run_query(detail_query)

        # df["PO Date"] = pd.to_datetime(df["PO Date"]).dt.strftime("%d-%b-%Y")

        if not po_data.empty:
            po_df = pd.DataFrame(po_data, columns=[
                "PO No.","PO Date", "Supplier Name",
                "PO Qty", "Received Qty", "Supply %", "Pending Qty", "Scheduled Delivery Date"
            ])

            # Format Dates
            for col in ["PO Date", "Scheduled Delivery Date"]:
                po_df[col] = po_df[col].apply(format_date_dd_mmm_yyyy)

            for col in ["PO Qty", "Received Qty", "Pending Qty"]:
                po_df[col] = po_df[col].apply(format_indian_number)

            po_df["Supply %"] = po_df["Supply %"].apply(lambda x: f"{int(round(x))}%" if pd.notnull(x) else "0%")

            styled_df = po_df.style.apply(highlight_low_supply, axis=1)

            st.dataframe(styled_df, hide_index=True)
        else:
            st.info("No purchase orders found for this item.")

st.markdown("<br>", unsafe_allow_html=True)




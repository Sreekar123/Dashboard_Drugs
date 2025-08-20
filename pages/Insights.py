import streamlit as st
import pandas as pd
import io

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from db_connection_updated import run_query  # Assuming you have a db helper
from streamlit_extras.stylable_container import stylable_container


# Define your button styles once for all colors
button_styles = {
    "yellow": """
        button {
            background-color: #FFFACD !important;
            color: #b59b00 !important;
            font-weight: bold;
            margin-bottom: 1rem;   /* or adjust as needed */
        }
    """,
    "lightred": """
        button {
            background-color: #FFD6D6 !important;
            color: #b71c1c !important;
            font-weight: bold;
            margin-bottom: 1rem;   /* or adjust as needed */
        }
    """,
    "darkred": """
        button {
            background-color: #FF4C4C !important;
            color: white !important;
            font-weight: bold;
            margin-bottom: 1rem;   /* or adjust as needed */
        }
    """
}



# Page Setup
st.set_page_config(
    page_title="Insights",
    # page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

# Page header
st.markdown("<h1 style='font-size: 42px;'>🔍 Insights</h1>", unsafe_allow_html=True)
st.markdown("---")

# Functions


#  Queries for Total Items

# RC Avl Count
query_count_rc_avl = """
SELECT COUNT(DISTINCT rcd.item_code)
FROM rate_contract_data rcd
JOIN item_master im ON rcd.item_code = im.item_code
WHERE im.priority_item in ('Yes','No')
"""
df = run_query(query_count_rc_avl)
count_rc_avl = df.iloc[0, 0] if not df.empty else 0

# RC Not Avl Count
count_rc_notavl = (522 - count_rc_avl) 

# RC expiring in 3 months count
query_count_rc_3m = """
select count(distinct item_code) from rate_contract_data 
where contract_to_date <= current_date + 90
and item_code in (select item_code from item_master)
"""

df = run_query(query_count_rc_3m)
count_rc_3m = df.iloc[0, 0] if not df.empty else 0

#  Queries for Priority Items

# RC Avl Count
query_count_rc_avl_p = """
SELECT COUNT(DISTINCT rcd.item_code)
FROM rate_contract_data rcd
JOIN item_master im ON rcd.item_code = im.item_code
WHERE im.priority_item = 'Yes' """
df = run_query(query_count_rc_avl_p)
count_rc_avl_p = df.iloc[0, 0] if not df.empty else 0

# RC Not Avl Count
count_rc_notavl_p = (100 - count_rc_avl_p) 

# RC expiring in 3 months count
query_count_rc_3m_p = """
SELECT COUNT(DISTINCT rcd.item_code)
FROM rate_contract_data rcd
JOIN item_master im ON rcd.item_code = im.item_code
WHERE im.priority_item = 'Yes'
and rcd.contract_to_date <= current_date + 90
"""

df = run_query(query_count_rc_3m_p)
count_rc_3m_p = df.iloc[0, 0] if not df.empty else 0


# --- Data Queries ---
query_total = """
SELECT 
    im.item_code AS "Item Code",
    im.item_name AS "Item Name",
    rc.supplier AS "Supplier",
    rc.rate AS "Rate",
    rc.rate_unit AS "Rate Unit",
    rc.tender_date AS "Tender Date",
    rc.contract_from_date AS "Contract From Date",
    rc.contract_to_date AS "Contract To Date",
    rc.rate_contract_level AS "RC Level"
FROM item_master im
LEFT JOIN rate_contract_data rc ON rc.item_code = im.item_code
ORDER BY im.item_code;
"""

query_available = """
SELECT 
    im.item_code AS "Item Code",
    im.item_name AS "Item Name",
    rc.supplier AS "Supplier",
    rc.rate AS "Rate",
    rc.rate_unit AS "Rate Unit",
    rc.tender_date AS "Tender Date",
    rc.contract_from_date AS "Contract From Date",
    rc.contract_to_date AS "Contract To Date",
    rc.rate_contract_level AS "RC Level"
FROM item_master im
JOIN rate_contract_data rc ON rc.item_code = im.item_code
ORDER BY im.item_code;
"""

query_not_available = """
SELECT 
    im.item_code AS "Item Code",
    im.item_name AS "Item Name"
FROM item_master im
WHERE NOT EXISTS (
    SELECT 1 FROM rate_contract_data rc
    WHERE rc.item_code = im.item_code
)
ORDER BY im.item_code;
"""

query_expiring = """
SELECT 
    im.item_code AS "Item Code",
    im.item_name AS "Item Name",
    rc.supplier AS "Supplier",
    rc.rate AS "Rate",
    rc.rate_unit AS "Rate Unit",
    rc.tender_date AS "Tender Date",
    rc.contract_from_date AS "Contract From Date",
    rc.contract_to_date AS "Contract To Date",
    rc.rate_contract_level AS "RC Level"
FROM item_master im
JOIN rate_contract_data rc ON rc.item_code = im.item_code
WHERE rc.contract_to_date <= CURRENT_DATE + INTERVAL '3 months'
ORDER BY rc.contract_to_date;
"""


# Section 1: RCs expiring in 3 months
st.markdown("### 📆 Summary of Rate Contracts")

st.markdown("<br>", unsafe_allow_html=True)
    
# Initialize session state for displaying details
if 'selected_metric' not in st.session_state:
    st.session_state.selected_metric = None

col1, col2, col3 = st.columns([6, 2, 2])

with col1:
    st.markdown("<span style='color:white;'>--</span>", unsafe_allow_html=True)
    if st.button("**Total Items**", key="none1", use_container_width=True):
            st.session_state.selected_metric = key
    if st.button("**Items with RC Available**", key="none2", use_container_width=True):
        st.session_state.selected_metric = key
    if st.button("**Items with RC Not Available**", key="none3", use_container_width=True):
        st.session_state.selected_metric = key
    if st.button("**Items for which RC expiring in 3 months**", key="none4", use_container_width=True):
        st.session_state.selected_metric = key

with col2:
    left, center, right = st.columns([1,3,1])
    with center:
        st.markdown("**All Items**")
    if st.button("522", key="total", use_container_width=True):
        st.session_state.selected_metric = "total"
    if st.button(str(count_rc_avl), key="avl", use_container_width=True):
        st.session_state.selected_metric = "avl"
    with stylable_container("darkred1", css_styles=button_styles["darkred"]):
        if st.button(str(count_rc_notavl), key="not_avl", use_container_width=True):
            st.session_state.selected_metric = "not_avl"
    with stylable_container("lightred1", css_styles=button_styles["lightred"]):
        if st.button(str(count_rc_3m), key="exp_3m", use_container_width=True):
            st.session_state.selected_metric = "exp_3m"

with col3:
    st.markdown("  **Priority Items**")
    if st.button("100", key="total_p", use_container_width=True):
        st.session_state.selected_metric = "total_p"
    if st.button(str(count_rc_avl_p), key="avl_p", use_container_width=True):
        st.session_state.selected_metric = "avl_p"
    with stylable_container("darkred2", css_styles=button_styles["darkred"]):
        if st.button(str(count_rc_notavl_p), key="not_avl_p", use_container_width=True):
            st.session_state.selected_metric = "not_avl_p"
    with stylable_container("lightred2", css_styles=button_styles["lightred"]):
        if st.button(str(count_rc_3m_p), key="exp_3m_p", use_container_width=True):
            st.session_state.selected_metric = "exp_3m_p"

    priority_condition = ""
    if st.session_state.selected_metric in ("exp_3m_p", "not_avl_p"):
        priority_condition = "AND im.priority_item = 'Yes'"

if st.session_state.selected_metric in ("exp_3m_p", "exp_3m"):

    # SQL Query with dynamic filter
    rc_query = f"""
    WITH rc_data AS (
        SELECT 
            rc.item_code,
            rc.supplier,
            rc.rate,
            rc.rate_unit,
            rc.contract_from_date,
            rc.contract_to_date,
            (rc.contract_to_date - CURRENT_DATE) AS days_till_expiry
        FROM rate_contract_data rc
        WHERE rc.contract_to_date IS NOT NULL
        AND rc.contract_to_date <= (CURRENT_DATE + INTERVAL '3 months')
    ),
    state_stock AS (
        SELECT 
            sd.item_code,
            COALESCE(SUM(sd.stock_quantity),0) AS state_stock_qty,
            COALESCE(SUM(sd.stock_pos_con_dem),0) AS stock_pos_con_dem
        FROM stock_data sd
        WHERE sd.warehouse_name = 'State Total'
        GROUP BY sd.item_code
    ),
    pending_po AS (
        SELECT 
            pod.item_code,
            (SUM(COALESCE(pod.po_qty,0)) - SUM(COALESCE(pod.received_qty,0))) AS pending_supply
        FROM purchase_order_data pod
        GROUP BY pod.item_code
    ),
    unique_items AS (
    SELECT 
        im.item_code,
        ROW_NUMBER() OVER (ORDER BY im.item_code) AS serial_no
    FROM item_master im
    INNER JOIN rc_data rc ON rc.item_code = im.item_code
    WHERE 1=1 {priority_condition}
    GROUP BY im.item_code
    )

    SELECT 
        ui.serial_no AS "S No.",
        rc.item_code AS "Item Code",
        im.item_name AS "Item Name",
        rc.supplier AS "Supplier Name",
        --rc.rate AS "Rate",
        --rc.rate_unit AS "Rate Unit",
        TO_CHAR(rc.contract_from_date,'DD-Mon-YY') AS "Contract Start Date",
        TO_CHAR(rc.contract_to_date,'DD-Mon-YY') AS "Contract End Date",
        rc.days_till_expiry AS "Days till Contract End",
        ss.stock_pos_con_dem AS "Stock Position (Months)",
        COALESCE(po.pending_supply,0) AS "Pending Supply (State Total)"
    FROM rc_data rc
    LEFT JOIN state_stock ss ON ss.item_code = rc.item_code
    LEFT JOIN pending_po po ON po.item_code = rc.item_code
    INNER JOIN item_master im ON im.item_code = rc.item_code
    INNER JOIN unique_items ui ON ui.item_code = rc.item_code
    WHERE 1=1
    {priority_condition}
    ORDER BY im.item_code, rc.contract_to_date;
    """

    df = run_query(rc_query)

    df['S No.'] = df['S No.'].where(~df['Item Code'].duplicated())

    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        addnl_text ="All Items" 
        if st.session_state.selected_metric == "exp_3m_p":
            addnl_text =  "Priority Items"

        st.markdown(f"#### Rate Contracts expiring within 3 months - {addnl_text}")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, filter=False, sortable=True, cellStyle={"textAlign": "center"}, wrapHeaderText=True, autoHeaderHeight=True)
        gb.configure_column("S No.", filter=False, width=100)
        gb.configure_column("Item Code", filter=False, width=150)
        gb.configure_column("Item Name", filter=False, width=600, cellStyle={"textAlign": "left"})
        gb.configure_column("Supplier Name", filter=False, width=400, cellStyle={"textAlign": "left"})
        gb.configure_column("Days till Contract End", filter=False)
        #gb.configure_column("Rate", type=["numericColumn"], valueFormatter="x.toLocaleString()")
        gb.configure_column("Stock Position (Months)", type=["numericColumn"], valueFormatter="x.toLocaleString()")
        gb.configure_column("Pending Supply (State Total)", type=["numericColumn"], valueFormatter="x.toLocaleString()")
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options, fit_columns_on_grid_load=True, theme="streamlit", height=450, width=800)

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
                    file_name="list.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("No expiring rate contracts found for the selected filters.")


if st.session_state.selected_metric in ("not_avl_p", "not_avl"):

    # SQL Query with dynamic filter
    rc_query = f"""
        WITH rc_items AS (
            SELECT DISTINCT item_code
            FROM rate_contract_data
        ),
        no_rc_items AS (
            SELECT item_code
            FROM item_master im
            WHERE item_code NOT IN (SELECT item_code FROM rc_items)
            {priority_condition}
        ),
        state_stock AS (
            SELECT 
                sd.item_code,
                COALESCE(SUM(sd.stock_quantity),0) AS stock_quantity,
                COALESCE(SUM(sd.stock_pos_con_dem),0) AS stock_pos_con_dem
            FROM stock_data sd
            WHERE sd.warehouse_name = 'State Total'
            GROUP BY sd.item_code
        ),
        pending_po AS (
            SELECT 
                pod.item_code,
                (SUM(COALESCE(pod.po_qty,0)) - SUM(COALESCE(pod.received_qty,0))) AS pending_supply
            FROM purchase_order_data pod
            GROUP BY pod.item_code
        ),
        serials AS (
            SELECT 
                nri.item_code,
                ROW_NUMBER() OVER (ORDER BY COALESCE(ss.stock_pos_con_dem, 0) ASC) AS serial_no
            FROM no_rc_items nri
            LEFT JOIN state_stock ss ON ss.item_code = nri.item_code
        )

        SELECT
            s.serial_no AS "S No.",
            im.item_code AS "Item Code",
            im.item_name AS "Item Name",
    		COALESCE(ss.stock_quantity,0) AS "Stock Quantity",
            COALESCE(ss.stock_pos_con_dem,0) AS "Stock Position (Months)",
            COALESCE(po.pending_supply,0) AS "Pending Supply (State Total)"
        FROM no_rc_items nri
        INNER JOIN item_master im ON im.item_code = nri.item_code
        LEFT JOIN state_stock ss ON ss.item_code = nri.item_code
        LEFT JOIN pending_po po ON po.item_code = nri.item_code
        INNER JOIN serials s ON s.item_code = nri.item_code
        ORDER BY "S No." ASC;
    
    """

    df = run_query(rc_query)

    df['S No.'] = df['S No.'].where(~df['Item Code'].duplicated())

    if not df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        addnl_text ="All" 
        if st.session_state.selected_metric == "not_avl_p":
            addnl_text =  "Priority"

        st.markdown(f"#### {addnl_text} Items with no active Rate Contract")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, filter=False, sortable=True, cellStyle={"textAlign": "center"}, wrapHeaderText=True, autoHeaderHeight=True)
        gb.configure_column("S No.", filter=False, width=100)
        gb.configure_column("Item Code", filter=False, width=150)
        gb.configure_column("Item Name", filter=False, width=600, cellStyle={"textAlign": "left"})
        gb.configure_column("Stock Position (Months)", type=["numericColumn"], valueFormatter="x.toLocaleString()")
        gb.configure_column("Pending Supply (State Total)", type=["numericColumn"], valueFormatter="x.toLocaleString()")
        gb.configure_column("Stock Quantity", type=["numericColumn"], valueFormatter="x.toLocaleString()", filter=False)
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options, fit_columns_on_grid_load=True, theme="streamlit", height=450, width=800)

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
                    file_name="list.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("All items have active rate contracts.")



st.markdown("---")

# Section 2: Low stock, RC available, but no pending supply

query = """
WITH rc_items AS (
    SELECT DISTINCT rc.item_code
    FROM rate_contract_data rc
),
state_stock AS (
    SELECT
        sd.item_code,
        COALESCE(SUM(sd.stock_pos_con_dem), 0) AS stock_pos_con_dem,
        COALESCE(SUM(sd.stock_quantity), 0) AS stock_qty
    FROM stock_data sd
    WHERE sd.warehouse_name = 'State Total'
    GROUP BY sd.item_code
),
pending_po AS (
    SELECT
        pod.item_code,
        (SUM(COALESCE(pod.po_qty,0)) - SUM(COALESCE(pod.received_qty,0))) AS pending_supply
    FROM purchase_order_data pod
    GROUP BY pod.item_code
)
SELECT
    ROW_NUMBER() OVER (ORDER BY im.priority_item DESC, ss.stock_pos_con_dem) AS "S No.",
    im.item_code AS "Item Code",
    im.item_name AS "Item Name",
    im.priority_item AS "Priority Status",
    ss.stock_qty AS "Stock Qty (State Total)",
    ss.stock_pos_con_dem AS "Stock Position (Months)",
    COALESCE(po.pending_supply,0) AS "Pending Supply (State Total)"
FROM item_master im
INNER JOIN state_stock ss ON ss.item_code = im.item_code
INNER JOIN rc_items rc ON rc.item_code = im.item_code
LEFT JOIN pending_po po ON po.item_code = im.item_code
WHERE
    ss.stock_pos_con_dem < 1
    AND (COALESCE(po.pending_supply, 0) = 0)
ORDER BY im.priority_item DESC, ss.stock_pos_con_dem;
"""

df = run_query(query)

count = len(df)

st.markdown(f"### ⚠️ Low stock, RC available, but no pending supply: {count}")

if st.button("Show List", key="low_stock"):

    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, filter=False, sortable=True, cellStyle={"textAlign": "center"}, wrapHeaderText=True, autoHeaderHeight=True)
        gb.configure_column("S No.", filter=False, width=100)
        gb.configure_column("Item Code", filter=False, width=150)
        gb.configure_column("Item Name", filter=False, width=600, cellStyle={"textAlign": "left"})
        gb.configure_column("Stock Qty (State Total)", type=["numericColumn"], valueFormatter="x.toLocaleString()", cellStyle={"textAlign": "right"})
        gb.configure_column("Stock Position (Months)", filter=False)
        gb.configure_column("Pending Supply (State Total)", type=["numericColumn"], valueFormatter="x.toLocaleString()")

        grid_options = gb.build()

        AgGrid(df, gridOptions=grid_options, fit_columns_on_grid_load=True, theme="streamlit", height=450, width=800)

        # Download Table Button
        # Convert to CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        col1, col2 = st.columns([4,1])

        with col2:
                st.download_button(
                    label="⬇️ Download Table",
                    data=csv_data,
                    file_name="list.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("No items found that match: low stock, RC available, and no pending supply.")



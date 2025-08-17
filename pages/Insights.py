import streamlit as st
import pandas as pd
from db_connection_updated import run_query  # Assuming you have a db helper

# Page header
st.markdown("# 🔍 Insights")
st.markdown("---")

# Functions
def clickable_text(label, key):
    link = f'<a href="?{key}=1" target="_self" style="text-decoration:underline; font-weight:bold; color:blue;">{label}</a>'
    st.markdown(link, unsafe_allow_html=True)

# Queries

# RC Avl Count
query_count_rc_avl = """
select count(distinct item_code) from rate_contract_data
"""
df = run_query(query_count_rc_avl)
count_rc_avl = df.iloc[0, 0] if not df.empty else 0

# RC Not Avl Count
count_rc_notavl = (522 - count_rc_avl) 

# RC expiring in 3 months count
query_count_rc_3m = """
select count(distinct item_code) from rate_contract_data 
where contract_to_date <= current_date + 90
"""

df = run_query(query_count_rc_3m)
count_rc_3m = df.iloc[0, 0] if not df.empty else 0

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
    

#st.markdown("**Total Items:** 522")
#st.markdown(f"**RC Available:** {count_rc_avl}")
#st.markdown(f"**RC Not Available: {count_rc_notavl}**")
#st.markdown(f"**RC expiring in 3 months (Unique Items): {count_rc_3m}**")

col1, col2, col3, col4 = st.columns([5, 1, 2, 2])

with col1:
    st.markdown("--")
    st.markdown("Total Items")
    st.markdown("Items with RC Available")
    st.markdown("Items with RC Not Available")
    st.markdown("Items for which RC expiring in 3 months")

with col2:
    st.markdown("--")
    st.markdown("**:**")
    st.markdown("**:**")
    st.markdown("**:**")
    st.markdown("**:**")

with col3:
    st.markdown("**All Items**")
    clickable_text("522", "total")
    clickable_text(str(count_rc_avl), "available")
    clickable_text(str(count_rc_notavl), "not_available")
    clickable_text(str(count_rc_3m), "expiring")

with col4:
    st.markdown("**Priority Items**")
    clickable_text("100", "total")
    clickable_text(str(count_rc_avl), "available_p")
    clickable_text(str(count_rc_notavl), "not_available_p")
    clickable_text(str(count_rc_3m), "expiring_p")


# Query example for RCs expiring in 3 months (customize as needed)
query_rc_expiry = """
SELECT 
    item_code AS "Item Code",
    supplier AS "Supplier",
    po_number AS "PO No.",
    scheduled_delivery_date AS "Scheduled Delivery Date"
FROM purchase_order_data
WHERE scheduled_delivery_date <= CURRENT_DATE + INTERVAL '3 months'
ORDER BY scheduled_delivery_date ASC
"""


st.markdown("---")

# Section 2: Low stock, RC available, but no pending supply
st.markdown("### ⚠️ Low stock, RC available, but no pending supply")

# Example logic: Stock Qty < threshold AND RC present AND pending supply = 0
query_low_stock = """
SELECT 
    s.item_code AS "Item Code",
    it.item_name AS "Item Name",
    s.stock_quantity AS "Stock Qty",
    COUNT(p.po_number) AS "PO Count",
    SUM(COALESCE(p.po_qty,0) - COALESCE(p.received_qty,0)) AS "Pending Supply"
FROM stock_data s
LEFT JOIN purchase_order_data p ON s.item_code = p.item_code
LEFT JOIN item_master it ON s.item_code = it.item_code

WHERE s.stock_pos_con_dem < 1  
AND (SUM(COALESCE(p.po_qty,0)) - SUM(COALESCE(p.received_qty,0))) = 0
and s.warehouse_name = "State Total"
GROUP BY s.item_code, s.item_name, s.stock_quantity
HAVING "Pending Supply" = 0
ORDER BY s.stock_pos_con_dem ASC
"""

if st.button("Show List", key="low_stock"):
    
    low_stock_data = run_query(query_low_stock)
    if not low_stock_data.empty:
        df_low_stock = pd.DataFrame(low_stock_data)
        st.dataframe(df_low_stock, hide_index=True)
    else:
        st.success("No such low stock items found.")

# Initialize session state for displaying details
if 'show_details_for' not in st.session_state:
    st.session_state.show_details_for = None

# Sample Data for Main Table
data = {
    'ID': [1, 2, 3],
    'Name': ['Item A', 'Item B', 'Item C'],
    'Description': ['Main description for A', 'Main description for B', 'Main description for C']
}
df = pd.DataFrame(data)

# Sample Data for Sub-tables (details)
details_data = {
    1: {'Detail 1': 'More info A1', 'Detail 2': 'More info A2'},
    2: {'Detail 1': 'More info B1', 'Detail 2': 'More info B2'},
    3: {'Detail 1': 'More info C1', 'Detail 2': 'More info C2'}
}

st.title("Main Table with Hyperlink to Details")

# Display Main Table
st.write("Click 'View Details' to see more information about each item.")

cols = st.columns([0.8, 0.2]) # Adjust column widths as needed
with cols[0]:
    st.dataframe(df, hide_index=True, use_container_width=True)

with cols[1]:
    for index, row in df.iterrows():
        if st.button(f"View Details", key=f"details_button_{row['ID']}"):
            st.session_state.show_details_for = row['ID']

# Conditionally display the sub-table
if st.session_state.show_details_for is not None:
    st.subheader(f"Details for Item ID: {st.session_state.show_details_for}")
    selected_id = st.session_state.show_details_for
    if selected_id in details_data:
        detail_df = pd.DataFrame([details_data[selected_id]])
        st.table(detail_df) # Using st.table for smaller detail tables
    else:
        st.write("No details available for this item.")
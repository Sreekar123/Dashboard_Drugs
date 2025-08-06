import streamlit as st
import pandas as pd
from db_connection import run_query  # Assuming you have a db helper

# Page header
st.markdown("# 🔍 Insights")
st.markdown("---")


# Section 1: RCs expiring in 3 months
st.markdown("### 📆 RC's expiring in next 3 months")

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

if st.button("Show List", key="rc_expiring"):
    
    rc_expiry_data = run_query(query_rc_expiry)
    
    if not rc_expiry_data.empty:
        df_rc_expiry = pd.DataFrame(rc_expiry_data)
        st.dataframe(df_rc_expiry, hide_index=True)
    else:
        st.info("No RCs expiring in the next 3 months.")

st.markdown("---")

# Section 2: Low stock, RC available, but no pending supply
st.markdown("### ⚠️ Low stock, RC available, but no pending supply")

# Example logic: Stock Qty < threshold AND RC present AND pending supply = 0
query_low_stock = """
SELECT 
    s.item_code AS "Item Code",
    s.item_name AS "Item Name",
    s.stock_quantity AS "Stock Qty",
    COUNT(p.po_number) AS "PO Count",
    SUM(p.po_qty - p.received_qty) AS "Pending Supply"
FROM stock_data s
LEFT JOIN purchase_order_data p ON s.item_code = p.item_code
WHERE s.stock_quantity < 50  -- Example threshold
GROUP BY s.item_code, s.item_name, s.stock_quantity
HAVING COUNT(p.po_number) > 0 AND SUM(p.po_qty - p.received_qty) = 0
ORDER BY s.stock_quantity ASC
"""

if st.button("Show List", key="low_stock"):
    
    low_stock_data = run_query(query_low_stock)
    if not low_stock_data.empty:
        df_low_stock = pd.DataFrame(low_stock_data)
        st.dataframe(df_low_stock, hide_index=True)
    else:
        st.success("No such low stock items found.")

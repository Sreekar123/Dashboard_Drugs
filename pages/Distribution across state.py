import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import io

# Establishing database connection
from db_connection_updated import fetch_one
from db_connection_updated import run_query

with st.sidebar:
    st.title("Custom Options")
    
    selected_cons_ref = st.selectbox("Select Reference Quantity", ["Consumption/Demand", "Only Consumption"])
    selected_category = st.selectbox("Select Drugs", ["All Drugs", "Priority Drugs"])
    selected_sort = st.selectbox("Sort CMS by", ["Zero Stock Items", ">3 month Items", "CMS Name"])

    cms_query = "SELECT DISTINCT warehouse_name FROM stock_data ORDER BY warehouse_name"
    cms_result = run_query(cms_query)  # assuming run_query returns a list of tuples or a DataFrame
    cms_list = cms_result['warehouse_name'].tolist()
    cms_list.insert(0, "None")  # Add manually to top
    selected_cms = st.selectbox('Select CMS (to view list)', cms_list)


# 1. Decide the stock position column
stock_col = "stock_pos_con_dem" if selected_cons_ref == "Consumption/Demand" else "stock_pos_cons"

# 2. Build dynamic query
query = f"""
SELECT 
    sd.warehouse_name,
    sd.item_code,
    sd.{stock_col} as stock_pos,
    sd.stock_quantity,
    im.priority_item
FROM stock_data sd
JOIN item_master im ON sd.item_code = im.item_code
WHERE sd.warehouse_name != ''
"""

# 3. Apply sidebar filter for drug category
if selected_category == "Priority Drugs":
    query += " AND im.priority_item = 'Yes'"

# 4. Run query and load data
data = run_query(query)
df = pd.DataFrame(data, columns=["warehouse_name", "item_code", "stock_pos", "stock_quantity", "priority_item"])

# 5. Classify stock position into buckets
def classify(pos, stck):
    if stck == 0:
        return "No Stock"
    elif 0 < pos <= 1:
        return "<1 month"
    elif pos <= 3:
        return "1-3 months"
    else:
        return ">3 months"

print(df[["stock_pos", "stock_quantity"]].head(10))
df["bucket"] = df.apply(lambda row: classify(float(row["stock_pos"]), row["stock_quantity"]), axis=1)

print(df["bucket"].value_counts())

# 6. Aggregate count of items in each bucket per warehouse
summary = df.pivot_table(index="warehouse_name", columns="bucket", values="item_code", aggfunc="count", fill_value=0).reset_index()

# 7. Ensure all columns are present
for col in [">3 months", "1-3 months", "<1 month", "No Stock"]:
    if col not in summary.columns:
        summary[col] = 0

# 8. Sort CMSs alphabetically (or by any metric)

if selected_sort == "Zero Stock Items":
    summary = summary.sort_values(by="No Stock",ascending=True)
if selected_sort == "CMS Name":
    summary = summary.sort_values(by="warehouse_name",ascending=True)
if selected_sort == ">3 month Items":
    summary = summary.sort_values(by=">3 months",ascending=True)

# 9. Plot vertical stacked bar chart
fig = go.Figure()
categories = [">3 months", "1-3 months", "<1 month"]
colors = ["#90EE90", "#FFFACD", "#FFD6D6"]

for cat, color in zip(categories, colors):
    fig.add_trace(go.Bar(
        x=summary["warehouse_name"],
        y=summary[cat],
        name=cat,
        marker=dict(color=color),
        text=summary[cat],
        textposition="auto",
        textangle=0,
        textfont=dict(size=10, color="black")
    ))

if selected_category == "Priority Drugs":
    fig.add_trace(go.Bar(
        x=summary["warehouse_name"],
        y=summary["No Stock"],
        name="No Stock",
        marker=dict(color="#FF7F7F"),
        text=summary["No Stock"],
        textposition="outside",
        textangle=0,
        textfont=dict(size=10, color="black", **{"weight": "bold"})
    ))
else: 
    fig.add_trace(go.Bar(
        x=summary["warehouse_name"],
        y=summary["No Stock"],
        name="No Stock",
        marker=dict(color="#FF7F7F"),
        text=summary["No Stock"],
        textposition="auto",
        textangle=0,
        textfont=dict(size=10, color="black", **{"weight": "bold"})
    ))


stacked_heights = summary[categories + ["No Stock"]].sum(axis=1)
y_max = stacked_heights.max()
buffer = 15

# 10. Layout config
fig.update_layout(
    barmode="stack",
    title='Stock Position Across CMSs',
    xaxis_title="CMS Name",
    yaxis_title="No. of Items",
    #xaxis=dict(tickangle=-45, tickfont=dict
    yaxis=dict(range=[0, y_max+buffer]),
    height=600,
)

# 11. Display in Streamlit
st.markdown("### Stock Position across CMSs")
st.plotly_chart(fig, use_container_width=True)


if selected_cms and selected_cms != "None":
    # Query to fetch zero stock items for selected CMS
    list_query = f"""
        WITH cms_data AS (
            SELECT 
                sd.item_code,
                COALESCE(SUM(sd.stock_quantity), 0) AS cms_stock
            FROM stock_data sd
            WHERE sd.warehouse_name = '{selected_cms}'
            GROUP BY sd.item_code
        ),
        state_data AS (
            SELECT 
                sd.item_code,
                COALESCE(SUM(sd.stock_quantity), 0) AS state_stock
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
            ROW_NUMBER() OVER (ORDER BY st.state_stock DESC) AS "S No.",
            c.item_code AS "Item Code",
            im.item_name AS "Item Name",
            c.cms_stock AS "Stock at CMS",
            st.state_stock AS "Total Stock in State"
        FROM cms_data c
        LEFT JOIN state_data st ON st.item_code = c.item_code
        LEFT JOIN pending_po po ON po.item_code = c.item_code
        LEFT JOIN item_master im ON im.item_code = c.item_code
        WHERE c.cms_stock = 0       
    """

    if selected_category == "Priority Drugs":
        list_query += " AND im.priority_item = 'Yes'"

    list_query += "ORDER BY st.state_stock DESC;"

    zero_stock_df = run_query(list_query)

    count_zero_stock = len(zero_stock_df)    

    from st_aggrid import AgGrid, GridOptionsBuilder

    if not zero_stock_df.empty:
        st.markdown(f"#### Zero Stock Items in {selected_cms}: {count_zero_stock}")

        # Build grid options for column configuration
        gb = GridOptionsBuilder.from_dataframe(zero_stock_df)
        gb.configure_default_column(sortable=True, resizable=True, filter=False, wrapHeaderText=True, autoHeaderHeight=True)
        gb.configure_column("S No.", width = 100, filter=False, cellStyle={"textAlign": "center"})
        gb.configure_column("Item Name", filter=True, width = 600)
        gb.configure_column("Item Code", filter=True, width = 200)
        gb.configure_column("Total Stock in State", width = 300)
        gb.configure_grid_options(domLayout='normal')          # Use normal layout
        gb.configure_grid_options(floatingFilter=False)

        # If you want to format numbers with commas
        for col in ["Stock at CMS", "Total Stock in State"]:
            if col in zero_stock_df.columns:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x.toLocaleString()")

        # Build options
        grid_options = gb.build()

        AgGrid(
            zero_stock_df,
            gridOptions=grid_options,
            enable_enterprise_modules=False,      # Set True for grouping/pivot/etc. if you want
            fit_columns_on_grid_load=True,
            height=400,
            theme="blue",                         # Choose: 'blue', 'streamlit', 'balham', 'light', 'dark'
            reload_data=True
        )

        # Download Table Button
        # Convert to CSV
        csv_buffer = io.StringIO()
        zero_stock_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        col1, col2 = st.columns([3,1])

        with col2:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name="zero_stock_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    else:
        st.warning(f"No zero stock items in {selected_cms}")



    
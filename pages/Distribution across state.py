import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

# Establishing database connection
from db_connection import fetch_one
from db_connection import run_query

with st.sidebar:
    st.title("Custom Options")
    
    selected_cons_ref = st.selectbox("Select Reference Quantity", ["Consumption/Demand", "Only Consumption"])
    selected_category = st.selectbox("Select Drugs", ["All Drugs", "Priority Drugs"])
    selected_sort = st.selectbox("Sort CMS by", ["Zero Stock Items", ">3 month Items", "CMS Name"])

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
colors = ["skyblue", "lightgreen", "orange"]

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
        marker=dict(color="red"),
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
        marker=dict(color="red"),
        text=summary["No Stock"],
        textposition="auto",
        textangle=0,
        textfont=dict(size=10, color="white", **{"weight": "bold"})
    ))


# 10. Layout config
fig.update_layout(
    barmode="stack",
    title='Stock Position Across CMSs',
    xaxis_title="CMS Name",
    yaxis_title="No. of Items",
    #xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
    height=600,
)

# 11. Display in Streamlit
st.markdown("### Stock Position across CMSs")
st.plotly_chart(fig, use_container_width=True)


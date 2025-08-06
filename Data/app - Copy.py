import streamlit as st

# Page config
st.set_page_config(layout="wide")  # Enables wide layout for dashboard

# Sidebar Navigation
menu = st.sidebar.radio(
    "Navigation",
    ["Upload Page", "Main Dashboard"]
)

# Use session_state to handle page-specific filters if needed
if 'selected_filter' not in st.session_state:
    st.session_state.selected_filter = None

# Page Routing
if menu == "Main Dashboard":
    # Code for dashboard goes here
    st.title("Drug Stock Overview")

    # Display overall stats
    st.markdown("### 📦 Total Drugs: **522**")

    # Dummy values for stock status
    stock_data = {
        "> 3 months": 78,
        "1–3 months": 310,
        "< 1 month": 89,
        "Zero": 45
    }

    col1, col2 = st.columns(2)
    for i, (label, value) in enumerate(stock_data.items()):
        col = col1 if i % 2 == 0 else col2
        if col.button(f"{label} ➜ {value} items"):
            st.session_state.selected_filter = label
            st.write(f"Showing list for: **{label}**")  # Placeholder for actual filtered table

elif menu == "Upload Page":
    st.title("📤 Upload Excel File")
    uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "xls"])
    if uploaded_file is not None:
        st.success("File uploaded successfully")
        # You'll add parsing logic here

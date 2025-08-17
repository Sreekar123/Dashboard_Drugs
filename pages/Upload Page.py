import streamlit as st
import pandas as pd
import io
import psycopg2
from db_connection_updated import get_connection  # Use your existing connection function
from datetime import datetime

st.title("Upload Page")

# Page configuration
st.set_page_config(page_title="Upload Data", layout="wide")

# Upload file for Stock Data
st.header("Upload Stock Data")
stock_file = st.file_uploader("Upload Stock CSV or Excel", type=["csv", "xlsx"], key="stock")

if stock_file:
    try:
        if stock_file.name.endswith('.csv'):
            stock_df = pd.read_csv(stock_file, dtype={"Item Code": str})
        else:
            stock_df = pd.read_excel(stock_file, dtype={"Item Code": str})


        st.success("File uploaded successfully!")
        st.dataframe(stock_df.head())

        if st.button("Insert Stock Data into Database"):
            conn = get_connection()
            cur = conn.cursor()

            try:
                # Delete existing data
                cur.execute("DELETE FROM stock_data")

                # Select only the required columns
                upload_df = stock_df[["Item Code", "Warehouse Name", "Stock Quantity"]].copy()
                upload_df.columns = ["item_code", "warehouse_name", "stock_quantity"]
                

                # Clean values
                # Clean values
                upload_df["item_code"] = upload_df["item_code"].apply(lambda x: str(x).strip() if pd.notnull(x) else "")
                upload_df["warehouse_name"] = upload_df["warehouse_name"].astype(str).str.strip()
                upload_df["stock_quantity"] = upload_df["stock_quantity"].fillna(0).astype(int)


                # Write to in-memory CSV buffer
                buffer = io.StringIO()
                upload_df.to_csv(buffer, index=False, header=False)
                buffer.seek(0)

                # Bulk insert using COPY
                cur.copy_from(buffer, "stock_data", sep=",", null="", columns=("item_code", "warehouse_name", "stock_quantity"))

                conn.commit()
                st.success("Stock data inserted successfully using COPY!")

            except Exception as e:
                conn.rollback()
                st.error(f"Insert error: {e}")

            finally:
                cur.close()
                conn.close()

    except Exception as e:
        st.error(f"Upload error: {e}")



# Upload file for Purchase Order Data
st.header("Upload Purchase Order Data")
po_file = st.file_uploader("Upload PO CSV or Excel", type=["csv", "xlsx"], key="po")

if po_file:
    try:
        # Read the uploaded file
        if po_file.name.endswith('.csv'):
            po_df = pd.read_csv(po_file)
        else:
            po_df = pd.read_excel(po_file)

        st.success("File uploaded successfully!")
        st.dataframe(po_df.head())

        if st.button("Insert PO Data into Database"):
            conn = get_connection()
            cur = conn.cursor()

            entry_date = datetime.today().date()

            # Prepare records list
            records = []
            for _, row in po_df.iterrows():
                records.append((
                    entry_date,
                    row['PO NO'],
                    pd.to_datetime(row['PO DATE']).date() if pd.notnull(row['PO DATE']) else None,
                    row['Item Code'],
                    row['SUPPLIER'],
                    float(row['RATE']) if pd.notnull(row['RATE']) else 0,
                    row['RATE UNIT'],
                    int(row['PO QTY']) if pd.notnull(row['PO QTY']) else 0,
                    float(row['PO VALUE (Rs.)']) if pd.notnull(row['PO VALUE (Rs.)']) else 0,
                    int(row['RECEIVED QTY']) if pd.notnull(row['RECEIVED QTY']) else 0,
                    float(row['RECEIVED VALUE (Rs.)']) if pd.notnull(row['RECEIVED VALUE (Rs.)']) else 0,
                    float(row['SUPPLY STATUS (%)']) if pd.notnull(row['SUPPLY STATUS (%)']) else 0,
                    row['Tender No.'],
                    pd.to_datetime(row['Scheduled Delivery Date']).date() if pd.notnull(row['Scheduled Delivery Date']) else None,
                    int(row['Extended Delivery Period (in Days)']) if pd.notnull(row['Extended Delivery Period (in Days)']) else 0
                ))

            # Delete existing data (optional: comment this if not needed)
            cur.execute("DELETE FROM purchase_order_data")

            # Insert all at once
            cur.executemany("""
                INSERT INTO purchase_order_data (
                    entry_date, po_number, po_date, item_code, supplier,
                    rate, rate_unit, po_qty, po_value, received_qty,
                    received_value, supply_status, tender_number,
                    scheduled_delivery_date, extended_delivery_period_days
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, records)

            conn.commit()
            cur.close()
            conn.close()
            st.success("PO data inserted successfully using batch upload!")

    except Exception as e:
        st.error(f"Error: {e}")

# Upload file for Purchase Order Data
st.header("Upload Rate Contract Data")
rc_file = st.file_uploader("Upload RC CSV or Excel", type=["csv", "xlsx"], key="rc")

if rc_file:
    try:
        # Read the uploaded file
        if rc_file.name.endswith('.csv'):
            rc_df = pd.read_csv(rc_file)
        else:
            rc_df = pd.read_excel(rc_file)

        st.success("File uploaded successfully!")
        st.dataframe(rc_df.head())

        if st.button("Insert RC Data into Database"):
            conn = get_connection()
            cur = conn.cursor()

            entry_date = datetime.today().date()

            # Prepare records list
            records = []
            for _, row in rc_df.iterrows():
                records.append((
                    row['Item Code'],
                    row['Supplier'],
                    float(row['Rate']) if pd.notnull(row['Rate']) else 0,
                    row['RATE UNIT'],
                    pd.to_datetime(row['Tender Date']).date() if pd.notnull(row['Tender Date']) else None,
                    pd.to_datetime(row['Contract From Date']).date() if pd.notnull(row['Contract From Date']) else None,
                    pd.to_datetime(row['Contract To Date']).date() if pd.notnull(row['Contract To Date']) else None,
                    row['Rate Contract Level']
                ))

            # Delete existing data (optional: comment this if not needed)
            cur.execute("DELETE FROM rate_contract_data")

            # Insert all at once
            cur.executemany("""
                INSERT INTO rate_contract_data (
                    item_code, supplier, rate, rate_unit, tender_date, 
                    contract_from_date, contract_to_date, rate_contract_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, records)

            conn.commit()
            cur.close()
            conn.close()
            st.success("RC data inserted successfully using batch upload!")

    except Exception as e:
        st.error(f"Error: {e}")


st.header("Recalculate Stock Positions")

if st.button("🔄 Recalculate Stock Positions"):
    try:
        conn = get_connection()
        cur = conn.cursor()

        update_query = """
        UPDATE stock_data sd
        SET 
            stock_pos_cons = subq.stock_pos_cons,
            stock_pos_con_dem = subq.stock_pos_con_dem
        FROM (
            SELECT 
                sd.item_code,
                sd.warehouse_name,
                sd.stock_quantity,
                im.type_cons_dem,
                cr.cons_qty_ref,
                dr.dem_qty_ref,

                -- Calculate stock_pos_cons
                CASE 
                    WHEN cr.cons_qty_ref > 0 THEN ROUND((sd.stock_quantity::numeric / cr.cons_qty_ref) * 12, 2)
                    WHEN cr.cons_qty_ref IS NULL OR cr.cons_qty_ref = 0 THEN 
                        CASE 
                            WHEN sd.stock_quantity > 0 THEN 3.00
                            ELSE 0.00
                        END
                END AS stock_pos_cons,

                -- Calculate stock_pos_con_dem
                CASE 
                    WHEN im.type_cons_dem = 'cons' THEN 
                        CASE 
                            WHEN cr.cons_qty_ref > 0 THEN ROUND((sd.stock_quantity::numeric / cr.cons_qty_ref) * 12, 2)
                            WHEN cr.cons_qty_ref IS NULL OR cr.cons_qty_ref = 0 THEN 
                                CASE 
                                    WHEN sd.stock_quantity > 0 THEN 3.00
                                    ELSE 0.00
                                END
                        END
                    WHEN im.type_cons_dem = 'dem' THEN 
                        CASE 
                            WHEN dr.dem_qty_ref > 0 THEN ROUND((sd.stock_quantity::numeric / dr.dem_qty_ref) * 12, 2)
                            WHEN dr.dem_qty_ref IS NULL OR dr.dem_qty_ref = 0 THEN 
                                CASE 
                                    WHEN sd.stock_quantity > 0 THEN 3.00
                                    ELSE 0.00
                                END
                        END
                    ELSE NULL
                END AS stock_pos_con_dem

            FROM stock_data sd
            LEFT JOIN item_master im ON im.item_code = sd.item_code
            LEFT JOIN consumption_reference cr ON cr.item_code = sd.item_code AND cr.warehouse_name = sd.warehouse_name
            LEFT JOIN demand_reference dr ON dr.item_code = sd.item_code AND dr.warehouse_name = sd.warehouse_name
        ) AS subq
        WHERE sd.item_code = subq.item_code AND sd.warehouse_name = subq.warehouse_name;
        """

        cur.execute(update_query)
        conn.commit()
        st.success("✅ Stock positions updated successfully!")

    except Exception as e:
        st.error(f"❌ Error while updating stock positions: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()

st.markdown("<br><br><br>", unsafe_allow_html=True)

st.header("Upload Consumption Reference Data")
cons_file = st.file_uploader("Upload Consumption CSV or Excel", type=["csv", "xlsx"], key="consumption")

if cons_file:
    try:
        # Read the uploaded file
        if cons_file.name.endswith('.csv'):
            cons_df = pd.read_csv(cons_file, dtype={"Item Code": str})
        else:
            cons_df = pd.read_excel(cons_file, dtype={"Item Code": str})

        st.success("File uploaded successfully!")
        st.dataframe(cons_df.head())

        if st.button("Insert Consumption Data into Database"):
            conn = get_connection()
            cur = conn.cursor()

            try:
                # Delete all existing rows
                cur.execute("DELETE FROM consumption_reference")

                # Prepare DataFrame
                cons_df = cons_df[["Item Code", "Warehouse Name", "Consumption Qty"]].copy()
                cons_df.columns = ["item_code", "warehouse_name", "cons_qty_ref"]

                # Fill missing values
                cons_df["cons_qty_ref"] = cons_df["cons_qty_ref"].fillna(0).astype(int)

                # Convert to CSV format in memory (no index, no header)
                csv_buffer = io.StringIO()
                cons_df.to_csv(csv_buffer, index=False, header=False)
                csv_buffer.seek(0)

                # Use COPY to bulk insert
                cur.copy_from(csv_buffer, 'consumption_reference', sep=",")
                conn.commit()
                st.success("Consumption reference data inserted successfully!")

            except Exception as e:
                conn.rollback()
                st.error(f"Database error: {e}")

            finally:
                cur.close()
                conn.close()

    except Exception as e:
        st.error(f"File error: {e}")

st.header("Upload Demand Reference Data")
dem_file = st.file_uploader("Upload Annual Demand CSV or Excel", type=["csv", "xlsx"], key="demand")

if dem_file:
    try:
        # Read the uploaded file
        if dem_file.name.endswith('.csv'):
            dem_df = pd.read_csv(dem_file)
        else:
            dem_df = pd.read_excel(dem_file)

        st.success("File uploaded successfully!")
        st.dataframe(dem_df.head())  # shows first 5 rows as sample

        if st.button("Insert Demand Data into Database"):
            conn = get_connection()
            cur = conn.cursor()

            try:
                # Delete all existing rows
                cur.execute("DELETE FROM demand_reference")

                # Insert new rows
                for _, row in dem_df.iterrows():
                    cur.execute("""
                        INSERT INTO demand_reference (
                            item_code, warehouse_name, dem_qty_ref
                        ) VALUES (%s, %s, %s)
                    """, (
                        row['Item Code'],
                        row['Warehouse Name'],
                        int(row['Demand Qty']) if pd.notnull(row['Demand Qty']) else 0
                    ))

                conn.commit()
                st.success("Demand reference data updated successfully!")

            except Exception as e:
                st.error(f"Database error: {e}")
                conn.rollback()

            finally:
                cur.close()
                conn.close()

    except Exception as e:
        st.error(f"File error: {e}")

st.markdown("<br>", unsafe_allow_html=True)




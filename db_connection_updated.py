import psycopg2
import pandas as pd

# Establishing database connection
def get_connection():
    return psycopg2.connect(
        host="183.82.59.13",
        database="dashboard_data",
        user="postgres",
        password="Tgmsidc@123",
        port="5432"  # default for Postgres
    )

def run_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def fetch_one(query):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

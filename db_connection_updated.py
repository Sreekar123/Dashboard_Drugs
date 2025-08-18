import psycopg2
import pandas as pd
import streamlit as st


# Establishing database connection
def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]  # default for Postgres
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

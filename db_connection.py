import psycopg2
import pandas as pd

# Establishing database connection
def get_connection():
    return psycopg2.connect(
        host="your_hostdpg-d1tk4padbo4c73dm49lg-a.singapore-postgres.render.com",
        database="drugdashboard",
        user="drugdashboard_user",
        password="XbKeBmyW6loPQmFm0VLNcJq7I4yxLHoy",
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

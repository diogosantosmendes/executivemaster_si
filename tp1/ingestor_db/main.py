import psycopg2
import time
import os
from hdfs import InsecureClient
from datetime import datetime
import os

# Configs
PG_CONFIG = {
    "host": "postgres-db",
    "database": "stock_management",
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}
DB_NAME = os.getenv("DB_NAME")

HDFS_URL = "http://namenode:9870"
BASE_HDFS_PATH = "/stock_management/" + DB_NAME

PERIODICITY = os.getenv("INGESTOR_PERIODICITY")
CHECKPOINT_FILE = f"/app/last_sync_{DB_NAME}.txt"

def get_last_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return f.read().strip()
    return "1970-01-01 00:00:00"

def save_checkpoint(timestamp):
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(timestamp))

def ingest():
    conn = None
    try:
        last_val = get_last_checkpoint()

        # Connect to PG
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()

        # Get DB datetime as reference
        cur.execute("SELECT now();")
        current_db_time = cur.fetchone()[0]

        print(f"[{datetime.now()}] Getting data between {last_val} and {current_db_time}...")

        query = f"""
            SELECT log_id, fao_product, fao_zone, quantity, quantity, value, log_time
            FROM {DB_NAME} 
            WHERE log_time > %s AND log_time <= %s
            ORDER BY log_time ASC;
        """
        
        cur.execute(query, (last_val, current_db_time))
        rows = cur.fetchall()
        
        if rows:
          # Transform data to CSV format
          csv_data = "\n".join([",".join(map(str, row)) for row in rows])
          
          # Connect to HDFS and save
          target_path = f"{BASE_HDFS_PATH}/{current_db_time.strftime('%Y%m%d_%H%M%S')}.csv"
          
          client = InsecureClient(HDFS_URL, user='root')
          with client.write(target_path, encoding='utf-8') as writer:
              writer.write(csv_data)
              
          print(f"[{datetime.now()}] Saved data in: {target_path}")
        else:
            print(f"[{datetime.now()}] No data to ingest.")

        
        save_checkpoint(current_db_time)

        cur.close()
    except Exception as e:
        print(f"[{datetime.now()}] Ingestion error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting periodic ingestion service (5 min)...")
    while True:
        ingest()
        time.sleep(int(PERIODICITY))
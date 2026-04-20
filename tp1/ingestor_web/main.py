import requests
import os
import pandas as pd
from hdfs import InsecureClient
from datetime import datetime
import io

# Configs
EMAIL = os.getenv("FAO_EMAIL", "teu_email@exemplo.com")
PASSWORD = os.getenv("FAO_PASSWORD", "tua_password")

HDFS_URL = "http://namenode:9870"
BASE_HDFS_PATH = "/stock_management/fao_prices"

YEAR_CHECKPOINT = "/app/last_processed_year.txt"

def get_last_processed_year():
    if os.path.exists(YEAR_CHECKPOINT):
        with open(YEAR_CHECKPOINT, "r") as f:
            content = f.read().strip()
            return int(content) if content else 0
    return 0

def save_current_year(year):
    with open(YEAR_CHECKPOINT, "w") as f:
        f.write(str(year))

def get_fao_token():
    print(f"[{datetime.now()}] Getting new access token from FAO...")
    url = "https://faostatservices.fao.org/api/v1/auth/login"
    data = {"username": EMAIL, "password": PASSWORD}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json().get("AuthenticationResult").get("AccessToken")
    except Exception as e:
        print(f"[{datetime.now()}] Error on FAO login: {e}")
        return None

def fetch_and_save_prices():
    last_year = get_last_processed_year()

    now = datetime.now()
    # Force previous year on first run to ensure we have a starting point
    current_year = now.year-1 if last_year == 0 else now.year

    if current_year > last_year:
        token = get_fao_token()
        if token:

            try:
                print(f"[{datetime.now()}] Getting data from FAO...")
                
                url = f"https://faostatservices.fao.org/api/v1/en/data/PP?&element=5532&year={current_year}"
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                dados_json = response.json().get("data")
                df = pd.DataFrame(dados_json)
                output = io.StringIO()
                df.to_csv(output, index=False)
                
                # Connect to HDFS and save
                hdfs_path = f"{BASE_HDFS_PATH}/{current_year}.csv"
                
                client = InsecureClient(HDFS_URL, user='root')
                with client.write(hdfs_path, encoding='utf-8', overwrite=True) as writer:
                    writer.write(output.getvalue())
                    
                print(f"[{datetime.now()}] Saved in {hdfs_path}")
                save_current_year(current_year)
            except Exception as e:
                print(f"[{datetime.now()}] Error getting data from FAO: {e}")

if __name__ == "__main__":
    fetch_and_save_prices()
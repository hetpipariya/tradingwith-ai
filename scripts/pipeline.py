import pandas as pd
import requests
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "metadata", "symbols.csv")
JSON_PATH = os.path.join(BASE_DIR, "data", "metadata", "master.json")

def run_pipeline():
    print("🚀 Starting Update...")
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    # 1. Stream Download (Fixes KeyboardInterrupt/Hang)
    print("⏳ Downloading (Streaming)...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
            with open(JSON_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
    except Exception as e: print(f"❌ Error: {e}"); return

    # 2. Filter
    print("🔍 Filtering Data...")
    try:
        with open(JSON_PATH, 'r') as f: data = json.load(f)
        df = pd.DataFrame(data)
        my_list = ["IOB", "SUZLON", "UCOBANK", "NHPC", "IDEA", "JPPOWER", "YESBANK", "IRFC"]
        filtered = []
        for name in my_list:
            row = df[(df['symbol'] == f"{name}-EQ") & (df['exch_seg'] == 'NSE')]
            if not row.empty: filtered.append({'symbol': name, 'token': row.iloc[0]['token']})
            
        pd.DataFrame(filtered).to_csv(CSV_PATH, index=False)
        print(f"✅ Success! Saved to {CSV_PATH}")
    except Exception as e: print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_pipeline()
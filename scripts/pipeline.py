import pandas as pd
import requests
import os
import sys
import io

# --- CONFIGURATION (તમારી કંપનીઓ અહીં લખો) ---
MY_WATCHLIST = [
    "RELIANCE", 
    "TCS", 
    "INFY", 
    "SBIN", 
    "HDFCBANK", 
    "TATAMOTORS", 
    "SUZLON", 
    "IDEA", 
    "ZOMATO",
    "PCJEWELLER"
]

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "metadata", "symbols.csv")
JSON_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

def run_pipeline():
    print(f"🚀 Starting Pipeline Update for {len(MY_WATCHLIST)} Companies...")
    
    # 1. Download Master List (Improved for Large Files)
    print("⏳ Downloading Master List (Might take 30-60 seconds)...")
    try:
        # Stream download logic to handle large file size
        with requests.get(JSON_URL, stream=True) as r:
            r.raise_for_status()
            # Read bytes into buffer
            f = io.BytesIO()
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
            f.seek(0)
            
            # Load into DataFrame
            data = pd.read_json(f)
            df_master = pd.DataFrame(data)
            print("✅ Master List Downloaded Successfully!")

    except Exception as e:
        print(f"❌ Error downloading Master List: {e}")
        return

    # 2. Process Watchlist
    new_data = []
    
    print("\n🔍 Searching Tokens...")
    for name in MY_WATCHLIST:
        # Search for NSE Equity Only
        filtered = df_master[
            (df_master['symbol'] == f"{name}-EQ") & 
            (df_master['exch_seg'] == "NSE")
        ]
        
        if not filtered.empty:
            row = filtered.iloc[0]
            print(f"✅ Found: {name} -> Token: {row['token']}")
            new_data.append({
                "symbol": name,
                "token": row['token'],
                "exchange": "NSE"
            })
        else:
            print(f"⚠️  Not Found: {name} (Check Spelling)")

    # 3. Save to CSV
    if new_data:
        df_new = pd.DataFrame(new_data)
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        df_new.to_csv(CSV_PATH, index=False)
        print("\n" + "="*40)
        print(f"🎉 SUCCESS! Updated {len(df_new)} companies in symbols.csv")
        print("Now run: streamlit run ui/app.py")
        print("="*40)
    else:
        print("\n❌ No valid companies found. CSV not updated.")

if __name__ == "__main__":
    run_pipeline()
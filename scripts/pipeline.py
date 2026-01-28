import pandas as pd
import requests
import os
import sys
import io

# --- CONFIGURATION (તમારું Penny Stocks લિસ્ટ) ---
MY_WATCHLIST = [
    "IDEA", 
    "YESBANK", 
    "SUZLON", 
    "SOUTHBANK", 
    "TRIDENT",
    "JPPOWER", 
    "UCOBANK", 
    "RTNPOWER", 
    "HATHWAY", 
    "DISHTV"
]

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "metadata", "symbols.csv")
JSON_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

def run_pipeline():
    print(f"🚀 Starting Pipeline Update for {len(MY_WATCHLIST)} Companies...")
    print(f"📡 Connecting to Angel One Server...")

    try:
        # 1. Start Stream Download
        response = requests.get(JSON_URL, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        # Buffer to store data
        f = io.BytesIO()
        downloaded = 0
        chunk_size = 1024 * 1024 # 1 MB chunks

        print("⏳ Downloading Master File (Approx 100 MB)... Please Wait.")
        
        # 2. Download with Progress Indicator
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                # Show Progress in MB
                mb_downloaded = downloaded / (1024 * 1024)
                sys.stdout.write(f"\r📥 Downloaded: {mb_downloaded:.2f} MB")
                sys.stdout.flush()

        print("\n✅ Download Complete! Processing Data...")
        
        # 3. Process Data
        f.seek(0)
        data = pd.read_json(f)
        df_master = pd.DataFrame(data)

    except Exception as e:
        print(f"\n❌ Error during download: {e}")
        return

    # 4. Filter Watchlist
    new_data = []
    print("🔍 Searching Tokens...")
    
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

    # 5. Save CSV
    if new_data:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        df_new = pd.DataFrame(new_data)
        df_new.to_csv(CSV_PATH, index=False)
        print("\n" + "="*40)
        print(f"🎉 SUCCESS! Updated {len(df_new)} companies in symbols.csv")
        print("Now run: python run.py")
        print("="*40)
    else:
        print("\n❌ No valid companies found. CSV not updated.")

if __name__ == "__main__":
    run_pipeline()
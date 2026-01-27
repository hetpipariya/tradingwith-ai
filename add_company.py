import pandas as pd
import requests
import os

# --- CONFIG ---
CSV_PATH = "data/metadata/symbols.csv"
JSON_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

def load_master_json():
    print("⏳ Downloading Angel One Scrip Master (One Time)...")
    try:
        data = requests.get(JSON_URL).json()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"❌ Error downloading Master List: {e}")
        return pd.DataFrame()

def add_symbol():
    # 1. Load Master Data
    df_master = load_master_json()
    
    if df_master.empty:
        return

    while True:
        print("\n" + "="*40)
        search_name = input("🔍 Enter Stock Name (e.g. RELIANCE, SBIN) or 'EXIT': ").upper().strip()
        
        if search_name == 'EXIT':
            break

        # 2. Filter Logic (NSE Equity Only)
        # Apne fakt NSE EQ (Equity) j joie chhe.
        filtered = df_master[
            (df_master['symbol'].str.contains(f"{search_name}-EQ")) & 
            (df_master['exch_seg'] == "NSE")
        ]

        if filtered.empty:
            print("❌ Company not found! Please check spelling.")
            continue

        # 3. Show Results
        row = filtered.iloc[0] # Take the first match
        token = row['token']
        symbol = row['name'] # Actual name e.g. RELIANCE
        exch = row['exch_seg']

        print(f"✅ Found: {symbol} | Token: {token} | Exch: {exch}")
        
        confirm = input(f"👉 Add {symbol} to System? (y/n): ").lower()
        
        if confirm == 'y':
            # 4. Save to CSV
            new_row = {"symbol": symbol, "token": token, "exchange": exch}
            
            # Check if file exists
            if os.path.exists(CSV_PATH):
                df_csv = pd.read_csv(CSV_PATH)
                # Check if already exists
                if token in df_csv['token'].astype(str).values:
                    print(f"⚠️ {symbol} already exists in CSV!")
                    continue
                
                # Append
                df_csv = pd.concat([df_csv, pd.DataFrame([new_row])], ignore_index=True)
            else:
                df_csv = pd.DataFrame([new_row])

            df_csv.to_csv(CSV_PATH, index=False)
            print(f"🎉 {symbol} Added Successfully!")
            print("🚀 Now refresh your Streamlit App!")

if __name__ == "__main__":
    add_symbol()
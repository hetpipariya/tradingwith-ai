import os
import requests
import pandas as pd
import json

# --- CONFIGURATION ---
URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

# આપણે ફાઈલ અહીં સેવ કરીશું જેથી app.py ને મળી રહે
OUTPUT_DIR = os.path.join("data", "metadata")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "symbols.csv")

# ✅ સુધારેલું લિસ્ટ (Correct NSE Symbols)
MY_WATCHLIST = [
    "IOB", 
    "SUZLON", 
    "UCOBANK", 
    "NHPC", 
    "IDEA", 
    "JPPOWER", 
    "YESBANK", 
    "IRFC", 
    "OLAELEC",       # સુધારો: OLAELC -> OLAELEC
    "PCJEWELLER", 
    "JAGRAN", 
    "ZOMATO",
    "GOLDBEES",      # GOLDECASE ની જગ્યાએ Gold ETF
    "SILVERBEES",    # SILVERCASE ની જગ્યાએ Silver ETF
    "KABRAEXTRU",    # KABARADG કદાચ KABRAEXTRU છે (Kabra Extrusion)
    "HINDCOPPER"     # Metal માટે એક સ્ટોક ઉમેર્યો
]

def run_pipeline():
    print("🚀 Starting Pipeline Update...")

    # 1. DOWNLOAD SCRIP MASTER
    print("⏳ Downloading Scrip Master from Angel One...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        r = requests.get(URL, headers=headers)
        if r.status_code != 200:
            print(f"❌ Download Failed! Status: {r.status_code}")
            return

        data = r.json()
        print(f"✅ Downloaded! Total Scrips: {len(data)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 2. PROCESS DATA
    print("⚙️ Processing Data...")
    
    try:
        df = pd.DataFrame(data)
        
        # ફક્ત NSE Equity (EQ) જ રાખો
        df_nse = df[df['exch_seg'] == 'NSE']
        
        watchlist_tokens = []
        
        for stock in MY_WATCHLIST:
            # 1. પહેલા સીધું નામ શોધો (Exact Match)
            match = df_nse[df_nse['symbol'] == stock]
            
            # 2. જો ન મળે, તો પાછળ -EQ લગાવીને શોધો (Angel One format)
            if match.empty:
                match = df_nse[df_nse['symbol'] == f"{stock}-EQ"]
            
            if not match.empty:
                # જો એક કરતા વધુ હોય તો પહેલું લઈ લો
                token = match.iloc[0]['token']
                symbol = match.iloc[0]['symbol'].replace('-EQ', '') # Save clean name
                watchlist_tokens.append({'symbol': symbol, 'token': token})
                print(f"   -> Found: {symbol} (Token: {token})")
            else:
                print(f"   ⚠️  Symbol Not Found: {stock} (Check Spelling)")

        # 3. SAVE TO CSV
        if watchlist_tokens:
            # ફોલ્ડર ના હોય તો બનાવો
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
            
            out_df = pd.DataFrame(watchlist_tokens)
            out_df.to_csv(OUTPUT_FILE, index=False)
            print(f"✅ Success! Saved {len(out_df)} symbols to '{OUTPUT_FILE}'")
        else:
            print("❌ No symbols matched!")

    except Exception as e:
        print(f"❌ Error processing data: {e}")

if __name__ == "__main__":
    run_pipeline()
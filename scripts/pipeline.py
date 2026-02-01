import os
import requests
import pandas as pd
import json


URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


OUTPUT_DIR = os.path.join("data", "metadata")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "symbols.csv")


MY_WATCHLIST = [
    "IOB", 
    "SUZLON", 
    "UCOBANK", 
    "NHPC", 
    "IDEA", 
    "JPPOWER", 
    "YESBANK", 
    "IRFC", 
    "OLAELEC",       
    "PCJEWELLER", 
    "JAGRAN", 
    "ZOMATO",
    "GOLDBEES",      
    "SILVERBEES",    
    "KABRAEXTRU",    
    "HINDCOPPER"     
]

def run_pipeline():
    print("🚀 Starting Pipeline Update...")

    
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

    
    print("⚙️ Processing Data...")
    
    try:
        df = pd.DataFrame(data)
        
        
        df_nse = df[df['exch_seg'] == 'NSE']
        
        watchlist_tokens = []
        
        for stock in MY_WATCHLIST:
            
            match = df_nse[df_nse['symbol'] == stock]
            
            
            if match.empty:
                match = df_nse[df_nse['symbol'] == f"{stock}-EQ"]
            
            if not match.empty:
                
                token = match.iloc[0]['token']
                symbol = match.iloc[0]['symbol'].replace('-EQ', '') 
                watchlist_tokens.append({'symbol': symbol, 'token': token})
                print(f"   -> Found: {symbol} (Token: {token})")
            else:
                print(f"   ⚠️  Symbol Not Found: {stock} (Check Spelling)")

        
        if watchlist_tokens:
            
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
import pandas as pd
import requests
import os
import sys
import io

# --- અપડેટ કરેલું લિસ્ટ (તમારા ફોટા મુજબ) ---
MY_WATCHLIST = [
    "IOB",          # Indian Overseas Bank
    "SUZLON",       # Suzlon Energy
    "UCOBANK",      # UCO Bank
    "NHPC",         # NHPC Ltd
    "IDEA",         # Vodafone Idea
    "JPPOWER",      # Jaiprakash Power
    "METALIETF",    # Metal ETF
    "PCJEWELLER",   # PC Jeweller
    "GOLDCASE",     # Gold Case ETF
    "SILVERCASE",   # Silver Case ETF
    "YESBANK",      # Yes Bank
    "SOUTHBANK",    # South Indian Bank
    "IRFC",         # Indian Railway Finance Corp
    "KABRADG",      # Kabra Drugs
    "JAGRAN"        # Jagran Prakashan
]

# --- PATHS ---
# અહી ખાતરી કરજો કે પાથ બરાબર હોય
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# જો પ્રોજેક્ટ સ્ટ્રક્ચર અલગ હોય તો આ પાથ ચેક કરવો:
CSV_PATH = os.path.join(BASE_DIR, "data", "metadata", "symbols.csv") 
JSON_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

def run_pipeline():
    print(f"🚀 Starting Pipeline Update for {len(MY_WATCHLIST)} Companies...")
    
    try:
        # 1. Angel One માંથી માસ્ટર ફાઈલ ડાઉનલોડ
        print("⏳ Downloading Master JSON... Please Wait.")
        response = requests.get(JSON_URL)
        data = response.json()
        df_master = pd.DataFrame(data)
        print("✅ Download Complete! Processing Data...")

    except Exception as e:
        print(f"\n❌ Error during download: {e}")
        return

    # 2. Watchlist ફિલ્ટર કરો
    new_data = []
    print("🔍 Searching Tokens...")
    
    for name in MY_WATCHLIST:
        # ઇક્વિટી (EQ) અને ETFs માટે ચેક કરીએ
        # નોટ: ઘણીવાર ETFs ના નામ પાછળ -EQ નથી હોતું, એટલે આપણે બે રીતે ટ્રાય કરીશું
        
        filtered = df_master[
            ((df_master['symbol'] == f"{name}-EQ") | (df_master['symbol'] == name)) & 
            (df_master['exch_seg'] == "NSE")
        ]
        
        if not filtered.empty:
            # જે પહેલું મળે તે લેવું (EQ હોય તો સારું)
            row = filtered.iloc[0]
            print(f"✅ Found: {name} -> Token: {row['token']}")
            new_data.append({
                "symbol": name,
                "token": row['token'],
                "exchange": "NSE"
            })
        else:
            print(f"⚠️  Not Found: {name} (Check Spelling or Exchange)")

    # 3. CSV સેવ કરો
    if new_data:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        df_new = pd.DataFrame(new_data)
        df_new.to_csv(CSV_PATH, index=False)
        print("\n" + "="*40)
        print(f"🎉 SUCCESS! Updated {len(df_new)} companies in symbols.csv")
        print("Now restart your Streamlit App.")
        print("="*40)
    else:
        print("\n❌ No valid companies found.")

if __name__ == "__main__":
    run_pipeline()
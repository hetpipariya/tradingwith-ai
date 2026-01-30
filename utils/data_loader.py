import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import streamlit as st
import os
import time

class DataLoader:
    # સેશનને કેશ (Cache) કરીએ છીએ જેથી વારંવાર લોગિન ન કરવું પડે
    @staticmethod
    @st.cache_resource(ttl=3600) # 1 કલાક સુધી લોગિન સાચવી રાખશે
    def get_session():
        try:
            # સિક્રેટ્સ લોડ કરો
            api_key = st.secrets.get("API_KEY") or os.getenv("API_KEY")
            client_id = st.secrets.get("CLIENT_ID") or os.getenv("CLIENT_ID")
            pwd = st.secrets.get("PASSWORD") or os.getenv("PASSWORD")
            raw_totp = st.secrets.get("TOTP_KEY") or os.getenv("TOTP_KEY")
            
            # સ્પેસ દૂર કરો (Non-base32 એરર ફિક્સ)
            totp_key = "".join(raw_totp.split()).strip()

            obj = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_key).now()
            
            data = obj.generateSession(client_id, pwd, totp)
            
            if data['status']:
                return obj
            else:
                st.error(f"Login Failed: {data['message']}")
                return None
        except Exception as e:
            st.error(f"Critical Login Error: {e}")
            return None

    @staticmethod
    # ડેટાને પણ 1 મિનિટ કેશ કરો જેથી રિફ્રેશ રેટ લિમિટ ન નડે
    @st.cache_data(ttl=60) 
    def fetch_ohlcv(symbol_token, interval="FIVE_MINUTE"):
        api = DataLoader.get_session()
        if not api: return pd.DataFrame()
        
        # 10 દિવસનો ડેટા
        to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        from_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M")
        
        try:
            # ધીમી રિક્વેસ્ટ માટે થોડો વિરામ (Safe side)
            time.sleep(0.5) 
            data = api.getCandleData({
                "exchange": "NSE", "symboltoken": str(symbol_token),
                "interval": interval, "fromdate": from_date, "todate": to_date
            })
            
            if data and data.get('status'):
                df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df.astype(float)
        except Exception as e:
            # ચૂપચાપ ફેલ થવાને બદલે પ્રિન્ટ કરો
            print(f"Data Fetch Error: {e}")
            pass
            
        return pd.DataFrame()
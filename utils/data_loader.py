import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import streamlit as st
import os
import time

class DataLoader:
    @staticmethod
    def get_session():
        # Session State માં ચેક કરો કે લોગિન છે કે નહિ
        if 'smart_api' in st.session_state and st.session_state['smart_api']:
            return st.session_state['smart_api']

        try:
            # Secrets માંથી ડેટા લો
            api_key = st.secrets["API_KEY"]
            client_id = st.secrets["CLIENT_ID"]
            pwd = st.secrets["PASSWORD"]
            raw_totp = st.secrets["TOTP_KEY"]
            
            # TOTP માં સ્પેસ હોય તો કાઢી નાખો
            totp_key = "".join(raw_totp.split()).strip()

            obj = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_key).now()
            
            data = obj.generateSession(client_id, pwd, totp)
            
            if data['status']:
                st.session_state['smart_api'] = obj
                return obj
            else:
                # જો લોગિન ફેઈલ થાય તો None રિટર્ન કરો (Crash નહિ)
                print(f"Login Failed: {data['message']}")
                return None
        except Exception as e:
            print(f"Critical Login Error: {e}")
            return None

    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def fetch_ohlcv(symbol_token, interval="FIVE_MINUTE"):
        api = DataLoader.get_session()
        if not api: return pd.DataFrame()
        
        to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
        
        try:
            time.sleep(0.2) # Rate limit થી બચવા
            data = api.getCandleData({
                "exchange": "NSE", 
                "symboltoken": str(symbol_token),
                "interval": interval, 
                "fromdate": from_date, 
                "todate": to_date
            })
            
            if data and isinstance(data, dict) and data.get('status'):
                df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                # બધો ડેટા ફ્લોટમાં કન્વર્ટ કરવો જરૂરી
                df = df.astype(float)
                return df
            else:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
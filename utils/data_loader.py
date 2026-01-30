import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import time

class DataLoader:
    @staticmethod
    def get_session():
        # જો લોગિન હોય તો ફરી ન કરો
        if 'smart_api' in st.session_state and st.session_state['smart_api']:
            return st.session_state['smart_api']

        try:
            # Secrets માંથી ડેટા લો
            api_key = st.secrets.get("TRADING_API_KEY") or st.secrets.get("API_KEY")
            client_id = st.secrets.get("CLIENT_ID")
            pwd = st.secrets.get("TRADING_PWD") or st.secrets.get("PASSWORD")
            raw_totp = st.secrets.get("TOTP_KEY")
            
            if not all([api_key, client_id, pwd, raw_totp]):
                return None

            totp_key = "".join(str(raw_totp).split()).strip()
            obj = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_key).now()
            
            data = obj.generateSession(client_id, pwd, totp)
            
            if data['status']:
                st.session_state['smart_api'] = obj
                return obj
            else:
                return None
        except Exception as e:
            return None

    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def fetch_ohlcv(symbol_token, interval="FIVE_MINUTE"):
        api = DataLoader.get_session()
        if not api: return pd.DataFrame()
        
        to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        from_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
        
        try:
            time.sleep(0.1) # Rate Limit Safety
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
                return df.astype(float)
            else:
                return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
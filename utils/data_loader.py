import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import streamlit as st
import sys
import os

class DataLoader:
    _session = None
    _obj = None

    @staticmethod
    def get_credentials():
        # 1. Try Streamlit Cloud Secrets
        try:
            return (st.secrets["TRADING_API_KEY"], st.secrets["CLIENT_ID"], 
                    st.secrets["TRADING_PWD"], st.secrets["TOTP_KEY"])
        except:
            pass
        
        # 2. Try Local .env via credentials.py
        try:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            import credentials
            return (credentials.TRADING_API_KEY, credentials.CLIENT_ID, 
                    credentials.TRADING_PWD, credentials.TOTP_KEY)
        except:
            return None, None, None, None

    @staticmethod
    def get_session():
        if DataLoader._obj is None:
            try:
                api_key, client_id, pwd, totp_key = DataLoader.get_credentials()
                if not api_key: return None
                
                obj = SmartConnect(api_key=api_key)
                totp = pyotp.TOTP(totp_key).now()
                data = obj.generateSession(client_id, pwd, totp)
                
                if data['status']:
                    DataLoader._obj = obj
                    DataLoader._session = data
            except Exception as e:
                print(f"Login Error: {e}")
        return DataLoader._obj

    @staticmethod
    def fetch_ohlcv(symbol_token, exchange="NSE", interval="FIVE_MINUTE"):
        try:
            api = DataLoader.get_session()
            if not api: return pd.DataFrame()
            
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5) # Last 5 days data
            
            historicParam = {
                "exchange": exchange,
                "symboltoken": str(symbol_token),
                "interval": interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            
            data = api.getCandleData(historicParam)
            if data['status'] and data['data']:
                df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df.astype(float)
        except:
            pass
        return pd.DataFrame()
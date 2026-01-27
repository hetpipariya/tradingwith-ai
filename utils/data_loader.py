import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import sys
import os
import streamlit as st

class DataLoader:
    _session = None
    _obj = None

    @staticmethod
    def get_credentials():
        """
        આ ફંક્શન સ્માર્ટ છે:
        1. પહેલા Streamlit Cloud પર Secrets ચેક કરશે.
        2. જો ત્યાં ના મળે, તો લોકલ credentials.py ચેક કરશે.
        """
        # 1. Try Cloud (Streamlit Secrets)
        try:
            return (
                st.secrets["TRADING_API_KEY"],
                st.secrets["CLIENT_ID"],
                st.secrets["TRADING_PWD"],
                st.secrets["TOTP_KEY"]
            )
        except (FileNotFoundError, KeyError):
            pass

        # 2. Try Local (credentials.py)
        try:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            import credentials
            return (
                credentials.API_KEY,
                credentials.CLIENT_ID,
                credentials.PASSWORD,
                credentials.TOTP_KEY
            )
        except ImportError:
            # જો બંને જગ્યાએ ના મળે તો
            return None, None, None, None

    @staticmethod
    def get_session():
        if DataLoader._obj is None:
            try:
                # ગમે ત્યાંથી ક્રેડેન્શિયલ લાવો
                api_key, client_id, pwd, totp_key = DataLoader.get_credentials()
                
                if not api_key: 
                    print("❌ Credentials Missing (Check Secrets or .env)")
                    return None

                obj = SmartConnect(api_key=api_key)
                totp = pyotp.TOTP(totp_key).now()
                data = obj.generateSession(client_id, pwd, totp)
                
                if data['status']:
                    DataLoader._obj = obj
                    DataLoader._session = data
                    print("✅ Angel One Login Successful")
                else:
                    print(f"❌ Login Failed: {data['message']}")
            except Exception as e:
                print(f"❌ Connection Error: {e}")
        return DataLoader._obj

    @staticmethod
    def fetch_ohlcv(symbol_token, exchange="NSE", interval="FIVE_MINUTE", days=2):
        try:
            api = DataLoader.get_session()
            if not api: return pd.DataFrame()

            # Token must be string
            token_str = str(symbol_token)
            
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            historicParam = {
                "exchange": exchange,
                "symboltoken": token_str,
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
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
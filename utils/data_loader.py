import pandas as pd
from datetime import datetime, timedelta
from SmartApi import SmartConnect
import pyotp
import sys
import os

# Import credentials
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import credentials

class DataLoader:
    _session = None
    _obj = None

    @staticmethod
    def get_session():
        if DataLoader._obj is None:
            try:
                obj = SmartConnect(api_key=credentials.API_KEY)
                totp = pyotp.TOTP(credentials.TOTP_KEY).now()
                data = obj.generateSession(credentials.CLIENT_ID, credentials.PASSWORD, totp)
                if data['status']:
                    DataLoader._obj = obj
                    DataLoader._session = data
                else:
                    print(f"Login Failed: {data['message']}")
            except Exception as e:
                print(f"Connection Error: {e}")
        return DataLoader._obj

    @staticmethod
    def fetch_ohlcv(symbol_token, exchange="NSE", interval="FIVE_MINUTE", days=2):
        try:
            api = DataLoader.get_session()
            if not api: return pd.DataFrame()

            # Fix: Ensure Token is String
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
            print(f"Error: {e}")
            return pd.DataFrame()
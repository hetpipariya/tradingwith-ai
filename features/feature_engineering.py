import pandas as pd
import pandas_ta as ta  # Ensure you add 'pandas_ta' to requirements.txt

class FeatureEngine:
    @staticmethod
    def apply_indicators(df):
        df = df.copy()
        
        # 1. EMA (Trend)
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_50'] = ta.ema(df['close'], length=50)
        
        # 2. RSI (Momentum)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # 3. Support & Resistance (Rolling Min/Max)
        df['support'] = df['low'].rolling(window=20).min()
        df['resistance'] = df['high'].rolling(window=20).max()
        
        # 4. Fill NaN
        df.fillna(method='bfill', inplace=True)
        return df
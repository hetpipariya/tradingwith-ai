import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class FeatureEngine:
    @staticmethod
    def apply_indicators(df):
        # 1. EMAs (9, 15, 50)
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_15'] = df['close'].ewm(span=15, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # 2. RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 3. VWAP
        v = df['volume'].values
        tp = (df['low'] + df['high'] + df['close']) / 3
        df['vwap'] = (tp * v).cumsum() / v.cumsum()

        # 4. Bollinger Bands (20, 2)
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['std_20'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma_20'] + (2 * df['std_20'])
        df['bb_lower'] = df['sma_20'] - (2 * df['std_20'])

        # 5. Supertrend (10, 3) - Manual Logic
        high = df['high']
        low = df['low']
        close = df['close']
        
        # ATR Calculation
        tr0 = abs(high - low)
        tr1 = abs(high - close.shift(1))
        tr2 = abs(low - close.shift(1))
        tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/10, adjust=False).mean()
        
        # Bands Calculation
        hl2 = (high + low) / 2
        df['st_upper'] = hl2 + (3 * atr)
        df['st_lower'] = hl2 - (3 * atr)
        df['in_uptrend'] = True
        
        # Supertrend Trend Logic
        for current in range(1, len(df.index)):
            previous = current - 1
            if close.iloc[current] > df['st_upper'].iloc[previous]:
                df.iloc[current, df.columns.get_loc('in_uptrend')] = True
            elif close.iloc[current] < df['st_lower'].iloc[previous]:
                df.iloc[current, df.columns.get_loc('in_uptrend')] = False
            else:
                df.iloc[current, df.columns.get_loc('in_uptrend')] = df.iloc[previous, df.columns.get_loc('in_uptrend')]
                
                if df.iloc[current, df.columns.get_loc('in_uptrend')] and df['st_lower'].iloc[current] < df['st_lower'].iloc[previous]:
                    df.iloc[current, df.columns.get_loc('st_lower')] = df['st_lower'].iloc[previous]
                if not df.iloc[current, df.columns.get_loc('in_uptrend')] and df['st_upper'].iloc[current] > df['st_upper'].iloc[previous]:
                    df.iloc[current, df.columns.get_loc('st_upper')] = df['st_upper'].iloc[previous]
                    
        df['supertrend'] = np.where(df['in_uptrend'], df['st_lower'], df['st_upper'])

        return df

    @staticmethod
    def find_patterns(df):
        # Double Bottom Detection
        lows = argrelextrema(df['low'].values, np.less, order=10)[0]
        patterns = []
        if len(lows) >= 2:
            if abs(df['low'].iloc[lows[-1]] - df['low'].iloc[lows[-2]]) / df['low'].iloc[lows[-2]] < 0.005:
                patterns.append("Double Bottom (Bullish)")
        return patterns
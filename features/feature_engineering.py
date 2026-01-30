import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class FeatureEngine:
    @staticmethod
    def calculate_supertrend(df, period=10, multiplier=3):
        # Supertrend Manual Calculation (કેમ કે ta લાઈબ્રેરીમાં આ ડાયરેક્ટ નથી)
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        # Calculate Basic Upper and Lower Bands
        hl2 = (high + low) / 2
        final_upperband = hl2 + (multiplier * atr)
        final_lowerband = hl2 - (multiplier * atr)
        
        supertrend = [True] * len(df) # True = Uptrend, False = Downtrend
        
        # Logic for Supertrend
        for i in range(1, len(df.index)):
            curr, prev = i, i-1
            
            # Upper Band Logic
            if close[curr] > final_upperband[prev]:
                supertrend[curr] = True
            elif close[curr] < final_lowerband[prev]:
                supertrend[curr] = False
            else:
                supertrend[curr] = supertrend[prev]
                
                # Adjustment keeping bands flat if no breakout
                if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                    final_lowerband[curr] = final_lowerband[prev]
                if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                    final_upperband[curr] = final_upperband[prev]

        # Remove bands that don't apply to the trend
        # Note: સાદગી માટે આપણે અહીં ખાલી Trend Direction return કરીએ છીએ
        return pd.Series(supertrend, index=df.index)

    @staticmethod
    def apply_indicators(df):
        if df.empty: return df
        
        # 1. EMA (9 & 50)
        df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
        
        # 2. RSI (14)
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        # 3. Bollinger Bands (20)
        indicator_bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_upper'] = indicator_bb.bollinger_hband()
        df['bb_lower'] = indicator_bb.bollinger_lband()
        
        # 4. Supertrend (Custom Function)
        # અહીં આપણે જાતે ગણતરી કરેલું ફંક્શન વાપરીએ છીએ
        df['in_uptrend'] = FeatureEngine.calculate_supertrend(df)
        
        # Supertrend Plotting માટે આપણે એક ડમી વેલ્યુ લઈએ (Graph માટે)
        # જો Uptrend હોય તો Low ની નીચે લીલું ટપકું, Downtrend હોય તો High ની ઉપર લાલ
        df['supertrend'] = np.where(df['in_uptrend'], df['low'] * 0.999, df['high'] * 1.001)

        # 5. VWAP (Manual Calculation)
        v = df['volume'].values
        tp = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (tp * v).cumsum() / v.cumsum()
        
        return df.dropna()
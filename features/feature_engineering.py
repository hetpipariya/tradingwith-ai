import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice

class FeatureEngine:
    @staticmethod
    def calculate_supertrend(df, period=10, multiplier=3):
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()

        hl2 = (high + low) / 2
        final_upperband = hl2 + (multiplier * atr)
        final_lowerband = hl2 - (multiplier * atr)
        
        supertrend = [True] * len(df)
        
        for i in range(1, len(df.index)):
            curr, prev = i, i-1
            if close[curr] > final_upperband[prev]:
                supertrend[curr] = True
            elif close[curr] < final_lowerband[prev]:
                supertrend[curr] = False
            else:
                supertrend[curr] = supertrend[prev]
                if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                    final_lowerband[curr] = final_lowerband[prev]
                if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                    final_upperband[curr] = final_upperband[prev]

        return pd.Series(supertrend, index=df.index)

    @staticmethod
    def apply_indicators(df):
        if df.empty: return df
        
        # 1. EMAs (9 & 15 માંગ્યા હતા તે)
        df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_15'] = EMAIndicator(close=df['close'], window=15).ema_indicator()
        
        # 2. RSI (14)
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        # 3. MACD (નવું ઉમેર્યું)
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # 4. VWAP (નવું ઉમેર્યું)
        try:
            vwap = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
            df['vwap'] = vwap.volume_weighted_average_price()
        except:
            df['vwap'] = df['close'] # જો ડેટા ઓછો હોય તો એરર ન આવે
        
        # 5. Supertrend
        df['in_uptrend'] = FeatureEngine.calculate_supertrend(df)
        df['supertrend'] = np.where(df['in_uptrend'], df['low'] * 0.999, df['high'] * 1.001)

        return df.dropna()
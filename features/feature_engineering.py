import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD, PSARIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

class FeatureEngine:
    @staticmethod
    def calculate_supertrend(df, period=10, multiplier=3):
        high = df['high']; low = df['low']; close = df['close']
        
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
            if close.iloc[curr] > final_upperband.iloc[prev]:
                supertrend[curr] = True
            elif close.iloc[curr] < final_lowerband.iloc[prev]:
                supertrend[curr] = False
            else:
                supertrend[curr] = supertrend[prev]
                if supertrend[curr] == True and final_lowerband.iloc[curr] < final_lowerband.iloc[prev]:
                    final_lowerband.iloc[curr] = final_lowerband.iloc[prev]
                if supertrend[curr] == False and final_upperband.iloc[curr] > final_upperband.iloc[prev]:
                    final_upperband.iloc[curr] = final_upperband.iloc[prev]

        return pd.Series(supertrend, index=df.index)

    @staticmethod
    def apply_indicators(df):
        if df.empty: return df
        
        # 1. EMAs (આ લાઈન ખૂટતી હતી એટલે એરર આવતી હતી)
        df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator() 
        
        # 2. RSI & Stoch RSI
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        stoch = StochRSIIndicator(close=df['close'], window=14, smooth1=3, smooth2=3)
        df['stoch_k'] = stoch.stochrsi_k()
        
        # 3. VWAP
        try:
            vwap = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
            df['vwap'] = vwap.volume_weighted_average_price()
        except:
            df['vwap'] = df['close']
        
        # 4. Supertrend
        df['in_uptrend'] = FeatureEngine.calculate_supertrend(df)
        df['supertrend'] = np.where(df['in_uptrend'], df['low'] * 0.999, df['high'] * 1.001)

        # 5. MACD
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()

        # 6. Bollinger Bands
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()

        # 7. Parabolic SAR
        psar = PSARIndicator(df['high'], df['low'], df['close'], step=0.02, max_step=0.2)
        df['psar'] = psar.psar()

        # 8. SCALP PRO SIGNALS
        df['scalp_buy'] = (df['close'] > df['ema_50']) & (df['in_uptrend']) & (df['stoch_k'] < 0.25)
        df['scalp_sell'] = (df['close'] < df['ema_50']) & (~df['in_uptrend']) & (df['stoch_k'] > 0.75)

        return df.dropna()

    @staticmethod
    def detect_patterns(df):
        return []
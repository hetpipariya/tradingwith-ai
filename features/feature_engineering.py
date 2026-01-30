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
        
        # Indicators
        df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_15'] = EMAIndicator(close=df['close'], window=15).ema_indicator()
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        try:
            vwap = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
            df['vwap'] = vwap.volume_weighted_average_price()
        except:
            df['vwap'] = df['close']
        
        df['in_uptrend'] = FeatureEngine.calculate_supertrend(df)
        df['supertrend'] = np.where(df['in_uptrend'], df['low'] * 0.999, df['high'] * 1.001)

        return df.dropna()

    @staticmethod
    def detect_patterns(df, window=5):
        """
        Detects Double Top and Double Bottom patterns
        """
        # Create a copy to avoid SettingWithCopy warnings
        df_pat = df.copy()
        patterns = []
        
        # Identify local peaks (highs) and troughs (lows)
        # We look at 5 candles: 2 before, current, 2 after
        df_pat['is_high'] = df_pat['high'].rolling(window=window, center=True).apply(lambda x: x.argmax() == window // 2, raw=True)
        df_pat['is_low'] = df_pat['low'].rolling(window=window, center=True).apply(lambda x: x.argmin() == window // 2, raw=True)
        
        highs = df_pat[df_pat['is_high'] == 1.0]
        lows = df_pat[df_pat['is_low'] == 1.0]

        # --- Double Top (Bearish - 'M' Shape) ---
        if len(highs) >= 2:
            # Check the last few peaks
            recent_highs = highs.tail(5) 
            for i in range(len(recent_highs) - 1):
                p1 = recent_highs.iloc[i]
                p2 = recent_highs.iloc[i+1]
                
                # Check if prices are similar (within 0.3% difference)
                price_diff = abs(p1['high'] - p2['high'])
                threshold = p1['high'] * 0.003
                
                # Check if there is enough time gap (at least 5 candles)
                time_diff = (df_pat.index.get_loc(p2.name) - df_pat.index.get_loc(p1.name))

                if price_diff <= threshold and time_diff > 5:
                    patterns.append({
                        'name': 'Double Top (Sell)',
                        'points': [(p1.name, p1['high']), (p2.name, p2['high'])],
                        'color': '#FF1744' # Red
                    })

        # --- Double Bottom (Bullish - 'W' Shape) ---
        if len(lows) >= 2:
            recent_lows = lows.tail(5)
            for i in range(len(recent_lows) - 1):
                p1 = recent_lows.iloc[i]
                p2 = recent_lows.iloc[i+1]
                
                price_diff = abs(p1['low'] - p2['low'])
                threshold = p1['low'] * 0.003
                time_diff = (df_pat.index.get_loc(p2.name) - df_pat.index.get_loc(p1.name))
                
                if price_diff <= threshold and time_diff > 5:
                    patterns.append({
                        'name': 'Double Bottom (Buy)',
                        'points': [(p1.name, p1['low']), (p2.name, p2['low'])],
                        'color': '#00E676' # Green
                    })
                        
        return patterns
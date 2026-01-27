import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

class FeatureEngine:
    """Vectorized feature engineering using modern 'ta' library."""
    
    @staticmethod
    def apply_indicators(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        
        # Ensure Inputs are Series
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        # 1. Trend Indicators (EMA)
        df['ema_9'] = EMAIndicator(close=close, window=9).ema_indicator()
        df['ema_21'] = EMAIndicator(close=close, window=21).ema_indicator()
        df['ema_50'] = EMAIndicator(close=close, window=50).ema_indicator()
        
        # 2. Momentum (RSI)
        df['rsi'] = RSIIndicator(close=close, window=14).rsi()
        
        # 3. Volatility (ATR)
        df['atr'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        
        # 4. VWAP
        vwap = VolumeWeightedAveragePrice(high=high, low=low, close=close, volume=volume, window=14)
        df['vwap'] = vwap.volume_weighted_average_price()
        
        # 5. Support & Resistance (Rolling Window Extremes)
        df['resistance'] = high.rolling(window=20).max()
        df['support'] = low.rolling(window=20).min()
        
        # 6. Price Action Logic
        # Breakout: Current close above previous resistance
        df['breakout'] = (close > df['resistance'].shift(1)).astype(int)
        
        # Volume Confirmation: Volume > 1.5x average
        df['vol_confirm'] = (volume > volume.rolling(20).mean() * 1.5).astype(int)
        
        # Cleanup NaN values created by indicators
        return df.fillna(method='bfill').fillna(method='ffill')
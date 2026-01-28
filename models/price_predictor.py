import pandas as pd

class PricePredictor:
    def predict_next_bias(self, df):
        if df.empty:
            return {"direction": "NEUTRAL", "confidence": 0.0, "target_price": 0.0}
            
        last_row = df.iloc[-1]
        
        # Logic Variables
        ema_9 = last_row['ema_9']
        ema_50 = last_row['ema_50']
        rsi = last_row['rsi']
        close = last_row['close']
        
        score = 0
        direction = "NEUTRAL"
        
        # --- BUY LOGIC ---
        if ema_9 > ema_50: score += 1      # Golden Cross
        if rsi > 40 and rsi < 70: score += 1 # Healthy Momentum
        if close > last_row['open']: score += 1 # Green Candle
        
        # --- SELL LOGIC ---
        if ema_9 < ema_50: score -= 1      # Death Cross
        if rsi > 70: score -= 1            # Overbought
        if close < last_row['open']: score -= 1 # Red Candle
        
        # Decision
        if score >= 2:
            direction = "UP"
            confidence = 0.85
            target = last_row['resistance']
        elif score <= -2:
            direction = "DOWN"
            confidence = 0.85
            target = last_row['support']
        else:
            direction = "SIDEWAYS"
            confidence = 0.40
            target = close
            
        return {
            "direction": direction,
            "confidence": confidence,
            "target_price": round(target, 2)
        }
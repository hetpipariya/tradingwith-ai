import pandas as pd

class PricePredictor:
    def predict_next_bias(self, df):
        if df.empty:
            return {"direction": "NEUTRAL", "confidence": 0.0, "target_price": 0.0}
            
        last_row = df.iloc[-1]
        
        
        ema_9 = last_row['ema_9']
        ema_50 = last_row['ema_50']
        rsi = last_row['rsi']
        close = last_row['close']
        
        score = 0
        direction = "NEUTRAL"
        
        
        if ema_9 > ema_50: score += 1      
        if rsi > 40 and rsi < 70: score += 1 
        if close > last_row['open']: score += 1 
        
        
        if ema_9 < ema_50: score -= 1      
        if rsi > 70: score -= 1            
        if close < last_row['open']: score -= 1 
        
        
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
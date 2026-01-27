import joblib
import numpy as np
import pandas as pd
import os

# --- PATH CONFIGURATION ---
# credentials.py ની જરૂર નથી, આપણે પાથ અહીં જ બનાવી લઈએ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "price_model.pkl")

class PricePredictor:
    """Inference engine only. Separation of training and prediction."""
    
    def __init__(self):
        self.model = self.load_model()
        self.feature_cols = ['ema_9', 'ema_21', 'rsi', 'atr', 'vwap', 'breakout', 'vol_confirm']

    def load_model(self):
        try:
            return joblib.load(MODEL_PATH)
        except FileNotFoundError:
            # જો મોડેલ ના મળે તો (Cloud પર કદાચ ટ્રેન ના થયું હોય)
            return None
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def predict_next_bias(self, df: pd.DataFrame):
        # જો મોડેલ ના હોય અથવા ડેટા ના હોય તો Safe Return
        if self.model is None or df.empty:
            return {"direction": "NEUTRAL", "confidence": 0.0, "target_price": 0.0}
        
        try:
            # Take the most recent data point
            latest_features = df[self.feature_cols].tail(1)
            
            # Prediction Logic
            prob = self.model.predict_proba(latest_features)[0]
            prediction = self.model.predict(latest_features)[0]
            
            direction = "UP" if prediction == 1 else "DOWN"
            confidence = prob[1] if prediction == 1 else prob[0]
            
            # Simple ATR-based target calculation
            current_price = df['close'].iloc[-1]
            atr = df['atr'].iloc[-1]
            target = current_price + (atr * 1.5) if direction == "UP" else current_price - (atr * 1.5)
            
            return {
                "direction": direction,
                "confidence": round(float(confidence), 2),
                "target_price": round(float(target), 2)
            }
        except Exception as e:
            print(f"Prediction Error: {e}")
            return {"direction": "NEUTRAL", "confidence": 0.0, "target_price": 0.0}
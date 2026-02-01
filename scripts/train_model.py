import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
from sklearn.ensemble import RandomForestClassifier
from utils.data_loader import DataLoader
from features.feature_engineering import FeatureEngine
from credentials import MODEL_PATH

def run_training():
    print("Starting Model Training...")
    
    df = DataLoader.fetch_ohlcv("NIFTY", limit=1000)
    df = FeatureEngine.apply_indicators(df)
    
    
    df['target'] = (df['close'].shift(-2) > df['close']).astype(int)
    
    
    features = ['ema_9', 'ema_21', 'rsi', 'atr', 'vwap', 'breakout', 'vol_confirm']
    X = df[features].iloc[:-2]
    y = df['target'].iloc[:-2]
    
    
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X, y)
    
    
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    run_training()
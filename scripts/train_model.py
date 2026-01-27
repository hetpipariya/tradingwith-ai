import sys
import os
# Add root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import joblib
from sklearn.ensemble import RandomForestClassifier
from utils.data_loader import DataLoader
from features.feature_engineering import FeatureEngine
from credentials import MODEL_PATH

def run_training():
    print("Starting Model Training...")
    # 1. Get Data
    df = DataLoader.fetch_ohlcv("NIFTY", limit=1000)
    df = FeatureEngine.apply_indicators(df)
    
    # 2. Define Target (10 mins = 2 bars of 5 min data)
    df['target'] = (df['close'].shift(-2) > df['close']).astype(int)
    
    # 3. Features
    features = ['ema_9', 'ema_21', 'rsi', 'atr', 'vwap', 'breakout', 'vol_confirm']
    X = df[features].iloc[:-2]
    y = df['target'].iloc[:-2]
    
    # 4. Train
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X, y)
    
    # 5. Save
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    run_training()
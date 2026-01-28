import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Path setup to find other folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from features.feature_engineering import FeatureEngine
from models.price_predictor import PricePredictor

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="AI Pro Terminal", page_icon="🎯")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .signal-card {
        padding: 20px; border-radius: 12px; text-align: center; color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5); margin-bottom: 20px;
    }
    .metric-box {
        background-color: #1A1C24; padding: 15px; border-radius: 8px;
        border: 1px solid #30363D; text-align: center;
    }
    .bull-text { color: #00E676; font-weight: bold; }
    .bear-text { color: #FF1744; font-weight: bold; }
    .neu-text { color: #FFC107; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def load_ui():
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎯 Pro Signals")
        
        # Load Pipeline Data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", "metadata", "symbols.csv")
        
        if not os.path.exists(csv_path):
            st.error("⚠️ Run pipeline.py first!")
            return
            
        try:
            sym_df = pd.read_csv(csv_path)
            sym_df['token'] = sym_df['token'].astype(str)
            symbol_list = sym_df['symbol'].unique().tolist()
            selected_name = st.selectbox("Select Asset", symbol_list)
            
            row = sym_df[sym_df['symbol'] == selected_name].iloc[0]
            selected_token = row['token']
            selected_exchange = row['exchange']
            
        except Exception as e:
            st.error(f"Data Error: {e}")
            st.stop()
            
        if st.button("🔄 Refresh"):
            st.rerun()

        # Login Status Check
        st.divider()
        session = DataLoader.get_session()
        if session:
            st.success("✅ System Online")
        else:
            st.error("❌ Offline (Check Secrets)")

    # --- MAIN ENGINE ---
    with st.spinner(f"Analyzing {selected_name}..."):
        df_raw = DataLoader.fetch_ohlcv(selected_token, selected_exchange)
    
    if df_raw.empty:
        st.warning("⚠️ No Data Available. Market might be closed.")
        st.stop()

    df = FeatureEngine.apply_indicators(df_raw)
    predictor = PricePredictor()
    pred = predictor.predict_next_bias(df)

    # --- SIGNAL LOGIC ---
    confidence = pred['confidence']
    direction = pred['direction']
    
    if confidence < 0.60:
        signal = "HOLD / WAIT"
        sig_color = "#FFC107"
        bg_gradient = "linear-gradient(90deg, #332f00 0%, #665c00 100%)"
    elif direction == "UP":
        signal = "STRONG BUY"
        sig_color = "#00E676"
        bg_gradient = "linear-gradient(90deg, #00331a 0%, #006633 100%)"
    else:
        signal = "STRONG SELL"
        sig_color = "#FF1744"
        bg_gradient = "linear-gradient(90deg, #33000b 0%, #660016 100%)"

    # --- DISPLAY UI ---
    curr_close = df['close'].iloc[-1]
    
    # Hero Section
    st.markdown(f"""
    <div class="signal-card" style="background: {bg_gradient}; border: 2px solid {sig_color};">
        <h3 style="margin:0; color: #ccc;">AI RECOMMENDATION</h3>
        <h1 style="font-size: 50px; margin: 10px 0; color: {sig_color};">{signal}</h1>
        <div style="display: flex; justify-content: space-around;">
            <div>Target: <b>₹{pred['target_price']}</b></div>
            <div>Confidence: <b>{int(confidence*100)}%</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chart
    col_chart, col_data = st.columns([3, 1])
    
    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df['ema_9'], line=dict(color='cyan', width=1), name="EMA 9"))
        fig.add_trace(go.Scatter(x=df.index, y=df['ema_50'], line=dict(color='orange', width=1), name="EMA 50"))
        
        # Support/Resistance Lines
        fig.add_hline(y=df['resistance'].iloc[-1], line_dash="dash", line_color="red", annotation_text="RES")
        fig.add_hline(y=df['support'].iloc[-1], line_dash="dash", line_color="green", annotation_text="SUP")
        
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_data:
        st.subheader("📊 Key Levels")
        st.markdown(f"""
        <div class="metric-box">
            <span class="bear-text">RES: ₹{df['resistance'].iloc[-1]:.2f}</span><br><br>
            <span class="neu-text">LTP: ₹{curr_close:.2f}</span><br><br>
            <span class="bull-text">SUP: ₹{df['support'].iloc[-1]:.2f}</span>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    load_ui()
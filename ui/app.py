import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from features.feature_engineering import FeatureEngine
from models.price_predictor import PricePredictor

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="AI Pro Terminal", page_icon="🎯")

# --- CSS STYLING (PRO LOOK) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    
    /* Signal Card */
    .signal-card {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    
    /* Metrics */
    .metric-box {
        background-color: #1A1C24;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363D;
        text-align: center;
    }

    /* Text Helpers */
    .bull-text { color: #00E676; font-weight: bold; }
    .bear-text { color: #FF1744; font-weight: bold; }
    .neu-text { color: #FFC107; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def get_price_action_comment(df, curr_price, res, supp):
    """Generates Smart Price Action Commentary"""
    comments = []
    
    # 1. Zone Analysis
    dist_to_res = (res - curr_price) / curr_price
    dist_to_sup = (curr_price - supp) / curr_price
    
    if dist_to_res < 0.005: # Less than 0.5% away
        comments.append("⚠️ Testing Resistance Zone")
    elif dist_to_sup < 0.005:
        comments.append("✅ Testing Support Zone")
    
    # 2. Candle Analysis
    last_open = df['open'].iloc[-1]
    if curr_price > last_open:
        comments.append("🕯️ Current Candle is Bullish (Green)")
    else:
        comments.append("🕯️ Current Candle is Bearish (Red)")
        
    # 3. RSI Context
    rsi = df['rsi'].iloc[-1]
    if rsi > 70: comments.append("🔥 Market is Overbought (Be Careful)")
    elif rsi < 30: comments.append("❄️ Market is Oversold (Bounce Likely)")
    
    return comments

def load_ui():
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎯 Pro Signals")
        
        # Load Pipeline Data
        csv_path = os.path.join("data", "metadata", "symbols.csv")
        if not os.path.exists(csv_path):
            st.error("⚠️ Run pipeline.py first!")
            st.stop()
            
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

    # --- MAIN ENGINE ---
    with st.spinner(f"Analyzing {selected_name}..."):
        df_raw = DataLoader.fetch_ohlcv(selected_token, selected_exchange)
    
    if df_raw.empty:
        st.error("⚠️ No Data. Market might be closed.")
        st.stop()

    df = FeatureEngine.apply_indicators(df_raw)
    predictor = PricePredictor()
    pred = predictor.predict_next_bias(df)

    # --- SIGNAL LOGIC (CORE UPDATE) ---
    confidence = pred['confidence']
    direction = pred['direction']
    
    # Logic: Only BUY/SELL if confidence > 60%, else HOLD
    if confidence < 0.60:
        signal = "HOLD / WAIT"
        sig_color = "#FFC107" # Yellow
        action_text = "Market is choppy. Stay out."
        bg_gradient = "linear-gradient(90deg, #332f00 0%, #665c00 100%)"
    elif direction == "UP":
        signal = "STRONG BUY"
        sig_color = "#00E676" # Green
        action_text = "Bullish momentum detected."
        bg_gradient = "linear-gradient(90deg, #00331a 0%, #006633 100%)"
    else:
        signal = "STRONG SELL"
        sig_color = "#FF1744" # Red
        action_text = "Bearish pressure detected."
        bg_gradient = "linear-gradient(90deg, #33000b 0%, #660016 100%)"

    # --- UI LAYOUT ---
    
    # 1. HEADER & PRICE
    curr_close = df['close'].iloc[-1]
    diff = curr_close - df['close'].iloc[-2]
    pct = (diff / df['close'].iloc[-2]) * 100
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"## {selected_name}")
    with c2:
        st.metric("LTP", f"₹{curr_close:.2f}", f"{diff:.2f} ({pct:.2f}%)")
        
    st.divider()

    # 2. HERO SECTION: THE SIGNAL CARD
    st.markdown(f"""
    <div class="signal-card" style="background: {bg_gradient}; border: 2px solid {sig_color};">
        <h3 style="margin:0; color: #ccc;">AI RECOMMENDATION</h3>
        <h1 style="font-size: 60px; margin: 10px 0; color: {sig_color}; text-shadow: 0 0 10px {sig_color};">
            {signal}
        </h1>
        <p style="font-size: 18px;">{action_text}</p>
        <hr style="border-color: rgba(255,255,255,0.2);">
        <div style="display: flex; justify-content: space-around;">
            <div>
                <small>Confidence</small><br>
                <b style="font-size: 24px;">{int(confidence*100)}%</b>
            </div>
            <div>
                <small>Target Price</small><br>
                <b style="font-size: 24px;">₹{pred['target_price']}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. PRICE ACTION & CHART
    col_chart, col_pa = st.columns([2, 1])
    
    with col_chart:
        # Candlestick Chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name="Price"
        ))
        
        # Overlays
        fig.add_trace(go.Scatter(x=df.index, y=df['ema_9'], line=dict(color='cyan', width=1), name="EMA 9"))
        fig.add_trace(go.Scatter(x=df.index, y=df['ema_50'], line=dict(color='orange', width=1), name="EMA 50"))
        
        # S/R Zones
        fig.add_hline(y=df['resistance'].iloc[-1], line_dash="dash", line_color="red", annotation_text="RESISTANCE")
        fig.add_hline(y=df['support'].iloc[-1], line_dash="dash", line_color="green", annotation_text="SUPPORT")
        
        fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_pa:
        st.subheader("🧠 Price Action")
        
        # Dynamic Comments
        res_level = df['resistance'].iloc[-1]
        sup_level = df['support'].iloc[-1]
        pa_comments = get_price_action_comment(df, curr_close, res_level, sup_level)
        
        for comment in pa_comments:
            st.info(comment)
            
        st.markdown("### 📊 Key Levels")
        st.markdown(f"""
        <div class="metric-box">
            <span class="bear-text">Res: ₹{res_level:.2f}</span>
            <hr style="margin: 5px 0; border-color: #333;">
            <span class="neu-text">LTP: ₹{curr_close:.2f}</span>
            <hr style="margin: 5px 0; border-color: #333;">
            <span class="bull-text">Sup: ₹{sup_level:.2f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Trend Meter
        ema_bullish = df['ema_9'].iloc[-1] > df['ema_50'].iloc[-1]
        st.markdown("### 🌊 Trend")
        if ema_bullish:
            st.success("Short Term: BULLISH (Up)")
        else:
            st.error("Short Term: BEARISH (Down)")

    # Bottom Data
    with st.expander("🔎 Raw Data View"):
        st.dataframe(df.tail(5))

if __name__ == "__main__":
    load_ui()
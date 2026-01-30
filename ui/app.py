import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

# --- 1. PATH SETUP (CRITICAL FIX) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from utils.data_loader import DataLoader
    from features.feature_engineering import FeatureEngine
except ImportError as e:
    st.error(f"System Error: {e}. Please check folder structure.")
    st.stop()

# Page Config
st.set_page_config(layout="wide", page_title="AI Trading", page_icon="📈")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    
    .status-badge {
        padding: 8px 15px; border-radius: 5px; font-weight: bold; font-size: 14px;
        margin-bottom: 20px; text-align: center; width: 100%;
    }
    .connected { background-color: #00E676; color: black; border: 1px solid #00b359; }
    .disconnected { background-color: #FF1744; color: white; border: 1px solid #b3002d; }

    .signal-card {
        padding: 15px; border-radius: 10px; text-align: center; color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 10px; border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR & CONNECTION ---
with st.sidebar:
    st.title("🚀 Pro Signals")
    
    api_session = DataLoader.get_session()
    
    if api_session:
        st.markdown('<div class="status-badge connected">✅ Angel One: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge disconnected">❌ Angel One: Disconnected</div>', unsafe_allow_html=True)

    if not api_session:
        st.warning("⚠️ Broker Disconnected")
    
    if api_session:
        # CSV Path Fix using root_dir
        csv_path = os.path.join(root_dir, 'data', 'metadata', 'symbols.csv')
        
        if os.path.exists(csv_path):
            df_symbols = pd.read_csv(csv_path)
            watchlist = dict(zip(df_symbols['symbol'], df_symbols['token']))
            
            asset = st.selectbox("Select Asset", list(watchlist.keys()))
            interval = st.radio("Interval", ["3min", "5min", "10min", "15min"], index=1)
            
            st.divider()
            st.caption("⚙️ Chart Settings")
            show_ema = st.checkbox("EMA 9 & 50", value=True)
            show_supertrend = st.checkbox("Supertrend", value=True)
            
            if st.button("🔄 Refresh"): st.rerun()
        else:
            st.error("⚠️ symbols.csv missing!")
            st.stop()

# --- 3. MAINTENANCE SCREEN ---
if not api_session:
    st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; text-align: center;">
            <h1 style="color: #FF1744; font-size: 40px;">⚠️ System Maintenance</h1>
            <h3 style="color: #aaa;">Angel One API Connection Failed.</h3>
            <p>Please check your API Key and Credentials.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 4. MAIN ENGINE & GRAPH ---
tf_map = {"3min": "THREE_MINUTE", "5min": "FIVE_MINUTE", "10min": "TEN_MINUTE", "15min": "FIFTEEN_MINUTE"}
df = DataLoader.fetch_ohlcv(watchlist[asset], tf_map[interval])

if df.empty:
    st.info(f"⏳ Waiting for market data: {asset}...")
    st.stop()

# Apply Indicators
try:
    df = FeatureEngine.apply_indicators(df)
except Exception as e:
    st.error(f"Calculation Error: {e}")
    st.stop()

# Signal Logic
if len(df) > 0:
    last_row = df.iloc[-1]
    rsi = last_row['rsi']
    close = last_row['close']
    is_uptrend = last_row['in_uptrend']
    
    if is_uptrend and rsi > 55:
        sig, color = "STRONG BUY 🚀", "#00E676"
    elif not is_uptrend and rsi < 45:
        sig, color = "STRONG SELL 🔻", "#FF1744"
    else:
        sig, color = "WAIT / SIDEWAYS ⚠️", "#FF9800"

    # Signal Card
    st.markdown(f"""
        <div class="signal-card" style="border: 1px solid {color};">
            <h2 style="margin:0; color: {color};">{asset}: {sig}</h2>
            <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                <span>CMP: <b>{close}</b></span>
                <span>RSI: <b>{round(rsi, 2)}</b></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

 # --- 5. ULTRA CLEAN TRADING GRAPH (Fix: Only Price & Crosshair) ---
    display_df = df.tail(100)

    # 3 Rows Layout
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.0, 
        row_heights=[0.7, 0.15, 0.15]
    )

    # 1. CANDLESTICK (Main Price)
    fig.add_trace(go.Candlestick(
        x=display_df.index, 
        open=display_df['open'], high=display_df['high'],
        low=display_df['low'], close=display_df['close'], 
        name="", # નામ ખાલી રાખ્યું જેથી Tooltip માં કચરો ન આવે
        increasing_line_color='#089981', decreasing_line_color='#F23645',
        # 'text' કાઢી નાખ્યું એટલે ડબલ ભાવ નહિ દેખાય
        # ખાલી OHLC (Open, High, Low, Close) જ દેખાશે
    ), row=1, col=1)

    # 2. INDICATORS (Hidden from Tooltip)
    if show_ema:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_9'], 
                                 line=dict(color='#2962FF', width=1), 
                                 hoverinfo='skip'), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_50'], 
                                 line=dict(color='#FF9800', width=1), 
                                 hoverinfo='skip'), row=1, col=1)

    if show_supertrend:
        st_color = ['#00E676' if x else '#FF1744' for x in display_df['in_uptrend']]
        fig.add_trace(go.Scatter(
            x=display_df.index, y=display_df['supertrend'], 
            mode='markers', marker=dict(color=st_color, size=3), 
            hoverinfo='skip'), row=1, col=1)

    # 3. VOLUME
    vol_colors = ['rgba(8, 153, 129, 0.5)' if c >= o else 'rgba(242, 54, 69, 0.5)' 
                  for o, c in zip(display_df['open'], display_df['close'])]
    fig.add_trace(go.Bar(x=display_df.index, y=display_df['volume'], 
                         marker_color=vol_colors, hoverinfo='skip'), row=2, col=1)

    # 4. RSI
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['rsi'], 
                             line=dict(color='#B39DDB', width=1.5), 
                             hoverinfo='skip'), row=3, col=1)
    
    fig.add_hline(y=70, line_dash="dot", line_color="#F23645", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#089981", row=3, col=1)

    # --- LAYOUT SETTINGS ---
    fig.update_layout(
        height=600, 
        template="plotly_dark",
        paper_bgcolor="#131722", plot_bgcolor="#131722",
        margin=dict(l=0, r=50, t=10, b=0),
        
        # આનાથી Tooltip ખાલી એક જ જગ્યાએ દેખાશે (Mouse પાસે)
        hovermode='x', 
        dragmode='pan',
        showlegend=False,
        
        # Tooltip Style Clean Up
        hoverlabel=dict(
            bgcolor="#1e222d",
            font_size=14,
            font_family="Monospace"
        )
    )

    # X-AXIS (Crosshair Lines)
    fig.update_xaxes(
        showgrid=False, 
        showspikes=True, spikemode='across', spikesnap='cursor',
        spikethickness=1, spikecolor='rgba(255,255,255,0.3)',
        row=3, col=1
    )
    fig.update_xaxes(showticklabels=False, showspikes=True, spikemode='across', row=1, col=1)
    fig.update_xaxes(showticklabels=False, showspikes=True, spikemode='across', row=2, col=1)

    # Y-AXIS (Price Cursor Label)
    fig.update_yaxes(
        side='right', 
        showgrid=True, gridcolor='rgba(255,255,255,0.1)',
        fixedrange=False,
        
        # આ સેટિંગથી તમે જ્યાં Arrow રાખશો ત્યાંની જ પ્રાઈસ દેખાશે
        showspikes=True, 
        spikemode='across',
        spikesnap='cursor', # Cursor ની લાઈનમાં ભાવ દેખાશે
        spikethickness=1,
        spikecolor='rgba(255,255,255,0.3)',
        
        row=1, col=1
    )
    
    fig.update_yaxes(showticklabels=False, showgrid=False, row=2, col=1)
    fig.update_yaxes(side='right', range=[0, 100], row=3, col=1)

    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True, 
        'displayModeBar': False,
        'staticPlot': False
    })
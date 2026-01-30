import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

# --- PATH FIX ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_loader import DataLoader
from features.feature_engineering import FeatureEngine

# Mobile Friendly Layout
st.set_page_config(layout="wide", page_title="Tradingwith-Ai", page_icon="🚀")

# --- CSS STYLING (Mobile Responsive) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    
    /* Mobile Responsive Card */
    .signal-card {
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5); 
        margin-bottom: 10px; 
        border: 1px solid #333;
    }
    
    /* Small adjustments for mobile text */
    @media only screen and (max-width: 600px) {
        .signal-card h2 { font-size: 20px !important; }
        .signal-card span { font-size: 14px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚀 Pro Signals")
    
    # CSV Loading Logic
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'metadata', 'symbols.csv')
    if os.path.exists(csv_path):
        df_symbols = pd.read_csv(csv_path)
        watchlist = dict(zip(df_symbols['symbol'], df_symbols['token']))
    else:
        st.error("⚠️ symbols.csv missing!")
        st.stop()

    asset = st.selectbox("Select Asset", list(watchlist.keys()))
    interval = st.radio("Interval", ["3min", "5min", "10min", "15min"], index=1)
    
    st.divider()
    st.caption("⚙️ Active Indicators")
    show_ema = st.checkbox("EMA 9 & 50", value=True)
    show_supertrend = st.checkbox("Supertrend", value=True)
    show_bb = st.checkbox("Bollinger Bands")
    show_vwap = st.checkbox("VWAP")
    show_volume = st.checkbox("Volume", value=True)
    show_rsi = st.checkbox("RSI Panel", value=True)
    
    if st.button("🔄 Refresh Data"): st.rerun()

# --- MAIN ENGINE ---
tf_map = {"3min": "THREE_MINUTE", "5min": "FIVE_MINUTE", "10min": "TEN_MINUTE", "15min": "FIFTEEN_MINUTE"}
df = DataLoader.fetch_ohlcv(watchlist[asset], tf_map[interval])

if df.empty:
    st.warning(f"Waiting for market data: {asset}...")
    st.stop()

# ગણતરી FeatureEngine માં
df = FeatureEngine.apply_indicators(df)

# --- SIGNAL CARD (Mobile Friendly) ---
if len(df) > 0:
    rsi_val = df['rsi'].iloc[-1]
    ltp = df['close'].iloc[-1]
    is_uptrend = df['in_uptrend'].iloc[-1]
    
    if rsi_val > 70:
        sig, color = "SELL", "#FF1744"
    elif rsi_val < 30:
        sig, color = "BUY", "#00E676"
    elif is_uptrend:
        sig, color = "BULLISH", "#00E676"
    else:
        sig, color = "BEARISH", "#FF1744"

    st.markdown(f"""
        <div class="signal-card" style="border: 1px solid {color};">
            <h2 style="margin:0; color: {color};">{asset}: {sig}</h2>
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; margin-top: 5px; font-size: 16px;">
                <span style="margin: 5px;">CMP: <b>{ltp}</b></span>
                <span style="margin: 5px;">Trend: <b>{'UP' if is_uptrend else 'DOWN'}</b></span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- PLOTLY GRAPH ---
    display_df = df.tail(150) # Mobile પર થોડો વધારે ડેટા લોડ કરીએ જેથી ઝૂમ કરવા મળે

    # Dynamic Rows
    rows = 1
    row_heights = [1.0]
    if show_volume and show_rsi:
        rows = 3
        row_heights = [0.6, 0.2, 0.2] # Mobile પર મેઈન ચાર્ટને થોડી વધારે જગ્યા આપી
    elif show_volume or show_rsi:
        rows = 2
        row_heights = [0.75, 0.25]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

    # 1. Price Candle
    fig.add_trace(go.Candlestick(
        x=display_df.index, open=display_df['open'], high=display_df['high'],
        low=display_df['low'], close=display_df['close'], name="Price",
        increasing_line_color='#089981', decreasing_line_color='#F23645'
    ), row=1, col=1)

    # 2. Indicators
    if show_supertrend:
        st_green = display_df[display_df['in_uptrend']]
        fig.add_trace(go.Scatter(x=st_green.index, y=st_green['supertrend'], mode='markers', marker=dict(color='green', size=2), name="ST Up"), row=1, col=1)
        st_red = display_df[~display_df['in_uptrend']]
        fig.add_trace(go.Scatter(x=st_red.index, y=st_red['supertrend'], mode='markers', marker=dict(color='red', size=2), name="ST Down"), row=1, col=1)

    if show_bb:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['bb_upper'], name="BB Up", line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['bb_lower'], name="BB Low", line=dict(color='gray', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(255,255,255,0.05)'), row=1, col=1)

    if show_ema:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_9'], name="EMA 9", line=dict(color='#2962FF', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_50'], name="EMA 50", line=dict(color='#FF9800', width=1)), row=1, col=1)
    
    if show_vwap:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['vwap'], name="VWAP", line=dict(color='#E11E63', width=1)), row=1, col=1)

    # --- SUBPLOTS ---
    current_row = 2
    if show_volume:
        colors = ['#F23645' if c < o else '#089981' for o, c in zip(display_df['open'], display_df['close'])]
        fig.add_trace(go.Bar(x=display_df.index, y=display_df['volume'], name="Vol", marker_color=colors), row=current_row, col=1)
        current_row += 1

    if show_rsi:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['rsi'], name="RSI", line=dict(color='#9C27B0', width=2)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=current_row, col=1)

    # --- LAYOUT (Mobile Optimized with ZOOM FIX) ---
    fig.update_layout(
        height=600, # Mobile પર બહુ લાંબો સ્ક્રોલ ન થાય તે માટે હાઈટ એડજસ્ટ કરી
        template="plotly_dark", 
        xaxis_rangeslider_visible=False,
        dragmode='pan', # Mobile માટે Pan બેસ્ટ છે
        margin=dict(l=0, r=0, t=0, b=0), 
        hovermode='x unified',
        paper_bgcolor="#0E1117", 
        plot_bgcolor="#0E1117",
        autosize=True
    )
    
    # CRITICAL FIX: fixedrange=True for Y-Axis
    # આનાથી જ્યારે તું Pinch કરીશ ત્યારે ગ્રાફ ચપટો નહીં થાય, ખાલી ટાઈમ ઝૂમ થશે.
    fig.update_yaxes(fixedrange=True, showspikes=True, spikemode='across', spikesnap='cursor', showgrid=True, gridcolor='#1e222d', side='right')
    fig.update_xaxes(fixedrange=False, showspikes=True, spikemode='across', spikesnap='cursor', showgrid=True, gridcolor='#1e222d')

    # Mobile Config
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,  # Pinch to Zoom ચાલુ
        'displayModeBar': False, # મોબાઈલમાં ઉપરના બટન્સ નડતરરૂપ હોય છે, તે કાઢી નાખ્યા
        'responsive': True 
    })
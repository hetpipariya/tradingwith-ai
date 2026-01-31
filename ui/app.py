import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os
import requests
import time

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from utils.data_loader import DataLoader
    from features.feature_engineering import FeatureEngine
except ImportError as e:
    st.error(f"System Error: {e}")
    st.stop()

st.set_page_config(layout="wide", page_title="Pro Trader", page_icon="📈")

# --- STATE ---
if 'balance' not in st.session_state: st.session_state['balance'] = 10000.0
if 'positions' not in st.session_state: st.session_state['positions'] = {}
if 'trade_log' not in st.session_state: st.session_state['trade_log'] = []

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #131722; }
    .block-container { padding-top: 3.5rem; padding-bottom: 5rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    .status-badge { padding: 5px; border-radius: 4px; font-size: 12px; margin-bottom: 10px; text-align: center; }
    .connected { background-color: #00E676; color: black; }
    .disconnected { background-color: #FF1744; color: white; }
    .metric-card { background: #1e222d; padding: 10px; border-radius: 8px; border: 1px solid #2a2e39; color: white; text-align: center; font-size: 14px; }
    .profit { color: #00E676; } .loss { color: #FF1744; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Algo Controls")
    trading_mode = st.toggle("🎮 Paper Trading", value=False)
    
    if 'smart_api' not in st.session_state: st.session_state['smart_api'] = None
    api_session = DataLoader.get_session()
    
    if api_session:
        st.markdown('<div class="status-badge connected">● API Live</div>', unsafe_allow_html=True)
        csv_path = os.path.join(root_dir, 'symbols.csv')
        if os.path.exists(csv_path):
            df_symbols = pd.read_csv(csv_path)
            watchlist = dict(zip(df_symbols['symbol'], df_symbols['token']))
            asset = st.selectbox("Symbol", list(watchlist.keys()))
            interval = st.radio("TF", ["3min", "5min", "10min", "15min"], index=1, horizontal=True)
            
            st.divider()
            st.caption("OVERLAYS")
            show_ema = st.checkbox("EMA 9/50", value=True)
            show_bb = st.checkbox("Bollinger Bands", value=False)
            show_psar = st.checkbox("Parabolic SAR", value=False)
            show_supertrend = st.checkbox("Supertrend", value=True)
            show_scalp = st.checkbox("🔥 SCALP SIGNALS", value=True)
            
            st.caption("OSCILLATORS")
            show_rsi = st.checkbox("RSI", value=True)
            show_macd = st.checkbox("MACD", value=True)
            
            if st.button("Refresh", use_container_width=True): st.rerun()
    else:
        st.markdown('<div class="status-badge disconnected">● Disconnected</div>', unsafe_allow_html=True)
        st.stop()

# --- DATA ---
tf_map = {"3min": "THREE_MINUTE", "5min": "FIVE_MINUTE", "10min": "TEN_MINUTE", "15min": "FIFTEEN_MINUTE"}
df = DataLoader.fetch_ohlcv(watchlist[asset], tf_map[interval])

if df.empty: st.warning("Data Loading..."); st.stop()

try:
    df = FeatureEngine.apply_indicators(df)
except: pass

last = df.iloc[-1]
rsi = last['rsi']
price = last['close']

# --- SCALP SIGNAL ---
scalp_signal = "NONE"
if 'scalp_buy' in last and last['scalp_buy']: scalp_signal = "SCALP BUY 🚀"
elif 'scalp_sell' in last and last['scalp_sell']: scalp_signal = "SCALP SELL 🔻"

# --- ALERT BAR ---
col = "#00E676" if "BUY" in scalp_signal else "#FF1744" if "SELL" in scalp_signal else "#FF9800"
msg = scalp_signal if scalp_signal != "NONE" else f"LTP: {price}"
st.markdown(f"""
    <div style="position: fixed; bottom: 10px; right: 10px; background: #1e222d; padding: 10px; border-radius: 8px; border-left: 4px solid {col}; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.5); z-index: 100; font-size: 14px;">
        <div style="font-weight:bold;">{msg}</div>
        <div style="font-size: 10px; opacity: 0.8;">MACD: {round(last.get('macd_hist', 0), 2)}</div>
    </div>
""", unsafe_allow_html=True)

# --- CHART LAYOUT ---
display_df = df.tail(100)
row_heights = [0.55, 0.15, 0.15, 0.15] if show_macd else [0.7, 0.15, 0.15]

fig = make_subplots(
    rows=4 if show_macd else 3, 
    cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.02, 
    row_heights=row_heights
)

# 1. CANDLESTICK
fig.add_trace(go.Candlestick(x=display_df.index, open=display_df['open'], high=display_df['high'], low=display_df['low'], close=display_df['close'], name="Price", increasing_line_color='#089981', decreasing_line_color='#F23645'), row=1, col=1)

# EMAs (With Safety Check)
if show_ema:
    if 'ema_9' in display_df:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_9'], line=dict(color='#2962FF', width=1), name="EMA 9"), row=1, col=1)
    if 'ema_50' in display_df:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_50'], line=dict(color='#FFEB3B', width=1.5), name="EMA 50"), row=1, col=1)

# Bollinger Bands (With Safety Check)
if show_bb and 'bb_upper' in display_df:
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['bb_upper'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1), name="BB Up"), row=1, col=1)
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['bb_lower'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1), fill='tonexty', fillcolor='rgba(255, 255, 255, 0.05)', name="BB Low"), row=1, col=1)

# PSAR
if show_psar and 'psar' in display_df:
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['psar'], mode='markers', marker=dict(color='white', size=2), name="PSAR"), row=1, col=1)

# Supertrend
if show_supertrend and 'supertrend' in display_df:
    st_colors = ['#00E676' if x else '#FF1744' for x in display_df['in_uptrend']]
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['supertrend'], mode='markers', marker=dict(color=st_colors, size=2), name="ST"), row=1, col=1)

# Scalp Signals
if show_scalp and 'scalp_buy' in display_df:
    buys = display_df[display_df['scalp_buy']]
    if not buys.empty: fig.add_trace(go.Scatter(x=buys.index, y=buys['low']*0.998, mode='markers', marker=dict(symbol='triangle-up', size=10, color='#00E676'), name="Buy"), row=1, col=1)
    sells = display_df[display_df['scalp_sell']]
    if not sells.empty: fig.add_trace(go.Scatter(x=sells.index, y=sells['high']*1.002, mode='markers', marker=dict(symbol='triangle-down', size=10, color='#FF1744'), name="Sell"), row=1, col=1)

# 2. VOLUME
vol_colors = ['rgba(8, 153, 129, 0.5)' if c >= o else 'rgba(242, 54, 69, 0.5)' for o, c in zip(display_df['open'], display_df['close'])]
fig.add_trace(go.Bar(x=display_df.index, y=display_df['volume'], marker_color=vol_colors, name="Vol"), row=2, col=1)

# 3. RSI
fig.add_trace(go.Scatter(x=display_df.index, y=display_df['rsi'], line=dict(color='#B39DDB', width=1.5), name="RSI"), row=3, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="#F23645", row=3, col=1); fig.add_hline(y=30, line_dash="dot", line_color="#089981", row=3, col=1)

# 4. MACD
if show_macd and 'macd' in display_df:
    hist_colors = ['#00E676' if h >= 0 else '#FF1744' for h in display_df['macd_hist']]
    fig.add_trace(go.Bar(x=display_df.index, y=display_df['macd_hist'], marker_color=hist_colors, name="Hist"), row=4, col=1)
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['macd'], line=dict(color='#2962FF', width=1), name="MACD"), row=4, col=1)
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['macd_signal'], line=dict(color='#FF9800', width=1), name="Signal"), row=4, col=1)

# Layout
fig.update_layout(height=700, template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722", margin=dict(l=0, r=45, t=10, b=0), hovermode='x unified', dragmode='pan', showlegend=False, xaxis=dict(rangeslider=dict(visible=False), type="category"))
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', showline=False, fixedrange=False)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', side='right', fixedrange=False)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

# --- PAPER TRADING UI ---
if trading_mode:
    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"#### Bal: ₹{st.session_state['balance']:.0f}")
        qty = st.number_input("Qty", min_value=1, value=10, label_visibility="collapsed")
        c_buy, c_sell = st.columns(2)
        if c_buy.button("BUY 🟢", use_container_width=True):
            if price*qty <= st.session_state['balance']:
                st.session_state['balance'] -= price*qty
                st.session_state['positions'][asset] = {'qty': qty, 'avg': price}
                st.rerun()
        if c_sell.button("SELL 🔻", use_container_width=True): st.rerun()
    with c2:
        if asset in st.session_state['positions']:
            pos = st.session_state['positions'][asset]
            pnl = (price - pos['avg']) * pos['qty']
            c = "profit" if pnl>=0 else "loss"
            st.markdown(f"<div class='metric-card'>Qty: {pos['qty']} <br> <span class='{c}'>P&L: {pnl:.1f}</span></div>", unsafe_allow_html=True)
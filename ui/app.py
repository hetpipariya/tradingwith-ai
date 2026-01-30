import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os
import requests 

# PATH SETUP
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from utils.data_loader import DataLoader
    from features.feature_engineering import FeatureEngine
except ImportError as e:
    st.error(f"System Error: {e}")
    st.stop()

st.set_page_config(layout="wide", page_title="AI Trading", page_icon="📈")

# CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .status-badge { padding: 8px 15px; border-radius: 5px; font-weight: bold; font-size: 14px; margin-bottom: 20px; text-align: center; width: 100%; }
    .connected { background-color: #00E676; color: black; border: 1px solid #00b359; }
    .disconnected { background-color: #FF1744; color: white; border: 1px solid #b3002d; }
    .signal-card { padding: 15px; border-radius: 10px; text-align: center; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("🚀 Pro Signals")
    
    api_session = DataLoader.get_session()
    
    if api_session:
        st.markdown('<div class="status-badge connected">✅ Angel One: Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge disconnected">❌ Angel One: Disconnected</div>', unsafe_allow_html=True)
    
    if api_session:
        csv_path = os.path.join(root_dir, 'data', 'metadata', 'symbols.csv')
        
        # Auto-Download if missing
        if not os.path.exists(csv_path):
            with st.spinner("Downloading Symbol Data..."):
                try:
                    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
                    r = requests.get(url)
                    data = r.json()
                    df_master = pd.DataFrame(data)
                    my_list = ["IOB", "SUZLON", "UCOBANK", "NHPC", "IDEA", "JPPOWER", "YESBANK", "IRFC"]
                    filtered = []
                    for name in my_list:
                        row = df_master[(df_master['symbol'] == f"{name}-EQ") & (df_master['exch_seg'] == 'NSE')]
                        if not row.empty: filtered.append({'symbol': name, 'token': row.iloc[0]['token']})
                    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                    pd.DataFrame(filtered).to_csv(csv_path, index=False)
                    st.rerun()
                except: st.error("Download Failed"); st.stop()

        if os.path.exists(csv_path):
            df_symbols = pd.read_csv(csv_path)
            watchlist = dict(zip(df_symbols['symbol'], df_symbols['token']))
            asset = st.selectbox("Select Asset", list(watchlist.keys()))
            interval = st.radio("Interval", ["3min", "5min", "10min", "15min"], index=1)
            
            st.divider()
            st.caption("⚙️ Indicators")
            show_ema = st.checkbox("EMA 9 & 15", value=True)
            show_vwap = st.checkbox("VWAP", value=True)
            show_supertrend = st.checkbox("Supertrend", value=True)
            
            if st.button("🔄 Refresh"): st.rerun()
        else:
            st.error("symbols.csv missing")
            st.stop()

if not api_session:
    st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; text-align: center;">
            <h1 style="color: #FF1744; font-size: 40px;">⚠️ System Maintenance</h1>
            <p>Connection Failed. Check Secrets in .streamlit/secrets.toml (Local) or Dashboard (Cloud).</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# MAIN ENGINE
tf_map = {"3min": "THREE_MINUTE", "5min": "FIVE_MINUTE", "10min": "TEN_MINUTE", "15min": "FIFTEEN_MINUTE"}
df = DataLoader.fetch_ohlcv(watchlist[asset], tf_map[interval])

if df.empty:
    st.info(f"⏳ Waiting for market data: {asset}...")
    st.stop()

try:
    df = FeatureEngine.apply_indicators(df)
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

# SIGNAL
last = df.iloc[-1]
rsi = last['rsi']
is_uptrend = last['in_uptrend']

if is_uptrend and rsi > 55: sig, color = "STRONG BUY 🚀", "#00E676"
elif not is_uptrend and rsi < 45: sig, color = "STRONG SELL 🔻", "#FF1744"
else: sig, color = "SIDEWAYS ⚠️", "#FF9800"

st.markdown(f"""
    <div class="signal-card" style="border: 1px solid {color};">
        <h2 style="margin:0; color: {color};">{asset}: {sig}</h2>
        <div style="display: flex; justify-content: space-between; margin-top: 10px;">
            <span>Price: <b>{last['close']}</b></span>
            <span>RSI: <b>{round(rsi, 2)}</b></span>
        </div>
    </div>
""", unsafe_allow_html=True)

# GRAPH
display_df = df.tail(100)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.0, row_heights=[0.7, 0.15, 0.15])

# Candle
fig.add_trace(go.Candlestick(x=display_df.index, open=display_df['open'], high=display_df['high'], low=display_df['low'], close=display_df['close'], name="", increasing_line_color='#089981', decreasing_line_color='#F23645'), row=1, col=1)

# Indicators
if show_ema:
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_9'], line=dict(color='#2962FF', width=1), hoverinfo='skip', name="EMA 9"), row=1, col=1)
    # EMA 15 Added Here
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_15'], line=dict(color='#FF9800', width=1), hoverinfo='skip', name="EMA 15"), row=1, col=1)

if show_vwap:
    # VWAP Added Here
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['vwap'], line=dict(color='#E91E63', width=1, dash='dot'), hoverinfo='skip', name="VWAP"), row=1, col=1)

if show_supertrend:
    st_color = ['#00E676' if x else '#FF1744' for x in display_df['in_uptrend']]
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['supertrend'], mode='markers', marker=dict(color=st_color, size=3), hoverinfo='skip'), row=1, col=1)

# Volume
vol_colors = ['rgba(8, 153, 129, 0.5)' if c >= o else 'rgba(242, 54, 69, 0.5)' for o, c in zip(display_df['open'], display_df['close'])]
fig.add_trace(go.Bar(x=display_df.index, y=display_df['volume'], marker_color=vol_colors, hoverinfo='skip'), row=2, col=1)

# RSI
fig.add_trace(go.Scatter(x=display_df.index, y=display_df['rsi'], line=dict(color='#B39DDB', width=1.5), hoverinfo='skip'), row=3, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="#F23645", row=3, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="#089981", row=3, col=1)

# Layout
fig.update_layout(height=600, template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722", margin=dict(l=0, r=50, t=10, b=0), hovermode='x', dragmode='pan', showlegend=False, hoverlabel=dict(bgcolor="#1e222d", font_size=14))
fig.update_xaxes(showgrid=False, showspikes=True, spikemode='across', spikesnap='cursor', row=3, col=1)
fig.update_xaxes(showticklabels=False, showspikes=True, spikemode='across', row=1, col=1)
fig.update_xaxes(showticklabels=False, showspikes=True, spikemode='across', row=2, col=1)
fig.update_yaxes(side='right', showgrid=True, gridcolor='rgba(255,255,255,0.1)', fixedrange=False, showspikes=True, spikemode='across', spikesnap='cursor', row=1, col=1)
fig.update_yaxes(showticklabels=False, showgrid=False, row=2, col=1)
fig.update_yaxes(side='right', range=[0, 100], row=3, col=1)

st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
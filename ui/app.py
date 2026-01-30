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

# Set layout to wide, but we will control margins with CSS
st.set_page_config(layout="wide", page_title="Pro Trader", page_icon="📈")

# --- PAPER TRADING STATE INITIALIZATION ---
if 'balance' not in st.session_state:
    st.session_state['balance'] = 10000.0
if 'positions' not in st.session_state:
    st.session_state['positions'] = {}
if 'trade_log' not in st.session_state:
    st.session_state['trade_log'] = []

# --- CSS STYLING (MOBILE OPTIMIZED & FIXED LAYOUT) ---
st.markdown("""
    <style>
    .stApp { background-color: #131722; }
    
    /* FIX: Increased padding-top so the alert bar is visible */
    .block-container {
        padding-top: 3.5rem;
        padding-bottom: 5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }

    .status-badge { padding: 5px; border-radius: 4px; font-size: 12px; margin-bottom: 10px; text-align: center; }
    .connected { background-color: #00E676; color: black; }
    .disconnected { background-color: #FF1744; color: white; }
    
    /* ALERT ANIMATION */
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 5px rgba(255, 23, 68, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }
    .alert-box {
        padding: 10px; border-radius: 8px; text-align: center; 
        font-weight: bold; color: white; margin-bottom: 10px; 
        animation: pulse 2s infinite; border: 1px solid white;
    }
    
    /* Responsive Text for Alert */
    @media only screen and (max-width: 600px) {
        .alert-box { font-size: 14px; }
        .stButton button { width: 100%; }
    }
    @media only screen and (min-width: 601px) {
        .alert-box { font-size: 20px; }
    }

    .buy-alert { background-color: #00E676; border-color: #00E676; box-shadow: 0 0 10px #00E676; }
    .sell-alert { background-color: #FF1744; border-color: #FF1744; box-shadow: 0 0 10px #FF1744; }
    
    /* TRADING METRICS */
    .metric-card { background: #1e222d; padding: 10px; border-radius: 8px; border: 1px solid #2a2e39; color: white; text-align: center; font-size: 14px; }
    .profit { color: #00E676; }
    .loss { color: #FF1744; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Algo Controls")
    
    # Paper Trading Toggle
    st.divider()
    trading_mode = st.toggle("🎮 Paper Trading Mode", value=False)
    
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
            show_ema = st.checkbox("EMA 9/15", value=True)
            show_vwap = st.checkbox("VWAP", value=True)
            show_supertrend = st.checkbox("Supertrend", value=True)
            show_patterns = st.checkbox("Patterns", value=True)
            
            if st.button("Refresh Chart", use_container_width=True): st.rerun()
    else:
        st.markdown('<div class="status-badge disconnected">● Disconnected</div>', unsafe_allow_html=True)
        st.stop()

# --- DATA FETCHING ---
tf_map = {"3min": "THREE_MINUTE", "5min": "FIVE_MINUTE", "10min": "TEN_MINUTE", "15min": "FIFTEEN_MINUTE"}
df = DataLoader.fetch_ohlcv(watchlist[asset], tf_map[interval])

if df.empty:
    st.warning("Data Loading...")
    st.stop()

# --- FIX: Initialize variable to avoid NameError ---
detected_patterns = [] 

try:
    df = FeatureEngine.apply_indicators(df)
    detected_patterns = FeatureEngine.detect_patterns(df) if show_patterns else []
except: pass

last = df.iloc[-1]
rsi = last['rsi']
current_price = last['close']
current_vol = last['volume']
is_uptrend = last['in_uptrend']

# --- ALERT SYSTEM ---
alert_placeholder = st.empty()
signal_type = "NEUTRAL"

if is_uptrend and rsi > 55:
    signal_type = "STRONG BUY"
    alert_placeholder.markdown(f"""
        <div class="alert-box buy-alert">
            🚨 STRONG BUY: {asset} @ {current_price}
        </div>
    """, unsafe_allow_html=True)
    
elif not is_uptrend and rsi < 45:
    signal_type = "STRONG SELL"
    signal_icon = "🔻"
    alert_placeholder.markdown(f"""
        <div class="alert-box sell-alert">
            🚨 STRONG SELL: {asset} @ {current_price}
        </div>
    """, unsafe_allow_html=True)

# --- CHART PLOTTING ---
display_df = df.tail(100) 
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.65, 0.15, 0.20])

# Candle
fig.add_trace(go.Candlestick(x=display_df.index, open=display_df['open'], high=display_df['high'], low=display_df['low'], close=display_df['close'], name="Price", increasing_line_color='#089981', decreasing_line_color='#F23645'), row=1, col=1)

# Indicators
if show_ema:
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_9'], line=dict(color='#2962FF', width=1), name="EMA 9"), row=1, col=1)
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['ema_15'], line=dict(color='#FF9800', width=1), name="EMA 15"), row=1, col=1)
if show_vwap:
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['vwap'], line=dict(color='#E91E63', width=1, dash='dot'), name="VWAP"), row=1, col=1)
if show_supertrend:
    st_colors = ['#00E676' if x else '#FF1744' for x in display_df['in_uptrend']]
    fig.add_trace(go.Scatter(x=display_df.index, y=display_df['supertrend'], mode='markers', marker=dict(color=st_colors, size=2), name="ST"), row=1, col=1)
    
if show_patterns and detected_patterns:
    for pat in detected_patterns:
        x_vals = [pt[0] for pt in pat['points']]
        y_vals = [pt[1] for pt in pat['points']]
        if x_vals[0] >= display_df.index[0]:
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines+markers', line=dict(color=pat['color'], width=2), marker=dict(size=6), name=pat['name']), row=1, col=1)

# Volume & RSI
vol_colors = ['rgba(8, 153, 129, 0.5)' if c >= o else 'rgba(242, 54, 69, 0.5)' for o, c in zip(display_df['open'], display_df['close'])]
fig.add_trace(go.Bar(x=display_df.index, y=display_df['volume'], marker_color=vol_colors, name="Vol"), row=2, col=1)
fig.add_trace(go.Scatter(x=display_df.index, y=display_df['rsi'], line=dict(color='#B39DDB', width=1.5), name="RSI"), row=3, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="#F23645", row=3, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="#089981", row=3, col=1)

# Layout Optimization
fig.update_layout(
    height=550,
    template="plotly_dark", 
    paper_bgcolor="#131722", 
    plot_bgcolor="#131722", 
    margin=dict(l=0, r=45, t=10, b=0), 
    hovermode='x unified', 
    dragmode='pan', # Changed to PAN for mobile
    showlegend=False, 
    xaxis=dict(rangeslider=dict(visible=False), type="category")
)
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', showline=False)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)', side='right') 

# FIX: scrollZoom False removes mobile lag/glitch
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': False, 
    'scrollZoom': False, 
    'staticPlot': False
})

# --- PAPER TRADING UI ---
if trading_mode:
    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown(f"#### Bal: ₹{st.session_state['balance']:.0f}")
        qty = st.number_input("Qty", min_value=1, value=10, label_visibility="collapsed")
        
        col_buy, col_sell = st.columns(2)
        if col_buy.button("BUY 🟢", use_container_width=True):
            cost = current_price * qty
            if cost <= st.session_state['balance']:
                st.session_state['balance'] -= cost
                if asset in st.session_state['positions']:
                    old_qty = st.session_state['positions'][asset]['qty']
                    old_avg = st.session_state['positions'][asset]['avg']
                    new_avg = ((old_qty * old_avg) + (qty * current_price)) / (old_qty + qty)
                    st.session_state['positions'][asset] = {'qty': old_qty + qty, 'avg': new_avg}
                else:
                    st.session_state['positions'][asset] = {'qty': qty, 'avg': current_price}
                st.session_state['trade_log'].append(f"🟢 BUY {qty} {asset} @ {current_price}")
                st.rerun()
            else:
                st.error("No Funds!")

        if col_sell.button("SELL 🔻", use_container_width=True):
            if asset in st.session_state['positions'] and st.session_state['positions'][asset]['qty'] >= qty:
                revenue = current_price * qty
                st.session_state['balance'] += revenue
                st.session_state['positions'][asset]['qty'] -= qty
                if st.session_state['positions'][asset]['qty'] == 0:
                    del st.session_state['positions'][asset]
                st.session_state['trade_log'].append(f"🔻 SELL {qty} {asset} @ {current_price}")
                st.rerun()
            else:
                st.error("No Qty!")

    with c2:
        st.markdown("#### Holdings")
        if asset in st.session_state['positions']:
            pos = st.session_state['positions'][asset]
            pnl = (current_price - pos['avg']) * pos['qty']
            pnl_color = "profit" if pnl >= 0 else "loss"
            st.markdown(f"""
            <div class="metric-card">
                <div>Qty: {pos['qty']}</div>
                <div class="{pnl_color}">P&L: ₹{pnl:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No Position")
            
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state['balance'] = 10000.0
            st.session_state['positions'] = {}
            st.session_state['trade_log'] = []
            st.rerun()
            
    if st.session_state['trade_log']:
        with st.expander("📜 Trade History"):
            log_text = "\n".join(st.session_state['trade_log'][-5:])
            st.code(log_text)

else:
    # --- FLOATING SIGNAL FOOTER ---
    col = "#00E676" if "BUY" in signal_type else "#FF1744" if "SELL" in signal_type else "#FF9800"
    st.markdown(f"""
        <div style="position: fixed; bottom: 10px; right: 10px; background: #1e222d; padding: 10px; border-radius: 8px; border-left: 4px solid {col}; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.5); z-index: 100; font-size: 14px;">
            <div style="font-weight:bold;">{current_price}</div>
            <div style="font-size: 10px; opacity: 0.8;">RSI: {round(rsi, 2)}</div>
        </div>
    """, unsafe_allow_html=True)
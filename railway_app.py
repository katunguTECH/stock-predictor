import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Stock Predictor", page_icon="📈", layout="wide")
st.title("🔮 Stock Market Predictor")
st.markdown("---")

with st.sidebar:
    ticker = st.text_input("Stock Symbol", value="AAPL").upper()
    period = st.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)

if ticker:
    try:
        with st.spinner(f"Analyzing {ticker}..."):
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if len(data) < 10:
                st.error("Insufficient data")
                st.stop()
            
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MAs
            ma_20 = data['Close'].rolling(20).mean().iloc[-1]
            ma_50 = data['Close'].rolling(50).mean().iloc[-1]
            
            # Volume ratio
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            volume_ratio = data['Volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1
            
            # Scoring
            score = 0
            if rsi < 30: score += 25
            elif rsi > 70: score -= 25
            if ma_20 > ma_50: score += 20
            else: score -= 20
            if volume_ratio > 1.2: score += 15
            elif volume_ratio < 0.8: score -= 15
            if change_pct > 0: score += 10
            else: score -= 10
            
            if score > 30: action = "🟢 BUY"
            elif score > 10: action = "🟡 ACCUMULATE"
            elif score < -30: action = "🔴 SELL / SHORT"
            elif score < -10: action = "🟠 REDUCE"
            else: action = "⚪ HOLD"
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Price", f"${current_price:.2f}", f"{change_pct:+.2f}%")
            col2.metric("RSI", f"{rsi:.1f}")
            col3.metric("Volume", f"{volume_ratio:.1f}x")
            
            if "BUY" in action:
                st.success(f"### {action}")
            elif "SELL" in action:
                st.error(f"### {action}")
            else:
                st.warning(f"### {action}")
            
            st.dataframe(data[['Close','Volume']].tail(10), use_container_width=True)
            st.caption("Disclaimer: Not financial advice.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Enter a stock symbol")
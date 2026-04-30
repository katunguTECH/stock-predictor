import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(page_title="Stock Predictor", page_icon="📈", layout="wide")
st.title("🔮 Stock Market Predictor")
st.markdown("---")

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    ticker = st.text_input("Stock Symbol", value="AAPL").upper()
    period = st.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    st.markdown("---")
    st.caption("Data Source: Yahoo Finance")

if ticker:
    try:
        with st.spinner(f"Analyzing {ticker}..."):
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if len(data) < 10:
                st.error(f"Insufficient data for {ticker}")
                st.stop()
            
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price) * 100
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MAs
            ma_20 = data['Close'].rolling(20).mean().iloc[-1]
            ma_50 = data['Close'].rolling(50).mean().iloc[-1]
            
            # Volume
            avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
            volume_ratio = data['Volume'].iloc[-1] / avg_volume if avg_volume > 0 else 1
            
            # Signals
            confidence = 0
            signals = []
            if rsi < 30:
                signals.append("✅ RSI: Oversold (Bullish)")
                confidence += 25
            elif rsi > 70:
                signals.append("❌ RSI: Overbought (Bearish)")
                confidence -= 25
            else:
                signals.append("⚖️ RSI: Neutral")
            
            if ma_20 > ma_50:
                signals.append("✅ MA: Golden Cross (Bullish)")
                confidence += 20
            else:
                signals.append("❌ MA: Death Cross (Bearish)")
                confidence -= 20
            
            if volume_ratio > 1.2:
                signals.append("✅ Volume: Above average (Strong)")
                confidence += 15
            elif volume_ratio < 0.8:
                signals.append("❌ Volume: Below average (Weak)")
                confidence -= 15
            else:
                signals.append("⚖️ Volume: Average")
            
            if change > 0:
                signals.append(f"✅ Price: +{change_pct:.2f}% (Bullish)")
                confidence += 10
            else:
                signals.append(f"❌ Price: {change_pct:.2f}% (Bearish)")
                confidence -= 10
            
            if confidence > 30:
                action = "🟢 BUY"
                rec = "Strong bullish signals - Consider entering long position"
            elif confidence > 10:
                action = "🟡 ACCUMULATE"
                rec = "Mildly bullish - Consider scaling in"
            elif confidence < -30:
                action = "🔴 SELL / SHORT"
                rec = "Strong bearish signals - Consider shorting"
            elif confidence < -10:
                action = "🟠 REDUCE"
                rec = "Mildly bearish - Consider trimming"
            else:
                action = "⚪ HOLD"
                rec = "Mixed signals - Wait for clearer direction"
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Current Price", f"", f"{change_pct:+.2f}%")
            with col2: st.metric("RSI (14)", f"{rsi:.1f}")
            with col3: st.metric("Volume Ratio", f"{volume_ratio:.1f}x")
            with col4: st.metric("Confidence", f"{abs(confidence):.0f}%")
            
            if "BUY" in action:
                st.success(f"### {action}")
            elif "SELL" in action or "SHORT" in action:
                st.error(f"### {action}")
            else:
                st.warning(f"### {action}")
            st.info(f"**Recommendation:** {rec}")
            
            st.subheader("📊 Signal Breakdown")
            for s in signals:
                st.write(s)
            
            st.subheader("📈 Recent Data")
            st.dataframe(data[['Open','High','Low','Close','Volume']].tail(10), use_container_width=True)
            
            st.markdown("---")
            st.caption("⚠️ **Disclaimer:** Educational only. Not financial advice.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("Enter a stock symbol to begin analysis")

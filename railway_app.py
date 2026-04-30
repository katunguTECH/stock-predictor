import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Predictor", layout="wide")
st.title("📈 Stock Market Predictor")

symbol = st.text_input("Symbol", "AAPL").upper()
period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=2)

if symbol:
    with st.spinner("Fetching data..."):
        try:
            data = yf.download(symbol, period=period, progress=False)
            if data.empty:
                st.error("No data found")
            else:
                st.metric("Latest Close", f"${data['Close'].iloc[-1]:.2f}")
                st.line_chart(data['Close'])
                st.dataframe(data.tail(10))
        except Exception as e:
            st.error(f"Error: {e}")
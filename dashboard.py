"""
Stock Prediction Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

# Import our predictor
from stock_predictor import StockPredictor

# Page config
st.set_page_config(
    page_title="Stock Predictor Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #00ff00;
        text-align: center;
        margin-bottom: 2rem;
    }
    .signal-buy {
        background-color: #00ff0015;
        border-left: 4px solid #00ff00;
        padding: 1rem;
        border-radius: 5px;
    }
    .signal-sell {
        background-color: #ff000015;
        border-left: 4px solid #ff0000;
        padding: 1rem;
        border-radius: 5px;
    }
    .signal-hold {
        background-color: #ffaa0015;
        border-left: 4px solid #ffaa00;
        padding: 1rem;
        border-radius: 5px;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🔮 Market Predictor Pro</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
    st.markdown("## ⚙️ Settings")
    
    # Stock input
    ticker = st.text_input("Stock Symbol", value="AAPL").upper()
    
    # Time period
    period = st.selectbox(
        "Time Period",
        ["1mo", "3mo", "6mo", "1y", "2y"],
        index=2
    )
    
    # Analysis type
    analysis_type = st.selectbox(
        "Analysis Mode",
        ["Technical Analysis", "ML Prediction", "Full Analysis"],
        index=2
    )
    
    st.markdown("---")
    st.markdown("### 📊 Quick Access")
    popular = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META"]
    for sym in popular:
        if st.button(sym, key=sym):
            ticker = sym
            st.rerun()
    
    st.markdown("---")
    st.markdown("Made with ❤️ using yfinance")

# Main content
if ticker:
    try:
        # Initialize predictor
        predictor = StockPredictor(ticker)
        
        with st.spinner(f"Fetching real-time data for {ticker}..."):
            data = predictor.fetch_data(period)
            predictor.calculate_indicators()
            if analysis_type in ["ML Prediction", "Full Analysis"]:
                predictor.train_prediction_model()
            signal = predictor.generate_signal()
        
        # Current price row
        col1, col2, col3, col4 = st.columns(4)
        
        current_price = signal['current_price']
        change = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) > 1 else 0
        change_pct = (change / data['Close'].iloc[-2]) * 100 if len(data) > 1 else 0
        
        with col1:
            st.metric("Current Price", f"${current_price:.2f}", f"{change_pct:+.2f}%")
        
        with col2:
            st.metric("RSI (14)", f"{signal['rsi']:.1f}", 
                     "Oversold" if signal['rsi'] < 30 else "Overbought" if signal['rsi'] > 70 else "Neutral")
        
        with col3:
            st.metric("Confidence", f"{signal['confidence']:.0%}", 
                     "High" if signal['confidence'] > 0.6 else "Medium" if signal['confidence'] > 0.3 else "Low")
        
        with col4:
            # Signal box
            if "BUY" in signal['action']:
                st.markdown("### 🟢 BUY SIGNAL")
            elif "SELL" in signal['action']:
                st.markdown("### 🔴 SELL SIGNAL")
            else:
                st.markdown("### ⚪ HOLD")
        
        # Recommendation card
        signal_class = "signal-buy" if "BUY" in signal['action'] else "signal-sell" if "SELL" in signal['action'] else "signal-hold"
        st.markdown(f"""
        <div class="{signal_class}">
            <h3>{signal['action']}</h3>
            <p>{signal['recommendation']}</p>
            <small>Overall Score: {signal['score']:.2f}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Charts
        st.markdown("## 📈 Price Chart")
        
        # Create interactive chart
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(f"{ticker} Price", "Volume", "RSI")
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Price"
            ),
            row=1, col=1
        )
        
        # Add moving averages
        ma20 = data['Close'].rolling(20).mean()
        ma50 = data['Close'].rolling(50).mean()
        
        fig.add_trace(
            go.Scatter(x=data.index, y=ma20, name="MA 20", line=dict(color="orange", width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=ma50, name="MA 50", line=dict(color="purple", width=1)),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['red' if data['Close'].iloc[i] < data['Open'].iloc[i] else 'green' for i in range(len(data))]
        fig.add_trace(
            go.Bar(x=data.index, y=data['Volume'], name="Volume", marker_color=colors),
            row=2, col=1
        )
        
        # RSI
        if 'momentum_rsi' in data.columns:
            fig.add_trace(
                go.Scatter(x=data.index, y=data['momentum_rsi'], name="RSI", line=dict(color="blue")),
                row=3, col=1
            )
            # Add overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(
            title=f"{ticker} - Real-time Analysis",
            xaxis_title="Date",
            height=800,
            template="plotly_dark"
        )
        
        fig.update_xaxes(rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Signal breakdown
        st.markdown("## 🔍 Signal Breakdown")
        
        signal_df = pd.DataFrame([
            {"Indicator": k, "Value": f"{v:+.2f}", "Interpretation": 
             "Bullish 📈" if v > 0 else "Bearish 📉" if v < 0 else "Neutral ⚖️"}
            for k, v in signal['signals'].items()
        ])
        st.dataframe(signal_df, use_container_width=True)
        
        # Trade Recommendation Box
        st.markdown("## 💡 Trade Recommendation")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            action = "LONG" if "BUY" in signal['action'] else "SHORT" if "SELL" in signal['action'] else "WAIT"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Action</h4>
                <h2>{action}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            stop_loss = current_price * 0.95 if "BUY" in signal['action'] else current_price * 1.05
            take_profit = current_price * 1.05 if "BUY" in signal['action'] else current_price * 0.95
            st.markdown(f"""
            <div class="metric-card">
                <h4>Stop Loss</h4>
                <h3>${stop_loss:.2f}</h3>
                <small>Target: ${take_profit:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            risk_amount = st.number_input("Risk per trade ($)", min_value=50, value=500, step=50)
            position_size = risk_amount / (abs(current_price - stop_loss) / current_price)
            st.markdown(f"**Suggested Position Size:** ${position_size:.0f}")
            st.caption(f"Risk: ${risk_amount} ({risk_amount/position_size:.1%} of position)")
        
        # News sentiment (basic)
        st.markdown("## 📰 Recent News")
        try:
            stock = yf.Ticker(ticker)
            news = stock.news[:3]
            for item in news:
                st.markdown(f"• [{item['title']}]({item['link']})")
        except:
            st.info("News data temporarily unavailable")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Check ticker symbol or try again later")
else:
    st.info("Enter a stock symbol to begin analysis")
"""
Stock Prediction Tool with Multi-API Fallback
Supports: yfinance (primary), Alpha Vantage, Polygon.io, FCS API
Run anytime to get buy/sell signals for any stock
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from ta import add_all_ta_features
from datetime import datetime, timedelta
import warnings
import os
import time
import requests
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# ============ API CLIENTS ============

class AlphaVantageClient:
    """Alpha Vantage API Client - Free tier: 5 calls/min, 500/day"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.last_call_time = 0
        self.min_call_interval = 12  # 5 calls per minute = 12 seconds between calls
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_call_interval:
            time.sleep(self.min_call_interval - elapsed)
        self.last_call_time = time.time()
    
    def get_quote(self, symbol):
        """Get real-time stock quote"""
        self._rate_limit()
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            quote = data.get('Global Quote', {})
            if quote and quote.get('05. price'):
                return {
                    'symbol': quote.get('01. symbol', symbol),
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                    'volume': int(quote.get('06. volume', 0)),
                    'source': 'Alpha Vantage'
                }
            return None
        except Exception as e:
            print(f"   Alpha Vantage error: {e}")
            return None
    
    def get_time_series(self, symbol, output_size='compact'):
        """Get daily time series"""
        self._rate_limit()
        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': output_size,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            time_series = data.get('Time Series (Daily)', {})
            if time_series:
                # Convert to DataFrame
                df_data = []
                for date, values in time_series.items():
                    df_data.append({
                        'Date': pd.to_datetime(date),
                        'Open': float(values.get('1. open', 0)),
                        'High': float(values.get('2. high', 0)),
                        'Low': float(values.get('3. low', 0)),
                        'Close': float(values.get('4. close', 0)),
                        'Volume': int(values.get('6. volume', 0))
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('Date')
                df.set_index('Date', inplace=True)
                return df
            return None
        except Exception as e:
            print(f"   Alpha Vantage time series error: {e}")
            return None


class PolygonClient:
    """Polygon.io (Massive.com) API Client - Free tier: 5 calls/min, previous day only"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.last_call_time = 0
        self.min_call_interval = 12
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_call_interval:
            time.sleep(self.min_call_interval - elapsed)
        self.last_call_time = time.time()
    
    def get_previous_close(self, symbol):
        """Get previous day's closing price (free tier available)"""
        self._rate_limit()
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
            params = {'apiKey': self.api_key}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                return {
                    'symbol': symbol,
                    'price': result.get('c', 0),
                    'open': result.get('o', 0),
                    'high': result.get('h', 0),
                    'low': result.get('l', 0),
                    'volume': result.get('v', 0),
                    'timestamp': result.get('t', 0),
                    'source': 'Polygon.io'
                }
            return None
        except Exception as e:
            print(f"   Polygon.io error: {e}")
            return None


class FCSAPIClient:
    """FCS API Client - Free tier: 500 calls/month"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api-v4.fcsapi.com"
        self.call_count = 0
        self.monthly_limit = 500
    
    def get_stock_quote(self, symbol):
        """Get real-time stock quote"""
        try:
            url = f"{self.base_url}/stock/quote"
            params = {
                'symbol': symbol,
                'access_key': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            self.call_count += 1
            print(f"   FCS API Call #{self.call_count}/{self.monthly_limit}")
            
            if data.get('status'):
                quote = data.get('response', [{}])[0]
                if quote.get('c'):
                    return {
                        'symbol': quote.get('s', symbol),
                        'price': float(quote.get('c', 0)),
                        'change': float(quote.get('ch', 0)),
                        'change_percent': quote.get('chp', '0'),
                        'volume': int(quote.get('v', 0)),
                        'source': 'FCS API'
                    }
            return None
        except Exception as e:
            print(f"   FCS API error: {e}")
            return None
    
    def get_history(self, symbol, period='1d', limit=100):
        """Get historical data"""
        try:
            url = f"{self.base_url}/stock/history"
            params = {
                'symbol': symbol,
                'period': period,
                'limit': limit,
                'access_key': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') and data.get('response'):
                history = data['response']
                df_data = []
                for bar in history:
                    df_data.append({
                        'Date': pd.to_datetime(bar.get('d')),
                        'Open': float(bar.get('o', 0)),
                        'High': float(bar.get('h', 0)),
                        'Low': float(bar.get('l', 0)),
                        'Close': float(bar.get('c', 0)),
                        'Volume': int(bar.get('v', 0))
                    })
                
                df = pd.DataFrame(df_data)
                df = df.sort_values('Date')
                df.set_index('Date', inplace=True)
                return df
            return None
        except Exception as e:
            print(f"   FCS API history error: {e}")
            return None


class MarketDataAggregator:
    """Unified market data client with automatic failover"""
    
    def __init__(self):
        # Load API keys from environment
        self.alpha_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.fcs_key = os.getenv('FCS_API_KEY')
        
        # Initialize clients only if keys exist
        self.alpha_client = AlphaVantageClient(self.alpha_key) if self.alpha_key else None
        self.polygon_client = PolygonClient(self.polygon_key) if self.polygon_key else None
        self.fcs_client = FCSAPIClient(self.fcs_key) if self.fcs_key else None
        
        self.apis_available = any([self.alpha_client, self.polygon_client, self.fcs_client])
    
    def get_stock_data_fallback(self, symbol, period="6mo"):
        """Try multiple APIs to get stock data"""
        
        # Try Alpha Vantage first (best free tier: 500/day)
        if self.alpha_client:
            print("   Trying Alpha Vantage...")
            df = self.alpha_client.get_time_series(symbol, 'full' if period in ['1y', '2y'] else 'compact')
            if df is not None and len(df) > 50:
                print(f"   ✓ Alpha Vantage data acquired: {len(df)} days")
                return df
        
        # Try FCS API second (good for historical)
        if self.fcs_client:
            print("   Trying FCS API...")
            limit = {'1mo': 30, '3mo': 90, '6mo': 180, '1y': 365, '2y': 730}.get(period, 180)
            df = self.fcs_client.get_history(symbol, period='1d', limit=limit)
            if df is not None and len(df) > 30:
                print(f"   ✓ FCS API data acquired: {len(df)} days")
                return df
        
        # Try Polygon.io for at least current price
        if self.polygon_client:
            print("   Trying Polygon.io...")
            quote = self.polygon_client.get_previous_close(symbol)
            if quote and quote.get('price', 0) > 0:
                print(f"   ✓ Polygon.io price acquired: ${quote['price']:.2f}")
                # Create minimal DataFrame
                dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
                df = pd.DataFrame({
                    'Open': [quote['price']] * 10,
                    'High': [quote['high']] * 10,
                    'Low': [quote['low']] * 10,
                    'Close': [quote['price']] * 10,
                    'Volume': [quote['volume']] * 10
                }, index=dates)
                return df
        
        print("   ❌ All API fallbacks failed")
        return None
    
    def get_current_price(self, symbol):
        """Get current price from any available API"""
        
        # Try Alpha Vantage
        if self.alpha_client:
            quote = self.alpha_client.get_quote(symbol)
            if quote and quote['price'] > 0:
                return quote
        
        # Try FCS API
        if self.fcs_client:
            quote = self.fcs_client.get_stock_quote(symbol)
            if quote and quote['price'] > 0:
                return quote
        
        # Try Polygon.io
        if self.polygon_client:
            quote = self.polygon_client.get_previous_close(symbol)
            if quote and quote['price'] > 0:
                return quote
        
        return None


# ============ MAIN PREDICTOR CLASS ============

class StockPredictor:
    def __init__(self, ticker, use_api_fallback=True):
        """
        Initialize Stock Predictor
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            use_api_fallback: If True, use Alpha Vantage/FCS/Polygon when yfinance fails
        """
        self.ticker = ticker.upper()
        self.data = None
        self.model = None
        self.scaler = StandardScaler()
        self.use_api_fallback = use_api_fallback
        self.market_aggregator = MarketDataAggregator() if use_api_fallback else None
        self.data_source = None
        
    def fetch_data(self, period="6mo", use_yfinance_first=True):
        """
        Fetch real-time stock data from multiple sources
        
        Args:
            period: Time period (1mo, 3mo, 6mo, 1y, 2y)
            use_yfinance_first: Try yfinance first before fallback APIs
        """
        print(f"📡 Fetching {self.ticker} data...")
        
        # Try yfinance first (free, no API key required)
        if use_yfinance_first:
            try:
                stock = yf.Ticker(self.ticker)
                self.data = stock.history(period=period)
                
                if len(self.data) > 30:
                    # Also get company info
                    info = stock.info
                    company_name = info.get('longName', self.ticker)
                    current_price = self.data['Close'].iloc[-1]
                    print(f"✅ yfinance: {company_name} - ${current_price:.2f} ({len(self.data)} days)")
                    self.data_source = "yfinance"
                    return self.data
                else:
                    print(f"   yfinance returned only {len(self.data)} days, trying fallback...")
            except Exception as e:
                print(f"   yfinance error: {e}")
        
        # Fallback to API aggregator
        if self.use_api_fallback and self.market_aggregator and self.market_aggregator.apis_available:
            print("   Using API fallback...")
            self.data = self.market_aggregator.get_stock_data_fallback(self.ticker, period)
            
            if self.data is not None and len(self.data) > 20:
                current_price = self.data['Close'].iloc[-1]
                print(f"✅ API fallback: {self.ticker} - ${current_price:.2f} ({len(self.data)} days)")
                self.data_source = "API_fallback"
                return self.data
        
        # Last resort: try to get at least current price
        if self.market_aggregator:
            quote = self.market_aggregator.get_current_price(self.ticker)
            if quote:
                print(f"⚠️ Limited data: Only current price ${quote['price']:.2f} available")
                # Create minimal DataFrame with simulated data
                dates = pd.date_range(end=datetime.now(), periods=5, freq='D')
                self.data = pd.DataFrame({
                    'Open': [quote['price']] * 5,
                    'High': [quote['price'] * 1.01] * 5,
                    'Low': [quote['price'] * 0.99] * 5,
                    'Close': [quote['price']] * 5,
                    'Volume': [1000000] * 5
                }, index=dates)
                self.data_source = "minimal"
                return self.data
        
        raise Exception(f"Unable to fetch data for {self.ticker}. Check ticker symbol or internet connection.")
    
    def calculate_indicators(self):
        """Add technical indicators for analysis"""
        if self.data is None or len(self.data) < 30:
            print(f"⚠️ Warning: Only {len(self.data) if self.data is not None else 0} days of data. Indicators may be limited.")
            
            # Create synthetic data for basic indicators if needed
            if len(self.data) < 30:
                # Pad with synthetic data for indicators
                last_price = self.data['Close'].iloc[-1]
                padding = pd.DataFrame({
                    'Open': [last_price] * (30 - len(self.data)),
                    'High': [last_price * 1.01] * (30 - len(self.data)),
                    'Low': [last_price * 0.99] * (30 - len(self.data)),
                    'Close': [last_price] * (30 - len(self.data)),
                    'Volume': [1000000] * (30 - len(self.data))
                }, index=pd.date_range(end=self.data.index[0], periods=30 - len(self.data), freq='D'))
                
                self.data = pd.concat([padding, self.data])
        
        df = self.data.copy()
        
        # Ensure we have all required columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df.columns:
                df[col] = df['Close'] if col != 'Volume' else 1000000
        
        try:
            # Use 'ta' library for comprehensive indicators
            df = add_all_ta_features(
                df, open="Open", high="High", low="Low", close="Close", volume="Volume",
                fillna=True
            )
        except Exception as e:
            print(f"   Indicator calculation warning: {e}")
            # Add basic indicators manually
            df['momentum_rsi'] = self._calculate_rsi(df['Close'], 14)
            df['trend_macd'] = self._calculate_macd(df['Close'])
        
        # Add custom indicators
        # RSI Signal (oversold < 30 = buy signal, overbought > 70 = sell signal)
        df['RSI_Signal'] = 0
        rsi_col = 'momentum_rsi' if 'momentum_rsi' in df.columns else 'rsi'
        if rsi_col in df.columns:
            df.loc[df[rsi_col] < 30, 'RSI_Signal'] = 1  # Buy
            df.loc[df[rsi_col] > 70, 'RSI_Signal'] = -1  # Sell
        
        # Moving Average Crossover (20-day vs 50-day)
        df['MA_20'] = df['Close'].rolling(window=min(20, len(df))).mean()
        df['MA_50'] = df['Close'].rolling(window=min(50, len(df))).mean()
        df['MA_Signal'] = 0
        df.loc[df['MA_20'] > df['MA_50'], 'MA_Signal'] = 1  # Bullish
        df.loc[df['MA_20'] < df['MA_50'], 'MA_Signal'] = -1  # Bearish
        
        # Volume confirmation
        df['Volume_SMA'] = df['Volume'].rolling(window=min(20, len(df))).mean()
        df['Volume_Signal'] = df['Volume'] > df['Volume_SMA'].shift(1)
        
        # Bollinger Bands
        window = min(20, len(df))
        df['BB_middle'] = df['Close'].rolling(window=window).mean()
        bb_std = df['Close'].rolling(window=window).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # Price position relative to bands (-1 to 1 scale)
        bb_range = df['BB_upper'] - df['BB_lower']
        df['BB_Position'] = (df['Close'] - df['BB_lower']) / bb_range
        df['BB_Position'] = df['BB_Position'].clip(0, 1) * 2 - 1  # -1 to 1
        
        self.data = df
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI manually"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices):
        """Calculate MACD manually"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        return macd
    
    def train_prediction_model(self):
        """Train a Random Forest model to predict next-day direction"""
        if self.data is None or len(self.data) < 50:
            print("⚠️ Not enough data for ML model. Using technical analysis only.")
            return None
        
        df = self.data.copy()
        
        # Create target: 1 if price goes up tomorrow, 0 if down
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        # Select features for training
        feature_cols = []
        for col in ['momentum_rsi', 'trend_macd', 'trend_macd_signal', 'RSI_Signal',
                    'MA_Signal', 'BB_Position', 'volume_obv']:
            if col in df.columns:
                feature_cols.append(col)
        
        # Add alternative column names if needed
        if not feature_cols:
            for col in ['Close', 'Volume', 'MA_Signal']:
                if col in df.columns:
                    feature_cols.append(col)
        
        # Drop NaN values
        df_clean = df.dropna()
        
        if len(df_clean) < 30:
            print("⚠️ Not enough clean data for ML model.")
            return None
        
        X = df_clean[feature_cols]
        y = df_clean['Target']
        
        # Train on first 80% of data
        split_idx = int(len(X) * 0.8)
        if split_idx < 10:
            split_idx = len(X) // 2
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        try:
            X_train_scaled = self.scaler.fit_transform(X_train)
            
            # Train Random Forest
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Calculate accuracy
            if len(X_test) > 5:
                X_test_scaled = self.scaler.transform(X_test)
                accuracy = self.model.score(X_test_scaled, y_test)
                print(f"🤖 Model trained. Accuracy: {accuracy:.1%}")
            else:
                print("🤖 Model trained (insufficient test data)")
            
            return self.model
        except Exception as e:
            print(f"   Model training error: {e}")
            return None
    
    def generate_signal(self):
        """Generate buy/hold/sell recommendation with confidence"""
        if self.data is None or len(self.data) < 10:
            print("❌ Insufficient data. Please check ticker symbol.")
            return None
        
        latest = self.data.iloc[-1]
        
        # Individual signals (each ranges -1 to 1)
        signals = {
            'RSI': 0,
            'MACD': 0,
            'Moving_Avg': 0,
            'Volume': 0,
            'Bollinger': 0,
            'ML_Prediction': 0
        }
        
        # 1. RSI Signal
        rsi_col = 'momentum_rsi' if 'momentum_rsi' in self.data.columns else 'rsi'
        rsi = latest.get(rsi_col, 50)
        if hasattr(rsi, 'iloc'):
            rsi = rsi.iloc[0] if len(rsi) > 0 else 50
        
        if isinstance(rsi, (int, float)):
            if rsi < 30:
                signals['RSI'] = 1  # Oversold - Buy signal
            elif rsi > 70:
                signals['RSI'] = -1  # Overbought - Sell signal
            
        # 2. MACD Signal
        macd = latest.get('trend_macd', 0)
        macd_signal = latest.get('trend_macd_signal', 0)
        if isinstance(macd, (int, float)) and isinstance(macd_signal, (int, float)):
            if macd > macd_signal:
                signals['MACD'] = 0.5
            elif macd < macd_signal:
                signals['MACD'] = -0.5
            
        # 3. Moving Average Crossover
        ma_signal = latest.get('MA_Signal', 0)
        if isinstance(ma_signal, (int, float)):
            signals['Moving_Avg'] = ma_signal if abs(ma_signal) > 0 else 0
            
        # 4. Volume Confirmation
        volume_signal = latest.get('Volume_Signal', False)
        signals['Volume'] = 0.5 if volume_signal else -0.2
        
        # 5. Bollinger Band Position
        bb_pos = latest.get('BB_Position', 0)
        if isinstance(bb_pos, (int, float)):
            signals['Bollinger'] = -bb_pos  # Near lower band gives buy signal
        
        # 6. Machine Learning Prediction (if model exists)
        if self.model is not None:
            try:
                feature_cols = [col for col in ['momentum_rsi', 'trend_macd', 'RSI_Signal',
                                                'MA_Signal', 'BB_Position'] if col in self.data.columns]
                
                if feature_cols:
                    features = np.array([[latest[col] for col in feature_cols]])
                    # Handle any non-numeric values
                    features = np.nan_to_num(features, nan=0.0)
                    features_scaled = self.scaler.transform(features)
                    
                    proba = self.model.predict_proba(features_scaled)[0]
                    ml_score = proba[1] * 2 - 1  # Convert (0.5=neutral, 1=buy, 0=sell)
                    signals['ML_Prediction'] = ml_score * 0.8  # Weight slightly less
            except Exception as e:
                print(f"   ML prediction error: {e}")
        
        # Calculate weighted overall score
        weights = {
            'RSI': 0.25,
            'MACD': 0.20,
            'Moving_Avg': 0.20,
            'Volume': 0.10,
            'Bollinger': 0.15,
            'ML_Prediction': 0.10
        }
        
        total_weight = sum(weights.values())
        overall_score = 0
        for k, v in signals.items():
            if isinstance(v, (int, float)):
                overall_score += v * weights.get(k, 0)
        overall_score = overall_score / total_weight
        
        # Determine action
        if overall_score > 0.3:
            action = "🟢 BUY"
            recommendation = f"Strong positive signals across multiple indicators"
        elif overall_score > 0.1:
            action = "🟡 ACCUMULATE"
            recommendation = "Mildly bullish - consider scaling in"
        elif overall_score < -0.3:
            action = "🔴 SELL / SHORT"
            recommendation = f"Bearish signals detected - consider shorting or taking profits"
        elif overall_score < -0.1:
            action = "🟠 REDUCE"
            recommendation = "Mildly bearish - consider trimming position"
        else:
            action = "⚪ HOLD"
            recommendation = "Mixed signals - wait for clearer direction"
        
        # Get current price safely
        current_price = latest['Close']
        if hasattr(current_price, 'iloc'):
            current_price = current_price.iloc[0] if len(current_price) > 0 else 0
        
        # Get RSI value safely
        rsi_value = rsi if isinstance(rsi, (int, float)) else 50
        
        # Get volume ratio
        volume_ratio = 1.0
        if 'Volume' in latest and 'Volume_SMA' in latest:
            vol = latest['Volume']
            vol_sma = latest['Volume_SMA']
            if isinstance(vol, (int, float)) and isinstance(vol_sma, (int, float)) and vol_sma > 0:
                volume_ratio = vol / vol_sma
        
        return {
            'action': action,
            'score': overall_score,
            'confidence': min(abs(overall_score) * 1.5, 0.95),
            'recommendation': recommendation,
            'signals': signals,
            'current_price': float(current_price),
            'rsi': float(rsi_value),
            'volume_ratio': float(volume_ratio),
            'data_source': self.data_source
        }
    
    def display_report(self):
        """Print a comprehensive analysis report"""
        print("\n" + "="*60)
        print(f"📈 STOCK ANALYSIS REPORT: {self.ticker}")
        print("="*60)
        
        signal = self.generate_signal()
        if not signal:
            return
        
        print(f"\n💰 Current Price: ${signal['current_price']:.2f}")
        print(f"📊 Data Source: {signal.get('data_source', 'Unknown').upper()}")
        print(f"📈 RSI (14): {signal['rsi']:.1f} ", end="")
        if signal['rsi'] < 30:
            print("(Oversold - Bullish)")
        elif signal['rsi'] > 70:
            print("(Overbought - Bearish)")
        else:
            print("(Neutral)")
        
        print(f"📊 Volume vs Avg: {signal['volume_ratio']:.1f}x")
        print(f"\n🎯 RECOMMENDATION: {signal['action']}")
        print(f"💪 Confidence: {signal['confidence']:.0%}")
        print(f"📝 {signal['recommendation']}")
        
        print("\n📊 Indicator Breakdown:")
        for indicator, value in signal['signals'].items():
            if isinstance(value, (int, float)):
                if value > 0:
                    status = "📈 Bullish"
                elif value < 0:
                    status = "📉 Bearish"
                else:
                    status = "⚖️ Neutral"
                print(f"  • {indicator:12}: {value:+.2f} - {status}")
        
        print("\n" + "="*60)


def run_multi_stock_analysis(tickers, period="6mo"):
    """Analyze multiple stocks at once"""
    results = []
    for ticker in tickers:
        print(f"\n🔄 Analyzing {ticker}...")
        predictor = StockPredictor(ticker, use_api_fallback=True)
        try:
            predictor.fetch_data(period=period)
            predictor.calculate_indicators()
            predictor.train_prediction_model()
            signal = predictor.generate_signal()
            
            if signal:
                results.append({
                    'ticker': ticker,
                    'price': signal['current_price'],
                    'action': signal['action'],
                    'confidence': signal['confidence'],
                    'rsi': signal['rsi'],
                    'source': signal.get('data_source', 'Unknown')
                })
                predictor.display_report()
        except Exception as e:
            print(f"   ❌ Error analyzing {ticker}: {e}")
    
    # Print summary
    if results:
        print("\n" + "="*60)
        print("📊 MULTI-STOCK SUMMARY")
        print("="*60)
        summary_df = pd.DataFrame(results)
        print(summary_df.to_string(index=False))
    
    return results


# ============ ENVIRONMENT SETUP HELPERS ============

def setup_api_keys():
    """Helper to set up API keys interactively"""
    print("\n" + "="*60)
    print("🔑 API KEY SETUP")
    print("="*60)
    print("\nTo use API fallbacks, get free API keys from:")
    print("  1. Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    print("  2. Polygon.io: https://polygon.io (free tier)")
    print("  3. FCS API: https://fcsapi.com (free tier)")
    
    setup = input("\nCreate .env file with API keys? (y/n): ").lower()
    if setup == 'y':
        alpha_key = input("Alpha Vantage API key (press Enter to skip): ").strip()
        polygon_key = input("Polygon.io API key (press Enter to skip): ").strip()
        fcs_key = input("FCS API key (press Enter to skip): ").strip()
        
        with open('.env', 'w') as f:
            if alpha_key:
                f.write(f"ALPHA_VANTAGE_KEY={alpha_key}\n")
            if polygon_key:
                f.write(f"POLYGON_API_KEY={polygon_key}\n")
            if fcs_key:
                f.write(f"FCS_API_KEY={fcs_key}\n")
        
        print("\n✅ .env file created successfully!")
        print("   The predictor will now use these APIs as fallbacks.")


# ============ MAIN EXECUTION ============

if __name__ == "__main__":
    print("\n" + "🔮"*30)
    print("STOCK PREDICTION TOOL - Multi-API Edition")
    print("🔮"*30)
    
    # Check for API keys
    has_keys = any([os.getenv('ALPHA_VANTAGE_KEY'), 
                    os.getenv('POLYGON_API_KEY'), 
                    os.getenv('FCS_API_KEY')])
    
    if not has_keys:
        print("\n⚠️ No API keys found. yfinance will be used as primary source.")
        print("   For better reliability, set up API keys.")
        setup_keys = input("\nSet up API keys now? (y/n): ").lower()
        if setup_keys == 'y':
            setup_api_keys()
            # Reload environment
            load_dotenv()
    
    # Single stock analysis
    ticker = input("\n📊 Enter stock ticker (e.g., AAPL, TSLA, NVDA): ").strip().upper()
    
    if ticker:
        period = input("Period (1mo/3mo/6mo/1y/2y) [default: 6mo]: ").strip() or "6mo"
        
        predictor = StockPredictor(ticker, use_api_fallback=True)
        try:
            predictor.fetch_data(period=period)
            predictor.calculate_indicators()
            predictor.train_prediction_model()
            predictor.display_report()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   Check ticker symbol or internet connection.")
    
    # Optional: Multi-stock analysis
    multi = input("\n🔍 Analyze multiple stocks? (y/n): ").strip().lower()
    if multi == 'y':
        tickers_input = input("Enter tickers separated by commas (e.g., AAPL,MSFT,GOOGL): ")
        tickers = [t.strip().upper() for t in tickers_input.split(',')]
        run_multi_stock_analysis(tickers, period)
    
    print("\n✅ Analysis complete!")
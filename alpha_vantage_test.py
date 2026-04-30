"""
Alpha Vantage API Test
Free tier: 5 requests per minute, 500 per day
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load API key from environment variable (recommended)
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_KEY', '4MKUNQ1QNML73LA')

class AlphaVantageClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_quote(self, symbol):
        """Get real-time quote for a stock"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        quote = data.get('Global Quote', {})
        return {
            'symbol': quote.get('01. symbol'),
            'price': float(quote.get('05. price', 0)),
            'change': float(quote.get('09. change', 0)),
            'change_percent': quote.get('10. change percent', '0%'),
            'volume': int(quote.get('06. volume', 0)),
            'timestamp': datetime.now()
        }
    
    def get_daily_prices(self, symbol, output_size='compact'):
        """Get daily adjusted prices (compact = last 100 days, full = 20+ years)"""
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'outputsize': output_size,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        time_series = data.get('Time Series (Daily)', {})
        return time_series
    
    def get_technical_indicator(self, symbol, indicator='RSI', interval='daily'):
        """Get technical indicators (free tier supports many indicators)"""
        params = {
            'function': indicator,
            'symbol': symbol,
            'interval': interval,
            'series_type': 'close',
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
    
    def get_company_overview(self, symbol):
        """Get company information"""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

# Test the API
if __name__ == "__main__":
    print("\n" + "="*50)
    print("📊 ALPHA VANTAGE API TEST")
    print("="*50)
    
    # Replace with your actual API key
    API_KEY = input("Enter your Alpha Vantage API key: ")
    
    client = AlphaVantageClient(API_KEY)
    
    # Test 1: Get real-time quote
    print("\n📈 Fetching AAPL real-time quote...")
    quote = client.get_quote('AAPL')
    print(f"   Symbol: {quote['symbol']}")
    print(f"   Price: ${quote['price']:.2f}")
    print(f"   Change: {quote['change_percent']}")
    
    # Test 2: Get RSI indicator
    print("\n📊 Fetching RSI indicator for AAPL...")
    rsi_data = client.get_technical_indicator('AAPL', 'RSI')
    if 'Technical Analysis: RSI' in rsi_data:
        latest_date = list(rsi_data['Technical Analysis: RSI'].keys())[0]
        latest_rsi = rsi_data['Technical Analysis: RSI'][latest_date]['RSI']
        print(f"   Latest RSI: {latest_rsi}")
    
    print("\n✅ Alpha Vantage test complete!")
    print("   Rate limits: 5 calls/min, 500 calls/day")
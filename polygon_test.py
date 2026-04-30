"""
Polygon.io (Massive.com) API Test
Free tier: 5 API calls per minute, previous day data only
Note: Real-time data requires paid subscription
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import the Massive client (formerly polygon)
try:
    from massive import RESTClient
except ImportError:
    print("Installing massive client...")
    os.system('pip install -U massive')
    from massive import RESTClient

load_dotenv()
API_KEY = os.getenv('POLYGON_API_KEY', 'g3g8NfkMJ9Up8obFU2pY70y0qW4WyzMG')

class PolygonClient:
    def __init__(self, api_key):
        self.client = RESTClient(api_key=api_key)
    
    def get_previous_close(self, symbol):
        """Get previous day's closing price (free tier available)"""
        try:
            previous = self.client.get_previous_close(symbol)
            return {
                'symbol': symbol,
                'price': previous.close,
                'volume': previous.volume,
                'date': previous.date
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_stock_aggregates(self, symbol, timespan='day', multiplier=1, from_date=None, to_date=None):
        """
        Get aggregate bars (free tier: limited to previous day)
        Paid tier required for real-time aggregates
        """
        if from_date is None:
            to_date = datetime.now()
            from_date = to_date - timedelta(days=7)
        
        try:
            aggs = self.client.get_aggregates(
                symbol,
                multiplier,
                timespan,
                from_date.strftime('%Y-%m-%d'),
                to_date.strftime('%Y-%m-%d')
            )
            return [{'open': agg.open, 'high': agg.high, 'low': agg.low, 
                    'close': agg.close, 'volume': agg.volume} for agg in aggs]
        except Exception as e:
            return {'error': str(e)}
    
    def get_ticker_details(self, symbol):
        """Get basic ticker information"""
        try:
            details = self.client.get_ticker_details(symbol)
            return {
                'symbol': details.ticker,
                'name': details.name,
                'market': details.market,
                'locale': details.locale,
                'active': details.active
            }
        except Exception as e:
            return {'error': str(e)}
    
    def list_tickers(self, limit=10):
        """List available tickers (free tier supported)"""
        try:
            tickers = self.client.list_tickers(limit=limit)
            return [{'ticker': t.ticker, 'name': t.name} for t in tickers]
        except Exception as e:
            return {'error': str(e)}

# Test the API
if __name__ == "__main__":
    print("\n" + "="*50)
    print("📊 POLYGON.IO (MASSIVE) API TEST")
    print("="*50)
    
    API_KEY = input("Enter your Polygon.io/Massive API key: ")
    
    client = PolygonClient(g3g8NfkMJ9Up8obFU2pY70y0qW4WyzMG)
    
    # Test 1: Get previous close (free tier)
    print("\n📈 Fetching AAPL previous close...")
    result = client.get_previous_close('AAPL')
    if 'error' not in result:
        print(f"   Symbol: {result['symbol']}")
        print(f"   Previous Close: ${result['price']:.2f}")
        print(f"   Date: {result['date']}")
    else:
        print(f"   Error: {result['error']}")
    
    # Test 2: Get ticker details
    print("\n🏢 Fetching company details...")
    details = client.get_ticker_details('AAPL')
    if 'error' not in details:
        print(f"   Name: {details['name']}")
        print(f"   Status: {'Active' if details['active'] else 'Inactive'}")
    
    print("\n✅ Polygon.io test complete!")
    print("   Note: Real-time data requires paid subscription")
    print("   Free tier: 5 calls/min, previous day data only")
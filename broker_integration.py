"""
Broker API Integration Templates
Supports TradeZero and Interactive Brokers
"""

import time
import hashlib
import hmac
import requests
from typing import Dict, Any
from datetime import datetime

class TradeZeroAPI:
    """
    TradeZero API Integration
    Note: TradeZero doesn't have a public REST API.
    Use their ZeroWeb API or ZeroMobile app for manual trades.
    This is a template structure for when API becomes available.
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.tradezero.com/v1"  # Hypothetical endpoint
        self.session = requests.Session()
        
    def authenticate(self):
        """Authenticate with API credentials"""
        if not self.api_key:
            print("⚠️ TradeZero API requires manual trading via ZeroWeb/ZeroMobile")
            print("📱 Access: https://tradezero.app/")
            return False
        
        try:
            # Hypothetical auth endpoint
            response = self.session.post(
                f"{self.base_url}/auth",
                json={"apiKey": self.api_key, "apiSecret": self.api_secret}
            )
            return response.status_code == 200
        except:
            return False
    
    def place_short_order(self, symbol: str, shares: int, order_type: str = "LIMIT"):
        """
        Place a short sell order
        TradeZero is known for excellent short locate system
        """
        print(f"\n🔴 SHORT ORDER (Manual) - TradeZero")
        print(f"   Symbol: {symbol}")
        print(f"   Shares: {shares}")
        print(f"   Type: {order_type}")
        print(f"\n📱 To execute:")
        print(f"   1. Open ZeroWeb or ZeroMobile")
        print(f"   2. Search for {symbol}")
        print(f"   3. Click 'Short Sell'")
        print(f"   4. Enter {shares} shares")
        print(f"   5. Set stop loss at +5%")
        print(f"   6. Set take profit at -5%")
        
        # If API exists, would return:
        # return self._api_call("/orders/short", method="POST", data={...})
        
        return {"status": "manual_required", "platform": "TradeZero"}
    
    def place_long_order(self, symbol: str, shares: int):
        """Place a long buy order"""
        print(f"\n🟢 LONG ORDER (Manual) - TradeZero")
        print(f"   Symbol: {symbol}")
        print(f"   Shares: {shares}")
        print(f"\n📱 Execute in ZeroWeb/ZeroMobile")
        return {"status": "manual_required"}

class InteractiveBrokersAPI:
    """
    Interactive Brokers Client Portal Web API
    Requires IBKR account with API access enabled
    """
    
    def __init__(self, account_id: str = None):
        self.account_id = account_id
        self.base_url = "https://localhost:5000/v1/api"
        self.session = requests.Session()
        self.session.verify = False  # SSL cert is self-signed locally
        
    def connect(self):
        """Connect to IBKR Gateway"""
        print("🔄 Connecting to IBKR Gateway...")
        print("   Make sure IB Gateway is running on port 5000")
        try:
            response = self.session.get(f"{self.base_url}/iserver/auth/status")
            if response.status_code == 200:
                print("✅ Connected to Interactive Brokers")
                return True
            else:
                print("❌ Not connected. Start IB Gateway and enable API")
                return False
        except:
            print("❌ Cannot connect. Ensure IB Gateway is running")
            return False
    
    def get_accounts(self):
        """Get available trading accounts"""
        response = self.session.get(f"{self.base_url}/iserver/accounts")
        if response.status_code == 200:
            accounts = response.json()
            print(f"📊 Available accounts: {accounts}")
            return accounts
        return None
    
    def place_order(self, symbol: str, action: str, quantity: int, 
                    order_type: str = "MKT", limit_price: float = None):
        """
        Place an order
        action: "BUY" or "SELL" (for shorts, use "SELL" with short=True)
        """
        
        order = {
            "acctId": self.account_id,
            "conid": self._get_conid(symbol),
            "orderType": order_type,
            "side": action,
            "quantity": quantity,
            "tif": "DAY"
        }
        
        if limit_price:
            order["price"] = limit_price
        
        print(f"\n📝 Placing order:")
        print(f"   Symbol: {symbol}")
        print(f"   Action: {action}")
        print(f"   Quantity: {quantity}")
        
        response = self.session.post(
            f"{self.base_url}/iserver/account/{self.account_id}/orders",
            json=order
        )
        
        if response.status_code == 200:
            print("✅ Order placed successfully")
            return response.json()
        else:
            print(f"❌ Order failed: {response.text}")
            return None
    
    def place_short(self, symbol: str, quantity: int):
        """Place a short sell order"""
        return self.place_order(symbol, "SELL", quantity)
    
    def place_long(self, symbol: str, quantity: int):
        """Place a long buy order"""
        return self.place_order(symbol, "BUY", quantity)
    
    def _get_conid(self, symbol: str) -> str:
        """Get contract ID for symbol"""
        response = self.session.get(
            f"{self.base_url}/trsrv/stocks?symbols={symbol}"
        )
        if response.status_code == 200:
            data = response.json()
            return data[symbol][0]["conid"]
        return None

class AutoTrader:
    """
    Automated trading based on predictor signals
    Connects to broker and executes trades
    """
    
    def __init__(self, broker: str, credentials: Dict[str, str]):
        self.broker = broker.lower()
        
        if self.broker == "tradezero":
            self.api = TradeZeroAPI(
                credentials.get("api_key"),
                credentials.get("api_secret")
            )
        elif self.broker == "ibkr" or self.broker == "interactivebrokers":
            self.api = InteractiveBrokersAPI(credentials.get("account_id"))
        else:
            raise ValueError("Broker must be 'tradezero' or 'ibkr'")
        
        self.predictor = None
        self.trading_enabled = False
    
    def enable_trading(self):
        """Enable automated trading"""
        if self.broker == "ibkr":
            if self.api.connect():
                self.trading_enabled = True
                print("✅ Auto trading enabled - IBKR")
        else:  # TradeZero (manual)
            self.trading_enabled = True
            print("✅ Manual trading enabled - Execute via TradeZero app")
    
    def analyze_and_trade(self, ticker: str):
        """Get prediction and execute trade"""
        if not self.trading_enabled:
            print("❌ Trading not enabled. Call enable_trading() first")
            return
        
        # Get prediction
        self.predictor = StockPredictor(ticker)
        self.predictor.fetch_data()
        self.predictor.calculate_indicators()
        signal = self.predictor.generate_signal()
        
        print(f"\n📊 Signal: {signal['action']}")
        print(f"   Confidence: {signal['confidence']:.0%}")
        
        # Determine position size
        capital = 10000  # Default, should come from account
        risk_per_trade = 0.02  # 2% risk
        position_size = (capital * risk_per_trade) / (signal['current_price'] * 0.05)  # 5% stop
        
        # Execute based on signal
        if "BUY" in signal['action']:
            print(f"\n🟢 Executing LONG order for {ticker}")
            print(f"   Position size: {position_size:.0f} shares")
            
            if self.broker == "ibkr":
                self.api.place_long(ticker, int(position_size))
            else:
                self.api.place_long_order(ticker, int(position_size))
                
        elif "SELL" in signal['action'] or "SHORT" in signal['action']:
            print(f"\n🔴 Executing SHORT order for {ticker}")
            print(f"   Position size: {position_size:.0f} shares")
            
            if self.broker == "ibkr":
                self.api.place_short(ticker, int(position_size))
            else:
                self.api.place_short_order(ticker, int(position_size))
        else:
            print("   No action taken - HOLD signal")
        
        return signal

# Example usage
if __name__ == "__main__":
    print("\n🔌 BROKER INTEGRATION SETUP")
    print("="*40)
    
    print("\nChoose broker:")
    print("1. TradeZero (manual execution)")
    print("2. Interactive Brokers (API auto-trading)")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == "1":
        trader = AutoTrader("tradezero", {})
        trader.enable_trading()
        
        ticker = input("Enter ticker to trade: ").upper()
        trader.analyze_and_trade(ticker)
        
    elif choice == "2":
        account = input("Enter IBKR account ID: ")
        trader = AutoTrader("ibkr", {"account_id": account})
        trader.enable_trading()
        
        if trader.trading_enabled:
            ticker = input("Enter ticker to trade: ").upper()
            trader.analyze_and_trade(ticker)
    
    print("\n💡 Note: Always verify trades before executing")
    print("⚠️ Never risk more than 1-2% per trade")
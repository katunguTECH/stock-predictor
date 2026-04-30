"""
Backtesting Engine
Test how trading signals would have performed historically
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from stock_predictor import StockPredictor

class Backtester:
    def __init__(self, ticker, initial_capital=10000):
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # Number of shares held
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, start_date, end_date):
        """Run backtest over historical period"""
        print(f"\n🔄 Backtesting {self.ticker} from {start_date} to {end_date}")
        
        # Get historical data
        stock = yf.Ticker(self.ticker)
        data = stock.history(start=start_date, end=end_date)
        
        if len(data) < 50:
            print("❌ Insufficient data for backtest")
            return None
        
        # Rolling prediction
        print("📊 Generating signals...")
        signals = []
        
        for i in range(50, len(data)):
            # Use only data up to current point
            historical_data = data.iloc[:i]
            
            # Create predictor and generate signal
            pred = StockPredictor(self.ticker)
            pred.data = historical_data.copy()
            pred.calculate_indicators()
            
            try:
                signal = pred.generate_signal()
                if signal:
                    # Map action to numeric signal
                    if "BUY" in signal['action']:
                        signals.append(1)  # Buy/long
                    elif "SELL" in signal['action'] or "SHORT" in signal['action']:
                        signals.append(-1)  # Sell/short
                    else:
                        signals.append(0)  # Hold
                else:
                    signals.append(0)
            except:
                signals.append(0)
        
        # Add first 50 days as neutral
        signals = [0] * 50 + signals
        
        # Execute trading strategy
        self.execute_strategy(data, signals)
        
        # Generate metrics
        return self.generate_report(data)
    
    def execute_strategy(self, data, signals):
        """Execute trades based on signals"""
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
        for i, (idx, row) in enumerate(data.iterrows()):
            price = row['Close']
            signal = signals[i]
            
            # Execute based on signal
            if signal == 1 and self.position == 0:
                # Buy signal - enter long position
                shares = int(self.capital / price)
                cost = shares * price
                self.position = shares
                self.capital -= cost
                self.trades.append({
                    'date': idx,
                    'type': 'BUY',
                    'price': price,
                    'shares': shares,
                    'value': cost
                })
                
            elif signal == -1 and self.position > 0:
                # Sell signal - exit position
                value = self.position * price
                self.capital += value
                self.trades.append({
                    'date': idx,
                    'type': 'SELL',
                    'price': price,
                    'shares': self.position,
                    'value': value
                })
                self.position = 0
            
            # Track equity
            current_equity = self.capital + (self.position * price)
            self.equity_curve.append({
                'date': idx,
                'equity': current_equity,
                'price': price,
                'signal': signal
            })
    
    def generate_report(self, data):
        """Calculate performance metrics"""
        equity_df = pd.DataFrame(self.equity_curve)
        
        if len(equity_df) == 0:
            print("No trades executed")
            return None
        
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Calculate daily returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe = equity_df['returns'].mean() / equity_df['returns'].std() * np.sqrt(252) if equity_df['returns'].std() > 0 else 0
        
        # Maximum drawdown
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min()
        
        # Win rate
        if len(self.trades) > 1:
            sell_trades = [t for t in self.trades if t['type'] == 'SELL']
            buy_trades = [t for t in self.trades if t['type'] == 'BUY']
            
            profits = []
            for sell in sell_trades:
                matching_buy = [b for b in buy_trades if b['date'] < sell['date']]
                if matching_buy:
                    buy = matching_buy[-1]
                    profit_pct = (sell['price'] - buy['price']) / buy['price']
                    profits.append(profit_pct)
            
            win_rate = sum(1 for p in profits if p > 0) / len(profits) if profits else 0
            avg_profit = np.mean(profits) if profits else 0
        else:
            win_rate = 0
            avg_profit = 0
        
        # Buy & hold benchmark
        buy_hold_return = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
        
        report = {
            'ticker': self.ticker,
            'period_start': equity_df['date'].iloc[0],
            'period_end': equity_df['date'].iloc[-1],
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'annualized_return': (1 + total_return) ** (252 / len(equity_df)) - 1 if len(equity_df) > 0 else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit,
            'number_of_trades': len([t for t in self.trades if t['type'] == 'BUY']),
            'buy_hold_return': buy_hold_return,
            'equity_curve': equity_df
        }
        
        return report
    
    def plot_results(self, report):
        """Visualize backtest results"""
        if not report:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Equity curve
        axes[0, 0].plot(report['equity_curve']['date'], report['equity_curve']['equity'])
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].axhline(y=report['initial_capital'], color='r', linestyle='--', alpha=0.5)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Drawdown
        axes[0, 1].fill_between(report['equity_curve']['date'], 
                                report['equity_curve']['drawdown'] * 100, 0, 
                                color='red', alpha=0.3)
        axes[0, 1].set_title('Drawdown')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Returns distribution
        returns = report['equity_curve']['returns'].dropna() * 100
        axes[1, 0].hist(returns, bins=50, alpha=0.7, color='blue')
        axes[1, 0].set_title('Daily Returns Distribution')
        axes[1, 0].set_xlabel('Return (%)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].axvline(x=0, color='r', linestyle='--')
        
        # Trade analysis
        trades_df = pd.DataFrame([t for t in self.trades if t['type'] in ['BUY', 'SELL']])
        if len(trades_df) > 0:
            trade_types = trades_df['type'].value_counts()
            axes[1, 1].bar(trade_types.index, trade_types.values)
            axes[1, 1].set_title('Trade Count')
            axes[1, 1].set_ylabel('Number of Trades')
        
        plt.suptitle(f'{report["ticker"]} Backtest Results', fontsize=16)
        plt.tight_layout()
        plt.show()
        
        # Print report
        print("\n" + "="*60)
        print(f"📊 BACKTEST REPORT: {report['ticker']}")
        print("="*60)
        print(f"Period: {report['period_start'].strftime('%Y-%m-%d')} to {report['period_end'].strftime('%Y-%m-%d')}")
        print(f"\n💰 Performance:")
        print(f"   Initial Capital: ${report['initial_capital']:,.2f}")
        print(f"   Final Equity:    ${report['final_equity']:,.2f}")
        print(f"   Total Return:    {report['total_return']:.2%}")
        print(f"   Annualized:      {report['annualized_return']:.2%}")
        print(f"   Buy & Hold:      {report['buy_hold_return']:.2%}")
        print(f"\n📈 Risk Metrics:")
        print(f"   Sharpe Ratio:    {report['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown:    {report['max_drawdown']:.2%}")
        print(f"\n🎯 Trade Stats:")
        print(f"   Number of Trades: {report['number_of_trades']}")
        print(f"   Win Rate:         {report['win_rate']:.1%}")
        print(f"   Avg Profit/Trade: {report['avg_profit_per_trade']:.2%}")
        print("="*60)

# Run backtest
if __name__ == "__main__":
    print("\n" + "📊"*30)
    print("BACKTESTING ENGINE")
    print("📊"*30)
    
    ticker = input("\nEnter stock ticker: ").upper()
    start_date = input("Start date (YYYY-MM-DD): ")
    end_date = input("End date (YYYY-MM-DD): ")
    
    backtester = Backtester(ticker, initial_capital=10000)
    report = backtester.run_backtest(start_date, end_date)
    
    if report:
        backtester.plot_results(report)
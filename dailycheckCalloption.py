import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def analyze_stock(ticker: str):
    stock = yf.Ticker(ticker)
    df = stock.history(period="6mo")
    if df.empty or len(df) < 50:
        return None

    # Calculate indicators
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Example Condition: Bullish Trend + RSI Rebound
    is_uptrend = latest['Close'] > latest['SMA_50']
    rsi_pullback_recovery = (prev['RSI'] < 50) and (latest['RSI'] >= 50)

    print(f"[{ticker}] Price: ${latest['Close']:.2f} | SMA50: ${latest['SMA_50']:.2f} | RSI: {latest['RSI']:.1f}")

    if is_uptrend and rsi_pullback_recovery:
        print(f"==> 🚀 Bullish Signal for {ticker}!")
        find_optimal_call_option(stock, latest['Close'])
    else:
        print(f"==> No trade signal today.")

def find_optimal_call_option(stock: yf.Ticker, current_price: float):
    expirations = stock.options
    target_date = None
    
    # Look for expiration between 30 and 50 days out
    today = datetime.today().date()
    for exp in expirations:
        exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
        dte = (exp_date - today).days
        if 30 <= dte <= 50:
            target_date = exp
            break

    if not target_date:
        print("No matching expiration date found.")
        return

    # Fetch option chain for target expiration
    opt_chain = stock.option_chain(target_date)
    calls = opt_chain.calls

    # Find Slightly ITM or ATM Call (Strike near or slightly below current price)
    suitable_calls = calls[(calls['strike'] <= current_price * 1.02) & 
                           (calls['strike'] >= current_price * 0.95)]
    
    if not suitable_calls.empty:
        # Pick the call with the highest open interest
        best_call = suitable_calls.sort_values(by="openInterest", ascending=False).iloc[0]
        print(f"Selected Contract: {target_date} Strike ${best_call['strike']}")
        print(f"Bid: ${best_call['bid']} | Ask: ${best_call['ask']} | OI: {best_call['openInterest']}")

if __name__ == "__main__":
    watchlist = ["AAPL", "MSFT", "SPY"]
    for sym in watchlist:
        analyze_stock(sym)
import pandas as pd
import time
from datetime import datetime
import os
from utils import load_config, is_simulation_mode
from indicators import calculate_vwap, calculate_ema
import ccxt  # For Kraken API integration

def execute_trade(order_type, amount, config, price):
    """Execute a live trade or simulate based on config."""
    if is_simulation_mode(config):
        print(f"Simulating {order_type} order for ${amount} at {price}")
        log_trade(order_type, amount, price)
    else:
        kraken = ccxt.kraken({
            'apiKey': config['kraken']['api_key'],
            'secret': config['kraken']['api_secret'],
        })

        try:
            order = kraken.create_order(
                symbol=config['trade_parameters']['symbol'],
                type='limit',  # Example type
                side=order_type.lower(),
                amount=amount,
                price=price
            )
            print(f"Live {order_type} order placed: {order}")
            log_trade(order_type, amount, price)
        except Exception as e:
            print(f"Error placing {order_type} order: {e}")

def log_trade(order_type, amount, price):
    """Log the trade to a CSV file for backtesting purposes."""
    trade_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order_type": order_type,
        "amount": amount,
        "price": price
    }
    log_path = os.path.join(os.path.dirname(__file__), '../logs/trade_log.csv')

    # Ensure that the logs directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Append to or create the CSV file
    df = pd.DataFrame([trade_data])
    df.to_csv(log_path, mode='a', header=not os.path.exists(log_path), index=False)

def main():
    config = load_config()
    open_orders_today = 0
    last_trade = None  # Track the last trade type ("BUY" or "SELL")

    # Simulated data for testing purposes (replace with live data fetching)
    data = pd.DataFrame({
        "close": [500, 502, 499, 501, 503, 505, 498, 497, 510, 507, 509, 506, 500, 495, 492, 500, 502, 510, 511, 513],
        "volume": [100, 110, 95, 105, 102, 98, 97, 100, 105, 110, 95, 101, 104, 99, 107, 108, 103, 106, 109, 111]
    })

    while True:
        # Calculate indicators
        vwap = calculate_vwap(data)
        ema_200 = calculate_ema(data, period=200)
        ema_20 = calculate_ema(data, period=20)

        current_price = data["close"].iloc[-1]

        # Debugging output to check values
        print(f"\nCurrent Price: {current_price}")
        print(f"VWAP: {vwap.iloc[-1]}")
        print(f"EMA 200: {ema_200.iloc[-1]}")
        print(f"EMA 20: {ema_20.iloc[-1]}")

        # SELL Condition (updated to original conditions)
        if vwap.iloc[-1] >= ema_200.iloc[-1] and vwap.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            if open_orders_today < config['trade_parameters']['max_orders_per_day'] and last_trade != "SELL":
                print("SELL condition met, executing sell order...")
                execute_trade("SELL", config['trade_parameters']['order_amount'], config, current_price)
                open_orders_today += 1
                last_trade = "SELL"  # Mark the last trade type as SELL

        # BUY Condition (updated to original conditions)
        if ema_20.iloc[-1] >= ema_200.iloc[-1] and ema_20.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            if open_orders_today < config['trade_parameters']['max_orders_per_day'] and last_trade != "BUY":
                print("BUY condition met, executing buy order...")
                execute_trade("BUY", config['trade_parameters']['order_amount'], config, current_price)
                open_orders_today += 1
                last_trade = "BUY"  # Mark the last trade type as BUY

        # Pause for live trading interval
        time.sleep(60)

if __name__ == "__main__":
    main()

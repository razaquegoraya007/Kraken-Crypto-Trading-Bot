import ccxt
import pandas as pd
import time
from datetime import datetime
import os
from utils import load_config, is_simulation_mode
from indicators import calculate_vwap, calculate_ema
import matplotlib.pyplot as plt

# Track cumulative profit and log each trade
trade_log = []
last_trade = None  # Track the last trade for PnL calculation

def execute_trade(order_type, amount, config, current_price):
    """Execute a live trade or simulate based on config."""
    if is_simulation_mode(config):
        print(f"Simulating {order_type} order for ${amount} at {current_price}")
        log_trade(order_type, amount, current_price)
    else:
        kraken_futures = ccxt.krakenfutures({
            'apiKey': config['kraken']['api_key'],
            'secret': config['kraken']['api_secret'],
            'urls': {
                'api': {
                    'public': 'https://demo-futures.kraken.com/derivatives/api/',
                    'private': 'https://demo-futures.kraken.com/derivatives/api/',
                }
            }
        })

        try:
            order_type_ccxt = 'market'
            price = current_price * 0.995 if order_type == "sell" else current_price * 1.005

            order = kraken_futures.create_order(
                symbol=config['trade_parameters']['symbol'],
                type=order_type_ccxt,
                side=order_type.lower(),
                amount=amount,
                price=price if order_type_ccxt == 'limit' else None
            )
            print(f"Live {order_type} order placed: {order}")
            log_trade(order_type, amount, current_price, order)
        except Exception as e:
            print(f"Error placing {order_type} order: {e}")

def log_trade(order_type, amount, price, order=None):
    """Log the trade details and calculate PnL for summary plotting."""
    global last_trade
    trade_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order_type": order_type,
        "amount": amount,
        "price": price,
        "status": "executed" if order else "simulated",
        "PnL": 0  # Default PnL value
    }

    if last_trade and last_trade["order_type"] != order_type:
        # Calculate PnL for alternating trades (BUY -> SELL or SELL -> BUY)
        if order_type == "SELL":
            trade_data["PnL"] = (price - last_trade["price"]) * amount
        elif order_type == "BUY":
            trade_data["PnL"] = (last_trade["price"] - price) * amount

        print(f"[TRADE] {order_type} at {price} with amount {amount}. PnL for this trade: {trade_data['PnL']:.2f}")

    # Update last_trade after PnL calculation
    last_trade = trade_data
    trade_log.append(trade_data)

    # Log cumulative PnL
    cumulative_PnL = sum(trade["PnL"] for trade in trade_log)
    print(f"[SUMMARY] Cumulative PnL after trade: {cumulative_PnL:.2f}")

    # Save to CSV
    log_path = os.path.join(os.path.dirname(__file__), '../logs/trade_log.csv')
    df = pd.DataFrame([trade_data])
    df.to_csv(log_path, mode='a', header=not os.path.exists(log_path), index=False)

def plot_trade_summary():
    """Plot cumulative PnL over time for a summary of trading performance."""
    df = pd.DataFrame(trade_log)
    df['cumulative_PnL'] = df['PnL'].cumsum()

    plt.figure(figsize=(10, 6))
    plt.plot(df['time'], df['cumulative_PnL'], label='Cumulative PnL', marker='o')
    plt.xlabel('Time')
    plt.ylabel('Cumulative PnL')
    plt.title('Trading Bot Performance Summary')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    config = load_config()
    open_orders_today = 0

    # Example data for testing purposes
    data = pd.DataFrame({
        "close": [500, 502, 499, 501, 503, 505, 498, 497, 510, 507, 509, 506, 500, 495, 492, 500, 502, 510, 511, 513],
        "volume": [100, 110, 95, 105, 102, 98, 97, 100, 105, 110, 95, 101, 104, 99, 107, 108, 103, 106, 109, 111]
    })

    while len(trade_log) < 3:  # Stop after 3 trades for testing
        # Calculate indicators
        vwap = calculate_vwap(data)
        ema_200 = calculate_ema(data, period=200)
        ema_20 = calculate_ema(data, period=20)

        current_price = data["close"].iloc[-1]

        print(f"\n[MARKET STATUS] Current Price: {current_price}")
        print(f"VWAP: {vwap.iloc[-1]}")
        print(f"EMA 200: {ema_200.iloc[-1]}")
        print(f"EMA 20: {ema_20.iloc[-1]}")

        # SELL Condition
        if vwap.iloc[-1] >= ema_200.iloc[-1] and vwap.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("SELL condition met, executing sell order...")
            execute_trade("SELL", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1

        # BUY Condition
        elif ema_20.iloc[-1] >= ema_200.iloc[-1] and ema_20.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("BUY condition met, executing buy order...")
            execute_trade("BUY", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1

        time.sleep(5)

    # Plot summary after stopping the loop
    plot_trade_summary()

if __name__ == "__main__":
    main()

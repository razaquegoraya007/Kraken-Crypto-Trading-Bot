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

def execute_trade(order_type, amount_usd, config, current_price):
    """Execute a live trade or simulate based on config."""
    kraken_futures = ccxt.krakenfutures({
        'apiKey': config['kraken']['api_key'],
        'secret': config['kraken']['api_secret']
    })

    # Convert USD amount to asset amount
    amount_asset = amount_usd / current_price
    min_trade_amount = 1  # Check Kraken's documentation for the exact minimum value

    # Ensure the amount is greater than minimum precision
    if amount_asset < min_trade_amount:
        print(f"[ERROR] Amount of {amount_asset} is less than the minimum required {min_trade_amount}. Adjusting amount...")
        amount_asset = min_trade_amount

    # Check simulation mode
    if config.get('simulation_mode', True):
        print(f"Simulating {order_type} order for {amount_asset} units at {current_price}")
        log_trade(order_type, amount_asset, current_price)
    else:
        try:
            order_type_ccxt = 'market'
            symbol = config['trade_parameters']['symbol']
            take_profit = config['trade_parameters']['take_profit']
            trailing_stop_loss = config['trade_parameters']['trailing_stop_loss']

            print("[DEBUG] Attempting to place SELL order...")
            print(f"[DEBUG] Symbol: {symbol}")
            print(f"[DEBUG] Order type: {order_type_ccxt}")
            print(f"[DEBUG] Amount: {amount_asset}")
            print(f"[DEBUG] Current Price: {current_price}")

            # Place the market order
            order = kraken_futures.create_order(
                symbol=symbol,
                type=order_type_ccxt,
                side=order_type.lower(),
                amount=amount_asset
            )
            print(f"Live {order_type} order placed: {order}")

            # Place take profit and stop loss orders if needed
            if take_profit:
                take_profit_price = current_price * take_profit if order_type == "BUY" else current_price / take_profit
                print(f"[DEBUG] Setting Take Profit at {take_profit_price}")
                # Place take profit order here using Kraken API

            if trailing_stop_loss:
                stop_loss_price = current_price * (1 - trailing_stop_loss) if order_type == "BUY" else current_price * (1 + trailing_stop_loss)
                print(f"[DEBUG] Setting Stop Loss at {stop_loss_price}")
                # Place stop loss order here using Kraken API

            log_trade(order_type, amount_asset, current_price, order)
        except Exception as e:
            print(f"[ERROR] Error placing {order_type} order: {e}")



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

    if last_trade:
        # Calculate PnL based on trade direction
        if last_trade["order_type"] == "BUY" and order_type == "SELL":
            # Profit = (Sell Price - Buy Price) * Amount
            trade_data["PnL"] = (price - last_trade["price"]) * amount
        elif last_trade["order_type"] == "SELL" and order_type == "BUY":
            # Profit = (Buy Price - Sell Price) * Amount
            trade_data["PnL"] = (last_trade["price"] - price) * amount

        print(f"[TRADE] {order_type} at {price} with amount {amount}. PnL for this trade: {trade_data['PnL']:.2f}")

    # Update the last trade details
    last_trade = trade_data
    trade_log.append(trade_data)

    # Calculate cumulative PnL
    cumulative_PnL = sum(trade["PnL"] for trade in trade_log)
    print(f"[SUMMARY] Cumulative PnL after trade: {cumulative_PnL:.2f}")

    # Log order details if it's a live order
    if order:
        print("\n=== Live Order Details ===")
        print(f"Order Type: {order_type}")
        print(f"Status: {order['info'].get('status', 'N/A')}")
        print(f"Order ID: {order['id']}")
        print(f"Symbol: {order['symbol']}")
        print(f"Price: {order['price']}")
        print(f"Amount: {order['amount']}")
        print(f"Average Executed Price: {order.get('average', 'N/A')}")
        print(f"Filled: {order['filled']}")
        print(f"Remaining: {order['remaining']}")
        print(f"Order Status: {order['status']}")

        print("\nExecution Details:")
        for i, execution in enumerate(order['info'].get('orderEvents', []), start=1):
            exec_price = execution.get('price')
            exec_amount = execution.get('amount')
            exec_id = execution.get('executionId')
            print(f"  Execution {i}:")
            print(f"    Execution ID: {exec_id}")
            print(f"    Price: {exec_price}")
            print(f"    Amount: {exec_amount}")

        print(f"\nTotal Cost: {order.get('cost', 'N/A')}")
        print(f"Fees: {order.get('fees', 'None')}")
        print("=== End of Order Details ===\n")

    # Save the trade log to a CSV file
    log_path = os.path.join(os.path.dirname(__file__), '../logs/trade_log.csv')
    df = pd.DataFrame([trade_data])
    df.to_csv(log_path, mode='a', header=not os.path.exists(log_path), index=False)



def plot_trade_summary():
    """Plot cumulative PnL over time for a summary of trading performance."""
    if not trade_log:
        print("[ERROR] No PnL data available to plot.")
        return

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

    data = pd.DataFrame({
        "close": [500, 502, 499, 501, 503, 505, 498, 497, 510, 507, 509, 506, 500, 495, 492, 500, 502, 510, 511, 513],
        "volume": [100, 110, 95, 105, 102, 98, 97, 100, 105, 110, 95, 101, 104, 99, 107, 108, 103, 106, 109, 111]
    })

    while len(trade_log) < 3:  # Stop after 3 trades for testing
        vwap = calculate_vwap(data)
        ema_200 = calculate_ema(data, period=200)
        ema_20 = calculate_ema(data, period=20)

        current_price = data["close"].iloc[-1]

        print(f"\n[MARKET STATUS] Current Price: {current_price}")
        print(f"VWAP: {vwap.iloc[-1]}")
        print(f"EMA 200: {ema_200.iloc[-1]}")
        print(f"EMA 20: {ema_20.iloc[-1]}")

        if vwap.iloc[-1] >= ema_200.iloc[-1] and vwap.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("SELL condition met, executing sell order...")
            execute_trade("SELL", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1
        elif ema_20.iloc[-1] >= ema_200.iloc[-1] and ema_20.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("BUY condition met, executing buy order...")
            execute_trade("BUY", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1

        time.sleep(5)

    plot_trade_summary()

if __name__ == "__main__":
    main()

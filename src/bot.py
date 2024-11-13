import ccxt
import pandas as pd
import time
from datetime import datetime

# Load your configuration
from utils import load_config
from indicators import calculate_vwap, calculate_ema

# Track cumulative profit and log each trade
trade_log = []
last_trade = None

def calculate_tp_sl(order_type, current_price):
    """Calculate Take Profit and Stop Loss prices within reasonable bounds."""
    tp_percentage = 0.01  # 1% for Take Profit
    sl_percentage = 0.01  # 1% for Stop Loss

    if order_type == "SELL":
        take_profit_price = current_price * (1 - tp_percentage)
        stop_loss_price = current_price * (1 + sl_percentage)
    elif order_type == "BUY":
        take_profit_price = current_price * (1 + tp_percentage)
        stop_loss_price = current_price * (1 - sl_percentage)

    return round(take_profit_price, 2), round(stop_loss_price, 2)

def execute_trade(order_type, amount, config, current_price):
    """Execute a live trade with adjusted TP, SL, and a limit price."""
    kraken_futures = ccxt.krakenfutures({
        'apiKey': config['kraken']['api_key'],
        'secret': config['kraken']['api_secret']
    })

    try:
        # Calculate Take Profit and Stop Loss prices
        take_profit_price, stop_loss_price = calculate_tp_sl(order_type, current_price)
        limit_price = current_price * (0.99 if order_type == "SELL" else 1.01)  # Slightly favorable limit price

        print(f"[DEBUG] Setting Take Profit at {take_profit_price}")
        print(f"[DEBUG] Setting Stop Loss at {stop_loss_price}")
        print(f"[DEBUG] Setting Limit Price at {limit_price}")

        # Place the order with Kraken Futures
        order = kraken_futures.create_order(
            symbol=config['trade_parameters']['symbol'],
            type="limit",
            side=order_type.lower(),
            amount=amount,
            price=limit_price,  # Set the limit price
            params={
                'stopLossPrice': stop_loss_price,
                'takeProfitPrice': take_profit_price,
                'reduceOnly': False
            }
        )

        print("Live", order_type, "order placed:", order)
        log_trade(order_type, amount, current_price, order)
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

    # Calculate PnL
    if last_trade and last_trade["order_type"] != order_type:
        if order_type == "SELL":
            trade_data["PnL"] = (price - last_trade["price"]) * amount
        elif order_type == "BUY":
            trade_data["PnL"] = (last_trade["price"] - price) * amount
        print(f"[TRADE] {order_type} at {price} with amount {amount}. PnL: {trade_data['PnL']:.2f}")

    last_trade = trade_data
    trade_log.append(trade_data)

    cumulative_PnL = sum(trade["PnL"] for trade in trade_log)
    print(f"[SUMMARY] Cumulative PnL: {cumulative_PnL:.2f}")

    # Log order details
    if order:
        print("\n=== Live Order Details ===")
        print(f"Order Type: {order_type}")
        print(f"Status: {order['info'].get('status', 'N/A')}")
        print(f"Order ID: {order['id']}")
        print(f"Symbol: {order['symbol']}")
        print(f"Price: {order.get('price', 'N/A')}")
        print(f"Amount: {order['amount']}")
        print(f"Average Executed Price: {order.get('average', 'N/A')}")
        print(f"Filled: {order['filled']}")
        print(f"Remaining: {order['remaining']}")
        print(f"Order Status: {order['status']}")
        print("=== End of Order Details ===\n")

def main():
    config = load_config()
    open_orders_today = 0

    # Load your live data here
    data = pd.DataFrame({
        "close": [500, 502, 499, 501, 503, 505, 498, 497, 510, 507, 509, 506, 500, 495, 492, 500, 502, 510, 511, 513],
        "volume": [100, 110, 95, 105, 102, 98, 97, 100, 105, 110, 95, 101, 104, 99, 107, 108, 103, 106, 109, 111]
    })

    # Trading loop
    while len(trade_log) < config['trade_parameters']['max_orders_per_day']:
        vwap = calculate_vwap(data)
        ema_200 = calculate_ema(data, period=200)
        ema_20 = calculate_ema(data, period=20)
        current_price = data["close"].iloc[-1]

        print(f"\n[MARKET STATUS] Current Price: {current_price}")
        print(f"VWAP: {vwap.iloc[-1]}, EMA 200: {ema_200.iloc[-1]}, EMA 20: {ema_20.iloc[-1]}")

        if vwap.iloc[-1] >= ema_200.iloc[-1] and vwap.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("SELL condition met, executing sell order...")
            execute_trade("SELL", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1
        elif ema_20.iloc[-1] >= ema_200.iloc[-1] and ema_20.iloc[-1] <= (ema_200.iloc[-1] * 1.02):
            print("BUY condition met, executing buy order...")
            execute_trade("BUY", config['trade_parameters']['order_amount'], config, current_price)
            open_orders_today += 1

        time.sleep(5)

if __name__ == "__main__":
    main()

import ccxt
import yaml
import os

def load_config():
    """Load the configuration file."""
    with open(os.path.join(os.path.dirname(__file__), '../config/config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    return config

def test_order():
    config = load_config()

    kraken = ccxt.kraken({
        'apiKey': config['kraken']['api_key'],
        'secret': config['kraken']['api_secret'],
    })

    try:
        # Replace 'BTC/USD' with a trading pair that is valid and small for testing, e.g., 'BTC/USDT' or 'BTC/USD'
        symbol = "BTC/USD"
        order_type = "market"
        side = "buy"  # Change to "sell" if you prefer to test a sell order
        amount = 0.0001  # Very small amount to minimize cost

        print(f"Attempting to place a test {side.upper()} order for {amount} {symbol}...")
        order = kraken.create_order(symbol=symbol, type=order_type, side=side, amount=amount)
        print("Order successfully placed:", order)
    except Exception as e:
        print(f"Error placing test order: {e}")

if __name__ == "__main__":
    test_order()

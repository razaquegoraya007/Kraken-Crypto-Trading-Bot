import ccxt
import yaml
import os

def load_config():
    """Load the configuration file."""
    with open(os.path.join(os.path.dirname(__file__), '../config/config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    return config

def print_demo_symbols():
    config = load_config()

    # Initialize Kraken futures instance with demo environment URLs
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
        markets = kraken_futures.load_markets()
        print("Available symbols on Kraken Futures Demo:")
        for symbol in markets:
            print(symbol)
    except Exception as e:
        print(f"Error fetching symbols from Kraken Futures Demo: {e}")

if __name__ == "__main__":
    print_demo_symbols()

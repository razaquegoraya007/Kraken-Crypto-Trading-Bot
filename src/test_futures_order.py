import ccxt
import yaml
import os

def load_config():
    """Load the configuration file."""
    with open(os.path.join(os.path.dirname(__file__), '../config/config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    return config

def check_endpoint():
    config = load_config()
    kraken_futures = ccxt.krakenfutures({
        'apiKey': config['kraken']['api_key'],
        'secret': config['kraken']['api_secret'],
    })

    # Print the API URLs for Kraken Futures
    print("Kraken Futures API URLs:")
    print(kraken_futures.urls)

if __name__ == "__main__":
    check_endpoint()

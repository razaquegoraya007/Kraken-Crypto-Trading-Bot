import yaml
import os

def load_config():
    """Load the configuration file."""
    with open(os.path.join(os.path.dirname(__file__), '../config/config.yaml'), 'r') as file:
        config = yaml.safe_load(file)
    return config

def is_simulation_mode(config):
    """Check if simulation mode is enabled."""
    return config.get('simulation_mode', False)

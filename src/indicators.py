import pandas as pd

def calculate_vwap(data):
    """Calculate VWAP (Volume Weighted Average Price)"""
    q = data['volume']
    p = data['close']
    vwap = (p * q).cumsum() / q.cumsum()
    return vwap

def calculate_ema(data, period):
    """Calculate Exponential Moving Average (EMA)"""
    return data['close'].ewm(span=period, adjust=False).mean()

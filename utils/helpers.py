import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logger(name):
    return logging.getLogger(name)

def calculate_position_size(account_balance, risk_percent, entry_price, stop_loss_price):
    risk_amount = account_balance * (risk_percent / 100)
    price_diff = abs(entry_price - stop_loss_price)
    if price_diff == 0:
        return 0
    position_size = risk_amount / price_diff
    return position_size

def format_number(num, decimals=2):
    if num is None or np.isnan(num):
        return "N/A"
    return f"{num:.{decimals}f}"

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp / 1000)

def get_market_structure_change(df):
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    
    if len(closes) < 3:
        return 'neutral'
    
    if closes[-1] > closes[-2] > closes[-3]:
        return 'bullish'
    elif closes[-1] < closes[-2] < closes[-3]:
        return 'bearish'
    else:
        return 'neutral'

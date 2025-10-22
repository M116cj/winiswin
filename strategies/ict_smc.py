import numpy as np
import pandas as pd
from utils.helpers import setup_logger, get_market_structure_change

logger = setup_logger(__name__)

class ICTSMCStrategy:
    def __init__(self):
        self.name = "ICT/SMC Strategy"
        self.order_blocks = []
        self.liquidity_zones = []
    
    def identify_order_blocks(self, df, lookback=20):
        order_blocks = []
        
        for i in range(lookback, len(df)):
            current_close = df.iloc[i]['close']
            prev_close = df.iloc[i-1]['close']
            
            if current_close > prev_close * 1.02:
                order_block = {
                    'type': 'bullish',
                    'high': df.iloc[i]['high'],
                    'low': df.iloc[i-1]['low'],
                    'timestamp': df.iloc[i]['timestamp']
                }
                order_blocks.append(order_block)
            
            elif current_close < prev_close * 0.98:
                order_block = {
                    'type': 'bearish',
                    'high': df.iloc[i-1]['high'],
                    'low': df.iloc[i]['low'],
                    'timestamp': df.iloc[i]['timestamp']
                }
                order_blocks.append(order_block)
        
        self.order_blocks = order_blocks[-5:]
        return self.order_blocks
    
    def identify_liquidity_zones(self, df, lookback=50):
        liquidity_zones = []
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(lookback, len(df)):
            window_highs = highs[i-lookback:i]
            window_lows = lows[i-lookback:i]
            
            current_high = highs[i]
            current_low = lows[i]
            
            if current_high >= np.max(window_highs):
                liquidity_zones.append({
                    'type': 'resistance',
                    'price': current_high,
                    'timestamp': df.iloc[i]['timestamp']
                })
            
            if current_low <= np.min(window_lows):
                liquidity_zones.append({
                    'type': 'support',
                    'price': current_low,
                    'timestamp': df.iloc[i]['timestamp']
                })
        
        self.liquidity_zones = liquidity_zones[-5:]
        return self.liquidity_zones
    
    def check_market_structure(self, df):
        if len(df) < 10:
            return None
        
        market_structure = get_market_structure_change(df)
        
        higher_highs = df['high'].iloc[-3:].is_monotonic_increasing
        higher_lows = df['low'].iloc[-3:].is_monotonic_increasing
        
        lower_highs = df['high'].iloc[-3:].is_monotonic_decreasing
        lower_lows = df['low'].iloc[-3:].is_monotonic_decreasing
        
        if higher_highs and higher_lows:
            return 'bullish_structure'
        elif lower_highs and lower_lows:
            return 'bearish_structure'
        else:
            return 'neutral_structure'
    
    def generate_signal(self, df):
        if len(df) < 50:
            logger.warning("Insufficient data for ICT/SMC analysis")
            return None
        
        self.identify_order_blocks(df)
        self.identify_liquidity_zones(df)
        structure = self.check_market_structure(df)
        
        current_price = df.iloc[-1]['close']
        macd = df.iloc[-1]['macd']
        macd_signal = df.iloc[-1]['macd_signal']
        ema_9 = df.iloc[-1]['ema_9']
        ema_21 = df.iloc[-1]['ema_21']
        
        signal = None
        
        if (structure == 'bullish_structure' and 
            macd > macd_signal and 
            ema_9 > ema_21 and 
            current_price > ema_9):
            
            for zone in self.liquidity_zones:
                if zone['type'] == 'support' and abs(current_price - zone['price']) < current_price * 0.01:
                    signal = {
                        'type': 'BUY',
                        'price': current_price,
                        'reason': 'Bullish structure + MACD crossover + price at support',
                        'confidence': 0.75
                    }
                    break
        
        elif (structure == 'bearish_structure' and 
              macd < macd_signal and 
              ema_9 < ema_21 and 
              current_price < ema_9):
            
            for zone in self.liquidity_zones:
                if zone['type'] == 'resistance' and abs(current_price - zone['price']) < current_price * 0.01:
                    signal = {
                        'type': 'SELL',
                        'price': current_price,
                        'reason': 'Bearish structure + MACD crossover + price at resistance',
                        'confidence': 0.75
                    }
                    break
        
        if signal:
            logger.info(f"ICT/SMC Signal: {signal['type']} at {signal['price']} - {signal['reason']}")
        
        return signal

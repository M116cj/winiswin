import numpy as np
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class ArbitrageStrategy:
    def __init__(self, threshold=0.005):
        self.name = "Arbitrage Strategy"
        self.threshold = threshold
    
    def check_spot_futures_arbitrage(self, spot_price, futures_price):
        if spot_price is None or futures_price is None or spot_price == 0:
            return None
        
        price_diff_percent = ((futures_price - spot_price) / spot_price) * 100
        
        if abs(price_diff_percent) > self.threshold * 100:
            if futures_price > spot_price:
                signal = {
                    'type': 'CASH_AND_CARRY',
                    'action': 'BUY_SPOT_SELL_FUTURES',
                    'spot_price': spot_price,
                    'futures_price': futures_price,
                    'spread_percent': price_diff_percent,
                    'expected_profit': price_diff_percent
                }
            else:
                signal = {
                    'type': 'REVERSE_CASH_AND_CARRY',
                    'action': 'SELL_SPOT_BUY_FUTURES',
                    'spot_price': spot_price,
                    'futures_price': futures_price,
                    'spread_percent': price_diff_percent,
                    'expected_profit': abs(price_diff_percent)
                }
            
            logger.info(f"Arbitrage opportunity: {signal['type']} - Spread: {price_diff_percent:.4f}%")
            return signal
        
        return None
    
    def check_triangular_arbitrage(self, prices):
        btc_usdt = prices.get('BTCUSDT')
        eth_usdt = prices.get('ETHUSDT')
        eth_btc = prices.get('ETHBTC')
        
        if not all([btc_usdt, eth_usdt, eth_btc]):
            return None
        
        implied_eth_usdt = eth_btc * btc_usdt
        
        price_diff_percent = ((implied_eth_usdt - eth_usdt) / eth_usdt) * 100
        
        if abs(price_diff_percent) > self.threshold * 100:
            if implied_eth_usdt > eth_usdt:
                signal = {
                    'type': 'TRIANGULAR_ARBITRAGE',
                    'path': 'USDT -> BTC -> ETH -> USDT',
                    'expected_profit': price_diff_percent,
                    'prices': {
                        'BTCUSDT': btc_usdt,
                        'ETHBTC': eth_btc,
                        'ETHUSDT': eth_usdt,
                        'implied_ETHUSDT': implied_eth_usdt
                    }
                }
            else:
                signal = {
                    'type': 'TRIANGULAR_ARBITRAGE',
                    'path': 'USDT -> ETH -> BTC -> USDT',
                    'expected_profit': abs(price_diff_percent),
                    'prices': {
                        'BTCUSDT': btc_usdt,
                        'ETHBTC': eth_btc,
                        'ETHUSDT': eth_usdt,
                        'implied_ETHUSDT': implied_eth_usdt
                    }
                }
            
            logger.info(f"Triangular arbitrage opportunity: {signal['path']} - Profit: {price_diff_percent:.4f}%")
            return signal
        
        return None
    
    def generate_signal(self, market_data):
        signals = []
        
        spot_futures_signal = self.check_spot_futures_arbitrage(
            market_data.get('spot_price'),
            market_data.get('futures_price')
        )
        if spot_futures_signal:
            signals.append(spot_futures_signal)
        
        triangular_signal = self.check_triangular_arbitrage(market_data.get('prices', {}))
        if triangular_signal:
            signals.append(triangular_signal)
        
        return signals if signals else None

import asyncio
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
import pandas as pd
import numpy as np
from config import Config
from utils.helpers import setup_logger, timestamp_to_datetime

logger = setup_logger(__name__)

class BinanceDataClient:
    def __init__(self):
        self.api_key = Config.BINANCE_API_KEY
        self.api_secret = Config.BINANCE_SECRET_KEY
        self.testnet = Config.BINANCE_TESTNET
        
        if not self.api_key or not self.api_secret:
            logger.warning("Binance API credentials not configured. Please set BINANCE_API_KEY and BINANCE_SECRET_KEY.")
            self.client = None
            self.async_client = None
            self.bsm = None
            return
        
        try:
            if self.testnet:
                self.client = Client(
                    self.api_key, 
                    self.api_secret,
                    testnet=True
                )
                logger.info("Initialized Binance client in TESTNET mode")
            else:
                self.client = Client(self.api_key, self.api_secret)
                logger.info("Initialized Binance client in LIVE mode")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            self.client = None
        
        self.async_client = None
        self.bsm = None
    
    async def initialize_async(self):
        if not self.api_key or not self.api_secret:
            logger.warning("Cannot initialize async client - credentials not configured")
            return
        
        self.async_client = await AsyncClient.create(
            self.api_key, 
            self.api_secret,
            testnet=self.testnet
        )
        self.bsm = BinanceSocketManager(self.async_client)
        logger.info("Async client initialized")
    
    def get_klines(self, symbol, interval='1h', limit=500):
        if not self.client:
            logger.error("Binance client not initialized")
            return None
        
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            logger.info(f"Fetched {len(df)} klines for {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
    
    def get_ticker_price(self, symbol):
        if not self.client:
            return None
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def get_account_balance(self):
        if not self.client:
            return {}
        try:
            account = self.client.get_account()
            balances = {}
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances[asset] = {'free': free, 'locked': locked, 'total': free + locked}
            return balances
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return {}
    
    def get_funding_rate(self, symbol):
        try:
            funding_rate = self.client.futures_funding_rate(symbol=symbol, limit=1)
            if funding_rate:
                return float(funding_rate[0]['fundingRate'])
            return None
        except Exception as e:
            logger.error(f"Error fetching funding rate for {symbol}: {e}")
            return None
    
    def get_long_short_ratio(self, symbol):
        try:
            ratio = self.client.futures_top_longshort_account_ratio(symbol=symbol, period='1h', limit=1)
            if ratio:
                return {
                    'long_account': float(ratio[0]['longAccount']),
                    'short_account': float(ratio[0]['shortAccount']),
                    'long_short_ratio': float(ratio[0]['longShortRatio'])
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching long/short ratio for {symbol}: {e}")
            return None
    
    def place_order(self, symbol, side, order_type, quantity, price=None):
        if not Config.ENABLE_TRADING:
            logger.warning("Trading is disabled. Set ENABLE_TRADING=true to enable.")
            return None
        
        try:
            if order_type == 'MARKET':
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
            else:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity,
                    price=price,
                    timeInForce='GTC'
                )
            
            logger.info(f"Order placed: {order}")
            return order
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def close_async(self):
        if self.async_client:
            await self.async_client.close_connection()
            logger.info("Async client closed")

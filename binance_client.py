import asyncio
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
from config import Config
from utils.helpers import setup_logger, timestamp_to_datetime, retry_on_failure, async_retry_on_failure

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
    
    @retry_on_failure(
        max_retries=3,
        backoff_factor=1.0,
        exceptions=(ConnectionError, TimeoutError, BinanceAPIException)
    )
    def get_klines(self, symbol, interval='1h', limit=500):
        """
        獲取 K 線數據（帶重試）
        
        重試策略：
        - 第 1 次失敗：等待 1 秒
        - 第 2 次失敗：等待 2 秒  
        - 第 3 次失敗：等待 4 秒
        - 仍失敗：拋出異常
        """
        if not self.client:
            raise RuntimeError("Binance client not initialized")
        
        klines = self.client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        # 數據驗證
        if not klines or len(klines) < 50:
            raise ValueError(f"Insufficient klines data: {len(klines)} < 50")
        
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
    
    @retry_on_failure(
        max_retries=2,
        backoff_factor=0.5,
        exceptions=(ConnectionError, TimeoutError, BinanceAPIException)
    )
    def get_ticker_price(self, symbol):
        """
        獲取最新價格（輕量級，快速重試）
        
        重試策略：
        - 第 1 次失敗：等待 0.5 秒
        - 第 2 次失敗：等待 1 秒
        - 仍失敗：拋出異常
        """
        if not self.client:
            raise RuntimeError("Binance client not initialized")
        
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    
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
    
    def get_futures_balance(self):
        """Get USDT-M futures account USDT balance."""
        if not self.client:
            return 0.0
        try:
            # Method 1: Try to get account balance (more accurate)
            try:
                balances = self.client.futures_account_balance()
                for balance in balances:
                    if balance['asset'] == 'USDT':
                        usdt_balance = float(balance['balance'])
                        logger.debug(f"Futures USDT balance (from account_balance): {usdt_balance}")
                        return usdt_balance
            except Exception as e:
                logger.debug(f"futures_account_balance failed, trying totalWalletBalance: {e}")
            
            # Method 2: Fallback to totalWalletBalance
            account = self.client.futures_account()
            total_balance = float(account.get('totalWalletBalance', 0.0))
            logger.debug(f"Futures balance (from totalWalletBalance): {total_balance}")
            return total_balance
            
        except Exception as e:
            logger.error(f"Error fetching futures balance: {e}")
            return 0.0
    
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
    
    def get_all_usdt_perpetual_pairs(self):
        """獲取所有 USDT 永續合約交易對"""
        if not self.client:
            logger.error("Binance client not initialized")
            return ['BTCUSDT', 'ETHUSDT']
        
        try:
            exchange_info = self.client.futures_exchange_info()
            
            usdt_pairs = [
                symbol['symbol'] 
                for symbol in exchange_info['symbols'] 
                if symbol['contractType'] == 'PERPETUAL' 
                and symbol['quoteAsset'] == 'USDT'
                and symbol['status'] == 'TRADING'
            ]
            
            logger.info(f"Found {len(usdt_pairs)} USDT perpetual pairs")
            return usdt_pairs
        
        except Exception as e:
            logger.error(f"Error fetching trading pairs: {e}")
            return ['BTCUSDT', 'ETHUSDT']
    
    def get_top_pairs_by_volume(self, limit=50):
        """獲取按24小時成交量排序的前N個交易對"""
        if not self.client:
            logger.error("Binance client not initialized")
            return ['BTCUSDT', 'ETHUSDT']
        
        try:
            all_pairs = self.get_all_usdt_perpetual_pairs()
            
            tickers = self.client.futures_ticker()
            
            usdt_tickers = [
                ticker for ticker in tickers 
                if ticker['symbol'] in all_pairs
            ]
            
            sorted_tickers = sorted(
                usdt_tickers, 
                key=lambda x: float(x.get('quoteVolume', 0)), 
                reverse=True
            )
            
            top_pairs = [ticker['symbol'] for ticker in sorted_tickers[:limit]]
            
            logger.info(f"Selected top {len(top_pairs)} pairs by 24h volume")
            
            for i, pair in enumerate(top_pairs[:10]):
                volume = float([t for t in sorted_tickers if t['symbol'] == pair][0]['quoteVolume'])
                logger.info(f"  {i+1}. {pair}: ${volume:,.0f} (24h volume)")
            
            return top_pairs
        
        except Exception as e:
            logger.error(f"Error fetching top pairs: {e}")
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
    
    async def get_klines_async(self, symbol, interval='1h', limit=500):
        """Async version of get_klines for non-blocking data fetch."""
        if not self.async_client:
            await self.initialize_async()
        
        if not self.async_client:
            logger.error("Async client not available")
            return None
        
        try:
            klines = await self.async_client.get_klines(
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
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching async klines for {symbol}: {e}")
            return None
    
    async def get_ticker(self, symbol):
        """Async get ticker (v3.0 compatible method)."""
        if not self.async_client:
            await self.initialize_async()
        
        if not self.async_client:
            return None
        
        try:
            ticker = await self.async_client.get_symbol_ticker(symbol=symbol)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def create_order(self, symbol, side, type, quantity, price=None):
        """Create order (v3.0 compatible method)."""
        return self.place_order(symbol, side, type, quantity, price)
    
    async def get_usdt_perpetual_symbols(self):
        """Async get all USDT perpetual symbols (v3.0 compatible)."""
        return self.get_all_usdt_perpetual_pairs()
    
    async def close_async(self):
        if self.async_client:
            await self.async_client.close_connection()
            logger.info("Async client closed")


# Alias for backwards compatibility
BinanceClient = BinanceDataClient

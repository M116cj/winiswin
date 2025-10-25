import asyncio
import time
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException
from binance.helpers import round_step_size
import pandas as pd
import numpy as np
import math
from config import Config
from utils.helpers import setup_logger, timestamp_to_datetime, retry_on_failure, async_retry_on_failure

logger = setup_logger(__name__)

# 手動黑名單：確實無效的交易對（極少數）
# 說明：大部分有效交易對通過 API 動態獲取（status='TRADING'）
# 此黑名單僅用於過濾測試符號或格式錯誤的交易對
INVALID_SYMBOLS = {
    # 測試符號（非正式交易對）
    "测试测试USDT", "币安人生USDT"
}

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
            self.symbol_info_cache = {}
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
        self.symbol_info_cache = {}
        
        # 動態交易對驗證緩存（TTL: 1小時）
        self.valid_symbols_cache = None
        self.valid_symbols_cache_time = None
    
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
        
        # 數據驗證（動態閾值：至少 10 條或請求數量的 20%，取較大值）
        # 對於技術分析，我們需要足夠的數據點
        min_required = max(10, int(limit * 0.2))
        if not klines or len(klines) < min_required:
            raise ValueError(f"Insufficient klines data: {len(klines)} < {min_required} (requested: {limit})")
        
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
        獲取期貨合約最新價格（輕量級，快速重試）
        
        重試策略：
        - 第 1 次失敗：等待 0.5 秒
        - 第 2 次失敗：等待 1 秒
        - 仍失敗：拋出異常
        """
        if not self.client:
            raise RuntimeError("Binance client not initialized")
        
        # ✅ 使用期貨 API 獲取價格
        ticker = self.client.futures_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    
    def get_account_balance(self):
        """
        ⚠️ DEPRECATED: This method uses Spot API (get_account) which is not needed.
        Use get_futures_balance() instead for futures trading.
        
        This method is kept for backward compatibility but disabled.
        """
        logger.warning(
            "get_account_balance() is deprecated and disabled. "
            "Use get_futures_balance() for futures trading."
        )
        return {}
    
    def get_futures_balance(self):
        """
        Get USDT-M futures account USDT balance.
        
        Returns:
            float: Actual balance (can be 0.0 if account is empty)
            None: API call failed
        """
        if not self.client:
            return None
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
            return None
    
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
    
    def get_valid_futures_symbols(self):
        """
        獲取所有有效的 USDT 永續合約交易對（帶 TTL 緩存）
        
        緩存策略：
        - TTL: 1 小時（3600 秒）
        - 緩存命中時直接返回，避免重複 API 調用
        - 緩存過期時重新從 API 獲取
        
        Returns:
            Set of valid USDT perpetual contract symbols with status='TRADING'
        """
        # 檢查緩存是否有效（TTL: 1 小時）
        cache_ttl = 3600  # 1 小時
        current_time = time.time()
        
        if (self.valid_symbols_cache is not None and 
            self.valid_symbols_cache_time is not None and 
            current_time - self.valid_symbols_cache_time < cache_ttl):
            logger.debug(
                f"✅ Using cached valid symbols "
                f"(age: {int(current_time - self.valid_symbols_cache_time)}s, "
                f"TTL: {cache_ttl}s)"
            )
            return self.valid_symbols_cache
        
        # 緩存過期或不存在，從 API 獲取
        if not self.client:
            logger.error("Binance client not initialized")
            return set()
        
        try:
            logger.info("🔄 Fetching valid futures symbols from Binance API...")
            exchange_info = self.client.futures_exchange_info()
            
            # 過濾有效的 USDT 永續合約（status == 'TRADING'）
            valid_symbols = {
                symbol['symbol'] 
                for symbol in exchange_info['symbols'] 
                if symbol['contractType'] == 'PERPETUAL' 
                and symbol['quoteAsset'] == 'USDT'
                and symbol['status'] == 'TRADING'
            }
            
            # 更新緩存
            self.valid_symbols_cache = valid_symbols
            self.valid_symbols_cache_time = current_time
            
            logger.info(
                f"✅ Fetched {len(valid_symbols)} valid USDT perpetual symbols "
                f"(cached for {cache_ttl}s)"
            )
            
            return valid_symbols
            
        except Exception as e:
            logger.error(f"❌ Error fetching valid futures symbols: {e}")
            # 如果 API 調用失敗但有舊緩存，返回舊緩存
            if self.valid_symbols_cache is not None:
                logger.warning(
                    f"⚠️ Using stale cache "
                    f"(age: {int(current_time - self.valid_symbols_cache_time)}s)"
                )
                return self.valid_symbols_cache
            return set()
    
    def get_symbol_info(self, symbol):
        """獲取交易對信息（帶緩存）"""
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]
        
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    self.symbol_info_cache[symbol] = s
                    return s
            
            logger.warning(f"Symbol {symbol} not found in exchange info")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching symbol info for {symbol}: {e}")
            return None
    
    def get_min_notional(self, symbol):
        """獲取交易對的最小名義價值要求"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return 5.0  # Default minimum
            
            # 獲取 MIN_NOTIONAL 或 NOTIONAL 過濾器
            for f in symbol_info['filters']:
                if f['filterType'] == 'MIN_NOTIONAL':
                    return float(f.get('minNotional', 5.0))
                elif f['filterType'] == 'NOTIONAL':
                    return float(f.get('minNotional', 5.0))
            
            return 5.0  # Default if not found
            
        except Exception as e:
            logger.error(f"Error getting min notional for {symbol}: {e}")
            return 5.0
    
    def format_quantity(self, symbol, quantity, price=None):
        """
        根據交易對的 LOT_SIZE 和 MIN_NOTIONAL 過濾器格式化數量
        
        Args:
            symbol: 交易對
            quantity: 原始數量
            price: 當前價格（用於驗證 MIN_NOTIONAL）
            
        Returns:
            格式化後的數量（float），如果無法滿足最小名義價值則返回 None
        """
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                logger.warning(f"No symbol info for {symbol}, using raw quantity")
                return quantity
            
            # 獲取 LOT_SIZE 過濾器
            lot_size_filter = None
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    lot_size_filter = f
                    break
            
            if not lot_size_filter:
                logger.warning(f"No LOT_SIZE filter for {symbol}, using raw quantity")
                return quantity
            
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            max_qty = float(lot_size_filter['maxQty'])
            
            # 使用 binance helper 函數進行精確的步長舍入
            formatted_qty = round_step_size(quantity, step_size)
            
            # 確保符合最小/最大數量要求
            if formatted_qty < min_qty:
                logger.warning(f"Quantity {formatted_qty} below minimum {min_qty}, using minimum")
                formatted_qty = min_qty
            elif formatted_qty > max_qty:
                logger.warning(f"Quantity {formatted_qty} above maximum {max_qty}, using maximum")
                formatted_qty = max_qty
            
            # 驗證 MIN_NOTIONAL（如果提供了價格）
            if price is not None:
                min_notional = self.get_min_notional(symbol)
                notional_value = formatted_qty * price
                
                if notional_value < min_notional:
                    # 🔧 使用安全邊際：1.02 倍最小名義價值（防止浮點精度問題）
                    safe_min_notional = min_notional * 1.02
                    required_qty = safe_min_notional / price
                    
                    # 向上舍入到下一個 stepSize 倍數
                    if step_size >= 1.0:
                        # 整數步長：向上取整
                        formatted_qty = math.ceil(required_qty / step_size) * step_size
                    else:
                        # 小數步長：使用 round_step_size 後再驗證
                        formatted_qty = round_step_size(required_qty, step_size)
                        
                        # 循環增加 stepSize 直到滿足要求（最多 10 次）
                        attempts = 0
                        while formatted_qty * price < safe_min_notional and attempts < 10:
                            formatted_qty += step_size
                            attempts += 1
                        
                        if attempts >= 10:
                            logger.error(
                                f"❌ {symbol}: Failed to meet MIN_NOTIONAL after 10 attempts "
                                f"(price=${price:.8f}, final_qty={formatted_qty})"
                            )
                            return None
                    
                    # 最終驗證（使用原始 min_notional，不是 safe 版本）
                    new_notional = formatted_qty * price
                    if new_notional < min_notional:
                        logger.warning(
                            f"❌ {symbol}: Cannot meet MIN_NOTIONAL ${min_notional:.2f} "
                            f"(price=${price:.8f}, qty={formatted_qty}, notional=${new_notional:.2f})"
                        )
                        return None
                    
                    logger.info(
                        f"📈 {symbol}: Adjusted quantity to meet MIN_NOTIONAL "
                        f"${min_notional:.2f}: {quantity:.6f} → {formatted_qty} "
                        f"(notional: ${new_notional:.2f}, safe margin: +2%)"
                    )
            
            logger.info(f"Formatted quantity for {symbol}: {quantity:.10f} → {formatted_qty} (step={step_size}, min={min_qty})")
            
            return formatted_qty
            
        except Exception as e:
            logger.error(f"Error formatting quantity for {symbol}: {e}")
            return quantity
    
    def place_order(self, symbol, side, order_type, quantity, price=None):
        """Place futures order (U本位合約)."""
        if not Config.ENABLE_TRADING:
            logger.warning("Trading is disabled. Set ENABLE_TRADING=true to enable.")
            return None
        
        try:
            # 獲取當前價格（用於 MIN_NOTIONAL 驗證）
            if price is None:
                current_price = self.get_ticker_price(symbol)
            else:
                current_price = float(price)
            
            # 格式化數量（去除科學計數法，應用 LOT_SIZE 和 MIN_NOTIONAL）
            formatted_quantity = self.format_quantity(symbol, quantity, current_price)
            
            # 如果無法滿足最小名義價值，拒絕訂單
            if formatted_quantity is None:
                logger.error(f"❌ Order rejected: {symbol} cannot meet MIN_NOTIONAL requirement")
                return None
            
            # ✅ 使用期貨 API (futures_create_order)
            # 設定持倉方向（雙向持倉模式必需）
            position_side = 'LONG' if side == 'BUY' else 'SHORT'
            
            if order_type == 'MARKET':
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=formatted_quantity,
                    positionSide=position_side  # 雙向持倉模式必需
                )
            else:
                # 限價單需要 timeInForce
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=formatted_quantity,
                    price=price,
                    timeInForce='GTC',
                    positionSide=position_side  # 雙向持倉模式必需
                )
            
            logger.info(f"✅ Futures order placed: {order.get('orderId', 'N/A')}")
            return order
        
        except Exception as e:
            logger.error(f"❌ Futures order failed: {e}")
            return None
    
    def set_stop_loss_order(self, symbol, side, quantity, stop_price, position_side):
        """
        設置止損訂單（交易所級別保護）
        
        Args:
            symbol: 交易對
            side: 'BUY' (平空倉) 或 'SELL' (平多倉)
            quantity: 數量
            stop_price: 止損觸發價格
            position_side: 'LONG' 或 'SHORT'
            
        Returns:
            訂單響應或 None
        """
        if not Config.ENABLE_TRADING:
            logger.warning("Trading is disabled. Set ENABLE_TRADING=true to enable.")
            return None
        
        try:
            # 格式化數量
            formatted_quantity = self.format_quantity(symbol, quantity, stop_price)
            if formatted_quantity is None:
                logger.error(f"❌ Stop-loss order rejected: {symbol} cannot meet requirements")
                return None
            
            # 格式化止損價格（保留8位小數）
            formatted_stop_price = round(stop_price, 8)
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                stopPrice=formatted_stop_price,
                quantity=formatted_quantity,
                positionSide=position_side,
                reduceOnly=True,  # 只平倉，不開新倉（安全保護）
                workingType='MARK_PRICE',  # 使用標記價格，更穩定
                priceProtect=True  # 價格保護
            )
            
            logger.info(
                f"✅ Stop-loss order set: {symbol} {side} @ {formatted_stop_price} "
                f"(qty={formatted_quantity}, position={position_side}, orderId={order.get('orderId', 'N/A')})"
            )
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to set stop-loss for {symbol}: {e}")
            return None
    
    def set_take_profit_order(self, symbol, side, quantity, tp_price, position_side):
        """
        設置止盈訂單（交易所級別保護）
        
        Args:
            symbol: 交易對
            side: 'BUY' (平空倉) 或 'SELL' (平多倉)
            quantity: 數量
            tp_price: 止盈觸發價格
            position_side: 'LONG' 或 'SHORT'
            
        Returns:
            訂單響應或 None
        """
        if not Config.ENABLE_TRADING:
            logger.warning("Trading is disabled. Set ENABLE_TRADING=true to enable.")
            return None
        
        try:
            # 格式化數量
            formatted_quantity = self.format_quantity(symbol, quantity, tp_price)
            if formatted_quantity is None:
                logger.error(f"❌ Take-profit order rejected: {symbol} cannot meet requirements")
                return None
            
            # 格式化止盈價格（保留8位小數）
            formatted_tp_price = round(tp_price, 8)
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=formatted_tp_price,
                quantity=formatted_quantity,
                positionSide=position_side,
                reduceOnly=True,  # 只平倉，不開新倉（安全保護）
                workingType='MARK_PRICE',  # 使用標記價格，更穩定
                priceProtect=True  # 價格保護
            )
            
            logger.info(
                f"✅ Take-profit order set: {symbol} {side} @ {formatted_tp_price} "
                f"(qty={formatted_quantity}, position={position_side}, orderId={order.get('orderId', 'N/A')})"
            )
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to set take-profit for {symbol}: {e}")
            return None
    
    def get_current_positions(self):
        """
        獲取當前所有持倉（從 Binance 期貨 API）
        
        Returns:
            List of position dictionaries with keys:
            - symbol: str
            - positionSide: 'LONG' or 'SHORT'
            - positionAmt: float (負數表示空倉)
            - entryPrice: float
            - unrealizedProfit: float
            - leverage: int
        """
        try:
            # 獲取所有持倉信息（包括 LONG 和 SHORT）
            positions = self.client.futures_position_information()
            
            # 過濾出有實際持倉的（數量不為0）
            active_positions = [
                pos for pos in positions
                if float(pos.get('positionAmt', 0)) != 0
            ]
            
            if active_positions:
                logger.info(f"📊 Found {len(active_positions)} active positions from Binance")
                for pos in active_positions:
                    symbol = pos['symbol']
                    side = pos['positionSide']
                    amt = float(pos['positionAmt'])
                    entry = float(pos['entryPrice'])
                    logger.info(
                        f"  • {symbol} {side}: {abs(amt)} @ {entry:.8f}"
                    )
            else:
                logger.info("No active positions found on Binance")
            
            return active_positions
            
        except Exception as e:
            logger.error(f"Error fetching current positions from Binance: {e}")
            return []
    
    def get_open_stop_orders(self, symbol=None):
        """
        獲取當前所有活躍的止損止盈訂單
        
        Args:
            symbol: 交易對（可選，不指定則返回所有）
            
        Returns:
            List of open STOP_MARKET and TAKE_PROFIT_MARKET orders
        """
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            # 過濾止損止盈訂單
            stop_orders = [
                order for order in orders
                if order['type'] in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']
            ]
            
            if stop_orders:
                logger.info(f"📊 Found {len(stop_orders)} active SL/TP orders")
                for order in stop_orders:
                    logger.info(
                        f"  • {order['symbol']} {order['type']}: "
                        f"{order['side']} @ {order['stopPrice']} "
                        f"(ID: {order['orderId']})"
                    )
            else:
                logger.info("No active SL/TP orders found")
            
            return stop_orders
        except Exception as e:
            logger.error(f"Error fetching open stop orders: {e}")
            return []
    
    def get_all_usdt_perpetual_pairs(self):
        """
        獲取所有有效的 USDT 永續合約交易對（使用動態驗證）
        
        工作流程：
        1. 使用 get_valid_futures_symbols() 從 API 獲取有效交易對（帶緩存）
        2. 應用手動黑名單過濾（INVALID_SYMBOLS）
        3. 記錄統計信息
        
        Returns:
            List of valid USDT perpetual symbols
        """
        if not self.client:
            logger.error("Binance client not initialized - using static symbols fallback")
            return Config.STATIC_SYMBOLS
        
        try:
            # 步驟 1: 從 API 獲取有效交易對（使用緩存）
            valid_symbols = self.get_valid_futures_symbols()
            
            if not valid_symbols:
                logger.warning("No valid symbols returned from API, using static symbols fallback")
                return Config.STATIC_SYMBOLS
            
            # 步驟 2: 應用手動黑名單過濾
            filtered_pairs = [
                symbol for symbol in valid_symbols
                if symbol not in INVALID_SYMBOLS
            ]
            
            # 步驟 3: 記錄統計信息
            api_count = len(valid_symbols)
            blacklist_filtered = api_count - len(filtered_pairs)
            
            if blacklist_filtered > 0:
                logger.info(
                    f"✅ Total valid symbols: {len(filtered_pairs)} "
                    f"(API: {api_count}, manual blacklist filtered: {blacklist_filtered})"
                )
            else:
                logger.info(
                    f"✅ Total valid symbols: {len(filtered_pairs)} "
                    f"(no manual blacklist filtering needed)"
                )
            
            return filtered_pairs
        
        except Exception as e:
            logger.error(f"❌ Error in get_all_usdt_perpetual_pairs: {e}")
            logger.warning(f"Using static symbols fallback: {Config.STATIC_SYMBOLS}")
            return Config.STATIC_SYMBOLS
    
    def get_top_pairs_by_volume(self, limit=50):
        """獲取按24小時成交量排序的前N個交易對"""
        if not self.client:
            logger.error("Binance client not initialized - using static symbols fallback")
            return Config.STATIC_SYMBOLS
        
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

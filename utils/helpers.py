import pandas as pd
import numpy as np
from datetime import datetime
import logging
import time
import asyncio
from functools import wraps
from typing import Callable, Tuple, Type

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logger(name):
    return logging.getLogger(name)


# ============================================================================
# 錯誤處理：重試裝飾器（v3.0 新增）
# ============================================================================

def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """
    帶指數退避的重試裝飾器（同步版本）
    
    參數：
        max_retries: 最大重試次數（不包括初次嘗試）
        backoff_factor: 退避基數（秒），每次重試等待時間 = backoff_factor * (2 ** attempt)
        exceptions: 需要重試的異常類型元組
        on_retry: 重試前的回調函數（可選，用於發送通知）
    
    範例：
        @retry_on_failure(max_retries=3, exceptions=(ConnectionError, Timeout))
        def fetch_data(symbol):
            return api.get_klines(symbol)
    """
    logger = logging.getLogger(__name__)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # 最後一次嘗試失敗，不再重試
                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # 計算等待時間（指數退避）
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s... Error: {e}"
                    )
                    
                    # 執行重試回調（如發送通知）
                    if on_retry:
                        try:
                            on_retry(func.__name__, attempt + 1, wait_time, e)
                        except Exception as callback_error:
                            logger.warning(f"Retry callback failed: {callback_error}")
                    
                    time.sleep(wait_time)
            
            # 理論上不會執行到這裡
            raise last_exception
        
        return wrapper
    return decorator


def async_retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    帶指數退避的重試裝飾器（異步版本）
    
    用於 async def 函數
    """
    logger = logging.getLogger(__name__)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s... Error: {e}"
                    )
                    
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

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

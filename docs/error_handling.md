# 錯誤處理與 API 重連機制（v3.0）

## 1. 設計原則

### 核心原則
1. **不因單次錯誤終止主循環**：交易機器人需要 24/7 運行，任何單一錯誤都不應導致整體崩潰
2. **區分可恢復 vs 不可恢復錯誤**：網路中斷可重試，API Key 錯誤應停止
3. **關鍵操作具備重試與指數退避**：避免頻繁重試加劇問題
4. **詳細日誌記錄**：所有錯誤都應記錄，便於調試和監控
5. **優雅降級**：非核心功能（如 Discord 通知）失敗不應阻塞交易

---

## 2. 錯誤分類與處理策略

### 2.1 錯誤類型矩陣

| 錯誤類型 | 舉例 | 可恢復性 | 處理方式 | 重試次數 | Discord 通知 |
|---------|------|---------|---------|---------|-------------|
| **網路暫時中斷** | `ConnectionError`, `Timeout` | ✅ 可恢復 | 重試 3 次，指數退避 | 3 | ⚠️ 超過 3 次失敗後通知 |
| **API 限流** | HTTP 429, Binance 418 | ✅ 可恢復 | 等待 `Retry-After` 時間 | 1 | ⚠️ 頻繁限流時通知 |
| **無效 API Key** | HTTP 401 Unauthorized | ❌ 不可恢復 | 記錄並停止交易 | 0 | 🔴 立即通知 |
| **訂單參數錯誤** | 價格超出漲跌停, 數量精度錯誤 | ⚠️ 部分可恢復 | 跳過該交易對，記錄日誌 | 0 | ⚠️ 記錄警告 |
| **Discord 通知失敗** | Token 錯誤, 網路中斷 | ✅ 可降級 | 記錄警告，不阻塞交易 | 1 | 不通知（避免循環） |
| **數據解析錯誤** | JSON 解析失敗, 欄位缺失 | ✅ 可恢復 | 跳過該數據，重試下次週期 | 0 | ⚠️ 連續 5 次失敗通知 |
| **止損/止盈觸發** | 正常交易事件 | ✅ 預期行為 | 平倉並記錄 | 0 | ✅ 正常通知 |
| **系統記憶體不足** | `MemoryError` | ❌ 不可恢復 | 清理緩存，重啟服務 | 0 | 🔴 立即通知 |

---

## 3. 重試機制實現

### 3.1 指數退避裝飾器（v3.0 新增）

**文件位置**：`utils/helpers.py`

```python
import time
import logging
from functools import wraps
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)

def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """
    帶指數退避的重試裝飾器
    
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
    異步版本的重試裝飾器
    
    用於 async def 函數
    """
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
```

### 3.2 應用範例

#### Binance API 調用

```python
from utils.helpers import retry_on_failure
from binance.exceptions import BinanceAPIException
from requests.exceptions import ConnectionError, Timeout

class BinanceDataClient:
    
    @retry_on_failure(
        max_retries=3,
        backoff_factor=1.0,
        exceptions=(ConnectionError, Timeout, BinanceAPIException)
    )
    def get_klines(self, symbol, interval='15m', limit=200):
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
        
        return self._parse_klines(klines)
    
    
    @retry_on_failure(
        max_retries=2,
        backoff_factor=0.5,
        exceptions=(ConnectionError, Timeout)
    )
    def get_ticker_price(self, symbol):
        """
        獲取最新價格（輕量級，快速重試）
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
```

#### Discord 通知（優雅降級）

```python
class DiscordBot:
    
    @retry_on_failure(
        max_retries=1,
        backoff_factor=0.5,
        exceptions=(HTTPException, ConnectionError)
    )
    async def send_trade_notification(self, message):
        """
        發送交易通知（1 次重試，失敗不阻塞）
        """
        try:
            await self.channel.send(embed=message)
        except Exception as e:
            logger.warning(f"Discord notification failed: {e}")
            # 不拋出異常，避免阻塞交易流程
```

---

## 4. 主循環健壯性設計

### 4.1 多層異常隔離

```python
class TradingBotV3:
    
    async def run(self):
        """
        主循環：永不崩潰設計
        
        層次：
        1. 最外層：捕獲所有未預期的異常
        2. 中間層：單個週期失敗不影響整體
        3. 內層：單個交易對失敗不影響其他交易對
        """
        logger.info("🚀 Starting trading bot main loop")
        self.is_running = True
        
        while self.is_running:
            try:
                # ============ 第二層：單週期隔離 ============
                await self._run_trading_cycle()
                
            except KeyboardInterrupt:
                logger.info("⏹️ Keyboard interrupt received, shutting down gracefully...")
                await self.shutdown()
                break
                
            except Exception as e:
                # ============ 第一層：全局異常捕獲 ============
                logger.critical(f"🔥 CRITICAL: Main loop crashed: {e}", exc_info=True)
                
                # 發送緊急通知
                if self.discord:
                    try:
                        await self.discord.send_alert(
                            "🔥 **CRITICAL ERROR**",
                            f"Main loop crashed: {str(e)[:200]}",
                            level="critical"
                        )
                    except:
                        pass
                
                # 等待 30 秒後重試（避免無限崩潰循環）
                logger.info("⏳ Waiting 30s before retry...")
                await asyncio.sleep(30)
    
    
    async def _run_trading_cycle(self):
        """
        單個交易週期：容錯設計
        """
        cycle_start = asyncio.get_event_loop().time()
        self.cycle_count += 1
        
        try:
            # 1. 獲取市場數據（批量，部分失敗不影響整體）
            market_data = await self._fetch_market_data_with_error_handling()
            
            # 2. 分析信號（批量，部分失敗不影響整體）
            signals = await self._analyze_signals_with_error_handling(market_data)
            
            # 3. 執行交易（單個失敗不影響其他）
            await self._execute_trades_with_error_handling(signals)
            
            # 4. 監控現有倉位（單個失敗不影響其他）
            await self._monitor_positions_with_error_handling()
            
        except Exception as e:
            logger.error(f"Trading cycle #{self.cycle_count} failed: {e}", exc_info=True)
            # 不拋出異常，讓主循環繼續
        
        finally:
            # 確保週期間隔
            elapsed = asyncio.get_event_loop().time() - cycle_start
            wait_time = max(0, self.cycle_interval - elapsed)
            await asyncio.sleep(wait_time)
    
    
    async def _fetch_market_data_with_error_handling(self):
        """
        批量獲取數據：容忍部分失敗
        
        策略：
        - 並行獲取所有交易對數據
        - 失敗的交易對跳過，不影響其他
        - 記錄失敗統計
        """
        successful_data = {}
        failed_symbols = []
        
        # 批量並行獲取
        tasks = []
        for symbol in self.symbols:
            task = self._fetch_single_symbol_data(symbol)
            tasks.append((symbol, task))
        
        # 等待所有結果
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        
        # 分類成功與失敗
        for i, (symbol, _) in enumerate(tasks):
            result = results[i]
            
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch {symbol}: {result}")
                failed_symbols.append(symbol)
            elif result is not None:
                successful_data[symbol] = result
        
        # 記錄統計
        logger.info(
            f"Data fetch: {len(successful_data)}/{len(self.symbols)} successful, "
            f"{len(failed_symbols)} failed"
        )
        
        # 失敗率過高時發送警告
        if len(failed_symbols) > len(self.symbols) * 0.5:
            logger.warning(
                f"⚠️ HIGH FAILURE RATE: {len(failed_symbols)}/{len(self.symbols)} "
                f"symbols failed to fetch data"
            )
            if self.discord:
                await self.discord.send_alert(
                    "⚠️ Data Fetch Warning",
                    f"{len(failed_symbols)}/{len(self.symbols)} symbols failed",
                    level="warning"
                )
        
        return successful_data
    
    
    async def _fetch_single_symbol_data(self, symbol):
        """
        獲取單個交易對數據（帶重試）
        """
        try:
            klines = await self.data_service.fetch_klines(
                symbol=symbol,
                timeframe=self.timeframe,
                limit=200
            )
            
            if klines is None or klines.empty:
                return None
            
            price = await self.binance.get_ticker_price_async(symbol)
            return (klines, price)
            
        except Exception as e:
            # 記錄但不拋出異常
            logger.debug(f"Failed to fetch {symbol}: {e}")
            return None
```

---

## 5. API 限流處理

### 5.1 Binance 限流規則

| 限制類型 | 限制值 | 時間窗口 | 超限後果 |
|---------|--------|---------|---------|
| **請求權重** | 1200 weight/min | 1 分鐘 | HTTP 418, 封禁 2 分鐘至 3 天 |
| **訂單頻率** | 50 orders/10s | 10 秒 | HTTP 429, 封禁 1 分鐘 |
| **WebSocket 連接** | 5 connections/IP | - | 連接被拒絕 |

### 5.2 限流處理實現（v3.0 現有機制）

**文件位置**：`core/rate_limiter.py`（已存在）

```python
class RateLimiter:
    """
    令牌桶算法實現
    
    v3.0 已實現，無需修改
    """
    def __init__(self, rate_per_minute, capacity=None):
        self.rate = rate_per_minute
        self.capacity = capacity or rate_per_minute
        self.tokens = self.capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens=1):
        async with self.lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # 需要等待
            wait_time = (tokens - self.tokens) / (self.rate / 60)
            logger.warning(f"Rate limit: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
            
            await self._refill()
            self.tokens -= tokens
            return True
```

### 5.3 處理 HTTP 429 響應

```python
def handle_binance_error(func):
    """
    處理 Binance 特定錯誤的裝飾器
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BinanceAPIException as e:
            if e.code == -1003:  # Too many requests
                retry_after = int(e.message.get('Retry-After', 60))
                logger.warning(f"API rate limit hit, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await func(*args, **kwargs)
            
            elif e.code == -2010:  # Insufficient balance
                logger.error("Insufficient balance for order")
                return None
            
            elif e.code == -1021:  # Timestamp out of sync
                logger.error("Server time sync issue")
                # 重新同步時間（v3.0 TODO）
                raise
            
            else:
                logger.error(f"Binance API error: {e.code} - {e.message}")
                raise
    
    return wrapper
```

---

## 6. 不可恢復錯誤處理

### 6.1 無效 API Key

```python
async def validate_api_credentials(self):
    """
    驗證 API 憑證
    
    在初始化時調用，失敗則終止程序
    """
    try:
        # 測試 API 連接
        account = await self.binance.get_account_async()
        logger.info("✅ API credentials validated")
        return True
        
    except BinanceAPIException as e:
        if e.code in [-2014, -2015]:  # Invalid API key
            logger.critical(
                "🔴 FATAL: Invalid API credentials. "
                "Please check BINANCE_API_KEY and BINANCE_SECRET_KEY"
            )
            
            if self.discord:
                await self.discord.send_alert(
                    "🔴 FATAL ERROR",
                    "Invalid Binance API credentials. Bot stopped.",
                    level="critical"
                )
            
            return False
        
        raise
```

### 6.2 系統資源不足

```python
import psutil

def check_system_resources():
    """
    檢查系統資源
    
    記憶體 < 100MB 或 磁碟 < 1GB 時發出警告
    """
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    if memory.available < 100 * 1024 * 1024:  # < 100MB
        logger.warning(
            f"⚠️ Low memory: {memory.available / 1024 / 1024:.1f}MB available"
        )
        return False
    
    if disk.free < 1024 * 1024 * 1024:  # < 1GB
        logger.warning(
            f"⚠️ Low disk space: {disk.free / 1024 / 1024 / 1024:.1f}GB available"
        )
        return False
    
    return True
```

---

## 7. 監控與告警

### 7.1 錯誤統計追蹤

```python
class ErrorTracker:
    """
    錯誤統計追蹤器
    
    用於監控錯誤頻率和觸發告警
    """
    def __init__(self, window_size=3600):  # 1小時窗口
        self.errors = {}
        self.window_size = window_size
    
    def record_error(self, error_type, error_message):
        """記錄錯誤"""
        timestamp = time.time()
        
        if error_type not in self.errors:
            self.errors[error_type] = []
        
        self.errors[error_type].append({
            'timestamp': timestamp,
            'message': error_message
        })
        
        # 清理過期錯誤
        self._cleanup_old_errors(error_type, timestamp)
    
    def get_error_count(self, error_type, window=None):
        """獲取錯誤計數"""
        window = window or self.window_size
        cutoff = time.time() - window
        
        if error_type not in self.errors:
            return 0
        
        return sum(1 for e in self.errors[error_type] if e['timestamp'] > cutoff)
    
    def should_alert(self, error_type, threshold=10):
        """
        判斷是否應該發送告警
        
        1小時內同一錯誤超過閾值次數
        """
        return self.get_error_count(error_type) >= threshold
```

### 7.2 告警通知集成

```python
async def handle_error_with_tracking(self, error_type, error, context=""):
    """
    帶追蹤的錯誤處理
    """
    # 記錄錯誤
    self.error_tracker.record_error(error_type, str(error))
    
    # 判斷是否需要告警
    if self.error_tracker.should_alert(error_type, threshold=10):
        error_count = self.error_tracker.get_error_count(error_type)
        
        logger.warning(
            f"🔔 Alert threshold reached for {error_type}: "
            f"{error_count} occurrences in last hour"
        )
        
        if self.discord:
            await self.discord.send_alert(
                f"⚠️ Error Alert: {error_type}",
                f"Occurred {error_count} times in the last hour\n"
                f"Latest: {str(error)[:200]}",
                level="warning"
            )
```

---

## 8. 優雅關閉

### 8.1 信號處理

```python
import signal

class TradingBotV3:
    
    def __init__(self):
        # ... 其他初始化 ...
        
        # 註冊信號處理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """處理終止信號"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.is_running = False
    
    async def shutdown(self):
        """
        優雅關閉
        
        1. 停止新交易
        2. 等待現有任務完成
        3. 保存狀態
        4. 關閉連接
        """
        logger.info("🛑 Shutting down gracefully...")
        
        # 1. 停止接受新信號
        self.is_running = False
        
        # 2. 等待現有倉位監控完成
        logger.info("Waiting for active position monitors to complete...")
        # (v3.0 已實現)
        
        # 3. 保存交易日誌
        logger.info("Flushing trade logs...")
        if self.trade_logger:
            self.trade_logger.flush()
        
        # 4. 關閉 Binance 連接
        if self.binance and self.binance.async_client:
            await self.binance.async_client.close_connection()
        
        # 5. 關閉 Discord 連接
        if self.discord:
            await self.discord.close()
        
        logger.info("✅ Shutdown complete")
```

---

## 9. 測試與驗證

### 9.1 錯誤注入測試

```python
# tests/test_error_handling.py

async def test_network_failure_retry():
    """測試網路失敗重試機制"""
    mock_client = MockBinanceClient(fail_count=2)
    
    @retry_on_failure(max_retries=3, exceptions=(ConnectionError,))
    def fetch_data():
        return mock_client.get_klines("BTCUSDT")
    
    # 應該在第 3 次嘗試成功
    result = fetch_data()
    assert result is not None
    assert mock_client.call_count == 3


async def test_api_key_failure_no_retry():
    """測試 API Key 錯誤不重試"""
    mock_client = MockBinanceClient(raise_auth_error=True)
    
    @retry_on_failure(max_retries=3)
    def fetch_data():
        return mock_client.get_account()
    
    # 應該立即失敗，不重試
    with pytest.raises(UnauthorizedError):
        fetch_data()
    
    assert mock_client.call_count == 1
```

---

## 10. v3.0 當前狀態與改進建議

### ✅ 已實現
- Rate Limiter (令牌桶)
- Circuit Breaker (斷路器)
- Cache Manager (緩存)
- 主循環異常隔離
- Discord 優雅降級

### ⚠️ 需要改進（本次任務）
- [ ] 添加通用重試裝飾器
- [ ] 改進錯誤分類處理
- [ ] 增強錯誤統計追蹤
- [ ] 完善優雅關閉流程

### 📋 未來優化方向
- [ ] 集成 Sentry 錯誤監控
- [ ] 死信隊列（Dead Letter Queue）
- [ ] 自動重啟策略
- [ ] 健康檢查端點（HTTP endpoint）

---

**文檔版本**：v3.0  
**最後更新**：2025-10-24  
**維護者**：Trading Bot Development Team

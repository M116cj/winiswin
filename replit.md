# Cryptocurrency Trading Bot v3.2

### Overview
This project is an automated cryptocurrency trading bot designed to monitor all 648 Binance USDT perpetual contracts. It employs ICT/SMC trading strategies combined with an intelligent 3-position management system to identify and execute trades. The bot provides comprehensive real-time notifications via Discord, keeping users informed of market activities and bot performance. Key features include full market coverage, advanced risk management with dynamic margin sizing (3%-13%) and win-rate based leverage (3-20x), exchange-level stop-loss/take-profit protection, and comprehensive trade logging for XGBoost machine learning. The business vision is to provide a robust, automated trading solution with advanced risk management and real-time insights for cryptocurrency traders.

### User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative with dynamic margin based on signal confidence
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

### Recent Updates (v3.2 - 2025-10-24)

#### 🔧 System Optimization (Latest - 2025-10-24 PM)
**Implementation**: API 使用率優化與虛擬倉位穩定性改進

1. **虛擬倉位價格獲取優化** (`virtual_position_tracker.py`)
   - 添加智能重試機制（最多 3 次嘗試，間隔 0.5 秒）
   - 改進日誌策略：首次失敗使用 debug 級別，避免日誌刷屏
   - 失敗時保留虛擬倉位供下一週期檢查（而非直接跳過）
   - 重試成功時記錄成功信息
   - 確保虛擬倉位使用市價單（當下價格）記錄

2. **無效交易對黑名單** (`binance_client.py`)
   - 添加 INVALID_SYMBOLS 常量，包含 38 個已下架或不存在的交易對
   - 自動過濾黑名單中的交易對，減少 API 調用
   - 記錄過濾統計日誌
   - 預期減少約 5-6% 的 API 請求量

**效果**：
- ✅ 消除 "Invalid symbol" API 錯誤
- ✅ 提高虛擬倉位價格獲取成功率
- ✅ 減少不必要的 API 調用
- ✅ 改善系統穩定性和日誌可讀性

#### 🎯 Multi-Timeframe Trading Strategy
**Implementation**: 使用15分鐘K線定義趨勢，1分鐘K線執行交易
1. **15分鐘趨勢分析** (`get_15m_trend()`)
   - 使用 EMA200 判斷整體趨勢方向（價格 > EMA200 = 多頭，否則 = 空頭）
   - 緩存機制：每15分鐘更新一次，避免頻繁 API 請求
   - 只在15分鐘趨勢一致時才允許開倉（防止逆勢交易）

2. **1分鐘精確執行**
   - 在1分鐘K線上尋找精確入場點
   - 結合 ICT/SMC 策略（訂單塊、流動性區域、市場結構）
   - 使用 MACD、EMA 進行技術確認

3. **動態風險回報比** (1:1 到 1:2)
   - 高信心度信號 (≥90%): 使用 1:2 風險回報比
   - 中信心度信號 (80-90%): 使用 1:1.5 風險回報比
   - 低信心度信號 (70-80%): 使用 1:1 風險回報比
   - 根據信號質量自動調整收益目標

4. **增強止損保護**
   - 驗證止損必須在正確的一側（做多: SL < 入場價，做空: SL > 入場價）
   - 當損益平衡止損無效時，自動降級到傳統 ATR 止損 (2.0x)
   - 雙重驗證確保風險控制完整性

#### 📊 XGBoost Machine Learning Integration (Latest - 2025-10-24)
**Implementation**: 完整的交易數據記錄系統，為 XGBoost 機器學習提供訓練數據

1. **開倉數據記錄** (`log_position_entry()`)
   - 記錄所有信號特徵（confidence、expected_roi、market_structure、OB score 等）
   - 記錄當下技術指標（MACD、EMA、ATR、Bollinger Bands）
   - 記錄價格位置（距離 EMA200 的距離和百分比）
   - 記錄 15 分鐘和 1 小時趨勢方向
   - 記錄開倉時的 K 線快照（最近 20 根）
   - 生成唯一 trade_id（格式：`SYMBOL_YYYYMMDD_HHMMSS`）

2. **平倉數據記錄** (`log_position_exit()`)
   - 記錄從開倉到平倉的完整 K 線歷史
   - 記錄平倉時的技術指標
   - 自動計算 MFE（最大有利波動）和 MAE（最大不利波動）
   - 記錄交易結果標籤（WIN/LOSS、是否命中止盈/止損）
   - 記錄持倉時長和退出原因

3. **數據完整性保護**
   - `_sanitize_metadata()`: 處理 NumPy 標量、pandas Timestamps、NaN/Inf 值
   - `_safe_float()`: 安全轉換所有數值，處理 None 值
   - `pending_entries` 持久化：進程重啟不會丟失待處理的開倉記錄
   - 時間戳驗證：自動解析字符串時間戳為 datetime 對象
   - MFE/MAE 計算保護：處理空 K 線歷史、無效價格、除以零等異常

4. **降級機制**
   - 當 `log_position_entry` 失敗時，自動生成降級 trade_id（`{symbol}_{timestamp}_fallback`）
   - 異常情況下生成錯誤 trade_id（`{symbol}_{timestamp}_error`）
   - 確保即使記錄失敗，交易仍能正常執行

5. **數據文件**
   - `trades.json`: 基本交易記錄（保持向後兼容）
   - `ml_training_data.json`: 完整的 ML 訓練數據（開倉 + 平倉合併）
   - `ml_pending_entries.json`: 待處理的開倉記錄（進程重啟持久化）

#### 🎯 Virtual Position Tracking (Latest - 2025-10-24)
**Implementation**: 追蹤排名第 4 名以後的信號作為虛擬倉位，大幅增加 XGBoost 訓練數據量

1. **虛擬倉位創建** (`VirtualPositionTracker`)
   - 從排名第 4 開始的信號自動創建虛擬倉位（不真實開倉）
   - 最多追蹤 10 個併發虛擬倉位
   - 只追蹤信心度 ≥ 70% 的信號
   - 使用與真實交易相同的止盈/止損計算邏輯
   - 記錄完整的開倉特徵（與真實交易完全相同）

2. **虛擬倉位監控**
   - 每個交易週期檢查所有虛擬倉位的止盈/止損觸發
   - 批量獲取價格數據，避免過多 API 請求
   - 自動追蹤持倉時長（cycles_since_open）
   - 超時自動平倉（96 個週期 ≈ 1.6 小時）

3. **虛擬倉位平倉**
   - 止盈觸發：價格達到目標價格
   - 止損觸發：價格觸及止損價格
   - 超時平倉：超過最大追蹤時間
   - 記錄完整的平倉數據（K 線歷史、MFE/MAE、退出原因）

4. **數據標記**
   - 所有虛擬交易數據標記為 `is_virtual: true`
   - 與真實交易數據存儲在同一個 ML 文件中
   - 可根據 `is_virtual` 字段區分真實和虛擬交易

5. **持久化和恢復**
   - 虛擬倉位持久化到 `virtual_positions.json`
   - 進程重啟後自動恢復虛擬倉位
   - trade_id 匹配機制確保開倉和平倉數據正確合併

6. **性能優化**
   - 使用 trade_id 作為字典鍵（O(1) 查找）
   - 支持同一 symbol 的多個虛擬倉位
   - 批量價格獲取，重用 DataService 緩存
   - 最大倉位數限制防止資源耗盡

7. **數據文件**
   - `virtual_positions.json`: 活躍虛擬倉位（進程重啟持久化）
   - `ml_training_data.json`: 包含虛擬和真實交易的完整 ML 數據

**優勢**：
- 無需承擔風險即可收集大量訓練數據
- 提供更多樣化的市場情況樣本
- 測試不同信號質量的實際表現
- 加速 XGBoost 模型訓練和優化

#### Critical Bug Fixes (Earlier)
1. **Fixed Margin Calculation (v3.0 → v3.2)**
   - **Issue**: RiskManager was importing old `calculate_position_size` from utils/helpers, causing fixed $0.4-0.6 margins
   - **Fix**: Removed legacy import, now correctly uses dynamic margin sizing (3%-13% based on signal confidence)
   - **Impact**: Positions now use proper margin allocation ($30-130 per position instead of $0.4-0.6)

2. **Fixed Stop-Loss/Take-Profit Orders**
   - **Issue**: `_set_stop_loss_take_profit` was calling synchronous Binance methods without async execution
   - **Fix**: Implemented `loop.run_in_executor` for proper async order placement
   - **Impact**: Exchange-level protection orders now correctly placed on Binance

3. **Version Tracking**
   - **Updated**: main_v3.py now displays "v3.2" with feature list on startup
   - **Verification**: Added `verify_v32_fixes.py` script to validate all fixes

### System Architecture
The bot has undergone a significant architectural overhaul to v3.2, transitioning from a monolithic application to a modular, service-oriented design with production-ready risk management.

**UI/UX Decisions:**
- **Interactive Discord Bot**: Features slash commands (`/positions`, `/balance`, `/stats`, `/status`, `/config`) for real-time querying and uses Embed formats for aesthetic and clear responses. Auto-notifications are sent for trade cycles and executions.

**Technical Implementations & Design Choices:**
- **Modular Architecture**: Re-engineered with `main_v3.py` as the coordinator for various services.
- **Asynchronous I/O**: Enhanced `binance_client.py` with async methods for non-blocking data fetching.
- **Core Infrastructure**:
    - `RateLimiter`: Implements Token Bucket algorithm for Binance API request limits.
    - `CircuitBreaker`: Provides fault tolerance, pausing operations after failures.
    - `CacheManager`: Utilizes LRU caching with a 30-second TTL for market data.
- **Service Layer**:
    - `DataService`: Handles concurrent batch data fetching and intelligent caching.
    - `StrategyEngine`: Manages multi-strategy analysis and signal ranking.
    - `ExecutionService`: Oversees the position lifecycle, including automatic stop-loss/take-profit.
    - `MonitoringService`: Collects system metrics and manages alerts.
- **Trading Strategy (ICT/SMC with Multi-Timeframe Analysis)**: 
    - **Trend Definition**: 15-minute K-line with EMA200 determines overall trend direction
    - **Execution**: 1-minute K-line for precise entry timing
    - **Signal Components**: Order blocks, liquidity zones, market structure with MACD and EMA confirmation
    - **Confidence Scoring**: 70-100% multi-factor weighting system
    - **Validation**: OB triple validation, MSB amplitude filtering, 15m trend filtering to prevent counter-trend trades
    - **Dynamic Risk/Reward**: 1:1 to 1:2 ratio based on signal confidence (90%+ → 1:2, 80-90% → 1:1.5, 70-80% → 1:1)
- **Intelligent Position Selection**: Scans all 648 symbols, scores signals by confidence/expected ROI, sorts them, and opens positions only for the top 3 signals, dynamically managing existing positions.
- **Advanced Risk Management (v3.2)**:
    - Automatic account balance detection from Binance API (Spot + Futures USDT).
    - **Variable Margin Sizing**: Each position uses 3%-13% of total capital as margin (based on signal confidence).
    - **Win-Rate Based Leverage**: Leverage (3-20x) calculated from historical win rate:
      - Win rate >= 60%: High leverage 15-20x
      - Win rate 50-60%: Medium-high leverage 10-15x
      - Win rate 40-50%: Medium leverage 5-10x
      - Win rate < 40%: Low leverage 3-5x
      - No history (<10 trades): Conservative 3x
    - Position value = Margin × Leverage (e.g., $5.2 margin × 10x = $52 position).
    - Dynamic stop-loss/take-profit based on ATR.
    - Automatic drawdown alerts (5% triggers Discord alert).
    - Exchange-level stop-loss/take-profit orders for true position protection.
    - Min Notional validation with +2% safety margin to prevent floating-point errors.
- **Technical Indicators**: Uses pure Python/NumPy for MACD, Bollinger Bands, EMA, and ATR.
- **Error Handling**: Implements exponential backoff retry decorators (`@retry_on_failure`, `@async_retry_on_failure`) and intelligent retry strategies for network and API errors.
- **Dynamic Position Monitoring**: Continuously validates market conditions for open positions, detecting signal reversals, monitoring confidence changes, and dynamically adjusting stop-loss/take-profit levels.
- **Immediate Rescan after Closure**: Forces a rescan of a trading pair immediately after a position is closed, maximizing capital utilization.
- **Security**: API keys stored in environment variables, trading disabled by default, testnet mode for testing, and no withdrawal permissions on API keys.
- **Multi-Timeframe Trading Mode (v3.2)**:
    - **Trend Timeframe**: 15-minute K-lines with EMA200 for trend direction (configurable via TREND_TIMEFRAME)
    - **Execution Timeframe**: 1-minute K-lines for precise entry timing (configurable via EXECUTION_TIMEFRAME)
    - **Dynamic Risk/Reward**: 1:1 to 1:2 based on signal confidence (MIN_RISK_REWARD_RATIO = 1.0, MAX_RISK_REWARD_RATIO = 2.0)
    - **Breakeven-based Stops**: Accounts for leverage and fees with 1.5 ATR buffer
    - **Stop-Loss Validation**: Guarantees stop is on correct side of entry (long: SL < entry, short: SL > entry)
    - **Fallback Protection**: Auto-switches to traditional ATR stops (2.0x) if breakeven stops are invalid
    - **Trading Fees**: Maker 0.02%, Taker 0.04% (configurable)
    - **Cache Optimization**: 15m trend cached per 15-minute period to minimize API calls

### External Dependencies
- **Binance API**: For real-time market data, order placement, and account information.
- **Discord API**: For sending notifications and interactive slash commands.
- **Python Libraries**: `numpy` for numerical operations, `asyncio` for asynchronous programming.
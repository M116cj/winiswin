# Cryptocurrency Trading Bot v3.2

### Overview
This project is an automated cryptocurrency trading bot designed to monitor all 648 Binance USDT perpetual contracts. It employs ICT/SMC trading strategies combined with an intelligent 3-position management system to identify and execute trades. The bot provides comprehensive real-time notifications via Discord, keeping users informed of market activities and bot performance. Key features include full market coverage, advanced risk management with dynamic margin sizing (3%-13%) and win-rate based leverage (3-20x), exchange-level stop-loss/take-profit protection, and comprehensive trade logging for XGBoost machine learning. The business vision is to provide a robust, automated trading solution with advanced risk management and real-time insights for cryptocurrency traders.

### User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative with dynamic margin based on signal confidence
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

### Recent Updates (v3.2 - 2025-10-24)

#### 🎯 Multi-Timeframe Trading Strategy (Latest)
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
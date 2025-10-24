# Cryptocurrency Trading Bot v3.2

### Overview
This project is an automated cryptocurrency trading bot designed to monitor all 648 Binance USDT perpetual contracts. It employs ICT/SMC trading strategies combined with an intelligent 3-position management system to identify and execute trades. The bot provides comprehensive real-time notifications via Discord, keeping users informed of market activities and bot performance. Key features include full market coverage, advanced risk management with dynamic margin sizing (3%-13%) and win-rate based leverage (3-20x), exchange-level stop-loss/take-profit protection, and comprehensive trade logging for XGBoost machine learning. The business vision is to provide a robust, automated trading solution with advanced risk management and real-time insights for cryptocurrency traders.

### User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative with dynamic margin based on signal confidence
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

### Recent Updates (v3.2 - 2025-10-24)
**Critical Bug Fixes:**
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
- **Trading Strategy (ICT/SMC)**: Identifies order blocks, liquidity zones, and market structure. Uses MACD and EMA for confirmation and assigns a confidence score (70-100%). Includes OB triple validation, MSB amplitude filtering, and 1h trend filtering.
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
- **High-Frequency Trading Mode (v3.1)**:
    - Switched to 1-minute candles for rapid signal detection and execution
    - Breakeven-based stop-loss/take-profit calculation accounting for leverage and fees
    - Configurable risk/reward ratios (1:1 or 1:2) via RISK_REWARD_RATIO parameter
    - Trading fees: Maker 0.02%, Taker 0.04% (configurable)
    - Stop-loss positioned at breakeven ± 1.5 ATR buffer
    - Take-profit calculated using: risk × RISK_REWARD_RATIO
    - Optimized for short-term price movements with tight risk management

### External Dependencies
- **Binance API**: For real-time market data, order placement, and account information.
- **Discord API**: For sending notifications and interactive slash commands.
- **Python Libraries**: `numpy` for numerical operations, `asyncio` for asynchronous programming.
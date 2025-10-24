# Cryptocurrency Trading Bot v3.2

### Overview
This project is an automated cryptocurrency trading bot designed to monitor all 648 Binance USDT perpetual contracts. It employs ICT/SMC trading strategies combined with an intelligent 3-position management system to identify and execute trades. The bot provides comprehensive real-time notifications via Discord, keeping users informed of market activities and bot performance. Key capabilities include full market coverage, advanced risk management with dynamic margin sizing (3%-13%) and win-rate based leverage (3-20x), exchange-level stop-loss/take-profit protection, and comprehensive trade logging for XGBoost machine learning. The business vision is to provide a robust, automated trading solution with advanced risk management and real-time insights for cryptocurrency traders.

### User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative with dynamic margin based on signal confidence
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

### System Architecture
The bot features a modular, service-oriented design with production-ready risk management.

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
    - **Trend Definition**: 15-minute K-line with EMA200 determines overall trend direction.
    - **Execution**: 1-minute K-line for precise entry timing.
    - **Signal Components**: Order blocks, liquidity zones, market structure with MACD and EMA confirmation.
    - **Confidence Scoring**: 70-100% multi-factor weighting system.
    - **Validation**: OB triple validation, MSB amplitude filtering, 15m trend filtering to prevent counter-trend trades.
    - **Dynamic Risk/Reward**: 1:1 to 1:2 ratio based on signal confidence.
- **Intelligent Position Selection**: Scans all 648 symbols, scores signals by confidence/expected ROI, sorts them, and opens positions only for the top 3 signals, dynamically managing existing positions.
- **Advanced Risk Management**:
    - **Automatic Balance Loading**: Reads actual USDT futures balance from Binance API on startup and every trading cycle. Correctly distinguishes API failures (retains previous balance) from legitimate zero balances (updates to 0), ensuring accurate capital allocation. Periodic updates only log when balance changes >1% to reduce noise.
    - **Variable Margin Sizing**: Each position uses 3%-13% of total capital as margin (based on signal confidence).
    - **Win-Rate Based Leverage**: Leverage (3-20x) calculated from historical win rate.
    - Dynamic stop-loss/take-profit based on ATR.
    - Automatic drawdown alerts (5% triggers Discord alert).
    - Exchange-level stop-loss/take-profit orders for true position protection, optimized with Mark Price Triggering and Price Protection.
    - Min Notional validation with +2% safety margin.
- **XGBoost Machine Learning Integration**: Comprehensive logging of trade entry and exit data, including signal features, technical indicators, and K-line snapshots for training XGBoost models. Includes robust data integrity protection and a fallback mechanism for logging failures.
- **Virtual Position Tracking**: Tracks signals from 4th rank onwards as virtual positions (up to 10 concurrent) to generate large volumes of training data for XGBoost without real capital risk. Virtual positions are monitored, closed based on TP/SL or timeout, and data is saved with real trade data.
- **Technical Indicators**: Uses pure Python/NumPy for MACD, Bollinger Bands, EMA, and ATR.
- **Error Handling**: Implements exponential backoff retry decorators and intelligent retry strategies.
- **Dynamic Position Monitoring**: Continuously validates market conditions for open positions, detecting signal reversals and dynamically adjusting stop-loss/take-profit levels.
- **Immediate Rescan after Closure**: Forces a rescan of a trading pair immediately after a position is closed.
- **Security**: API keys stored in environment variables, trading disabled by default, testnet mode for testing, and no withdrawal permissions on API keys.
- **System Optimization**: API usage optimization includes invalid symbol blacklisting to reduce requests and intelligent retry mechanisms for virtual position price fetching to improve stability.

### External Dependencies
- **Binance API**: For real-time market data, order placement, and account information.
- **Discord API**: For sending notifications and interactive slash commands.
- **Python Libraries**: `numpy` for numerical operations, `asyncio` for asynchronous programming.
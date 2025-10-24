# Cryptocurrency Trading Bot v3.0

### Overview
This project is an automated cryptocurrency trading bot designed to monitor all 648 Binance USDT perpetual contracts. It utilizes ICT/SMC trading strategies combined with an intelligent 3-position management system to identify and execute trades. The bot provides comprehensive real-time notifications via Discord, ensuring users are informed of market activities and bot performance. Key features include full market coverage, advanced risk management (0.3% per trade, 0.5% max position, 33.33% capital per position), and dynamic signal selection based on confidence or ROI.

### User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative (low risk per trade)
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

### Recent Updates (October 24, 2025)
- **平倉後立即重新掃描機制** (NEW): 當任何倉位平倉後（止損/止盈/手動），系統會立即重新分析該交易對
  - 繞過30秒緩存，強制獲取最新市場數據 (`force_refresh=True`)
  - 如果發現新信號且有空閒倉位，立即開倉
  - 不等待下一個60秒週期，最大化資金使用效率
  - 使用異步回調機制（`asyncio.create_task`），不阻塞平倉流程
  - Discord 特殊通知："⚡ 快速重新進場"

### Recent Updates (October 23, 2025)
- **Automatic Account Balance Loading**: Bot now automatically reads real USDT balance from both Spot and Futures accounts (especially USDT-M Futures) on startup
- **Enhanced Balance Reporting**: Detailed logging shows Spot balance, Futures balance, and total USDT with capital allocation per position
- **Real-time Position Notifications**: Comprehensive Discord notifications for all position events:
  - 📈 Position opened: Entry price, stop-loss, take-profit, confidence, allocated capital, risk/reward ratio, **leverage**
  - 💰 Position closed: Exit price, PnL (USDT & %), holding duration, reason (stop-loss/take-profit/manual)
  - 🔴 Live trading mode indicator vs 🟡 Simulation mode
- **Railway Deployment Ready**: Fixed IP configured, ready for deployment on Railway EU West region
- **Discord Integration**: `/balance` command displays real-time account balance, slash commands for monitoring and control
- **Optimized Timeframe**: Changed from 1h to 15m K-lines for faster signal generation
- **Intelligent Confidence System**: Multi-weighted scoring (70% minimum threshold) - no longer requires 100% confidence to enter trades
  - Market Structure: 40%
  - MACD Confirmation: 20%
  - EMA Confirmation: 20%
  - Price Position: 10%
  - Liquidity Zone: 10%
- **Complete Bug Fixes**: All critical bugs resolved with defensive programming
  - Fixed strategy method call (analyze → generate_signal)
  - Added divide-by-zero protection for all calculations
  - Complete data validation for all indicators (ATR, MACD, EMA, price)
  - Exception handling for trade parameter calculations
  - Boundary checks for None, NaN, zero, and negative values
- **Dynamic Leverage Adjustment** (NEW): Intelligent leverage calculation based on signal confidence and market volatility
  - Confidence-based: 70-80% → 3x, 80-90% → 3-10x (linear), 90-100% → 10-20x (linear)
  - Volatility adjustment: Low volatility +20%, High volatility -30%
  - Configurable: MIN_LEVERAGE (3.0x) to MAX_LEVERAGE (20.0x)
  - Can be disabled via ENABLE_DYNAMIC_LEVERAGE=false

### System Architecture
The bot has undergone a significant architectural overhaul to v3.0, transitioning from a monolithic application to a modular, service-oriented design.

**UI/UX Decisions:**
- Interactive Discord Bot: Features slash commands (`/positions`, `/balance`, `/stats`, `/status`, `/config`) for real-time querying and uses Embed formats for aesthetic and clear responses. Auto-notifications are sent for trade cycles and executions.

**Technical Implementations & Design Choices:**
- **Modular Architecture**: Re-engineered with `main_v3.py` as the coordinator for various services.
- **Asynchronous I/O**: Enhanced `binance_client.py` with async methods for non-blocking data fetching, improving scanning time from 3-4 minutes to under 2 minutes.
- **Core Infrastructure**:
    - `RateLimiter`: Implements Token Bucket algorithm for Binance API request limits (1200 req/min).
    - `CircuitBreaker`: Provides fault tolerance, pausing operations after 5 failures for 60 seconds.
    - `CacheManager`: Utilizes LRU caching with a 30-second TTL for market data.
- **Service Layer**:
    - `DataService`: Handles concurrent batch data fetching and intelligent caching.
    - `StrategyEngine`: Manages multi-strategy analysis and signal ranking.
    - `ExecutionService`: Oversees the position lifecycle, including automatic stop-loss/take-profit.
    - `MonitoringService`: Collects system metrics and manages alerts.
- **Trading Strategy (ICT/SMC)**: Identifies order blocks, liquidity zones, and market structure. Uses MACD and EMA for confirmation and assigns a confidence score (70-100%).
- **Intelligent Position Selection**: Scans all 648 symbols, scores signals by confidence/expected ROI, sorts them, and opens positions only for the top 3 signals. It dynamically manages existing positions.
- **Advanced Risk Management**:
    - Automatic account balance detection from Binance API (Spot + Futures USDT)
    - Dual position limits based on 0.3% risk and a 0.5% maximum position size
    - Capital is divided into 3 equal parts, with each position using 33.33% of the allocated funds
    - Dynamic stop-loss/take-profit based on ATR
    - Automatic drawdown alerts (5% triggers Discord alert)
    - Real-time balance updates in Discord `/balance` command
- **Technical Indicators**: Uses pure Python/NumPy for MACD, Bollinger Bands, EMA, and ATR to reduce dependencies.
- **Dependency Optimization**: Significant reduction in external libraries, removing PyTorch LSTM and TA-Lib dependencies, leading to smaller Docker images and faster startup times.
- **Trade Logging**: Optimized batch writing for performance.
- **Security**: API keys stored in environment variables, trading disabled by default, testnet mode for testing, and no withdrawal permissions on API keys.

### External Dependencies
- **Binance API**: For real-time market data, order placement, and account information.
- **Discord API**: For sending notifications and interactive slash commands.
- **Python Libraries**: `numpy` for numerical operations, `asyncio` for asynchronous programming.
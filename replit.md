# Winiswin - Cryptocurrency Trading Bot

## Overview

Winiswin is an automated cryptocurrency trading bot designed for Binance USDT perpetual futures contracts. The system implements ICT (Inner Circle Trader) and SMC (Smart Money Concepts) trading strategies with multi-timeframe analysis and intelligent risk management.

### Key Features
- **Full Market Coverage**: Monitors 648+ USDT perpetual contracts on Binance
- **Multi-Timeframe Analysis**: 1-hour trend filtering + 15-minute signal generation
- **ICT/SMC Strategy**: Order blocks, liquidity zones, market structure breaks
- **Dynamic Risk Management**: Confidence-based leverage (3-20x), automatic stop-loss/take-profit
- **Discord Integration**: Real-time notifications and interactive commands
- **Machine Learning Ready**: XGBoost training data collection infrastructure

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Design Principles

**Modular Service Architecture**: The system follows a service-oriented design where each major function is isolated into dedicated services with clear boundaries and responsibilities.

**Multi-Timeframe Strategy**: 
- Primary: 15-minute candles for signal generation and execution
- Secondary: 1-hour candles for trend filtering and directional bias
- This dual-layer approach balances responsiveness with signal quality

**Conservative Risk Philosophy**: The bot prioritizes capital preservation over aggressive profits. It uses:
- Minimum 70% confidence threshold for signals
- Triple verification for order blocks
- Dynamic position sizing based on confidence levels
- Maximum 3 concurrent positions to manage risk exposure

### Service Modules

**1. Data Service** (`services/data_service.py`)
- Centralized market data fetching with intelligent caching
- Batch processing for multiple symbols
- Rate limiting to respect Binance API constraints
- Cache TTL management (30-60 seconds depending on data type)
- Handles all K-line data retrieval for multiple timeframes

**2. Strategy Engine** (`services/strategy_engine.py`)
- Implements ICT/SMC signal generation logic
- Order block identification with triple verification
- Liquidity zone detection
- Market structure break confirmation
- Multi-level confidence scoring system (40/20/20/10/10 weights)
- Filters signals below 70% confidence threshold

**3. Execution Service** (`services/execution_service.py`)
- Position management and order placement
- Converts signals into actual Binance futures orders
- Dynamic leverage calculation (3-20x based on confidence)
- Stop-loss and take-profit management
- Position tracking and monitoring
- Enforces max 3 concurrent positions limit

**4. Risk Manager** (`risk_manager.py`)
- Dynamic leverage adjustment based on:
  - Signal confidence level (higher confidence = higher leverage)
  - Market volatility (ATR-based)
  - Historical win rate
- Position sizing using capital allocation per position (33.33% per slot)
- Margin calculation (3-13% of total capital per position)
- Ensures minimum notional value requirements ($5 USDT)

**5. Virtual Position Tracker** (`services/virtual_position_tracker.py`)
- Tracks hypothetical positions for machine learning training
- Collects 38 standardized features per trade
- Records outcomes without real capital exposure
- Prepares data for future XGBoost model integration

**6. Monitoring Service** (`services/monitoring_service.py`)
- System health checks and metrics
- API rate limit monitoring
- Memory usage tracking
- Performance metrics collection

### Trading Strategy Logic

**ICT/SMC Methodology**:
1. **Order Blocks (OB)**: Identifies institutional order zones - the last opposing candle before a strong price move
2. **Liquidity Zones**: Detects areas where price seeks liquidity (recent highs/lows)
3. **Market Structure**: Tracks higher highs/higher lows (bullish) or lower highs/lower lows (bearish)
4. **Market Structure Break (MSB)**: Confirms trend changes when structure is violated

**Signal Generation Flow**:
1. Fetch 250 candles of 15m data for primary analysis
2. Fetch 250 candles of 1h data for trend filtering
3. Identify order blocks using price action patterns
4. Calculate technical indicators (EMA, MACD, RSI, ATR)
5. Check bullish/bearish conditions with multi-level scoring
6. Filter by 1h trend (only trade with the higher timeframe bias)
7. Generate signal if confidence ≥ 70%

**Confidence Scoring Breakdown**:
- Base score (40%): Price position relative to support/resistance
- Market structure (20%): Bullish/bearish/neutral structure
- 1h trend alignment (20%): Matches higher timeframe
- MACD confirmation (10%): Momentum indicator
- Volume/volatility (10%): Market conditions

### Data Flow

**Main Loop (60-second cycles)**:
```
1. Fetch all USDT perpetual symbols from Binance
2. Batch fetch market data (50 symbols at a time)
3. Analyze each symbol with ICT/SMC strategy
4. Collect signals above 70% confidence
5. Sort signals by confidence/ROI
6. Execute top 3 signals (if position slots available)
7. Monitor existing positions for stop-loss/take-profit
8. Update virtual positions for ML training
9. Send Discord notifications
10. Wait 60 seconds, repeat
```

### Risk Management

**Capital Allocation**:
- Total capital divided into 3 equal slots (33.33% each)
- Each position uses one slot
- Margin per position: 3-13% of total capital (varies by confidence)
- Effective leverage amplifies position size

**Dynamic Leverage Calculation**:
- Base leverage from confidence: 70%=3x, 90%=10x, 100%=20x
- Volatility adjustment: Low volatility (+0.6-2x), High volatility (-1-2x)
- Win rate factor: Recent performance influences leverage
- Final range: 3x minimum to 20x maximum

**Stop-Loss/Take-Profit**:
- Stop-loss: Entry ± 2x ATR (Average True Range)
- Take-profit: Entry ± 3x ATR
- Risk-to-reward ratio approximately 1:1.5

### Deployment Configuration

**Railway Deployment** (`railway.json`):
- Uses Nixpacks builder for Python 3.11
- Starts with `python -m src.main`
- Auto-restart on failure (max 10 retries)
- Deployed to EU West region for Binance API compatibility

**Environment Variables**:
- `BINANCE_API_KEY` / `BINANCE_SECRET_KEY`: API credentials
- `ENABLE_TRADING`: false=paper trading, true=live trading
- `SYMBOL_MODE`: auto (top N), all (648), or static (manual list)
- `MAX_CONCURRENT_POSITIONS`: Default 3 positions
- `DISCORD_BOT_TOKEN` / `DISCORD_CHANNEL_ID`: Notification setup

## External Dependencies

### APIs and Services

**Binance Futures API**:
- Primary data source for all market data
- K-line (candlestick) data retrieval
- Order placement and position management
- Account balance and position information
- Rate limit: 1200 requests per minute
- Requires deployment in non-restricted regions (EU recommended)

**Discord API**:
- Real-time trade notifications
- Interactive slash commands for bot control
- Status updates and alerts
- Optional feature (bot works without Discord if disabled)

### Python Libraries

**Core Dependencies** (`requirements.txt`):
- `python-binance==1.0.19`: Official Binance API wrapper
- `discord.py==2.3.2`: Discord bot framework
- `pandas==2.1.4`: Data manipulation and analysis
- `numpy==1.26.3`: Numerical computations for indicators
- `python-dotenv==1.0.0`: Environment variable management
- `requests==2.32.3`: HTTP requests for API calls

**Technical Indicators**: All indicators (EMA, MACD, RSI, ATR) are implemented using pure NumPy/Pandas without external libraries like TA-Lib, reducing deployment complexity and memory usage.

### Data Storage

**Local JSON Files**:
- `data/trades.json`: Historical trade log
- `data/ml_pending_entries.json`: Virtual positions for ML training
- No external database required
- File-based persistence for simplicity

### Infrastructure

**Railway Platform**:
- Cloud hosting with EU West deployment
- Static outbound IPs for Binance whitelist compatibility
- Automatic builds from GitHub
- Environment variable management
- Logs and monitoring dashboard

**GitHub**:
- Source code version control
- Automated deployment triggers
- Repository: https://github.com/M116cj/winiswin

**Note**: The system is designed to be lightweight and self-contained, minimizing external dependencies while maintaining full functionality for automated cryptocurrency trading.
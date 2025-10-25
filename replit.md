# Winiswin - Cryptocurrency Trading Bot

## Overview

Winiswin is an automated cryptocurrency trading bot designed for Binance USDT perpetual futures contracts. The system uses ICT (Inner Circle Trader) and SMC (Smart Money Concepts) trading strategies to analyze market structure and generate trading signals across multiple timeframes.

**Current Version**: v3.2 Enhanced  
**Platform**: Binance Futures USDT Perpetual Contracts  
**Strategy**: ICT/SMC Multi-Timeframe Analysis  
**Deployment**: Railway (Europe West recommended)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Design Principles

**1. Modular Service Architecture**
- Separation of concerns across distinct services
- Clear boundaries between data, strategy, execution, and monitoring layers
- Event-driven coordination through main orchestrator

**2. Multi-Timeframe Strategy**
The system evolved from 1-hour focused analysis to a dual-layer approach:
- **Primary (15m)**: Core signal generation, position calculations, and trade execution using ta-lib-binary for fast technical indicator computation
- **Secondary (1h)**: Trend filtering and risk adjustment to improve signal quality and avoid counter-trend trades

This balances reaction speed (4x faster than hourly) with signal quality (less noise than 1-minute data).

**3. Risk Management**
- Dynamic leverage calculation (3-20x) based on confidence levels and volatility
- Capital split into 3 equal portions for position diversification
- Margin requirements: 3-13% of total capital per position
- Multi-level confidence scoring system (minimum 70% threshold)

**4. Data Flow & Caching Strategy**

The system implements a sophisticated caching mechanism to minimize API calls:

```
Market Data Service (services/data_service.py)
├─ Unified Cache Manager (TTL: 30-60s)
├─ Batch Fetching (50 symbols per request)
├─ Rate Limiting (1200 req/min)
└─ Circuit Breaker (5 failures → 60s timeout)
```

**Key Decisions**:
- **Why unified caching?** Reduces 80%+ redundant API calls by storing kline data across all consumers
- **Why 30-60s TTL?** Balances data freshness for 15m analysis with API efficiency
- **Why batch fetching?** Processes 648 trading pairs in ~6-7 seconds instead of 10+ minutes

**5. Signal Generation Pipeline**

```
1. Order Block Detection → 2. Liquidity Zone Identification → 
3. Market Structure Analysis → 4. Technical Indicators (MACD, EMA, RSI, ATR) → 
5. Multi-Level Confidence Scoring → 6. 1h Trend Filter → 7. Signal Output
```

Confidence scoring uses weighted components:
- 1h trend alignment: 40%
- Market structure: 20%
- Price position (support/resistance): 20%
- Momentum indicators: 10%
- Volatility assessment: 10%

**6. XGBoost Machine Learning Preparation**

The system collects comprehensive training data for future ML integration:
- 38 standardized features per trade
- Virtual position tracking for non-executed signals
- Smart flush mechanism (every 25 entries or 5-minute intervals)
- Data validation ensures no missing values before recording

**Rationale**: While current trading uses pure technical analysis, the infrastructure is prepared for gradient boosting models that can learn from historical performance patterns.

**7. Position Management**

Three-slot concurrent position system:
- Maximum 3 simultaneous positions
- Each position uses 33.33% of total capital
- Position sizing calculated using: Entry Price, Stop Loss (2x ATR), and Dynamic Leverage
- Continuous validation: Positions are re-evaluated every cycle to ensure conditions remain valid

**8. Error Handling & Resilience**

- Exponential backoff retry mechanism for transient failures
- Circuit breaker pattern for API protection
- Graceful degradation (Discord failures don't block trading)
- Comprehensive logging at all critical points

### Technology Stack

**Core Framework**: Python 3.11  
**Technical Analysis**: numpy, pandas (lightweight, no heavy ML dependencies)  
**API Client**: python-binance (Binance USDT Futures)  
**Notifications**: discord.py  
**Deployment**: Railway (Nixpacks builder)

**Notable Architectural Decisions**:
- **Removed PyTorch LSTM**: Initial versions included LSTM models, but removed to reduce memory (800MB → 150MB) and build time (8min → 2min). Pure technical indicators proved more stable and faster.
- **No TA-Lib dependency**: Replaced with native numpy/pandas implementations to avoid compilation issues and reduce complexity.

### File Structure

```
src/                          # All source code
├─ main.py                   # Main orchestrator
├─ config.py                 # Configuration management
├─ clients/
│  └─ binance_client.py      # Binance API wrapper
├─ integrations/
│  └─ discord_bot.py         # Discord integration
├─ managers/
│  ├─ risk_manager.py        # Dynamic risk & leverage calculation
│  └─ trade_logger.py        # XGBoost data recorder
├─ monitoring/
│  ├─ health_check.py        # Health checks
│  └─ railway_status.py      # Railway deployment status
├─ services/
│  ├─ data_service.py        # Market data with caching & rate limiting
│  ├─ strategy_engine.py     # ICT/SMC signal generation
│  ├─ execution_service.py   # Order execution & position management
│  ├─ monitoring_service.py  # System metrics & health checks
│  └─ virtual_position_tracker.py # ML training data collection
├─ strategies/
│  └─ ict_smc.py             # ICT/SMC strategy implementation
├─ core/
│  ├─ cache_manager.py       # Unified caching layer
│  ├─ rate_limiter.py        # API rate limiting
│  └─ circuit_breaker.py     # Fault tolerance
└─ utils/
   ├─ indicators.py          # Technical indicators (EMA, RSI, MACD, ATR)
   └─ helpers.py             # Utility helper functions

data/                         # Data files
├─ trades.json               # Trade history
├─ ml_pending_entries.json   # ML training data buffer
└─ logs/
   └─ trading_bot.log        # Application logs

docs/                         # Documentation
├─ README.md                 # Project overview
├─ replit.md                 # Technical documentation
├─ OPTIMIZATION_REPORT_V3.2.md # Optimization report
└─ V3.0_SYSTEM_VALIDATION.md   # System validation
```

## External Dependencies

### Third-Party APIs

**1. Binance Futures API**
- Purpose: Market data and trade execution
- Endpoints: 
  - `/fapi/v1/exchangeInfo` - Trading pair metadata
  - `/fapi/v1/klines` - Candlestick data (1m, 15m, 1h)
  - `/fapi/v1/order` - Order placement
  - `/fapi/v2/account` - Account balance
  - `/fapi/v2/positionRisk` - Open positions
- Rate Limits: 1200 requests/minute (enforced by internal limiter)
- Authentication: API Key + Secret (HMAC-SHA256 signatures)

**Important**: Binance blocks requests from certain regions (US, Singapore, etc.). Deployment must use Railway Europe West region for API access.

**2. Discord Bot API**
- Purpose: Real-time notifications and interactive commands
- Features:
  - Slash commands for status checks (`/balance`, `/positions`, `/stats`)
  - Trade alerts with formatted embeds
  - System health notifications
- Authentication: Bot token via environment variable

### Database & Persistence

**Local JSON Files** (no external database):
- `data/trades.json` - Trade history
- `data/ml_pending_entries.json` - XGBoost training data buffer
- `data/logs/` - Application logs

**Rationale**: Simple JSON storage reduces infrastructure complexity and deployment requirements. Suitable for single-instance deployment with <10,000 trades/month volume.

### Environment Variables

Required configuration (see `.env` file):

```bash
# Binance API Credentials
BINANCE_API_KEY=<your_api_key>
BINANCE_SECRET_KEY=<your_secret_key>
BINANCE_TESTNET=false

# Discord Integration
DISCORD_BOT_TOKEN=<your_bot_token>
DISCORD_CHANNEL_ID=<your_channel_id>

# Trading Configuration
ENABLE_TRADING=false           # Set to 'true' for live trading
SYMBOL_MODE=all                # all/auto/static
MAX_SYMBOLS=648                # Number of trading pairs to monitor

# Risk Parameters
RISK_PER_TRADE_PERCENT=0.3
MAX_POSITION_SIZE_PERCENT=0.5
DEFAULT_LEVERAGE=3.0
MIN_LEVERAGE=3.0
MAX_LEVERAGE=20.0

# Position Management
MAX_CONCURRENT_POSITIONS=3
```

### Deployment Platform

**Railway** (recommended):
- Region: Europe West (for Binance API access)
- Nixpacks builder (auto-detected from `requirements.txt`)
- Restart policy: ON_FAILURE with 10 max retries
- Static outbound IPs recommended for API whitelisting

**Alternative Considerations**:
- Replit: ❌ Blocked by Binance region restrictions
- Local: ❌ Requires 24/7 uptime and stable internet
- Other cloud providers: Ensure Europe/Asia regions for API access
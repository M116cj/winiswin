# Overview

This is a cryptocurrency trading bot (v3.0) designed for automated trading on Binance Futures using the ICT/SMC (Inner Circle Trader/Smart Money Concepts) strategy. The bot analyzes market data, generates trading signals based on order blocks and liquidity zones, and executes trades with dynamic risk management.

**Key Features:**
- ICT/SMC-based trading strategy focusing on order blocks and market structure
- Multi-symbol monitoring (up to 648 USDT perpetual contracts)
- Dynamic leverage adjustment (3x-20x) based on confidence and volatility
- Position management with stop-loss/take-profit automation
- Discord notifications for trade alerts and monitoring
- Modular service architecture for maintainability

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Trading Strategy (ICT/SMC)

**Order Block Detection:**
- Identifies institutional order zones (last reversal candles before strong moves)
- Validates order blocks with price action confirmation
- Tracks bullish/bearish order blocks for entry opportunities

**Market Structure Analysis:**
- Monitors higher highs/lows for trend identification
- Detects market structure breaks (MSB) for reversal signals
- Uses 15-minute candles as primary timeframe

**Signal Generation:**
- Multi-factor confidence scoring system (70-100% scale)
- Combines technical indicators (MACD, RSI, EMA, ATR) for filtering
- Prioritizes top 3 signals per cycle to avoid overtrading

## Risk Management Architecture

**Dynamic Leverage System:**
- Base leverage calculated from confidence score (70% → 3x, 90% → 10x, 100% → 20x)
- Volatility adjustments using ATR (Average True Range)
- Automatic margin calculation to meet minimum notional requirements

**Position Limits:**
- Maximum 3 concurrent positions (33.33% capital allocation each)
- Margin usage: 3-13% of total account balance per position
- Safety margin applied to meet Binance's $5 minimum notional requirement

**Stop-Loss/Take-Profit:**
- Dynamic SL/TP based on ATR multiples
- Breakeven price calculation includes trading fees
- Risk-reward ratio tracking for performance analysis

## Service Layer Architecture

**DataService:**
- Async batch fetching of market data from Binance
- Caching mechanism with TTL to reduce API calls
- Rate limiting (1200 req/min) to comply with Binance limits
- Handles symbol validation and filtering

**StrategyEngine:**
- Signal generation using ICT/SMC logic
- Confidence scoring with weighted factors (trend, structure, price zones)
- Signal filtering and prioritization (top 3 per cycle)

**ExecutionService:**
- Order placement with Binance Futures API
- Position tracking and monitoring
- Stop-loss/take-profit order management
- Order quantity formatting per symbol requirements

**MonitoringService:**
- System health metrics tracking
- Performance statistics (win rate, profit/loss)
- Circuit breaker for fault tolerance
- Trade logging for ML training data preparation

## Error Handling & Resilience

**Retry Mechanism:**
- Exponential backoff for transient network errors
- Maximum 3 retries with configurable delays
- Graceful degradation for non-critical failures

**Circuit Breaker Pattern:**
- Protects against cascading failures
- Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
- Automatic recovery attempts after timeout

**API Error Classification:**
- Distinguishes recoverable (network timeout) vs non-recoverable (invalid API key) errors
- Rate limit handling with automatic backoff
- Invalid symbol filtering to avoid repeated errors

## Data Storage

**Trade Logging:**
- JSON-based trade history (`trades.json`)
- ML training data preparation (`ml_training_data.json`)
- Pending entry tracking persisted to disk (recovery on restart)

**Position Tracking:**
- In-memory position state with RiskManager
- Virtual position tracker for paper trading mode
- Entry/exit data correlation for performance analysis

## Configuration Management

**Environment Variables:**
- Binance API credentials (API_KEY, SECRET_KEY, TESTNET flag)
- Discord bot configuration (TOKEN, CHANNEL_ID)
- Risk parameters (leverage, position size, risk per trade)
- Symbol selection mode (static/auto/all)
- Trading toggle (ENABLE_TRADING flag)

**Symbol Selection Modes:**
- `static`: Fixed 5 trading pairs
- `auto`: Top N symbols by volume
- `all`: All 648+ USDT perpetual contracts

# External Dependencies

## Trading Platform
- **Binance Futures API**: Primary trading execution platform
  - Market data fetching (Klines/candlestick data)
  - Order placement and management
  - Account balance queries
  - Futures-specific endpoints (leverage, position mode)

## Communication
- **Discord Bot API**: Real-time notifications and monitoring
  - Slash commands for status queries (/balance, /status, /positions)
  - Trade alerts and system notifications
  - Error/warning messages

## Data Processing
- **NumPy**: Technical indicator calculations (moving averages, volatility)
- **Pandas**: Time-series data manipulation and analysis
  - Candlestick data processing
  - Indicator computation
  - Signal generation logic

## Python Libraries
- `python-binance`: Binance API wrapper (v1.0.19)
- `discord.py`: Discord bot framework (v2.3.2)
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for API calls

## Deployment Platform
- **Railway**: Cloud hosting platform
  - Configured via `railway.json`
  - Nixpacks builder for containerization
  - EU region deployment (europe-west4)
  - Auto-restart on failure (max 10 retries)

## Database
- **Note**: Currently file-based (JSON). The system architecture supports future database integration (e.g., PostgreSQL with Drizzle ORM) for:
  - Trade history persistence
  - ML training data storage
  - Performance metrics tracking
  - Position state recovery
# Cryptocurrency Trading Bot

## Overview
An automated cryptocurrency trading bot that monitors Binance markets, uses ICT/SMC strategies and LSTM models for predictions, manages risk automatically, and sends notifications via Discord.

## Features
- **Real-time Market Monitoring**: Connects to Binance API for live market data (K-lines, funding rates, long/short ratios)
- **Technical Analysis**: Calculates indicators (MACD, Bollinger Bands, EMA, ATR, RSI) using TA-Lib
- **ICT/SMC Strategy**: Identifies order blocks, liquidity zones, and market structure
- **LSTM Price Prediction**: Neural network model for price forecasting
- **Arbitrage Detection**: Monitors spot vs futures price differences
- **Risk Management**: Automated position sizing, stop-loss, and take-profit based on ATR
- **Discord Notifications**: Real-time trade alerts and performance reports
- **Trade Logging**: Persistent storage of all trades with performance statistics

## Project Structure
```
.
├── main.py                 # Main bot entry point
├── config.py              # Configuration management
├── binance_client.py      # Binance API integration
├── discord_bot.py         # Discord notification system
├── risk_manager.py        # Risk management and position tracking
├── trade_logger.py        # Trade logging and statistics
├── utils/
│   ├── indicators.py      # Technical indicators (MACD, BB, EMA, ATR)
│   └── helpers.py         # Utility functions
├── strategies/
│   ├── ict_smc.py        # ICT/SMC trading strategy
│   └── arbitrage.py      # Arbitrage detection
└── models/
    └── lstm_model.py     # LSTM price prediction model
```

## Setup Instructions

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:

```bash
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=true

DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_discord_channel_id_here

ENABLE_TRADING=false  # Set to true for live trading
```

**Important Security Notes:**
- Create API keys with trading permissions but **DISABLE WITHDRAWAL**
- Start with TESTNET mode (`BINANCE_TESTNET=true`)
- Keep `ENABLE_TRADING=false` for simulation mode

### 2. Get API Keys

**Binance API:**
1. Go to Binance.com → Account → API Management
2. Create new API key with trading permissions
3. **Disable** withdrawal permissions for security
4. Add IP whitelist for additional security

**Discord Bot:**
1. Go to Discord Developer Portal
2. Create new application → Bot
3. Copy bot token
4. Enable necessary permissions and invite to your server
5. Get channel ID from Discord (right-click channel → Copy ID)

### 3. Run the Bot
The bot runs automatically via the configured workflow. It will:
- Initialize connections to Binance and Discord
- Train LSTM model on historical data
- Monitor markets every 60 seconds
- Execute trades based on strategy signals
- Send notifications to Discord

## Configuration

### Risk Parameters (config.py)
- `RISK_PER_TRADE_PERCENT`: Maximum risk per trade (default: 1.0%)
- `MAX_POSITION_SIZE_PERCENT`: Maximum position size (default: 1.5% of balance)
- `DEFAULT_LEVERAGE`: Trading leverage (default: 1.0x)
- `STOP_LOSS_ATR_MULTIPLIER`: Stop loss distance in ATR units (default: 2.0)
- `TAKE_PROFIT_ATR_MULTIPLIER`: Take profit distance in ATR units (default: 3.0)

### Trading Parameters
- `SYMBOLS`: List of trading pairs (default: ['BTCUSDT', 'ETHUSDT'])
- `TIMEFRAME`: Candle timeframe (default: '1h')
- `MODEL_RETRAIN_INTERVAL`: Model retraining frequency in seconds (default: 3600)

## Trading Strategy

### ICT/SMC (Inner Circle Trader / Smart Money Concepts)
1. **Order Blocks**: Identifies institutional entry zones
2. **Liquidity Zones**: Detects support/resistance levels
3. **Market Structure**: Analyzes bullish/bearish trends
4. **Confirmation**: Uses MACD and EMA crossovers

### LSTM Model
- Trained on 500 periods of historical data
- Features: Close, Volume, MACD, RSI, ATR
- Confirms strategy signals with price predictions
- Retrains every hour to adapt to market changes

### Risk Management
- Position sizing based on account balance and stop-loss distance
- Dynamic stop-loss and take-profit using ATR
- Maximum drawdown alerts at 5%
- Automatic position tracking and closure

## Recent Changes
- **2025-10-23**: Configured for small capital live trading
  - **Adjusted risk parameters for conservative live trading**:
    - RISK_PER_TRADE_PERCENT: 1.0% → **0.3%**
    - MAX_POSITION_SIZE_PERCENT: 1.5% → **0.5%**
  - Created comprehensive production deployment guides
  - Prepared Railway deployment with live trading configuration
  - Added emergency stop procedures and monitoring guidelines
  
- **2025-10-22**: Initial project setup with complete trading infrastructure
  - Implemented Binance API client with WebSocket support and error handling
  - Created ICT/SMC and arbitrage strategies
  - Built LSTM model for price prediction with NaN handling
  - Set up Discord notification system
  - Implemented comprehensive risk management with defensive checks
  - Added trade logging and performance tracking
  - Fixed NaN handling in technical indicators (removed leading NaNs only)
  - Added data validation at every stage (indicators, model training, risk calculations)
  - Created Railway deployment configuration with GitHub Actions CI/CD
  - Configured for Singapore deployment region to avoid Binance geo-restrictions
  - **Grok 4 System Check**: Fixed TA-Lib deployment dependency, all systems verified

## User Preferences
- Language: Traditional Chinese (繁體中文)
- Trading mode: Conservative (low risk per trade)
- Focus on: ICT/SMC strategy with ML confirmation
- Notifications: Discord alerts for all trades and warnings

## Next Phase Features
- xAI Grok 4 integration for automated model iteration
- Multi-model comparison (LSTM, ARIMA, XGBoost, Transformer)
- Advanced arbitrage (triangular arbitrage across multiple pairs)
- Sentiment analysis from X platform
- VaR (Value at Risk) modeling
- PostgreSQL database for persistent storage
- Redis caching for market data
- Interactive Discord commands
- Dynamic leverage adjustment

## Safety & Compliance
- All API keys stored in environment variables
- Trading disabled by default (simulation mode)
- Testnet mode for safe testing
- Comprehensive error logging
- Automatic drawdown alerts
- No withdrawal permissions on API keys

## Support
For issues or questions:
1. Check logs in `trading_bot.log`
2. Review trade history in `trades.json`
3. Monitor Discord notifications
4. Verify API keys and permissions

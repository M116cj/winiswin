# Cryptocurrency Trading Bot v3.0 (全量648幣種 + 智能3倉位管理)

## Overview
An automated cryptocurrency trading bot that monitors ALL 648 Binance USDT perpetual contracts, uses ICT/SMC trading strategies with intelligent 3-position management, and sends comprehensive notifications via Discord.

**v3.0 重大升級**：
- 📊 監控全交易所 648 個 USDT 永續合約
- 🎯 智能 3 倉位管理系統（資金三等分，只持有最優倉位）
- 🔍 按信心度或投報率自動選擇最優信號
- ⚖️ 雙重風險保護（0.3% 每筆 + 0.5% 最大倉位）
- 💰 每個倉位使用賬戶 33.33% 的資金

## Features
- **Full Market Coverage**: Monitors ALL 648 USDT perpetual contracts on Binance
- **Intelligent Position Management**: 
  - Maximum 3 concurrent positions (資金三等分)
  - Automatic signal ranking by confidence or ROI
  - Only trades the top 3 signals each cycle
- **Real-time Market Monitoring**: Connects to Binance API for live market data
- **Technical Analysis**: Lightweight indicators (MACD, Bollinger Bands, EMA, ATR, RSI) using pure Python/NumPy
- **ICT/SMC Strategy**: Identifies order blocks, liquidity zones, and market structure with confidence scoring
- **Advanced Risk Management**: 
  - Double protection: 0.3% risk per trade + 0.5% max position
  - Capital allocation: 33.33% per position (3 equal parts)
  - Dynamic position sizing based on ATR and allocated capital
- **Interactive Discord Bot**: 
  - **Slash Commands**: `/positions`, `/balance`, `/stats`, `/status`, `/config`
  - Uses Discord's official Application Commands API
  - Real-time position查询
  - Account balance and performance查詢
  - Detailed statistics on demand
  - Auto notifications for cycles and trades
- **Trade Logging**: Optimized batch writing for better performance

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
- `RISK_PER_TRADE_PERCENT`: Maximum risk per trade (default: 0.3%)
- `MAX_POSITION_SIZE_PERCENT`: Maximum position size (default: 0.5% of allocated capital)
- `MAX_CONCURRENT_POSITIONS`: Maximum simultaneous positions (default: 3)
- `CAPITAL_PER_POSITION_PERCENT`: Capital per position (default: 33.33% = 100/3)
- `DEFAULT_LEVERAGE`: Trading leverage (default: 1.0x)
- `STOP_LOSS_ATR_MULTIPLIER`: Stop loss distance in ATR units (default: 2.0)
- `TAKE_PROFIT_ATR_MULTIPLIER`: Take profit distance in ATR units (default: 3.0)

### Trading Parameters
- `SYMBOL_MODE`: Trading pair selection mode (default: **'all'** for 648 pairs)
  - `static`: Use predefined list (5 pairs: BTC, ETH, BNB, SOL, XRP)
  - `auto`: Auto-select top N pairs by volume
  - `all`: Monitor all 648 USDT perpetual pairs ✅ **CURRENT DEFAULT**
- `MAX_SYMBOLS`: Maximum symbols (default: 648)
- `TIMEFRAME`: Candle timeframe (default: '1h')

## Trading Strategy

### ICT/SMC (Inner Circle Trader / Smart Money Concepts)
1. **Order Blocks**: Identifies institutional entry zones
2. **Liquidity Zones**: Detects support/resistance levels
3. **Market Structure**: Analyzes bullish/bearish trends
4. **Confirmation**: Uses MACD and EMA crossovers
5. **Confidence Scoring**: 
   - Base: 70% (structure detected)
   - +10% for MACD confirmation
   - +10% for EMA confirmation
   - +10% for liquidity zone alignment
   - Maximum: 100%

### Intelligent Position Selection (NEW in v3.0)
**每個交易週期的流程：**
1. **掃描階段**: 分析所有 648 個幣種，收集所有交易信號
2. **評分階段**: 計算每個信號的：
   - **信心度** (Confidence): 基於技術指標一致性 (70-100%)
   - **預期投報率** (Expected ROI): 基於止盈/止損比例
3. **排序階段**: 按信心度或投報率排序所有信號
4. **執行階段**: 只對前 3 個最優信號開倉
5. **管理階段**: 持續監控現有倉位，觸及止損/止盈自動平倉

**排序模式（可配置）：**
- `sort_by='confidence'`: 優先選擇信心度最高的信號（預設）
- `sort_by='roi'`: 優先選擇預期投報率最高的信號

### Risk Management (Enhanced in v3.0)
- **雙重倉位限制**:
  1. 基於風險的倉位計算（0.3% 風險）
  2. 最大倉位限制（分配資金的 0.5%）
- **資金分配**: 
  - 總資金平均拆成 3 等份
  - 每個倉位使用 33.33% 的資金
  - 最多同時持有 3 個倉位
- **動態止損止盈**: 基於 ATR 自動計算
- **最大回撤警報**: 5% 觸發 Discord 警報
- **自動倉位管理**: 觸及目標自動平倉

## Recent Changes
- **2025-10-23**: **Discord 斜線命令系統（Application Commands）**
  - 使用 Discord 官方規範的斜線命令（Slash Commands）
  - 5 個互動命令：`/positions`, `/balance`, `/stats`, `/status`, `/config`
  - 自動補全和內建說明
  - 使用 `app_commands` API
  - 實時查詢當前持倉
  - 查看賬戶餘額和資金分配
  - 詳細性能統計
  - 機器人狀態和配置查詢
  - 美觀的 Embed 格式回應
  - 創建 DISCORD_COMMANDS_GUIDE.md 完整文檔

- **2025-10-23**: **v3.0 全量監控 + 智能3倉位管理系統**
  - **全交易所監控**: 預設監控所有 648 個 USDT 永續合約
  - **3 倉位管理**: 資金拆成 3 等份，最多同時持有 3 個倉位
  - **智能信號選擇**: 
    - 收集所有信號 → 計算信心度和投報率 → 排序 → 只執行前 3 個
    - 可按信心度或投報率排序
  - **增強風險管理**:
    - 每倉位使用賬戶 33.33% 的資金
    - 雙重保護: 0.3% 風險 + 0.5% 最大倉位
    - 動態倉位計算基於分配資金
  - **完整測試**: 5 個測試全部通過
    - ✅ 最大倉位數限制（3個）
    - ✅ 資金分配（33.33% 每倉位）
    - ✅ 信號排序（信心度 vs 投報率）
    - ✅ 完整週期模擬
    - ✅ 配置驗證
  - **增強 Discord 通知**:
    - 週期開始顯示倉位狀態（X/3）
    - 信號通知包含信心度和預期投報率
    - 週期完成顯示詳細統計

- **2025-10-23**: **v2.0 重大優化 - Grok 4 架構審查**
  - **移除 PyTorch LSTM**：從 ~800MB 降到 ~150MB 記憶體
  - **純 Python 技術指標**：替換 TA-Lib，無需原生編譯
  - **優化依賴**：從 12 個減到 6 個（移除 torch, matplotlib, aiohttp, websockets, scikit-learn, TA-Lib）
  - **條件性 Discord**：按需初始化，節省 ~100MB
  - **批量寫入**：TradeLogger 緩衝優化
  - **構建時間**：從 ~8 分鐘降到 ~2 分鐘 (75% ↓)
  - **啟動時間**：從 3-5 分鐘降到 10-20 秒 (90% ↓)
  - **Docker 鏡像**：從 ~3.5GB 降到 ~800MB (77% ↓)
  
- **2025-10-23**: Expanded to ALL Binance USDT perpetual pairs (648 contracts)
  - **Dynamic trading pair selection system**:
    - `SYMBOL_MODE=static`: 5 predefined pairs (BTC, ETH, BNB, SOL, XRP)
    - `SYMBOL_MODE=auto`: Top N pairs by volume (default: 50, configurable)
    - `SYMBOL_MODE=all`: All 648 USDT perpetual contracts
  - **Multi-model LSTM management**: Separate LSTM model for each trading pair
  - **Volume-based ranking**: Auto-select most liquid markets
  - **Resource optimization**: Configurable symbol limits to balance coverage vs resources
  - Created ALL_PAIRS_DEPLOYMENT_GUIDE.md with scaling strategies
  
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

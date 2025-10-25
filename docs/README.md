# 🤖 Cryptocurrency Trading Bot v3.2

自動化加密貨幣交易機器人，採用 ICT/SMC 策略，專為 Binance USDT 永續合約設計。

## ✨ 核心功能

- 📊 **全市場監控**：648 個 USDT 永續合約
- 🎯 **ICT/SMC 策略**：多時間框架分析（1h/15m/1m）
- 🛡️ **智能風險管理**：動態槓桿 3-20x，自動止損/止盈
- 💬 **Discord 集成**：實時通知和交互式指令
- 🤖 **XGBoost 準備**：完整的機器學習訓練數據收集

## 🚀 快速開始

### 1. 環境配置

```bash
# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 添加您的 API 密鑰
```

### 2. 環境變數

```bash
# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id

# 交易設置
ENABLE_TRADING=false  # true 啟用實盤交易
SYMBOL_MODE=all       # all/auto/static
```

### 3. 運行

```bash
# 本地運行
python main_v3.py

# Railway 部署
railway up
```

## 📊 系統架構

```
main_v3.py (協調器)
├─ services/
│  ├─ data_service.py        # 市場數據（緩存、批量）
│  ├─ strategy_engine.py     # 信號生成
│  ├─ execution_service.py   # 訂單執行
│  ├─ monitoring_service.py  # 系統監控
│  └─ virtual_position_tracker.py  # ML 數據生成
├─ binance_client.py         # API 客戶端
├─ risk_manager.py           # 風險控制
├─ trade_logger.py           # 交易記錄
└─ discord_bot.py            # Discord 集成
```

## 💬 Discord 指令

- `/status` - Bot 運行狀態
- `/balance` - 帳戶餘額
- `/positions` - 當前倉位
- `/stats` - 交易統計

## 📈 交易策略

### ICT/SMC 多時間框架

- **1小時**：EMA200 趨勢過濾
- **15分鐘**：趨勢定義
- **1分鐘**：精準入場

### 信號組件

- Order Blocks（訂單塊）
- Liquidity Zones（流動性區域）
- Market Structure Breaks（市場結構突破）
- MACD + EMA 確認

### 信心度評分

- 市場結構：40%
- MACD 確認：20%
- EMA 確認：20%
- 價格位置：10%
- 流動性區域：10%

最低門檻：70%

## 🔒 安全特性

- ✅ 交易所級止損/止盈（Mark Price 觸發）
- ✅ 自動倉位保護（啟動時加載現有倉位）
- ✅ API 限流保護
- ✅ 故障容錯機制
- ✅ 模擬模式支持

## 📝 文檔

- 查看 `archive/old_docs/` 了解詳細文檔
- 系統架構請參考 `archive/old_docs/ARCHITECTURE_V3.md`
- 部署指南請參考 `archive/old_docs/RAILWAY_DEPLOYMENT_GUIDE.md`

## 📦 部署

系統已配置 Railway 自動部署：

1. 推送到 GitHub main 分支
2. GitHub Actions 自動觸發部署
3. 查看 Railway Dashboard 確認狀態

## ⚠️ 免責聲明

此軟件僅供教育和研究目的。加密貨幣交易存在高風險，可能導致資金損失。使用本軟件進行實盤交易的風險由您自行承擔。

## 📄 授權

MIT License

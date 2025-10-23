# 加密貨幣自動交易機器人

基於 ICT/SMC 策略和 LSTM 深度學習的自動化虛擬貨幣交易系統。

## ✨ 核心功能

- 🔄 **實時市場監控** - Binance API 實時數據（K線、資金費率、多空比）
- 📊 **技術分析** - MACD、布林帶、EMA、ATR、RSI 等指標
- 🎯 **ICT/SMC 策略** - 訂單塊、流動性區域、市場結構分析
- 🤖 **LSTM 價格預測** - 深度學習神經網絡預測價格走勢
- ⚖️ **風險管理** - 自動倉位計算、基於 ATR 的動態止損止盈
- 💬 **Discord 通知** - 實時交易提醒和績效報告
- 📝 **交易日誌** - 完整的交易記錄和績效統計

## 🚀 快速開始

### 1. 設定環境變數

在 Replit Secrets 或 `.env` 文件中設定：

```bash
BINANCE_API_KEY=你的_Binance_API_金鑰
BINANCE_SECRET_KEY=你的_Binance_私鑰
BINANCE_TESTNET=true  # 測試環境

DISCORD_BOT_TOKEN=你的_Discord_Bot_Token  # 選填
DISCORD_CHANNEL_ID=你的_頻道_ID  # 選填

ENABLE_TRADING=false  # false=模擬模式，true=實盤交易
```

### 2. 本地測試（Replit）

直接運行：
```bash
python main.py
```

機器人會每 60 秒分析市場並執行交易策略。

### 3. 部署到 Railway（推薦）

Railway 新加坡節點可以避免 Binance 地區限制。

#### 方式 A：手動部署
1. 前往 [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. 選擇部署區域：**Singapore**
4. 添加環境變數（同上）

#### 方式 B：GitHub Actions 自動部署（已配置✅）
1. 獲取 Railway Token：Railway → Account Settings → Tokens
2. 添加到 GitHub Secrets：`RAILWAY_TOKEN`
3. 推送代碼到 `main` 分支自動部署

**往後所有更新都會自動部署！** 🚀

詳細步驟請參考：
- **[GITHUB_AUTO_DEPLOY_SETUP.md](GITHUB_AUTO_DEPLOY_SETUP.md)** - GitHub 自動部署完整指南
- **[DEPLOY_NOW.md](DEPLOY_NOW.md)** - 手動部署指南

## ⚙️ 配置參數

在 `config.py` 中調整：

```python
RISK_PER_TRADE_PERCENT = 1.0      # 每筆交易風險 1%
MAX_POSITION_SIZE_PERCENT = 1.5   # 最大倉位 1.5%
DEFAULT_LEVERAGE = 1.0            # 槓桿倍數
STOP_LOSS_ATR_MULTIPLIER = 2.0    # 止損距離（ATR 倍數）
TAKE_PROFIT_ATR_MULTIPLIER = 3.0  # 止盈距離（ATR 倍數）
```

## 📊 交易策略

### ICT/SMC 策略
- 識別訂單塊（機構入場區域）
- 檢測流動性區域（支撐/阻力）
- 分析市場結構（多頭/空頭趨勢）
- MACD 和 EMA 確認信號

### LSTM 模型
- 使用 500 根 K 線歷史數據訓練
- 特徵：收盤價、成交量、MACD、RSI、ATR
- 每小時重新訓練以適應市場變化
- 預測結果用於確認交易信號

## 🛡️ 安全建議

- ✅ 先用 **Testnet** 測試（BINANCE_TESTNET=true）
- ✅ 先用**模擬模式**（ENABLE_TRADING=false）
- ✅ API Key **停用提現權限**
- ✅ 設定 IP 白名單（Railway 會提供固定 IP）
- ✅ 小額資金測試後再擴大
- ⚠️ 定期檢查交易日誌和績效

## 📁 專案結構

```
.
├── main.py                 # 主程式入口
├── config.py              # 配置管理
├── binance_client.py      # Binance API 客戶端
├── discord_bot.py         # Discord 通知系統
├── risk_manager.py        # 風險管理
├── trade_logger.py        # 交易日誌
├── utils/                 # 工具函數
│   ├── indicators.py      # 技術指標
│   └── helpers.py         # 輔助函數
├── strategies/            # 交易策略
│   ├── ict_smc.py        # ICT/SMC 策略
│   └── arbitrage.py      # 套利策略
├── models/                # 機器學習模型
│   └── lstm_model.py     # LSTM 預測模型
├── railway.json           # Railway 配置
├── requirements.txt       # Python 依賴
└── .github/workflows/     # GitHub Actions CI/CD
    └── deploy.yml
```

## 📈 監控與日誌

- **交易記錄**：`trades.json` - 所有交易的完整記錄
- **系統日誌**：`trading_bot.log` - 運行日誌和錯誤信息
- **Discord 通知**：實時交易提醒、警報（回撤 >5%）、每日報告
- **Railway 儀表板**：實時監控部署狀態和日誌

## 🔮 下一階段功能

- xAI Grok 4 整合（自動模型迭代）
- 多模型比較（LSTM、ARIMA、XGBoost、Transformer）
- 高級套利策略（三角套利）
- X 平台情緒分析
- VaR 風險模型
- PostgreSQL 資料庫
- Redis 快取
- 互動式 Discord 指令

## 📝 更多資訊

- **部署指南**：[README_DEPLOYMENT.md](README_DEPLOYMENT.md)
- **專案文檔**：[replit.md](replit.md)
- **GitHub Actions 設定**：[.github/workflows/README.md](.github/workflows/README.md)

## ⚠️ 免責聲明

此交易機器人僅供教育和研究目的。加密貨幣交易具有高風險，可能導致資金損失。使用者需自行承擔所有風險，作者不對任何交易損失負責。

## 📧 支援

遇到問題請檢查：
1. `trading_bot.log` 日誌文件
2. `trades.json` 交易記錄
3. Discord 通知信息
4. API 金鑰和權限設定

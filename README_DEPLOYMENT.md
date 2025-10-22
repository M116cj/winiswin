# Railway 部署指南

## 部署步驟

### 1. 準備 Railway 專案

1. 前往 [Railway.app](https://railway.app)
2. 使用 GitHub 帳號登入
3. 點擊 "New Project" → "Deploy from GitHub repo"
4. 選擇這個專案的 repository

### 2. 設定環境變數

在 Railway 專案中，前往 "Variables" 頁面，添加以下環境變數：

**必填項目**：
- `BINANCE_API_KEY` - 您的 Binance API 金鑰
- `BINANCE_SECRET_KEY` - 您的 Binance 私鑰
- `BINANCE_TESTNET` - 設為 `false`（使用正式環境）或 `true`（使用測試網）

**Discord 通知**（選填）：
- `DISCORD_BOT_TOKEN` - Discord Bot Token
- `DISCORD_CHANNEL_ID` - Discord 頻道 ID

**交易設定**：
- `ENABLE_TRADING` - 設為 `true` 啟用真實交易，`false` 為模擬模式
- `MAX_POSITION_SIZE_PERCENT` - 最大倉位百分比（預設：1.5）
- `RISK_PER_TRADE_PERCENT` - 每筆交易風險百分比（預設：1.0）
- `DEFAULT_LEVERAGE` - 預設槓桿倍數（預設：1.0）

### 3. 選擇部署區域

1. 在 Railway 設定中，選擇 **Singapore** 作為部署區域
2. 這樣可以確保 IP 位址在 Binance 支援的地區

### 4. 部署

1. Railway 會自動檢測到 `nixpacks.toml` 和 `requirements.txt`
2. 自動安裝所有依賴
3. 執行 `python main.py` 啟動機器人

### 5. 監控日誌

在 Railway 的 "Deployments" → "Logs" 中可以查看：
- 機器人啟動狀態
- 市場分析日誌
- 交易執行記錄
- 錯誤訊息

## 從 Replit 遷移到 Railway

如果您目前在 Replit 測試，要遷移到 Railway：

1. 將代碼推送到 GitHub repository
2. 在 Railway 連接該 repository
3. 複製所有環境變數到 Railway
4. 將 `BINANCE_TESTNET` 改為 `false`（如果要使用正式環境）
5. 部署並監控日誌

## 安全建議

- ✅ 使用新加坡節點可以正常訪問 Binance
- ✅ 環境變數在 Railway 中加密儲存
- ✅ API Key 請設定 IP 白名單（Railway 會提供固定 IP）
- ✅ 確保 API Key **已停用提現權限**
- ⚠️ 建議先用小額資金測試
- ⚠️ 定期檢查交易日誌和績效

## 檢查部署狀態

機器人啟動後，會在日誌中顯示：
```
INFO - Initializing Trading Bot...
INFO - Initialized Binance client in LIVE mode
INFO - Trading Bot initialized successfully
INFO - Trading Bot started
```

如果看到這些訊息，表示機器人已成功啟動並開始監控市場。

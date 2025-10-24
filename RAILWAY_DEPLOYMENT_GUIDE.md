# 🚀 Railway 部署指南

## 📋 必需的環境變數

在 Railway 項目設置中添加以下環境變數：

### 1️⃣ **Binance API 憑證**
```
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
```

### 2️⃣ **Discord Bot 憑證**
```
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
```

### 3️⃣ **交易設置**
```
ENABLE_TRADING=true        # ⚠️ 設為 true 啟用實盤交易
SYMBOL_MODE=all            # 監控所有 648 個 USDT 合約
TIMEFRAME=1m               # 1分鐘 K 線
```

### 4️⃣ **可選設置**
```
CYCLE_INTERVAL=60          # 交易週期間隔（秒）
MAX_POSITIONS=3            # 最大同時持倉數
LOG_LEVEL=INFO             # 日誌級別
```

## 🔄 部署步驟

### 方式 1：自動部署（推薦）

代碼會自動同步到 GitHub，然後 GitHub Actions 會自動部署到 Railway。

**查看部署狀態：**
1. 訪問 [GitHub Actions](https://github.com/your-repo/actions)
2. 查看最新的 "Deploy to Railway" 工作流

### 方式 2：手動部署

如果需要手動部署：

```bash
# 1. 安裝 Railway CLI
npm install -g @railway/cli

# 2. 登入 Railway
railway login

# 3. 鏈接項目
railway link

# 4. 部署
railway up
```

## ✅ 部署後驗證

部署成功後，Bot 會自動：

1. ✅ 連接 Binance API（讀取實際餘額）
2. ✅ 加載現有倉位
3. ✅ **為現有倉位設置止盈止損保護**
4. ✅ 開始監控 648 個 USDT 合約
5. ✅ 發送 Discord 通知

**查看日誌：**
```bash
railway logs
```

或在 Railway Dashboard: https://railway.app

## 🛡️ 止盈止損自動保護

Bot 啟動時會：
- 從 Binance API 讀取所有現有倉位
- 為每個倉位計算止損/止盈價格
- 在 Binance 交易所設置 STOP_MARKET 和 TAKE_PROFIT_MARKET 訂單

**日誌示例：**
```
✅ Loaded BTCUSDT BUY position: qty=0.001, entry=67245.50
🔒 Setting exchange-level protection for BTCUSDT LONG: SL @ 65890.00, TP @ 69320.00
✅ Stop-loss order set: orderId=123456
✅ Take-profit order set: orderId=123457
🛡️ Position fully protected
```

## 📊 監控運行狀態

### Discord 指令
- `/status` - 查看 Bot 運行狀態
- `/balance` - 查看帳戶餘額
- `/positions` - 查看當前倉位
- `/stats` - 查看交易統計

### 預期行為

**帳戶餘額：**
- Bot 會自動從 Binance 讀取實際 USDT 餘額
- 每個交易週期更新一次
- 只有變化 > 1% 時才記錄日誌

**倉位管理：**
- 最多同時持有 3 個倉位
- 每個倉位自動設置止盈止損
- 動態監控並調整保護

## ⚠️ 重要提醒

1. **首次部署：** 確認所有環境變數正確設置
2. **實盤交易：** `ENABLE_TRADING=true` 才會實際下單
3. **API 權限：** 確保 Binance API Key 有期貨交易權限（但**不要**開啟提現權限）
4. **止盈止損：** Bot 會自動為所有倉位設置交易所級別保護

## 🆘 故障排除

### Bot 沒有讀取到倉位
- 檢查 Binance API Key 是否有效
- 確認 API Key 有期貨帳戶讀取權限
- 查看日誌是否有 API 錯誤

### 止盈止損沒有設置
- 確認 `ENABLE_TRADING=true`
- 查看日誌中的 "Setting exchange-level protection" 信息
- 檢查 Binance 交易所的委託訂單列表

### 無法連接 Discord
- 驗證 `DISCORD_BOT_TOKEN` 是否正確
- 確認 `DISCORD_CHANNEL_ID` 是否正確
- Bot 需要有該頻道的發送訊息權限

---

**部署完成後，您的所有現有倉位將自動受到止盈止損保護！** 🛡️

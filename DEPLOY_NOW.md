# 🚀 立即部署 - Railway 上線指南

**目標**：5-10 分鐘內讓交易機器人上線運行

---

## ✅ 部署前檢查

### 必需文件清單（已確認）

- ✅ `main.py` - 主程式
- ✅ `config.py` - 配置管理
- ✅ `binance_client.py` - Binance API 客戶端
- ✅ `discord_bot.py` - Discord 通知
- ✅ `risk_manager.py` - 風險管理
- ✅ `trade_logger.py` - 交易日誌
- ✅ `requirements.txt` - Python 依賴
- ✅ `nixpacks.toml` - 部署配置（含 TA-Lib）
- ✅ `railway.json` - Railway 配置
- ✅ `Procfile` - 啟動命令
- ✅ `strategies/` - 交易策略
- ✅ `models/` - LSTM 模型
- ✅ `utils/` - 工具函數

**狀態**：🟢 所有文件就緒

---

## 🎯 部署步驟（3 步驟）

### 步驟 1️⃣：創建 Railway 專案（2 分鐘）

1. 打開瀏覽器，前往 **https://railway.app**
2. 使用 GitHub 帳號登入
3. 點擊右上角 **"New Project"** 按鈕
4. 選擇 **"Empty Project"**
5. 專案會自動創建

---

### 步驟 2️⃣：上傳代碼（2 分鐘）

**方式 A：從 GitHub（推薦）**

如果您的代碼已在 GitHub：
1. 在專案中點擊 **"New"**
2. 選擇 **"GitHub Repo"**
3. 授權 Railway 訪問 GitHub
4. 選擇您的倉庫
5. Railway 自動開始構建

**方式 B：本地上傳**

如果沒有 GitHub：
1. 下載 Replit 專案所有文件為 ZIP
2. 在 Railway 專案中點擊 **"New"**
3. 選擇 **"Empty Service"**
4. 在 Settings → Source 上傳代碼

**方式 C：使用 Railway CLI**（進階）

在您的本機電腦：
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

---

### 步驟 3️⃣：配置環境變數（3 分鐘）

在 Railway Dashboard → 點擊專案 → **Variables** 標籤

**複製以下變數並填入您的值**：

```bash
# === Binance API 配置 ===
BINANCE_API_KEY=你的Binance_API金鑰
BINANCE_SECRET_KEY=你的Binance私鑰
BINANCE_TESTNET=false
ENABLE_TRADING=true

# === Discord 通知 ===
DISCORD_BOT_TOKEN=你的Discord_Bot_Token
DISCORD_CHANNEL_ID=你的Discord頻道ID

# === 交易對配置（推薦：AUTO 模式）===
SYMBOL_MODE=auto
MAX_SYMBOLS=50

# === 風險管理參數 ===
RISK_PER_TRADE_PERCENT=0.5
MAX_POSITION_SIZE_PERCENT=1.0
DEFAULT_LEVERAGE=1.0

# === 高級配置（可選）===
TIMEFRAME=1h
MODEL_RETRAIN_INTERVAL=3600
```

**如何獲取這些值**：

**Binance API**：
- 前往 Binance.com → 帳戶 → API 管理
- 創建 API 金鑰（啟用交易，**停用提現**）
- 複製 API Key 和 Secret Key

**Discord Bot**：
- 前往 Discord Developer Portal
- 創建應用程式 → Bot
- 複製 Token
- 在 Discord 中右鍵點擊頻道 → 複製 ID

---

### 步驟 4️⃣：設置部署區域（30 秒）⚠️ 重要

1. 在專案中點擊 **Settings**
2. 找到 **Region** 選項
3. 選擇：**ap-southeast-1 (Singapore)** 🇸🇬
4. 保存

**為什麼必須選 Singapore**：
- Binance 封鎖其他地區的 IP
- 只有亞洲節點可正常連接 Binance API

---

### 步驟 5️⃣：升級 Railway 方案（1 分鐘）

**推薦方案**：Railway Pro ($20/月)

1. 點擊右上角 → **Upgrade**
2. 選擇 **Pro Plan**
3. 輸入支付信息

**為什麼需要 Pro**：
- 50 個交易對需要 4-6GB 記憶體
- Hobby 方案只有 512MB（不夠）
- Pro 提供 8GB RAM

**如果只想測試（5 個交易對）**：
```bash
SYMBOL_MODE=static  # 使用靜態模式
```
可以使用 Hobby 方案（$5/月）

---

## 📊 驗證部署

### 查看構建日誌

Railway → **Deployments** → 點擊最新部署

期待看到：
```log
✅ Building...
✅ Installing Python 3.11
✅ Installing TA-Lib
✅ Installing dependencies
✅ Build successful
✅ Deployment live
```

### 查看運行日誌

Railway → **Logs** 標籤

期待看到：
```log
INFO - Initializing Trading Bot...
INFO - Mode: AUTO - Fetching top 50 pairs by volume...
INFO - Found 648 USDT perpetual pairs
INFO - Selected top 50 pairs by 24h volume
INFO -   1. BTCUSDT: $45,123,456,789 (24h volume)
INFO -   2. ETHUSDT: $23,456,789,012 (24h volume)
...
INFO - Loaded 50 trading pairs
INFO - Binance client initialized (LIVE MODE)
INFO - Current balance: $XXX.XX USDT
INFO - Training LSTM model for BTCUSDT...
INFO - Model training completed for BTCUSDT
INFO - Training LSTM model for ETHUSDT...
...
INFO - Trading Bot started
INFO - Starting market monitoring (LIVE TRADING ENABLED)
INFO - Analyzing BTCUSDT...
```

### 確認 Discord 通知

您的 Discord 頻道應該收到：
```
🤖 交易機器人已啟動
📊 交易對：50 個（AUTO 模式）
💰 賬戶餘額：$XXX.XX USDT
⚙️ 風險設定：0.5% per trade
🌏 部署區域：Singapore
🚀 狀態：實盤交易已啟用
```

---

## 🚨 常見問題排除

### 問題 1：構建失敗 - TA-Lib 錯誤

**錯誤**：`Could not find ta-lib`

**解決**：
- 檢查 `nixpacks.toml` 是否存在
- 確認包含 `ta-lib` 在 `nixPkgs` 列表中
- ✅ 已預先修復

### 問題 2：運行時錯誤 - API 連接失敗

**錯誤**：`APIError: Unauthorized`

**檢查**：
1. 部署區域是否為 **Singapore**
2. Binance API 金鑰是否正確
3. API 權限是否包含「交易」
4. 提現權限是否已**停用**

### 問題 3：容器重啟 - 記憶體不足

**錯誤**：`Container killed (OOMKilled)`

**解決**：
```bash
# 方案 A：減少交易對
MAX_SYMBOLS=20

# 方案 B：切換到靜態模式
SYMBOL_MODE=static

# 方案 C：升級到 Railway Pro
```

### 問題 4：沒有 Discord 通知

**檢查**：
1. `DISCORD_BOT_TOKEN` 是否正確
2. `DISCORD_CHANNEL_ID` 是否正確
3. Bot 是否已加入伺服器
4. Bot 是否有發送訊息權限

---

## ⏱️ 時間線

| 時間 | 階段 | 預期 |
|------|------|------|
| 0-2 分鐘 | 創建專案 | 專案已創建 |
| 2-4 分鐘 | 上傳代碼 | 代碼已上傳 |
| 4-7 分鐘 | 設置變數 | 環境變數已配置 |
| 7-12 分鐘 | 構建部署 | Railway 自動構建 |
| 12-15 分鐘 | 模型訓練 | LSTM 模型訓練中 |
| 15 分鐘+ | 正式運行 | 機器人開始監控市場 |

**總時間**：約 **15-20 分鐘**（包含模型訓練）

---

## 🎯 第一個小時監控

部署成功後，請密切監控：

### 0-15 分鐘
- [ ] Railway 構建成功
- [ ] 機器人啟動無錯誤
- [ ] Discord 收到啟動通知
- [ ] Binance API 連接成功

### 15-30 分鐘
- [ ] 所有 50 個交易對模型訓練完成
- [ ] 市場監控循環開始
- [ ] 無記憶體或 CPU 警告

### 30-60 分鐘
- [ ] 如有交易信號，檢查邏輯是否正確
- [ ] 如有交易執行，確認倉位大小合理
- [ ] Discord 通知正常發送

---

## 🛡️ 安全檢查

部署前最後確認：

- [ ] Binance API **已停用提現權限**
- [ ] 測試資金在可承受範圍（$100-1000）
- [ ] 理解可能損失全部資金
- [ ] Railway 部署區域為 **Singapore**
- [ ] Discord 通知已測試
- [ ] 已閱讀所有風險提醒

---

## 🎉 部署成功！

如果看到以下內容，恭喜部署成功：

✅ Railway 日誌顯示 "Trading Bot started"  
✅ Discord 收到啟動通知  
✅ 沒有錯誤訊息  
✅ 市場監控循環運行  

**您的交易機器人現在已上線！** 🚀

---

## 📱 持續監控

### 每日檢查
- Railway 日誌（是否有錯誤）
- Discord 通知（交易和警報）
- Binance 帳戶（餘額和倉位）

### 每週檢查
- 交易績效統計
- 勝率和盈虧比
- 最大回撤
- API 使用情況

### 緊急停止
如需緊急停止交易：
```bash
# 在 Railway Variables 設置
ENABLE_TRADING=false
```

---

## 🆘 需要幫助？

**Railway 構建問題**：
- 查看 Deployments → Build Logs
- 搜索錯誤訊息

**運行時問題**：
- 查看 Logs 標籤
- 檢查環境變數

**策略問題**：
- 閱讀 `SYSTEM_STATUS_REPORT.md`
- 理解 ICT/SMC 和 LSTM 邏輯

---

**準備好了嗎？開始部署！** 🎯

立即前往：**https://railway.app**

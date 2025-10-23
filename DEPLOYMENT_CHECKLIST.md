# ✅ Railway 部署檢查清單

使用此清單確保每個步驟都正確完成。

---

## 📋 部署前準備

- [ ] 已註冊 Railway 帳號（https://railway.app）
- [ ] 已準備 Binance API 金鑰（交易權限，**停用提現**）
- [ ] 已準備 Discord Bot Token 和 Channel ID
- [ ] 已準備信用卡（Railway Pro 方案）
- [ ] 理解交易風險，可承受全部損失

---

## 🚀 Railway 部署步驟

### 步驟 1：創建專案
- [ ] 登入 Railway.app
- [ ] 點擊 "New Project"
- [ ] 選擇 "Empty Project"
- [ ] 專案已創建

### 步驟 2：上傳代碼
- [ ] 選擇上傳方式（GitHub / 本地上傳 / CLI）
- [ ] 代碼已上傳到 Railway
- [ ] Railway 開始自動構建

### 步驟 3：設置環境變數
複製 `ENVIRONMENT_VARIABLES.txt` 中的變數，逐一添加：

#### 必需變數
- [ ] BINANCE_API_KEY
- [ ] BINANCE_SECRET_KEY
- [ ] BINANCE_TESTNET=false
- [ ] ENABLE_TRADING=true
- [ ] DISCORD_BOT_TOKEN
- [ ] DISCORD_CHANNEL_ID

#### 交易對配置
- [ ] SYMBOL_MODE（選擇：static / auto / all）
- [ ] MAX_SYMBOLS（如使用 auto 模式）

#### 風險參數
- [ ] RISK_PER_TRADE_PERCENT
- [ ] MAX_POSITION_SIZE_PERCENT
- [ ] DEFAULT_LEVERAGE

### 步驟 4：設置部署區域 ⚠️ 重要
- [ ] 點擊 Settings
- [ ] 找到 Region
- [ ] 選擇：**ap-southeast-1 (Singapore)**
- [ ] 保存設置

### 步驟 5：升級方案（如使用 AUTO 或 ALL 模式）
- [ ] 點擊 Upgrade
- [ ] 選擇 Pro Plan ($20/月)
- [ ] 完成支付

---

## ✅ 部署驗證

### 構建檢查
- [ ] Railway Deployments 顯示 "Building..."
- [ ] 構建日誌無錯誤
- [ ] 顯示 "Installing TA-Lib" ✅
- [ ] 顯示 "Build successful" ✅
- [ ] 顯示 "Deployment live" ✅

### 運行檢查
- [ ] Railway Logs 顯示 "Initializing Trading Bot..."
- [ ] 顯示 "Mode: AUTO - Fetching top 50 pairs..."
- [ ] 顯示 "Found 648 USDT perpetual pairs"
- [ ] 顯示 "Loaded XX trading pairs"
- [ ] 顯示 "Binance client initialized (LIVE MODE)"
- [ ] 顯示 "Current balance: $XXX.XX USDT"
- [ ] 顯示 "Training LSTM model for..."
- [ ] 顯示 "Trading Bot started"
- [ ] 顯示 "Starting market monitoring"

### Discord 通知檢查
- [ ] Discord 頻道收到啟動通知
- [ ] 通知包含正確的交易對數量
- [ ] 通知顯示正確的賬戶餘額
- [ ] 通知顯示正確的風險設定

---

## 🔍 第一小時監控

### 0-15 分鐘
- [ ] 無錯誤日誌
- [ ] Binance API 連接成功
- [ ] Discord 通知正常
- [ ] 記憶體使用正常（< 80%）

### 15-30 分鐘
- [ ] LSTM 模型訓練完成
- [ ] 市場監控循環開始
- [ ] 無 API 速率限制警告

### 30-60 分鐘
- [ ] 系統穩定運行
- [ ] 如有信號，邏輯正確
- [ ] 如有交易，倉位合理

---

## 🚨 常見問題檢查

### 如果構建失敗
- [ ] 檢查 nixpacks.toml 是否存在
- [ ] 檢查 requirements.txt 是否完整
- [ ] 查看 Build Logs 具體錯誤

### 如果 API 連接失敗
- [ ] 確認部署區域為 Singapore
- [ ] 確認 API 金鑰正確
- [ ] 確認 API 權限包含「交易」
- [ ] 確認提現權限已停用

### 如果記憶體不足
- [ ] 檢查 SYMBOL_MODE 設置
- [ ] 考慮減少 MAX_SYMBOLS
- [ ] 考慮升級到更高方案

### 如果沒有 Discord 通知
- [ ] 檢查 DISCORD_BOT_TOKEN
- [ ] 檢查 DISCORD_CHANNEL_ID
- [ ] 確認 Bot 已加入伺服器
- [ ] 確認 Bot 有發送權限

---

## ✅ 部署成功標誌

全部打勾即為成功部署：

- [ ] Railway 構建成功
- [ ] 機器人啟動無錯誤
- [ ] Binance API 連接正常
- [ ] Discord 通知正常
- [ ] 市場監控正常運行
- [ ] 無記憶體或資源警告
- [ ] 第一個小時無異常

---

## 🎉 恭喜！

如果所有項目都已勾選，您的交易機器人已成功上線！

**接下來**：
- 持續監控第一天
- 記錄所有交易
- 分析績效數據
- 根據結果調整參數

**祝交易順利！** 🚀

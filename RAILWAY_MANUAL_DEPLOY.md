# 🚀 Railway 手動部署指南（最簡化版本）

由於無法使用 CLI 直接部署，請按照以下步驟在 Railway 網站上手動部署。

---

## ⚡ 快速部署 - 5 分鐘完成

### 步驟 1: 推送到 GitHub（1 分鐘）

在 **Replit Shell** 執行：

```bash
# 運行自動部署腳本
./deploy_to_railway.sh
```

或手動執行：

```bash
git add .
git commit -m "Production deployment"
```

### 步驟 2: 在 Railway 創建專案（2 分鐘）

1. 打開 **[railway.app](https://railway.app)** 並登入
2. 點擊 **"New Project"**
3. 選擇 **"Empty Project"**
4. 專案名稱：`crypto-trading-bot`

### 步驟 3: 上傳代碼（1 分鐘）

#### 方式 A：從 GitHub 部署（推薦）

1. 在專案中點擊 **"New"** → **"GitHub Repo"**
2. 授權 Railway 訪問 GitHub
3. 選擇您的倉庫
4. Railway 會自動開始構建

#### 方式 B：直接上傳（如果沒有 GitHub）

1. 下載專案所有文件為 ZIP
2. 在 Railway 專案中點擊 **"New"** → **"Empty Service"**
3. 在 Settings 中連接代碼倉庫

### 步驟 4: 設置部署區域（30 秒）

⚠️ **非常重要**

1. 點擊專案 → **Settings**
2. 找到 **"Region"**
3. 選擇：**ap-southeast-1 (Singapore)** 🇸🇬
4. 保存

### 步驟 5: 添加環境變數（1 分鐘）

點擊 **Variables** 標籤，逐一添加：

```bash
BINANCE_API_KEY
```
**值**: [從 Replit Secrets 中複製 BINANCE_API_KEY]

```bash
BINANCE_SECRET_KEY
```
**值**: [從 Replit Secrets 中複製 BINANCE_SECRET_KEY]

```bash
BINANCE_TESTNET
```
**值**: `false`

```bash
ENABLE_TRADING
```
**值**: `true`

```bash
DISCORD_BOT_TOKEN
```
**值**: [從 Replit Secrets 中複製]

```bash
DISCORD_CHANNEL_ID
```
**值**: [從 Replit Secrets 中複製]

---

## ✅ 完成！

設置完環境變數後，Railway 會自動：
1. 檢測 `nixpacks.toml` 配置
2. 安裝 Python 3.11 + TA-Lib
3. 安裝所有依賴 (`requirements.txt`)
4. 運行 `python main.py`

---

## 📊 驗證部署

### 查看構建日誌

Railway → **Deployments** → 點擊最新部署

期待看到：
```
✅ Building...
✅ Installing Python 3.11
✅ Installing TA-Lib
✅ Installing dependencies
✅ Build successful
```

### 查看運行日誌

Railway → **Logs**

期待看到：
```
INFO - Initializing Trading Bot...
INFO - Binance client initialized (LIVE MODE)
INFO - Current balance: $XX.XX USDT
INFO - Training LSTM model for BTCUSDT...
INFO - Model training completed
INFO - Starting market monitoring (LIVE TRADING ENABLED)
```

### Discord 通知

應該收到：
```
🤖 交易機器人已啟動
💰 賬戶餘額：$XX.XX USDT
⚙️ 風險設定：0.3% per trade
📊 模式：實盤交易
```

---

## 🚨 如果部署失敗

### 錯誤 1: TA-Lib 安裝失敗

**檢查**: `nixpacks.toml` 是否包含 `ta-lib`
```toml
nixPkgs = ["python311", "gcc", "ta-lib"]
```

### 錯誤 2: Binance 地區限制

**檢查**: 部署區域是否為 **Singapore**

### 錯誤 3: API 權限錯誤

**檢查**: 
- Binance API 金鑰是否正確
- 是否有交易權限
- 提現權限是否已停用

---

## 📱 監控運行

### 第一個小時

**每 15 分鐘檢查**：
- Railway Logs
- Discord 通知
- Binance 賬戶

### 緊急停止

在 Railway Variables 設置：
```
ENABLE_TRADING = false
```

---

## 🎉 部署完成！

您的交易機器人現在：
- ✅ 在 Railway 新加坡節點運行
- ✅ 使用真實 Binance API
- ✅ 風險極度保守（0.3% per trade）
- ✅ Discord 實時監控
- ✅ 自動執行 ICT/SMC + LSTM 策略

**開始您的交易之旅！** 🚀

記住：
- 📊 密切監控第一天
- 🛡️ 遵守風險管理
- 📝 記錄每筆交易
- ⚠️ 理性決策

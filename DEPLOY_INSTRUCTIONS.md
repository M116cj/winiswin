# 🚀 部署指令 - Railway 自動部署

## ✅ 系統狀態確認

- ✅ 所有代碼已完成並通過 Grok 4 檢查
- ✅ TA-Lib 依賴已修復
- ✅ NaN 數據驗證已實施
- ✅ Railway 配置已完成
- ✅ 所有 API 密鑰已儲存

---

## 📦 方式 A：GitHub Actions 自動部署（推薦）

### 步驟 1: 初始化 Git 倉庫

在 Replit Shell 執行：

```bash
# 初始化 Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Trading bot with ICT/SMC and LSTM"
```

### 步驟 2: 連接到 GitHub

```bash
# 替換成您的 GitHub 倉庫 URL
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 步驟 3: 設置 GitHub Secrets

1. 前往 GitHub Repository → Settings → Secrets and variables → Actions
2. 點擊 "New repository secret"
3. 添加以下 secrets：

**必需的 Secrets：**
```
名稱: RAILWAY_TOKEN
值: [從 Replit Secrets 中複製 RAILWAY_TOKEN 的值]

名稱: BINANCE_API_KEY
值: [從 Replit Secrets 中複製]

名稱: BINANCE_SECRET_KEY
值: [從 Replit Secrets 中複製]
```

**可選的 Secrets（如果使用 Discord）：**
```
名稱: DISCORD_BOT_TOKEN
值: [從 Replit Secrets 中複製]

名稱: DISCORD_CHANNEL_ID
值: [從 Replit Secrets 中複製]
```

### 步驟 4: 觸發自動部署

推送代碼後，GitHub Actions 會自動：
1. 運行工作流程 (.github/workflows/deploy.yml)
2. 使用 RAILWAY_TOKEN 部署到 Railway
3. 設置所有環境變數
4. 部署到新加坡節點

查看部署狀態：
- GitHub → Actions 標籤
- Railway → Dashboard

---

## 📦 方式 B：Railway 手動部署

### 步驟 1: 創建 Railway 專案

1. 前往 [railway.app](https://railway.app)
2. 點擊 "New Project"
3. 選擇 "Deploy from GitHub repo"
4. 授權並選擇您的倉庫

### 步驟 2: 設置部署區域

⚠️ **重要**：必須選擇 **Singapore** 區域以避免 Binance 地區限制

1. 在專案設置中找到 "Region"
2. 選擇：**ap-southeast-1 (Singapore)**

### 步驟 3: 添加環境變數

在 Railway Dashboard → Variables，添加：

```bash
BINANCE_API_KEY=你的API金鑰
BINANCE_SECRET_KEY=你的私鑰
BINANCE_TESTNET=true
ENABLE_TRADING=false

# 可選：Discord 通知
DISCORD_BOT_TOKEN=你的Token
DISCORD_CHANNEL_ID=你的頻道ID
```

### 步驟 4: 部署

Railway 會自動：
1. 檢測 nixpacks.toml 配置
2. 安裝 TA-Lib 系統依賴
3. 安裝 Python 依賴
4. 運行 `python main.py`

---

## 🔍 驗證部署

### 檢查 Railway 日誌

```
Railway Dashboard → Deployments → 查看日誌
```

**成功標誌：**
```
✅ Binance client initialized successfully
✅ Training LSTM model for BTCUSDT...
✅ Model training completed
✅ Starting market monitoring...
```

**失敗標誌：**
```
❌ Service unavailable from a restricted location
   → 檢查部署區域是否為 Singapore

❌ Invalid API-key, IP, or permissions
   → 檢查 Binance API 金鑰是否正確

❌ No module named 'talib'
   → TA-Lib 安裝失敗（應該已修復）
```

### 檢查 Discord 通知

如果設置了 Discord，您應該會收到：
- 🤖 機器人啟動通知
- 📊 模型訓練完成通知
- 📈 市場監控開始通知

---

## ⚙️ 部署後設置

### 1. 測試模式運行（建議）

先在測試環境確認運作正常：
```bash
BINANCE_TESTNET=true
ENABLE_TRADING=false
```

### 2. 切換到實盤

確認測試無誤後：
```bash
BINANCE_TESTNET=false  # 使用真實 Binance
ENABLE_TRADING=true    # 啟用實際交易
```

⚠️ **警告**：實盤交易前請：
- ✅ 確認 API 金鑰已停用提現權限
- ✅ 先用小額資金測試
- ✅ 設置 IP 白名單
- ✅ 仔細檢查交易參數

---

## 📊 監控運行狀態

### Railway Dashboard
```
https://railway.app/dashboard
→ 查看實時日誌
→ 監控資源使用
→ 檢查部署狀態
```

### 本地查看交易記錄

從 Railway 下載檔案：
```bash
# trades.json - 所有交易記錄
# trading_bot.log - 系統日誌
```

### Discord 監控（推薦）

設置 Discord 通知後，您會收到：
- 每筆交易的實時提醒
- 回撤警報（>5%）
- 每日績效報告

---

## 🆘 常見問題排除

### 問題 1: TA-Lib 安裝失敗
```
解決：已在 nixpacks.toml 添加 ta-lib 依賴
```

### 問題 2: Binance 地區限制
```
解決：確認 Railway 部署區域為 Singapore
```

### 問題 3: API 權限錯誤
```
檢查：
- Binance API 金鑰是否有交易權限
- IP 白名單設置
- 金鑰是否過期
```

### 問題 4: LSTM 訓練失敗
```
解決：已實施 NaN 數據驗證，自動跳過無效數據
```

---

## 📞 下一步

部署完成後：
1. 監控 Railway 日誌 24 小時
2. 檢查 Discord 通知是否正常
3. 驗證交易邏輯（模擬模式）
4. 小額資金實盤測試
5. 逐步擴大交易規模

---

## 🎉 準備就緒！

您的交易機器人已經：
- ✅ 代碼完整且經過驗證
- ✅ 部署配置正確
- ✅ 安全性檢查通過
- ✅ 所有依賴已解決

立即開始部署！🚀

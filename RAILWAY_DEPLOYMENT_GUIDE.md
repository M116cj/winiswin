# 🚀 Railway 部署完整指南

## 📋 部署前準備清單

### ✅ 已完成的配置
- ✅ `railway.json` - Railway 配置（新加坡節點）
- ✅ `nixpacks.toml` - 構建配置（極簡版）
- ✅ `requirements.txt` - 優化的依賴列表（6 個依賴）
- ✅ `main.py` - 優化後的主程序
- ✅ 所有代碼測試通過

### 📊 預期性能
```
構建時間: ~2 分鐘
啟動時間: 10-20 秒
記憶體使用: 150-250MB
月費用: $5-10 (Hobby Plan)
```

---

## 🎯 部署步驟

### 方法 1: Railway CLI（最快 ⚡）

#### 1. 安裝 Railway CLI
```bash
# 在本地終端（不是 Replit）
npm install -g @railway/cli

# 或使用 Homebrew (Mac)
brew install railway
```

#### 2. 登錄 Railway
```bash
railway login
```

#### 3. 初始化項目
```bash
railway init
```

#### 4. 設置環境變數
```bash
railway variables set BINANCE_API_KEY="your_key_here"
railway variables set BINANCE_SECRET_KEY="your_secret_here"
railway variables set DISCORD_BOT_TOKEN="your_token_here"
railway variables set DISCORD_CHANNEL_ID="your_channel_id_here"
railway variables set ENABLE_TRADING="true"
railway variables set BINANCE_TESTNET="false"
railway variables set SYMBOL_MODE="auto"
railway variables set MAX_SYMBOLS="50"
```

#### 5. 部署
```bash
railway up
```

#### 6. 查看日誌
```bash
railway logs
```

---

### 方法 2: Railway Dashboard（推薦 🌟）

#### 步驟 1: 連接 GitHub

1. **推送代碼到 GitHub**
   ```bash
   # 在 Replit Shell 執行
   git add .
   git commit -m "v2.0: Optimized for Railway deployment"
   git push
   ```

2. **前往 Railway**
   - 訪問：https://railway.app/
   - 點擊 "Start a New Project"
   - 選擇 "Deploy from GitHub repo"

3. **授權 GitHub**
   - 連接你的 GitHub 帳號
   - 選擇你的交易機器人 repository

#### 步驟 2: 配置部署

1. **選擇 Branch**
   - Branch: `main` 或 `master`

2. **Railway 會自動檢測**
   ```
   ✅ 檢測到 nixpacks.toml
   ✅ 檢測到 requirements.txt
   ✅ 使用 Python 3.11
   ✅ 部署區域: Singapore (來自 railway.json)
   ```

#### 步驟 3: 設置環境變數

在 Railway Dashboard → Variables → Add Variable:

```bash
BINANCE_API_KEY=你的_Binance_API_Key
BINANCE_SECRET_KEY=你的_Binance_Secret_Key
DISCORD_BOT_TOKEN=你的_Discord_Bot_Token
DISCORD_CHANNEL_ID=你的_Discord_Channel_ID
ENABLE_TRADING=true
BINANCE_TESTNET=false
SYMBOL_MODE=auto
MAX_SYMBOLS=50
RISK_PER_TRADE_PERCENT=0.3
MAX_POSITION_SIZE_PERCENT=0.5
DEFAULT_LEVERAGE=1.0
```

**重要提示**：
- ⚠️ 確保 API Key **沒有提款權限**
- ⚠️ 從小資金開始測試
- ⚠️ 先用 `ENABLE_TRADING=false` 模擬模式

#### 步驟 4: 部署

1. **點擊 "Deploy"**
2. **等待構建**（約 2-3 分鐘）
3. **查看日誌**

預期日誌輸出：
```log
====== Nixpacks Build ======
--> Installing Python 3.11
--> Creating virtual environment
--> Installing dependencies
    ✅ python-binance
    ✅ discord.py
    ✅ pandas
    ✅ numpy
    ✅ python-dotenv
    ✅ requests

====== Starting Application ======
INFO - Initializing Trading Bot...
INFO - Mode: AUTO - Fetching top 50 pairs by volume
INFO - Binance client initialized (LIVE MODE)
INFO - Loaded 50 trading pairs
INFO - Discord notifier enabled
INFO - Trading Bot started ✅
INFO - Starting analysis cycle for 50 symbols...
```

---

### 方法 3: GitHub Actions 自動部署（高級）

#### 1. 創建 GitHub Actions Workflow

創建 `.github/workflows/deploy-railway.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service trading-bot
```

#### 2. 設置 GitHub Secrets

在 GitHub repo → Settings → Secrets → Actions:

```
RAILWAY_TOKEN=你的_Railway_Token
```

獲取 Railway Token:
```bash
railway login
railway token
```

#### 3. 推送代碼自動觸發
```bash
git push
# GitHub Actions 自動部署到 Railway
```

---

## 🔧 部署後配置

### 1. 驗證 Binance 連接
```bash
railway logs | grep "Binance"
# 應該看到: Binance client initialized (LIVE MODE)
```

### 2. 驗證 Discord 連接
```bash
railway logs | grep "Discord"
# 應該看到: Discord notifier enabled
```

### 3. 監控交易
在 Discord 頻道查看：
- 🚀 啟動通知
- 📊 交易信號
- 💰 倉位開關
- 📈 性能報告

---

## 📊 監控和維護

### 查看日誌
```bash
# Railway CLI
railway logs --tail 100

# 或在 Railway Dashboard
Deployments → Logs → Live Stream
```

### 重啟服務
```bash
railway restart
```

### 檢查資源使用
```
Railway Dashboard → Metrics
- CPU 使用率
- 記憶體使用
- 網絡流量
```

---

## 🛡️ 安全檢查

### API Key 權限
```
✅ 可讀取市場數據
✅ 可執行交易
❌ 禁止提款
❌ 禁止轉帳
```

### 風險控制
```
✅ 每筆交易風險: 0.3%
✅ 最大倉位: 0.5%
✅ 槓桿: 1.0x
✅ 最大回撤警報: 5%
```

### 資金管理
```
⚠️ 建議起始資金: $100-500
⚠️ 測試期: 1-2 週
⚠️ 每日監控: Discord 通知
```

---

## ❓ 故障排除

### 問題 1: 構建失敗
```bash
# 檢查 nixpacks.toml
cat nixpacks.toml

# 應該只有:
[phases.setup]
nixPkgs = ["python311"]

[start]
cmd = "python main.py"
```

### 問題 2: Binance API 錯誤
```
錯誤: Service unavailable from restricted location
解決: 確認 railway.json 中 region = "singapore"
```

### 問題 3: Discord 無法連接
```bash
# 檢查環境變數
railway variables

# 確認 Token 格式正確
DISCORD_BOT_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4.GaBcDe.F1G2H3...
```

### 問題 4: 記憶體不足
```
當前配置: 150-250MB
Railway Hobby: 最多 512MB
如果超過: 升級到 Developer Plan
```

---

## 💰 費用估算

### Railway Hobby Plan ($5/月)
```
✅ 512MB RAM
✅ 1 vCPU
✅ 100GB 流量
✅ 足夠運行 50 個交易對
```

### Railway Developer Plan ($20/月)
```
✅ 8GB RAM
✅ 2 vCPU
✅ 無限流量
✅ 可運行 ALL 648 交易對
```

---

## 📈 性能優化建議

### 如果需要更多交易對
```bash
# 調整環境變數
MAX_SYMBOLS=100  # Hobby Plan 極限
MAX_SYMBOLS=648  # 需要 Developer Plan
```

### 如果需要更快分析
```python
# 未來優化: 異步並行分析
tasks = [analyze_market(s) for s in symbols]
results = await asyncio.gather(*tasks)
# 預期提升: 70% 更快
```

---

## 🎯 快速開始（3 步驟）

### 1️⃣ 推送代碼
```bash
git add .
git commit -m "v2.0: Ready for Railway"
git push
```

### 2️⃣ Railway 部署
1. 訪問 https://railway.app/
2. "New Project" → "Deploy from GitHub"
3. 選擇你的 repo

### 3️⃣ 設置環境變數
複製你的 API Keys 到 Railway Variables

**完成！** 🎉

---

## 📚 相關文檔

- Railway 官方文檔: https://docs.railway.app/
- Nixpacks 文檔: https://nixpacks.com/docs
- Binance API 文檔: https://binance-docs.github.io/apidocs/futures/en/

---

## ✅ 部署檢查清單

```
🟢 代碼已優化
🟢 配置文件已更新
🟢 測試全部通過
🟢 Git 推送完成
🟢 Railway 項目創建
🟢 環境變數設置
🟢 部署成功
🟢 日誌驗證
🟢 Discord 通知
🟢 開始交易
```

---

**準備好了嗎？讓我們開始部署！** 🚀

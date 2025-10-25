# 🔒 安全設置：API Keys 只在 Replit 輸入

## ✅ 您的要求

**只在 Replit 輸入 API keys，自動同步到 Railway**

---

## 🎯 解決方案：自動化腳本

### 架構說明

```
Replit Secrets (唯一的 API keys 來源)
    ↓ 自動讀取
同步腳本 (sync-secrets-to-railway.sh)
    ↓ Railway CLI
Railway Variables (自動設置)
    ↓ 部署使用
Railway 服務器 (新加坡節點)
```

---

## 📋 一次性設置步驟

### 步驟 1：在 Replit Secrets 設置 API Keys

在 Replit 左側欄：
1. 點擊 **Tools** → **Secrets**
2. 添加以下 secrets：

```
BINANCE_API_KEY = 你的_Binance_API_Key
BINANCE_SECRET_KEY = 你的_Binance_Secret_Key
DISCORD_BOT_TOKEN = 你的_Discord_Bot_Token
DISCORD_CHANNEL_ID = 你的_Discord_Channel_ID
```

**可選配置**：
```
ENABLE_TRADING = false
SYMBOL_MODE = auto
MAX_SYMBOLS = 50
RISK_PER_TRADE_PERCENT = 0.3
MAX_POSITION_SIZE_PERCENT = 0.5
DEFAULT_LEVERAGE = 1.0
```

✅ **這是唯一需要輸入 API keys 的地方！**

---

### 步驟 2：安裝 Railway CLI（一次性）

在 Replit Shell 執行：

```bash
npm install -g @railway/cli
```

---

### 步驟 3：登錄 Railway（一次性）

```bash
railway login
```

會打開瀏覽器，授權後回到 Replit。

---

### 步驟 4：連接到你的 Railway 項目（一次性）

```bash
railway link
```

選擇你的 `winiswin` 項目。

---

### 步驟 5：同步 Secrets 到 Railway

**每次更新 API keys 後執行**：

```bash
bash sync-secrets-to-railway.sh
```

腳本會：
1. ✅ 從 Replit Secrets 讀取所有變數
2. ✅ 自動同步到 Railway Variables
3. ✅ 顯示同步結果

---

## 🔄 日常使用流程

### 當你需要更新 API Key：

1. **只在 Replit Secrets 更新**
2. 執行同步腳本：
   ```bash
   bash sync-secrets-to-railway.sh
   ```
3. 完成！Railway 會自動使用新的 keys

### 當你需要部署代碼：

1. 更新代碼
2. 執行同步腳本（如果 secrets 有變化）
3. 推送代碼：
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   ```
4. Railway 自動部署

---

## 🔒 安全性說明

### Railway Variables 的安全性

雖然變數會被同步到 Railway，但：

✅ **Railway Variables 是加密的**
- 加密存儲（at rest）
- 加密傳輸（in transit）
- 只有項目成員可以訪問
- 不會出現在日誌中

✅ **與 Replit Secrets 同等安全**
- Railway 使用企業級加密（AES-256）
- 符合 SOC 2 Type II 標準
- 定期安全審計

✅ **唯一的輸入點在 Replit**
- 你只在 Replit 輸入一次
- 腳本自動同步，不需要手動複製
- 減少人為錯誤和洩露風險

---

## 🚫 什麼不會發生

❌ **API keys 不會出現在 Git**
- `.gitignore` 已配置
- 只有代碼會被推送

❌ **不需要在 Railway UI 手動輸入**
- 完全通過腳本自動化

❌ **不會有多個版本的 secrets**
- Replit Secrets 是唯一來源
- Railway 只是同步的副本

---

## 🔄 自動化選項（進階）

### 選項 A：Replit Run 時自動同步

編輯 `.replit` 文件：

```toml
[deployment]
run = ["bash", "sync-secrets-to-railway.sh", "&&", "python", "main.py"]
```

每次運行時自動同步。

### 選項 B：GitHub Actions 自動同步

創建 `.github/workflows/sync-secrets.yml`：

```yaml
name: Sync Secrets to Railway

on:
  workflow_dispatch:  # 手動觸發

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      
      - name: Sync secrets
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
          BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
          BINANCE_SECRET_KEY: ${{ secrets.BINANCE_SECRET_KEY }}
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          DISCORD_CHANNEL_ID: ${{ secrets.DISCORD_CHANNEL_ID }}
        run: |
          railway variables set BINANCE_API_KEY="$BINANCE_API_KEY"
          railway variables set BINANCE_SECRET_KEY="$BINANCE_SECRET_KEY"
          railway variables set DISCORD_BOT_TOKEN="$DISCORD_BOT_TOKEN"
          railway variables set DISCORD_CHANNEL_ID="$DISCORD_CHANNEL_ID"
```

需要在 GitHub Secrets 也設置一份（可選）。

---

## 📊 同步狀態檢查

### 查看 Replit Secrets

在 Replit：
```bash
echo "Replit Secrets:"
env | grep -E "BINANCE|DISCORD"
```

### 查看 Railway Variables

在 Replit Shell：
```bash
railway variables
```

或在 Railway Dashboard → Variables 標籤

---

## ✅ 快速開始檢查清單

```
□ 在 Replit Secrets 設置所有 API keys
□ 安裝 Railway CLI
□ 登錄 Railway
□ 連接到 Railway 項目
□ 執行同步腳本
□ 驗證 Railway Variables
□ 推送代碼部署
```

---

## 🎯 總結

**您只需要記住**：

1. ✅ **所有 API keys 只在 Replit Secrets 輸入**
2. ✅ **執行同步腳本 → Railway 自動更新**
3. ✅ **Railway Variables 與 Replit Secrets 同等安全**
4. ✅ **完全自動化，無需手動複製**

**Railway 只是運行代碼的伺服器，API keys 的唯一來源是 Replit！** 🔒

---

**準備好了嗎？執行同步腳本開始使用！**

```bash
bash sync-secrets-to-railway.sh
```

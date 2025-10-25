# 🚀 GitHub 自動部署到 Railway - 完整設置指南

此專案已配置為使用 GitHub Actions 自動部署到 Railway。每次推送到 `main` 分支時，都會自動觸發部署。

---

## ✅ 已完成的配置

### 1. GitHub Actions Workflow
- ✅ `.github/workflows/deploy.yml` - 自動部署工作流
- ✅ 每次 push 到 main 分支自動觸發
- ✅ 支持手動觸發部署

### 2. .gitignore 配置
- ✅ 排除敏感環境變數文件（.env）
- ✅ 排除日誌和數據文件
- ✅ 排除 Python 緩存和虛擬環境
- ✅ 保留所有部署配置文件

### 3. 部署配置文件
- ✅ `nixpacks.toml` - Railway 構建配置
- ✅ `railway.json` - Railway 專案配置
- ✅ `Procfile` - 啟動命令
- ✅ `requirements.txt` - Python 依賴（已優化版本）
- ✅ `.nixpacks` - Provider 配置

---

## 🎯 設置步驟

### 步驟 1：創建 GitHub 倉庫

如果還沒有 GitHub 倉庫：

1. 前往 **https://github.com** 並登入
2. 點擊右上角 **"New repository"**
3. 倉庫名稱：`crypto-trading-bot`（或您喜歡的名稱）
4. 設置為 **Private**（重要！保護您的策略代碼）
5. **不要**勾選 "Initialize with README"
6. 點擊 **"Create repository"**

---

### 步驟 2：推送代碼到 GitHub

**在 Replit Shell 執行**：

```bash
# 如果還沒初始化 git（已初始化可跳過）
git init

# 添加遠程倉庫（替換為您的倉庫 URL）
git remote add origin https://github.com/你的用戶名/crypto-trading-bot.git

# 或使用 SSH（推薦）
git remote add origin git@github.com:你的用戶名/crypto-trading-bot.git

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Trading bot with auto-deploy"

# 推送到 GitHub
git push -u origin main
```

**如果遇到認證問題**：
- 使用 Personal Access Token（Settings → Developer settings → Personal access tokens）
- 或設置 SSH key

---

### 步驟 3：獲取 Railway Token

1. 前往 **https://railway.app**
2. 登入您的帳號
3. 點擊右上角頭像 → **Account Settings**
4. 選擇 **Tokens** 標籤
5. 點擊 **"Create Token"**
6. 輸入描述：`GitHub Actions Auto Deploy`
7. 複製生成的 Token（只顯示一次！）

---

### 步驟 4：添加 GitHub Secrets

1. 前往您的 GitHub 倉庫
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **"New repository secret"**
4. 添加以下 Secret：

**Secret 名稱**: `RAILWAY_TOKEN`  
**Secret 值**: [貼上步驟 3 複製的 Railway Token]

5. 點擊 **"Add secret"**

---

### 步驟 5：連接 Railway 專案

**在本機電腦或 Replit Shell**：

```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入 Railway
railway login

# 連接到您的 Railway 專案
railway link

# 或創建新專案
railway init
```

**記下專案 ID**（在 Railway Dashboard URL 中可見）

---

### 步驟 6：設置 Railway 環境變數

在 Railway Dashboard：

1. 選擇您的專案
2. 點擊 **Variables** 標籤
3. 添加所有環境變數（參考 `ENVIRONMENT_VARIABLES.txt`）

**必需變數**：
```bash
BINANCE_API_KEY
BINANCE_SECRET_KEY
BINANCE_TESTNET=false
ENABLE_TRADING=true
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
SYMBOL_MODE=auto
MAX_SYMBOLS=50
RISK_PER_TRADE_PERCENT=0.5
MAX_POSITION_SIZE_PERCENT=1.0
DEFAULT_LEVERAGE=1.0
```

**重要**：
- Settings → Region → 選擇 **ap-southeast-1 (Singapore)**
- Upgrade to **Pro Plan** ($20/月) 如使用 50 個交易對

---

## 🔄 自動部署工作流程

### 觸發自動部署

每次您更新代碼並推送到 GitHub：

```bash
# 修改代碼後
git add .
git commit -m "Update: 描述您的更改"
git push
```

**自動發生**：
1. GitHub 檢測到 push
2. GitHub Actions 啟動
3. 檢出代碼
4. 安裝 Railway CLI
5. 執行 `railway up` 部署
6. Railway 自動構建並運行

**整個過程約 5-10 分鐘**

---

### 查看部署狀態

**GitHub**：
1. 前往倉庫 → **Actions** 標籤
2. 查看最新的 workflow 運行
3. 點擊查看詳細日誌

**Railway**：
1. 前往 Railway Dashboard
2. 點擊專案 → **Deployments**
3. 查看最新部署狀態和日誌

---

### 手動觸發部署

如果需要手動重新部署（不更改代碼）：

1. GitHub 倉庫 → **Actions** 標籤
2. 選擇 **"Deploy to Railway"** workflow
3. 點擊 **"Run workflow"**
4. 選擇分支（main）
5. 點擊 **"Run workflow"** 按鈕

---

## 📊 部署流程圖

```
代碼更新
    ↓
git commit & push
    ↓
GitHub 檢測變更
    ↓
GitHub Actions 觸發
    ↓
    ├─ Checkout code
    ├─ Setup Node.js
    ├─ Install Railway CLI
    └─ Run: railway up
           ↓
    Railway 接收代碼
           ↓
    Railway 構建
    ├─ Installing Python 3.11
    ├─ Installing TA-Lib
    ├─ Installing dependencies
    └─ Build successful
           ↓
    Railway 部署
           ↓
    機器人啟動
    ├─ Binance API 連接
    ├─ LSTM 模型訓練
    ├─ Discord 通知
    └─ 市場監控開始
           ↓
    部署完成 ✅
```

---

## 🔧 配置文件說明

### .github/workflows/deploy.yml

```yaml
name: Deploy to Railway

on:
  push:
    branches:
      - main          # main 分支觸發
  workflow_dispatch:   # 允許手動觸發

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install -g @railway/cli
      - run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**說明**：
- `on.push.branches` - 指定觸發分支
- `workflow_dispatch` - 啟用手動觸發
- `RAILWAY_TOKEN` - 從 GitHub Secrets 讀取

---

### .gitignore

**排除的內容**：
- ✅ `.env` 和所有環境變數文件
- ✅ Python 緩存 (`__pycache__/`)
- ✅ 日誌文件 (`*.log`)
- ✅ 交易數據 (`trades.json`)
- ✅ 虛擬環境 (`venv/`)
- ✅ IDE 配置 (`.vscode/`, `.idea/`)

**保留的內容**：
- ✅ `nixpacks.toml`
- ✅ `railway.json`
- ✅ `Procfile`
- ✅ `requirements.txt`
- ✅ 所有 `.py` 源代碼文件

---

## 🎯 最佳實踐

### 1. 分支策略

**推薦工作流**：

```bash
# 創建功能分支
git checkout -b feature/new-strategy

# 開發和測試
git add .
git commit -m "Add: new trading strategy"

# 推送到 GitHub（不會觸發部署）
git push origin feature/new-strategy

# 測試通過後，合併到 main
git checkout main
git merge feature/new-strategy
git push  # ← 這裡觸發自動部署
```

### 2. Commit 訊息規範

使用清晰的 commit 訊息：

```bash
# 功能添加
git commit -m "Add: support for 648 trading pairs"

# Bug 修復
git commit -m "Fix: Railway pip installation error"

# 配置更新
git commit -m "Update: risk parameters to 0.3%"

# 文檔更新
git commit -m "Docs: add GitHub auto-deploy guide"
```

### 3. 版本標籤

為重要版本打標籤：

```bash
# 創建標籤
git tag -a v1.0.0 -m "Version 1.0.0: Initial release"

# 推送標籤
git push origin v1.0.0

# 查看所有標籤
git tag -l
```

---

## 🚨 故障排除

### 問題 1：GitHub Actions 失敗

**錯誤**：`Error: RAILWAY_TOKEN not found`

**解決**：
1. 確認 GitHub Secrets 已設置
2. Secret 名稱必須是 `RAILWAY_TOKEN`
3. 重新運行 workflow

---

### 問題 2：Railway 構建失敗

**錯誤**：`pip: command not found`

**解決**：
✅ 已修復！`nixpacks.toml` 使用 `python -m pip`

---

### 問題 3：部署後機器人沒啟動

**檢查**：
1. Railway Logs 查看錯誤
2. 確認環境變數已設置
3. 確認部署區域為 Singapore
4. 檢查 Binance API 金鑰

---

### 問題 4：推送被拒絕

**錯誤**：`! [rejected] main -> main (fetch first)`

**解決**：
```bash
# 先拉取最新代碼
git pull origin main

# 解決衝突（如果有）
# 然後推送
git push origin main
```

---

## 📈 監控和維護

### 每日檢查

**GitHub Actions**：
- 查看最新 workflow 運行狀態
- 確認自動部署成功

**Railway**：
- 檢查部署日誌
- 監控資源使用（記憶體、CPU）
- 查看應用程式日誌

**Discord**：
- 確認機器人在線
- 查看交易通知
- 監控警報訊息

---

### 每週維護

**代碼更新**：
```bash
# 更新依賴包
pip list --outdated

# 測試新版本
# 提交並推送觸發部署
```

**性能優化**：
- 分析交易績效
- 調整風險參數
- 優化交易對數量

---

## ✅ 設置檢查清單

完成以下項目確保設置正確：

- [ ] GitHub 倉庫已創建（Private）
- [ ] 代碼已推送到 GitHub
- [ ] Railway Token 已獲取
- [ ] GitHub Secret `RAILWAY_TOKEN` 已設置
- [ ] Railway 專案已連接
- [ ] Railway 環境變數已配置
- [ ] Railway 部署區域為 Singapore
- [ ] Railway Pro 方案已升級
- [ ] 首次自動部署成功
- [ ] 機器人啟動無誤
- [ ] Discord 通知正常
- [ ] Binance API 連接成功

---

## 🎉 完成！

設置完成後，您的工作流程將是：

```bash
# 1. 修改代碼
vim main.py

# 2. 測試（可選）
python main.py

# 3. 提交
git add .
git commit -m "Update: improve trading strategy"

# 4. 推送（自動觸發部署）
git push

# 5. 等待 5-10 分鐘
# 6. 檢查 Railway Dashboard 確認部署成功
# 7. 在 Discord 確認機器人更新
```

**往後所有更新都會自動部署到 Railway！** 🚀

---

## 📚 相關文檔

- **DEPLOY_NOW.md** - 手動部署指南
- **RAILWAY_BUILD_FIX.md** - 構建問題修復
- **ENVIRONMENT_VARIABLES.txt** - 環境變數模板
- **DEPLOYMENT_CHECKLIST.md** - 部署檢查清單

---

**祝自動部署順利！** 🌟

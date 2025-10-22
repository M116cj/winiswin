# GitHub Actions 自動部署設定

## 如何設置自動部署到 Railway

### 步驟 1：獲取 Railway Token

1. 登入 [Railway](https://railway.app)
2. 前往 Account Settings → Tokens
3. 點擊 "Create Token"
4. 複製生成的 token

### 步驟 2：添加到 GitHub Secrets

1. 前往您的 GitHub repository
2. Settings → Secrets and variables → Actions
3. 點擊 "New repository secret"
4. Name: `RAILWAY_TOKEN`
5. Secret: 貼上您的 Railway token
6. 點擊 "Add secret"

### 步驟 3：自動部署

現在每次您推送代碼到 `main` 分支時：
- GitHub Actions 會自動觸發
- 代碼會自動部署到 Railway 新加坡節點
- 您可以在 Actions 標籤查看部署狀態

## 環境變數設置

記得在 Railway 平台上設置以下環境變數：
- BINANCE_API_KEY
- BINANCE_SECRET_KEY
- DISCORD_BOT_TOKEN
- DISCORD_CHANNEL_ID
- ENABLE_TRADING
- BINANCE_TESTNET

這些環境變數**不應該**儲存在 GitHub 中，只在 Railway 平台上設置。

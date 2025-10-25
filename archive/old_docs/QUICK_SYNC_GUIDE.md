# 🔒 快速指南：API Keys 只在 Replit 輸入

## ✅ 核心概念

**您只在 Replit Secrets 輸入 API keys**
**↓ 自動同步腳本**
**Railway Variables 自動更新**

---

## 🚀 快速 4 步驟

### 1️⃣ 在 Replit 設置 Secrets

Replit 左側欄 → **Tools** → **Secrets** → 添加：

```
BINANCE_API_KEY
BINANCE_SECRET_KEY
DISCORD_BOT_TOKEN
DISCORD_CHANNEL_ID
```

### 2️⃣ 安裝 Railway CLI（一次性）

```bash
npm install -g @railway/cli
railway login
railway link  # 選擇 winiswin 項目
```

### 3️⃣ 同步到 Railway

```bash
bash sync-secrets-to-railway.sh
```

### 4️⃣ 部署代碼

```bash
git push origin main
```

**完成！** 🎉

---

## 🔄 日後更新 API Key

1. **只在 Replit Secrets 更新**
2. 執行：`bash sync-secrets-to-railway.sh`
3. 完成！

---

## ✅ 安全保證

- ✅ Railway Variables 是加密的（AES-256）
- ✅ 與 Replit Secrets 同等安全
- ✅ 不會出現在 Git 中
- ✅ 唯一輸入點在 Replit

**Railway 只是運行代碼的伺服器，不是 secrets 的來源！** 🔒

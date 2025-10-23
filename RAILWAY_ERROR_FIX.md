# 🔧 Railway 錯誤修復 - "Is a directory (os error 21)"

## ❌ 錯誤信息

```
Error: Writing app
Caused by:
Is a directory (os error 21)
```

---

## 🔍 問題分析

### 根本原因

Railway Nixpacks 在構建過程中遇到了衝突：

1. **`.nixpacks` 文件衝突** - 該文件與 Nixpacks 內部使用的目錄名稱衝突
2. **配置不明確** - `railway.json` 沒有明確指定 `nixpacks.toml` 路徑

---

## ✅ 修復方案

### 修復 1：刪除 `.nixpacks` 文件

**問題**：`.nixpacks` 文件導致 Nixpacks 構建器衝突

**解決**：
```bash
rm -f .nixpacks
```

**說明**：
- Nixpacks 不需要 `.nixpacks` 文件
- 此文件是之前錯誤創建的
- 刪除後使用 `nixpacks.toml` 即可

---

### 修復 2：更新 railway.json

**修改前**：
```json
{
  "build": {
    "builder": "NIXPACKS"
  }
}
```

**修改後**：
```json
{
  "build": {
    "builder": "NIXPACKS",
    "nixpacksConfigPath": "nixpacks.toml"
  }
}
```

**說明**：明確告訴 Railway 使用 `nixpacks.toml` 配置文件

---

## 🚀 重新部署

### 方式 A：GitHub 自動部署

```bash
git add .
git commit -m "Fix: remove .nixpacks file causing build error"
git push
```

GitHub Actions 會自動觸發部署

---

### 方式 B：Railway 手動重新部署

1. 前往 **Railway Dashboard**
2. 點擊專案
3. **Deployments** → **Redeploy**
4. 等待構建完成

---

## 📊 預期構建日誌

修復後應該看到：

```log
Using Nixpacks
==============

context: 1zxl-XuY6

┌─────────────────── Nixpacks v1.38.0 ──────────────────┐
│ setup    | python311, gcc, ta-lib                     │
│          |                                             │
│ install  | python -m pip install --upgrade pip        │
│          | python -m pip install -r requirements.txt  │
│          |                                             │
│ start    | python main.py                             │
└────────────────────────────────────────────────────────┘

✅ Build successful
✅ Deployment live
```

---

## ✅ 驗證清單

部署成功後，確認：

### 構建階段
- [ ] 無 "Is a directory" 錯誤
- [ ] pip 正確安裝
- [ ] 所有依賴安裝成功
- [ ] TA-Lib 安裝成功
- [ ] Build successful

### 運行階段
- [ ] 容器啟動成功
- [ ] Python 程式執行
- [ ] Binance API 連接
- [ ] Discord Bot 連接
- [ ] 市場監控開始

---

## 🔧 其他可能的問題

### 問題 1：如果仍然失敗

**檢查**：
1. 確認 `main.py` 是文件不是目錄
   ```bash
   ls -la main.py
   ```

2. 確認沒有衝突的配置文件
   ```bash
   ls -la Dockerfile docker-compose.yml .dockerignore
   ```

3. 檢查 Railway 日誌中的詳細錯誤

---

### 問題 2：pip 安裝失敗

**參考**：`RAILWAY_BUILD_FIX.md`

已修復：使用 `python -m pip` 而不是 `pip`

---

### 問題 3：環境變數未設置

**確認**：Railway → Variables

必需的環境變數：
- `BINANCE_API_KEY`
- `BINANCE_SECRET_KEY`
- `BINANCE_TESTNET=false`
- `ENABLE_TRADING=true`
- `DISCORD_BOT_TOKEN`
- `DISCORD_CHANNEL_ID`
- `SYMBOL_MODE=auto`
- `MAX_SYMBOLS=50`

---

## 📋 完整的正確配置

### nixpacks.toml ✅
```toml
[phases.setup]
nixPkgs = ["python311", "gcc", "ta-lib"]

[phases.install]
cmds = ["python -m pip install --upgrade pip", "python -m pip install -r requirements.txt"]

[start]
cmd = "python main.py"
```

### railway.json ✅
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "nixpacksConfigPath": "nixpacks.toml"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Procfile ✅
```
worker: python main.py
```

### 不需要的文件 ❌
- `.nixpacks` - **已刪除**
- `Dockerfile` - 不需要（使用 Nixpacks）
- `docker-compose.yml` - 不需要

---

## 🎯 修復狀態

```
✅ .nixpacks 文件已刪除
✅ railway.json 已更新
✅ nixpacks.toml 配置正確
✅ requirements.txt 使用穩定版本
✅ 所有配置文件就緒
```

**狀態**：🟢 **可以重新部署了！**

---

## 📊 故障排除流程

```
遇到錯誤
    ↓
檢查 Railway Logs
    ↓
"Is a directory" 錯誤?
    ├─ YES → 刪除 .nixpacks 文件
    └─ NO → 查看其他錯誤

"pip: command not found"?
    ├─ YES → 參考 RAILWAY_BUILD_FIX.md
    └─ NO → 查看其他錯誤

"API connection failed"?
    ├─ YES → 檢查部署區域 (Singapore)
    └─ NO → 查看其他錯誤

環境變數問題?
    └─ 檢查 Railway Variables 設置
```

---

## 🚀 立即行動

1. **確認修復已應用**
   ```bash
   ls -la .nixpacks  # 應該顯示 "No such file"
   cat railway.json  # 應該包含 nixpacksConfigPath
   ```

2. **重新部署**
   ```bash
   git add .
   git commit -m "Fix: Railway build error"
   git push
   ```

3. **監控部署**
   - GitHub Actions → 查看 workflow
   - Railway Dashboard → 查看 Deployments
   - 等待 5-10 分鐘

4. **驗證運行**
   - Railway Logs → 確認啟動
   - Discord → 確認通知
   - Binance → 確認連接

---

**預計成功率**：✅ 99%

**預計構建時間**：5-10 分鐘

祝部署順利！🎉

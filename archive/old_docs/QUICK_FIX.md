# ⚡ 快速修復指南

## 🎯 立即嘗試的解決方案

### 方案 1: 先切回模擬模式測試（最安全）

這樣可以確認機器人本身是否能正常運行：

```bash
# 在 Replit Shell 執行
railway variables --set "ENABLE_TRADING=false" --service winiswin
```

**等待 1-2 分鐘**，然後在 Discord 測試 `/status`

**如果機器人恢復**：
- ✅ 說明機器人代碼沒問題
- ❓ 可能是實盤模式的某個配置有問題
- → 我們可以逐步排查

**如果機器人仍無回應**：
- ❌ 說明有更深層的問題（Discord Token、部署配置等）
- → 需要查看 Railway 日誌找出具體原因

---

### 方案 2: 強制重新部署

```bash
# 在 Replit Shell 執行
cd /home/runner/workspace
railway up --service winiswin --detach
```

這會重新上傳代碼並重新部署。

---

### 方案 3: 檢查 Railway 網頁控制台

**必須步驟**：

1. 訪問：https://railway.com/dashboard
2. 登入您的帳號
3. 選擇項目：`ravishing-luck`
4. 選擇服務：`winiswin`
5. **查看 Logs 標籤** ← 這是最重要的！

**尋找以下關鍵詞**：
- `ERROR` (紅色錯誤)
- `CRITICAL` (嚴重錯誤)
- `Traceback` (Python 異常)
- `discord.errors` (Discord 問題)
- `APIError` (Binance API 問題)

---

## 📊 根據日誌類型的解決方案

### 看到：Discord Token 錯誤
```
ERROR - Improper token has been passed
discord.errors.LoginFailure
```

**原因**：Discord Bot Token 無效或過期

**解決方案**：
1. 訪問：https://discord.com/developers/applications
2. 選擇您的 Bot
3. Bot → Reset Token → 複製新 Token
4. 在 Railway 更新：
   ```bash
   railway variables --set "DISCORD_BOT_TOKEN=新的token" --service winiswin
   ```

---

### 看到：Binance API 錯誤
```
ERROR - Invalid API-key
ERROR - APIError
```

**原因**：Binance API Key 有問題

**檢查清單**：
- [ ] API Key 是否正確複製（沒有多餘空格）
- [ ] API Key 是否有「現貨與槓桿交易」和「合約交易」權限
- [ ] API Key 是否被禁用或刪除
- [ ] IP 白名單是否限制了訪問（應該不設置白名單）

**解決方案**：
重新在 Binance 創建 API Key 並更新到 Railway

---

### 看到：地理限制錯誤
```
Service unavailable from a restricted location
```

**原因**：Railway 部署區域不在歐洲

**解決方案**：
在 Railway 控制台：
1. Settings → Region
2. 改為：`europe-west4` 或其他歐洲區域
3. 重新部署

---

### 看到：Python 模組錯誤
```
ModuleNotFoundError: No module named 'xxx'
```

**原因**：缺少依賴

**解決方案**：
檢查 `requirements.txt` 是否包含所有依賴

---

## 🔄 最後手段：完全重置

如果以上都無效，嘗試完全重置：

```bash
# 1. 暫時停用交易
railway variables --set "ENABLE_TRADING=false" --service winiswin

# 2. 等待 2 分鐘

# 3. 重新部署
cd /home/runner/workspace
railway up --service winiswin

# 4. 等待 2 分鐘，測試 Discord

# 5. 如果正常，再啟用交易
railway variables --set "ENABLE_TRADING=true" --service winiswin
```

---

## 📞 我需要的信息

請把 Railway Logs 的最後 30 行複製給我，我會立即診斷問題！

訪問：
1. https://railway.com/dashboard
2. ravishing-luck → winiswin → Logs
3. 複製最後 30 行（包括紅色錯誤）

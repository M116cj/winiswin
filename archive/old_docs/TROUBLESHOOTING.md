# 🔧 機器人掉線故障排查指南

## 📊 當前狀態

✅ 環境變量已設置：
- `ENABLE_TRADING = true`
- `BINANCE_TESTNET = false`
- `BINANCE_API_KEY = 已設置`
- `DISCORD_BOT_TOKEN = 已設置`

❌ 機器人狀態：掉線

---

## 🔍 立即檢查：Railway 網頁控制台

### 步驟 1: 查看部署日誌

1. **訪問**：https://railway.com/dashboard
2. **選擇項目**：`ravishing-luck`
3. **選擇服務**：`winiswin`
4. **點擊 "Deployments" 標籤**
   - 查看最新的部署狀態
   - 是否顯示 "Success" 還是 "Failed"？

5. **點擊 "Logs" 標籤**
   - 查看最近的日誌輸出
   - 尋找錯誤訊息（紅色文字）

---

## 🎯 常見問題診斷

### 可能原因 1: Discord Token 過期或無效

**症狀**：
- 日誌顯示 Discord 連接錯誤
- `discord.errors.LoginFailure`
- `Improper token has been passed`

**檢查日誌中是否包含**：
```
ERROR - Discord connection failed
ERROR - Improper token
```

**解決方案**：
→ 需要重新生成 Discord Bot Token

---

### 可能原因 2: Binance API 連接問題

**症狀**：
- 日誌顯示 API 錯誤
- `Service unavailable from a restricted location`
- `Invalid API-key`

**檢查日誌中是否包含**：
```
ERROR - Error fetching klines
ERROR - APIError
ERROR - Invalid API-key
```

**可能的問題**：
1. **地理限制仍存在**（但應該已解決，因為在歐洲）
2. **API Key 無效或過期**
3. **API Key 權限不足**

**解決方案**：
→ 需要檢查 Binance API 設置

---

### 可能原因 3: Python 依賴問題

**症狀**：
- 日誌顯示 `ModuleNotFoundError`
- `ImportError`
- 部署失敗

**檢查日誌中是否包含**：
```
ModuleNotFoundError: No module named 'xxx'
ImportError: cannot import name 'xxx'
```

**解決方案**：
→ 需要檢查 `requirements.txt`

---

### 可能原因 4: 代碼錯誤

**症狀**：
- Python 異常錯誤
- `AttributeError`, `TypeError`, `ValueError`
- 機器人啟動後立即崩潰

**檢查日誌中是否包含**：
```
Traceback (most recent call last):
AttributeError:
TypeError:
```

**解決方案**：
→ 需要修復代碼 bug

---

### 可能原因 5: Railway 資源限制

**症狀**：
- `OOMKilled` (記憶體不足)
- 服務頻繁重啟
- `Resource limit exceeded`

**解決方案**：
→ 需要優化記憶體使用或升級 Railway 方案

---

## 📋 請提供給我的信息

為了更準確地診斷問題，請您：

1. **訪問 Railway 控制台**：
   - https://railway.com/dashboard
   - 項目：ravishing-luck
   - 服務：winiswin
   - Logs 標籤

2. **複製最近的錯誤日誌**（最後 20-30 行）

3. **告訴我您看到的錯誤類型**：
   - [ ] Discord 連接錯誤
   - [ ] Binance API 錯誤
   - [ ] Python 代碼錯誤
   - [ ] 部署失敗
   - [ ] 其他（請描述）

---

## 🚀 快速修復方案

### 方案 A: 重新部署（如果是臨時問題）

```bash
# 在 Replit Shell 執行
cd /home/runner/workspace
railway up --service winiswin
```

### 方案 B: 暫時切回模擬模式測試

```bash
# 先切回模擬模式，確認機器人能正常運行
railway variables --set "ENABLE_TRADING=false" --service winiswin
```

等待 1-2 分鐘後，在 Discord 檢查 `/status`，看機器人是否恢復。

### 方案 C: 檢查 Railway 服務狀態

在 Railway 控制台：
- Settings → General
- 確認 "Start Command" 是否正確：`python main_v3.py`
- 確認 Region 是否為歐洲區域

---

## 📱 Discord 測試命令

如果機器人有回應（即使是模擬模式），請測試：

```
/status   # 查看運行狀態
/balance  # 查看帳戶連接
```

如果完全沒有回應，說明：
1. Discord Bot 沒有啟動
2. Token 有問題
3. 機器人崩潰了

---

## 🆘 我需要您的反饋

請告訴我：

**問題 1**: Railway Logs 中看到什麼錯誤？
- 請複製粘貼最後 20-30 行日誌

**問題 2**: Discord 機器人有任何回應嗎？
- 試試 `/status` 或 `/balance`

**問題 3**: Railway Deployments 狀態如何？
- Success（成功）還是 Failed（失敗）？

有了這些信息，我就能精確診斷並修復問題！

# 🚀 立即部署到 Railway - 實盤測試

## ⚡ 快速部署指令

系統已配置為**小資金實盤測試模式**，現在可以立即部署。

---

## 📋 步驟 1: 在 Railway 設置環境變數

前往 [Railway Dashboard](https://railway.app) → 您的專案 → **Variables**

### 複製以下環境變數

從 **Replit Secrets** 複製到 **Railway Variables**：

```bash
# === 核心配置 ===
BINANCE_API_KEY=[從 Replit Secrets 複製]
BINANCE_SECRET_KEY=[從 Replit Secrets 複製]

# === 實盤模式 ===
BINANCE_TESTNET=false
ENABLE_TRADING=true

# === Discord 通知（強烈建議）===
DISCORD_BOT_TOKEN=[從 Replit Secrets 複製]
DISCORD_CHANNEL_ID=[從 Replit Secrets 複製]
```

### 如何從 Replit Secrets 複製

1. Replit 左側 → Tools → Secrets
2. 點擊每個 Secret 的👁️圖標查看值
3. 全選複製
4. 貼到 Railway Variables 的對應欄位

---

## 📋 步驟 2: 確認部署區域

⚠️ **非常重要**

在 Railway → Settings → Region，確認設為：
```
ap-southeast-1 (Singapore) 🇸🇬
```

如果不是，請更改為新加坡。

---

## 📋 步驟 3: 推送代碼（如果使用 GitHub Actions）

```bash
# 在 Replit Shell 執行
git add .
git commit -m "Production ready: Small capital live trading"
git push origin main
```

GitHub Actions 會自動部署到 Railway。

---

## 📋 步驟 4: 監控部署

### Railway Dashboard → Deployments

等待構建完成（約 3-5 分鐘）：

```log
✅ Building...
✅ Installing dependencies...
✅ Installing TA-Lib... 
✅ Deployment successful
```

### Railway Dashboard → Logs

確認機器人正常啟動：

```log
✅ 期待看到：
INFO - Initializing Trading Bot...
INFO - Binance client initialized (LIVE MODE)
INFO - Current balance: $XX.XX USDT
INFO - Training LSTM model for BTCUSDT...
INFO - Model training completed
INFO - Starting market monitoring (LIVE TRADING ENABLED)
```

### Discord 頻道

應該收到：
```
🤖 交易機器人已啟動
📊 模式：實盤交易
💰 賬戶餘額：$XX.XX USDT
⚙️ 風險設定：0.3% per trade
```

---

## ⚠️ 部署前最後確認

### 安全檢查清單

再次確認以下項目（非常重要）：

- [ ] Binance API **已停用提現權限**
- [ ] Railway 部署區域為 **Singapore**
- [ ] Discord 通知已設置
- [ ] 測試資金在 $50-100 USD
- [ ] 我理解可能損失全部資金
- [ ] 我已閱讀 `PRODUCTION_SETUP.md`

### 當前風險參數

系統已自動設置為保守模式：
- 每筆交易風險：**0.3%** 賬戶
- 最大倉位：**0.5%** 賬戶
- 槓桿：**1.0x**（無槓桿）
- 止損：**2.0 ATR**
- 止盈：**3.0 ATR**

---

## 🎯 第一個小時監控計劃

部署後的第一個小時**必須密切監控**：

### 0-15 分鐘
- ✅ 確認機器人啟動
- ✅ 檢查 Binance 連接
- ✅ 驗證賬戶餘額顯示正確

### 15-30 分鐘
- ✅ LSTM 模型訓練完成
- ✅ 市場數據正常更新
- ✅ Discord 通知正常

### 30-60 分鐘
- ✅ 觀察交易信號（可能還沒有）
- ✅ 如果有交易，檢查倉位大小
- ✅ 確認止損止盈正確設置

---

## 🚨 緊急停止

如果出現任何異常，立即在 Railway Variables 設置：

```bash
ENABLE_TRADING=false
```

這會停止下新單，但不會平倉現有倉位。

---

## 📊 預期交易頻率

基於 1 小時時間框架和保守策略：

- **每天**：0-3 筆交易
- **每週**：5-15 筆交易
- **每月**：20-40 筆交易

如果交易頻率遠超這個範圍，請檢查系統是否正常。

---

## 💰 預期倉位大小

假設賬戶 $100 USD：

| 交易對 | 價格範圍 | 預期倉位 | 風險金額 |
|--------|---------|---------|---------|
| BTCUSDT | $50,000 | ~0.00001 BTC | ~$0.30 |
| ETHUSDT | $3,000 | ~0.0002 ETH | ~$0.30 |

倉位應該**非常小**，這是正常的保守設置。

---

## ✅ 部署確認

完成上述步驟後，您的系統將：

1. ✅ 在 Railway 新加坡節點運行
2. ✅ 連接真實 Binance API
3. ✅ 使用真實資金交易（小額）
4. ✅ 發送 Discord 實時通知
5. ✅ 記錄所有交易到 `trades.json`
6. ✅ 自動執行 ICT/SMC + LSTM 策略

---

## 🎉 開始部署！

**一切準備就緒！**

現在可以：
1. 在 Railway 設置環境變數
2. 推送代碼（或手動部署）
3. 監控 Railway Logs
4. 查看 Discord 通知
5. 記錄第一筆交易

祝您交易順利！🚀

---

**重要提醒**：
- 📊 前 24 小時密切監控
- 🛡️ 嚴格遵守風險管理
- 📝 記錄每筆交易
- ⚠️ 不要貪婪或恐懼
- 🎯 專注於過程，而非結果

**這是學習和測試階段，不要期待立即盈利。**

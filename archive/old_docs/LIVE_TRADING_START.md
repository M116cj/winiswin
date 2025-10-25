# 🚀 實盤交易啟動指南

## ⚠️ 重要提醒

1. **地理限制**: Replit 伺服器無法訪問 Binance API，**必須部署到 Railway EU**
2. **交易紀錄**: 所有交易數據自動保存到 `trades.json` 供 XGBoost 學習
3. **Discord 通知**: 確保 Discord Channel ID 正確設置

---

## 📊 當前系統狀態

✅ **交易紀錄系統已升級** - 完整記錄供 XGBoost 學習：
- 進場/出場數據（價格、時間、數量、槓桿）
- 技術指標（MACD, EMA, ATR, 市場結構等）
- 交易結果（PnL, 勝率、止損/止盈觸發）
- 策略信息（信心度、預期 ROI）

✅ **高頻交易模式已配置**:
- 1 分鐘 K 線掃描
- 損益平衡止損策略
- 可配置風險收益比（1:1 或 1:2）
- 交易手續費已納入計算

✅ **Discord 連接測試通過**

❌ **Replit 地理限制** - 無法從此環境訪問 Binance API

---

## 🎯 Railway 部署步驟

### 步驟 1: 設置 Railway 環境變量

在 Railway 專案的 **Variables** 頁面設置：

```bash
# ⚠️ 啟用實盤交易（關鍵！）
ENABLE_TRADING=true

# 🔐 API 密鑰（應已設置）
BINANCE_API_KEY=<您的 API Key>
BINANCE_SECRET_KEY=<您的 Secret Key>
DISCORD_BOT_TOKEN=<您的 Bot Token>

# 📱 Discord 頻道 ID
# 當前設置: 1430538906629050500
# 如需更新，請從 Discord 複製正確的頻道 ID
DISCORD_CHANNEL_ID=<正確的頻道 ID>

# 📊 高頻交易配置（可選，已有默認值）
RISK_REWARD_RATIO=2.0  # 或 1.0 (1:1 風險收益比)
USE_BREAKEVEN_STOPS=true
```

### 步驟 2: 部署到 Railway

```bash
# 方法 A: 使用部署腳本
./deploy_to_railway.sh

# 方法 B: 使用 Railway CLI
railway link
railway up
```

### 步驟 3: 監控部署狀態

```bash
# 查看實時日誌
railway logs --follow

# 或使用檢查腳本
./check_railway_logs.sh
```

---

## ✅ 部署成功標誌

日誌中應該看到：

```
✅ Monitoring: 648 symbols
✅ Trading mode: 🔴 LIVE
✅ Timeframe: 1m
✅ Discord bot logged in
✅ Discord bot ready
📊 Trading Cycle #1 - Analyzing market data...
```

**確認 Discord 通知**:
- 系統啟動通知
- 交易信號通知
- 開倉/平倉通知

---

## 📊 交易數據記錄

每筆交易都會保存到 `trades.json`，包含：

### 開倉記錄
```json
{
  "type": "OPEN",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "entry_price": 50000.0,
  "quantity": 0.1,
  "leverage": 10.0,
  "confidence": 85.5,
  "expected_roi": 2.5,
  "metadata": {
    "macd": 125.5,
    "ema_9": 49950.0,
    "atr": 500.0,
    "structure": "bullish_structure"
  }
}
```

### 平倉記錄
```json
{
  "type": "CLOSE",
  "symbol": "BTCUSDT",
  "entry_price": 50000.0,
  "exit_price": 51000.0,
  "pnl": 100.0,
  "pnl_percent": 3.0,
  "duration_hours": 0.5,
  "is_winner": true,
  "hit_take_profit": true
}
```

這些數據可直接用於 XGBoost 特徵工程和模型訓練。

---

## ⚠️ 風險管理提醒

1. **小額測試**: 建議首次以小額資金測試（例如 100-500 USDT）
2. **密切監控**: 監控前幾個交易週期，確認策略正常運行
3. **止損保護**: 系統會自動設置交易所級別止損/止盈訂單
4. **Discord 警報**: 確保 Discord 通知正常，及時收到警報

---

## 🆘 緊急停止

如需緊急停止交易：

```bash
# 在 Railway 設置
railway variables set ENABLE_TRADING=false

# 或直接停止服務
railway down
```

---

## 📞 故障排除

### 問題 1: Binance API 連接失敗
- ✅ 確認部署在 Railway EU (europe-west4)
- ✅ 檢查 API 密鑰有期貨交易權限
- ✅ 確認 API 未設置 IP 白名單

### 問題 2: Discord Channel ID 錯誤
- ✅ 在 Discord 啟用開發者模式
- ✅ 右鍵點擊頻道 → 複製頻道 ID
- ✅ 更新 Railway 環境變量

### 問題 3: 交易未執行
- ✅ 確認 `ENABLE_TRADING=true`
- ✅ 檢查賬戶餘額
- ✅ 查看日誌中的拒絕原因

---

**準備就緒後，執行部署腳本開始實盤交易！** 🚀

# 🚀 快速開始指南

## ✅ 機器人已啟動！

您的加密貨幣交易機器人現在正在運行，並且**每個動作都在 Discord 中報告**！

---

## 📱 在 Discord 中查看

### 步驟 1: 打開 Discord

前往您的 Discord 應用或網頁版：https://discord.com

### 步驟 2: 找到通知頻道

頻道 ID: `1430538906629050500`

### 步驟 3: 查看實時通知

您會看到類似這樣的通知：

```
🤖 Trading Bot is now online and monitoring markets!

🔄 開始新的分析週期 - 監控 5 個交易對...

[嵌入訊息]
┌─ 🔍 市場分析: BTCUSDT ───────┐
│ 當前價格: $50,628.78         │
│ ATR: $1,012.58              │
│ 市場結構: bullish            │
└─────────────────────────────┘

[嵌入訊息]
┌─ 📡 交易信號: BTCUSDT ───────┐
│ **BUY** 信號檢測             │
│ 入場價格: $50,628.78         │
│ 止損: $49,600.00            │
│ 止盈: $51,700.00            │
└─────────────────────────────┘

[嵌入訊息]
┌─ 🔔 Trade Executed ──────────┐
│ Type: BUY                   │
│ Price: $50,628.78           │
│ Quantity: 0.001000          │
└─────────────────────────────┘

✅ 分析週期完成（用時 7.2秒）- 發現 1 個信號
```

---

## 🎯 當前狀態

| 項目 | 狀態 |
|------|------|
| **Discord Bot** | ✅ winiswin#6842 |
| **運行模式** | 演示模式（模擬數據） |
| **週期間隔** | 30 秒 |
| **監控交易對** | 5 個 (BTC, ETH, BNB, SOL, XRP) |
| **通知功能** | ✅ 完全啟用 |

---

## 📊 通知類型

### 1. 🔄 週期通知
- 開始: "🔄 開始新的分析週期..."
- 完成: "✅ 分析週期完成（用時 X秒）- 發現 X 個信號"

### 2. 🔍 市場分析（紫色嵌入訊息）
- 當前價格
- ATR（波動率）
- 市場結構
- RSI, MACD 信號

### 3. 📡 交易信號（綠色/紅色嵌入訊息）
- 信號類型（BUY/SELL）
- 入場價格
- 止損/止盈
- 建議倉位
- 信心度

### 4. 🔔 交易執行（詳細嵌入訊息）
- 交易類型
- 執行價格
- 數量
- 止損/止盈設置

### 5. 📊 性能報告（藍色，每天一次）
- 賬戶餘額
- 總交易數
- 勝率
- 總盈虧
- 最大回撤
- ROI

### 6. ⚠️ 警報（橙色/紅色）
- 警告（回撤過高等）
- 錯誤（系統問題）

---

## 🔧 控制機器人

### 查看運行狀態

```bash
tail -f demo_bot.log
```

### 停止機器人

```bash
pkill -f demo_bot.py
```

### 重啟機器人

```bash
nohup python3 demo_bot.py > demo_bot.log 2>&1 &
```

---

## 📚 相關文檔

1. **[DISCORD_NOTIFICATIONS_GUIDE.md](DISCORD_NOTIFICATIONS_GUIDE.md)** - Discord 通知完整指南
2. **[RISK_MANAGEMENT_EXPLAINED.md](RISK_MANAGEMENT_EXPLAINED.md)** - 風險管理詳解
3. **[SYSTEM_PRESENTATION_V2.md](SYSTEM_PRESENTATION_V2.md)** - 系統完整報告

---

## 🎮 切換到真實模式

當您準備好使用真實 Binance 數據時：

### 1. 設置測試網

```bash
export BINANCE_TESTNET=true
```

### 2. 停止演示模式

```bash
pkill -f demo_bot.py
```

### 3. 啟動真實模式

```bash
python3 main.py
```

**注意**: 真實模式需要有效的 Binance API 連接。

---

## ✅ 一切就緒！

**立即前往 Discord 查看您的機器人正在做什麼！** 📱

每個分析、每個信號、每筆交易都會實時報告給您！

---

**問題？** 查看 `demo_bot.log` 或相關文檔。

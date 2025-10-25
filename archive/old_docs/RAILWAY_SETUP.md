# Railway 部署配置指南

## 環境變數設置

在 Railway Dashboard → 您的服務 → **Variables** 中設置以下環境變數：

### 🔐 必需的 API 密鑰

```bash
# 幣安 API（必須）
BINANCE_API_KEY=你的幣安API密鑰
BINANCE_SECRET_KEY=你的幣安密鑰

# Discord 機器人（必須）
DISCORD_BOT_TOKEN=你的Discord機器人令牌
DISCORD_CHANNEL_ID=你的Discord頻道ID
```

### ⚙️ 交易配置

```bash
# 啟用真實交易（重要！）
ENABLE_TRADING=false          # false = 模擬模式（紙上交易）
                              # true  = 真實交易模式

# 幣安測試網（生產環境應該設為 false）
BINANCE_TESTNET=false         # false = 真實幣安
                              # true  = 幣安測試網

# 風險管理參數
RISK_PER_TRADE_PERCENT=0.3    # 每筆交易風險：0.3%
MAX_POSITION_SIZE_PERCENT=0.5 # 最大倉位：0.5%
DEFAULT_LEVERAGE=1.0          # 槓桿（建議保持 1.0）

# 倉位管理
MAX_CONCURRENT_POSITIONS=3    # 最多同時持倉：3個
```

### 📊 交易對選擇

```bash
# 交易對模式
SYMBOL_MODE=all               # all = 全部 648 個 USDT 合約
                              # static = 使用靜態列表
                              # auto = 自動選擇（按成交量）

MAX_SYMBOLS=648               # 最多監控交易對數量
```

---

## 🚀 如何啟用真實交易

### ⚠️ 在啟用真實交易之前，請確保：

1. **帳戶餘額已正確讀取**
   - 查看 Railway Logs，確認顯示真實的 USDT 餘額
   - Discord 執行 `/balance`，確認數字正確

2. **機器人運行穩定**
   - 在模擬模式下至少運行 24 小時
   - 確認沒有錯誤或崩潰

3. **Discord 通知正常**
   - 所有 Slash Commands 正常工作
   - 能夠接收週期和信號通知

### ✅ 啟用步驟：

1. **Railway Dashboard** → 您的服務 → **Variables**

2. 找到 `ENABLE_TRADING` 變數

3. 將值改為：`true`

4. 點擊 **Save**（Railway 會自動重新部署）

5. **監控日誌**：
   ```
   Railway Dashboard → Deployments → 查看 Logs
   ```
   
   應該看到：
   ```
   📈 Trading Mode: LIVE TRADING
   ```

6. **測試**：等待機器人找到交易信號，確認 Discord 通知：
   - 🟡 模擬模式 → 🔴 真實模式
   - 顯示 "LIVE" 標記

---

## 📍 IP 白名單（可選）

如果您在幣安 API 設置中啟用了 IP 白名單：

1. **獲取 Railway 固定 IP**：
   - Railway Dashboard → 服務 → Settings
   - 啟用 **Static Outbound IPs**（需要 Pro 計劃）
   - 複製顯示的 IP 地址

2. **添加到幣安白名單**：
   - 幣安網站 → API 管理
   - 找到您的 API Key
   - 添加 Railway 的固定 IP

---

## 🔍 驗證部署

### 檢查日誌：

```
Railway Dashboard → Deployments → View Logs
```

**應該看到：**
```
======================================================================
📊 Loading Account Balance from Binance
======================================================================
📈 U本位合約 USDT: $XXX.XX USDT
----------------------------------------------------------------------
✅ Total Account Balance: $XXX.XX USDT
----------------------------------------------------------------------
📊 Risk Management Configuration:
   • Max Positions: 3
   • Capital per Position: $XXX.XX USDT (33.33%)
   • Risk per Trade: 0.3%
   • Max Position Size: 0.5%
======================================================================
✅ Initialization Complete - Bot Ready
======================================================================
💰 Account Balance: $XXX.XX USDT
📈 Trading Mode: SIMULATION (Paper Trading)  ← 或 LIVE TRADING
======================================================================
```

### Discord 驗證：

執行以下命令：
```
/status   → 查看系統狀態
/balance  → 查看帳戶餘額（應該是真實金額）
/config   → 查看當前配置
```

---

## ⚙️ 重要提醒

### ⚠️ 安全建議：

1. **API 權限**：
   - ✅ 啟用：現貨與槓桿交易、合約交易
   - ❌ 禁用：提現權限（Withdraw）
   
2. **IP 限制**：
   - 建議啟用 Railway 固定 IP 白名單
   - 提高安全性

3. **風險控制**：
   - 建議從小金額開始（$100-$1000 USDT）
   - 觀察 1-2 周後再增加資金

### 🛑 緊急停止：

如果需要立即停止交易：

**方法 1：禁用交易**
```bash
# Railway Variables
ENABLE_TRADING=false
```

**方法 2：停止服務**
```
Railway Dashboard → 服務 → ... → Pause Service
```

**方法 3：Discord 命令**
```
/status  # 檢查當前狀態
```

---

## 📞 支援

如果遇到問題：

1. 檢查 Railway Logs
2. 檢查 Discord 是否收到錯誤通知
3. 使用 Discord `/status` 查看系統健康狀態
4. 確認環境變數設置正確

---

## 🎯 當前配置摘要

| 參數 | 當前值 | 說明 |
|------|--------|------|
| 交易模式 | SIMULATION | 紙上交易，不會真實下單 |
| 最大倉位 | 3 個 | 最多同時持有 3 個倉位 |
| 每倉位資金 | 總資金 ÷ 3 | 33.33% 資金分配 |
| 每筆風險 | 0.3% | 每筆交易最大虧損 0.3% |
| 最大倉位 | 0.5% | 單個倉位不超過 0.5% |
| 監控數量 | 648 個 | 所有 USDT 永續合約 |

---

**記住：啟用真實交易前，務必在模擬模式下充分測試！**

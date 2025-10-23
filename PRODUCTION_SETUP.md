# 🔴 實盤交易配置指南 - 小資金測試模式

## ⚠️ 重要安全警告

**在繼續之前，請確認您已完成以下檢查：**

- [ ] 我理解加密貨幣交易有高風險，可能損失全部資金
- [ ] 我已在 Testnet 環境測試至少 24 小時
- [ ] 我的 Binance API Key **已停用提現權限**
- [ ] 我已設置 IP 白名單（可選但推薦）
- [ ] 我準備的測試資金在 $50-100 USD 範圍
- [ ] 我已啟用 Discord 通知以實時監控交易

---

## 🎯 小資金實盤測試配置

### 當前風險參數（已優化）

系統已自動調整為保守的小資金測試模式：

| 參數 | 測試模式值 | 說明 |
|------|-----------|------|
| **RISK_PER_TRADE_PERCENT** | 0.3% | 每筆交易僅冒 0.3% 賬戶風險 |
| **MAX_POSITION_SIZE_PERCENT** | 0.5% | 單筆最大倉位為賬戶的 0.5% |
| **DEFAULT_LEVERAGE** | 1.0x | 不使用槓桿（現貨交易） |
| **STOP_LOSS_ATR_MULTIPLIER** | 2.0 | 止損距離為 2 倍 ATR |
| **TAKE_PROFIT_ATR_MULTIPLIER** | 3.0 | 止盈距離為 3 倍 ATR |

**舉例計算**（假設賬戶 $100 USD）：
- 單筆交易風險：$100 × 0.3% = $0.30
- 最大倉位大小：$100 × 0.5% = $0.50
- 如果 BTC 價格 $50,000，止損在 2% 距離，則倉位約 0.00001 BTC

---

## 📋 Railway 環境變數設置

### 方式 1：手動在 Railway Dashboard 設置

前往 Railway → 您的專案 → **Variables** 標籤，設置：

```bash
# ===== Binance 配置 =====
BINANCE_API_KEY=你的_Binance_API_金鑰
BINANCE_SECRET_KEY=你的_Binance_私鑰
BINANCE_TESTNET=false          # 🔴 實盤模式
ENABLE_TRADING=true            # 🔴 啟用真實交易

# ===== Discord 通知（強烈建議）=====
DISCORD_BOT_TOKEN=你的_Discord_Token
DISCORD_CHANNEL_ID=你的_頻道_ID

# ===== 風險參數（可選，使用代碼默認值）=====
# RISK_PER_TRADE_PERCENT=0.3
# MAX_POSITION_SIZE_PERCENT=0.5
# DEFAULT_LEVERAGE=1.0
```

### 方式 2：使用 Railway CLI

```bash
railway variables set BINANCE_TESTNET=false
railway variables set ENABLE_TRADING=true
```

---

## 🚀 部署流程

### 步驟 1: 推送代碼到 GitHub

```bash
# 提交最新配置
git add .
git commit -m "Configure for small capital live trading"
git push origin main
```

### 步驟 2: 在 Railway 設置環境變數

按照上方的**環境變數設置**部分，在 Railway Dashboard 中設置：
- `BINANCE_TESTNET=false`
- `ENABLE_TRADING=true`

### 步驟 3: 觸發部署

- 如果使用 GitHub Actions：推送代碼會自動部署
- 如果手動部署：Railway 會自動重新部署

### 步驟 4: 監控啟動日誌

在 Railway Dashboard → Logs，確認看到：

```log
✅ 成功啟動標誌：
INFO - Initializing Trading Bot...
INFO - Binance client initialized successfully (LIVE MODE)
INFO - Current account balance: $XX.XX USDT
INFO - Training LSTM model for BTCUSDT...
INFO - Model training completed
INFO - Starting market monitoring (LIVE TRADING ENABLED)
```

---

## 📊 實盤運行監控

### 第一個小時 (0-1h)

**必須監控**：
- ✅ Railway 日誌無錯誤
- ✅ Discord 收到啟動通知
- ✅ Binance 賬戶餘額正確顯示
- ✅ 訂單簿數據正常更新

**如果出現任何錯誤**：立即停止（設置 `ENABLE_TRADING=false`）

### 第一天 (0-24h)

**觀察重點**：
- 📊 交易信號是否合理
- 💰 倉位大小是否符合預期（應該很小）
- 🛡️ 止損是否正確設置
- 📈 勝率和盈虧比

**檢查點**：每 4 小時檢查一次 Discord 和 Railway 日誌

### 第一週 (1-7d)

**績效評估**：
- 總交易次數
- 勝率（應 >45%）
- 最大回撤（應 <5%）
- 夏普比率

**調整決策**：
- 如果表現良好：可考慮增加風險參數
- 如果表現不佳：降低風險或暫停交易

---

## 🎛️ 風險參數調整指南

### 如果想更保守（推薦初期）

在 Railway Variables 設置：
```bash
RISK_PER_TRADE_PERCENT=0.2      # 從 0.3% 降到 0.2%
MAX_POSITION_SIZE_PERCENT=0.3   # 從 0.5% 降到 0.3%
```

### 如果想稍微激進（測試穩定後）

```bash
RISK_PER_TRADE_PERCENT=0.5      # 增加到 0.5%
MAX_POSITION_SIZE_PERCENT=1.0   # 增加到 1.0%
```

⚠️ **永遠不要超過**：
- RISK_PER_TRADE_PERCENT > 2.0%
- MAX_POSITION_SIZE_PERCENT > 5.0%

---

## 🚨 緊急停止程序

### 情況 1: 立即停止交易

如果發生以下情況，立即執行：

**在 Railway Variables 設置**：
```bash
ENABLE_TRADING=false
```

Railway 會自動重啟，機器人將停止下新單（但不會關閉現有倉位）。

**觸發條件**：
- 連續 5 筆以上虧損
- 單日回撤超過 5%
- API 錯誤頻繁發生
- 交易邏輯異常

### 情況 2: 完全關閉系統

在 Railway Dashboard：
- 點擊專案 → Settings → 暫停部署
- 或直接刪除專案

手動在 Binance 平倉所有倉位。

---

## 📱 Discord 通知設置

### 必須啟用的通知

機器人會發送：
- 🤖 **啟動通知** - 確認系統已上線
- 📊 **交易執行** - 每筆買入/賣出的詳情
- ⚠️ **風險警報** - 回撤超過 5%
- 📈 **每日報告** - 當日績效摘要

### Discord 監控最佳實踐

1. 設置 Discord 手機通知
2. 固定機器人通知頻道
3. 每天至少查看 2-3 次
4. 記錄每筆交易的感想

---

## 💡 建議的測試計劃

### 第 1-3 天：觀察模式
- 資金：$50-100 USD
- 風險：0.3% per trade
- 目標：熟悉系統運作
- 行動：僅觀察，不調整參數

### 第 4-7 天：小規模測試
- 資金：可考慮增加到 $200
- 風險：保持 0.3-0.5%
- 目標：驗證策略有效性
- 行動：記錄所有交易並分析

### 第 2-4 週：穩定運行
- 資金：根據績效決定
- 風險：可調整到 0.5-1.0%
- 目標：穩定盈利
- 行動：優化參數

### 1 個月後：評估決策
- 如果勝率 >50%，考慮擴大規模
- 如果勝率 <40%，重新評估策略
- 如果回撤 >10%，降低風險或暫停

---

## ✅ 部署前最終檢查清單

在點擊"部署"之前，再次確認：

### Binance API 安全
- [ ] API Key 已停用提現權限 ✓
- [ ] API Key 僅啟用現貨交易權限
- [ ] （可選）已設置 IP 白名單
- [ ] API Key 和 Secret 已安全儲存在 Railway Variables

### 系統配置
- [ ] Railway 部署區域設為 **Singapore** ✓
- [ ] `BINANCE_TESTNET=false` 
- [ ] `ENABLE_TRADING=true`
- [ ] Discord 通知已設置並測試

### 資金準備
- [ ] 測試資金 $50-100 USD
- [ ] 我能承受全部損失這筆資金
- [ ] 已在 Binance 賬戶存入資金

### 心理準備
- [ ] 我理解交易風險
- [ ] 我會遵守止損紀律
- [ ] 我不會頻繁干預系統
- [ ] 我會記錄和分析每筆交易

---

## 🎯 預期表現（參考）

基於 ICT/SMC + LSTM 策略的保守估計：

| 指標 | 小資金測試目標 |
|------|---------------|
| 月勝率 | 45-55% |
| 盈虧比 | 1.5:1 以上 |
| 月報酬 | 3-8% |
| 最大回撤 | <10% |
| 月交易次數 | 20-40 筆 |

⚠️ **實際結果可能差異很大**，這只是理論估計。

---

## 📞 技術支援

### 查看日誌
```bash
# Railway Dashboard → Logs
# 或下載日誌文件：trading_bot.log
```

### 查看交易記錄
```bash
# Railway Dashboard → 下載 trades.json
# 包含所有交易的完整記錄
```

### 常見問題
- 參考 `README.md` 和 `DEPLOY_INSTRUCTIONS.md`
- 檢查 Discord 錯誤通知
- 查看 Railway 部署日誌

---

## 🎉 準備就緒！

系統已配置為**小資金實盤測試模式**：
- ✅ 保守的風險參數（0.3% per trade）
- ✅ 小倉位限制（0.5% 最大）
- ✅ 無槓桿（1.0x）
- ✅ Discord 實時監控
- ✅ 完整的安全檢查

**記住**：
- 📊 定期監控
- 🛡️ 遵守紀律
- 📝 記錄學習
- ⚠️ 理性決策

祝交易順利！🚀

---

**免責聲明**：此交易系統僅供教育目的。加密貨幣交易風險極高，您可能損失全部資金。使用者需自行承擔所有風險。

# 🔍 機器人未開倉診斷指南

## ✅ 已確認的配置

- **部署位置**：Railway EU（歐洲伺服器）✅
- **交易模式**：ENABLE_TRADING = true（實盤）✅
- **測試網**：BINANCE_TESTNET = false（真實 API）✅
- **Discord 頻道**：1430538906629050500 ✅

---

## 🎯 可能的原因分析

### 原因 1：策略門檻過高（最可能）⭐

**ICT/SMC 策略要求**：
```
✅ 最低信心度：70%
✅ OB 三重驗證（過濾 60%+ 弱信號）
✅ MSB 幅度 ≥0.3%（消除假突破）
✅ 1h 趨勢過濾（避免逆勢交易）
```

**結果**：只有極少數信號能通過所有驗證！

#### 典型情況（日誌應該顯示）：
```
📊 Trading Cycle #15
✅ Fetched data in 1.8s
✅ Analysis complete - 12 signals generated

📊 Top signals (sorted by confidence):
  1. BTCUSDT: BUY, confidence=68.5% ❌ 低於 70%
  2. ETHUSDT: SELL, confidence=65.2% ❌ 低於 70%
  3. SOLUSDT: BUY, confidence=62.1% ❌ 低於 70%

ℹ️  No signals above 70% threshold
```

### 原因 2：市場條件不符合（正常）

**當前市場可能處於**：
- 盤整期（沒有明確趨勢）
- 高波動期（信號不穩定）
- 15m 和 1h 趨勢不一致

**這是正常的**！ICT/SMC 策略是保守策略，寧可錯過也不亂開倉。

### 原因 3：信號被 1h 趨勢過濾（v2.0 優化）

```python
# 策略邏輯
if 15m_signal == BUY 且 1h_trend == bear:
    拒絕信號  # 不在空頭趨勢做多
    
if 15m_signal == SELL 且 1h_trend == bull:
    拒絕信號  # 不在多頭趨勢做空
```

**日誌應該顯示**：
```
BTCUSDT - 1h趨勢: bear
Skipping BUY signal: 1h trend is bearish
```

### 原因 4：OB/MSB 驗證未通過

**OB 三重驗證**：
```
驗證 1：反向 K 棒 ❌
驗證 2：突破幅度 <1.2x ❌
驗證 3：5 根 K 棒回測 ❌
```

如果 OB 無效，信號不會生成。

---

## 📊 如何確認實際原因

### 方法 1：查看 Railway 日誌（最準確）

**訪問**：https://railway.com/dashboard → ravishing-luck → winiswin → Logs

**尋找關鍵字**：

#### 1. 確認機器人正在運行
```bash
# 搜索：Trading Cycle
應該看到：📊 Trading Cycle #1, #2, #3...（每 60 秒一次）
```

#### 2. 確認交易模式
```bash
# 搜索：Trading mode
應該看到：⚙️  Trading mode: 🔴 LIVE
```

#### 3. 查看信號生成情況
```bash
# 搜索：signals generated
看到類似：
✅ Analysis complete - 5 signals generated  ← 有信號
✅ Analysis complete - 0 signals generated  ← 無信號
```

#### 4. 查看被拒絕的信號
```bash
# 搜索：confidence
可能看到：
BTCUSDT: BUY, confidence=68.5% ← 低於 70%
```

#### 5. 查看 1h 趨勢過濾
```bash
# 搜索：1h trend
可能看到：
Skipping BUY signal: 1h trend is bearish
Skipping SELL signal: 1h trend is bullish
```

### 方法 2：使用 Discord 命令

在 Discord 輸入：
```
/status
```

**檢查**：
- 狀態：應該是 ✅ 運行中
- 交易模式：應該是 🔴 實盤模式
- 當前週期：應該在不斷增加

---

## 🔧 調整策略（如果您想要更多交易）

### 選項 1：降低信心度門檻（不推薦）⚠️

**當前門檻**：70%
**可調整為**：65%（但會增加假信號）

**修改文件**：`strategies/ict_smc.py`
```python
# 第 18 行
self.min_confidence_threshold = 65.0  # 從 70.0 降低到 65.0
```

**影響**：
- ✅ 更多交易機會
- ❌ 勝率可能下降
- ❌ 風險增加

### 選項 2：暫時禁用 1h 趨勢過濾（不推薦）⚠️

**修改文件**：`strategies/ict_smc.py`

找到這段代碼（約 412-416 行）：
```python
# === v2.0 優化：1h 趨勢過濾（避免逆勢做多）===
if trend_1h == 'bear':
    logger.debug(f"Skipping BUY signal: 1h trend is bearish")
    pass  # 不在空頭趨勢中做多
```

**註釋掉**：
```python
# if trend_1h == 'bear':
#     logger.debug(f"Skipping BUY signal: 1h trend is bearish")
#     pass
```

**影響**：
- ✅ 允許逆勢交易
- ❌ 預期勝率下降 20-30%

### 選項 3：放寬 OB 驗證（不推薦）⚠️

**當前要求**：
- 突破幅度 >1.2x
- 5 根 K 棒不回測

**可調整為**：
- 突破幅度 >1.0x
- 3 根 K 棒不回測

**影響**：
- ✅ 更多 OB 信號
- ❌ 信號質量下降

---

## 🎯 我的建議

### 建議 1：先觀察 24-48 小時（推薦）⭐

**原因**：
- ✅ ICT/SMC 是保守策略，本來就不會每小時開倉
- ✅ 市場條件會變化，符合條件的機會會出現
- ✅ 當前設定（70% 門檻）是為了高勝率

**預期交易頻率**：
- 保守估計：每天 2-3 筆
- 有時可能一整天沒有符合條件的信號

### 建議 2：查看 Railway 日誌確認原因

**必須確認**：
1. 機器人是否正在運行（有 Trading Cycle 日誌）
2. 是否有信號生成但 <70%
3. 是否被 1h 趨勢過濾

**如果日誌顯示**：
```
✅ Analysis complete - 8 signals generated
📊 Top signals:
  1. BTCUSDT: 68%
  2. ETHUSDT: 65%
```

說明策略正常運作，只是市場暫時沒有高質量機會。

### 建議 3：臨時測試開倉功能

如果您想**立即測試**機器人是否能正常開倉，可以臨時降低門檻：

```python
# 修改 strategies/ict_smc.py 第 18 行
self.min_confidence_threshold = 60.0  # 臨時降低到 60%
```

然後重新部署：
```bash
railway up --service winiswin
```

**注意**：測試完成後記得改回 70%！

---

## 📊 正常運行的日誌示例

```
2025-10-24 10:15:00 - 📊 Trading Cycle #120
2025-10-24 10:15:00 - 📥 Fetching data for 648 symbols...
2025-10-24 10:15:02 - ✅ Fetched data in 1.9s
2025-10-24 10:15:02 - 🔍 Analyzing market data...
2025-10-24 10:15:03 - BTCUSDT - 1h趨勢: bull
2025-10-24 10:15:03 - ETHUSDT - 1h趨勢: bear
2025-10-24 10:15:04 - ✅ Analysis complete - 6 signals generated

📊 Top signals (sorted by confidence):
  1. BTCUSDT: BUY, confidence=68.5%, ROI=1.5
  2. ETHUSDT: SELL, confidence=67.2%, ROI=1.6
  3. SOLUSDT: BUY, confidence=65.8%, ROI=1.4

ℹ️  No signals above 70% threshold
💼 Active positions: 0/3
⏳ Waiting 60s for next cycle...
```

**這是正常的**！策略正在工作，只是等待高質量機會。

---

## 🚨 異常情況（需要處理）

### 異常 1：機器人根本沒運行
```
（日誌完全沒有 "Trading Cycle" 的輸出）
```
**解決**：重新部署 Railway

### 異常 2：顯示模擬模式
```
⚙️  Trading mode: 🟡 SIMULATION
```
**解決**：檢查 Railway 環境變量 ENABLE_TRADING

### 異常 3：API 錯誤
```
APIError: Service unavailable from restricted location
```
**解決**：確認 Railway 服務區域為 EU

### 異常 4：Discord Bot 離線
```
/status 命令無回應
```
**解決**：檢查 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID

---

## ✅ 行動清單

請按順序檢查：

- [ ] 1. 訪問 Railway 日誌查看是否有 "Trading Cycle" 輸出
- [ ] 2. 確認交易模式顯示 "🔴 LIVE"
- [ ] 3. 查看是否有信號生成（數量可能為 0 或 <70%）
- [ ] 4. 在 Discord 使用 `/status` 確認機器人在線
- [ ] 5. 觀察 1-2 小時，看是否有符合條件的信號

**如果以上都正常**，機器人就是在正常運作，只是暫時沒有高質量交易機會！

---

**📅 創建時間**：2025-10-24  
**🎯 目的**：診斷為何機器人未開倉  
**💡 結論**：大多數情況下，這是策略正常運作的表現（保守策略，高門檻）

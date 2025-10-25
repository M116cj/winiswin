# 🌐 全交易對部署指南

## ✅ 已完成的更新

系統已升級為支持所有 Binance USDT 永續合約交易對（648個）。

---

## 🎯 交易對模式

系統現在支援三種交易對選擇模式：

### 模式 1：AUTO（自動 - 推薦）⭐

**說明**：自動獲取成交量最高的前 N 個交易對

**環境變數**：
```bash
SYMBOL_MODE=auto
MAX_SYMBOLS=50
```

**優勢**：
- ✅ 自動選擇最活躍的市場
- ✅ 高流動性，低滑點
- ✅ 平衡資源使用
- ✅ 每次啟動自動更新

**適用場景**：
- 中等資金（$500-5000）
- 希望覆蓋主要市場
- 需要穩定收益

**資源需求**：
- Railway Pro 方案（8GB RAM 推薦）
- API 權重：約 200-300/分鐘
- 記憶體：約 2.5-5GB

---

### 模式 2：ALL（全部交易對）

**說明**：獲取並交易所有 648 個 USDT 永續合約

**環境變數**：
```bash
SYMBOL_MODE=all
```

**優勢**：
- ✅ 最大化交易機會
- ✅ 捕捉所有市場動向
- ✅ 全面分散風險

**⚠️ 資源需求**：
- **Railway Enterprise 方案**（32GB+ RAM）
- API 權重：約 2000-3000/分鐘
- 記憶體：約 30-60GB
- CPU：8+ 核心
- 每小時模型訓練時間：2-3 小時

**成本估算**：
- Railway Enterprise：$200-500/月
- 建議賬戶規模：$10,000+

**⚠️ 警告**：
- 可能觸發 Binance API 速率限制
- 需要大量計算資源
- 僅建議大資金用戶

---

### 模式 3：STATIC（靜態列表）

**說明**：使用預定義的交易對列表

**環境變數**：
```bash
SYMBOL_MODE=static
```

**當前列表**：
```python
['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
```

**優勢**：
- ✅ 資源需求最低
- ✅ 可控和可預測
- ✅ 適合小資金測試

**適用場景**：
- 小資金測試（$50-500）
- 學習和優化階段
- Railway 免費/Hobby 方案

**資源需求**：
- Railway Hobby 方案（512MB RAM）
- API 權重：約 50/分鐘
- 記憶體：約 500MB-1GB

---

## 📊 推薦配置方案

### 方案 1：小資金測試（$50-500）

```bash
SYMBOL_MODE=static
BINANCE_TESTNET=false
ENABLE_TRADING=true
RISK_PER_TRADE_PERCENT=0.3
MAX_POSITION_SIZE_PERCENT=0.5
```

**Railway 方案**：Hobby ($5/月)  
**預期交易對**：5 個  
**預期交易頻率**：每日 0-5 筆

---

### 方案 2：中等資金實盤（$500-5000）⭐ 推薦

```bash
SYMBOL_MODE=auto
MAX_SYMBOLS=50
BINANCE_TESTNET=false
ENABLE_TRADING=true
RISK_PER_TRADE_PERCENT=0.5
MAX_POSITION_SIZE_PERCENT=1.0
```

**Railway 方案**：Pro ($20/月)  
**預期交易對**：50 個  
**預期交易頻率**：每日 5-20 筆  
**記憶體**：約 4-6GB

**優化建議**：
- 每小時重訓模型（分批進行）
- 僅為活躍市場訓練 LSTM
- 監控 API 權重使用

---

### 方案 3：大資金全自動（$10,000+）

```bash
SYMBOL_MODE=all
BINANCE_TESTNET=false
ENABLE_TRADING=true
RISK_PER_TRADE_PERCENT=0.3
MAX_POSITION_SIZE_PERCENT=0.5
```

**Railway 方案**：Enterprise（聯繫 Railway）  
**預期交易對**：648 個  
**預期交易頻率**：每日 50-200 筆  
**記憶體**：約 30-60GB

**優化建議**：
- 使用 Redis 快取市場數據
- 分散式模型訓練
- 專用 PostgreSQL 資料庫
- 多區域部署

---

## 🚀 Railway 部署步驟

### 步驟 1：選擇您的模式

根據資金規模和目標選擇上述方案之一。

### 步驟 2：設置環境變數

在 Railway → Variables 添加：

**基本配置（所有方案）**：
```bash
BINANCE_API_KEY=你的金鑰
BINANCE_SECRET_KEY=你的私鑰
BINANCE_TESTNET=false
ENABLE_TRADING=true
DISCORD_BOT_TOKEN=你的Token
DISCORD_CHANNEL_ID=你的ID
```

**交易對配置（根據方案選擇）**：

**小資金**：
```bash
SYMBOL_MODE=static
```

**中等資金**：
```bash
SYMBOL_MODE=auto
MAX_SYMBOLS=50
```

**大資金**：
```bash
SYMBOL_MODE=all
```

**風險配置（根據資金調整）**：
```bash
RISK_PER_TRADE_PERCENT=0.3
MAX_POSITION_SIZE_PERCENT=0.5
DEFAULT_LEVERAGE=1.0
```

### 步驟 3：升級 Railway 方案（如需要）

**如果選擇 AUTO 或 ALL 模式**：
1. Railway Dashboard → Settings → Plan
2. 升級到 Pro ($20/月) 或更高
3. 配置記憶體限制（建議 8GB）

### 步驟 4：部署並監控

1. Railway 自動部署
2. 查看 Logs 確認：
   ```
   INFO - Mode: AUTO - Fetching top 50 pairs by volume...
   INFO - Loaded 50 trading pairs
   INFO -   1. BTCUSDT: $XX,XXX,XXX (24h volume)
   INFO -   2. ETHUSDT: $XX,XXX,XXX (24h volume)
   ...
   INFO - Training LSTM model for BTCUSDT...
   ```

---

## 📊 性能監控

### 關鍵指標

**API 使用率**：
```
靜態模式（5對）：  ~50 請求/分鐘
自動模式（50對）： ~300 請求/分鐘
全部模式（648對）：~3000 請求/分鐘

Binance 限制：1200 權重/分鐘
```

**記憶體使用**：
```
靜態模式：  500MB - 1GB
自動模式：  4GB - 6GB
全部模式：  30GB - 60GB
```

**模型訓練時間**：
```
單個模型：  ~30-60 秒
5 個交易對： ~5 分鐘
50 個交易對：~45 分鐘
648 個交易對：~8-10 小時
```

### 優化建議

**如果 API 超限**：
```bash
# 減少交易對數量
MAX_SYMBOLS=30

# 或切換到靜態模式
SYMBOL_MODE=static
```

**如果記憶體不足**：
```bash
# 減少交易對
MAX_SYMBOLS=20

# 或增加 Railway 記憶體配額
```

**如果訓練太慢**：
```bash
# 增加重訓間隔（環境變數）
MODEL_RETRAIN_INTERVAL=7200  # 2小時

# 或減少 Epochs
# 修改 main.py: epochs=20
```

---

## 🎯 各模式預期表現

### 靜態模式（5 對）

| 指標 | 值 |
|------|-----|
| 日均交易 | 0-5 筆 |
| 月交易頻率 | 30-100 筆 |
| 資源成本 | $5/月 |
| 勝率目標 | 45-55% |
| 月收益目標 | 3-8% |

### 自動模式（50 對）

| 指標 | 值 |
|------|-----|
| 日均交易 | 5-20 筆 |
| 月交易頻率 | 150-600 筆 |
| 資源成本 | $20/月 |
| 勝率目標 | 45-55% |
| 月收益目標 | 5-12% |

### 全部模式（648 對）

| 指標 | 值 |
|------|-----|
| 日均交易 | 50-200 筆 |
| 月交易頻率 | 1500-6000 筆 |
| 資源成本 | $200-500/月 |
| 勝率目標 | 45-55% |
| 月收益目標 | 8-15% |

⚠️ **以上為理論估計，實際結果可能有顯著差異**

---

## 🔧 動態調整

系統支援在運行時切換模式（需要重啟）：

```bash
# 在 Railway Variables 修改
SYMBOL_MODE=auto → SYMBOL_MODE=static

# 系統會在下次重啟時應用新配置
```

---

## ⚠️ 重要提醒

### 對於 AUTO 和 ALL 模式

1. **API 配額管理**
   - 監控 Binance API 使用情況
   - 準備備用 API 金鑰
   - 設置速率限制警報

2. **記憶體管理**
   - Railway Pro 最低 8GB RAM
   - 監控記憶體使用趨勢
   - 考慮模型壓縮技術

3. **成本控制**
   - Railway 費用會隨資源增加
   - 計算預期收益 vs 成本
   - 小額測試後再擴大

4. **風險分散**
   - 更多交易對 ≠ 更高收益
   - 需要更嚴格的風險管理
   - 建議逐步擴展

---

## 💡 最佳實踐

### 階段式擴展（推薦路徑）

**第 1 週**：
```bash
SYMBOL_MODE=static  # 5 對
```
- 驗證策略有效性
- 優化參數
- 建立信心

**第 2-4 週**：
```bash
SYMBOL_MODE=auto
MAX_SYMBOLS=20  # 20 對
```
- 擴展市場覆蓋
- 觀察績效變化
- 調整風險參數

**第 2-3 月**：
```bash
MAX_SYMBOLS=50  # 50 對
```
- 規模化運營
- 優化資源使用
- 評估是否繼續擴展

**第 6 月+**：
```bash
SYMBOL_MODE=all  # 僅在績效穩定後
```
- 全市場覆蓋
- 機構級運營
- 持續優化

---

## 📚 相關文檔

- **START_DEPLOYMENT.md** - 基礎部署指南
- **RAILWAY_MANUAL_DEPLOY.md** - 手動部署步驟
- **SYSTEM_STATUS_REPORT.md** - 系統狀態報告
- **replit.md** - 專案架構說明

---

## 🆘 故障排除

### 問題 1：API 速率限制

**錯誤**：`Error 429: Too many requests`

**解決**：
```bash
# 減少交易對
MAX_SYMBOLS=30

# 或增加循環間隔（修改 main.py）
await asyncio.sleep(90)  # 從 60 改為 90 秒
```

### 問題 2：記憶體不足

**錯誤**：`MemoryError` 或容器重啟

**解決**：
```bash
# 切換到靜態模式
SYMBOL_MODE=static

# 或升級 Railway 方案
```

### 問題 3：訓練時間過長

**現象**：模型訓練佔用整個循環週期

**解決**：
```bash
# 增加重訓間隔
MODEL_RETRAIN_INTERVAL=7200

# 或減少 Epochs（修改 main.py）
epochs=20
```

---

## 🎉 準備就緒！

系統現已支援：
- ✅ 全部 648 個 USDT 永續合約
- ✅ 三種靈活模式（靜態/自動/全部）
- ✅ 動態成交量排序
- ✅ 獨立 LSTM 模型管理
- ✅ 資源優化配置

**選擇您的模式，開始交易之旅！** 🚀

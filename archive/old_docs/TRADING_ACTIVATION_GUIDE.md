# 🚀 交易機器人啟動指南

## ✅ 當前狀態檢查

### 帳戶讀取功能 - 已就緒 ✅

您的機器人**已經正確配置**了 U 本位合約帳戶讀取功能：

```python
# 位於 main_v3.py 第 203 行
futures_usdt = await loop.run_in_executor(None, self.binance.get_futures_balance)
```

**讀取邏輯** (`binance_client.py`):
1. 優先使用 `futures_account_balance()` 獲取精確的 USDT 餘額
2. 失敗時降級到 `futures_account()` 的 `totalWalletBalance`
3. 自動記錄詳細日誌

---

## ⚠️ 當前限制

### 1. 交易模式：已禁用 ❌

```python
# config.py 第 17 行
ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
```

**當前設置**: `false` (安全模式，僅分析不交易)

### 2. 地理限制：Binance API 訪問受限 ❌

**錯誤信息**:
```
APIError(code=0): Service unavailable from a restricted location 
according to 'b. Eligibility' in https://www.binance.com/en/terms
```

**原因**: Replit 環境的 IP 地址在 Binance 限制區域內

### 3. 測試網模式：已啟用 ⚠️

```python
# config.py 第 9 行
BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
```

**當前設置**: `true` (連接到 Binance 測試網，非真實資金)

---

## 🔧 啟動步驟

### 方案 A: 本地部署 Railway（推薦）

這是解決地理限制的**唯一可靠方案**。

#### 步驟 1: 部署到 Railway EU West

```bash
# 1. 安裝 Railway CLI（如果尚未安裝）
npm i -g @railway/cli

# 2. 登入 Railway
railway login

# 3. 初始化項目
railway init

# 4. 鏈接到 Railway 項目
railway link

# 5. 設置環境變量
railway variables set BINANCE_API_KEY="your_api_key_here"
railway variables set BINANCE_SECRET_KEY="your_secret_key_here"
railway variables set DISCORD_BOT_TOKEN="your_discord_token_here"
railway variables set DISCORD_CHANNEL_ID="your_channel_id_here"

# 6. 啟用交易（可選，建議先測試）
railway variables set ENABLE_TRADING="false"  # 先保持 false 測試
railway variables set BINANCE_TESTNET="false"  # 使用真實 API

# 7. 部署
railway up
```

#### 步驟 2: 選擇歐洲區域

在 Railway 控制台：
1. 進入項目設置
2. 選擇 **EU West** 區域（繞過地理限制）
3. 確認部署

#### 步驟 3: 監控啟動

```bash
# 查看實時日誌
railway logs

# 期待看到：
# ✅ Initialized Binance client in LIVE mode
# ✅ Futures USDT balance: XXX.XX
# ✅ Total Account Balance: $XXX.XX USDT
```

---

### 方案 B: 在當前環境測試（有限功能）

如果您只想**測試代碼邏輯**而不連接真實 API：

#### 修改配置文件

創建或修改 `.env` 文件：

```bash
# 啟用交易模式
ENABLE_TRADING=true

# 保持測試網模式（安全）
BINANCE_TESTNET=true

# API 憑證（即使無法連接也需要）
BINANCE_API_KEY=your_testnet_api_key
BINANCE_SECRET_KEY=your_testnet_secret_key

# Discord 通知（可選）
DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=your_channel_id
```

#### 重啟機器人

```bash
# Replit 會自動重啟 workflow
# 或手動重啟
python main_v3.py
```

**限制**: 
- ❌ 無法連接 Binance API（地理限制）
- ❌ 無法讀取真實帳戶餘額
- ❌ 無法執行任何交易
- ✅ 可以測試代碼邏輯和錯誤處理

---

## 🎯 啟用真實交易（僅在 Railway 部署後）

### ⚠️ 安全檢查清單

在啟用真實交易前，**務必確認**：

- [ ] ✅ 已在 Railway EU West 部署
- [ ] ✅ Binance API 連接成功（檢查日誌）
- [ ] ✅ Futures USDT 帳戶餘額正確顯示
- [ ] ✅ 已完成 3-7 天模擬測試（`ENABLE_TRADING=false`）
- [ ] ✅ 策略表現符合預期
- [ ] ✅ Discord 通知系統正常
- [ ] ✅ API 金鑰**沒有提現權限**
- [ ] ✅ 使用小額資金測試（建議 $100-500）

### 啟用步驟

```bash
# 1. 設置為真實 API（非測試網）
railway variables set BINANCE_TESTNET="false"

# 2. 啟用交易（謹慎！）
railway variables set ENABLE_TRADING="true"

# 3. 重新部署
railway up

# 4. 實時監控
railway logs -f
```

### 監控指標

啟用後，密切監控：

```
📊 關鍵指標:
- 開倉次數 / 小時
- 平均信心度
- 勝率 %
- 盈虧比
- 最大回撤

⚠️ 警告信號:
- 連續虧損 > 3 次 → 暫停檢查
- 單日回撤 > 5% → 立即停止
- 異常高頻開倉 → 檢查策略
- Discord 警告過多 → 調查原因
```

---

## 📊 驗證帳戶讀取

### 檢查日誌

部署成功後，您應該在日誌中看到：

```
2025-10-24 12:00:00 - binance_client - INFO - Initialized Binance client in LIVE mode
2025-10-24 12:00:01 - binance_client - DEBUG - Futures USDT balance (from account_balance): 1234.56
2025-10-24 12:00:01 - __main__ - INFO - 💰 Spot USDT: $100.00
2025-10-24 12:00:01 - __main__ - INFO - 💰 Futures USDT: $1234.56
2025-10-24 12:00:01 - __main__ - INFO - ✅ Total Account Balance: $1334.56 USDT
2025-10-24 12:00:01 - __main__ - INFO - 💼 Capital per position (33.33%): $444.85
```

### 使用 Discord 命令檢查

```
/balance  # 查看實時帳戶餘額
/status   # 查看系統狀態
/positions # 查看當前持倉
```

---

## 🔐 安全建議

### API 金鑰權限設置

在 Binance 創建 API 金鑰時：

```
✅ 必須啟用:
- Enable Reading (讀取權限)
- Enable Futures (合約交易)

❌ 必須禁用:
- Enable Withdrawals (提現權限) ⚠️ 重要！
- Enable Margin (槓桿借貸，非必需)
```

### IP 白名單（推薦）

1. 部署到 Railway 後獲取固定 IP
2. 在 Binance API 設置中添加 IP 白名單
3. 只允許 Railway IP 訪問

### 資金管理

```
保守配置（推薦）:
- 初始資金: $100-500
- 風險/交易: 0.3% ($0.30-1.50)
- 最大倉位: 0.5% ($0.50-2.50)
- 最大同時倉位: 3 個

測試通過後擴展:
- 逐步增加到 $1000-5000
- 保持風險比例不變
- 持續監控表現
```

---

## ❓ 常見問題

### Q1: 為什麼在 Replit 無法連接 Binance？

**A**: Replit 的 IP 地址在 Binance 限制區域內。必須部署到 Railway EU West 或其他不受限制的地區。

### Q2: 測試網和真實網有什麼區別？

**A**: 
- **測試網**: 使用假資金，適合測試策略邏輯
- **真實網**: 使用真實資金，需要謹慎操作

### Q3: ENABLE_TRADING=false 時會發生什麼？

**A**: 
- ✅ 機器人正常運行
- ✅ 分析市場數據
- ✅ 生成交易信號
- ✅ 發送 Discord 通知（模擬模式標記）
- ❌ **不會**執行任何真實交易

### Q4: 如何確認正在讀取 U 本位合約帳戶？

**A**: 檢查日誌中的 "Futures USDT balance" 信息，或使用 Discord `/balance` 命令。

### Q5: 可以同時使用現貨和合約帳戶嗎？

**A**: 可以！機器人會讀取：
- Spot USDT（現貨 USDT）
- Futures USDT（U 本位合約 USDT）
- 計算總餘額並分配資金

---

## 🚀 快速啟動總結

### 推薦路徑（最安全）

```
第 1 步: 部署到 Railway EU West
    ↓
第 2 步: 設置 ENABLE_TRADING=false, BINANCE_TESTNET=false
    ↓
第 3 步: 驗證 API 連接和帳戶餘額讀取
    ↓
第 4 步: 運行 3-7 天模擬測試
    ↓
第 5 步: 分析結果，確認策略表現
    ↓
第 6 步: 啟用 ENABLE_TRADING=true（小額資金）
    ↓
第 7 步: 密切監控，逐步擴大資金
```

---

## 📞 支持

如有問題，檢查：
1. Railway 部署日誌
2. Discord 通知
3. `VERSION_REPORT_v3.0.1.md` 完整文檔
4. `docs/` 目錄下的技術文檔

---

**⚠️ 重要提醒**: 
- 加密貨幣交易有風險，僅投資您能承受損失的資金
- 建議從小額開始，逐步增加
- 持續監控機器人表現
- 定期檢查和優化策略

**✅ 您的機器人已經準備就緒，正在等待部署到無地理限制的環境！**

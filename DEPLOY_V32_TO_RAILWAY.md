# 🚀 部署 v3.2 到 Railway - 完整指南

**目的**: 將修復後的 v3.2 代碼部署到 Railway，解決保證金和止損/止盈問題

**預期結果**:
- ✅ 保證金從 $0.4-0.6 (v3.0) → $30-130 (v3.2，3%-13% 動態保證金)
- ✅ 倉位顯示止損/止盈訂單
- ✅ 版本顯示為 v3.2

---

## 📋 部署前檢查清單

### 1. 驗證本地修復

```bash
# 在 Replit 執行驗證腳本
python verify_v32_fixes.py
```

**預期輸出**:
```
✅ PASSED: 導入驗證
✅ PASSED: 保證金計算
✅ PASSED: 版本號
✅ PASSED: 異步訂單執行
總計: 4/4 項測試通過
🎉 所有驗證通過！v3.2 修復成功！
```

### 2. 確認修復內容

**修復 1: risk_manager.py**
```python
# ❌ 舊代碼（已移除）
from utils.helpers import setup_logger, calculate_position_size

# ✅ 新代碼
from utils.helpers import setup_logger
# 使用類內的 calculate_position_size 方法（v3.2 邏輯）
```

**修復 2: services/execution_service.py**
```python
# ❌ 舊代碼
sl_order = self.binance.set_stop_loss_order(...)

# ✅ 新代碼
loop = asyncio.get_event_loop()
sl_order = await loop.run_in_executor(
    None,
    self.binance.set_stop_loss_order,
    ...
)
```

**修復 3: main_v3.py**
```python
# ❌ 舊代碼
logger.info("Initializing Cryptocurrency Trading Bot v3.0")

# ✅ 新代碼
logger.info("Initializing Cryptocurrency Trading Bot v3.2")
logger.info("🚀 Version 3.2 Features:")
logger.info("  ✅ Dynamic Margin Sizing (3%-13% based on confidence)")
logger.info("  ✅ Win-Rate Based Leverage (3-20x based on performance)")
logger.info("  ✅ Exchange-Level Stop-Loss/Take-Profit Protection")
logger.info("  ✅ Comprehensive Trade Logging for XGBoost ML")
```

---

## 🔧 部署步驟

### 步驟 1: 提交代碼到 Git

```bash
# 1. 查看修改
git status

# 2. 添加所有修改
git add .

# 3. 提交修改
git commit -m "🐛 Fix v3.2 critical bugs: margin calculation & stop-loss/take-profit orders

- Fixed RiskManager importing old calculate_position_size (now uses 3%-13% dynamic margin)
- Fixed ExecutionService async order placement for stop-loss/take-profit
- Updated version to v3.2 with feature banner
- Added verification script verify_v32_fixes.py

Impact:
- Positions now use $30-130 margin (was $0.4-0.6)
- Stop-loss/take-profit orders now placed correctly on Binance
- All fixes verified with test suite (4/4 passed)"

# 4. 推送到遠程倉庫
git push origin main
```

### 步驟 2: 部署到 Railway

**方法 A: 自動部署（如果已配置）**

Railway 會自動檢測到 GitHub 更新並重新部署。

1. 前往 Railway Dashboard: https://railway.app/
2. 找到你的專案
3. 點擊 "Deployments" 查看部署進度
4. 等待部署完成（通常 2-5 分鐘）

**方法 B: 手動觸發部署**

```bash
# 安裝 Railway CLI（如果尚未安裝）
npm install -g @railway/cli

# 登入 Railway
railway login

# 連接到專案
railway link

# 手動部署
railway up

# 或者重啟服務
railway restart
```

### 步驟 3: 監控部署日誌

```bash
# 實時查看日誌
railway logs --follow
```

**查找關鍵日誌**:

1. **啟動日誌**（確認版本）:
```
======================================================================
Initializing Cryptocurrency Trading Bot v3.2
======================================================================
🚀 Version 3.2 Features:
  ✅ Dynamic Margin Sizing (3%-13% based on confidence)
  ✅ Win-Rate Based Leverage (3-20x based on performance)
  ✅ Exchange-Level Stop-Loss/Take-Profit Protection
  ✅ Comprehensive Trade Logging for XGBoost ML
======================================================================
```

2. **倉位加載日誌**（確認同步）:
```
🔍 Loading current positions from Binance API...
✅ Successfully loaded X positions from Binance
```

3. **保證金計算日誌**（確認新邏輯）:
```
💰 保證金計算: 信心度=85.0% → 保證金比例=8.00%
📊 倉位計算: BTCUSDT - 總資金=$1000.00, 保證金比例=8.00%, 保證金=$80.00, 槓桿=10.00x, 倉位價值=$800.00
```

4. **止損/止盈設置日誌**（確認保護訂單）:
```
🔒 Setting exchange-level protection for BTCUSDT LONG: SL @ 49000.00, TP @ 51000.00
✅ Stop-loss order set successfully for BTCUSDT: 12345678
✅ Take-profit order set successfully for BTCUSDT: 87654321
```

---

## ✅ 驗證部署成功

### 1. 檢查版本號

```bash
# 查看啟動日誌
railway logs | grep "Cryptocurrency Trading Bot"
```

**預期輸出**:
```
Initializing Cryptocurrency Trading Bot v3.2  ✅
```

**如果看到 v3.0**:
```
❌ Railway 仍在運行舊代碼
解決方案：清除 Railway 緩存並重新部署
```

### 2. 檢查保證金計算

```bash
# 查找保證金計算日誌
railway logs | grep "保證金計算"
```

**預期輸出**（v3.2）:
```
💰 保證金計算: 信心度=85.0% → 保證金比例=8.00%  ✅
保證金=$80.00  ✅ (3%-13% 範圍內)
```

**錯誤輸出**（v3.0）:
```
保證金=$0.60  ❌ (舊邏輯)
```

### 3. 檢查止損/止盈訂單

**選項 A: 查看 Railway 日誌**
```bash
railway logs | grep "Stop-loss order set"
railway logs | grep "Take-profit order set"
```

**預期輸出**:
```
✅ Stop-loss order set successfully for BTCUSDT: 12345678  ✅
✅ Take-profit order set successfully for BTCUSDT: 87654321  ✅
```

**選項 B: 檢查幣安倉位**

1. 登入幣安網頁
2. 前往 **期貨交易** → **當前倉位**
3. 點擊倉位查看詳情

**預期看到**:
```
止損價格: 顯示具體價格  ✅
止盈價格: 顯示具體價格  ✅
```

**如果沒看到**:
```
止損價格: --  ❌
止盈價格: --  ❌

說明: 止損/止盈訂單未設置
原因: 可能異步調用仍有問題
```

### 4. 監控下一個交易週期

```bash
# 實時監控
railway logs --follow
```

等待下一個 **開倉事件** 並檢查：

**完整的開倉日誌應包含**:
```
🎯 Opening position: BTCUSDT BUY @ 50000.00
💰 保證金計算: 信心度=85.0% → 保證金比例=8.00%
📊 倉位計算: ... 保證金=$80.00, 槓桿=10.00x ...  ✅
✅ Position opened successfully
🔒 Setting exchange-level protection for BTCUSDT LONG  ✅
✅ Stop-loss order set successfully for BTCUSDT  ✅
✅ Take-profit order set successfully for BTCUSDT  ✅
```

---

## 🔍 故障排除

### 問題 1: Railway 仍顯示 v3.0

**症狀**:
```
Initializing Cryptocurrency Trading Bot v3.0  ❌
```

**原因**: Railway 使用了緩存的舊代碼

**解決方案**:
```bash
# 1. 清除 Railway 緩存
railway restart --clear-cache

# 2. 或者重新部署
railway up --force

# 3. 監控日誌
railway logs --follow
```

### 問題 2: 保證金仍是 $0.4-0.6

**症狀**:
```
保證金=$0.60  ❌
```

**原因**: Git 推送可能失敗或 Railway 未拉取最新代碼

**解決方案**:
```bash
# 1. 確認 Git 推送成功
git log -1  # 查看最新提交

# 2. 確認 Railway 拉取最新代碼
railway logs | head -20  # 查看部署日誌

# 3. 如果需要，強制重新部署
railway restart --clear-cache
railway up --force
```

### 問題 3: 止損/止盈仍未設置

**症狀**:
```
幣安倉位沒有顯示止損/止盈
```

**檢查日誌**:
```bash
railway logs | grep "Setting exchange-level protection"
railway logs | grep "Stop-loss order set"
```

**可能原因**:

1. **訂單失敗（API 錯誤）**:
```
❌ Failed to set stop-loss for BTCUSDT
Error: APIError(code=-1111): Precision is over the maximum defined
```

**解決**: 檢查數量精度和最小名義價值

2. **異步調用錯誤**:
```
TypeError: 'coroutine' object is not callable
```

**解決**: 確認代碼使用 `await loop.run_in_executor`

3. **權限問題**:
```
Error: APIError(code=-2015): Invalid API-key, IP, or permissions
```

**解決**: 確認 API Key 有期貨交易權限

---

## 📊 預期結果對比

### 部署前（v3.0）

**幣安倉位顯示**:
```
BTCUSDT LONG
保證金: $0.40  ❌
止損: --  ❌
止盈: --  ❌
```

**Railway 日誌**:
```
Initializing Cryptocurrency Trading Bot v3.0  ❌
保證金=$0.60  ❌
```

### 部署後（v3.2）

**幣安倉位顯示**:
```
BTCUSDT LONG
保證金: $80.00  ✅ (8% × $1000)
止損: $49,000.00  ✅
止盈: $51,000.00  ✅
```

**Railway 日誌**:
```
Initializing Cryptocurrency Trading Bot v3.2  ✅
🚀 Version 3.2 Features:
  ✅ Dynamic Margin Sizing (3%-13% based on confidence)
💰 保證金計算: 信心度=85.0% → 保證金比例=8.00%  ✅
📊 倉位計算: ... 保證金=$80.00 ...  ✅
✅ Stop-loss order set successfully  ✅
✅ Take-profit order set successfully  ✅
```

---

## 🎯 部署檢查清單

### 部署前
- [ ] 運行 `python verify_v32_fixes.py`（4/4 測試通過）
- [ ] 確認代碼已提交到 Git
- [ ] 確認代碼已推送到遠程倉庫

### 部署中
- [ ] Railway 顯示新部署進度
- [ ] 部署成功完成（無錯誤）

### 部署後
- [ ] Railway 日誌顯示 "v3.2"
- [ ] 保證金計算日誌顯示 3%-13% 範圍
- [ ] 止損/止盈訂單設置成功
- [ ] 幣安倉位顯示止損/止盈價格

---

## 📞 需要幫助？

如果部署過程中遇到問題：

1. **檢查完整錯誤日誌**:
```bash
railway logs | grep -i error | tail -50
```

2. **檢查倉位加載**:
```bash
railway logs | grep "Loading current positions" -A 10
```

3. **檢查環境變數**:
```bash
railway variables list
```

4. **重啟服務**:
```bash
railway restart
```

---

## ✅ 成功標準

部署成功的標準：

1. ✅ Railway 啟動日誌顯示 "Cryptocurrency Trading Bot v3.2"
2. ✅ 保證金計算日誌顯示 $30-130 範圍（3%-13%）
3. ✅ 止損/止盈訂單設置成功日誌
4. ✅ 幣安倉位顯示具體的止損/止盈價格
5. ✅ 無重複的導入錯誤或異步調用錯誤

**全部通過 = 🎉 v3.2 部署成功！**

---

**最後更新**: 2025-10-24  
**版本**: v3.2  
**狀態**: 已驗證並準備部署

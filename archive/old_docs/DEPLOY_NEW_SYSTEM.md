# 🚀 部署新的保證金和槓桿系統到 Railway

## ⚠️ 為什麼需要重新部署？

您在 Railway 上看到的保證金 0.4/0.6 是因為還在運行**舊版本代碼**。

新系統已經在 Replit 上完成，但 Railway 需要手動重新部署才能更新。

---

## 📊 新舊系統對比

### 舊系統（當前 Railway 運行的版本）
- 保證金計算：基於 0.3% 風險
- 結果：保證金約 $0.4-0.6（太小）
- 槓桿：固定或基於信心度

### 新系統（v3.2）
- ✅ **保證金：3%-13%**（基於信心度）
- ✅ **槓桿：3-20x**（基於勝率）
- ✅ **MIN_NOTIONAL 修復**（+2% 安全邊際）
- ✅ **完整交易記錄**（供 XGBoost 學習）

---

## 🔧 部署步驟

### 步驟 1: 連接到 Railway 專案

```bash
railway link
```

選擇您的專案：`ravishing-luck`

### 步驟 2: 推送最新代碼

```bash
# 確認最新代碼已提交
git status

# 部署到 Railway
railway up
```

### 步驟 3: 驗證環境變量

確保以下變量已設置（新增的配置）：

```bash
# 查看當前變量
railway variables

# 如果缺少以下變量，請設置：
railway variables set MARGIN_MIN_PERCENT=3.0
railway variables set MARGIN_MAX_PERCENT=13.0
railway variables set LEVERAGE_MODE=win_rate
railway variables set MIN_LEVERAGE=3.0
railway variables set MAX_LEVERAGE=20.0
```

### 步驟 4: 重啟服務

```bash
# 重啟以應用更新
railway restart
```

### 步驟 5: 監控日誌

```bash
railway logs --follow
```

---

## ✅ 確認部署成功

在日誌中查找以下關鍵信息：

### 1. 勝率槓桿計算
```
🎯 勝率槓桿計算: 勝率=X.X% (X/X 勝), 風險等級=高, 槓桿=XX.XXx
```

### 2. 保證金計算
```
💰 保證金計算: 信心度=XX.X% → 保證金比例=X.XX%
```

### 3. 倉位計算（新格式）
```
📊 倉位計算: SYMBOL - 
   總資金=$XX.XX, 
   保證金比例=X.XX%, 
   保證金=$X.XX,          ← 應該是 $3-$13 範圍（如果總資金 $100）
   槓桿=XX.XXx, 
   倉位價值=$XX.XX, 
   數量=X.XXXXXX
```

### 4. 開倉通知
Discord 通知應該顯示：
- 保證金：$3-$13（3%-13% 範圍）
- 槓桿：3-20x（基於勝率）
- 倉位價值：保證金 × 槓桿

---

## 🧪 測試新系統

部署後，等待第一個交易信號：

**預期結果（假設總資金 $10,000）：**

| 信心度 | 勝率 | 保證金比例 | 保證金 | 槓桿 | 倉位價值 |
|--------|------|------------|--------|------|----------|
| 70% | 無記錄 | 3% | $300 | 3x | $900 |
| 85% | 58% | 8% | $800 | 14x | $11,200 |
| 95% | 67% | 11.5% | $1,150 | 16x | $18,400 |

**舊系統（您目前看到的）：**
- 保證金：$0.4-0.6 ❌
- 倉位太小無法滿足 MIN_NOTIONAL

---

## ⚠️ 重要提醒

1. **停止交易後再部署**
   ```bash
   railway variables set ENABLE_TRADING=false
   railway up
   # 等待部署完成後再啟用
   railway variables set ENABLE_TRADING=true
   ```

2. **確認 MIN_NOTIONAL 修復已生效**
   - 日誌應該顯示：`safe margin: +2%`
   - 不應該再看到 MIN_NOTIONAL 錯誤

3. **驗證勝率系統**
   - 初期會使用保守槓桿 3x（交易記錄不足）
   - 累積 10+ 筆交易後，槓桿會根據勝率調整

---

## 📞 故障排除

### 問題：部署後還是顯示舊保證金
```bash
# 強制重啟
railway restart

# 檢查代碼版本
railway logs | grep "Cryptocurrency Trading Bot"
```

### 問題：找不到 Railway 專案
```bash
# 重新連接
railway logout
railway login
railway link
```

### 問題：環境變量未生效
```bash
# 刪除並重新設置
railway variables delete MARGIN_MIN_PERCENT
railway variables set MARGIN_MIN_PERCENT=3.0
railway restart
```

---

**完成部署後，您應該看到保證金從 $0.4-0.6 變為 $3-$13（假設總資金 $100）** ✅

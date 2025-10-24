# 🔍 如何檢查 Railway 端的版本

## 📊 當前狀態分析

### Replit 環境（本地）
```
✅ 版本: v3.0
⚠️ 狀態: 地理限制，無法訪問 Binance API
📊 監控: 僅 2 個交易對（測試模式）
🔴 問題: "Service unavailable from a restricted location"
```

**注意**: Replit 無法運行實盤交易，必須使用 Railway！

---

## 🚀 檢查 Railway 版本的方法

### 方法 1: 查看 Railway 日誌（推薦）

```bash
# 連接到 Railway 專案
railway link

# 查看實時日誌
railway logs --follow
```

**在日誌中查找版本信息**：

#### v3.0 版本日誌特徵：
```
Initializing Cryptocurrency Trading Bot v3.0
📥 Fetching data for 526 symbols...
```

**無保證金/槓桿計算日誌**：
- ❌ 沒有 "保證金計算" 
- ❌ 沒有 "勝率槓桿計算"
- ❌ 沒有 "倉位計算" 詳細信息

#### v3.2 版本日誌特徵：
```
Initializing Cryptocurrency Trading Bot v3.2
💰 保證金計算: 信心度=85.0% → 保證金比例=8.00%
🎯 勝率槓桿計算: 勝率=58.3% (7/12 勝), 風險等級=中高, 槓桿=14.17x
📊 倉位計算: BTCUSDT - 
   總資金=$10000.00, 
   保證金比例=8.00%, 
   保證金=$800.00,
   槓桿=14.17x, 
   倉位價值=$11336.00
```

**有完整的保證金/槓桿計算日誌** ✅

---

### 方法 2: 檢查 GitHub 最新提交

```bash
# 查看最新提交
git log --oneline -1

# 查看主文件版本
git show HEAD:main_v3.py | grep -E "version|v3\."
```

**確認最新提交包含 v3.2 更新**：
- 動態保證金 (3%-13%)
- 勝率槓桿 (3-20x)
- MIN_NOTIONAL 修復

---

### 方法 3: Railway CLI 檢查部署狀態

```bash
# 查看當前部署
railway status

# 查看環境變量（確認新變量是否存在）
railway variables

# 查找 v3.2 新增的變量
railway variables | grep -E "MARGIN|LEVERAGE"
```

**v3.2 新增的環境變量**：
```
MARGIN_MIN_PERCENT=3.0
MARGIN_MAX_PERCENT=13.0
LEVERAGE_MODE=win_rate
MIN_LEVERAGE=3.0
MAX_LEVERAGE=20.0
```

如果這些變量**不存在**，說明 v3.2 未部署或未配置。

---

## 🎯 確認 v3.2 是否已部署的關鍵指標

### ✅ v3.2 已部署的標誌

1. **日誌中有保證金計算**：
   ```
   💰 保證金計算: 信心度=XX.X% → 保證金比例=X.XX%
   ```

2. **日誌中有勝率槓桿計算**：
   ```
   🎯 勝率槓桿計算: 勝率=XX.X% → 槓桿=XX.XXx
   ```

3. **倉位計算顯示新格式**：
   ```
   📊 倉位計算: 保證金=$XXX.XX, 槓桿=XX.XXx, 倉位價值=$X,XXX.XX
   ```

4. **保證金範圍正確**：
   - 對於 $10,000 賬戶：保證金應為 **$300-$1,300**
   - 對於 $100 賬戶：保證金應為 **$3-$13**

### ❌ v3.0 舊版本的標誌

1. **日誌中沒有保證金計算**
2. **日誌中沒有勝率槓桿計算**
3. **保證金顯示為 $0.4-$0.6**（基於固定 0.3% 風險）
4. **沒有 v3.2 環境變量**

---

## 🔧 如果 Railway 還是舊版本，如何更新？

### 步驟 1: 確認 GitHub 已更新

```bash
# 查看本地版本
cat main_v3.py | grep "version"

# 推送到 GitHub（如果尚未推送）
git add .
git commit -m "Deploy v3.2 with dynamic margin and win-rate leverage"
git push origin main
```

### 步驟 2: 觸發 Railway 重新部署

**選項 A: 通過 Railway CLI**
```bash
railway link
railway up
```

**選項 B: 通過 GitHub 集成（自動部署）**
- Railway 應該自動檢測到新提交並重新部署
- 查看 Railway Dashboard → Deployments 確認

**選項 C: 手動觸發部署**
```bash
# 在 Railway Dashboard 點擊 "Redeploy"
```

### 步驟 3: 設置 v3.2 環境變量

```bash
railway variables set MARGIN_MIN_PERCENT=3.0
railway variables set MARGIN_MAX_PERCENT=13.0
railway variables set LEVERAGE_MODE=win_rate
railway variables set MIN_LEVERAGE=3.0
railway variables set MAX_LEVERAGE=20.0
```

### 步驟 4: 重啟服務

```bash
railway restart
```

### 步驟 5: 驗證部署

```bash
# 監控日誌
railway logs --follow

# 查找 v3.2 特徵日誌
railway logs | grep -E "保證金計算|勝率槓桿|v3.2"
```

---

## 📊 快速檢查腳本

創建檔案 `check_railway_version.sh`：

```bash
#!/bin/bash

echo "🔍 檢查 Railway 版本..."

# 連接到 Railway
railway link

# 查看最新 100 行日誌
echo ""
echo "📊 最新日誌："
railway logs --tail 100 > /tmp/railway_logs.txt

# 檢查版本特徵
echo ""
echo "✅ 檢查 v3.2 特徵："

if grep -q "保證金計算" /tmp/railway_logs.txt; then
    echo "  ✅ 找到保證金計算日誌"
else
    echo "  ❌ 未找到保證金計算日誌"
fi

if grep -q "勝率槓桿" /tmp/railway_logs.txt; then
    echo "  ✅ 找到勝率槓桿計算日誌"
else
    echo "  ❌ 未找到勝率槓桿計算日誌"
fi

if grep -q "倉位計算" /tmp/railway_logs.txt; then
    echo "  ✅ 找到倉位計算日誌"
else
    echo "  ❌ 未找到倉位計算日誌"
fi

# 檢查環境變量
echo ""
echo "🔧 檢查環境變量："
railway variables | grep -E "MARGIN|LEVERAGE" || echo "  ❌ 未找到 v3.2 環境變量"

echo ""
echo "📋 完整日誌已保存到: /tmp/railway_logs.txt"
```

使用方法：
```bash
chmod +x check_railway_version.sh
./check_railway_version.sh
```

---

## 🆘 常見問題

### Q: GitHub 已更新，但 Railway 還是舊版本？

**A**: Railway 可能沒有自動部署，手動觸發：
```bash
railway up
```

### Q: Railway 日誌中沒有保證金計算？

**A**: 檢查兩個可能原因：
1. **代碼未更新**：重新部署
2. **環境變量缺失**：設置 v3.2 變量

### Q: 如何確認 Railway 運行的是哪個版本？

**A**: 查看啟動日誌：
```bash
railway logs | head -50 | grep "Cryptocurrency Trading Bot"
```

應該顯示：
- v3.0: `Cryptocurrency Trading Bot v3.0`
- v3.2: `Cryptocurrency Trading Bot v3.2` （如果更新了主文件版本號）

---

## ✅ 總結

要確認 Railway 是否運行 v3.2：

1. ✅ **查看日誌** → 檢查保證金/槓桿計算
2. ✅ **檢查環境變量** → 確認 v3.2 變量存在
3. ✅ **驗證保證金範圍** → 應為 $3-$13（$100 賬戶）

如果都沒有，執行重新部署流程！

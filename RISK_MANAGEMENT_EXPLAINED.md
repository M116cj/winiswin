# 🎯 風險管理與倉位計算邏輯詳解

## 📊 概覽

這個交易機器人採用**雙重保護機制**：
1. **基於風險百分比的倉位計算** - 控制每筆交易的最大損失
2. **最大倉位限制** - 避免單筆交易佔用過多資金

---

## 💰 當前風險參數（保守設置）

```python
RISK_PER_TRADE_PERCENT = 0.3%     # 每筆交易最大風險
MAX_POSITION_SIZE_PERCENT = 0.5%  # 最大倉位大小
DEFAULT_LEVERAGE = 1.0x           # 無槓桿
STOP_LOSS_ATR_MULTIPLIER = 2.0    # 止損距離（2倍ATR）
TAKE_PROFIT_ATR_MULTIPLIER = 3.0  # 止盈距離（3倍ATR）
```

---

## 🧮 倉位計算公式（核心邏輯）

### 步驟 1: 計算基於風險的倉位大小

```python
# utils/helpers.py - 第 14-20 行

def calculate_position_size(account_balance, risk_percent, entry_price, stop_loss_price):
    # 1. 計算風險金額
    risk_amount = account_balance * (risk_percent / 100)
    
    # 2. 計算價格差距（止損距離）
    price_diff = abs(entry_price - stop_loss_price)
    
    # 3. 計算倉位大小
    position_size = risk_amount / price_diff
    
    return position_size
```

### 步驟 2: 應用最大倉位限制

```python
# risk_manager.py - 第 49-52 行

# 計算最大允許的倉位價值
max_position_value = account_balance * (max_position_size / 100)

# 轉換為數量
max_quantity = max_position_value / entry_price

# 取較小值（雙重保護）
final_position_size = min(position_size, max_quantity)
```

---

## 📐 實際計算範例

### 範例 1: 標準交易（BTC）

**假設條件**:
- 賬戶餘額: $10,000
- 風險百分比: 0.3%
- 最大倉位: 0.5%
- 入場價格: $50,000
- 止損價格: $49,000（止損距離 $1,000）

**計算過程**:

#### Step 1: 基於風險的倉位計算
```
風險金額 = $10,000 × 0.3% = $30
止損距離 = |$50,000 - $49,000| = $1,000
倉位大小 = $30 ÷ $1,000 = 0.03 BTC
```

#### Step 2: 檢查最大倉位限制
```
最大倉位價值 = $10,000 × 0.5% = $50
最大數量 = $50 ÷ $50,000 = 0.001 BTC
```

#### Step 3: 取較小值
```
最終倉位 = min(0.03, 0.001) = 0.001 BTC
```

**結果**:
- ✅ **開倉**: 0.001 BTC（$50）
- ✅ **風險**: 如果觸及止損，最大損失 = $1
- ✅ **佔用資金**: $50（0.5% 的賬戶）
- ✅ **實際風險**: $1（0.01% 的賬戶）

---

### 範例 2: 緊湊止損（ETH）

**假設條件**:
- 賬戶餘額: $10,000
- 風險百分比: 0.3%
- 最大倉位: 0.5%
- 入場價格: $3,000
- 止損價格: $2,970（止損距離 $30）

**計算過程**:

#### Step 1: 基於風險的倉位計算
```
風險金額 = $10,000 × 0.3% = $30
止損距離 = |$3,000 - $2,970| = $30
倉位大小 = $30 ÷ $30 = 1.0 ETH
```

#### Step 2: 檢查最大倉位限制
```
最大倉位價值 = $10,000 × 0.5% = $50
最大數量 = $50 ÷ $3,000 = 0.0167 ETH
```

#### Step 3: 取較小值
```
最終倉位 = min(1.0, 0.0167) = 0.0167 ETH
```

**結果**:
- ✅ **開倉**: 0.0167 ETH（$50）
- ✅ **風險**: 如果觸及止損，最大損失 = $0.50
- ✅ **佔用資金**: $50（0.5%）
- ✅ **實際風險**: $0.50（0.005%）

> **重點**: 即使止損很緊（只有 $30），最大倉位限制仍然保護你不會過度投入。

---

## 🎯 止損/止盈計算（基於 ATR）

### 什麼是 ATR？

**ATR (Average True Range)** = 平均真實波動範圍
- 衡量市場波動性的指標
- 數值越大 = 市場波動越大
- 用於設置動態的止損/止盈距離

### 止損計算

```python
# risk_manager.py - 第 57-73 行

def calculate_stop_loss(entry_price, atr, direction='LONG'):
    multiplier = 2.0  # STOP_LOSS_ATR_MULTIPLIER
    
    if direction == 'LONG':
        stop_loss = entry_price - (atr * multiplier)
    else:  # SHORT
        stop_loss = entry_price + (atr * multiplier)
    
    return stop_loss
```

### 止盈計算

```python
# risk_manager.py - 第 75-91 行

def calculate_take_profit(entry_price, atr, direction='LONG'):
    multiplier = 3.0  # TAKE_PROFIT_ATR_MULTIPLIER
    
    if direction == 'LONG':
        take_profit = entry_price + (atr * multiplier)
    else:  # SHORT
        take_profit = entry_price - (atr * multiplier)
    
    return take_profit
```

---

## 📊 ATR 止損/止盈範例

**假設條件**:
- BTC 當前價格: $50,000
- ATR（1小時）: $500
- 方向: LONG（做多）

**計算**:
```
止損 = $50,000 - ($500 × 2.0) = $49,000
止盈 = $50,000 + ($500 × 3.0) = $51,500
```

**盈虧比**:
```
風險: $1,000（入場 → 止損）
回報: $1,500（入場 → 止盈）
盈虧比: 1.5:1（每冒 $1 風險，可能賺 $1.5）
```

---

## 🔒 多層安全機制

### 1. 資料驗證（防止錯誤）

```python
# risk_manager.py - 第 30-36 行

# 檢查 None 值
if entry_price is None or stop_loss_price is None:
    return 0

# 檢查 NaN（Not a Number）
if np.isnan(entry_price) or np.isnan(stop_loss_price):
    return 0
```

### 2. 倉位驗證（防止異常值）

```python
# risk_manager.py - 第 45-47 行

if np.isnan(position_size) or position_size <= 0:
    logger.error(f"Invalid position size calculated: {position_size}")
    return 0
```

### 3. 重複開倉保護

```python
# risk_manager.py - 第 93-98 行

def can_open_position(symbol):
    if symbol in self.open_positions:
        logger.warning(f"Position already open for {symbol}")
        return False
    return True
```

### 4. 回撤監控（警報系統）

```python
# risk_manager.py - 第 20-27 行

def update_balance(new_balance):
    # 更新峰值餘額
    if new_balance > self.peak_balance:
        self.peak_balance = new_balance
    
    # 計算回撤百分比
    current_drawdown = ((self.peak_balance - new_balance) / self.peak_balance) * 100
    
    # 記錄最大回撤
    if current_drawdown > self.max_drawdown:
        self.max_drawdown = current_drawdown
```

---

## 💡 實際交易流程

### 完整的風險管理循環

```
1. 策略生成信號
   ↓
2. 計算 ATR（波動性）
   ↓
3. 計算止損價格 = 入場 - (2 × ATR)
   ↓
4. 計算倉位大小:
   - 基於風險: $30 ÷ 止損距離
   - 最大倉位: 0.5% 賬戶
   - 取較小值
   ↓
5. 檢查安全性:
   - 是否已有該交易對的倉位？
   - 倉位大小是否合理？
   - 止損/止盈是否有效？
   ↓
6. 執行交易（如果 ENABLE_TRADING=true）
   ↓
7. 持續監控:
   - 每個循環檢查價格
   - 觸及止損/止盈自動平倉
   - 更新餘額和回撤
```

---

## 📈 為什麼這樣設計？

### 保守參數的原因

| 參數 | 值 | 原因 |
|------|-----|------|
| **風險/交易** | 0.3% | 即使連續虧損 10 筆，只損失 3% |
| **最大倉位** | 0.5% | 限制單筆交易的資金暴露 |
| **槓桿** | 1.0x | 避免爆倉風險，適合小資金測試 |
| **止損倍數** | 2.0 ATR | 給交易足夠的"呼吸空間" |
| **止盈倍數** | 3.0 ATR | 確保盈虧比 > 1:1 |

### 雙重保護的好處

```
範例: BTC $50,000，止損 $49,000

僅基於風險（0.3%）:
  → 可能開倉 0.03 BTC = $1,500（15% 賬戶！）
  
加上最大倉位限制（0.5%）:
  → 實際開倉 0.001 BTC = $50（0.5% 賬戶）✅
```

**結論**: 最大倉位限制防止了過度集中風險！

---

## 🎯 連續虧損情境分析

### 情境 1: 10 筆連續虧損（最壞情況）

```
初始資金: $10,000

交易 1: 虧損 $30 → 餘額 $9,970
交易 2: 虧損 $29.91 → 餘額 $9,940.09
交易 3: 虧損 $29.82 → 餘額 $9,910.27
交易 4: 虧損 $29.73 → 餘額 $9,880.54
交易 5: 虧損 $29.64 → 餘額 $9,850.90
交易 6: 虧損 $29.55 → 餘額 $9,821.35
交易 7: 虧損 $29.46 → 餘額 $9,791.89
交易 8: 虧損 $29.38 → 餘額 $9,762.51
交易 9: 虧損 $29.29 → 餘額 $9,733.22
交易 10: 虧損 $29.20 → 餘額 $9,704.02

總損失: $295.98（-2.96%）
```

**結論**: 即使 10 連虧，賬戶只損失 3%，仍有 97% 資金！

---

### 情境 2: 50% 勝率，盈虧比 1.5:1

```
100 筆交易:
  → 50 筆盈利 × $45 = +$2,250
  → 50 筆虧損 × $30 = -$1,500
  
淨利潤: $750（+7.5%）
```

**結論**: 只要勝率 ≥ 50%，系統就能盈利！

---

## 🔧 可調整參數

### 如果想要更激進（不推薦新手）

```env
RISK_PER_TRADE_PERCENT=1.0        # 每筆 1%
MAX_POSITION_SIZE_PERCENT=2.0     # 最大 2%
DEFAULT_LEVERAGE=2.0              # 2倍槓桿
```

**風險**: 10 連虧 = -10%，更快盈利但也更快虧損

### 如果想要更保守

```env
RISK_PER_TRADE_PERCENT=0.1        # 每筆 0.1%
MAX_POSITION_SIZE_PERCENT=0.2     # 最大 0.2%
DEFAULT_LEVERAGE=1.0              # 無槓桿
```

**好處**: 100 連虧才損失 10%，但盈利也較慢

---

## 📊 性能追蹤

### RiskManager 自動記錄的指標

```python
# risk_manager.py - 第 169-181 行

def get_performance_stats():
    return {
        'account_balance': 當前餘額,
        'total_trades': 總交易數,
        'winning_trades': 盈利交易,
        'losing_trades': 虧損交易,
        'win_rate': 勝率（%）,
        'total_profit': 總盈虧（$）,
        'max_drawdown': 最大回撤（%）,
        'roi': 投資回報率（%）
    }
```

### 每筆交易的盈虧計算

```python
# risk_manager.py - 第 123-126 行

# 做多（LONG）盈虧
pnl = (exit_price - entry_price) × quantity

# 做空（SHORT）盈虧
pnl = (entry_price - exit_price) × quantity

# 盈虧百分比（佔賬戶）
pnl_percent = (pnl / account_balance) × 100
```

---

## ⚠️ 關鍵限制

### 當前系統的保護機制

1. **單交易對單倉位**
   - 每個交易對同時只能有 1 個倉位
   - 防止重複開倉

2. **無部分平倉**
   - 只能全部平倉
   - 觸及止損/止盈 → 完全退出

3. **固定止損/止盈**
   - 開倉後不會調整
   - 不支持移動止損（trailing stop）

4. **無倉位金字塔**
   - 不支持加倉
   - 每個信號 = 獨立新倉位

---

## 🎯 總結

### 核心公式
```
倉位大小 = MIN(
    賬戶餘額 × 0.3% ÷ 止損距離,    ← 基於風險
    賬戶餘額 × 0.5% ÷ 入場價格      ← 最大倉位
)

止損 = 入場價格 ∓ (ATR × 2.0)
止盈 = 入場價格 ± (ATR × 3.0)
```

### 設計哲學
1. **保本優先** - 保護資金比追求利潤更重要
2. **雙重驗證** - 風險限制 + 倉位限制
3. **動態調整** - 基於市場波動性（ATR）
4. **透明記錄** - 所有交易和指標完整記錄

### 適合對象
✅ 小資金測試（$100-$1,000）  
✅ 保守投資者  
✅ 長期穩定收益  
❌ 高風險高回報  
❌ 快速致富  

---

**下一步**: 在模擬模式下運行 1-2 週，觀察實際風險和回報！


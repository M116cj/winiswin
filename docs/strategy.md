# ICT/SMC 策略邏輯詳解（v3.0）

## 1. 策略核心理念

本機器人採用 **Inner Circle Trader (ICT)** 與 **Smart Money Concepts (SMC)** 的市場結構分析框架，聚焦於：

- **識別機構資金行為（Smart Money）**：追蹤大資金的訂單流和操作模式
- **捕捉訂單塊（Order Blocks）**：識別機構下單的關鍵區域
- **流動性區域（Liquidity Zones）**：找出流動性抓取與反轉點
- **判斷市場結構破壞（Market Structure Break, MSB）**：確認趨勢反轉信號

### 策略特點（v3.0）
- ✅ **純價格行為分析**：不使用預測模型（如 LSTM）
- ✅ **輕量技術指標**：使用 MACD、EMA、RSI、ATR 進行過濾
- ✅ **多級配重信心度系統**：70% 最低門檻，綜合評分
- ✅ **動態槓桿調整**：3-20x，基於信心度和波動率
- ✅ **持續倉位驗證**：開倉後持續監控條件是否依然成立

---

## 2. 訊號生成流程

### 完整流程圖

```
獲取 15m K 線數據 (200 根)
        ↓
識別訂單塊（Order Blocks）
        ↓
識別流動性區域（Liquidity Zones）
        ↓
判定市場結構（Market Structure）
        ↓
計算技術指標（MACD, EMA, ATR）
        ↓
檢查做多/做空條件
        ↓
計算多級配重信心度
        ↓
信心度 ≥ 70% → 生成交易信號
```

---

## 3. 核心概念詳解

### 3.1 訂單塊（Order Block, OB）判定

**定義**：機構資金集中下單的價格區域，通常是趨勢啟動前的最後反向 K 線。

#### 看漲訂單塊（Bullish OB）
```
條件：
1. 出現強勢上漲（當前收盤 > 前收盤 × 1.02，即 +2%）
2. 上漲前的最後一根下跌 K 線作為 OB
3. OB 區間 = [該 K 線的 low, 前一根 K 線的 low]

有效性：
- OB 後至少 3 根 K 線未回測該區間
- OB 區間未被後續價格完全吞沒
```

#### 看跌訂單塊（Bearish OB）
```
條件：
1. 出現強勢下跌（當前收盤 < 前收盤 × 0.98，即 -2%）
2. 下跌前的最後一根上漲 K 線作為 OB
3. OB 區間 = [前一根 K 線的 high, 該 K 線的 high]
```

**實現代碼**（`strategies/ict_smc.py`）：
```python
def identify_order_blocks(self, df, lookback=20):
    order_blocks = []
    
    for i in range(lookback, len(df)):
        current_close = df.iloc[i]['close']
        prev_close = df.iloc[i-1]['close']
        
        # 看漲 OB
        if current_close > prev_close * 1.02:
            order_block = {
                'type': 'bullish',
                'high': df.iloc[i]['high'],
                'low': df.iloc[i-1]['low'],
                'timestamp': df.iloc[i]['timestamp']
            }
            order_blocks.append(order_block)
        
        # 看跌 OB
        elif current_close < prev_close * 0.98:
            order_block = {
                'type': 'bearish',
                'high': df.iloc[i-1]['high'],
                'low': df.iloc[i]['low'],
                'timestamp': df.iloc[i]['timestamp']
            }
            order_blocks.append(order_block)
    
    return order_blocks[-5:]  # 保留最近 5 個
```

---

### 3.2 流動性區域（Liquidity Zone）

**定義**：近期高點/低點形成的支撐/阻力區域，機構常在此抓取流動性後反轉。

#### 識別邏輯
- **支撐區**：50 根 K 線窗口內的最低點
- **阻力區**：50 根 K 線窗口內的最高點
- **有效範圍**：當前價格 ± 1.5% 內視為"在流動性區域"

```python
def identify_liquidity_zones(self, df, lookback=50):
    liquidity_zones = []
    
    for i in range(lookback, len(df)):
        window_highs = highs[i-lookback:i]
        window_lows = lows[i-lookback:i]
        
        # 新高 = 阻力區
        if current_high >= np.max(window_highs):
            liquidity_zones.append({
                'type': 'resistance',
                'price': current_high,
                'timestamp': df.iloc[i]['timestamp']
            })
        
        # 新低 = 支撐區
        if current_low <= np.min(window_lows):
            liquidity_zones.append({
                'type': 'support',
                'price': current_low,
                'timestamp': df.iloc[i]['timestamp']
            })
    
    return liquidity_zones[-5:]  # 保留最近 5 個
```

---

### 3.3 市場結構（Market Structure）

**定義**：通過高低點關係判斷趨勢方向。

| 結構類型 | 條件 | 解釋 |
|---------|------|------|
| **看漲結構** | 高點↑ + 低點↑ | 連續 3 根 K 線高點遞增且低點遞增 |
| **看跌結構** | 高點↓ + 低點↓ | 連續 3 根 K 線高點遞減且低點遞減 |
| **中性結構** | 其他情況 | 震盪或盤整 |

#### 市場結構破壞（MSB）
- **上升結構中跌破前低** → 轉空訊號
- **下降結構中突破前高** → 轉多訊號

```python
def check_market_structure(self, df):
    higher_highs = df['high'].iloc[-3:].is_monotonic_increasing
    higher_lows = df['low'].iloc[-3:].is_monotonic_increasing
    
    lower_highs = df['high'].iloc[-3:].is_monotonic_decreasing
    lower_lows = df['low'].iloc[-3:].is_monotonic_decreasing
    
    if higher_highs and higher_lows:
        return 'bullish_structure'
    elif lower_highs and lower_lows:
        return 'bearish_structure'
    else:
        return 'neutral_structure'
```

---

## 4. 技術指標過濾（輕量級實現）

### 指標參數與用途

| 指標 | 參數 | 用途 | 實現位置 |
|------|------|------|---------|
| **EMA** | 9, 21 | 判斷短期/長期趨勢方向 | `utils/indicators.py` |
| **RSI** | 14 | 避免超買（>70）做多 / 超賣（<30）做空 | `utils/indicators.py` |
| **MACD** | (12, 26, 9) | 確認動能方向（柱狀圖由負轉正為多） | `utils/indicators.py` |
| **ATR** | 14 | 動態設定止損距離（2×ATR）和止盈（3×ATR） | `utils/indicators.py` |

### 做多條件範例

```
✅ 市場結構 = 看漲結構 或 中性結構
✅ 價格在支撐區附近（±1.5%）
✅ MACD > MACD Signal（動能向上）
✅ EMA 9 > EMA 21（短期趨勢向上）
✅ 價格 > EMA 9（價格在趨勢線上方）
✅ 信心度 ≥ 70%
```

### 做空條件範例

```
✅ 市場結構 = 看跌結構 或 中性結構
✅ 價格在阻力區附近（±1.5%）
✅ MACD < MACD Signal（動能向下）
✅ EMA 9 < EMA 21（短期趨勢向下）
✅ 價格 < EMA 9（價格在趨勢線下方）
✅ 信心度 ≥ 70%
```

---

## 5. 多級配重信心度系統（v3.0 核心創新）

### 配重分配

| 項目 | 權重 | 計算方式 |
|------|------|---------|
| **市場結構** | 40% | 完美匹配=40分，中性=20分，相反=0分 |
| **MACD 確認** | 20% | 基於 MACD 與 Signal 的差距強度 |
| **EMA 確認** | 20% | 基於 EMA 9 與 EMA 21 的差距強度 |
| **價格位置** | 10% | 價格相對於 EMA 的位置 |
| **流動性區域** | 10% | 是否在關鍵支撐/阻力區 |

### 計算邏輯（做多為例）

```python
def calculate_confidence(self, structure, macd, macd_signal, ema_9, ema_21, 
                       current_price, signal_type, at_liquidity_zone):
    confidence = 0.0
    
    # 1. 市場結構 (40%)
    if signal_type == 'BUY':
        if structure == 'bullish_structure':
            confidence += 40.0  # 完美看漲結構
        elif structure == 'neutral_structure':
            confidence += 20.0  # 中性可接受
    
    # 2. MACD 確認 (20%)
    if signal_type == 'BUY' and macd > macd_signal:
        macd_strength = min(abs(macd - macd_signal) / abs(macd_signal) * 100, 1.0)
        confidence += 20.0 * macd_strength
    
    # 3. EMA 確認 (20%)
    if signal_type == 'BUY' and ema_9 > ema_21:
        ema_strength = min((ema_9 - ema_21) / ema_21 * 100, 1.0)
        confidence += 20.0 * max(ema_strength, 0.5)  # 至少 10%
    
    # 4. 價格位置 (10%)
    if signal_type == 'BUY':
        if current_price > ema_9:
            confidence += 10.0
        elif current_price > ema_21:
            confidence += 5.0
    
    # 5. 流動性區域 (10%)
    if at_liquidity_zone:
        confidence += 10.0
    
    return min(confidence, 100.0)
```

### 信心度等級

| 範圍 | 等級 | 槓桿 | 說明 |
|------|------|------|------|
| 90-100% | 高信心 | 10-20x | 所有條件完美匹配 |
| 80-90% | 中高信心 | 3-10x | 大部分條件符合 |
| 70-80% | 中信心 | 3x | 達到最低門檻 |
| <70% | 不開倉 | - | 條件不足 |

---

## 6. 倉位與風險管理

### 止損/止盈設置（ATR 動態）

```python
# 做多
stop_loss = current_price - (ATR × 2.0)      # 下方 2 倍 ATR
take_profit = current_price + (ATR × 3.0)    # 上方 3 倍 ATR

# 做空
stop_loss = current_price + (ATR × 2.0)      # 上方 2 倍 ATR
take_profit = current_price - (ATR × 3.0)    # 下方 3 倍 ATR

# 風險回報比 = 1:1.5
```

### 槓桿計算（動態）

```python
# 基於信心度
if 70 <= confidence < 80:
    base_leverage = 3.0
elif 80 <= confidence < 90:
    base_leverage = 3.0 + (confidence - 80) * 0.7  # 線性 3-10x
else:  # 90-100%
    base_leverage = 10.0 + (confidence - 90) * 1.0  # 線性 10-20x

# 波動率調整
if ATR_normalized < 0.02:  # 低波動
    leverage = base_leverage × 1.2
elif ATR_normalized > 0.05:  # 高波動
    leverage = base_leverage × 0.7

leverage = max(3.0, min(leverage, 20.0))  # 限制在 3-20x
```

### 倉位大小計算

```
倉位大小 = (帳戶權益 × 33.33% × 槓桿) ÷ 當前價格
風險金額 = 帳戶權益 × 0.3% (單筆風險)
最大倉位 = 帳戶權益 × 0.5% (單倉上限)
```

---

## 7. 動態倉位監控（v3.0 新增）

### 持續驗證機制

開倉後每 60 秒重新分析市場，檢查：

1. **信號反轉**：市場結構從看漲變看跌 → 立即平倉
2. **信心度暴跌**：下降 >20% → 立即平倉
3. **信心度下降**：下降 10-20% → 發送警告
4. **信心度提升**：提升 >5% → 動態收緊止損/止盈
5. **價格逆向移動**：逆向 >2% 且信心度 <75% → 警告

### 動態調整規則

```python
# 多頭倉位
if 新信心度 > 原信心度 + 5%:
    新止損 = max(新計算的止損, 原止損)  # 只能上移
    新止盈 = max(新計算的止盈, 原止盈)  # 只能上移

# 空頭倉位
if 新信心度 > 原信心度 + 5%:
    新止損 = min(新計算的止損, 原止損)  # 只能下移
    新止盈 = min(新計算的止盈, 原止盈)  # 只能下移
```

---

## 8. 信號範例

### 範例 1：高信心做多信號

```json
{
  "type": "BUY",
  "price": 45280.50,
  "stop_loss": 45100.00,
  "take_profit": 45550.00,
  "confidence": 92.5,
  "expected_roi": 1.5,
  "leverage": 15.2,
  "reason": "看漲結構 + 價格在支撐區 + 高信心",
  "metadata": {
    "structure": "bullish_structure",
    "at_liquidity_zone": true,
    "macd": 125.3,
    "macd_signal": 98.7,
    "ema_9": 45200.0,
    "ema_21": 44800.0
  }
}
```

### 範例 2：中信心做空信號

```json
{
  "type": "SELL",
  "price": 3250.80,
  "stop_loss": 3285.00,
  "take_profit": 3200.00,
  "confidence": 75.2,
  "expected_roi": 1.5,
  "leverage": 3.5,
  "reason": "中性結構 + 價格在阻力區 + 中信心",
  "metadata": {
    "structure": "neutral_structure",
    "at_liquidity_zone": true,
    "macd": -15.2,
    "macd_signal": -8.5
  }
}
```

---

## 9. 策略優化建議

### 當前版本（v3.0）強項
✅ 全市場覆蓋（648 交易對）  
✅ 智能信心度評分  
✅ 動態槓桿調整  
✅ 持續倉位驗證  
✅ ATR 自適應止損/止盈  

### 未來可優化方向
- [ ] 多時間框架確認（1h + 4h）
- [ ] 訂單塊強度評分
- [ ] 機構訂單流分析（Cumulative Delta）
- [ ] 流動性抓取確認（Liquidity Sweep Detection）
- [ ] 分批止盈（25% @ 1.5R, 50% @ 2R, 25% @ 3R）

---

**文檔版本**：v3.0  
**最後更新**：2025-10-24  
**維護者**：Trading Bot Development Team

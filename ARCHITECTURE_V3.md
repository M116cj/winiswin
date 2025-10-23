# Trading Bot v3.0 - 模塊化架構設計

## 概述
從單體架構遷移到**服務導向的模塊化架構**，提升性能、可維護性和擴展性。

## 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Application                          │
│                       (orchestrator.py)                          │
└──────────────┬──────────────┬──────────────┬───────────────────┘
               │              │              │
       ┌───────▼─────┐ ┌─────▼──────┐ ┌─────▼──────┐
       │ DataService │ │  Strategy  │ │ Execution  │
       │             │ │   Engine   │ │  Service   │
       └──────┬──────┘ └──────┬─────┘ └─────┬──────┘
              │                │              │
       ┌──────▼────────────────▼──────────────▼──────┐
       │         MonitoringService (監控中心)         │
       └──────────────────┬──────────────────────────┘
                          │
                 ┌────────▼─────────┐
                 │  Discord Bot     │
                 │  (通知與控制)     │
                 └──────────────────┘
```

---

## 核心服務模塊

### 1. DataService（市場數據服務）
**職責**：集中管理所有市場數據獲取、緩存和分發

**功能**：
- **並發批量獲取**：使用 `asyncio.gather` 同時獲取多個交易對數據
- **增量緩存**：只更新變化的數據，避免重複計算
- **速率限制管理**：集中式速率限制器，確保不超過 Binance API 限制
- **數據驗證**：統一的數據清洗和驗證
- **緩存層**：內存緩存（dict）+ 可選 Redis

**接口**：
```python
class DataService:
    async def fetch_klines_batch(symbols: List[str]) -> Dict[str, pd.DataFrame]
    async def get_cached_klines(symbol: str) -> pd.DataFrame
    async def get_ticker_info(symbol: str) -> Dict
    def is_rate_limited() -> bool
```

---

### 2. StrategyEngine（策略引擎）
**職責**：執行技術分析和交易信號生成

**功能**：
- **多策略支持**：ICT/SMC、套利、自定義策略
- **向量化計算**：使用 numpy/pandas 批量計算指標
- **信號評分**：多因子評分系統（技術指標 + 市場狀態）
- **信號過濾**：市場狀態過濾、信心度閾值
- **優先級隊列**：按信心度或 ROI 排序信號

**接口**：
```python
class StrategyEngine:
    async def analyze_symbol(symbol: str, df: pd.DataFrame) -> Optional[Signal]
    async def rank_signals(signals: List[Signal], mode: str) -> List[Signal]
    def get_strategy_stats() -> Dict
```

---

### 3. ExecutionService（執行服務）
**職責**：管理倉位生命週期和訂單執行

**功能**：
- **倉位管理**：3 倉位限制、資金分配（33.33% 每倉位）
- **風險控制**：雙重保護（0.3% 風險 + 0.5% 最大倉位）
- **訂單執行**：市價/限價單、止損止盈
- **倉位監控**：實時追蹤、自動平倉
- **緊急停止**：異常時自動停止交易

**接口**：
```python
class ExecutionService:
    async def execute_signal(signal: Signal) -> bool
    async def monitor_positions() -> None
    async def close_position(symbol: str) -> bool
    def get_active_positions() -> List[Position]
    def emergency_stop() -> None
```

---

### 4. MonitoringService（監控服務）
**職責**：收集、聚合和報告系統性能指標

**功能**：
- **性能指標**：掃描時間、API 延遲、內存使用
- **交易統計**：勝率、盈虧、夏普比率
- **錯誤追蹤**：API 錯誤、異常堆棧
- **告警系統**：回撤告警、速率限制告警
- **健康檢查**：所有服務和 API 連接狀態

**接口**：
```python
class MonitoringService:
    def record_metric(name: str, value: float) -> None
    def get_system_health() -> Dict
    def get_trading_stats() -> Dict
    async def send_alert(message: str, severity: str) -> None
```

---

## 性能優化策略

### 1. 並發數據獲取
```python
# 舊方式（串行）：3-4 分鐘
for symbol in symbols:
    df = await binance.get_klines(symbol)  # 每次 300ms
    
# 新方式（並行）：< 2 分鐘
# 分批並發，每批 50 個交易對
async def fetch_batch(batch):
    tasks = [binance.get_klines(s) for s in batch]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. 增量緩存機制
```python
# 只更新最新的蠟燭，不重新計算所有指標
cache = {
    'BTCUSDT': {
        'data': DataFrame,
        'indicators': {'macd': [], 'rsi': []},
        'last_update': timestamp
    }
}
```

### 3. 向量化指標計算
```python
# 使用 numpy 批量計算，避免 Python 循環
def calculate_indicators_vectorized(df: pd.DataFrame):
    # numpy 批量計算 MACD, RSI, BB 等
    return indicators_dict
```

---

## API 整合最佳實踐

### Binance API
**速率限制**：
- 權重限制：1200 請求/分鐘
- 訂單限制：100 訂單/10 秒
- 實施：TokenBucket 算法 + 請求隊列

**錯誤處理**：
- 指數退避重試（1s, 2s, 4s, 8s）
- 斷路器模式（5 次失敗後暫停 60 秒）
- 優雅降級（使用緩存數據）

**連接管理**：
- 連接池複用
- 超時設置（連接 5s，讀取 30s）
- 健康檢查端點

### Discord API
**穩定性**：
- 遷移到 `discord.ext.commands.Bot`
- 心跳監控（每 3 秒檢查）
- 自動重連（jitter: 1-5 秒）
- 命令超時保護（15 秒）

**功能完整性**：
- 所有 5 個斜線命令
- 錯誤處理和用戶反饋
- 權限檢查
- 速率限制（5 命令/分鐘/用戶）

---

## 風險管理增強

### 組合級別風險控制
```python
# Value at Risk (95% 信心度)
portfolio_var = calculate_var(positions, confidence=0.95)

# 最大回撤監控
if current_drawdown > MAX_DRAWDOWN_PERCENT:
    execution_service.emergency_stop()
    monitoring.send_alert("最大回撤觸發", severity="critical")
```

### 異常檢測
```python
# 檢測異常 PnL 波動
if abs(current_pnl - expected_pnl) > 3 * std_dev:
    monitoring.send_alert("異常 PnL 檢測", severity="warning")
```

---

## 監控指標

### 系統指標
- `scan_duration_seconds`：掃描 648 個交易對耗時
- `api_latency_ms`：Binance API 延遲
- `memory_usage_mb`：內存使用量
- `active_positions_count`：當前倉位數

### 交易指標
- `total_trades`：總交易數
- `win_rate`：勝率
- `sharpe_ratio`：夏普比率
- `max_drawdown`：最大回撤

### API 健康
- `binance_api_errors`：Binance API 錯誤數
- `discord_reconnects`：Discord 重連次數
- `rate_limit_hits`：速率限制觸發次數

---

## 數據流

```
1. 數據獲取週期開始
   └─> DataService.fetch_klines_batch(648 個交易對)
       └─> 分批並發（50 個/批）
       └─> 緩存更新

2. 策略分析
   └─> StrategyEngine.analyze_all()
       └─> 向量化指標計算
       └─> ICT/SMC 信號生成
       └─> 信號評分和排序

3. 執行決策
   └─> ExecutionService.process_signals(top 3)
       └─> 風險檢查
       └─> 倉位管理
       └─> 訂單執行

4. 監控報告
   └─> MonitoringService.report()
       └─> 性能指標
       └─> Discord 通知
       └─> 告警檢查
```

---

## 部署架構

### 開發環境（Replit）
- 代碼編輯和測試
- 環境變量管理
- Git 版本控制

### 生產環境（Railway EU West）
- 容器化部署
- 自動擴展（未來）
- 監控和日誌

### 數據存儲
- **內存緩存**：實時市場數據
- **本地文件**：trades.json, logs
- **Redis**（可選）：分佈式緩存
- **PostgreSQL**（未來）：歷史數據

---

## 遷移策略

### Phase 1（當前）：基礎模塊化
1. 創建新服務類
2. 保留舊 TradingBot 作為協調器
3. 逐步遷移功能到新服務
4. 確保向後兼容

### Phase 2：性能優化
1. 實施並發獲取
2. 添加緩存層
3. 向量化計算
4. 測試性能提升

### Phase 3：高級功能
1. 監控系統完善
2. 自動迭代機制
3. 管理 API
4. 全面測試

---

## 成功指標

### 性能目標
- ✅ 掃描時間：從 3-4 分鐘 → < 2 分鐘
- ✅ Discord 穩定性：零斷線
- ✅ API 錯誤率：< 0.1%
- ✅ 內存使用：< 300 MB

### 功能目標
- ✅ 所有 Discord 斜線命令正常
- ✅ 實時監控面板
- ✅ 自動風險控制
- ✅ 完整錯誤處理

---

## 文件結構

```
.
├── main.py                      # 主入口（協調器）
├── services/
│   ├── __init__.py
│   ├── data_service.py          # 數據服務
│   ├── strategy_engine.py       # 策略引擎
│   ├── execution_service.py     # 執行服務
│   └── monitoring_service.py    # 監控服務
├── core/
│   ├── __init__.py
│   ├── rate_limiter.py         # 速率限制器
│   ├── circuit_breaker.py      # 斷路器
│   └── cache_manager.py        # 緩存管理
├── strategies/
│   ├── __init__.py
│   ├── ict_smc.py              # ICT/SMC 策略
│   └── base_strategy.py        # 策略基類
├── config.py                    # 配置管理
├── binance_client.py           # Binance 客戶端
├── discord_bot.py              # Discord 機器人
├── risk_manager.py             # 風險管理器
└── utils/
    ├── indicators.py           # 技術指標
    └── helpers.py              # 工具函數
```

---

## 測試策略

### 單元測試
- 每個服務模塊獨立測試
- Mock 外部 API 調用
- 邊界條件和異常處理

### 集成測試
- API 交互測試
- 數據流測試
- 錯誤恢復測試

### 性能測試
- 掃描速度基準測試
- 並發壓力測試
- 內存洩漏測試

### 生產驗證
- Canary 部署
- A/B 測試
- 監控和回滾計劃

---

## 版本歷史

- **v1.0**：基礎交易機器人
- **v2.0**：優化依賴和性能
- **v3.0**：模塊化架構重組（當前）
- **v4.0**（計劃）：AI 驅動的自適應策略

---

## 總結

v3.0 架構重組將交易機器人從單體應用轉變為**高性能、可擴展的模塊化系統**，提升：

✅ **性能**：掃描時間減少 50%+  
✅ **穩定性**：API 錯誤處理和自動恢復  
✅ **可維護性**：清晰的模塊邊界和接口  
✅ **可擴展性**：易於添加新策略和功能  
✅ **可觀測性**：全面的監控和告警系統  

這為未來的 AI 驅動優化和分佈式部署奠定了堅實基礎。

# 🤖 加密貨幣交易機器人 v2.0

## 🎯 專案概述

自動化加密貨幣交易機器人，監控 Binance 期貨市場，使用 ICT/SMC 交易策略，自動風險管理，並通過 Discord 發送通知。

**v2.0 重大優化**：移除 PyTorch LSTM，使用輕量級技術指標，構建時間減少 75%，記憶體使用減少 81%。

---

## ✨ 核心功能

- ✅ **實時市場監控** - Binance API 即時數據
- ✅ **技術分析** - 輕量級指標（MACD、布林帶、EMA、ATR、RSI）
- ✅ **ICT/SMC 策略** - 訂單塊、流動性區域、市場結構
- ✅ **風險管理** - 自動倉位計算、止損、止盈
- ✅ **Discord 通知** - 實時交易提醒和性能報告
- ✅ **交易日誌** - 批量優化寫入

---

## 📊 v2.0 性能提升

| 指標 | 優化前 | 優化後 | 改進 |
|------|--------|--------|------|
| 構建時間 | ~8 分鐘 | ~2 分鐘 | ⬇️ 75% |
| 記憶體 | ~800MB | ~150MB | ⬇️ 81% |
| 啟動時間 | 3-5 分鐘 | 10-20 秒 | ⬇️ 90% |
| 依賴數 | 12 個 | 6 個 | ⬇️ 50% |

---

## 🚀 快速開始

### Railway 部署（推薦）

**📖 完整指南**：[DEPLOY_INSTRUCTIONS_FINAL.md](DEPLOY_INSTRUCTIONS_FINAL.md)

**快速 3 步驟**：

1. **推送代碼到 GitHub**
   ```bash
   git add .
   git commit -m "v2.0: Ready for deployment"
   git push origin main
   ```

2. **在 Railway 創建項目**
   - 訪問：https://railway.app/new
   - 選擇 "Deploy from GitHub repo"
   - 連接你的 repository

3. **設置環境變數**
   ```
   BINANCE_API_KEY=你的key
   BINANCE_SECRET_KEY=你的secret
   DISCORD_BOT_TOKEN=你的token
   DISCORD_CHANNEL_ID=你的channel_id
   ENABLE_TRADING=false
   ```

**完成！** 等待 2-3 分鐘查看日誌

---

## ⚙️ 環境變數

### 必需
```bash
BINANCE_API_KEY          # Binance API Key
BINANCE_SECRET_KEY       # Binance Secret Key
DISCORD_BOT_TOKEN        # Discord Bot Token
DISCORD_CHANNEL_ID       # Discord Channel ID
```

### 可選
```bash
ENABLE_TRADING=false          # 先用模擬模式
SYMBOL_MODE=auto              # auto/static/all
MAX_SYMBOLS=50                # 最大監控數量
RISK_PER_TRADE_PERCENT=0.3    # 每筆風險
MAX_POSITION_SIZE_PERCENT=0.5 # 最大倉位
DEFAULT_LEVERAGE=1.0          # 槓桿倍數
```

---

## 📁 專案結構

```
├── main.py              # 主程序（優化版）
├── config.py           # 配置管理
├── binance_client.py   # Binance API
├── discord_bot.py      # Discord 通知
├── risk_manager.py     # 風險管理
├── trade_logger.py     # 交易日誌（優化）
├── utils/
│   ├── indicators.py   # 技術指標（輕量級）
│   └── helpers.py      # 工具函數
├── strategies/
│   ├── ict_smc.py     # ICT/SMC 策略
│   └── arbitrage.py   # 套利檢測
├── requirements.txt    # 6 個核心依賴
├── nixpacks.toml      # Railway 構建配置
└── railway.json       # Railway 部署配置
```

---

## 🛠️ 技術棧

### 核心依賴（只有 6 個！）
```
python-binance==1.0.19  # Binance API
discord.py==2.3.2       # Discord 通知
pandas==2.1.4           # 數據處理
numpy==1.26.3           # 數值計算
python-dotenv==1.0.0    # 環境變數
requests==2.32.3        # HTTP 請求
```

### v2.0 優化
```
❌ 移除 PyTorch - 節省 500MB、8分鐘構建時間
❌ 移除 TA-Lib - 避免原生編譯
❌ 移除 scikit-learn - 節省 100MB
❌ 移除 matplotlib - 節省 150MB
```

---

## 📚 文檔

- 📖 [部署指南](DEPLOY_INSTRUCTIONS_FINAL.md) - 3 步驟部署到 Railway
- 📖 [優化報告](CODE_OPTIMIZATION_REPORT.md) - v2.0 詳細說明
- 📖 [Railway 指南](RAILWAY_DEPLOYMENT_GUIDE.md) - Railway 深度配置
- 📖 [專案總覽](replit.md) - 完整專案信息

---

## 🔒 安全提示

### API Key 權限
```
✅ 讀取市場數據
✅ 執行交易
❌ 禁止提款
❌ 禁止轉帳
```

### 風險控制
```
✅ 每筆風險: 0.3%
✅ 最大倉位: 0.5%
✅ 槓桿: 1.0x
✅ 回撤警報: 5%
```

### 建議
```
⚠️ 起始資金: $100-500
⚠️ 先測試 1-2 週（模擬模式）
⚠️ 不要投入超過你能承受的損失
```

---

## 💰 費用估算

### Railway Hobby - $5/月
```
✅ 512MB RAM（足夠 50 個交易對）
✅ 實際使用：~150MB
✅ 足夠運行優化版本
```

---

## ✅ 版本歷史

### v2.0 (2025-10-23) - 重大優化
- ✅ 移除 PyTorch LSTM
- ✅ 替換 TA-Lib 輕量級實現
- ✅ 依賴優化（12 → 6）
- ✅ 構建時間 -75%
- ✅ 記憶體使用 -81%

---

**準備部署？** 👉 [開始部署](DEPLOY_INSTRUCTIONS_FINAL.md)

**祝交易順利！** 🚀📈

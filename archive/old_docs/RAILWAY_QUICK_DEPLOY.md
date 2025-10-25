# 🚀 Railway 快速部署指南

您已經完成了 Railway 配置！截圖顯示：
- ✅ Region: `europe-west4-drams3a` (歐洲)
- ✅ Static Outbound IPs: 已啟用
- ✅ Private Networking: 已就緒

## 📋 部署步驟

### 步驟 1: 設置環境變量

在 Railway 控制台，進入 **Variables** 頁面，添加以下環境變量：

```bash
BINANCE_API_KEY=你的Binance API密鑰
BINANCE_SECRET_KEY=你的Binance密鑰
DISCORD_BOT_TOKEN=你的Discord機器人Token
DISCORD_CHANNEL_ID=你的Discord頻道ID

# 交易設置（重要！）
ENABLE_TRADING=false          # 先設為 false 測試連接
BINANCE_TESTNET=false         # 使用真實 API（不是測試網）

# 可選配置
SESSION_SECRET=任意隨機字符串
```

### 步驟 2: 連接 GitHub 倉庫

#### 方法 A: 使用 Railway CLI（推薦）

```bash
# 1. 安裝 Railway CLI（如果還沒安裝）
npm i -g @railway/cli

# 2. 登入
railway login

# 3. 鏈接到您的 Railway 項目
railway link

# 4. 部署當前代碼
railway up
```

#### 方法 B: 從 Railway 控制台部署

1. 在 Railway Dashboard 點擊您的項目
2. 點擊 **Settings** → **Connect Repo**
3. 選擇 GitHub 倉庫
4. Railway 會自動檢測到 `railway.json` 並開始部署

### 步驟 3: 監控部署

```bash
# 查看實時日誌
railway logs --follow
```

**預期成功日誌**：

```
✅ Initialized Binance client in LIVE mode
✅ Fetching ALL USDT perpetual contracts...
✅ Monitoring 648 USDT perpetual contracts
✅ Futures USDT balance: XXX.XX USDT
✅ Total Account Balance: $XXX.XX USDT
✅ Discord bot ready
🚀 Starting trading bot main loop
📊 Trading Cycle #1...
```

**如果看到這些，說明成功了**：
- ✅ 沒有 "restricted location" 錯誤
- ✅ 成功讀取到 Futures USDT 餘額
- ✅ Discord 機器人連接成功

### 步驟 4: 測試 Discord 命令

在您的 Discord 頻道輸入：

```
/balance    # 查看帳戶餘額
/status     # 查看機器人狀態
/positions  # 查看當前倉位
/stats      # 查看統計數據
```

### 步驟 5: 啟用真實交易（可選）

**⚠️ 確認一切正常後再啟用！**

在 Railway Variables 中修改：

```bash
ENABLE_TRADING=true
```

機器人會自動重啟並開始監控市場。

---

## 🔍 故障排查

### 問題 1: 仍然看到 "restricted location" 錯誤

**檢查**：
```bash
# 在 Railway Shell 中運行
curl https://api.ipify.org
```

應該顯示歐洲 IP，而不是美國 IP。

**解決**：確認 Railway 項目設置中的 Region 是 `europe-west4` 或其他歐洲區域。

### 問題 2: 無法讀取帳戶餘額

**檢查**：
- Binance API 密鑰是否正確
- API 密鑰是否有 "讀取" 權限
- BINANCE_TESTNET 應該設為 `false`（真實 API）

### 問題 3: Discord 通知未收到

**檢查**：
- DISCORD_CHANNEL_ID 是否正確（18-19位數字）
- Discord Bot Token 是否正確
- 機器人是否已加入您的 Discord 伺服器

---

## 📊 預期結果

部署成功後，您應該：

1. **在 Railway 日誌中看到**：
   ```
   ✅ Monitoring 648 USDT perpetual contracts
   ✅ Futures USDT balance: XXX.XX USDT
   📊 Trading Cycle #1...
   ```

2. **在 Discord 收到通知**：
   ```
   🤖 交易機器人已啟動
   💰 帳戶餘額：$XXX.XX USDT
   📊 監控：648 個交易對
   ```

3. **使用 Discord 命令**：
   - `/balance` 顯示真實餘額
   - `/status` 顯示機器人運行狀態
   - `/positions` 顯示當前倉位（應為 0/3）

---

## 🎯 下一步

部署成功後：

1. **監控 24 小時**：觀察機器人是否正常生成信號
2. **檢查信號質量**：查看生成的交易信號是否符合預期
3. **小額測試**：如果一切正常，設置小額資金測試真實交易
4. **逐步增加**：確認策略有效後再增加資金

---

## 📞 需要幫助？

如果遇到任何問題：

1. 檢查 Railway 日誌：`railway logs`
2. 檢查 Discord 通知
3. 使用 Discord `/status` 命令查看詳細狀態

祝部署順利！🚀

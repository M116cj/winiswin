# 🔧 Discord 斜線命令無法使用 - 修復指南

## 🚨 問題診斷

Discord 斜線命令無法呼叫通常是以下幾個原因之一：

1. **Bot 權限不足** ⚠️ 最常見
2. **命令未同步**
3. **Bot 未正常啟動**
4. **Discord Developer Portal 設置錯誤**

---

## ✅ 修復步驟

### 步驟 1: 檢查 Bot 權限（最重要！）

#### 1.1 前往 Discord Developer Portal

1. 訪問：https://discord.com/developers/applications
2. 選擇您的交易機器人應用
3. 點擊左側 **"Bot"** 頁面

#### 1.2 確認 Bot 權限

確保以下權限已啟用：

```
✅ PUBLIC BOT (可選)
✅ PRESENCE INTENT
✅ SERVER MEMBERS INTENT
✅ MESSAGE CONTENT INTENT ⭐ 重要
```

#### 1.3 檢查 OAuth2 設置

1. 點擊左側 **"OAuth2"** → **"URL Generator"**
2. 在 **SCOPES** 中勾選：
   ```
   ✅ bot
   ✅ applications.commands ⭐ 這個最關鍵！
   ```

3. 在 **BOT PERMISSIONS** 中勾選：
   ```
   ✅ Send Messages
   ✅ Embed Links
   ✅ Read Message History
   ✅ Use Slash Commands ⭐
   ```

4. **複製生成的 URL**

#### 1.4 重新邀請 Bot

1. **先移除舊 Bot**：
   - 在 Discord 伺服器設置 → 整合 → 找到您的 Bot → 移除

2. **使用新 URL 邀請**：
   - 打開步驟 1.3 生成的 URL
   - 選擇您的伺服器
   - 授權所有權限

---

### 步驟 2: 檢查 Railway 部署日誌

#### 2.1 查看啟動日誌

前往 **Railway.app** → 您的項目 → **Deployments** → 查看日誌

**應該看到：**
```
✅ Discord bot logged in as [您的Bot名稱]
✅ Synced X slash commands
```

**如果看到：**
```
❌ Failed to sync commands: ...
❌ Forbidden (403)
❌ Missing Access
```
→ 這表示權限問題，回到步驟 1

#### 2.2 查看完整日誌

檢查是否有錯誤：
```bash
# 在 Railway 日誌中搜尋
"discord"
"slash"
"sync"
"command"
```

---

### 步驟 3: 驗證 Discord Bot Token

#### 3.1 檢查環境變數

在 **Railway** → **Variables** 中確認：

```
DISCORD_BOT_TOKEN = Bot XXXXXXXXXXXXX
DISCORD_CHANNEL_ID = 1430538906629050500
```

**注意**：
- Token 必須是 **"Bot "** 開頭的完整 token
- Channel ID 必須是純數字

#### 3.2 重新生成 Token（如果需要）

1. Discord Developer Portal → Bot
2. 點擊 **"Reset Token"**
3. 複製新 Token
4. 更新 Railway 環境變數中的 `DISCORD_BOT_TOKEN`
5. 重新部署

---

### 步驟 4: 手動同步命令（進階）

如果命令自動同步失敗，可以手動同步：

#### 4.1 創建同步腳本

創建 `sync_commands.py`：

```python
import discord
from discord import app_commands
import asyncio
import os

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = None  # None = 全局同步，或填入伺服器ID加快同步

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Synced commands to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            print("Synced commands globally (may take up to 1 hour)")

client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await client.close()

client.run(TOKEN)
```

#### 4.2 在本地運行

```bash
# 在 Replit Shell
export DISCORD_BOT_TOKEN="Bot XXXXX"
python sync_commands.py
```

---

### 步驟 5: 檢查 Discord 應用設置

#### 5.1 確認應用類型

Discord Developer Portal → General Information

確保：
```
✅ PUBLIC BOT (如果要在多個伺服器使用)
❌ REQUIRE OAUTH2 CODE GRANT (應該關閉)
```

#### 5.2 確認 Slash Commands 已啟用

Discord Developer Portal → Bot

確保：
```
✅ Authorization Method: In-app Authorization
```

---

## 🧪 測試步驟

### 測試 1: Bot 在線狀態

在 Discord 成員列表中查看：
```
✅ 您的 Bot 應該顯示為 "在線"（綠色圓點）
❌ 如果離線，檢查 Railway 部署狀態
```

### 測試 2: 命令可見性

在 Discord 頻道輸入 `/`：
```
✅ 應該看到您的 Bot 命令列表
   /positions
   /balance
   /stats
   /status
   /config

❌ 如果看不到，可能是：
   • 權限問題
   • 命令未同步
   • Bot 未正確邀請
```

### 測試 3: 執行命令

輸入 `/status`：
```
✅ 應該收到 Bot 回應
❌ 如果收到 "interaction failed"：
   • 檢查 Railway 日誌中的錯誤
   • 確認 Bot 有發送訊息權限
```

---

## 🔍 常見錯誤和解決方案

### 錯誤 1: "Application did not respond"

**原因**：Bot 沒有在 3 秒內回應

**解決**：
1. 檢查 Railway 日誌看是否有錯誤
2. 確認 risk_manager 已初始化
3. 重啟 Railway 服務

### 錯誤 2: "Unknown interaction"

**原因**：命令同步後立即使用

**解決**：
- 等待 1-2 分鐘後再試
- 重新邀請 Bot

### 錯誤 3: 看不到斜線命令

**原因**：Bot 邀請時缺少 `applications.commands` scope

**解決**：
1. 移除 Bot
2. 使用包含 `applications.commands` 的新 URL 重新邀請

### 錯誤 4: "403 Forbidden"

**原因**：Bot 權限不足

**解決**：
1. Discord Developer Portal → Bot → 啟用所有 Intents
2. 重新邀請 Bot 並授予所有權限

---

## 📋 完整檢查清單

### Discord Developer Portal
- [ ] Bot Intents 已啟用（MESSAGE CONTENT INTENT）
- [ ] OAuth2 Scopes 包含 `applications.commands`
- [ ] Bot Permissions 包含 "Use Slash Commands"
- [ ] Token 已正確複製到 Railway

### Discord 伺服器
- [ ] Bot 已使用正確的 URL 邀請
- [ ] Bot 顯示為在線
- [ ] Bot 有發送訊息的權限
- [ ] 在頻道權限中，Bot 可以使用斜線命令

### Railway 部署
- [ ] DISCORD_BOT_TOKEN 環境變數正確
- [ ] DISCORD_CHANNEL_ID 環境變數正確
- [ ] 部署成功，沒有錯誤
- [ ] 日誌顯示 "Synced X slash commands"
- [ ] 日誌顯示 "Discord bot logged in"

### 本地測試
- [ ] 輸入 `/` 可以看到命令列表
- [ ] `/status` 命令有回應
- [ ] 其他命令正常工作

---

## 🚀 快速修復（最常見情況）

如果您不確定問題在哪，按照以下步驟操作：

1. **前往 Discord Developer Portal**
   - 確保 `applications.commands` scope 已勾選

2. **生成新的邀請 URL**
   - Scopes: `bot` + `applications.commands`
   - Permissions: 所有必要權限

3. **移除舊 Bot**
   - Discord 伺服器設置 → 整合 → 移除

4. **重新邀請 Bot**
   - 使用新 URL

5. **重啟 Railway 部署**
   - Railway → Deployments → Redeploy

6. **等待 1-2 分鐘**

7. **測試 `/status`**

---

## 💡 注意事項

### 全局 vs 伺服器命令

- **全局命令**：所有伺服器可用，但同步需要 **最多 1 小時**
- **伺服器命令**：只在指定伺服器可用，但同步**立即生效**

目前代碼使用全局命令，首次同步可能需要等待。

### 命令更新

如果您修改了命令（名稱、描述、參數），需要：
1. 重新部署
2. 等待同步（最多 1 小時）
3. 或使用手動同步腳本

---

## 🎯 下一步

完成以上步驟後：

1. 在 Discord 輸入 `/status` 測試
2. 如果成功，測試其他命令
3. 如果失敗，分享 Railway 日誌中的錯誤訊息

---

**最重要的檢查：`applications.commands` scope 必須在 Bot 邀請時包含！**


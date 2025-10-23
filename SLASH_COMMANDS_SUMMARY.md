# Discord 斜線命令系統總結

## 📱 改動概要

已將 Discord 命令系統從**前綴命令**（`!command`）改為 Discord 官方規範的**斜線命令**（`/command`）。

---

## 🔄 技術改動

### 1. Discord.py API 更新
```python
# 舊方式（前綴命令）
from discord.ext import commands
bot = commands.Bot(command_prefix='!')

@bot.command(name='positions')
async def positions(ctx):
    await ctx.send(embed)

# 新方式（斜線命令）⭐
from discord import app_commands
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@tree.command(name="positions", description="查看當前持倉")
async def positions(interaction: discord.Interaction):
    await interaction.response.send_message(embed)
```

### 2. 命令同步
```python
@bot.event
async def on_ready():
    # 同步斜線命令到 Discord
    synced = await tree.sync()
    logger.info(f"Synced {len(synced)} slash commands")
```

---

## 📋 可用命令

| 斜線命令 | 說明 | 回傳內容 |
|---------|------|---------|
| `/positions` | 查看當前持倉 | 倉位詳情、盈虧、止損止盈 |
| `/balance` | 查看賬戶餘額 | 餘額、總盈虧、ROI、資金分配 |
| `/stats` | 查看性能統計 | 交易數、勝率、回撤 |
| `/status` | 查看機器人狀態 | 運行狀態、監控模式 |
| `/config` | 查看配置 | 風險管理、止損止盈設定 |

---

## ✨ 斜線命令優勢

1. **Discord 官方規範** - 符合 Discord 最佳實踐
2. **自動補全** - 輸入 `/` 後自動顯示命令列表
3. **內建說明** - 每個命令都有 description 參數
4. **更好的權限控制** - 使用 Discord 的權限系統
5. **無衝突** - 不會與其他機器人的前綴命令衝突
6. **現代化 UX** - 更直觀的用戶體驗

---

## 🚀 使用方式

### 傳統方式（已淘汰）
```
在 Discord 輸入: !positions
```

### 新方式（推薦）⭐
```
1. 在 Discord 輸入框中輸入: /
2. Discord 自動顯示所有可用命令
3. 選擇 /positions（或繼續輸入）
4. 按 Enter 執行
```

---

## 📝 更新的文件

- ✅ **discord_bot.py** - 主要程式碼改動
- ✅ **DISCORD_COMMANDS_GUIDE.md** - 完整命令文檔
- ✅ **QUICK_START.md** - 快速開始指南
- ✅ **replit.md** - 項目文檔
- ✅ **SLASH_COMMANDS_SUMMARY.md** - 本文件

---

## 🔧 Railway 部署

斜線命令已完全相容 Railway 部署：

1. **無命令衝突** - 不會有 `!help` 命令重複問題
2. **自動同步** - 機器人啟動時自動同步命令到 Discord
3. **穩定可靠** - 使用 Discord 官方 API

---

## 📚 參考資料

- [Discord.py Application Commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- [Discord Developer Portal - Slash Commands](https://discord.com/developers/docs/interactions/application-commands)

---

**立即前往 Discord 試試 `/positions` 命令！** 🎉


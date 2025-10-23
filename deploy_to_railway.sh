#!/bin/bash

# 🚀 Railway 自動部署腳本
# 此腳本會引導您完成 Railway 部署流程

echo "=================================="
echo "🚀 加密貨幣交易機器人 - Railway 部署"
echo "=================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步驟 1: 檢查環境變數
echo -e "${YELLOW}步驟 1: 檢查必需的環境變數${NC}"
echo "檢查 Replit Secrets..."

if [ -z "$BINANCE_API_KEY" ]; then
    echo -e "${RED}❌ BINANCE_API_KEY 未設置${NC}"
    exit 1
else
    echo -e "${GREEN}✅ BINANCE_API_KEY 已設置${NC}"
fi

if [ -z "$BINANCE_SECRET_KEY" ]; then
    echo -e "${RED}❌ BINANCE_SECRET_KEY 未設置${NC}"
    exit 1
else
    echo -e "${GREEN}✅ BINANCE_SECRET_KEY 已設置${NC}"
fi

if [ -z "$RAILWAY_TOKEN" ]; then
    echo -e "${RED}❌ RAILWAY_TOKEN 未設置${NC}"
    exit 1
else
    echo -e "${GREEN}✅ RAILWAY_TOKEN 已設置${NC}"
fi

echo ""

# 步驟 2: 檢查文件完整性
echo -e "${YELLOW}步驟 2: 檢查必需文件${NC}"

required_files=(
    "main.py"
    "config.py"
    "binance_client.py"
    "discord_bot.py"
    "risk_manager.py"
    "requirements.txt"
    "railway.json"
    "nixpacks.toml"
    "Procfile"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file 缺失${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo -e "${RED}錯誤：缺少必需文件${NC}"
    exit 1
fi

echo ""

# 步驟 3: 顯示當前配置
echo -e "${YELLOW}步驟 3: 當前配置摘要${NC}"
echo "風險參數："
grep -E "(RISK_PER_TRADE|MAX_POSITION|LEVERAGE)" config.py | sed 's/^/  /'
echo ""

# 步驟 4: Git 準備
echo -e "${YELLOW}步驟 4: Git 倉庫狀態${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git 倉庫已初始化${NC}"
    echo "當前分支: $(git branch --show-current)"
    echo "未提交的文件數: $(git status --short | wc -l)"
else
    echo -e "${YELLOW}⚠️  Git 倉庫未初始化${NC}"
    echo "正在初始化 Git..."
    git init
    echo -e "${GREEN}✅ Git 初始化完成${NC}"
fi

echo ""

# 步驟 5: 提交代碼
echo -e "${YELLOW}步驟 5: 提交所有代碼${NC}"
git add .
git commit -m "Production: Small capital live trading - $(date +%Y%m%d_%H%M%S)" || echo "沒有新的變更需要提交"
echo -e "${GREEN}✅ 代碼已提交${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}✅ 本地準備工作完成！${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}接下來的步驟需要在 Railway 網站上操作：${NC}"
echo ""
echo "📋 Railway 部署步驟："
echo ""
echo "1️⃣  前往 https://railway.app"
echo "2️⃣  點擊 'New Project'"
echo "3️⃣  選擇 'Deploy from GitHub repo'"
echo "4️⃣  連接此 GitHub 倉庫"
echo "5️⃣  設置部署區域為: ap-southeast-1 (Singapore)"
echo ""
echo "6️⃣  添加環境變數 (Variables)："
echo "    BINANCE_API_KEY=$BINANCE_API_KEY"
echo "    BINANCE_SECRET_KEY=***已隱藏***"
echo "    BINANCE_TESTNET=false"
echo "    ENABLE_TRADING=true"
echo "    DISCORD_BOT_TOKEN=***已隱藏***"
echo "    DISCORD_CHANNEL_ID=$DISCORD_CHANNEL_ID"
echo ""
echo "7️⃣  點擊 'Deploy' 開始部署"
echo ""
echo "=================================="
echo -e "${GREEN}📊 監控部署狀態：${NC}"
echo "=================================="
echo ""
echo "在 Railway Dashboard → Logs 中查看："
echo "  ✅ Binance client initialized (LIVE MODE)"
echo "  ✅ Current balance: \$XX.XX USDT"
echo "  ✅ Training LSTM model..."
echo "  ✅ Starting market monitoring (LIVE TRADING ENABLED)"
echo ""
echo "在 Discord 中應該收到："
echo "  🤖 交易機器人已啟動"
echo "  💰 賬戶餘額：\$XX.XX USDT"
echo "  ⚙️ 風險設定：0.3% per trade"
echo ""
echo "=================================="
echo -e "${YELLOW}⚠️  重要提醒${NC}"
echo "=================================="
echo ""
echo "• 這是實盤交易，會使用真實資金"
echo "• 風險參數已設為保守模式 (0.3% per trade)"
echo "• 請密切監控第一個小時"
echo "• 如需緊急停止，在 Railway 設置 ENABLE_TRADING=false"
echo ""
echo "祝交易順利！🚀"
echo ""

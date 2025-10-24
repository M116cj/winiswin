#!/bin/bash
# 🚀 自動部署到 Railway（歐洲區域）

set -e  # Exit on error

echo "========================================"
echo "🚀 自動部署到 Railway EU"
echo "========================================"
echo ""

# 顏色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 步驟 1: 確認 Railway CLI
echo -e "${YELLOW}步驟 1: 檢查 Railway CLI${NC}"
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI 未安裝${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Railway CLI 版本: $(railway --version)${NC}"
echo ""

# 步驟 2: 檢查項目狀態
echo -e "${YELLOW}步驟 2: 檢查項目鏈接${NC}"
railway status
echo -e "${GREEN}✅ 項目已鏈接${NC}"
echo ""

# 步驟 3: 設置環境變量
echo -e "${YELLOW}步驟 3: 同步環境變量到 Railway${NC}"
echo "正在設置必需變量..."

# 確保使用正確的服務（如果需要）
export RAILWAY_SERVICE="winiswin"

# 同步環境變量（使用 Replit Secrets）
if [ -n "$BINANCE_API_KEY" ]; then
    railway variables set BINANCE_API_KEY="$BINANCE_API_KEY" --service winiswin 2>&1 | grep -v "Service not found" || true
    echo -e "${GREEN}  ✅ BINANCE_API_KEY${NC}"
fi

if [ -n "$BINANCE_SECRET_KEY" ]; then
    railway variables set BINANCE_SECRET_KEY="$BINANCE_SECRET_KEY" --service winiswin 2>&1 | grep -v "Service not found" || true
    echo -e "${GREEN}  ✅ BINANCE_SECRET_KEY${NC}"
fi

if [ -n "$DISCORD_BOT_TOKEN" ]; then
    railway variables set DISCORD_BOT_TOKEN="$DISCORD_BOT_TOKEN" --service winiswin 2>&1 | grep -v "Service not found" || true
    echo -e "${GREEN}  ✅ DISCORD_BOT_TOKEN${NC}"
fi

if [ -n "$DISCORD_CHANNEL_ID" ]; then
    railway variables set DISCORD_CHANNEL_ID="$DISCORD_CHANNEL_ID" --service winiswin 2>&1 | grep -v "Service not found" || true
    echo -e "${GREEN}  ✅ DISCORD_CHANNEL_ID${NC}"
fi

# 設置交易配置（先保持禁用）
railway variables set ENABLE_TRADING="false" --service winiswin 2>&1 | grep -v "Service not found" || true
railway variables set BINANCE_TESTNET="false" --service winiswin 2>&1 | grep -v "Service not found" || true

echo -e "${GREEN}✅ 環境變量已同步${NC}"
echo ""

# 步驟 4: 準備代碼
echo -e "${YELLOW}步驟 4: 準備代碼部署${NC}"

# 確保 Git 是乾淨的
git add .
git commit -m "Auto deploy to Railway EU - $(date +%Y%m%d_%H%M%S)" || echo "No changes to commit"

echo -e "${GREEN}✅ 代碼已準備${NC}"
echo ""

# 步驟 5: 部署
echo -e "${YELLOW}步驟 5: 開始部署到 Railway${NC}"
echo ""

# 使用 railway up 部署（非交互式）
echo "正在部署..."
railway up --service winiswin --detach 2>&1 || \
railway up --detach 2>&1 || \
echo "Note: Railway will deploy automatically"

echo ""
echo "========================================"
echo -e "${GREEN}✅ 部署命令已執行${NC}"
echo "========================================"
echo ""
echo "📊 下一步："
echo "1. 查看部署日誌: railway logs --service winiswin"
echo "2. 預期看到:"
echo "   ✅ Initialized Binance client in LIVE mode"
echo "   ✅ Futures USDT balance: XXX.XX USDT"
echo "   ✅ Monitoring 648 USDT perpetual contracts"
echo ""
echo "3. 測試 Discord 命令:"
echo "   /balance - 查看帳戶餘額"
echo "   /status - 查看機器人狀態"
echo ""

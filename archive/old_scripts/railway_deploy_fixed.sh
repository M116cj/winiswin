#!/bin/bash
# 🚀 修正版 Railway 自動部署

set -e

echo "========================================"
echo "🚀 Railway EU 自動部署"
echo "========================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 步驟 1: 確認環境變量
echo -e "${YELLOW}步驟 1: 檢查 Replit Secrets${NC}"

if [ -z "$BINANCE_API_KEY" ]; then
    echo "❌ BINANCE_API_KEY 未設置"
    exit 1
fi

if [ -z "$BINANCE_SECRET_KEY" ]; then
    echo "❌ BINANCE_SECRET_KEY 未設置"
    exit 1
fi

if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "❌ DISCORD_BOT_TOKEN 未設置"
    exit 1
fi

if [ -z "$DISCORD_CHANNEL_ID" ]; then
    echo "❌ DISCORD_CHANNEL_ID 未設置"
    exit 1
fi

echo -e "${GREEN}✅ 所有必需的 Secrets 已設置${NC}"
echo ""

# 步驟 2: 同步環境變量到 Railway
echo -e "${YELLOW}步驟 2: 同步環境變量到 Railway${NC}"

railway variables \
  --set "BINANCE_API_KEY=$BINANCE_API_KEY" \
  --set "BINANCE_SECRET_KEY=$BINANCE_SECRET_KEY" \
  --set "DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN" \
  --set "DISCORD_CHANNEL_ID=$DISCORD_CHANNEL_ID" \
  --set "ENABLE_TRADING=false" \
  --set "BINANCE_TESTNET=false" \
  --service winiswin \
  --skip-deploys

echo -e "${GREEN}✅ 環境變量已同步${NC}"
echo ""

# 步驟 3: 顯示當前變量（驗證）
echo -e "${YELLOW}步驟 3: 驗證環境變量${NC}"
railway variables --service winiswin | head -20
echo ""

# 步驟 4: 部署
echo -e "${YELLOW}步驟 4: 部署到 Railway EU${NC}"
echo "正在部署代碼到歐洲區域..."
echo ""

railway up --service winiswin --detach 2>&1 || railway up --detach 2>&1

echo ""
echo "========================================"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "========================================"
echo ""
echo "📊 查看部署狀態："
echo "  railway logs --service winiswin"
echo ""
echo "預期成功日誌："
echo "  ✅ Initialized Binance client in LIVE mode"
echo "  ✅ Futures USDT balance: XXX.XX USDT"
echo "  ✅ Monitoring 648 USDT perpetual contracts"
echo ""

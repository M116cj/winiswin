#!/bin/bash
# 🚀 Railway 一鍵部署命令

echo "=================================="
echo "🚀 Railway 快速部署"
echo "=================================="
echo ""

# 檢查是否安裝 Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安裝"
    echo ""
    echo "請運行："
    echo "  npm i -g @railway/cli"
    echo ""
    exit 1
fi

echo "✅ Railway CLI 已安裝"
echo ""

# 步驟 1: 登入
echo "📝 步驟 1: 登入 Railway"
railway login

# 步驟 2: 鏈接項目（如果還沒鏈接）
echo ""
echo "📝 步驟 2: 鏈接到您的 Railway 項目"
railway link

# 步驟 3: 設置環境變量
echo ""
echo "📝 步驟 3: 設置環境變量"
echo ""
echo "⚠️  請在 Railway 網頁控制台設置以下變量："
echo ""
echo "必需變量："
echo "  BINANCE_API_KEY=你的API密鑰"
echo "  BINANCE_SECRET_KEY=你的密鑰"
echo "  DISCORD_BOT_TOKEN=你的Token"
echo "  DISCORD_CHANNEL_ID=你的頻道ID"
echo ""
echo "交易設置："
echo "  ENABLE_TRADING=false       # 先測試連接"
echo "  BINANCE_TESTNET=false      # 使用真實API"
echo ""
read -p "已設置完環境變量？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "請先在 Railway 控制台設置環境變量"
    echo "網址: https://railway.app/dashboard"
    exit 1
fi

# 步驟 4: 部署
echo ""
echo "📝 步驟 4: 開始部署"
railway up

echo ""
echo "=================================="
echo "✅ 部署命令已執行"
echo "=================================="
echo ""
echo "查看部署狀態："
echo "  railway logs --follow"
echo ""
echo "預期看到："
echo "  ✅ Initialized Binance client in LIVE mode"
echo "  ✅ Futures USDT balance: XXX.XX USDT"
echo "  ✅ Monitoring 648 USDT perpetual contracts"
echo ""

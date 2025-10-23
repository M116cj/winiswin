#!/bin/bash
# 🔒 從 Replit Secrets 同步到 Railway
# 這樣您只需要在 Replit 輸入一次 API keys

echo "========================================"
echo "🔒 同步 Replit Secrets 到 Railway"
echo "========================================"
echo ""

# 檢查 Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI 未安裝"
    echo "安裝方式："
    echo "  npm install -g @railway/cli"
    echo ""
    exit 1
fi

# 檢查是否已登錄
if ! railway whoami &> /dev/null; then
    echo "🔐 請先登錄 Railway..."
    railway login
fi

echo "✅ Railway CLI 已就緒"
echo ""

# 從 Replit 環境變數讀取（Replit Secrets 會自動注入）
echo "📋 從 Replit Secrets 讀取變數..."
echo ""

# 必需的變數
REQUIRED_VARS=(
    "BINANCE_API_KEY"
    "BINANCE_SECRET_KEY"
    "DISCORD_BOT_TOKEN"
    "DISCORD_CHANNEL_ID"
)

# 檢查變數是否存在
MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "⚠️  缺少: $var"
        MISSING=1
    else
        echo "✅ 找到: $var"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "❌ 請先在 Replit Secrets 中設置所有必需的變數"
    echo "   Tools → Secrets → Add new secret"
    exit 1
fi

echo ""
echo "========================================"
echo "🚀 開始同步到 Railway..."
echo "========================================"
echo ""

# 同步每個變數到 Railway
railway variables set BINANCE_API_KEY="$BINANCE_API_KEY"
railway variables set BINANCE_SECRET_KEY="$BINANCE_SECRET_KEY"
railway variables set DISCORD_BOT_TOKEN="$DISCORD_BOT_TOKEN"
railway variables set DISCORD_CHANNEL_ID="$DISCORD_CHANNEL_ID"

# 可選變數（如果存在）
[ -n "$ENABLE_TRADING" ] && railway variables set ENABLE_TRADING="$ENABLE_TRADING"
[ -n "$SYMBOL_MODE" ] && railway variables set SYMBOL_MODE="$SYMBOL_MODE"
[ -n "$MAX_SYMBOLS" ] && railway variables set MAX_SYMBOLS="$MAX_SYMBOLS"
[ -n "$RISK_PER_TRADE_PERCENT" ] && railway variables set RISK_PER_TRADE_PERCENT="$RISK_PER_TRADE_PERCENT"
[ -n "$MAX_POSITION_SIZE_PERCENT" ] && railway variables set MAX_POSITION_SIZE_PERCENT="$MAX_POSITION_SIZE_PERCENT"
[ -n "$DEFAULT_LEVERAGE" ] && railway variables set DEFAULT_LEVERAGE="$DEFAULT_LEVERAGE"

echo ""
echo "========================================"
echo "✅ 同步完成！"
echo "========================================"
echo ""
echo "📊 驗證 Railway 變數："
railway variables

echo ""
echo "✅ 所有 API keys 已從 Replit 同步到 Railway"
echo "✅ 您只需要在 Replit Secrets 維護一份"
echo ""

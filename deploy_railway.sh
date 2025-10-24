#!/bin/bash

echo "🚀 部署到 Railway"
echo "================================"
echo ""

# 檢查 token
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ RAILWAY_TOKEN 未設置"
    exit 1
fi

# 獲取服務名稱
SERVICE_NAME="${1:-trading-bot}"

echo "📊 項目: ravishing-luck"
echo "🌍 環境: production"
echo "🎯 服務: $SERVICE_NAME"
echo ""

# 執行部署
echo "⏳ 開始部署..."
railway up --service="$SERVICE_NAME" --detach

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 部署成功！"
    echo "🔗 查看狀態: https://railway.app"
else
    echo ""
    echo "❌ 部署失敗"
    echo ""
    echo "💡 可能的服務名稱："
    echo "   - trading-bot"
    echo "   - crypto-bot"
    echo "   - bot"
    echo ""
    echo "使用方式: ./deploy_railway.sh <服務名稱>"
    echo "例如: ./deploy_railway.sh my-service-name"
fi

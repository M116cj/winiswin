#!/bin/bash

echo "================================================"
echo "🚀 啟動加密貨幣交易機器人 v2.0"
echo "================================================"
echo ""

# 檢查環境變數
echo "🔍 檢查環境變數..."
if [ -z "$BINANCE_API_KEY" ]; then
    echo "❌ BINANCE_API_KEY 未設置"
    exit 1
fi

if [ -z "$BINANCE_SECRET_KEY" ]; then
    echo "❌ BINANCE_SECRET_KEY 未設置"
    exit 1
fi

if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "⚠️  DISCORD_BOT_TOKEN 未設置 - Discord 通知將被禁用"
fi

if [ -z "$DISCORD_CHANNEL_ID" ]; then
    echo "⚠️  DISCORD_CHANNEL_ID 未設置 - Discord 通知將被禁用"
fi

echo "✅ 環境變數檢查完成"
echo ""

# 顯示當前配置
echo "📊 當前配置:"
echo "   模式: ${SYMBOL_MODE:-auto}"
echo "   交易對數量: ${MAX_SYMBOLS:-50}"
echo "   風險/交易: ${RISK_PER_TRADE_PERCENT:-0.3}%"
echo "   最大倉位: ${MAX_POSITION_SIZE_PERCENT:-0.5}%"
echo "   槓桿: ${DEFAULT_LEVERAGE:-1.0}x"
echo "   交易啟用: ${ENABLE_TRADING:-false}"
echo "   測試網: ${BINANCE_TESTNET:-true}"
echo ""

echo "================================================"
echo "🤖 啟動機器人..."
echo "================================================"
echo ""

# 運行機器人
python3 main.py

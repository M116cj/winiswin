#!/bin/bash
# 診斷 Railway 部署問題

echo "========================================"
echo "🔍 診斷 Railway 機器人狀態"
echo "========================================"
echo ""

echo "1️⃣ 檢查環境變量："
railway variables --service winiswin 2>&1 | grep -E "ENABLE_TRADING|BINANCE_TESTNET" || echo "無法獲取"
echo ""

echo "2️⃣ 嘗試查看最近的日誌："
railway logs --service winiswin 2>&1 | tail -100
echo ""

echo "========================================"
echo "完成診斷"
echo "========================================"

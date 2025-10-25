#!/bin/bash
# 檢查 Railway 部署狀態

echo "========================================"
echo "🔍 檢查 Railway 部署狀態"
echo "========================================"
echo ""

# 設置環境變量
export RAILWAY_TOKEN="$RAILWAY_TOKEN"

echo "1️⃣ 項目狀態："
railway status
echo ""

echo "2️⃣ 嘗試獲取日誌（最近 30 行）："
echo "執行: railway logs --service winiswin | tail -30"
echo ""
railway logs --service winiswin 2>&1 | tail -30 || echo "⚠️  無法獲取日誌，請使用網頁控制台"
echo ""

echo "========================================"
echo "📱 替代方法：使用 Railway 網頁控制台"
echo "========================================"
echo ""
echo "1. 訪問：https://railway.com/dashboard"
echo "2. 選擇項目：ravishing-luck"
echo "3. 選擇服務：winiswin"
echo "4. 點擊 'Logs' 標籤"
echo ""
echo "預期看到："
echo "  ✅ Initialized Binance client in LIVE mode"
echo "  ✅ Futures USDT balance: XXX.XX USDT"
echo "  ✅ Monitoring 648 USDT perpetual contracts"
echo ""

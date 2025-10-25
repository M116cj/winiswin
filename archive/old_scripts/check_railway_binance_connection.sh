#!/bin/bash

# 檢查 Railway 與幣安的連線狀況
# 使用方法: ./check_railway_binance_connection.sh

echo "🔍 檢查 Railway 與幣安 API 連線狀況..."
echo "================================================"
echo ""

# 1. 連接到 Railway 專案
echo "📡 連接到 Railway..."
railway link

echo ""
echo "================================================"
echo "📊 獲取最新日誌（最近 200 行）..."
echo "================================================"
railway logs --tail 200 > /tmp/railway_binance_check.log

# 2. 檢查 API 錯誤
echo ""
echo "🔴 檢查 API 錯誤："
echo "---"

# 檢查地理限制錯誤
GEO_ERRORS=$(grep -c "Service unavailable from a restricted location" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$GEO_ERRORS" -gt 0 ]; then
    echo "  ❌ 地理限制錯誤: $GEO_ERRORS 次"
    echo "     問題: Railway 部署位置無法訪問幣安 API"
    echo "     建議: 檢查 Railway 區域設置或使用 VPN"
else
    echo "  ✅ 無地理限制錯誤"
fi

# 檢查 API Key 錯誤
API_KEY_ERRORS=$(grep -c "Invalid API-key" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$API_KEY_ERRORS" -gt 0 ]; then
    echo "  ❌ API Key 錯誤: $API_KEY_ERRORS 次"
    echo "     問題: API Key 無效或未設置"
    echo "     建議: 檢查環境變數 BINANCE_API_KEY"
else
    echo "  ✅ 無 API Key 錯誤"
fi

# 檢查 Signature 錯誤
SIGNATURE_ERRORS=$(grep -c "Signature for this request is not valid" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$SIGNATURE_ERRORS" -gt 0 ]; then
    echo "  ❌ Signature 錯誤: $SIGNATURE_ERRORS 次"
    echo "     問題: Secret Key 不匹配或時間同步問題"
    echo "     建議: 檢查環境變數 BINANCE_SECRET_KEY"
else
    echo "  ✅ 無 Signature 錯誤"
fi

# 檢查 Invalid Symbol 錯誤
INVALID_SYMBOL_ERRORS=$(grep -c "Invalid symbol" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$INVALID_SYMBOL_ERRORS" -gt 0 ]; then
    echo "  ⚠️  Invalid Symbol 錯誤: $INVALID_SYMBOL_ERRORS 次"
    echo "     問題: 交易對列表包含無效交易對"
    echo "     建議: 清理無效交易對列表"
else
    echo "  ✅ 無 Invalid Symbol 錯誤"
fi

# 檢查 Rate Limit 錯誤
RATE_LIMIT_ERRORS=$(grep -c "Too many requests" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$RATE_LIMIT_ERRORS" -gt 0 ]; then
    echo "  ⚠️  Rate Limit 錯誤: $RATE_LIMIT_ERRORS 次"
    echo "     問題: API 請求過於頻繁"
    echo "     建議: 調整請求頻率或檢查 RateLimiter 配置"
else
    echo "  ✅ 無 Rate Limit 錯誤"
fi

# 3. 檢查成功的數據獲取
echo ""
echo "✅ 檢查成功連線："
echo "---"

SUCCESSFUL_FETCHES=$(grep -c "Fetched [1-9][0-9]*/[0-9]* symbols" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
if [ "$SUCCESSFUL_FETCHES" -gt 0 ]; then
    echo "  ✅ 成功數據獲取: $SUCCESSFUL_FETCHES 次"
    
    # 顯示最近一次成功的獲取
    LAST_FETCH=$(grep "Fetched [1-9][0-9]*/[0-9]* symbols" /tmp/railway_binance_check.log | tail -1)
    echo "  📊 最近一次: $LAST_FETCH"
else
    echo "  ❌ 無成功的數據獲取"
    echo "     問題: 機器人無法從幣安獲取數據"
fi

# 4. 檢查生成的信號
SIGNALS_GENERATED=$(grep "signals generated" /tmp/railway_binance_check.log | tail -5)
if [ -n "$SIGNALS_GENERATED" ]; then
    echo ""
    echo "🎯 最近生成的信號："
    echo "---"
    echo "$SIGNALS_GENERATED"
else
    echo ""
    echo "  ⚠️  未找到信號生成記錄"
fi

# 5. 檢查環境變數
echo ""
echo "================================================"
echo "🔧 檢查環境變數配置："
echo "================================================"

# 檢查 API Keys（不顯示實際值）
if railway variables | grep -q "BINANCE_API_KEY"; then
    echo "  ✅ BINANCE_API_KEY 已設置"
else
    echo "  ❌ BINANCE_API_KEY 未設置"
fi

if railway variables | grep -q "BINANCE_SECRET_KEY"; then
    echo "  ✅ BINANCE_SECRET_KEY 已設置"
else
    echo "  ❌ BINANCE_SECRET_KEY 未設置"
fi

# 檢查 Discord 配置
if railway variables | grep -q "DISCORD_BOT_TOKEN"; then
    echo "  ✅ DISCORD_BOT_TOKEN 已設置"
else
    echo "  ⚠️  DISCORD_BOT_TOKEN 未設置"
fi

# 6. 分析交易週期
echo ""
echo "================================================"
echo "📈 交易週期分析："
echo "================================================"

TOTAL_CYCLES=$(grep -c "Trading Cycle" /tmp/railway_binance_check.log 2>/dev/null || echo "0")
echo "  📊 總週期數: $TOTAL_CYCLES"

if [ "$TOTAL_CYCLES" -gt 0 ]; then
    # 獲取最近一個週期的詳細信息
    echo ""
    echo "  🔍 最近週期摘要："
    grep -A 10 "Trading Cycle" /tmp/railway_binance_check.log | tail -15
fi

# 7. 顯示最近的錯誤
echo ""
echo "================================================"
echo "🔴 最近的錯誤訊息（最後 10 條）："
echo "================================================"
grep "ERROR" /tmp/railway_binance_check.log | tail -10

# 8. 連線狀態總結
echo ""
echo "================================================"
echo "📋 連線狀態總結："
echo "================================================"

if [ "$GEO_ERRORS" -eq 0 ] && [ "$API_KEY_ERRORS" -eq 0 ] && [ "$SIGNATURE_ERRORS" -eq 0 ] && [ "$SUCCESSFUL_FETCHES" -gt 0 ]; then
    echo "  ✅ Railway 與幣安 API 連線正常"
    echo "  ✅ 機器人運行正常"
elif [ "$GEO_ERRORS" -gt 0 ]; then
    echo "  ❌ 地理限制錯誤 - Railway 無法訪問幣安 API"
    echo "  🔧 解決方案："
    echo "     1. 檢查 Railway 部署區域"
    echo "     2. 考慮更改部署位置"
    echo "     3. 聯繫 Railway 支援"
elif [ "$API_KEY_ERRORS" -gt 0 ] || [ "$SIGNATURE_ERRORS" -gt 0 ]; then
    echo "  ❌ API 認證錯誤 - 金鑰配置問題"
    echo "  🔧 解決方案："
    echo "     1. 重新生成幣安 API Key"
    echo "     2. 更新 Railway 環境變數"
    echo "     3. 確保 API Key 有正確權限（期貨交易）"
else
    echo "  ⚠️  連線狀態異常 - 需要進一步診斷"
fi

echo ""
echo "📄 完整日誌已保存到: /tmp/railway_binance_check.log"
echo "================================================"

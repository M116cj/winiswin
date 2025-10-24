#!/usr/bin/env python3
"""
倉位同步修復腳本 - 清除幽靈倉位

用途：檢測並修復機器人內存與幣安實際倉位的不一致問題
使用：python fix_ghost_positions.py
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from binance_client import BinanceClient
from config import Config

async def diagnose_and_fix_positions():
    """
    診斷並修復倉位同步問題
    
    步驟：
    1. 從幣安 API 獲取實際倉位
    2. 顯示診斷報告
    3. 提供修復建議
    """
    
    print("="*70)
    print("🔍 倉位同步診斷工具 v1.0")
    print("="*70)
    print()
    
    try:
        # 初始化幣安客戶端
        logger.info("📡 連接幣安 API...")
        binance = BinanceClient(
            api_key=Config.BINANCE_API_KEY or os.getenv('BINANCE_API_KEY'),
            api_secret=Config.BINANCE_SECRET_KEY or os.getenv('BINANCE_SECRET_KEY'),
            testnet=Config.TESTNET
        )
        
        # 獲取實際倉位
        logger.info("🔍 獲取幣安實際倉位...")
        real_positions = binance.get_current_positions()
        
        if not real_positions:
            print()
            print("="*70)
            print("✅ 診斷結果：幣安沒有任何開倉倉位")
            print("="*70)
            print()
            print("📋 詳細信息：")
            print("  - 幣安實際倉位數：0")
            print()
            print("💡 如果 Railway 顯示 Active positions: 3/3，說明：")
            print("  ❌ 機器人內存中有 3 個「幽靈倉位」")
            print("  ❌ 這些倉位實際不存在於幣安交易所")
            print()
            print("🔧 解決方案：")
            print("  1. 立即重啟 Railway 服務")
            print("     railway restart")
            print()
            print("  2. 監控重啟日誌")
            print("     railway logs --follow")
            print()
            print("  3. 查找同步日誌：")
            print("     應該看到：'Successfully loaded 0 positions from Binance'")
            print()
            print("  4. 驗證結果：")
            print("     日誌應顯示：Active positions: 0/3 ✅")
            print("="*70)
            return
        
        # 顯示實際倉位
        print()
        print("="*70)
        print(f"📊 幣安實際倉位：{len(real_positions)} 個")
        print("="*70)
        print()
        
        for i, pos in enumerate(real_positions, 1):
            symbol = pos['symbol']
            side = pos['positionSide']
            amt = float(pos['positionAmt'])
            entry_price = float(pos['entryPrice'])
            unrealized_pnl = float(pos.get('unRealizedProfit', 0))
            leverage = int(pos.get('leverage', 1))
            
            # 計算倉位價值
            position_value = abs(amt) * entry_price
            
            print(f"  {i}. {symbol}")
            print(f"     方向: {side}")
            print(f"     數量: {abs(amt):.8f}")
            print(f"     入場價: ${entry_price:.8f}")
            print(f"     槓桿: {leverage}x")
            print(f"     倉位價值: ${position_value:.2f}")
            print(f"     未實現盈虧: ${unrealized_pnl:.2f}")
            print()
        
        print("="*70)
        print("📋 同步狀態分析")
        print("="*70)
        print()
        print(f"✅ 幣安實際倉位：{len(real_positions)} 個")
        print()
        print("⚠️  如果 Railway 顯示的倉位數量不同，請執行以下步驟：")
        print()
        print("🔧 修復步驟：")
        print()
        print("1. 重啟 Railway 服務（推薦）")
        print("   $ railway restart")
        print()
        print("2. 重啟後機器人會自動從幣安同步倉位")
        print(f"   預期結果：Active positions: {len(real_positions)}/3 ✅")
        print()
        print("3. 如果重啟後仍不一致，檢查日誌：")
        print("   $ railway logs | grep 'Loading current positions'")
        print("   $ railway logs | grep 'Successfully loaded'")
        print()
        print("4. 確認環境變數：")
        print("   $ railway variables | grep ENABLE_TRADING")
        print("   應該是：ENABLE_TRADING=true")
        print()
        print("="*70)
        
        # 檢查訂單歷史（最近 24 小時）
        logger.info("📜 獲取最近訂單歷史...")
        try:
            # 注意：這裡需要修改 binance_client.py 添加獲取訂單歷史的方法
            # 或者直接使用 binance API
            print()
            print("💡 建議：同時檢查幣安訂單歷史")
            print("   登入幣安網頁 → 期貨 → 訂單歷史")
            print("   查看最近是否有：")
            print("   - 開倉失敗的訂單")
            print("   - 自動平倉的訂單（止損/止盈）")
            print()
        except Exception as e:
            logger.warning(f"無法獲取訂單歷史: {e}")
        
        # 提供詳細的診斷信息
        print("="*70)
        print("🔍 可能的問題原因：")
        print("="*70)
        print()
        print("1. 🔴 開倉失敗但未清除內存")
        print("   - 機器人嘗試開倉但失敗（資金不足/API 錯誤）")
        print("   - 內存中記錄了倉位，但幣安實際未開倉")
        print()
        print("2. 🟡 倉位已平倉但機器人未更新")
        print("   - 幣安交易所層級的止損/止盈觸發")
        print("   - 倉位自動平倉，但機器人未檢測到")
        print()
        print("3. 🟡 機器人重啟時同步失敗")
        print("   - 重啟時未正確從幣安加載倉位")
        print("   - 使用了舊的內存數據")
        print()
        print("4. 🟢 測試模式倉位殘留")
        print("   - 機器人在測試模式運行時創建模擬倉位")
        print("   - 切換到實盤模式後未清除")
        print()
        print("="*70)
        
    except Exception as e:
        logger.error(f"❌ 診斷過程出錯: {e}")
        logger.exception(e)
        print()
        print("="*70)
        print("❌ 診斷失敗")
        print("="*70)
        print()
        print("錯誤信息：", str(e))
        print()
        print("可能原因：")
        print("  - API Key 配置錯誤")
        print("  - 網路連線問題")
        print("  - 幣安 API 暫時無法訪問")
        print()
        print("請檢查：")
        print("  1. 環境變數 BINANCE_API_KEY 和 BINANCE_SECRET_KEY")
        print("  2. 網路連線")
        print("  3. 幣安 API 狀態")
        print()
        print("="*70)
        return 1
    
    return 0

if __name__ == "__main__":
    print()
    exit_code = asyncio.run(diagnose_and_fix_positions())
    print()
    sys.exit(exit_code)

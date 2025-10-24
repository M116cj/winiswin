#!/usr/bin/env python3
"""
止損止盈功能測試腳本
用於驗證 Binance API 止損止盈訂單是否正確設置
"""

import asyncio
from binance_client import BinanceDataClient
from config import Config

async def test_stop_orders():
    print("🔍 測試止損止盈功能")
    print("=" * 60)
    
    client = BinanceDataClient()
    
    # 1. 檢查是否有活躍倉位
    print("\n1️⃣  檢查當前倉位...")
    positions = client.get_current_positions()
    
    if not positions:
        print("❌ 沒有活躍倉位，無法測試止損止盈")
        return
    
    print(f"✅ 找到 {len(positions)} 個活躍倉位")
    
    # 2. 查詢所有止損止盈訂單
    print("\n2️⃣  查詢止損止盈訂單...")
    stop_orders = client.get_open_stop_orders()
    
    if not stop_orders:
        print("⚠️  警告：沒有找到任何止損止盈訂單！")
        print("這可能意味著：")
        print("  - 止損止盈未正確設置")
        print("  - 訂單已被取消")
        print("  - 訂單已被觸發")
    else:
        print(f"✅ 找到 {len(stop_orders)} 個止損止盈訂單")
        
        # 3. 驗證每個倉位都有對應的止損止盈
        print("\n3️⃣  驗證倉位保護...")
        for pos in positions:
            symbol = pos['symbol']
            side = pos['positionSide']
            
            # 查找該倉位的止損止盈訂單
            sl_orders = [o for o in stop_orders if o['symbol'] == symbol and o['type'] == 'STOP_MARKET']
            tp_orders = [o for o in stop_orders if o['symbol'] == symbol and o['type'] == 'TAKE_PROFIT_MARKET']
            
            print(f"\n  {symbol} ({side}):")
            if sl_orders:
                print(f"    ✅ 止損訂單: {len(sl_orders)} 個")
                for sl in sl_orders:
                    print(f"       - 價格: {sl['stopPrice']}, ID: {sl['orderId']}")
            else:
                print(f"    ❌ 未找到止損訂單！")
            
            if tp_orders:
                print(f"    ✅ 止盈訂單: {len(tp_orders)} 個")
                for tp in tp_orders:
                    print(f"       - 價格: {tp['stopPrice']}, ID: {tp['orderId']}")
            else:
                print(f"    ❌ 未找到止盈訂單！")
    
    print("\n" + "=" * 60)
    print("測試完成")

if __name__ == "__main__":
    asyncio.run(test_stop_orders())

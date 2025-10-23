#!/usr/bin/env python3
"""
幣安 API 診斷工具
"""
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

def test_binance_connection():
    """測試幣安 API 連接"""
    print("=" * 70)
    print("🔍 幣安 API 診斷報告")
    print("=" * 70)
    
    # 檢查環境變數
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    
    print("\n1️⃣ 環境變數檢查:")
    print(f"   ✅ BINANCE_API_KEY: {'已設置' if api_key else '❌ 未設置'}")
    print(f"   ✅ BINANCE_SECRET_KEY: {'已設置' if api_secret else '❌ 未設置'}")
    print(f"   ℹ️  BINANCE_TESTNET: {testnet}")
    
    if not api_key or not api_secret:
        print("\n❌ 錯誤: API 密鑰未設置")
        return
    
    # 測試 API 連接
    print("\n2️⃣ API 連接測試:")
    
    try:
        if testnet:
            client = Client(api_key, api_secret, testnet=True)
            print("   🧪 使用測試網絡")
        else:
            client = Client(api_key, api_secret)
            print("   🌐 使用主網絡")
        
        # 測試 1: Ping
        print("\n   測試 1: Ping 服務器...")
        client.ping()
        print("   ✅ Ping 成功")
        
    except BinanceAPIException as e:
        print(f"   ❌ Ping 失敗: {e}")
        if "restricted location" in str(e).lower():
            print("\n" + "=" * 70)
            print("⚠️  地理限制檢測")
            print("=" * 70)
            print("幣安 API 錯誤: 從受限地區訪問")
            print("")
            print("根本原因:")
            print("  - Replit 伺服器位於幣安服務條款禁止的地區")
            print("  - 這不是 API Key 的問題")
            print("  - API Key 本身是有效的")
            print("")
            print("解決方案:")
            print("  ✅ 部署到 Railway EU West 區域")
            print("  ✅ 使用 VPN (不推薦，可能違反條款)")
            print("  ✅ 使用 Binance US (如果在美國)")
            print("")
            print("狀態: 需要重新部署到允許的地理位置")
            print("=" * 70)
        return
    except Exception as e:
        print(f"   ❌ 連接失敗: {type(e).__name__}: {e}")
        return
    
    try:
        # 測試 2: 獲取服務器時間
        print("\n   測試 2: 獲取服務器時間...")
        server_time = client.get_server_time()
        print(f"   ✅ 服務器時間: {server_time['serverTime']}")
        
        # 測試 3: 獲取賬戶信息
        print("\n   測試 3: 獲取賬戶資訊...")
        account = client.get_account()
        print(f"   ✅ 賬戶類型: {account.get('accountType', 'N/A')}")
        print(f"   ✅ 可以交易: {account.get('canTrade', False)}")
        
        # 測試 4: 獲取市場數據
        print("\n   測試 4: 獲取 BTCUSDT K線...")
        klines = client.get_klines(symbol='BTCUSDT', interval='1h', limit=5)
        print(f"   ✅ 成功獲取 {len(klines)} 條 K線數據")
        
        # 測試 5: 獲取交易對信息
        print("\n   測試 5: 獲取 USDT 永續合約...")
        exchange_info = client.futures_exchange_info()
        usdt_symbols = [s for s in exchange_info['symbols'] 
                       if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
        print(f"   ✅ 找到 {len(usdt_symbols)} 個 USDT 永續合約")
        
        print("\n" + "=" * 70)
        print("✅ 所有測試通過！幣安 API 連接正常")
        print("=" * 70)
        
    except BinanceAPIException as e:
        print(f"\n   ❌ API 錯誤: {e}")
        if "restricted location" in str(e).lower():
            print("\n⚠️  地理限制: 需要部署到允許的地區（Railway EU West）")
    except Exception as e:
        print(f"\n   ❌ 未知錯誤: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_binance_connection()

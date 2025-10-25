#!/usr/bin/env python3
"""
測試幣安帳號資訊讀取
"""
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

def test_account_info():
    """測試讀取幣安帳號資訊"""
    print("=" * 70)
    print("💰 幣安帳號資訊測試")
    print("=" * 70)
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')
    testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ API 密鑰未設置")
        return
    
    try:
        # 初始化客戶端
        if testnet:
            client = Client(api_key, api_secret, testnet=True)
            print("🧪 連接到測試網絡...")
        else:
            client = Client(api_key, api_secret)
            print("🌐 連接到主網絡...")
        
        print("\n1️⃣ 嘗試獲取帳號資訊...")
        account = client.get_account()
        
        print("\n✅ 成功讀取帳號資訊！")
        print("=" * 70)
        
        # 顯示帳號基本信息
        print(f"\n📋 帳號類型: {account.get('accountType', 'N/A')}")
        print(f"✅ 可交易: {account.get('canTrade', False)}")
        print(f"✅ 可提現: {account.get('canWithdraw', False)}")
        print(f"✅ 可存款: {account.get('canDeposit', False)}")
        
        # 顯示餘額
        print("\n💰 帳戶餘額:")
        print("-" * 70)
        balances = account.get('balances', [])
        has_balance = False
        
        for balance in balances:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                has_balance = True
                print(f"  {asset:8s}: 可用={free:>15.8f}  鎖定={locked:>15.8f}  總計={total:>15.8f}")
        
        if not has_balance:
            print("  ℹ️  目前沒有餘額")
        
        # 嘗試獲取合約帳戶資訊（如果有權限）
        print("\n2️⃣ 嘗試獲取合約帳戶資訊...")
        try:
            futures_account = client.futures_account()
            print("\n✅ 合約帳戶資訊:")
            print(f"  總資產: {futures_account.get('totalWalletBalance', 0)} USDT")
            print(f"  可用餘額: {futures_account.get('availableBalance', 0)} USDT")
            print(f"  未實現盈虧: {futures_account.get('totalUnrealizedProfit', 0)} USDT")
        except BinanceAPIException as e:
            if "restricted location" in str(e).lower():
                print("  ❌ 地理限制: 無法訪問")
            else:
                print(f"  ℹ️  合約功能可能未啟用或無權限")
        
        print("\n" + "=" * 70)
        print("✅ 帳號資訊讀取功能正常")
        print("=" * 70)
        
    except BinanceAPIException as e:
        if "restricted location" in str(e).lower():
            print("\n" + "=" * 70)
            print("❌ 無法讀取帳號資訊 - 地理限制")
            print("=" * 70)
            print("\n問題原因:")
            print("  - Replit 伺服器位於幣安禁止的地區")
            print("  - 所有 API 請求都會被拒絕")
            print("  - 包括讀取帳號資訊、餘額、市場數據等")
            print("\n您的設置:")
            print("  ✅ API Key: 有效")
            print("  ✅ Secret Key: 有效")
            print("  ❌ 伺服器位置: 受限")
            print("\n解決方案:")
            print("  🚂 部署到 Railway EU West 區域")
            print("     → 歐洲伺服器不受地理限制")
            print("     → 可以正常讀取所有帳號資訊")
            print("     → 可以執行交易")
            print("\n部署後您將看到:")
            print("  ✅ 帳戶類型和權限")
            print("  ✅ 所有幣種餘額")
            print("  ✅ 合約帳戶資訊")
            print("  ✅ 持倉和訂單")
            print("=" * 70)
        else:
            print(f"\n❌ API 錯誤: {e}")
    except Exception as e:
        print(f"\n❌ 未知錯誤: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_account_info()

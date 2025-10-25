#!/usr/bin/env python3
"""
API 連接測試腳本
測試 Binance API 和 Discord Bot 的連接狀況
"""

import asyncio
import sys
from datetime import datetime
from config import Config
from binance_client import BinanceDataClient
from utils.helpers import setup_logger

logger = setup_logger(__name__)

def print_section(title):
    """打印分隔線"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_status(item, status, details=""):
    """打印狀態信息"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {item}: {details}")

async def test_binance_connection():
    """測試 Binance API 連接"""
    print_section("Binance API 連接測試")
    
    results = {
        'api_key_configured': False,
        'secret_key_configured': False,
        'client_initialized': False,
        'connection_successful': False,
        'symbols_loaded': False,
        'market_data_accessible': False
    }
    
    try:
        # 1. 檢查 API 金鑰配置
        if Config.BINANCE_API_KEY and Config.BINANCE_API_KEY != "":
            results['api_key_configured'] = True
            print_status("API Key 配置", True, f"長度: {len(Config.BINANCE_API_KEY)}")
        else:
            print_status("API Key 配置", False, "未設置")
            return results
        
        if Config.BINANCE_SECRET_KEY and Config.BINANCE_SECRET_KEY != "":
            results['secret_key_configured'] = True
            print_status("Secret Key 配置", True, f"長度: {len(Config.BINANCE_SECRET_KEY)}")
        else:
            print_status("Secret Key 配置", False, "未設置")
            return results
        
        # 2. 初始化客戶端
        print("\n正在初始化 Binance 客戶端...")
        client = BinanceDataClient()
        results['client_initialized'] = True
        print_status("客戶端初始化", True)
        
        # 3. 測試連接
        print("\n正在測試 API 連接...")
        try:
            # 獲取伺服器時間
            server_time = client.client.get_server_time()
            results['connection_successful'] = True
            server_datetime = datetime.fromtimestamp(server_time['serverTime'] / 1000)
            print_status("API 連接", True, f"伺服器時間: {server_datetime}")
        except Exception as e:
            print_status("API 連接", False, str(e))
            return results
        
        # 4. 測試獲取交易對
        print("\n正在加載交易對...")
        try:
            symbols = client.get_all_usdt_perpetual_symbols()
            results['symbols_loaded'] = True
            print_status("交易對加載", True, f"找到 {len(symbols)} 個 USDT 永續合約")
            
            # 顯示前 10 個
            print("\n前 10 個交易對:")
            for i, symbol in enumerate(symbols[:10], 1):
                print(f"  {i}. {symbol}")
            if len(symbols) > 10:
                print(f"  ... 還有 {len(symbols) - 10} 個")
        except Exception as e:
            print_status("交易對加載", False, str(e))
            return results
        
        # 5. 測試獲取市場數據
        print("\n正在測試市場數據...")
        try:
            test_symbol = 'BTCUSDT'
            klines = client.get_historical_klines(test_symbol, '1h', limit=10)
            if klines and len(klines) > 0:
                results['market_data_accessible'] = True
                latest_price = float(klines[-1][4])  # 收盤價
                print_status("市場數據", True, f"{test_symbol} 最新價格: ${latest_price:,.2f}")
                print(f"  獲取了 {len(klines)} 根 K 線數據")
            else:
                print_status("市場數據", False, "無法獲取數據")
        except Exception as e:
            print_status("市場數據", False, str(e))
            return results
        
        # 6. 測試賬戶信息（如果有權限）
        print("\n正在測試賬戶信息...")
        try:
            account = client.client.futures_account()
            balance = float(account.get('totalWalletBalance', 0))
            print_status("賬戶信息", True, f"餘額: ${balance:,.2f} USDT")
        except Exception as e:
            error_msg = str(e)
            if "API-key format invalid" in error_msg or "Invalid API-key" in error_msg:
                print_status("賬戶信息", False, "API Key 無效")
            elif "Signature for this request is not valid" in error_msg:
                print_status("賬戶信息", False, "簽名驗證失敗")
            elif "IP address is not whitelisted" in error_msg:
                print_status("賬戶信息", False, "IP 未加入白名單")
            else:
                print_status("賬戶信息", False, error_msg[:100])
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return results

async def test_discord_connection():
    """測試 Discord Bot 連接"""
    print_section("Discord Bot 連接測試")
    
    results = {
        'token_configured': False,
        'channel_configured': False,
        'bot_can_connect': False
    }
    
    try:
        # 1. 檢查 Token 配置
        if Config.DISCORD_BOT_TOKEN and Config.DISCORD_BOT_TOKEN != "":
            results['token_configured'] = True
            token_preview = Config.DISCORD_BOT_TOKEN[:20] + "..." if len(Config.DISCORD_BOT_TOKEN) > 20 else "短"
            print_status("Bot Token 配置", True, f"前綴: {token_preview}")
        else:
            print_status("Bot Token 配置", False, "未設置")
            return results
        
        # 2. 檢查 Channel ID 配置
        if Config.DISCORD_CHANNEL_ID and Config.DISCORD_CHANNEL_ID != "":
            results['channel_configured'] = True
            print_status("Channel ID 配置", True, Config.DISCORD_CHANNEL_ID)
        else:
            print_status("Channel ID 配置", False, "未設置")
        
        # 3. 測試 Bot 連接（簡單驗證）
        print("\n正在驗證 Discord Bot Token...")
        import discord
        
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
            
            @client.event
            async def on_ready():
                print_status("Bot 連接", True, f"已登入為 {client.user}")
                results['bot_can_connect'] = True
                await client.close()
            
            # 設置超時
            async def timeout_handler():
                await asyncio.sleep(10)
                if client.is_ready():
                    await client.close()
                else:
                    print_status("Bot 連接", False, "連接超時（10秒）")
                    await client.close()
            
            # 同時運行連接和超時處理
            await asyncio.gather(
                client.start(Config.DISCORD_BOT_TOKEN),
                timeout_handler(),
                return_exceptions=True
            )
            
        except discord.errors.LoginFailure:
            print_status("Bot 連接", False, "Token 無效")
        except Exception as e:
            error_msg = str(e)
            if "Improper token" in error_msg:
                print_status("Bot 連接", False, "Token 格式錯誤")
            else:
                print_status("Bot 連接", False, error_msg[:100])
    
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return results

def print_summary(binance_results, discord_results):
    """打印測試總結"""
    print_section("測試總結")
    
    print("\n📊 Binance API:")
    total_binance = len(binance_results)
    passed_binance = sum(1 for v in binance_results.values() if v)
    print(f"  通過: {passed_binance}/{total_binance}")
    
    if binance_results.get('connection_successful'):
        print("  ✅ Binance API 連接正常")
    else:
        print("  ❌ Binance API 連接失敗")
    
    print("\n📱 Discord Bot:")
    total_discord = len(discord_results)
    passed_discord = sum(1 for v in discord_results.values() if v)
    print(f"  通過: {passed_discord}/{total_discord}")
    
    if discord_results.get('token_configured'):
        print("  ✅ Discord Token 已配置")
    else:
        print("  ❌ Discord Token 未配置")
    
    # 整體狀態
    print("\n" + "="*70)
    all_critical_passed = (
        binance_results.get('connection_successful', False) and
        binance_results.get('symbols_loaded', False) and
        discord_results.get('token_configured', False)
    )
    
    if all_critical_passed:
        print("✅ 所有關鍵 API 連接正常，可以部署到 Railway！")
    else:
        print("⚠️  部分 API 連接有問題，請檢查配置")
    print("="*70)

async def main():
    """主測試函數"""
    print("\n" + "="*70)
    print("  🔍 API 連接狀況測試")
    print("  測試時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    # 測試環境信息
    print("\n環境配置:")
    print(f"  Testnet 模式: {Config.BINANCE_TESTNET}")
    print(f"  交易啟用: {Config.ENABLE_TRADING}")
    print(f"  交易對模式: {Config.SYMBOL_MODE}")
    print(f"  最大交易對: {Config.MAX_SYMBOLS}")
    
    # 執行測試
    binance_results = await test_binance_connection()
    discord_results = await test_discord_connection()
    
    # 打印總結
    print_summary(binance_results, discord_results)
    
    return binance_results, discord_results

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

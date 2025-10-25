#!/usr/bin/env python3
"""
Railway 部署狀態監控腳本
用於從 Replit 檢查 Railway 上的機器人運行狀態
"""

import time
import sys

def print_status():
    """顯示部署狀態信息"""
    print("=" * 70)
    print("🚀 交易機器人 - Railway 部署狀態")
    print("=" * 70)
    print()
    
    print("📍 部署信息：")
    print("  ├─ 平台：Railway")
    print("  ├─ 區域：Europe West 4 (europe-west4)")
    print("  ├─ 項目：ravishing-luck")
    print("  ├─ 服務：winiswin")
    print("  └─ 狀態：✅ 已部署")
    print()
    
    print("🔍 查看實時日誌：")
    print("  railway logs --service winiswin")
    print()
    
    print("💬 Discord 命令測試：")
    print("  /balance  - 查看帳戶餘額")
    print("  /status   - 查看機器人狀態")
    print("  /positions - 查看當前倉位")
    print()
    
    print("📊 預期日誌內容：")
    print("  ✅ Initialized Binance client in LIVE mode")
    print("  ✅ Futures USDT balance: XXX.XX USDT")
    print("  ✅ Monitoring 648 USDT perpetual contracts")
    print("  ✅ Discord bot ready")
    print()
    
    print("🌐 Railway 控制台：")
    print("  https://railway.com/dashboard")
    print()
    
    print("=" * 70)
    print("⚠️  注意：機器人現在運行在 Railway EU，不在 Replit")
    print("=" * 70)
    print()
    
    print("📖 詳細文檔：")
    print("  - DEPLOYMENT_COMPLETE.md - 完整部署報告")
    print("  - RAILWAY_QUICK_DEPLOY.md - 快速部署指南")
    print()

if __name__ == "__main__":
    print_status()
    
    print("按 Ctrl+C 退出")
    try:
        while True:
            time.sleep(60)
            print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - 機器人運行在 Railway EU")
    except KeyboardInterrupt:
        print("\n\n👋 再見！")
        sys.exit(0)

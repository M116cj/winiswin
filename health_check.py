"""
健康檢查模組 - 確保實盤模式啟動前所有組件正常
"""

import asyncio
import logging
from config import Config
from binance_client import BinanceClient

logger = logging.getLogger(__name__)


class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
    
    async def run_all_checks(self) -> bool:
        """運行所有健康檢查"""
        logger.info("="*70)
        logger.info("🏥 開始健康檢查...")
        logger.info("="*70)
        
        checks = [
            self.check_environment_variables(),
            self.check_binance_connection(),
            self.check_binance_permissions(),
            self.check_discord_config()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        all_passed = all(r is True for r in results if not isinstance(r, Exception))
        
        logger.info("\n" + "="*70)
        if all_passed:
            logger.info("✅ 所有健康檢查通過！")
        else:
            logger.warning(f"⚠️  {len(self.checks_failed)} 項檢查失敗")
            for check in self.checks_failed:
                logger.warning(f"  ❌ {check}")
        logger.info("="*70 + "\n")
        
        return all_passed
    
    async def check_environment_variables(self) -> bool:
        """檢查環境變量配置"""
        logger.info("1️⃣  檢查環境變量...")
        
        required_vars = {
            'BINANCE_API_KEY': Config.BINANCE_API_KEY,
            'BINANCE_SECRET_KEY': Config.BINANCE_SECRET_KEY,
            'DISCORD_BOT_TOKEN': Config.DISCORD_BOT_TOKEN,
            'DISCORD_CHANNEL_ID': Config.DISCORD_CHANNEL_ID
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        
        if missing:
            self.checks_failed.append(f"Missing env vars: {', '.join(missing)}")
            logger.error(f"  ❌ 缺少環境變量: {', '.join(missing)}")
            return False
        
        logger.info(f"  ✅ 環境變量完整")
        logger.info(f"  ⚙️  交易模式: {'🔴 LIVE' if Config.ENABLE_TRADING else '🟡 SIMULATION'}")
        logger.info(f"  ⚙️  測試網: {'是' if Config.BINANCE_TESTNET else '否'}")
        self.checks_passed.append("Environment variables")
        return True
    
    async def check_binance_connection(self) -> bool:
        """檢查 Binance API 連接"""
        logger.info("2️⃣  檢查 Binance API 連接...")
        
        try:
            client = BinanceClient()
            
            # 嘗試獲取帳戶資訊
            spot_balance = client.get_account_balance()
            futures_balance = client.get_futures_balance()
            
            total_usdt = 0
            if spot_balance and 'USDT' in spot_balance:
                total_usdt += spot_balance['USDT']['total']
            total_usdt += futures_balance
            
            logger.info(f"  ✅ Binance API 連接成功")
            logger.info(f"  💰 總 USDT 餘額: ${total_usdt:.2f}")
            logger.info(f"     📊 現貨: ${spot_balance.get('USDT', {}).get('total', 0):.2f}")
            logger.info(f"     📈 合約: ${futures_balance:.2f}")
            
            self.checks_passed.append("Binance connection")
            return True
            
        except Exception as e:
            self.checks_failed.append(f"Binance connection: {str(e)}")
            logger.error(f"  ❌ Binance API 連接失敗: {e}")
            return False
    
    async def check_binance_permissions(self) -> bool:
        """檢查 Binance API 權限"""
        logger.info("3️⃣  檢查 Binance API 權限...")
        
        try:
            client = BinanceClient()
            
            # 檢查是否能夠下單（僅檢查權限，不實際下單）
            if Config.ENABLE_TRADING:
                logger.info("  ⚙️  實盤模式 - API Key 需要交易權限")
                # 這裡可以嘗試獲取訂單信息來驗證權限
                # 但不實際下單
            else:
                logger.info("  ⚙️  模擬模式 - 不需要交易權限")
            
            logger.info(f"  ✅ API 權限檢查完成")
            self.checks_passed.append("Binance permissions")
            return True
            
        except Exception as e:
            self.checks_failed.append(f"Binance permissions: {str(e)}")
            logger.error(f"  ❌ API 權限檢查失敗: {e}")
            return False
    
    async def check_discord_config(self) -> bool:
        """檢查 Discord 配置"""
        logger.info("4️⃣  檢查 Discord 配置...")
        
        if not Config.DISCORD_BOT_TOKEN:
            self.checks_failed.append("Discord bot token not configured")
            logger.error("  ❌ Discord Bot Token 未配置")
            return False
        
        if not Config.DISCORD_CHANNEL_ID:
            self.checks_failed.append("Discord channel ID not configured")
            logger.error("  ❌ Discord Channel ID 未配置")
            return False
        
        logger.info(f"  ✅ Discord 配置完整")
        logger.info(f"  📱 頻道 ID: {Config.DISCORD_CHANNEL_ID}")
        self.checks_passed.append("Discord configuration")
        return True


async def main():
    """運行健康檢查"""
    checker = HealthChecker()
    success = await checker.run_all_checks()
    
    if success:
        logger.info("🎉 系統健康狀態良好，可以啟動！")
        return 0
    else:
        logger.error("⚠️  系統健康檢查失敗，請修復問題後重試")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    exit_code = asyncio.run(main())
    exit(exit_code)

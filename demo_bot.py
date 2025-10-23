#!/usr/bin/env python3
"""
演示模式 - 展示所有 Discord 通知功能
不需要 Binance 連接，使用模擬數據
"""

import asyncio
import random
import time
from datetime import datetime
from discord_bot import TradingBotNotifier
from config import Config
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class DemoTradingBot:
    def __init__(self):
        self.notifier = None
        if Config.DISCORD_BOT_TOKEN and Config.DISCORD_CHANNEL_ID:
            self.notifier = TradingBotNotifier()
            logger.info("Discord notifier enabled")
        else:
            logger.error("Discord credentials not configured!")
            raise ValueError("Please set DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID")
        
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
        self.running = False
        self.cycle_count = 0
    
    async def initialize(self):
        """初始化機器人"""
        logger.info("🚀 初始化演示交易機器人...")
        
        if self.notifier:
            asyncio.create_task(self.notifier.start_bot())
            await asyncio.sleep(5)  # 等待 Discord bot 準備好
        
        logger.info("✅ 演示機器人初始化完成")
    
    async def simulate_market_analysis(self, symbol):
        """模擬市場分析"""
        # 生成隨機價格
        base_prices = {
            'BTCUSDT': 50000,
            'ETHUSDT': 3000,
            'BNBUSDT': 400,
            'SOLUSDT': 100,
            'XRPUSDT': 0.50
        }
        
        price = base_prices.get(symbol, 1000) * random.uniform(0.98, 1.02)
        atr = price * 0.02  # ATR 約為價格的 2%
        
        analysis = {
            'symbol': symbol,
            'price': price,
            'atr': atr,
            'rsi': random.uniform(30, 70),
            'market_structure': random.choice(['bullish', 'bearish', 'neutral']),
            'macd_signal': random.choice(['bullish', 'bearish', 'neutral'])
        }
        
        # 發送市場分析通知
        if self.notifier:
            await self.notifier.send_market_analysis(symbol, analysis)
        
        return analysis
    
    async def simulate_signal(self, symbol, analysis):
        """模擬交易信號"""
        signal_type = random.choice(['BUY', 'SELL', None, None, None])  # 20% 機率生成信號
        
        if not signal_type:
            return None
        
        entry_price = analysis['price']
        atr = analysis['atr']
        
        if signal_type == 'BUY':
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
        else:  # SELL
            stop_loss = entry_price + (atr * 2.0)
            take_profit = entry_price - (atr * 3.0)
        
        signal_info = {
            'type': signal_type,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': 0.001,
            'confidence': random.uniform(60, 95),
            'reason': f"ICT/SMC 策略: {'訂單塊突破' if signal_type == 'BUY' else '流動性掃蕩'}"
        }
        
        # 發送信號通知
        if self.notifier:
            await self.notifier.send_signal(symbol, signal_info)
        
        return signal_info
    
    async def simulate_trade_execution(self, symbol, signal):
        """模擬交易執行"""
        if not signal:
            return
        
        # 發送交易執行通知
        trade_info = {
            'symbol': symbol,
            'type': signal['type'],
            'price': signal['entry_price'],
            'quantity': signal['position_size'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'reason': signal['reason']
        }
        
        if self.notifier:
            await self.notifier.send_trade_notification(trade_info)
        
        logger.info(f"✅ 模擬交易執行: {symbol} {signal['type']} @ ${signal['entry_price']:.2f}")
    
    async def run_demo_cycle(self):
        """運行一個演示週期"""
        start_time = time.time()
        signals_found = 0
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 開始第 {self.cycle_count + 1} 個分析週期")
        logger.info(f"{'='*60}\n")
        
        # 通知週期開始
        if self.notifier:
            await self.notifier.send_cycle_start(len(self.symbols))
        
        # 分析每個交易對
        for symbol in self.symbols:
            logger.info(f"📊 分析 {symbol}...")
            
            # 模擬市場分析
            analysis = await self.simulate_market_analysis(symbol)
            
            # 模擬等待（看起來更真實）
            await asyncio.sleep(1)
            
            # 模擬信號生成
            signal = await self.simulate_signal(symbol, analysis)
            
            if signal:
                signals_found += 1
                logger.info(f"📡 {symbol} 發現 {signal['type']} 信號！")
                
                # 模擬交易執行
                await self.simulate_trade_execution(symbol, signal)
            else:
                logger.info(f"⚪ {symbol} 無信號")
        
        duration = time.time() - start_time
        
        # 通知週期完成
        if self.notifier:
            await self.notifier.send_cycle_complete(duration, signals_found)
        
        # 模擬性能統計
        if self.cycle_count % 3 == 0 and self.notifier:
            stats = {
                'account_balance': 10000 + random.uniform(-500, 1000),
                'total_trades': self.cycle_count * 2,
                'win_rate': random.uniform(50, 70),
                'total_profit': random.uniform(-200, 500),
                'max_drawdown': random.uniform(1, 5),
                'roi': random.uniform(-2, 5)
            }
            await self.notifier.send_performance_report(stats)
        
        # 偶爾發送警報
        if random.random() < 0.1 and self.notifier:
            await self.notifier.send_alert(
                'warning',
                f"演示警報: 市場波動率異常升高（僅供測試）"
            )
        
        logger.info(f"\n✅ 週期完成！用時 {duration:.1f}秒，發現 {signals_found} 個信號\n")
        
        self.cycle_count += 1
    
    async def run(self):
        """運行演示機器人"""
        self.running = True
        
        logger.info("\n" + "="*60)
        logger.info("🚀 演示交易機器人啟動")
        logger.info("="*60 + "\n")
        
        if self.notifier:
            await self.notifier.send_message(
                "🤖 演示交易機器人已上線！\n\n"
                "這是演示模式，使用模擬數據展示所有通知功能。\n"
                "您將看到：\n"
                "• 📊 市場分析\n"
                "• 📡 交易信號\n"
                "• 🔔 交易執行\n"
                "• 📈 性能報告\n"
                "• ⚠️  警報通知\n\n"
                "每 30 秒運行一個分析週期..."
            )
        
        try:
            while self.running:
                await self.run_demo_cycle()
                
                logger.info("⏳ 等待 30 秒後開始下一個週期...\n")
                await asyncio.sleep(30)
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  收到停止信號")
        except Exception as e:
            logger.error(f"❌ 錯誤: {e}")
            if self.notifier:
                await self.notifier.send_alert('error', f"系統錯誤: {str(e)}")
    
    async def shutdown(self):
        """關閉機器人"""
        logger.info("\n" + "="*60)
        logger.info("🛑 關閉演示交易機器人")
        logger.info("="*60)
        
        self.running = False
        
        if self.notifier:
            await self.notifier.send_message(
                "🛑 演示交易機器人正在關閉...\n\n"
                f"運行統計:\n"
                f"• 總週期數: {self.cycle_count}\n"
                f"• 感謝使用！"
            )
            await self.notifier.close()
        
        logger.info("✅ 關閉完成\n")

async def main():
    """主函數"""
    print("\n" + "="*60)
    print("🎮 加密貨幣交易機器人 - 演示模式")
    print("="*60)
    print("\n這是演示模式，使用模擬數據展示所有功能。")
    print("請確保已設置 DISCORD_BOT_TOKEN 和 DISCORD_CHANNEL_ID\n")
    
    bot = DemoTradingBot()
    
    try:
        await bot.initialize()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("\n👋 收到 Ctrl+C，正在關閉...")
    except Exception as e:
        logger.error(f"\n❌ 致命錯誤: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

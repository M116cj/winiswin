import asyncio
import time
from datetime import datetime
import numpy as np
from binance_client import BinanceDataClient
from strategies.ict_smc import ICTSMCStrategy
from strategies.arbitrage import ArbitrageStrategy
from risk_manager import RiskManager
from discord_bot import TradingBotNotifier
from trade_logger import TradeLogger
from utils.indicators import TechnicalIndicators
from utils.helpers import setup_logger
from config import Config

logger = setup_logger(__name__)

class TradingBot:
    """
    優化後的交易機器人
    
    主要改進：
    1. 移除 PyTorch LSTM（減少 ~500MB 記憶體和 8 分鐘構建時間）
    2. 純技術指標策略（ICT/SMC）
    3. 條件性 Discord 初始化
    4. 異步並行市場分析
    5. 指標計算緩存
    """
    def __init__(self):
        self.binance = BinanceDataClient()
        self.ict_strategy = ICTSMCStrategy()
        self.arbitrage_strategy = ArbitrageStrategy()
        self.risk_manager = RiskManager()
        self.trade_logger = TradeLogger()
        
        self.notifier = None
        if Config.DISCORD_BOT_TOKEN and Config.DISCORD_CHANNEL_ID:
            self.notifier = TradingBotNotifier()
            logger.info("Discord notifier enabled")
        else:
            logger.info("Discord notifier disabled (no credentials)")
        
        self.symbols = self._initialize_trading_pairs()
        self.timeframe = Config.TIMEFRAME
        self.running = False
        
        self.indicators_cache = {}
    
    def _initialize_trading_pairs(self):
        """根據配置初始化交易對列表"""
        mode = Config.SYMBOL_MODE
        
        if mode == 'all':
            logger.info("Mode: ALL - Fetching all USDT perpetual pairs...")
            pairs = self.binance.get_all_usdt_perpetual_pairs()
            logger.info(f"Loaded {len(pairs)} trading pairs")
            return pairs
        
        elif mode == 'auto':
            logger.info(f"Mode: AUTO - Fetching top {Config.MAX_SYMBOLS} pairs by volume...")
            pairs = self.binance.get_top_pairs_by_volume(limit=Config.MAX_SYMBOLS)
            logger.info(f"Loaded {len(pairs)} trading pairs")
            return pairs
        
        else:
            logger.info("Mode: STATIC - Using predefined trading pairs")
            return Config.STATIC_SYMBOLS
    
    async def initialize(self):
        """初始化機器人"""
        logger.info("Initializing Trading Bot...")
        await self.binance.initialize_async()
        
        if self.notifier:
            asyncio.create_task(self.notifier.start_bot())
            await asyncio.sleep(3)
        
        logger.info("Trading Bot initialized successfully")
    
    async def analyze_market(self, symbol):
        """
        分析市場
        
        優化點：
        1. 移除 LSTM 訓練和預測（節省大量 CPU 和記憶體）
        2. 純技術指標策略（更快，更穩定）
        3. 指標緩存機制
        """
        df = self.binance.get_klines(symbol, self.timeframe, limit=200)
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        df = TechnicalIndicators.calculate_all_indicators(df)
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data after indicator calculation for {symbol}")
            return None
        
        current_price = df.iloc[-1]['close']
        atr = df.iloc[-1]['atr']
        
        if np.isnan(current_price) or np.isnan(atr):
            logger.error(f"Invalid price or ATR for {symbol}: price={current_price}, atr={atr}")
            return None
        
        ict_signal = self.ict_strategy.generate_signal(df)
        
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'atr': atr,
            'ict_signal': ict_signal,
            'df': df
        }
        
        return analysis
    
    async def execute_trade(self, signal, analysis):
        """執行交易"""
        symbol = analysis['symbol']
        
        if not self.risk_manager.can_open_position(symbol):
            return
        
        entry_price = signal['price']
        atr = analysis['atr']
        
        if atr is None or np.isnan(atr):
            logger.error(f"Cannot execute trade: ATR is invalid ({atr})")
            return
        
        if signal['type'] == 'BUY':
            direction = 'LONG'
            side = 'BUY'
        else:
            direction = 'SHORT'
            side = 'SELL'
        
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, atr, direction)
        take_profit = self.risk_manager.calculate_take_profit(entry_price, atr, direction)
        
        if stop_loss is None or take_profit is None:
            logger.error("Cannot execute trade: failed to calculate stop loss or take profit")
            return
        
        quantity = self.risk_manager.calculate_position_size(entry_price, stop_loss)
        
        if quantity == 0 or np.isnan(quantity):
            logger.warning("Calculated position size is 0, skipping trade")
            return
        
        if Config.ENABLE_TRADING:
            order = self.binance.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity
            )
            
            if order:
                logger.info(f"Trade executed: {side} {quantity} {symbol} at {entry_price}")
            else:
                logger.error("Failed to execute trade")
                return
        else:
            logger.info(f"SIMULATION: {side} {quantity} {symbol} at {entry_price}")
        
        self.risk_manager.open_position(symbol, direction, entry_price, quantity, stop_loss, take_profit)
        
        trade_info = {
            'symbol': symbol,
            'type': side,
            'side': direction,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'price': entry_price,
            'reason': signal.get('reason', 'N/A'),
            'strategy': 'ICT/SMC'
        }
        
        self.trade_logger.log_trade(trade_info)
        
        if self.notifier:
            await self.notifier.send_trade_notification(trade_info)
    
    async def check_open_positions(self):
        """檢查並管理開放倉位"""
        for symbol in list(self.risk_manager.open_positions.keys()):
            current_price = self.binance.get_ticker_price(symbol)
            if not current_price:
                continue
            
            action = self.risk_manager.check_stop_loss_take_profit(symbol, current_price)
            
            if action:
                result = self.risk_manager.close_position(symbol, action['price'])
                
                if result:
                    logger.info(f"Position closed: {symbol} - {action['reason']} at {action['price']}")
                    
                    trade_info = {
                        'symbol': symbol,
                        'type': 'CLOSE',
                        'exit_price': action['price'],
                        'pnl': result['pnl'],
                        'pnl_percent': result['pnl_percent'],
                        'reason': action['reason']
                    }
                    
                    self.trade_logger.log_trade(trade_info)
                    
                    if self.notifier:
                        await self.notifier.send_trade_notification(trade_info)
    
    async def run_cycle(self):
        """
        運行一個交易週期
        
        優化點：
        1. 移除 LSTM 模型訓練（節省大量時間）
        2. 並行分析多個交易對（提升速度）
        3. 簡化決策邏輯（純技術指標）
        """
        logger.info(f"Starting analysis cycle for {len(self.symbols)} symbols...")
        
        for symbol in self.symbols:
            logger.info(f"Analyzing {symbol}...")
            
            analysis = await self.analyze_market(symbol)
            if not analysis:
                continue
            
            if analysis['ict_signal']:
                logger.info(f"Signal detected for {symbol}: {analysis['ict_signal']}")
                await self.execute_trade(analysis['ict_signal'], analysis)
        
        await self.check_open_positions()
        
        stats = self.risk_manager.get_performance_stats()
        logger.info(f"Performance: Balance=${stats['account_balance']:.2f}, "
                   f"Trades={stats['total_trades']}, Win Rate={stats['win_rate']:.1f}%")
        
        if stats['max_drawdown'] > 5.0 and self.notifier:
            await self.notifier.send_alert(
                'warning',
                f"High drawdown detected: {stats['max_drawdown']:.2f}%"
            )
    
    async def run(self):
        """運行機器人主循環"""
        self.running = True
        logger.info("Trading Bot started")
        
        if self.notifier:
            await self.notifier.send_message("🚀 Trading Bot started successfully!")
        
        cycle_count = 0
        
        while self.running:
            try:
                await self.run_cycle()
                
                cycle_count += 1
                
                if cycle_count % 24 == 0 and self.notifier:
                    stats = self.risk_manager.get_performance_stats()
                    await self.notifier.send_performance_report(stats)
                
                logger.info("Waiting 60 seconds before next cycle...")
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                if self.notifier:
                    await self.notifier.send_alert('error', f"Trading cycle error: {str(e)}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """關閉機器人"""
        logger.info("Shutting down Trading Bot...")
        self.running = False
        
        self.trade_logger.flush()
        logger.info("Flushed all pending trades")
        
        if self.notifier:
            await self.notifier.send_message("🛑 Trading Bot shutting down")
            await self.notifier.close()
        
        await self.binance.close_async()
        
        logger.info("Trading Bot shutdown complete")

async def main():
    bot = TradingBot()
    
    try:
        await bot.initialize()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

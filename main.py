import asyncio
import time
from datetime import datetime
from binance_client import BinanceDataClient
from strategies.ict_smc import ICTSMCStrategy
from strategies.arbitrage import ArbitrageStrategy
from models.lstm_model import LSTMPredictor
from risk_manager import RiskManager
from discord_bot import TradingBotNotifier
from trade_logger import TradeLogger
from utils.indicators import TechnicalIndicators
from utils.helpers import setup_logger
from config import Config

logger = setup_logger(__name__)

class TradingBot:
    def __init__(self):
        self.binance = BinanceDataClient()
        self.ict_strategy = ICTSMCStrategy()
        self.arbitrage_strategy = ArbitrageStrategy()
        self.lstm_predictor = LSTMPredictor()
        self.risk_manager = RiskManager()
        self.trade_logger = TradeLogger()
        self.notifier = TradingBotNotifier()
        
        self.symbols = Config.SYMBOLS
        self.timeframe = Config.TIMEFRAME
        self.running = False
        self.last_model_training = 0
    
    async def initialize(self):
        logger.info("Initializing Trading Bot...")
        await self.binance.initialize_async()
        
        asyncio.create_task(self.notifier.start_bot())
        await asyncio.sleep(3)
        
        logger.info("Trading Bot initialized successfully")
    
    async def train_models(self, symbol):
        logger.info(f"Training LSTM model for {symbol}...")
        
        df = self.binance.get_klines(symbol, self.timeframe, limit=500)
        if df is None or len(df) < 100:
            logger.warning(f"Insufficient data for training {symbol}")
            return
        
        df = TechnicalIndicators.calculate_all_indicators(df)
        
        success = self.lstm_predictor.train(df, epochs=30)
        if success:
            logger.info(f"Model training completed for {symbol}")
        else:
            logger.error(f"Model training failed for {symbol}")
    
    async def analyze_market(self, symbol):
        df = self.binance.get_klines(symbol, self.timeframe, limit=200)
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        df = TechnicalIndicators.calculate_all_indicators(df)
        
        current_price = df.iloc[-1]['close']
        atr = df.iloc[-1]['atr']
        
        ict_signal = self.ict_strategy.generate_signal(df)
        
        lstm_prediction = self.lstm_predictor.predict(df)
        
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'atr': atr,
            'ict_signal': ict_signal,
            'lstm_prediction': lstm_prediction,
            'df': df
        }
        
        return analysis
    
    async def execute_trade(self, signal, analysis):
        symbol = analysis['symbol']
        
        if not self.risk_manager.can_open_position(symbol):
            return
        
        entry_price = signal['price']
        atr = analysis['atr']
        
        if signal['type'] == 'BUY':
            direction = 'LONG'
            side = 'BUY'
        else:
            direction = 'SHORT'
            side = 'SELL'
        
        stop_loss = self.risk_manager.calculate_stop_loss(entry_price, atr, direction)
        take_profit = self.risk_manager.calculate_take_profit(entry_price, atr, direction)
        
        quantity = self.risk_manager.calculate_position_size(entry_price, stop_loss)
        
        if quantity == 0:
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
        await self.notifier.send_trade_notification(trade_info)
    
    async def check_open_positions(self):
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
                    await self.notifier.send_trade_notification(trade_info)
    
    async def run_cycle(self):
        current_time = time.time()
        
        if current_time - self.last_model_training > Config.MODEL_RETRAIN_INTERVAL:
            for symbol in self.symbols:
                await self.train_models(symbol)
            self.last_model_training = current_time
        
        for symbol in self.symbols:
            logger.info(f"Analyzing {symbol}...")
            
            analysis = await self.analyze_market(symbol)
            if not analysis:
                continue
            
            if analysis['ict_signal']:
                logger.info(f"Signal detected for {symbol}: {analysis['ict_signal']}")
                
                if analysis['lstm_prediction']:
                    lstm_direction = analysis['lstm_prediction']['direction']
                    signal_type = analysis['ict_signal']['type']
                    
                    if (signal_type == 'BUY' and lstm_direction == 'UP') or \
                       (signal_type == 'SELL' and lstm_direction == 'DOWN'):
                        logger.info("LSTM prediction confirms signal")
                        await self.execute_trade(analysis['ict_signal'], analysis)
                    else:
                        logger.info("LSTM prediction does not confirm signal, skipping")
                else:
                    await self.execute_trade(analysis['ict_signal'], analysis)
        
        await self.check_open_positions()
        
        stats = self.risk_manager.get_performance_stats()
        logger.info(f"Performance: Balance=${stats['account_balance']:.2f}, "
                   f"Trades={stats['total_trades']}, Win Rate={stats['win_rate']:.1f}%")
        
        if stats['max_drawdown'] > 5.0:
            await self.notifier.send_alert(
                'warning',
                f"High drawdown detected: {stats['max_drawdown']:.2f}%"
            )
    
    async def run(self):
        self.running = True
        logger.info("Trading Bot started")
        
        await self.notifier.send_message("🚀 Trading Bot started successfully!")
        
        cycle_count = 0
        
        while self.running:
            try:
                await self.run_cycle()
                
                cycle_count += 1
                
                if cycle_count % 24 == 0:
                    stats = self.risk_manager.get_performance_stats()
                    await self.notifier.send_performance_report(stats)
                
                logger.info("Waiting 60 seconds before next cycle...")
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}")
                await self.notifier.send_alert('error', f"Trading cycle error: {str(e)}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        logger.info("Shutting down Trading Bot...")
        self.running = False
        
        await self.notifier.send_message("🛑 Trading Bot shutting down")
        await self.binance.close_async()
        await self.notifier.close()
        
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

"""
Cryptocurrency Trading Bot v3.0 - Modular Architecture

Main orchestrator that coordinates all services.
"""

import asyncio
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import configuration
from config import Config

# Import services
from services import DataService, StrategyEngine, ExecutionService, MonitoringService
from services.virtual_position_tracker import VirtualPositionTracker
from binance_client import BinanceClient
from discord_bot import TradingBotNotifier as DiscordBot
from risk_manager import RiskManager
from trade_logger import TradeLogger


class TradingBotV3:
    """
    Main trading bot orchestrator using modular service architecture.
    
    Services:
    - DataService: Market data with caching and rate limiting
    - StrategyEngine: Multi-strategy signal generation
    - ExecutionService: Position management and trade execution
    - MonitoringService: System metrics and alerts
    """
    
    def __init__(self):
        """Initialize trading bot with all services."""
        logger.info("="*70)
        logger.info("Initializing Cryptocurrency Trading Bot v3.2")
        logger.info("="*70)
        logger.info("🚀 Version 3.2 Features:")
        logger.info("  ✅ Dynamic Margin Sizing (3%-13% based on confidence)")
        logger.info("  ✅ Win-Rate Based Leverage (3-20x based on performance)")
        logger.info("  ✅ Exchange-Level Stop-Loss/Take-Profit Protection")
        logger.info("  ✅ Comprehensive Trade Logging for XGBoost ML")
        logger.info("  ✅ Virtual Position Tracking (Rank 4+ signals)")
        logger.info("="*70)
        
        # Core components (BinanceClient reads from Config automatically)
        self.binance = BinanceClient()
        
        self.risk_manager = RiskManager()
        self.trade_logger = TradeLogger(Config.TRADES_FILE)
        
        # Trading configuration（先定義，因為後面 ExecutionService 需要用）
        self.symbols = []
        self.timeframe = Config.TIMEFRAME
        self.cycle_interval = 60  # seconds
        
        # Initialize Discord bot (will be started separately)
        self.discord = None
        if Config.DISCORD_BOT_TOKEN:
            try:
                self.discord = DiscordBot(risk_manager=self.risk_manager)
                logger.info("Discord bot initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Discord bot: {e}")
        
        # Initialize services
        self.data_service = DataService(
            binance_client=self.binance,
            batch_size=50  # Concurrent fetch 50 symbols at a time
        )
        
        self.strategy_engine = StrategyEngine(
            risk_manager=self.risk_manager,
            data_service=self.data_service  # v3.1: 傳遞 DataService 用於緩存
        )
        
        self.execution_service = ExecutionService(
            binance_client=self.binance,
            risk_manager=self.risk_manager,
            discord_bot=self.discord,
            enable_trading=Config.ENABLE_TRADING,
            trade_logger=self.trade_logger  # 📊 傳遞 trade_logger 供 XGBoost 學習
        )
        
        logger.info(f"⚙️  Trading mode: {'🔴 LIVE' if Config.ENABLE_TRADING else '🟡 SIMULATION'}")
        
        # 註冊平倉後立即重新掃描回調
        self.execution_service.on_position_closed_callback = self.rescan_symbol_immediately
        logger.info("Registered position closed callback for immediate rescan")
        
        # 設置信號驗證所需的引用
        self.execution_service.strategy_engine = self.strategy_engine
        self.execution_service.data_service = self.data_service
        self.execution_service.timeframe = self.timeframe  # 傳遞時間框架配置
        logger.info(f"Configured dynamic position validation (timeframe: {self.timeframe})")
        
        self.monitoring_service = MonitoringService(
            discord_bot=self.discord
        )
        
        # Initialize Virtual Position Tracker
        self.virtual_tracker = VirtualPositionTracker(
            trade_logger=self.trade_logger,
            risk_manager=self.risk_manager,
            binance_client=self.binance,
            max_virtual_positions=Config.MAX_VIRTUAL_POSITIONS,
            min_confidence=Config.VIRTUAL_MIN_CONFIDENCE,
            max_age_cycles=Config.VIRTUAL_MAX_AGE_CYCLES
        )
        
        # State
        self.is_running = False
        self.cycle_count = 0
        
        logger.info("All services initialized successfully")
    
    async def initialize(self):
        """Initialize trading symbols and verify connections."""
        logger.info("\n" + "="*70)
        logger.info("Initializing Trading Bot")
        logger.info("="*70)
        
        # 運行健康檢查（僅在實盤模式）
        if Config.ENABLE_TRADING:
            logger.info("🏥 實盤模式：運行啟動健康檢查...")
            try:
                from health_check import HealthChecker
                checker = HealthChecker()
                health_ok = await checker.run_all_checks()
                if not health_ok:
                    logger.error("⚠️  健康檢查未完全通過，但繼續啟動（請檢查警告）")
            except Exception as e:
                logger.warning(f"健康檢查執行失敗: {e}，繼續啟動")
        
        # Get trading symbols based on mode
        try:
            if Config.SYMBOL_MODE == 'all':
                logger.info("Fetching ALL USDT perpetual contracts...")
                self.symbols = await self.binance.get_usdt_perpetual_symbols()
                logger.info(f"✅ Monitoring {len(self.symbols)} USDT perpetual contracts")
                
            elif Config.SYMBOL_MODE == 'auto':
                logger.info(f"Auto-selecting top {Config.MAX_SYMBOLS} pairs by volume...")
                all_symbols = await self.binance.get_usdt_perpetual_symbols()
                # Future: Sort by volume and take top N
                self.symbols = all_symbols[:Config.MAX_SYMBOLS]
                logger.info(f"✅ Selected {len(self.symbols)} trading pairs")
                
            else:  # static
                self.symbols = Config.STATIC_SYMBOLS
                logger.info(f"✅ Using {len(self.symbols)} static symbols")
            
        except Exception as e:
            logger.error(f"Failed to get trading symbols: {e}")
            self.symbols = Config.STATIC_SYMBOLS
            logger.info(f"Fallback to {len(self.symbols)} static symbols")
        
        # Verify API connections
        await self._verify_connections()
        
        # 🔥 預熱緩存：加載所有 symbols 的 1h/15m 趨勢數據（v3.1 優化）
        logger.info("\n" + "="*70)
        logger.info("🔥 Prewarming Cache for Trend Data")
        logger.info("="*70)
        try:
            await self.data_service.prewarm_cache(
                symbols=self.symbols,
                timeframes=['15m', '1h']  # 預熱 15m 和 1h 數據
            )
            logger.info("✅ Cache prewarming complete - ready for analysis")
        except Exception as e:
            logger.warning(f"⚠️  Cache prewarming failed: {e}, continuing anyway...")
        
        # 🔒 加載並保護現有倉位（重啟後恢復倉位狀態）
        logger.info("\n" + "="*70)
        logger.info("🔒 Loading & Protecting Existing Positions from Binance")
        logger.info("="*70)
        
        # 從 Binance API 加載真實持倉到內存
        loaded_count = await self.execution_service.load_positions_from_binance()
        
        # 為這些持倉設置交易所級別的止損/止盈保護
        if loaded_count > 0:
            await self.execution_service.set_protection_for_existing_positions()
        else:
            logger.info("No existing positions found, skipping protection setup")
        
        logger.info("\n" + "="*70)
        logger.info("✅ Initialization Complete - Bot Ready")
        logger.info("="*70)
        logger.info(f"📊 Monitoring: {len(self.symbols)} symbols")
        logger.info(f"⏱️  Timeframe: {self.timeframe}")
        logger.info(f"🔄 Cycle interval: {self.cycle_interval}s")
        logger.info(f"💰 Account Balance: ${self.risk_manager.account_balance:,.2f} USDT")
        logger.info(f"📍 Max Positions: {self.execution_service.max_positions}")
        logger.info(f"💵 Capital per Position: ${self.risk_manager.account_balance/3:,.2f} USDT")
        logger.info(f"📈 Trading Mode: {'LIVE TRADING' if Config.ENABLE_TRADING else 'SIMULATION (Paper Trading)'}")
        logger.info("="*70 + "\n")
    
    async def _verify_connections(self):
        """Verify all API connections and load account balance."""
        # Test Binance
        try:
            await self.binance.get_ticker('BTCUSDT')
            self.monitoring_service.update_health('binance_api', 'healthy')
            logger.info("✅ Binance API connection verified")
        except Exception as e:
            self.monitoring_service.update_health('binance_api', 'unhealthy')
            logger.error(f"❌ Binance API connection failed: {e}")
        
        # Always attempt to load balance (will use default if fails)
        await self._load_account_balance()
        
        # Test Discord
        if self.discord:
            self.monitoring_service.update_health('discord_api', 'healthy')
            logger.info("✅ Discord bot ready")
        else:
            self.monitoring_service.update_health('discord_api', 'unhealthy')
    
    async def _load_account_balance(self):
        """Load real account balance from Binance and update RiskManager."""
        try:
            # 讀取 Binance 期貨帳戶實際餘額
            loop = asyncio.get_event_loop()
            actual_balance = await loop.run_in_executor(None, self.binance.get_futures_balance)
            
            # 區分 API 失敗（None）和實際餘額為 0（0.0）
            if actual_balance is not None:
                self.risk_manager.update_balance(actual_balance)
                if actual_balance > 0:
                    logger.info(f"💰 從 Binance 讀取實際餘額: ${actual_balance:.2f} USDT")
                else:
                    logger.warning(f"⚠️ Binance 帳戶餘額為 0 USDT！無法進行交易")
            else:
                logger.warning(f"⚠️ 無法讀取 Binance 餘額（API 失敗），使用默認值: ${self.risk_manager.account_balance:.2f} USDT")
        except Exception as e:
            logger.error(f"❌ 讀取 Binance 餘額失敗: {e}，使用默認值: ${self.risk_manager.account_balance:.2f} USDT")
    
    async def rescan_symbol_immediately(self, symbol: str):
        """
        立即重新掃描單一交易對並嘗試開倉。
        在倉位平倉後觸發，不等待下一個週期。
        
        Args:
            symbol: 要重新掃描的交易對
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"🔄 立即重新掃描 {symbol} - 倉位已平倉")
            logger.info(f"{'='*70}")
            
            # 檢查是否還有空閒倉位
            current_positions = len(self.execution_service.positions)
            available_slots = self.execution_service.max_positions - current_positions
            
            if available_slots <= 0:
                logger.info(f"ℹ️  無可用倉位槽位 ({current_positions}/{self.execution_service.max_positions})")
                return
            
            # 獲取該交易對的最新數據（強制刷新，繞過緩存）
            logger.info(f"📥 獲取 {symbol} 最新數據（強制刷新）...")
            klines = await self.data_service.fetch_klines(
                symbol=symbol,
                timeframe=self.timeframe,
                limit=200,
                force_refresh=True  # 繞過緩存，確保獲取最新數據
            )
            
            if klines is None or klines.empty:
                logger.warning(f"⚠️  無法獲取 {symbol} 數據")
                return
            
            # 分析該交易對
            current_price = float(klines.iloc[-1]['close'])
            logger.info(f"🔍 分析 {symbol} @ {current_price:.4f}...")
            
            symbols_data = {symbol: (klines, current_price)}
            signals = await self.strategy_engine.analyze_batch(symbols_data)
            
            if not signals:
                logger.info(f"ℹ️  {symbol} 未產生新信號")
                return
            
            # 執行信號
            signal = signals[0]
            logger.info(
                f"🎯 發現新信號: {signal.action} @ {signal.price:.4f} "
                f"(信心度: {signal.confidence:.1f}%, ROI: {signal.expected_roi:.2f}%)"
            )
            
            success = await self.execution_service.execute_signal(signal)
            
            if success:
                logger.info(f"✅ {symbol} 立即重新開倉成功")
                if self.discord:
                    await self.discord.send_alert(
                        "trade",
                        f"⚡ **快速重新進場**\n"
                        f"交易對: {symbol}\n"
                        f"方向: {signal.action}\n"
                        f"價格: {signal.price:.4f}\n"
                        f"信心度: {signal.confidence:.1f}%\n"
                        f"預期投報率: {signal.expected_roi:.2f}%\n"
                        f"_平倉後立即重新掃描_"
                    )
            else:
                logger.info(f"ℹ️  {symbol} 重新開倉被拒絕")
            
            logger.info(f"{'='*70}\n")
            
        except Exception as e:
            logger.error(f"重新掃描 {symbol} 時發生錯誤: {e}", exc_info=True)
    
    async def run_cycle(self):
        """Execute one complete trading cycle."""
        self.cycle_count += 1
        cycle_start = asyncio.get_event_loop().time()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 Trading Cycle #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*70}")
        
        # 每個交易週期更新帳戶餘額
        try:
            loop = asyncio.get_event_loop()
            current_balance = await loop.run_in_executor(None, self.binance.get_futures_balance)
            
            # 區分 API 失敗（None）和實際餘額為 0（0.0）
            if current_balance is not None:
                old_balance = self.risk_manager.account_balance
                self.risk_manager.update_balance(current_balance)
                
                # 只有當餘額變化超過 1% 時才記錄（避免日誌過多，防止除以零）
                if old_balance > 0:
                    balance_change_percent = abs(current_balance - old_balance) / old_balance * 100
                    if balance_change_percent > 1.0:
                        logger.info(f"💰 帳戶餘額更新: ${old_balance:.2f} → ${current_balance:.2f} USDT ({balance_change_percent:+.2f}%)")
                elif current_balance != old_balance:
                    # 餘額從 0 變化或變為 0
                    logger.info(f"💰 帳戶餘額更新: ${old_balance:.2f} → ${current_balance:.2f} USDT")
        except Exception as e:
            logger.debug(f"餘額更新失敗: {e}")
        
        try:
            # Step 1: Fetch market data (concurrent batch fetching)
            logger.info(f"📥 Fetching data for {len(self.symbols)} symbols...")
            fetch_start = asyncio.get_event_loop().time()
            
            klines_data = await self.data_service.fetch_klines_batch(
                symbols=self.symbols,
                timeframe=self.timeframe,
                limit=200
            )
            
            fetch_time = asyncio.get_event_loop().time() - fetch_start
            self.monitoring_service.record_metric('fetch_time_seconds', fetch_time)
            logger.info(f"✅ Fetched data in {fetch_time:.2f}s")
            
            # Step 2: Analyze all symbols and generate signals
            logger.info(f"🔍 Analyzing market data...")
            analysis_start = asyncio.get_event_loop().time()
            
            # Prepare data for analysis (ADD TECHNICAL INDICATORS!)
            from utils.indicators import TechnicalIndicators
            
            symbols_data = {}
            for symbol, df in klines_data.items():
                if df is not None and not df.empty:
                    # 添加技術指標（MACD、EMA、ATR等）
                    df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
                    
                    if df_with_indicators is not None and not df_with_indicators.empty:
                        current_price = float(df_with_indicators.iloc[-1]['close'])
                        symbols_data[symbol] = (df_with_indicators, current_price)
            
            # Run analysis (v3.1: 使用 DataService 緩存獲取趨勢數據)
            signals = await self.strategy_engine.analyze_batch(symbols_data, data_service=self.data_service)
            
            analysis_time = asyncio.get_event_loop().time() - analysis_start
            self.monitoring_service.record_metric('analysis_time_seconds', analysis_time)
            logger.info(f"✅ Analysis complete in {analysis_time:.2f}s - {len(signals)} signals generated")
            
            # Step 3: Rank and filter signals
            if signals:
                top_signals = self.strategy_engine.rank_signals(
                    signals=signals,
                    mode='confidence',  # or 'roi'
                    limit=self.execution_service.max_positions
                )
                
                logger.info(f"🎯 Top {len(top_signals)} signals selected:")
                for i, signal in enumerate(top_signals, 1):
                    logger.info(
                        f"  {i}. {signal.symbol}: {signal.action} @ {signal.price:.4f} "
                        f"(confidence: {signal.confidence:.1f}%, ROI: {signal.expected_roi:.2f}%)"
                    )
            else:
                top_signals = []
                logger.info("ℹ️  No signals generated this cycle")
            
            # Step 4: Execute signals (if any positions available)
            current_positions = len(self.execution_service.positions)
            available_slots = self.execution_service.max_positions - current_positions
            
            if available_slots > 0 and top_signals:
                logger.info(f"💼 Executing signals ({available_slots} slots available)...")
                
                for signal in top_signals[:available_slots]:
                    success = await self.execution_service.execute_signal(signal)
            
            # Step 5: Create virtual positions from remaining signals (rank 4+)
            if signals and len(signals) > 3:
                logger.info(f"🔷 Creating virtual positions from rank 4+ signals...")
                # Sort all signals by confidence (same as top_signals logic)
                sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)
                self.virtual_tracker.create_virtual_positions(sorted_signals, start_rank=4)
            
            # Step 6: Check existing virtual positions
            await self.virtual_tracker.check_virtual_positions(self.data_service)
            
            # Step 7: Monitor existing positions
            if self.execution_service.positions:
                closed = await self.execution_service.monitor_positions()
                if closed:
                    logger.info(f"🔄 Closed {len(closed)} positions: {', '.join(closed)}")
            
            # Step 8: Cleanup cache
            await self.data_service.cleanup_cache()
            
            # Calculate cycle time
            cycle_time = asyncio.get_event_loop().time() - cycle_start
            self.monitoring_service.record_metric('cycle_time_seconds', cycle_time)
            
            # Log summary
            logger.info(f"\n📊 Cycle Summary:")
            logger.info(f"  ⏱️  Total time: {cycle_time:.2f}s")
            logger.info(f"  📥 Fetch time: {fetch_time:.2f}s")
            logger.info(f"  🔍 Analysis time: {analysis_time:.2f}s")
            logger.info(f"  📊 Symbols analyzed: {len(symbols_data)}")
            logger.info(f"  🎯 Signals generated: {len(signals)}")
            logger.info(f"  💼 Active positions: {current_positions}/{self.execution_service.max_positions}")
            logger.info(f"{'='*70}\n")
            
            # Check for alerts
            data_stats = self.data_service.get_stats()
            api_error_rate = data_stats['data_service'].get('failed_fetches', 0) / max(data_stats['data_service'].get('total_fetches', 1), 1)
            
            await self.monitoring_service.check_alerts(
                current_drawdown=0,  # TODO: Calculate from positions
                api_error_rate=api_error_rate,
                scan_time=cycle_time
            )
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
            await self.monitoring_service.send_alert(
                f"Trading cycle error: {str(e)}",
                severity='critical'
            )
    
    async def run(self):
        """Main run loop."""
        self.is_running = True
        
        logger.info("\n🚀 Starting trading bot main loop")
        logger.info("Press Ctrl+C to stop\n")
        
        # Start Discord bot if available
        if self.discord:
            asyncio.create_task(self.discord.start_bot())
            await asyncio.sleep(2)  # Wait for Discord to connect
        
        try:
            while self.is_running:
                await self.run_cycle()
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {self.cycle_interval}s for next cycle...")
                await asyncio.sleep(self.cycle_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the bot."""
        logger.info("\n" + "="*70)
        logger.info("🛑 Shutting down trading bot...")
        logger.info("="*70)
        
        self.is_running = False
        
        # Save virtual positions
        logger.info("Saving virtual positions...")
        self.virtual_tracker.save_virtual_positions()
        
        # Close all positions if live trading
        if Config.ENABLE_TRADING and self.execution_service.positions:
            logger.info("Closing all positions...")
            for symbol in list(self.execution_service.positions.keys()):
                try:
                    ticker = await self.binance.get_ticker(symbol)
                    if ticker:
                        price = float(ticker.get('lastPrice', 0))
                        await self.execution_service.close_position(symbol, price, "shutdown")
                except Exception as e:
                    logger.error(f"Error closing {symbol}: {e}")
        
        # Export monitoring data
        self.monitoring_service.export_metrics()
        
        # Log final statistics
        logger.info("\n📊 Final Statistics:")
        stats = self.monitoring_service.get_trading_stats(
            self.data_service,
            self.strategy_engine,
            self.execution_service
        )
        
        for service_name, service_stats in stats.items():
            logger.info(f"\n{service_name}:")
            for key, value in service_stats.items():
                logger.info(f"  {key}: {value}")
        
        logger.info("\n✅ Shutdown complete")
        logger.info("="*70)


async def main():
    """Main entry point."""
    try:
        bot = TradingBotV3()
        await bot.initialize()
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

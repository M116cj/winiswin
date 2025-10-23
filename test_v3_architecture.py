"""
Test script for v3.0 architecture components.

Tests:
1. Core utilities (RateLimiter, CircuitBreaker, CacheManager)
2. DataService
3. StrategyEngine
4. ExecutionService
5. MonitoringService
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_core_utilities():
    """Test core utilities."""
    from core import RateLimiter, CircuitBreaker, CacheManager
    
    logger.info("\n" + "="*70)
    logger.info("Testing Core Utilities")
    logger.info("="*70)
    
    # Test RateLimiter
    logger.info("\n1. Testing RateLimiter...")
    limiter = RateLimiter(requests_per_minute=60)
    
    # Acquire some tokens
    for i in range(5):
        acquired = await limiter.acquire(tokens=1)
        logger.info(f"  Token {i+1}: {'✅ Acquired' if acquired else '❌ Denied'}")
    
    stats = limiter.get_stats()
    logger.info(f"  Stats: {stats}")
    
    # Test CircuitBreaker
    logger.info("\n2. Testing CircuitBreaker...")
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5, name="TestAPI")
    
    async def failing_func():
        raise Exception("Simulated failure")
    
    async def success_func():
        return "Success"
    
    # Trigger failures
    for i in range(4):
        try:
            await breaker.call(failing_func)
        except:
            logger.info(f"  Failure {i+1}: Circuit state = {breaker.get_state().value}")
    
    # Test CacheManager
    logger.info("\n3. Testing CacheManager...")
    cache = CacheManager(max_size=100, default_ttl=60)
    
    await cache.set('test_key', 'test_value')
    value = await cache.get('test_key')
    logger.info(f"  Cache set/get: {'✅ Pass' if value == 'test_value' else '❌ Fail'}")
    
    cache_stats = cache.get_stats()
    logger.info(f"  Stats: {cache_stats}")
    
    logger.info("\n✅ Core utilities tests complete")


async def test_services():
    """Test all services."""
    from services import DataService, StrategyEngine, ExecutionService, MonitoringService
    from binance_client import BinanceClient
    from risk_manager import RiskManager
    from config import Config
    
    logger.info("\n" + "="*70)
    logger.info("Testing Services")
    logger.info("="*70)
    
    # Initialize components (reads from Config automatically)
    binance = BinanceClient()
    risk_manager = RiskManager()
    
    # Test DataService
    logger.info("\n1. Testing DataService...")
    data_service = DataService(binance, batch_size=10)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    klines_data = await data_service.fetch_klines_batch(symbols, '1h', 100)
    
    successful = len([k for k in klines_data.values() if k is not None])
    logger.info(f"  Fetched {successful}/{len(symbols)} symbols")
    logger.info(f"  Stats: {data_service.get_stats()}")
    
    # Test StrategyEngine
    logger.info("\n2. Testing StrategyEngine...")
    strategy_engine = StrategyEngine(risk_manager)
    
    if klines_data['BTCUSDT'] is not None:
        signal = await strategy_engine.analyze_symbol(
            'BTCUSDT',
            klines_data['BTCUSDT'],
            float(klines_data['BTCUSDT'].iloc[-1]['close'])
        )
        logger.info(f"  Signal generated: {'✅ Yes' if signal else 'ℹ️  None'}")
        if signal:
            logger.info(f"    {signal.symbol}: {signal.action} @ {signal.price:.2f} (confidence: {signal.confidence:.1f}%)")
    
    # Test ExecutionService
    logger.info("\n3. Testing ExecutionService...")
    execution_service = ExecutionService(binance, risk_manager, enable_trading=False)
    
    logger.info(f"  Max positions: {execution_service.max_positions}")
    logger.info(f"  Active positions: {len(execution_service.positions)}")
    logger.info(f"  Stats: {execution_service.get_stats()}")
    
    # Test MonitoringService
    logger.info("\n4. Testing MonitoringService...")
    monitoring_service = MonitoringService()
    
    monitoring_service.record_metric('test_metric', 42.0)
    monitoring_service.update_health('test_component', 'healthy')
    
    health = monitoring_service.get_system_health()
    logger.info(f"  System health: {health['overall']}")
    logger.info(f"  Stats: {monitoring_service.get_stats()}")
    
    logger.info("\n✅ All services tests complete")


async def test_integration():
    """Test integration between services."""
    logger.info("\n" + "="*70)
    logger.info("Testing Service Integration")
    logger.info("="*70)
    
    from services import DataService, StrategyEngine, ExecutionService, MonitoringService
    from binance_client import BinanceClient
    from risk_manager import RiskManager
    from config import Config
    
    # Initialize all services (reads from Config automatically)
    binance = BinanceClient()
    risk_manager = RiskManager()
    
    data_service = DataService(binance, batch_size=10)
    strategy_engine = StrategyEngine(risk_manager)
    execution_service = ExecutionService(binance, risk_manager, enable_trading=False)
    monitoring_service = MonitoringService()
    
    # Simulate one trading cycle
    logger.info("\n📊 Simulating trading cycle...")
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    # 1. Fetch data
    logger.info("  1. Fetching market data...")
    klines_data = await data_service.fetch_klines_batch(symbols, '1h', 200)
    logger.info(f"     ✅ Fetched {len([k for k in klines_data.values() if k is not None])} symbols")
    
    # 2. Analyze and generate signals
    logger.info("  2. Analyzing market...")
    symbols_data = {}
    for symbol, df in klines_data.items():
        if df is not None and not df.empty:
            current_price = float(df.iloc[-1]['close'])
            symbols_data[symbol] = (df, current_price)
    
    signals = await strategy_engine.analyze_batch(symbols_data)
    logger.info(f"     ✅ Generated {len(signals)} signals")
    
    # 3. Rank signals
    if signals:
        logger.info("  3. Ranking signals...")
        top_signals = strategy_engine.rank_signals(signals, mode='confidence', limit=3)
        logger.info(f"     ✅ Selected top {len(top_signals)} signals")
        
        # 4. Execute (simulated)
        logger.info("  4. Executing signals (simulated)...")
        for signal in top_signals:
            success = await execution_service.execute_signal(signal)
            logger.info(f"     {'✅' if success else '❌'} {signal.symbol}: {signal.action}")
    
    # 5. Get aggregated stats
    logger.info("\n📊 Aggregated Statistics:")
    stats = monitoring_service.get_trading_stats(
        data_service,
        strategy_engine,
        execution_service
    )
    
    for service_name, service_stats in stats.items():
        logger.info(f"\n  {service_name}:")
        for key, value in list(service_stats.items())[:5]:  # Show first 5 items
            logger.info(f"    {key}: {value}")
    
    logger.info("\n✅ Integration test complete")


async def main():
    """Run all tests."""
    logger.info("\n" + "="*70)
    logger.info("Trading Bot v3.0 Architecture Tests")
    logger.info("="*70)
    
    try:
        await test_core_utilities()
        await test_services()
        await test_integration()
        
        logger.info("\n" + "="*70)
        logger.info("✅ All tests passed!")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())

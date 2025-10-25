"""
Data Service - Centralized market data management with caching and rate limiting.

Responsibilities:
- Concurrent batch kline fetching
- Incremental caching
- Rate limit management
- Data validation
"""

import asyncio
from typing import List, Dict, Optional, Any
import pandas as pd
import logging
from datetime import datetime, timedelta

from core.rate_limiter import APIRateLimitManager
from core.circuit_breaker import CircuitBreaker
from core.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class DataService:
    """Centralized service for market data operations."""
    
    def __init__(self, binance_client, batch_size: int = 50):
        """
        Initialize data service.
        
        Args:
            binance_client: Binance API client
            batch_size: Number of symbols to fetch concurrently
        """
        self.binance = binance_client
        self.batch_size = batch_size
        
        # Core utilities
        self.rate_limiter = APIRateLimitManager()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            name="BinanceAPI"
        )
        self.cache = CacheManager(max_size=1000, default_ttl=30.0)
        
        # Statistics
        self.stats = {
            'total_fetches': 0,
            'cache_hits': 0,
            'failed_fetches': 0,
            'total_time': 0.0
        }
        
        logger.info(f"DataService initialized: batch_size={batch_size}")
    
    async def fetch_klines_batch(
        self,
        symbols: List[str],
        timeframe: str = '1h',
        limit: int = 200
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Fetch klines for multiple symbols concurrently.
        
        Args:
            symbols: List of trading symbols
            timeframe: Candlestick timeframe
            limit: Number of candles to fetch
            
        Returns:
            Dict mapping symbol to DataFrame (or None if failed)
        """
        start_time = asyncio.get_event_loop().time()
        results = {}
        
        # Split into batches to avoid overwhelming the API
        for i in range(0, len(symbols), self.batch_size):
            batch = symbols[i:i + self.batch_size]
            
            # Fetch batch concurrently
            batch_results = await asyncio.gather(
                *[self._fetch_single_kline(sym, timeframe, limit) for sym in batch],
                return_exceptions=True
            )
            
            # Process results
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching {symbol}: {result}")
                    results[symbol] = None
                    self.stats['failed_fetches'] += 1
                else:
                    results[symbol] = result
                    self.stats['total_fetches'] += 1
            
            # Yield control to event loop (Discord heartbeat fix)
            await asyncio.sleep(0.1)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        self.stats['total_time'] += elapsed
        
        logger.info(
            f"Fetched {len([r for r in results.values() if r is not None])}/{len(symbols)} symbols "
            f"in {elapsed:.2f}s"
        )
        
        return results
    
    async def fetch_klines(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 200,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch klines for a single symbol (public method).
        
        Args:
            symbol: Trading symbol
            timeframe: Candlestick timeframe
            limit: Number of candles
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            DataFrame or None if failed
        """
        return await self._fetch_single_kline(symbol, timeframe, limit, force_refresh)
    
    async def _fetch_single_kline(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        force_refresh: bool = False,
        ttl: Optional[float] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch klines for a single symbol with caching and rate limiting.
        
        Args:
            symbol: Trading symbol
            timeframe: Candlestick timeframe
            limit: Number of candles
            force_refresh: If True, bypass cache and fetch fresh data
            ttl: Custom cache TTL in seconds (if None, uses timeframe-based TTL)
            
        Returns:
            DataFrame or None if failed
        """
        cache_key = f"{symbol}:{timeframe}:{limit}"
        
        # Check cache first (unless force_refresh is True)
        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                self.stats['cache_hits'] += 1
                return cached
        
        # Acquire rate limit token
        if not await self.rate_limiter.acquire(weight=1, endpoint='api'):
            logger.warning(f"Rate limit timeout for {symbol}")
            return None
        
        try:
            # Initialize async client if needed
            if not self.binance.async_client:
                await self.binance.initialize_async()
            
            # TRUE async fetch with circuit breaker protection (non-blocking I/O)
            async def fetch_async():
                return await self.binance.get_klines_async(symbol, timeframe, limit)
            
            df = await self.circuit_breaker.call(fetch_async)
            
            if df is not None and not df.empty:
                # Determine TTL based on timeframe if not specified
                if ttl is None:
                    ttl = self._get_ttl_for_timeframe(timeframe)
                
                # Cache the result with appropriate TTL
                await self.cache.set(cache_key, df, ttl=ttl)
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
    
    def _get_ttl_for_timeframe(self, timeframe: str) -> float:
        """
        Get appropriate cache TTL based on timeframe.
        
        Args:
            timeframe: Candlestick timeframe (e.g., '1m', '15m', '1h')
            
        Returns:
            TTL in seconds
        """
        # Timeframe-based TTL mapping
        ttl_mapping = {
            '1m': 30.0,      # 1分鐘數據：30秒緩存
            '5m': 150.0,     # 5分鐘數據：2.5分鐘緩存
            '15m': 900.0,    # 15分鐘數據：15分鐘緩存
            '30m': 1800.0,   # 30分鐘數據：30分鐘緩存
            '1h': 3600.0,    # 1小時數據：1小時緩存
            '4h': 7200.0,    # 4小時數據：2小時緩存
            '1d': 14400.0,   # 1天數據：4小時緩存
        }
        
        return ttl_mapping.get(timeframe, 30.0)  # 默認30秒
    
    async def get_ticker_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get 24h ticker information for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker info dict or None
        """
        cache_key = f"ticker:{symbol}"
        
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            if not await self.rate_limiter.acquire(weight=1):
                return None
            
            ticker = await self.circuit_breaker.call(
                self.binance.get_ticker,
                symbol
            )
            
            if ticker:
                await self.cache.set(cache_key, ticker, ttl=10.0)
            
            return ticker
            
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    async def cleanup_cache(self):
        """Remove expired cache entries."""
        await self.cache.cleanup_expired()
    
    async def prewarm_cache(
        self,
        symbols: List[str],
        timeframes: List[str] = ['15m', '1h']
    ) -> Dict[str, Dict[str, int]]:
        """
        Prewarm cache by fetching trend data for all symbols.
        
        This method is called on startup to populate the cache with 1h and 15m data,
        avoiding bulk API calls during the first analysis cycle.
        
        Args:
            symbols: List of trading symbols
            timeframes: List of timeframes to prewarm (default: ['15m', '1h'])
            
        Returns:
            Dict with statistics (successful, failed counts per timeframe)
        """
        logger.info(f"🔥 Prewarming cache for {len(symbols)} symbols across {len(timeframes)} timeframes...")
        
        stats = {tf: {'success': 0, 'failed': 0} for tf in timeframes}
        
        for timeframe in timeframes:
            logger.info(f"   ⏰ Fetching {timeframe} data for {len(symbols)} symbols...")
            
            # Fetch all symbols for this timeframe concurrently
            results = await self.fetch_klines_batch(
                symbols=symbols,
                timeframe=timeframe,
                limit=250  # Need 250 for EMA200 calculation
            )
            
            # Count successes and failures
            for symbol, df in results.items():
                if df is not None and not df.empty:
                    stats[timeframe]['success'] += 1
                else:
                    stats[timeframe]['failed'] += 1
            
            logger.info(
                f"   ✅ {timeframe}: {stats[timeframe]['success']} succeeded, "
                f"{stats[timeframe]['failed']} failed"
            )
        
        total_success = sum(s['success'] for s in stats.values())
        total_failed = sum(s['failed'] for s in stats.values())
        
        logger.info(
            f"🔥 Cache prewarming complete: {total_success} successful, {total_failed} failed"
        )
        
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get data service statistics."""
        cache_stats = self.cache.get_stats()
        rate_limit_stats = self.rate_limiter.get_all_stats()
        circuit_stats = self.circuit_breaker.get_stats()
        
        avg_fetch_time = (
            self.stats['total_time'] / self.stats['total_fetches']
            if self.stats['total_fetches'] > 0
            else 0
        )
        
        return {
            'data_service': {
                **self.stats,
                'avg_fetch_time': avg_fetch_time,
                'success_rate': (
                    (self.stats['total_fetches'] - self.stats['failed_fetches']) /
                    max(self.stats['total_fetches'], 1)
                )
            },
            'cache': cache_stats,
            'rate_limiter': rate_limit_stats,
            'circuit_breaker': circuit_stats
        }
    
    def reset_stats(self):
        """Reset all statistics."""
        self.stats = {
            'total_fetches': 0,
            'cache_hits': 0,
            'failed_fetches': 0,
            'total_time': 0.0
        }
        self.cache.reset_stats()
        self.rate_limiter.reset_all_stats()
        self.circuit_breaker.reset_stats()

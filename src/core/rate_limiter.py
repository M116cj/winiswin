"""
Rate limiter using Token Bucket algorithm for Binance API.

Binance API Limits:
- Weight limit: 1200 requests/minute
- Order limit: 100 orders/10 seconds
"""

import time
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token Bucket rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 1200, burst_size: Optional[int] = None):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.capacity = burst_size or requests_per_minute
        self.tokens = float(self.capacity)
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
        # Statistics
        self.total_requests = 0
        self.denied_requests = 0
        
        logger.info(f"RateLimiter initialized: {requests_per_minute} req/min, capacity: {self.capacity}")
    
    async def acquire(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum wait time in seconds
            
        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()
        
        async with self.lock:
            while True:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.total_requests += 1
                    return True
                
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.denied_requests += 1
                    logger.warning(f"Rate limit timeout after {elapsed:.2f}s")
                    return False
                
                wait_time = min((tokens - self.tokens) / self.rate, timeout - elapsed)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        if elapsed > 0:
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        async with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                self.total_requests += 1
                return True
            else:
                self.denied_requests += 1
                return False
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            'total_requests': self.total_requests,
            'denied_requests': self.denied_requests,
            'denial_rate': self.denied_requests / max(self.total_requests, 1),
            'current_tokens': self.tokens,
            'capacity': self.capacity,
            'utilization': 1.0 - (self.tokens / self.capacity)
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.total_requests = 0
        self.denied_requests = 0


class APIRateLimitManager:
    """Manages multiple rate limiters for different API endpoints."""
    
    def __init__(self):
        """Initialize rate limit manager with Binance-specific limits."""
        self.limiters = {
            'api': RateLimiter(requests_per_minute=1200),  # General API limit
            'orders': RateLimiter(requests_per_minute=600),  # Order endpoints (more conservative)
        }
        logger.info("APIRateLimitManager initialized with Binance limits")
    
    async def acquire(self, endpoint: str = 'api', weight: int = 1) -> bool:
        """
        Acquire tokens for an API endpoint.
        
        Args:
            endpoint: Endpoint type ('api' or 'orders')
            weight: Request weight (some endpoints use more weight)
            
        Returns:
            True if acquired, False if timeout
        """
        limiter = self.limiters.get(endpoint, self.limiters['api'])
        return await limiter.acquire(tokens=weight)
    
    async def try_acquire(self, endpoint: str = 'api', weight: int = 1) -> bool:
        """Try to acquire tokens without waiting."""
        limiter = self.limiters.get(endpoint, self.limiters['api'])
        return await limiter.try_acquire(tokens=weight)
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all rate limiters."""
        return {name: limiter.get_stats() for name, limiter in self.limiters.items()}
    
    def reset_all_stats(self):
        """Reset all statistics."""
        for limiter in self.limiters.values():
            limiter.reset_stats()

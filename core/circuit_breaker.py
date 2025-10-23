"""
Circuit Breaker pattern for fault tolerance and graceful degradation.
"""

import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Test if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            expected_exception: Exception type to catch
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = asyncio.Lock()
        
        # Statistics
        self.total_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0
        
        logger.info(f"CircuitBreaker '{name}' initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        self.total_calls += 1
        
        async with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"CircuitBreaker '{self.name}' entering HALF_OPEN state")
                else:
                    self.rejected_calls += 1
                    raise Exception(f"CircuitBreaker '{self.name}' is OPEN - rejecting request")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.expected_exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call."""
        async with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"CircuitBreaker '{self.name}' closed - service recovered")
            
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """Handle failed call."""
        self.failed_calls += 1
        
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"CircuitBreaker '{self.name}' OPENED - "
                    f"{self.failure_count} failures exceeded threshold {self.failure_threshold}"
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False
        
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'total_calls': self.total_calls,
            'failed_calls': self.failed_calls,
            'rejected_calls': self.rejected_calls,
            'failure_rate': self.failed_calls / max(self.total_calls, 1),
            'rejection_rate': self.rejected_calls / max(self.total_calls, 1)
        }
    
    async def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        async with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"CircuitBreaker '{self.name}' manually reset")
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.total_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0

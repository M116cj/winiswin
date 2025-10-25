"""
Strategy Engine - Multi-strategy analysis and signal generation.

Responsibilities:
- Execute technical analysis across strategies
- Multi-factor signal scoring
- Signal filtering and ranking
- Strategy performance tracking
"""

import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import pandas as pd
import logging

from src.strategies.ict_smc import ICTSMCStrategy

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal with metadata."""
    symbol: str
    action: str  # 'BUY' or 'SELL'
    price: float
    confidence: float
    expected_roi: float
    stop_loss: float
    take_profit: float
    strategy: str
    timestamp: float
    metadata: Dict[str, Any]


class StrategyEngine:
    """Engine for running multiple trading strategies and ranking signals."""
    
    def __init__(self, risk_manager, data_service=None):
        """
        Initialize strategy engine.
        
        Args:
            risk_manager: Risk management instance
            data_service: DataService instance for cached market data
        """
        self.risk_manager = risk_manager
        self.data_service = data_service
        
        # Initialize strategies
        self.strategies = {
            'ict_smc': ICTSMCStrategy()
        }
        
        # Statistics
        self.stats = {
            'total_analyses': 0,
            'signals_generated': 0,
            'signals_filtered': 0,
            'strategy_stats': {name: {'analyses': 0, 'signals': 0} 
                              for name in self.strategies.keys()}
        }
        
        logger.info(f"StrategyEngine initialized with {len(self.strategies)} strategies")
    
    async def analyze_symbol(
        self,
        symbol: str,
        df: pd.DataFrame,
        current_price: float,
        data_service=None
    ) -> Optional[Signal]:
        """
        Analyze a single symbol across all strategies.
        
        Args:
            symbol: Trading symbol
            df: Price data DataFrame
            current_price: Current market price
            data_service: DataService instance (for cached trend data)
            
        Returns:
            Signal object or None
        """
        self.stats['total_analyses'] += 1
        
        # Use data_service from instance if not provided
        if data_service is None:
            data_service = self.data_service
        
        # For now, use ICT/SMC strategy
        # Future: Run multiple strategies and combine signals
        strategy = self.strategies['ict_smc']
        self.stats['strategy_stats']['ict_smc']['analyses'] += 1
        
        try:
            # v3.1 優化：使用 DataService 緩存獲取趨勢數據
            result = await strategy.generate_signal(df, symbol=symbol, data_service=data_service)
            
            if result and result.get('type') != 'HOLD':
                # Create signal object
                signal = Signal(
                    symbol=symbol,
                    action=result['type'],
                    price=result['price'],
                    confidence=result['confidence'],
                    expected_roi=result.get('expected_roi', 3.0),
                    stop_loss=result['stop_loss'],
                    take_profit=result['take_profit'],
                    strategy='ict_smc',
                    timestamp=pd.Timestamp.now().timestamp(),
                    metadata=result.get('metadata', {})
                )
                
                self.stats['signals_generated'] += 1
                self.stats['strategy_stats']['ict_smc']['signals'] += 1
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    async def analyze_batch(
        self,
        symbols_data: Dict[str, tuple],
        data_service=None
    ) -> List[Signal]:
        """
        Analyze multiple symbols concurrently.
        
        Args:
            symbols_data: Dict of {symbol: (df, current_price)}
            data_service: DataService instance (for cached trend data)
            
        Returns:
            List of signals
        """
        # Use data_service from instance if not provided
        if data_service is None:
            data_service = self.data_service
        
        tasks = []
        for symbol, (df, price) in symbols_data.items():
            if df is not None and not df.empty:
                tasks.append(self.analyze_symbol(symbol, df, price, data_service=data_service))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        signals = [r for r in results if isinstance(r, Signal)]
        
        logger.info(f"Generated {len(signals)} signals from {len(symbols_data)} symbols")
        return signals
    
    def rank_signals(
        self,
        signals: List[Signal],
        mode: str = 'confidence',
        limit: int = 3
    ) -> List[Signal]:
        """
        Rank and filter signals.
        
        Args:
            signals: List of signals to rank
            mode: Ranking mode ('confidence' or 'roi')
            limit: Maximum number of signals to return
            
        Returns:
            Top N signals
        """
        if not signals:
            return []
        
        # Sort by chosen metric
        if mode == 'confidence':
            sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)
        elif mode == 'roi':
            sorted_signals = sorted(signals, key=lambda s: s.expected_roi, reverse=True)
        else:
            # Combined score
            sorted_signals = sorted(
                signals,
                key=lambda s: s.confidence * s.expected_roi,
                reverse=True
            )
        
        # Take top N
        top_signals = sorted_signals[:limit]
        
        filtered_count = len(signals) - len(top_signals)
        if filtered_count > 0:
            self.stats['signals_filtered'] += filtered_count
            logger.info(f"Filtered {filtered_count} signals, kept top {len(top_signals)}")
        
        return top_signals
    
    def add_strategy(self, name: str, strategy):
        """Add a new strategy to the engine."""
        self.strategies[name] = strategy
        self.stats['strategy_stats'][name] = {'analyses': 0, 'signals': 0}
        logger.info(f"Added strategy: {name}")
    
    def remove_strategy(self, name: str):
        """Remove a strategy from the engine."""
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"Removed strategy: {name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy engine statistics."""
        return {
            **self.stats,
            'signal_rate': (
                self.stats['signals_generated'] / max(self.stats['total_analyses'], 1)
            ),
            'active_strategies': len(self.strategies)
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'total_analyses': 0,
            'signals_generated': 0,
            'signals_filtered': 0,
            'strategy_stats': {name: {'analyses': 0, 'signals': 0} 
                              for name in self.strategies.keys()}
        }

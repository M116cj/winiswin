"""
Service modules for the trading bot.
"""

try:
    from .data_service import DataService
except ImportError:
    DataService = None

try:
    from .strategy_engine import StrategyEngine, Signal
except ImportError:
    StrategyEngine = None
    Signal = None

try:
    from .execution_service import ExecutionService, Position
except ImportError:
    ExecutionService = None
    Position = None

try:
    from .monitoring_service import MonitoringService
except ImportError:
    MonitoringService = None

__all__ = ['DataService', 'StrategyEngine', 'ExecutionService', 'MonitoringService', 'Signal', 'Position']

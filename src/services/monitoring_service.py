"""
Monitoring Service - System metrics and performance tracking.

Responsibilities:
- Collect performance metrics
- Track trading statistics
- Monitor system health
- Generate alerts
"""

import time
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric with timestamp."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]


class MonitoringService:
    """Service for collecting and reporting system metrics."""
    
    def __init__(self, discord_bot=None):
        """
        Initialize monitoring service.
        
        Args:
            discord_bot: Discord bot for notifications
        """
        self.discord = discord_bot
        
        # Metrics storage
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics = 1000  # Keep last 1000 metrics
        
        # System health
        self.health = {
            'binance_api': 'unknown',
            'discord_api': 'unknown',
            'data_service': 'unknown',
            'strategy_engine': 'unknown',
            'execution_service': 'unknown'
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'max_drawdown_pct': 5.0,
            'api_error_rate': 0.05,
            'scan_time_seconds': 300
        }
        
        # Statistics
        self.stats = {
            'metrics_recorded': 0,
            'alerts_sent': 0,
            'health_checks': 0
        }
        
        logger.info("MonitoringService initialized")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for categorization
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        self.stats['metrics_recorded'] += 1
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_metrics(self, name: str = None, limit: int = 100) -> List[Dict]:
        """
        Get recorded metrics.
        
        Args:
            name: Filter by metric name
            limit: Maximum number of metrics to return
            
        Returns:
            List of metric dicts
        """
        filtered = self.metrics
        
        if name:
            filtered = [m for m in filtered if m.name == name]
        
        # Return most recent
        recent = filtered[-limit:]
        return [asdict(m) for m in recent]
    
    def update_health(self, component: str, status: str):
        """
        Update component health status.
        
        Args:
            component: Component name
            status: Status ('healthy', 'degraded', 'unhealthy')
        """
        if component in self.health:
            self.health[component] = status
            self.stats['health_checks'] += 1
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        unhealthy = [k for k, v in self.health.items() if v == 'unhealthy']
        degraded = [k for k, v in self.health.items() if v == 'degraded']
        
        if unhealthy:
            overall = 'unhealthy'
        elif degraded:
            overall = 'degraded'
        else:
            overall = 'healthy'
        
        return {
            'overall': overall,
            'components': self.health.copy(),
            'unhealthy_components': unhealthy,
            'degraded_components': degraded
        }
    
    def get_trading_stats(self, data_service, strategy_engine, execution_service) -> Dict[str, Any]:
        """
        Aggregate trading statistics from all services.
        
        Args:
            data_service: DataService instance
            strategy_engine: StrategyEngine instance
            execution_service: ExecutionService instance
            
        Returns:
            Aggregated statistics
        """
        return {
            'data_service': data_service.get_stats() if data_service else {},
            'strategy_engine': strategy_engine.get_stats() if strategy_engine else {},
            'execution_service': execution_service.get_stats() if execution_service else {},
            'monitoring': self.get_stats()
        }
    
    async def send_alert(self, message: str, severity: str = "warning"):
        """
        Send alert notification.
        
        Args:
            message: Alert message
            severity: Severity level ('info', 'warning', 'critical')
        """
        self.stats['alerts_sent'] += 1
        
        logger.log(
            logging.CRITICAL if severity == 'critical' else logging.WARNING,
            f"ALERT [{severity.upper()}]: {message}"
        )
        
        # Send to Discord if available
        if self.discord:
            try:
                emoji = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'critical': '🚨'
                }.get(severity, '📢')
                
                await self.discord.send_notification(
                    f"{emoji} **{severity.upper()}**: {message}"
                )
            except Exception as e:
                logger.error(f"Failed to send Discord alert: {e}")
    
    async def check_alerts(
        self,
        current_drawdown: float = 0,
        api_error_rate: float = 0,
        scan_time: float = 0
    ):
        """
        Check if any alert thresholds are breached.
        
        Args:
            current_drawdown: Current drawdown percentage
            api_error_rate: API error rate
            scan_time: Last scan time in seconds
        """
        # Check drawdown
        if current_drawdown > self.alert_thresholds['max_drawdown_pct']:
            await self.send_alert(
                f"Maximum drawdown exceeded: {current_drawdown:.2f}% > "
                f"{self.alert_thresholds['max_drawdown_pct']:.2f}%",
                severity='critical'
            )
        
        # Check API error rate
        if api_error_rate > self.alert_thresholds['api_error_rate']:
            await self.send_alert(
                f"High API error rate: {api_error_rate:.1%}",
                severity='warning'
            )
        
        # Check scan time
        if scan_time > self.alert_thresholds['scan_time_seconds']:
            await self.send_alert(
                f"Slow scan detected: {scan_time:.1f}s > "
                f"{self.alert_thresholds['scan_time_seconds']:.1f}s",
                severity='info'
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        if not self.metrics:
            return {}
        
        # Group by metric name
        by_name = {}
        for metric in self.metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for name, values in by_name.items():
            if values:
                summary[name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1]
                }
        
        return summary
    
    def export_metrics(self, filepath: str = "metrics.json"):
        """Export metrics to JSON file."""
        try:
            data = {
                'exported_at': datetime.now().isoformat(),
                'metrics': [asdict(m) for m in self.metrics],
                'health': self.health,
                'stats': self.stats
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(self.metrics)} metrics to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring service statistics."""
        return {
            **self.stats,
            'metrics_stored': len(self.metrics),
            'health_status': self.get_system_health()
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'metrics_recorded': 0,
            'alerts_sent': 0,
            'health_checks': 0
        }
        self.metrics.clear()

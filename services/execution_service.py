"""
Execution Service - Position management and trade execution.

Responsibilities:
- Manage position lifecycle
- Execute trades with risk checks
- Monitor open positions
- Handle stop-loss and take-profit
"""

import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Active trading position."""
    symbol: str
    action: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    opened_at: datetime
    strategy: str
    confidence: float
    allocated_capital: float
    leverage: float = 1.0


class ExecutionService:
    """Service for executing and managing trades."""
    
    def __init__(self, binance_client, risk_manager, discord_bot=None, enable_trading: bool = False):
        """
        Initialize execution service.
        
        Args:
            binance_client: Binance API client
            risk_manager: Risk management instance
            discord_bot: Discord bot for notifications
            enable_trading: Enable live trading
        """
        self.binance = binance_client
        self.risk_manager = risk_manager
        self.discord = discord_bot
        self.enable_trading = enable_trading
        
        self.positions: Dict[str, Position] = {}
        self.max_positions = 3
        
        # Callback for position closed event (平倉後立即重新掃描)
        self.on_position_closed_callback = None
        
        # Statistics
        self.stats = {
            'total_signals_received': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'positions_closed': 0,
            'stop_losses_hit': 0,
            'take_profits_hit': 0
        }
        
        logger.info(
            f"ExecutionService initialized: "
            f"trading={'ENABLED' if enable_trading else 'DISABLED'}, "
            f"max_positions={self.max_positions}"
        )
    
    async def execute_signal(self, signal) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal: Signal object from strategy engine
            
        Returns:
            True if executed, False if rejected
        """
        self.stats['total_signals_received'] += 1
        
        # Check if we can open new position
        if len(self.positions) >= self.max_positions:
            logger.info(f"Max positions reached ({self.max_positions}), rejecting {signal.symbol}")
            self.stats['trades_rejected'] += 1
            return False
        
        # Check if already have position in this symbol
        if signal.symbol in self.positions:
            logger.info(f"Already have position in {signal.symbol}, rejecting")
            self.stats['trades_rejected'] += 1
            return False
        
        # Get allocated capital for this position
        allocated_capital = self.risk_manager.get_allocated_capital()
        
        # 計算動態槓桿
        atr = signal.metadata.get('atr', 0)
        current_price = signal.metadata.get('current_price', signal.price)
        leverage = self.risk_manager.calculate_dynamic_leverage(
            confidence=signal.confidence,
            atr=atr,
            current_price=current_price
        )
        
        # Calculate position size with risk management
        position_params = self.risk_manager.calculate_position_size(
            signal.symbol,
            signal.price,
            signal.stop_loss,
            allocated_capital
        )
        
        if not position_params:
            logger.warning(f"Risk check failed for {signal.symbol}")
            self.stats['trades_rejected'] += 1
            return False
        
        # 應用槓桿到倉位數量
        if leverage > 1.0:
            position_params['quantity'] = position_params['quantity'] * leverage
            position_params['leverage'] = leverage
            logger.info(f"Applied leverage {leverage:.2f}x to position size")
        else:
            position_params['leverage'] = 1.0
            logger.info(f"No leverage applied (leverage = 1.0x)")
        
        # Execute trade
        if self.enable_trading:
            try:
                # Place market order
                order = await self._place_order(
                    signal.symbol,
                    signal.action,
                    position_params['quantity']
                )
                
                if not order:
                    self.stats['trades_rejected'] += 1
                    return False
                    
            except Exception as e:
                logger.error(f"Error placing order for {signal.symbol}: {e}")
                self.stats['trades_rejected'] += 1
                return False
        
        # Create position record
        position = Position(
            symbol=signal.symbol,
            action=signal.action,
            entry_price=signal.price,
            quantity=position_params['quantity'],
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            opened_at=datetime.now(),
            strategy=signal.strategy,
            confidence=signal.confidence,
            allocated_capital=allocated_capital,
            leverage=position_params.get('leverage', 1.0)
        )
        
        # Add to risk manager
        self.risk_manager.add_position(
            signal.symbol,
            signal.action,
            signal.price,
            position_params['quantity'],
            signal.stop_loss,
            signal.take_profit
        )
        
        # Store position
        self.positions[signal.symbol] = position
        self.stats['trades_executed'] += 1
        
        logger.info(
            f"{'SIMULATED' if not self.enable_trading else 'EXECUTED'} "
            f"{signal.action} {signal.symbol} @ {signal.price:.4f} "
            f"qty={position_params['quantity']:.4f} "
            f"(confidence: {signal.confidence:.1f}%)"
        )
        
        # Send Discord notification for new position
        if self.discord:
            await self._notify_position_opened(position, position_params)
        
        return True
    
    async def _notify_position_opened(self, position: Position, position_params: Dict):
        """Send Discord notification when position is opened."""
        try:
            trade_info = {
                'type': 'OPEN',
                'symbol': position.symbol,
                'action': position.action,
                'price': position.entry_price,
                'quantity': position.quantity,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'confidence': position.confidence,
                'strategy': position.strategy,
                'allocated_capital': position.allocated_capital,
                'risk_amount': position_params.get('risk_amount', 0),
                'leverage': position.leverage,
                'mode': 'LIVE' if self.enable_trading else 'SIMULATION'
            }
            await self.discord.send_trade_notification(trade_info)
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    async def _place_order(self, symbol: str, action: str, quantity: float) -> Optional[Dict]:
        """
        Place market order on Binance.
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            quantity: Order quantity
            
        Returns:
            Order response or None
        """
        try:
            side = 'BUY' if action == 'BUY' else 'SELL'
            
            order = self.binance.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return None
    
    async def monitor_positions(self) -> List[str]:
        """
        Monitor open positions and close if stop-loss or take-profit hit.
        
        Returns:
            List of closed position symbols
        """
        if not self.positions:
            return []
        
        closed_symbols = []
        
        for symbol, position in list(self.positions.items()):
            try:
                # Get current price
                ticker = await self.binance.get_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = float(ticker.get('lastPrice', 0))
                if current_price == 0:
                    continue
                
                should_close = False
                reason = ""
                
                # Check stop-loss
                if position.action == 'BUY' and current_price <= position.stop_loss:
                    should_close = True
                    reason = "stop-loss"
                    self.stats['stop_losses_hit'] += 1
                elif position.action == 'SELL' and current_price >= position.stop_loss:
                    should_close = True
                    reason = "stop-loss"
                    self.stats['stop_losses_hit'] += 1
                
                # Check take-profit
                if position.action == 'BUY' and current_price >= position.take_profit:
                    should_close = True
                    reason = "take-profit"
                    self.stats['take_profits_hit'] += 1
                elif position.action == 'SELL' and current_price <= position.take_profit:
                    should_close = True
                    reason = "take-profit"
                    self.stats['take_profits_hit'] += 1
                
                if should_close:
                    await self.close_position(symbol, current_price, reason)
                    closed_symbols.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
        
        return closed_symbols
    
    async def close_position(self, symbol: str, price: float, reason: str = "manual") -> bool:
        """
        Close a position.
        
        Args:
            symbol: Trading symbol
            price: Closing price
            reason: Reason for closing
            
        Returns:
            True if closed successfully
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # Execute closing trade if live trading
        if self.enable_trading:
            try:
                # Close position with market order
                opposite_side = 'SELL' if position.action == 'BUY' else 'BUY'
                await self._place_order(symbol, opposite_side, position.quantity)
            except Exception as e:
                logger.error(f"Error closing position {symbol}: {e}")
                return False
        
        # Remove from risk manager
        self.risk_manager.close_position(symbol)
        
        # Calculate PnL
        if position.action == 'BUY':
            pnl = (price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - price) * position.quantity
        
        pnl_pct = (pnl / position.allocated_capital) * 100
        
        # Remove position
        del self.positions[symbol]
        self.stats['positions_closed'] += 1
        
        logger.info(
            f"Closed {symbol} @ {price:.4f} ({reason}): "
            f"PnL = {pnl:.2f} USDT ({pnl_pct:+.2f}%)"
        )
        
        # Send Discord notification for closed position
        if self.discord:
            await self._notify_position_closed(position, price, pnl, pnl_pct, reason)
        
        # 觸發平倉後立即重新掃描回調
        if self.on_position_closed_callback:
            try:
                logger.info(f"🔄 觸發 {symbol} 立即重新掃描回調")
                asyncio.create_task(self.on_position_closed_callback(symbol))
            except Exception as e:
                logger.error(f"執行平倉回調時發生錯誤: {e}")
        
        return True
    
    async def _notify_position_closed(self, position: Position, exit_price: float, 
                                     pnl: float, pnl_pct: float, reason: str):
        """Send Discord notification when position is closed."""
        try:
            trade_info = {
                'type': 'CLOSE',
                'symbol': position.symbol,
                'action': position.action,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'quantity': position.quantity,
                'pnl': pnl,
                'pnl_percent': pnl_pct,
                'reason': reason.upper(),
                'strategy': position.strategy,
                'duration': (datetime.now() - position.opened_at).total_seconds() / 3600,
                'mode': 'LIVE' if self.enable_trading else 'SIMULATION'
            }
            await self.discord.send_trade_notification(trade_info)
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get list of active positions."""
        return [
            {
                'symbol': pos.symbol,
                'action': pos.action,
                'entry_price': pos.entry_price,
                'quantity': pos.quantity,
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit,
                'opened_at': pos.opened_at.isoformat(),
                'strategy': pos.strategy,
                'confidence': pos.confidence
            }
            for pos in self.positions.values()
        ]
    
    def emergency_stop(self):
        """Emergency stop all trading."""
        logger.critical("EMERGENCY STOP ACTIVATED")
        self.enable_trading = False
        # Future: Close all positions immediately
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution service statistics."""
        return {
            **self.stats,
            'active_positions': len(self.positions),
            'execution_rate': (
                self.stats['trades_executed'] / 
                max(self.stats['total_signals_received'], 1)
            ),
            'rejection_rate': (
                self.stats['trades_rejected'] / 
                max(self.stats['total_signals_received'], 1)
            )
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'total_signals_received': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'positions_closed': 0,
            'stop_losses_hit': 0,
            'take_profits_hit': 0
        }

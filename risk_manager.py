import numpy as np
from config import Config
from utils.helpers import setup_logger, calculate_position_size

logger = setup_logger(__name__)

class RiskManager:
    def __init__(self, account_balance=10000):
        self.account_balance = account_balance
        self.risk_per_trade = Config.RISK_PER_TRADE_PERCENT
        self.max_position_size = Config.MAX_POSITION_SIZE_PERCENT
        self.max_concurrent_positions = Config.MAX_CONCURRENT_POSITIONS
        self.capital_per_position = Config.CAPITAL_PER_POSITION_PERCENT
        self.open_positions = {}
        self.pending_signals = {}  # 儲存所有候選信號
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.max_drawdown = 0
        self.peak_balance = account_balance
        
        logger.info(f"RiskManager initialized - Max concurrent positions: {self.max_concurrent_positions}, "
                   f"Capital per position: {self.capital_per_position:.2f}%")
    
    def update_balance(self, new_balance):
        self.account_balance = new_balance
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        
        current_drawdown = ((self.peak_balance - new_balance) / self.peak_balance) * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
    
    def get_allocated_capital(self):
        """Get capital allocated per position (1/3 of total for 3-position system)."""
        return self.account_balance * (self.capital_per_position / 100)
    
    def calculate_position_size(self, symbol, entry_price, stop_loss_price, allocated_capital=None):
        """
        Calculate position size with risk management.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            allocated_capital: Capital allocated for this position (optional)
        
        Returns:
            Dict with position parameters or None if invalid
        """
        if entry_price is None or stop_loss_price is None:
            logger.error("Cannot calculate position size: entry_price or stop_loss_price is None")
            return None
        
        if np.isnan(entry_price) or np.isnan(stop_loss_price):
            logger.error("Cannot calculate position size: NaN values detected")
            return None
        
        # Use provided capital or calculate from account
        if allocated_capital is None:
            allocated_capital = self.get_allocated_capital()
        
        position_size = calculate_position_size(
            allocated_capital,
            self.risk_per_trade,
            entry_price,
            stop_loss_price
        )
        
        if np.isnan(position_size) or position_size <= 0:
            logger.error(f"Invalid position size calculated: {position_size}")
            return None
        
        # Maximum position limit (based on allocated capital)
        max_position_value = allocated_capital * (self.max_position_size / 100)
        max_quantity = max_position_value / entry_price
        
        final_position_size = min(position_size, max_quantity)
        
        logger.info(f"Calculated position size: {final_position_size:.6f} "
                   f"(Entry: {entry_price}, SL: {stop_loss_price}, "
                   f"Capital allocated: ${allocated_capital:.2f})")
        
        return {
            'quantity': final_position_size,
            'allocated_capital': allocated_capital,
            'risk_amount': allocated_capital * (self.risk_per_trade / 100)
        }
    
    def calculate_stop_loss(self, entry_price, atr, direction='LONG'):
        if atr is None or np.isnan(atr) or atr <= 0:
            logger.error(f"Invalid ATR value: {atr}")
            return None
        
        if entry_price is None or np.isnan(entry_price):
            logger.error(f"Invalid entry price: {entry_price}")
            return None
        
        multiplier = Config.STOP_LOSS_ATR_MULTIPLIER
        
        if direction == 'LONG':
            stop_loss = entry_price - (atr * multiplier)
        else:
            stop_loss = entry_price + (atr * multiplier)
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price, atr, direction='LONG'):
        if atr is None or np.isnan(atr) or atr <= 0:
            logger.error(f"Invalid ATR value: {atr}")
            return None
        
        if entry_price is None or np.isnan(entry_price):
            logger.error(f"Invalid entry price: {entry_price}")
            return None
        
        multiplier = Config.TAKE_PROFIT_ATR_MULTIPLIER
        
        if direction == 'LONG':
            take_profit = entry_price + (atr * multiplier)
        else:
            take_profit = entry_price - (atr * multiplier)
        
        return take_profit
    
    def can_open_position(self, symbol):
        if symbol in self.open_positions:
            logger.warning(f"Position already open for {symbol}")
            return False
        
        if len(self.open_positions) >= self.max_concurrent_positions:
            logger.warning(f"Maximum concurrent positions reached ({self.max_concurrent_positions})")
            return False
        
        return True
    
    def add_pending_signal(self, symbol, signal_info):
        """添加候選信號到待處理隊列"""
        self.pending_signals[symbol] = signal_info
        logger.info(f"Added pending signal for {symbol}: {signal_info.get('type')} "
                   f"(confidence: {signal_info.get('confidence', 0):.1f}%, "
                   f"roi: {signal_info.get('expected_roi', 0):.2f}%)")
    
    def get_top_signals(self, sort_by='confidence'):
        """
        獲取最優的信號
        
        Args:
            sort_by: 'confidence' (信心度) 或 'roi' (投報率)
        
        Returns:
            排序後的信號列表
        """
        if not self.pending_signals:
            return []
        
        available_slots = self.max_concurrent_positions - len(self.open_positions)
        if available_slots <= 0:
            logger.info("No available position slots")
            return []
        
        # 排序信號
        sorted_signals = []
        for symbol, signal in self.pending_signals.items():
            if symbol not in self.open_positions:  # 排除已開倉的
                sorted_signals.append((symbol, signal))
        
        if sort_by == 'roi':
            # 按預期投報率排序（高到低）
            sorted_signals.sort(key=lambda x: x[1].get('expected_roi', 0), reverse=True)
            logger.info(f"Sorted {len(sorted_signals)} signals by ROI")
        else:
            # 按信心度排序（高到低）
            sorted_signals.sort(key=lambda x: x[1].get('confidence', 0), reverse=True)
            logger.info(f"Sorted {len(sorted_signals)} signals by confidence")
        
        # 返回前 N 個（可用倉位數）
        top_signals = sorted_signals[:available_slots]
        
        if top_signals:
            logger.info(f"Selected top {len(top_signals)} signals:")
            for symbol, signal in top_signals:
                logger.info(f"  - {symbol}: {signal.get('type')} "
                          f"(confidence: {signal.get('confidence', 0):.1f}%, "
                          f"roi: {signal.get('expected_roi', 0):.2f}%)")
        
        return top_signals
    
    def clear_pending_signals(self):
        """清空待處理信號"""
        count = len(self.pending_signals)
        self.pending_signals = {}
        logger.info(f"Cleared {count} pending signals")
    
    def add_position(self, symbol, side, entry_price, quantity, stop_loss, take_profit):
        """Add a position (v3.0 compatible method name)."""
        return self.open_position(symbol, side, entry_price, quantity, stop_loss, take_profit)
    
    def open_position(self, symbol, side, entry_price, quantity, stop_loss, take_profit):
        if not self.can_open_position(symbol):
            return False
        
        self.open_positions[symbol] = {
            'side': side,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'unrealized_pnl': 0
        }
        
        logger.info(f"Opened {side} position for {symbol} at {entry_price}")
        return True
    
    def close_position(self, symbol, exit_price=None):
        """Close a position (supports both old and new signatures)."""
        if symbol not in self.open_positions:
            logger.warning(f"No open position for {symbol}")
            return None
        
        position = self.open_positions[symbol]
        
        # If no exit price provided, use current entry price (for API compatibility)
        if exit_price is None:
            exit_price = position['entry_price']
        
        if position['side'] in ['LONG', 'BUY']:
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        pnl_percent = (pnl / self.account_balance) * 100
        
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.total_profit += pnl
        self.update_balance(self.account_balance + pnl)
        
        logger.info(f"Closed position for {symbol} at {exit_price}. PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)")
        
        del self.open_positions[symbol]
        
        return {
            'symbol': symbol,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'exit_price': exit_price
        }
    
    def check_stop_loss_take_profit(self, symbol, current_price):
        if symbol not in self.open_positions:
            return None
        
        position = self.open_positions[symbol]
        
        if position['side'] == 'LONG':
            if current_price <= position['stop_loss']:
                return {'action': 'CLOSE', 'reason': 'STOP_LOSS', 'price': position['stop_loss']}
            elif current_price >= position['take_profit']:
                return {'action': 'CLOSE', 'reason': 'TAKE_PROFIT', 'price': position['take_profit']}
        else:
            if current_price >= position['stop_loss']:
                return {'action': 'CLOSE', 'reason': 'STOP_LOSS', 'price': position['stop_loss']}
            elif current_price <= position['take_profit']:
                return {'action': 'CLOSE', 'reason': 'TAKE_PROFIT', 'price': position['take_profit']}
        
        return None
    
    def get_performance_stats(self):
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'account_balance': self.account_balance,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'max_drawdown': self.max_drawdown,
            'roi': (self.total_profit / 10000) * 100
        }

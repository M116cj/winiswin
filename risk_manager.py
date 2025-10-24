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
    
    def calculate_breakeven_price(self, entry_price, leverage, action='BUY', use_taker_fee=True):
        """
        計算考慮槓桿和手續費的損益平衡價格
        
        Args:
            entry_price: 進場價格
            leverage: 槓桿倍數
            action: 'BUY' (做多) 或 'SELL' (做空)
            use_taker_fee: 是否使用吃單手續費（True）或掛單手續費（False）
        
        Returns:
            損益平衡價格
        
        說明：
            損益平衡價格 = 進場價格 ± 總手續費成本
            總手續費成本 = (開倉手續費 + 平倉手續費) * 進場價格
            
            例如：
            - 做多 BTC @ 50000，槓桿 10x，吃單手續費 0.04%
            - 開倉手續費 = 50000 * 0.0004 = 20 USDT
            - 平倉手續費 = 50000 * 0.0004 = 20 USDT
            - 總手續費 = 40 USDT
            - 損益平衡價格 = 50000 + 40 = 50040 USDT
        """
        try:
            # 選擇手續費率
            fee_rate = Config.TAKER_FEE_RATE if use_taker_fee else Config.MAKER_FEE_RATE
            
            # 計算總手續費率（開倉 + 平倉）
            total_fee_rate = fee_rate * 2
            
            # 計算手續費成本（以價格百分比表示）
            fee_cost_percent = total_fee_rate
            
            # 計算損益平衡價格
            if action == 'BUY':
                # 做多：需要價格上漲才能彌補手續費
                breakeven = entry_price * (1 + fee_cost_percent)
            else:  # SELL
                # 做空：需要價格下跌才能彌補手續費
                breakeven = entry_price * (1 - fee_cost_percent)
            
            logger.debug(
                f"損益平衡計算: {action} @ {entry_price:.8f}, "
                f"槓桿={leverage:.1f}x, 手續費={fee_rate*100:.3f}%×2, "
                f"損益平衡={breakeven:.8f}"
            )
            
            return breakeven
            
        except Exception as e:
            logger.error(f"Error calculating breakeven price: {e}")
            # 發生錯誤時，返回進場價格（保守做法）
            return entry_price
    
    def calculate_dynamic_leverage(self, confidence, atr, current_price):
        """
        智能槓桿計算：根據信心度和市場波動性動態調整槓桿倍數
        
        Args:
            confidence: 信號信心度 (70-100)
            atr: 平均真實波幅（ATR）
            current_price: 當前價格
        
        Returns:
            槓桿倍數 (1.0-2.0x)
        """
        # 如果未啟用動態槓桿，返回預設值
        if not Config.ENABLE_DYNAMIC_LEVERAGE:
            return Config.DEFAULT_LEVERAGE
        
        # 數據驗證
        if confidence is None or np.isnan(confidence) or confidence < 0:
            logger.warning(f"Invalid confidence {confidence}, using default leverage")
            return Config.DEFAULT_LEVERAGE
        
        if atr is None or np.isnan(atr) or atr <= 0:
            logger.warning(f"Invalid ATR {atr}, using default leverage")
            return Config.DEFAULT_LEVERAGE
        
        if current_price is None or np.isnan(current_price) or current_price <= 0:
            logger.warning(f"Invalid price {current_price}, using default leverage")
            return Config.DEFAULT_LEVERAGE
        
        try:
            # === 第一步：根據信心度計算基礎槓桿 ===
            # 100-90%: 20x (線性從 90% = 10x 到 100% = 20x)
            # 90-80%: 10x (線性從 80% = 3x 到 90% = 10x)
            # 80-70%: 3x (固定 3x)
            
            if confidence >= Config.HIGH_CONFIDENCE_THRESHOLD:
                # 90-100% 信心度：10x-20x
                confidence_range = 10.0  # 100 - 90
                base_leverage = 10.0 + (confidence - Config.HIGH_CONFIDENCE_THRESHOLD) * (10.0 / confidence_range)
            elif confidence >= Config.MEDIUM_CONFIDENCE_THRESHOLD:
                # 80-90% 信心度：3x-10x
                confidence_range = Config.HIGH_CONFIDENCE_THRESHOLD - Config.MEDIUM_CONFIDENCE_THRESHOLD
                base_leverage = 3.0 + (confidence - Config.MEDIUM_CONFIDENCE_THRESHOLD) * (7.0 / confidence_range)
            else:
                # 70-80% 信心度：3x (固定)
                base_leverage = 3.0
            
            # === 第二步：根據波動性調整 ===
            atr_percent = (atr / current_price) * 100  # ATR 佔價格百分比
            
            volatility_adjustment = 0.0
            if atr_percent < Config.LOW_VOLATILITY_ATR_THRESHOLD * 100:
                # 低波動：可以增加槓桿（最多+20%）
                volatility_adjustment = base_leverage * 0.2
                volatility_level = "低"
            elif atr_percent > Config.HIGH_VOLATILITY_ATR_THRESHOLD * 100:
                # 高波動：降低槓桿以控制風險（最多-30%）
                volatility_adjustment = -base_leverage * 0.3
                volatility_level = "高"
            else:
                # 正常波動：不調整
                volatility_level = "正常"
            
            # === 第三步：計算最終槓桿 ===
            final_leverage = base_leverage + volatility_adjustment
            
            # 限制在允許範圍內
            final_leverage = max(Config.MIN_LEVERAGE, min(final_leverage, Config.MAX_LEVERAGE))
            
            logger.info(f"🎯 槓桿計算: 信心度={confidence:.1f}% → 基礎={base_leverage:.2f}x, "
                       f"波動性={volatility_level}({atr_percent:.2f}%) → 調整={volatility_adjustment:+.1f}x, "
                       f"最終槓桿={final_leverage:.2f}x")
            
            return final_leverage
            
        except Exception as e:
            logger.error(f"Error calculating dynamic leverage: {e}")
            return Config.DEFAULT_LEVERAGE
    
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

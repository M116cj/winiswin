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
    trade_id: Optional[str] = None  # 用於關聯開倉和平倉的 ML 數據


class ExecutionService:
    """Service for executing and managing trades."""
    
    def __init__(self, binance_client, risk_manager, discord_bot=None, enable_trading: bool = False, trade_logger=None):
        """
        Initialize execution service.
        
        Args:
            binance_client: Binance API client
            risk_manager: Risk management instance
            discord_bot: Discord bot for notifications
            enable_trading: Enable live trading
            trade_logger: Trade logger for ML training data
        """
        self.binance = binance_client
        self.risk_manager = risk_manager
        self.discord = discord_bot
        self.enable_trading = enable_trading
        self.trade_logger = trade_logger
        
        self.positions: Dict[str, Position] = {}
        self.max_positions = 3
        
        # Callback for position closed event (平倉後立即重新掃描)
        self.on_position_closed_callback = None
        
        # Strategy engine reference (will be set externally for signal validation)
        self.strategy_engine = None
        self.data_service = None
        self.timeframe = '15m'  # Will be set from Config.TIMEFRAME
        
        # Statistics
        self.stats = {
            'total_signals_received': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'positions_closed': 0,
            'stop_losses_hit': 0,
            'take_profits_hit': 0,
            'signal_invalidation_exits': 0,
            'dynamic_adjustments': 0
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
        
        # 計算動態槓桿（基於勝率或信心度）
        atr = signal.metadata.get('atr', 0)
        current_price = signal.metadata.get('current_price', signal.price)
        leverage = self.risk_manager.calculate_dynamic_leverage(
            confidence=signal.confidence,
            atr=atr,
            current_price=current_price
        )
        
        # 計算倉位大小（使用新的保證金比例系統：3%-13%）
        position_params = self.risk_manager.calculate_position_size(
            symbol=signal.symbol,
            entry_price=signal.price,
            stop_loss_price=signal.stop_loss,
            confidence=signal.confidence,  # 用於計算保證金比例（3%-13%）
            leverage=leverage               # 用於計算倉位價值
        )
        
        if not position_params:
            logger.warning(f"Risk check failed for {signal.symbol}")
            self.stats['trades_rejected'] += 1
            return False
        
        # Execute trade
        if self.enable_trading:
            try:
                # Place order (MARKET or LIMIT based on config)
                order = await self._place_order(
                    signal.symbol,
                    signal.action,
                    position_params['quantity'],
                    signal.price  # Pass entry price for limit order calculation
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
            allocated_capital=position_params['margin'],  # 保證金
            leverage=position_params['leverage']
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
        
        # 🔒 設置交易所級別的止損/止盈訂單（關鍵安全功能）
        if self.enable_trading:
            await self._set_stop_loss_take_profit(position)
        
        # 📊 記錄開倉數據供 XGBoost 學習
        if self.trade_logger:
            trade_data = {
                'type': 'OPEN',
                'symbol': signal.symbol,
                'side': signal.action,
                'entry_price': signal.price,
                'quantity': position_params['quantity'],
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'leverage': position_params['leverage'],
                'confidence': signal.confidence,
                'expected_roi': signal.expected_roi,
                'strategy': signal.strategy,
                'reason': signal.reason,
                # 技術指標 (供 XGBoost 學習)
                'metadata': signal.metadata,  # 包含 MACD, EMA, ATR, structure 等
                'margin': position_params['margin'],
                'margin_percent': position_params['margin_percent'],
                'position_value': position_params['position_value'],
                'mode': 'LIVE' if self.enable_trading else 'SIMULATION'
            }
            # 保持向後兼容的簡單記錄
            self.trade_logger.log_trade(trade_data)
            
            # 新增：記錄詳細的 ML 訓練數據（開倉）
            try:
                trade_id = self.trade_logger.log_position_entry(
                    trade_data=trade_data,
                    binance_client=self.binance,
                    timeframe=self.timeframe
                )
                # 修復問題 2.4：處理 trade_id 缺失情況
                if trade_id:
                    position.trade_id = trade_id
                    logger.debug(f"Assigned trade_id {trade_id} to position {signal.symbol}")
                else:
                    # 降級處理：生成臨時 trade_id（避免平倉時無法記錄）
                    position.trade_id = f"{signal.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_fallback"
                    logger.warning(f"log_position_entry failed, using fallback trade_id: {position.trade_id}")
            except Exception as e:
                logger.error(f"Failed to log position entry for ML: {e}")
                logger.exception(e)
                # 即使失敗，也生成一個降級的 trade_id
                position.trade_id = f"{signal.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_error"
        
        # Send Discord notification for new position
        if self.discord:
            await self._notify_position_opened(position, position_params)
        
        return True
    
    async def load_positions_from_binance(self):
        """
        從 Binance API 加載當前真實持倉到內存
        
        這個方法在啟動時調用，確保重啟後能識別現有倉位並為它們設置保護
        """
        try:
            logger.info("🔍 Loading current positions from Binance API...")
            
            # 從 Binance API 獲取持倉
            loop = asyncio.get_event_loop()
            binance_positions = await loop.run_in_executor(None, self.binance.get_current_positions)
            
            if not binance_positions:
                logger.info("No positions to load from Binance")
                return 0
            
            loaded_count = 0
            
            for binance_pos in binance_positions:
                try:
                    symbol = binance_pos['symbol']
                    position_side = binance_pos['positionSide']  # 'LONG' or 'SHORT'
                    position_amt = float(binance_pos['positionAmt'])
                    entry_price = float(binance_pos['entryPrice'])
                    leverage = int(binance_pos.get('leverage', 1))
                    
                    # 根據 positionSide 確定 action
                    # LONG = BUY 開倉, SHORT = SELL 開倉
                    if position_side == 'LONG':
                        action = 'BUY'
                        quantity = abs(position_amt)
                    else:  # SHORT
                        action = 'SELL'
                        quantity = abs(position_amt)
                    
                    # 計算止損/止盈（使用當前價格和簡單策略）
                    current_price = entry_price  # 使用進場價作為參考
                    
                    # 簡單策略：3% 止損，5% 止盈
                    if action == 'BUY':
                        stop_loss = entry_price * 0.97
                        take_profit = entry_price * 1.05
                    else:
                        stop_loss = entry_price * 1.03
                        take_profit = entry_price * 0.95
                    
                    # 創建 Position 對象
                    position = Position(
                        symbol=symbol,
                        action=action,
                        entry_price=entry_price,
                        quantity=quantity,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        opened_at=datetime.now(),  # 實際開倉時間未知，使用當前時間
                        strategy='LOADED_FROM_BINANCE',
                        confidence=80.0,  # 假設信心度
                        allocated_capital=quantity * entry_price / leverage,  # 估算
                        leverage=leverage
                    )
                    
                    # 添加到內存
                    self.positions[symbol] = position
                    
                    # 添加到風險管理器
                    self.risk_manager.add_position(
                        symbol, action, entry_price, quantity, stop_loss, take_profit
                    )
                    
                    logger.info(
                        f"✅ Loaded {symbol} {action} position: "
                        f"qty={quantity:.4f}, entry={entry_price:.8f}, "
                        f"SL={stop_loss:.8f}, TP={take_profit:.8f}"
                    )
                    
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Error loading position {binance_pos.get('symbol', 'UNKNOWN')}: {e}")
                    continue
            
            logger.info(f"✅ Successfully loaded {loaded_count} positions from Binance")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading positions from Binance: {e}")
            logger.exception(e)
            return 0
    
    async def set_protection_for_existing_positions(self):
        """
        為現有倉位補設止損/止盈訂單（啟動時或手動調用）
        
        用於修復沒有交易所級別保護的舊倉位
        """
        if not self.positions:
            logger.info("No existing positions to protect")
            return
        
        logger.info(f"🔍 Checking {len(self.positions)} existing positions for exchange-level protection...")
        
        for symbol, position in self.positions.items():
            try:
                logger.info(
                    f"📊 Position: {symbol} {position.action} @ {position.entry_price:.8f}, "
                    f"qty={position.quantity}, SL={position.stop_loss:.8f}, TP={position.take_profit:.8f}"
                )
                
                # 設置止損/止盈
                if self.enable_trading:
                    await self._set_stop_loss_take_profit(position)
                else:
                    logger.info(f"⚠️  Trading disabled, skipping protection for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error setting protection for {symbol}: {e}")
                logger.exception(e)
        
        logger.info("✅ Finished setting protection for existing positions")
    
    async def _set_stop_loss_take_profit(self, position: Position):
        """
        在交易所設置止損/止盈訂單（關鍵安全功能）
        
        Args:
            position: 倉位對象
        """
        try:
            symbol = position.symbol
            quantity = position.quantity
            
            # 確定平倉方向和持倉側
            # LONG 倉位 (BUY 開倉) → SELL 平倉，positionSide=LONG
            # SHORT 倉位 (SELL 開倉) → BUY 平倉，positionSide=SHORT
            if position.action == 'BUY':
                close_side = 'SELL'
                position_side = 'LONG'
            else:
                close_side = 'BUY'
                position_side = 'SHORT'
            
            logger.info(
                f"🔒 Setting exchange-level protection for {symbol} {position_side}: "
                f"SL @ {position.stop_loss:.8f}, TP @ {position.take_profit:.8f}"
            )
            
            # 設置止損訂單（異步執行同步方法）
            loop = asyncio.get_event_loop()
            sl_order = await loop.run_in_executor(
                None,
                self.binance.set_stop_loss_order,
                symbol,
                close_side,
                quantity,
                position.stop_loss,
                position_side
            )
            
            if sl_order:
                logger.info(f"✅ Stop-loss order set successfully for {symbol}: {sl_order.get('orderId', 'N/A')}")
            else:
                logger.error(f"❌ Failed to set stop-loss for {symbol}")
            
            # 設置止盈訂單（異步執行同步方法）
            tp_order = await loop.run_in_executor(
                None,
                self.binance.set_take_profit_order,
                symbol,
                close_side,
                quantity,
                position.take_profit,
                position_side
            )
            
            if tp_order:
                logger.info(f"✅ Take-profit order set successfully for {symbol}: {tp_order.get('orderId', 'N/A')}")
            else:
                logger.error(f"❌ Failed to set take-profit for {symbol}")
            
            # 如果兩個訂單都失敗，發出嚴重警告
            if not sl_order and not tp_order:
                logger.critical(
                    f"🚨 CRITICAL: Failed to set ANY protection orders for {symbol}! "
                    f"Position is UNPROTECTED!"
                )
                # 可選：發送 Discord 緊急通知
                if self.discord:
                    try:
                        await self.discord.send_alert(
                            f"🚨 **CRITICAL ALERT**\n\n"
                            f"Failed to set stop-loss/take-profit for {symbol}!\n"
                            f"Position is UNPROTECTED - manual intervention required!"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send Discord alert: {e}")
            
        except Exception as e:
            logger.error(f"Error setting stop-loss/take-profit for {position.symbol}: {e}")
            logger.exception(e)
    
    async def _notify_position_opened(self, position: Position, position_params: Dict):
        """Send Discord notification when position is opened."""
        if not self.discord:
            logger.warning("Discord bot not available, skipping notification")
            return
            
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
            logger.exception(e)
    
    async def _place_order(self, symbol: str, action: str, quantity: float, price: float = None) -> Optional[Dict]:
        """
        Place order on Binance (supports both MARKET and LIMIT orders).
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Entry price for limit order calculation (optional)
            
        Returns:
            Order response or None
        """
        try:
            from config import Config
            
            side = 'BUY' if action == 'BUY' else 'SELL'
            order_type = Config.ORDER_TYPE
            
            # 計算限價單價格（如果使用限價單）
            limit_price = None
            if order_type == 'LIMIT':
                if price is None:
                    # 獲取當前價格
                    price = self.binance.get_ticker_price(symbol)
                
                offset_pct = Config.LIMIT_ORDER_OFFSET_PERCENT / 100
                
                if action == 'BUY':
                    # 做多：設置稍低於市價的限價（等待更好的買入價）
                    limit_price = price * (1 - offset_pct)
                else:
                    # 做空：設置稍高於市價的限價（等待更好的賣出價）
                    limit_price = price * (1 + offset_pct)
                
                # 格式化限價（使用 PRICE_FILTER 精度）
                limit_price = round(limit_price, 8)  # Binance 最多 8 位小數
                
                logger.info(
                    f"{'[LIVE]' if self.enable_trading else '[SIM]'} Placing {side} LIMIT order: "
                    f"{symbol} qty={quantity:.6f}, price={limit_price:.8f} "
                    f"(market: {price:.8f}, offset: {Config.LIMIT_ORDER_OFFSET_PERCENT}%)"
                )
            else:
                logger.info(
                    f"{'[LIVE]' if self.enable_trading else '[SIM]'} Placing {side} MARKET order: "
                    f"{symbol} qty={quantity:.6f}"
                )
            
            # 下單
            if order_type == 'LIMIT':
                order = self.binance.create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    quantity=quantity,
                    price=limit_price
                )
            else:
                order = self.binance.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
            
            if order:
                logger.info(f"✅ Order placed successfully: {order.get('orderId', 'N/A')}")
            else:
                logger.warning(f"⚠️  Order returned None (trading may be disabled)")
            
            return order
            
        except Exception as e:
            logger.error(f"❌ Order placement failed for {symbol}: {e}")
            logger.exception(e)
            return None
    
    async def monitor_positions(self) -> List[str]:
        """
        Monitor open positions and close if stop-loss, take-profit, or signal invalidation.
        
        動態監控機制：
        1. 檢查止損/止盈價格觸發
        2. 重新驗證開倉時的市場條件
        3. 如果信號失效，提前平倉
        4. 如果市場條件改善，調整止損/止盈
        
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
                
                # === 第一步：檢查傳統止損/止盈 ===
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
                
                # === 第二步：如果未觸發止損/止盈，驗證信號是否仍然有效 ===
                if not should_close and self.strategy_engine and self.data_service:
                    validation_result = await self.validate_position_signal(symbol, position, current_price)
                    
                    if validation_result['action'] == 'CLOSE':
                        should_close = True
                        reason = validation_result['reason']
                        self.stats['signal_invalidation_exits'] += 1
                        logger.warning(
                            f"⚠️  {symbol} 信號失效: {validation_result['details']}"
                        )
                    elif validation_result['action'] == 'ADJUST':
                        # 動態調整止損/止盈
                        await self.adjust_position_levels(symbol, position, validation_result)
                        self.stats['dynamic_adjustments'] += 1
                    elif validation_result['action'] == 'WARN':
                        # 發送警告但不平倉
                        if self.discord:
                            await self.discord.send_notification(
                                f"⚠️ **倉位警告** - {symbol}\n"
                                f"方向: {position.action}\n"
                                f"當前價格: {current_price:.4f}\n"
                                f"警告: {validation_result['details']}\n"
                                f"建議: 密切關注市場變化"
                            )
                
                if should_close:
                    await self.close_position(symbol, current_price, reason)
                    closed_symbols.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
        
        return closed_symbols
    
    async def validate_position_signal(self, symbol: str, position: Position, current_price: float) -> Dict[str, Any]:
        """
        驗證持倉信號是否仍然有效。
        
        檢查項目：
        1. 市場結構是否反轉
        2. 當前信號方向是否與開倉方向一致
        3. 信心度是否大幅下降
        4. 關鍵指標是否反轉
        
        Args:
            symbol: Trading symbol
            position: Current position
            current_price: Current market price
            
        Returns:
            {
                'action': 'HOLD' | 'CLOSE' | 'ADJUST' | 'WARN',
                'reason': str,
                'details': str,
                'new_stop_loss': float (optional),
                'new_take_profit': float (optional)
            }
        """
        try:
            # 獲取最新市場數據（使用配置的時間框架）
            klines = await self.data_service.fetch_klines(
                symbol=symbol,
                timeframe=self.timeframe,  # 使用與開倉一致的時間框架
                limit=200,
                force_refresh=False  # 使用緩存以減少 API 壓力
            )
            
            # 如果無法獲取數據，返回警告（而非靜默 HOLD）
            if klines is None or klines.empty:
                logger.warning(f"{symbol} 無法獲取市場數據，無法驗證信號")
                # 如果開倉時信心度很高，發送警告
                if position.confidence >= 80.0:
                    return {
                        'action': 'WARN',
                        'reason': 'no_validation_data',
                        'details': '無法獲取市場數據進行驗證，建議檢查 API 連接'
                    }
                return {'action': 'HOLD', 'reason': 'no_data', 'details': '無法獲取市場數據'}
            
            # 重新分析當前市場
            symbols_data = {symbol: (klines, current_price)}
            signals = await self.strategy_engine.analyze_batch(symbols_data)
            
            # 如果沒有新信號
            if not signals:
                # 檢查是否市場結構已經中性化（沒有明確方向）
                if position.confidence >= 85.0:  # 如果開倉時信心度很高
                    return {
                        'action': 'WARN',
                        'reason': 'signal_weakened',
                        'details': '市場信號消失，但尚未反轉，建議密切關注'
                    }
                return {'action': 'HOLD', 'reason': 'neutral', 'details': '市場中性，繼續持倉'}
            
            # 找到對應的交易對信號（修復：不要盲目取 signals[0]）
            current_signal = None
            for sig in signals:
                if sig.symbol == symbol:
                    current_signal = sig
                    break
            
            if current_signal is None:
                logger.warning(f"未找到 {symbol} 的信號，但策略返回了其他信號")
                return {'action': 'HOLD', 'reason': 'no_matching_signal', 'details': '未找到匹配的信號'}
            
            # === 檢查 1：方向是否反轉 ===
            if current_signal.action != position.action:
                return {
                    'action': 'CLOSE',
                    'reason': 'signal-reversal',
                    'details': f'市場信號反轉：原{position.action}，現{current_signal.action}（信心度{current_signal.confidence:.1f}%）'
                }
            
            # === 檢查 2：信心度是否大幅下降 ===
            confidence_drop = position.confidence - current_signal.confidence
            
            if confidence_drop > 20.0:  # 信心度下降超過20%
                return {
                    'action': 'CLOSE',
                    'reason': 'confidence-drop',
                    'details': f'信心度大幅下降：{position.confidence:.1f}% → {current_signal.confidence:.1f}%（下降{confidence_drop:.1f}%）'
                }
            elif confidence_drop > 10.0:  # 信心度下降10-20%
                return {
                    'action': 'WARN',
                    'reason': 'confidence-weakening',
                    'details': f'信心度下降：{position.confidence:.1f}% → {current_signal.confidence:.1f}%'
                }
            
            # === 檢查 3：信心度是否提升（可以放寬止損）===
            if current_signal.confidence > position.confidence + 5.0:
                # 信心度提升，可以考慮調整止損/止盈
                return {
                    'action': 'ADJUST',
                    'reason': 'confidence-improved',
                    'details': f'信心度提升：{position.confidence:.1f}% → {current_signal.confidence:.1f}%',
                    'new_stop_loss': current_signal.stop_loss,  # 使用新的止損
                    'new_take_profit': current_signal.take_profit  # 使用新的止盈
                }
            
            # === 檢查 4：價格是否偏離預期太遠 ===
            if position.action == 'BUY':
                # 做多倉位，如果價格跌破入場價太多但還沒觸及止損
                price_drop_pct = (position.entry_price - current_price) / position.entry_price * 100
                if price_drop_pct > 2.0 and current_signal.confidence < 75.0:
                    return {
                        'action': 'WARN',
                        'reason': 'adverse-movement',
                        'details': f'價格逆向移動{price_drop_pct:.2f}%，當前信心度{current_signal.confidence:.1f}%'
                    }
            else:  # SELL
                # 做空倉位，如果價格漲超入場價太多但還沒觸及止損
                price_rise_pct = (current_price - position.entry_price) / position.entry_price * 100
                if price_rise_pct > 2.0 and current_signal.confidence < 75.0:
                    return {
                        'action': 'WARN',
                        'reason': 'adverse-movement',
                        'details': f'價格逆向移動{price_rise_pct:.2f}%，當前信心度{current_signal.confidence:.1f}%'
                    }
            
            # 一切正常，繼續持倉
            return {'action': 'HOLD', 'reason': 'valid', 'details': '信號仍然有效'}
            
        except Exception as e:
            logger.error(f"Error validating signal for {symbol}: {e}")
            return {'action': 'HOLD', 'reason': 'error', 'details': f'驗證錯誤: {str(e)}'}
    
    async def adjust_position_levels(self, symbol: str, position: Position, validation_result: Dict[str, Any]):
        """
        動態調整倉位的止損/止盈水平。
        
        Args:
            symbol: Trading symbol
            position: Current position
            validation_result: Validation result with new levels
        """
        try:
            new_sl = validation_result.get('new_stop_loss')
            new_tp = validation_result.get('new_take_profit')
            
            if new_sl is None and new_tp is None:
                return
            
            old_sl = position.stop_loss
            old_tp = position.take_profit
            
            # === 驗證新的止損/止盈是否合理（不能比原來更寬鬆） ===
            # 對於多頭倉位
            if position.action == 'BUY':
                # 止損不能比原來更低（更寬鬆）
                if new_sl is not None and new_sl < old_sl:
                    logger.warning(f"{symbol} 新止損 {new_sl:.4f} 比原止損 {old_sl:.4f} 更寬鬆，拒絕調整")
                    new_sl = None  # 拒絕調整
                # 止盈可以調高（更保守）但不能調低
                if new_tp is not None and new_tp < old_tp:
                    logger.warning(f"{symbol} 新止盈 {new_tp:.4f} 比原止盈 {old_tp:.4f} 更差，使用原值")
                    new_tp = old_tp  # 保持原值
            else:  # SELL
                # 止損不能比原來更高（更寬鬆）
                if new_sl is not None and new_sl > old_sl:
                    logger.warning(f"{symbol} 新止損 {new_sl:.4f} 比原止損 {old_sl:.4f} 更寬鬆，拒絕調整")
                    new_sl = None  # 拒絕調整
                # 止盈可以調低（更保守）但不能調高
                if new_tp is not None and new_tp > old_tp:
                    logger.warning(f"{symbol} 新止盈 {new_tp:.4f} 比原止盈 {old_tp:.4f} 更差，使用原值")
                    new_tp = old_tp  # 保持原值
            
            # 如果調整被完全拒絕，返回
            if new_sl is None and new_tp is None:
                logger.info(f"{symbol} 動態調整被拒絕（風險保護）")
                return
            
            # 更新倉位
            if new_sl is not None:
                position.stop_loss = new_sl
            else:
                new_sl = old_sl  # 用於日誌顯示
            
            if new_tp is not None:
                position.take_profit = new_tp
            else:
                new_tp = old_tp  # 用於日誌顯示
            
            # 更新 risk manager
            if symbol in self.risk_manager.open_positions:
                self.risk_manager.open_positions[symbol]['stop_loss'] = position.stop_loss
                self.risk_manager.open_positions[symbol]['take_profit'] = position.take_profit
            
            logger.info(
                f"🔄 {symbol} 動態調整止損/止盈:\n"
                f"   止損: {old_sl:.4f} → {new_sl:.4f}\n"
                f"   止盈: {old_tp:.4f} → {new_tp:.4f}\n"
                f"   原因: {validation_result['details']}"
            )
            
            # 發送 Discord 通知
            if self.discord:
                await self.discord.send_notification(
                    f"🔄 **動態調整倉位** - {symbol}\n"
                    f"方向: {position.action}\n"
                    f"原因: {validation_result['details']}\n\n"
                    f"**止損調整**\n"
                    f"舊: {old_sl:.4f}\n"
                    f"新: {new_sl:.4f}\n\n"
                    f"**止盈調整**\n"
                    f"舊: {old_tp:.4f}\n"
                    f"新: {new_tp:.4f}"
                )
            
        except Exception as e:
            logger.error(f"Error adjusting position levels for {symbol}: {e}")
    
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
        
        # 📊 記錄平倉數據供 XGBoost 學習
        if self.trade_logger:
            trade_data = {
                'type': 'CLOSE',
                'symbol': symbol,
                'side': position.action,
                'entry_price': position.entry_price,
                'exit_price': price,
                'quantity': position.quantity,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit,
                'leverage': position.leverage,
                'pnl': pnl,
                'pnl_percent': pnl_pct,
                'reason': reason,
                'strategy': position.strategy,
                'confidence': position.confidence,
                'allocated_capital': position.allocated_capital,
                'duration_hours': (datetime.now() - position.opened_at).total_seconds() / 3600,
                'mode': 'LIVE' if self.enable_trading else 'SIMULATION',
                # 交易結果標記 (供 XGBoost 學習)
                'is_winner': pnl > 0,
                'hit_stop_loss': 'STOP' in reason.upper(),
                'hit_take_profit': 'PROFIT' in reason.upper() or 'TARGET' in reason.upper()
            }
            # 保持向後兼容的簡單記錄
            self.trade_logger.log_trade(trade_data)
            
            # 新增：記錄詳細的 ML 訓練數據（平倉）
            try:
                # 獲取當前市場數據（用於記錄平倉時的技術指標）
                exit_metadata = {}
                if self.data_service:
                    try:
                        klines = await self.data_service.fetch_klines(
                            symbol=symbol,
                            timeframe=self.timeframe,
                            limit=200,
                            force_refresh=False
                        )
                        if klines is not None and not klines.empty:
                            # 提取最新的技術指標（修復問題 2.2：添加導入錯誤處理）
                            try:
                                from utils.indicators import calculate_indicators
                            except ImportError as e:
                                logger.error(f"Failed to import calculate_indicators: {e}")
                                raise
                            
                            indicators_df = calculate_indicators(klines)
                            if not indicators_df.empty:
                                latest = indicators_df.iloc[-1]
                                exit_metadata = {
                                    'macd': latest.get('macd'),
                                    'macd_signal': latest.get('macd_signal'),
                                    'ema_9': latest.get('ema_9'),
                                    'ema_21': latest.get('ema_21'),
                                    'ema_50': latest.get('ema_50'),
                                    'ema_200': latest.get('ema_200'),
                                    'atr': latest.get('atr'),
                                    'rsi': latest.get('rsi')
                                }
                    except Exception as e:
                        logger.warning(f"Failed to fetch exit metadata for {symbol}: {e}")
                
                # 修復問題 2.1：確保 exit_data 包含所有必要字段
                exit_data = {
                    'trade_id': getattr(position, 'trade_id', None),
                    'symbol': symbol,
                    'side': position.action,  # 從 position 對象獲取 side（修復 2.1）
                    'entry_price': position.entry_price,  # 從 position 對象獲取 entry_price（修復 2.1）
                    'exit_price': price,
                    'exit_reason': reason,
                    'pnl': pnl,
                    'pnl_percent': pnl_pct,
                    'holding_duration_minutes': (datetime.now() - position.opened_at).total_seconds() / 60,
                    'entry_time': position.opened_at,
                    'exit_time': datetime.now(),
                    'metadata': exit_metadata
                }
                
                self.trade_logger.log_position_exit(
                    trade_data=exit_data,
                    binance_client=self.binance,
                    timeframe=self.timeframe
                )
            except Exception as e:
                logger.error(f"Failed to log position exit for ML: {e}")
                logger.exception(e)
        
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

"""
Virtual Position Tracker - 虛擬倉位追蹤系統

功能：
1. 追蹤排名第 4 名以後的交易信號（不實際開倉）
2. 收集虛擬交易數據供 XGBoost 訓練
3. 持久化虛擬倉位（進程重啟不丟失）
4. 檢查止盈/止損觸發並記錄完整數據
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class VirtualPosition:
    """虛擬倉位數據類"""
    trade_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    stop_loss: float
    take_profit: float
    quantity: float
    opened_at: str  # ISO format timestamp
    confidence: float
    expected_roi: float
    cycles_since_open: int  # 已經過的週期數
    max_age_cycles: int  # 最大追蹤週期數（默認 96，約 1.6 小時）
    metadata: Dict[str, Any]  # 完整的信號 metadata
    leverage: float = 1.0  # 槓桿
    margin: float = 0.0  # 保證金


class VirtualPositionTracker:
    """
    虛擬倉位追蹤器
    
    功能：
    1. 從排名第 4 開始的信號創建虛擬倉位（最多 10 個併發）
    2. 每個週期檢查虛擬倉位的止盈/止損是否觸發
    3. 當觸發或超時時，記錄平倉數據到 TradeLogger
    4. 持久化虛擬倉位（進程重啟不丟失）
    """
    
    def __init__(
        self,
        trade_logger,
        risk_manager,
        binance_client,
        max_virtual_positions: int = 10,
        min_confidence: float = 70.0,
        max_age_cycles: int = 96,
        persistence_file: str = 'virtual_positions.json'
    ):
        """
        初始化虛擬倉位追蹤器
        
        參數：
        - trade_logger: TradeLogger 實例
        - risk_manager: RiskManager 實例（用於計算止盈/止損）
        - binance_client: BinanceClient 實例（用於獲取價格）
        - max_virtual_positions: 最大併發虛擬倉位數（默認 10）
        - min_confidence: 最低信心度閾值（默認 70%）
        - max_age_cycles: 最大追蹤週期數（默認 96，約 1.6 小時）
        - persistence_file: 持久化文件路徑
        """
        self.trade_logger = trade_logger
        self.risk_manager = risk_manager
        self.binance_client = binance_client
        self.max_virtual_positions = max_virtual_positions
        self.min_confidence = min_confidence
        self.max_age_cycles = max_age_cycles
        self.persistence_file = persistence_file
        
        # 虛擬倉位存儲
        self.virtual_positions: Dict[str, VirtualPosition] = {}
        
        # 統計信息
        self.stats = {
            'total_created': 0,
            'total_closed': 0,
            'take_profit_hits': 0,
            'stop_loss_hits': 0,
            'timeouts': 0
        }
        
        # 加載持久化的虛擬倉位
        self.load_virtual_positions()
        
        logger.info(
            f"VirtualPositionTracker initialized: "
            f"max_positions={max_virtual_positions}, "
            f"min_confidence={min_confidence}%, "
            f"max_age={max_age_cycles} cycles, "
            f"loaded_positions={len(self.virtual_positions)}"
        )
    
    def create_virtual_positions(self, signals: List, start_rank: int = 4):
        """
        從排名第 start_rank 開始創建虛擬倉位
        
        參數：
        - signals: 已排序的信號列表（Signal 對象）
        - start_rank: 從第幾名開始（默認第 4 名，索引為 3）
        
        流程：
        1. 過濾：排名 >= start_rank 且信心度 >= min_confidence
        2. 限制：當前虛擬倉位數 < max_virtual_positions
        3. 計算倉位大小（重用 RiskManager）
        4. 創建 VirtualPosition 對象
        5. 調用 TradeLogger.log_position_entry(..., is_virtual=True)
        6. 存儲到 self.virtual_positions
        7. 持久化
        """
        try:
            # 檢查可用槽位
            available_slots = self.max_virtual_positions - len(self.virtual_positions)
            if available_slots <= 0:
                logger.debug(f"No available slots for virtual positions ({len(self.virtual_positions)}/{self.max_virtual_positions})")
                return
            
            # 過濾信號：從 start_rank 開始，信心度 >= min_confidence
            candidate_signals = []
            for i, signal in enumerate(signals):
                # 檢查排名（索引 >= start_rank - 1）
                if i < start_rank - 1:
                    continue
                
                # 檢查信心度
                if signal.confidence < self.min_confidence:
                    logger.debug(f"Skipping {signal.symbol}: confidence {signal.confidence:.1f}% < {self.min_confidence}%")
                    continue
                
                # ✅ 修復：檢查是否已存在該交易對的虛擬倉位（現在 dict 的鍵是 trade_id，需要檢查值）
                has_position = any(pos.symbol == signal.symbol for pos in self.virtual_positions.values())
                if has_position:
                    logger.debug(f"Skipping {signal.symbol}: already has virtual position")
                    continue
                
                candidate_signals.append(signal)
            
            # 限制數量
            signals_to_create = candidate_signals[:available_slots]
            
            if not signals_to_create:
                logger.debug("No candidate signals for virtual positions")
                return
            
            # 創建虛擬倉位
            for signal in signals_to_create:
                try:
                    self._create_single_virtual_position(signal)
                except Exception as e:
                    logger.error(f"Error creating virtual position for {signal.symbol}: {e}")
                    continue
            
            # 持久化
            self.save_virtual_positions()
            
            logger.info(
                f"📊 Created {len(signals_to_create)} virtual positions "
                f"(active: {len(self.virtual_positions)}/{self.max_virtual_positions})"
            )
            
        except Exception as e:
            logger.error(f"Error in create_virtual_positions: {e}")
    
    def _create_single_virtual_position(self, signal):
        """
        創建單個虛擬倉位
        
        參數：
        - signal: Signal 對象
        """
        try:
            # 計算動態槓桿
            atr = signal.metadata.get('atr', 0)
            current_price = signal.metadata.get('current_price', signal.price)
            leverage = self.risk_manager.calculate_dynamic_leverage(
                confidence=signal.confidence,
                atr=atr,
                current_price=current_price
            )
            
            # 計算倉位大小
            position_params = self.risk_manager.calculate_position_size(
                symbol=signal.symbol,
                entry_price=signal.price,
                stop_loss_price=signal.stop_loss,
                confidence=signal.confidence,
                leverage=leverage
            )
            
            if not position_params:
                logger.warning(f"Risk check failed for virtual position {signal.symbol}")
                return
            
            # 準備開倉數據（TradeLogger 會生成 trade_id）
            timestamp = datetime.utcnow()
            
            # 記錄開倉到 TradeLogger（標記為虛擬），獲取真實的 trade_id
            trade_data = {
                'type': 'OPEN',
                'symbol': signal.symbol,
                'side': signal.action,
                'entry_price': signal.price,
                'quantity': position_params['quantity'],
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'leverage': position_params['leverage'],
                'margin': position_params['margin'],
                'margin_percent': position_params['margin_percent'],
                'confidence': signal.confidence,
                'expected_roi': signal.expected_roi,
                'strategy': signal.strategy,
                'reason': f"Virtual position (rank >= 4)",
                'metadata': signal.metadata
            }
            
            # ✅ 修復：捕獲 TradeLogger 返回的 trade_id
            returned_trade_id = self.trade_logger.log_position_entry(
                trade_data,
                binance_client=self.binance_client,
                is_virtual=True
            )
            
            # ✅ 修復：使用 TradeLogger 返回的 trade_id（如果返回 None，使用降級機制）
            if returned_trade_id:
                actual_trade_id = returned_trade_id
            else:
                # 降級：生成備用 ID
                actual_trade_id = f"VIRTUAL_{signal.symbol}_{int(timestamp.timestamp() * 1000)}_fallback"
                logger.warning(
                    f"⚠️ TradeLogger.log_position_entry returned None for {signal.symbol}, "
                    f"using fallback ID: {actual_trade_id}"
                )
            
            # ✅ 修復：創建虛擬倉位對象（使用正確的 trade_id）
            virtual_pos = VirtualPosition(
                trade_id=actual_trade_id,
                symbol=signal.symbol,
                side=signal.action,
                entry_price=signal.price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                quantity=position_params['quantity'],
                opened_at=timestamp.isoformat(),
                confidence=signal.confidence,
                expected_roi=signal.expected_roi,
                cycles_since_open=0,
                max_age_cycles=self.max_age_cycles,
                metadata=signal.metadata,
                leverage=position_params['leverage'],
                margin=position_params['margin']
            )
            
            # ✅ 修復：存儲虛擬倉位（使用 trade_id 作為鍵）
            self.virtual_positions[actual_trade_id] = virtual_pos
            self.stats['total_created'] += 1
            
            logger.info(
                f"🔷 Created VIRTUAL position: {actual_trade_id} - {signal.action} {signal.symbol} @ {signal.price:.4f} "
                f"(confidence: {signal.confidence:.1f}%, qty: {position_params['quantity']:.4f})"
            )
            
        except Exception as e:
            logger.error(f"Error creating virtual position for {signal.symbol}: {e}")
    
    async def check_virtual_positions(self, data_service):
        """
        檢查所有虛擬倉位的止盈/止損是否觸發
        
        參數：
        - data_service: DataService 實例（用於批量獲取價格）
        
        流程：
        1. 遍歷所有虛擬倉位
        2. 增加 cycles_since_open
        3. 批量獲取當前價格（從 data_service 緩存或 binance_client）
        4. 檢查是否觸發止盈/止損或超時
        5. 如果觸發，調用 _close_virtual_position()
        6. 持久化更新
        """
        if not self.virtual_positions:
            return
        
        try:
            # ✅ 修復：獲取需要檢查的交易對列表（從倉位的 symbol 提取）
            symbols = list(set(pos.symbol for pos in self.virtual_positions.values()))
            
            # 批量獲取當前價格（使用 ticker 數據）
            prices = {}
            for symbol in symbols:
                try:
                    # 嘗試從 data_service 獲取 ticker
                    ticker = await data_service.get_ticker_info(symbol)
                    if ticker and 'lastPrice' in ticker:
                        prices[symbol] = float(ticker['lastPrice'])
                    else:
                        # 如果 ticker 失敗，跳過此交易對
                        logger.warning(f"Failed to get price for {symbol}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching price for {symbol}: {e}")
                    continue
            
            # ✅ 修復：檢查每個虛擬倉位（現在鍵是 trade_id）
            positions_to_close = []
            for trade_id, pos in list(self.virtual_positions.items()):
                try:
                    # 增加週期計數
                    pos.cycles_since_open += 1
                    
                    # 獲取當前價格
                    current_price = prices.get(pos.symbol)
                    if current_price is None:
                        logger.debug(f"No price available for {pos.symbol}, skipping check")
                        continue
                    
                    # 檢查是否觸發止盈/止損
                    exit_reason = None
                    exit_price = None
                    
                    if pos.side in ['BUY', 'LONG']:
                        # 做多：止盈 = 價格上漲，止損 = 價格下跌
                        if current_price >= pos.take_profit:
                            exit_reason = 'TAKE_PROFIT'
                            exit_price = pos.take_profit
                        elif current_price <= pos.stop_loss:
                            exit_reason = 'STOP_LOSS'
                            exit_price = pos.stop_loss
                    else:  # SELL or SHORT
                        # 做空：止盈 = 價格下跌，止損 = 價格上漲
                        if current_price <= pos.take_profit:
                            exit_reason = 'TAKE_PROFIT'
                            exit_price = pos.take_profit
                        elif current_price >= pos.stop_loss:
                            exit_reason = 'STOP_LOSS'
                            exit_price = pos.stop_loss
                    
                    # 檢查超時
                    if exit_reason is None and pos.cycles_since_open >= pos.max_age_cycles:
                        exit_reason = 'TIMEOUT'
                        exit_price = current_price
                    
                    # 如果需要平倉，記錄到待處理列表
                    if exit_reason:
                        positions_to_close.append((pos.trade_id, exit_price, exit_reason))
                        
                except Exception as e:
                    logger.error(f"Error checking virtual position {trade_id} ({pos.symbol}): {e}")
                    continue
            
            # 平倉所有觸發的虛擬倉位
            if positions_to_close:
                for trade_id, exit_price, exit_reason in positions_to_close:
                    try:
                        self._close_virtual_position(trade_id, exit_price, exit_reason)
                    except Exception as e:
                        logger.error(f"Error closing virtual position {trade_id}: {e}")
                
                # 持久化更新
                self.save_virtual_positions()
                
                logger.info(f"Closed {len(positions_to_close)} virtual positions")
            
        except Exception as e:
            logger.error(f"Error in check_virtual_positions: {e}")
    
    def _close_virtual_position(self, trade_id: str, exit_price: float, exit_reason: str):
        """
        平倉虛擬倉位並記錄數據
        
        參數：
        - trade_id: 虛擬倉位的 trade_id
        - exit_price: 平倉價格
        - exit_reason: 平倉原因（"TAKE_PROFIT", "STOP_LOSS", "TIMEOUT"）
        
        流程：
        1. 獲取虛擬倉位信息
        2. 計算 PnL
        3. 準備 exit_data（包含所有必要字段）
        4. 調用 TradeLogger.log_position_exit(..., is_virtual=True)
        5. 從 self.virtual_positions 中刪除
        6. 更新統計
        """
        try:
            # ✅ 修復：直接通過 trade_id 查找虛擬倉位
            pos = self.virtual_positions.get(trade_id)
            
            if not pos:
                logger.error(f"Virtual position not found: {trade_id}")
                return
            
            # 計算 PnL
            if pos.side in ['BUY', 'LONG']:
                pnl = (exit_price - pos.entry_price) * pos.quantity
            else:  # SELL or SHORT
                pnl = (pos.entry_price - exit_price) * pos.quantity
            
            pnl_percent = (pnl / pos.margin) * 100 if pos.margin > 0 else 0
            
            # 準備平倉數據
            exit_data = {
                'type': 'CLOSE',
                'trade_id': trade_id,
                'symbol': pos.symbol,
                'side': pos.side,
                'entry_price': pos.entry_price,
                'exit_price': exit_price,
                'quantity': pos.quantity,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'reason': exit_reason,
                'leverage': pos.leverage,
                'margin': pos.margin,
                'confidence': pos.confidence,
                'expected_roi': pos.expected_roi,
                'cycles_held': pos.cycles_since_open,
                'metadata': pos.metadata
            }
            
            # 記錄平倉到 TradeLogger
            self.trade_logger.log_position_exit(
                exit_data,
                binance_client=self.binance_client,
                is_virtual=True
            )
            
            # ✅ 修復：從虛擬倉位中刪除（使用 trade_id 作為鍵）
            del self.virtual_positions[trade_id]
            
            # 更新統計
            self.stats['total_closed'] += 1
            if exit_reason == 'TAKE_PROFIT':
                self.stats['take_profit_hits'] += 1
            elif exit_reason == 'STOP_LOSS':
                self.stats['stop_loss_hits'] += 1
            elif exit_reason == 'TIMEOUT':
                self.stats['timeouts'] += 1
            
            logger.info(
                f"🔷 Closed VIRTUAL position: {pos.symbol} @ {exit_price:.4f} "
                f"(PnL: ${pnl:+.2f}, {pnl_percent:+.2f}%, reason: {exit_reason})"
            )
            
        except Exception as e:
            logger.error(f"Error closing virtual position {trade_id}: {e}")
    
    def load_virtual_positions(self):
        """從文件加載虛擬倉位"""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # ✅ 修復：重建 VirtualPosition 對象（使用 trade_id 作為鍵）
                    for trade_id, pos_dict in data.items():
                        self.virtual_positions[trade_id] = VirtualPosition(**pos_dict)
                    
                    logger.info(f"Loaded {len(self.virtual_positions)} virtual positions from {self.persistence_file}")
            else:
                logger.info(f"No existing virtual positions file found at {self.persistence_file}")
                
        except Exception as e:
            logger.error(f"Error loading virtual positions: {e}")
            self.virtual_positions = {}
    
    def save_virtual_positions(self):
        """保存虛擬倉位到文件"""
        try:
            # ✅ 修復：轉換為可序列化的字典（使用 trade_id 作為鍵）
            data = {}
            for trade_id, pos in self.virtual_positions.items():
                data[trade_id] = asdict(pos)
            
            # 保存到文件
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.virtual_positions)} virtual positions to {self.persistence_file}")
            
        except Exception as e:
            logger.error(f"Error saving virtual positions: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取虛擬倉位統計信息"""
        return {
            "active_virtual_positions": len(self.virtual_positions),
            "max_virtual_positions": self.max_virtual_positions,
            "available_slots": self.max_virtual_positions - len(self.virtual_positions),
            "total_created": self.stats['total_created'],
            "total_closed": self.stats['total_closed'],
            "take_profit_hits": self.stats['take_profit_hits'],
            "stop_loss_hits": self.stats['stop_loss_hits'],
            "timeouts": self.stats['timeouts']
        }

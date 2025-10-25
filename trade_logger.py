import json
import os
import threading
import time
import atexit
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.helpers import setup_logger

logger = setup_logger(__name__)

ML_FEATURE_SCHEMA = {
    'signal_features': {
        'confidence': {'type': 'float', 'required': True, 'description': '信號信心度 (0-100)'},
        'expected_roi': {'type': 'float', 'required': True, 'description': '預期收益率 (%)'},
        'strategy': {'type': 'str', 'required': True, 'description': '策略名稱 (ICT_SMC, etc.)'},
        'reason': {'type': 'str', 'required': True, 'description': '開倉理由'},
        'market_structure': {'type': 'str', 'required': False, 'description': '市場結構 (bullish/bearish/neutral)'},
        'ob_score': {'type': 'float', 'required': False, 'description': '訂單塊得分'},
        'liquidity_grabbed': {'type': 'bool', 'required': False, 'description': '是否抓取流動性'},
        'trend_15m': {'type': 'str', 'required': False, 'description': '15分鐘趨勢'},
        'trend_1h': {'type': 'str', 'required': False, 'description': '1小時趨勢'}
    },
    'technical_indicators': {
        'macd': {'type': 'float', 'required': False, 'description': 'MACD 值'},
        'macd_signal': {'type': 'float', 'required': False, 'description': 'MACD 信號線'},
        'macd_histogram': {'type': 'float', 'required': False, 'description': 'MACD 柱狀圖'},
        'ema_9': {'type': 'float', 'required': False, 'description': '9週期EMA'},
        'ema_21': {'type': 'float', 'required': False, 'description': '21週期EMA'},
        'ema_50': {'type': 'float', 'required': False, 'description': '50週期EMA'},
        'ema_200': {'type': 'float', 'required': False, 'description': '200週期EMA'},
        'atr': {'type': 'float', 'required': False, 'description': '平均真實範圍'},
        'bollinger_upper': {'type': 'float', 'required': False, 'description': '布林帶上軌'},
        'bollinger_middle': {'type': 'float', 'required': False, 'description': '布林帶中軌'},
        'bollinger_lower': {'type': 'float', 'required': False, 'description': '布林帶下軌'},
        'rsi': {'type': 'float', 'required': False, 'description': '相對強弱指標'}
    },
    'price_position': {
        'current_price': {'type': 'float', 'required': True, 'description': '當前價格'},
        'distance_from_ema200': {'type': 'float', 'required': False, 'description': '與EMA200的距離'},
        'distance_from_ema200_pct': {'type': 'float', 'required': False, 'description': '與EMA200的距離百分比'}
    },
    'trade_parameters': {
        'entry_price': {'type': 'float', 'required': True, 'description': '入場價格'},
        'stop_loss': {'type': 'float', 'required': False, 'description': '止損價格'},
        'take_profit': {'type': 'float', 'required': False, 'description': '止盈價格'},
        'leverage': {'type': 'float', 'required': True, 'description': '槓桿倍數'},
        'margin': {'type': 'float', 'required': True, 'description': '保證金'},
        'margin_percent': {'type': 'float', 'required': True, 'description': '保證金百分比'}
    },
    'kline_data': {
        'entry_klines': {'type': 'list', 'required': False, 'description': '開倉時K線快照 (最近20根)'},
        'kline_history': {'type': 'list', 'required': False, 'description': '持倉期間完整K線歷史'}
    },
    'outcome_labels': {
        'outcome': {'type': 'str', 'required': True, 'description': '交易結果 (WIN/LOSS)'},
        'pnl_percent': {'type': 'float', 'required': True, 'description': '損益百分比'},
        'max_favorable_excursion': {'type': 'float', 'required': True, 'description': '最大有利波動 (%)'},
        'max_adverse_excursion': {'type': 'float', 'required': True, 'description': '最大不利波動 (%)'},
        'hit_take_profit': {'type': 'bool', 'required': True, 'description': '是否觸及止盈'},
        'hit_stop_loss': {'type': 'bool', 'required': True, 'description': '是否觸及止損'}
    }
}


class TradeLogger:
    """
    增強的交易日誌記錄器 - 支持完整的 XGBoost 機器學習數據記錄
    
    功能：
    1. 記錄開倉時的完整特徵數據（技術指標、K線快照、信號特徵）
    2. 記錄平倉時的完整歷史數據（K線歷史、MFE/MAE、交易結果）
    3. 合併開倉/平倉數據生成完整的 ML 訓練樣本
    4. 保存基本交易記錄和 ML 訓練數據到不同文件
    5. 智能 Flush 機制：每 10 筆交易或 30 秒自動保存
    6. 數據完整性驗證：確保所有開倉都有對應的平倉
    7. 統計追蹤：記錄完整性、特徵覆蓋率等
    """
    
    def __init__(self, log_file='trades.json', ml_file='ml_training_data.json', buffer_size=10, auto_flush_interval=30):
        """
        初始化交易日誌記錄器
        
        Args:
            log_file: 基本交易記錄文件
            ml_file: ML 訓練數據文件
            buffer_size: 緩衝區大小（多少條記錄後保存一次）
            auto_flush_interval: 自動 flush 時間間隔（秒）
        """
        self.log_file = log_file
        self.ml_file = ml_file
        self.pending_entries_file = 'ml_pending_entries.json'
        self.buffer_size = buffer_size
        self.auto_flush_interval = auto_flush_interval
        self.unsaved_count = 0
        self.last_flush_time = time.time()
        
        # 統計數據
        self.stats = {
            'total_entries': 0,
            'total_exits': 0,
            'complete_pairs': 0,
            'incomplete_pairs': 0,
            'total_flushes': 0,
            'last_flush_timestamp': None,
            'validation_errors': 0,
            'feature_coverage': {}
        }
        
        # 加載現有記錄
        self.trades = self.load_trades()
        
        # ML 訓練數據結構
        self.ml_data = self.load_ml_data()
        self.pending_entries = self.load_pending_entries()
        
        # 更新統計數據
        self.stats['incomplete_pairs'] = len(self.pending_entries)
        self.stats['complete_pairs'] = len(self.ml_data)
        
        # 啟動自動 flush 線程
        self._stop_auto_flush = threading.Event()
        self._auto_flush_thread = threading.Thread(target=self._auto_flush_worker, daemon=True)
        self._auto_flush_thread.start()
        
        # 註冊退出時強制 flush
        atexit.register(self._on_exit)
        
        logger.info(
            f"TradeLogger initialized: "
            f"trades={len(self.trades)}, "
            f"ml_samples={len(self.ml_data)}, "
            f"pending_entries={len(self.pending_entries)}, "
            f"auto_flush_interval={auto_flush_interval}s"
        )
    
    def _auto_flush_worker(self):
        """自動 flush 工作線程 - 每 N 秒檢查並 flush"""
        while not self._stop_auto_flush.is_set():
            try:
                time.sleep(self.auto_flush_interval)
                
                current_time = time.time()
                time_since_last_flush = current_time - self.last_flush_time
                
                if time_since_last_flush >= self.auto_flush_interval:
                    if self.unsaved_count > 0 or len(self.ml_data) > 0:
                        logger.debug(f"Auto-flush triggered (interval: {self.auto_flush_interval}s)")
                        self.flush()
                
            except Exception as e:
                logger.error(f"Error in auto-flush worker: {e}")
    
    def _on_exit(self):
        """程序退出時的清理函數"""
        logger.info("TradeLogger shutting down, flushing all data...")
        self._stop_auto_flush.set()
        self.flush()
        logger.info("TradeLogger shutdown complete")
    
    def load_trades(self) -> List[Dict]:
        """加載現有交易記錄"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading trades: {e}")
                return []
        return []
    
    def load_ml_data(self) -> List[Dict]:
        """加載現有 ML 訓練數據"""
        if os.path.exists(self.ml_file):
            try:
                with open(self.ml_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading ML data: {e}")
                return []
        return []
    
    def load_pending_entries(self) -> Dict[str, Dict]:
        """
        加載待處理的開倉記錄
        
        進程重啟時從文件恢復待處理的開倉記錄，避免孤立交易
        
        Returns:
            待處理的開倉記錄字典
        """
        if os.path.exists(self.pending_entries_file):
            try:
                with open(self.pending_entries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} pending entries from {self.pending_entries_file}")
                    return data
            except Exception as e:
                logger.error(f"Error loading pending entries: {e}")
                return {}
        return {}
    
    def save_pending_entries(self):
        """
        保存待處理的開倉記錄到文件
        
        確保重啟後不會丟失待處理的開倉記錄
        """
        try:
            with open(self.pending_entries_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_entries, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.pending_entries)} pending entries to {self.pending_entries_file}")
        except Exception as e:
            logger.error(f"Error saving pending entries: {e}")
    
    def save_trades(self):
        """保存交易記錄到文件"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.trades)} trades to {self.log_file}")
            self.unsaved_count = 0
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
    
    def save_ml_data(self):
        """保存 ML 訓練數據到單獨文件"""
        try:
            with open(self.ml_file, 'w', encoding='utf-8') as f:
                json.dump(self.ml_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(self.ml_data)} ML training samples to {self.ml_file}")
        except Exception as e:
            logger.error(f"Error saving ML data: {e}")
    
    def validate_entry_data(self, trade_data: Dict) -> tuple[bool, List[str]]:
        """
        驗證開倉數據的完整性和正確性
        
        Args:
            trade_data: 開倉數據字典
            
        Returns:
            (is_valid, missing_fields)
        """
        missing_fields = []
        warnings = []
        
        # 檢查必需字段
        required_fields = ['symbol', 'side', 'entry_price', 'quantity', 'leverage', 'margin', 'confidence']
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                missing_fields.append(field)
        
        # 檢查數據類型和範圍
        if 'confidence' in trade_data:
            confidence = trade_data['confidence']
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 100):
                warnings.append(f"Invalid confidence value: {confidence}")
        
        if 'entry_price' in trade_data:
            if not isinstance(trade_data['entry_price'], (int, float)) or trade_data['entry_price'] <= 0:
                warnings.append(f"Invalid entry_price: {trade_data['entry_price']}")
        
        if 'leverage' in trade_data:
            if not isinstance(trade_data['leverage'], (int, float)) or trade_data['leverage'] <= 0:
                warnings.append(f"Invalid leverage: {trade_data['leverage']}")
        
        # 記錄警告
        if warnings:
            logger.warning(f"Validation warnings for entry data: {warnings}")
            self.stats['validation_errors'] += 1
        
        is_valid = len(missing_fields) == 0
        
        if not is_valid:
            logger.error(f"Missing required fields in entry data: {missing_fields}")
            self.stats['validation_errors'] += 1
        
        return is_valid, missing_fields
    
    def validate_exit_data(self, trade_data: Dict) -> tuple[bool, List[str]]:
        """
        驗證平倉數據的完整性和正確性
        
        Args:
            trade_data: 平倉數據字典
            
        Returns:
            (is_valid, missing_fields)
        """
        missing_fields = []
        warnings = []
        
        # 檢查必需字段
        required_fields = ['trade_id', 'symbol', 'exit_price', 'pnl', 'pnl_percent']
        for field in required_fields:
            if field not in trade_data or trade_data[field] is None:
                missing_fields.append(field)
        
        # 檢查 trade_id 是否存在於 pending_entries
        if 'trade_id' in trade_data:
            trade_id = trade_data['trade_id']
            if trade_id not in self.pending_entries:
                warnings.append(f"No matching entry record for trade_id: {trade_id}")
        
        # 記錄警告
        if warnings:
            logger.warning(f"Validation warnings for exit data: {warnings}")
            self.stats['validation_errors'] += 1
        
        is_valid = len(missing_fields) == 0
        
        if not is_valid:
            logger.error(f"Missing required fields in exit data: {missing_fields}")
            self.stats['validation_errors'] += 1
        
        return is_valid, missing_fields
    
    def calculate_feature_coverage(self, entry_record: Dict) -> Dict[str, float]:
        """
        計算特徵覆蓋率
        
        Args:
            entry_record: 開倉記錄
            
        Returns:
            特徵覆蓋率字典
        """
        coverage = {
            'signal_features': 0,
            'technical_indicators': 0,
            'price_position': 0,
            'kline_data': 0
        }
        
        signal_features = entry_record.get('signal_features', {})
        total_signal_features = len(ML_FEATURE_SCHEMA['signal_features'])
        present_signal_features = sum(1 for k in ML_FEATURE_SCHEMA['signal_features'].keys() if k in signal_features and signal_features[k] is not None)
        coverage['signal_features'] = (present_signal_features / total_signal_features * 100) if total_signal_features > 0 else 0
        
        total_tech_indicators = len(ML_FEATURE_SCHEMA['technical_indicators'])
        present_tech_indicators = sum(1 for k in ML_FEATURE_SCHEMA['technical_indicators'].keys() if k in signal_features and signal_features[k] is not None)
        coverage['technical_indicators'] = (present_tech_indicators / total_tech_indicators * 100) if total_tech_indicators > 0 else 0
        
        total_price_position = len(ML_FEATURE_SCHEMA['price_position'])
        present_price_position = sum(1 for k in ML_FEATURE_SCHEMA['price_position'].keys() if k in signal_features and signal_features[k] is not None)
        coverage['price_position'] = (present_price_position / total_price_position * 100) if total_price_position > 0 else 0
        
        has_entry_klines = 'entry_klines' in entry_record and entry_record['entry_klines']
        coverage['kline_data'] = 100 if has_entry_klines else 0
        
        return coverage
    
    def log_position_entry(self, trade_data: Dict, binance_client=None, timeframe='1m', is_virtual=False) -> str:
        """
        記錄開倉時的完整特徵數據
        
        Args:
            trade_data: 交易數據字典，包含：
                - symbol: 交易對
                - side: 'BUY' or 'SELL'
                - entry_price: 入場價格
                - quantity: 數量
                - stop_loss: 止損價格
                - take_profit: 止盈價格
                - leverage: 槓桿
                - margin: 保證金
                - margin_percent: 保證金百分比
                - confidence: 信心度
                - expected_roi: 預期收益
                - strategy: 策略名稱
                - reason: 開倉理由
                - metadata: 信號的完整 metadata（包含所有技術指標）
            binance_client: Binance 客戶端（用於獲取 K 線快照）
            timeframe: 時間框架
            is_virtual: 是否為虛擬倉位（默認 False）
            
        Returns:
            trade_id: 唯一的交易ID
        """
        try:
            # 驗證數據
            is_valid, missing_fields = self.validate_entry_data(trade_data)
            if not is_valid:
                logger.error(f"Entry data validation failed, missing fields: {missing_fields}")
                return None
            
            # 生成唯一的交易ID
            timestamp = datetime.utcnow()
            trade_id = self._generate_trade_id(trade_data['symbol'], timestamp)
            
            # 獲取 K 線快照（最近 20 根）
            entry_klines = []
            if binance_client:
                try:
                    entry_klines = self._fetch_klines_snapshot(
                        binance_client, 
                        trade_data['symbol'], 
                        timeframe, 
                        limit=20
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch klines snapshot for {trade_data['symbol']}: {e}")
            
            # 從 metadata 中提取技術指標
            metadata = trade_data.get('metadata', {})
            
            # 構建完整的開倉記錄
            entry_record = {
                'trade_id': trade_id,
                'timestamp': timestamp.isoformat(),
                'symbol': trade_data.get('symbol', 'UNKNOWN'),
                'side': trade_data.get('side', 'BUY'),
                'entry_price': self._safe_float(trade_data.get('entry_price'), 0.0),
                'quantity': self._safe_float(trade_data.get('quantity'), 0.0),
                'stop_loss': self._safe_float(trade_data.get('stop_loss')),
                'take_profit': self._safe_float(trade_data.get('take_profit')),
                'leverage': self._safe_float(trade_data.get('leverage'), 1.0),
                'margin': self._safe_float(trade_data.get('margin'), 0.0),
                'margin_percent': self._safe_float(trade_data.get('margin_percent'), 0.0),
                'is_virtual': is_virtual,
                
                # ICT/SMC 信號特徵
                'signal_features': {
                    'confidence': self._safe_float(trade_data.get('confidence'), 0.0),
                    'expected_roi': self._safe_float(trade_data.get('expected_roi'), 0.0),
                    'strategy': trade_data.get('strategy', 'UNKNOWN'),
                    'reason': trade_data.get('reason', ''),
                    
                    # 市場結構（從 metadata 提取）
                    'market_structure': metadata.get('market_structure', 'neutral'),
                    'ob_score': self._safe_float(metadata.get('ob_score')),
                    'liquidity_grabbed': metadata.get('liquidity_grabbed', False),
                    'trend_15m': metadata.get('trend_15m', 'neutral'),
                    'trend_1h': metadata.get('trend_1h', 'neutral'),
                    
                    # 技術指標（當下值）
                    'macd': self._safe_float(metadata.get('macd')),
                    'macd_signal': self._safe_float(metadata.get('macd_signal')),
                    'macd_histogram': self._safe_float(metadata.get('macd_histogram')),
                    'ema_9': self._safe_float(metadata.get('ema_9')),
                    'ema_21': self._safe_float(metadata.get('ema_21')),
                    'ema_50': self._safe_float(metadata.get('ema_50')),
                    'ema_200': self._safe_float(metadata.get('ema_200')),
                    'atr': self._safe_float(metadata.get('atr')),
                    'bollinger_upper': self._safe_float(metadata.get('bollinger_upper')),
                    'bollinger_middle': self._safe_float(metadata.get('bollinger_middle')),
                    'bollinger_lower': self._safe_float(metadata.get('bollinger_lower')),
                    'rsi': self._safe_float(metadata.get('rsi')),
                    
                    # 價格位置
                    'current_price': self._safe_float(metadata.get('current_price')),
                    'distance_from_ema200': self._calculate_distance_from_ema200(
                        metadata.get('current_price'),
                        metadata.get('ema_200')
                    ),
                    'distance_from_ema200_pct': self._calculate_distance_from_ema200_pct(
                        metadata.get('current_price'),
                        metadata.get('ema_200')
                    ),
                    
                    # 完整的 metadata
                    'metadata': self._sanitize_metadata(metadata)
                },
                
                # 開倉時的 K 線快照（最近 20 根）
                'entry_klines': entry_klines
            }
            
            # 計算特徵覆蓋率
            coverage = self.calculate_feature_coverage(entry_record)
            self.stats['feature_coverage'] = coverage
            
            # 暫存開倉數據，等待平倉後合併
            self.pending_entries[trade_id] = entry_record
            
            # 更新統計
            self.stats['total_entries'] += 1
            self.stats['incomplete_pairs'] = len(self.pending_entries)
            
            # 立即持久化到文件，避免進程重啟導致孤立交易
            self.save_pending_entries()
            
            logger.info(
                f"📥 Logged position entry: {trade_id} ({trade_data.get('symbol', 'UNKNOWN')} {trade_data.get('side', 'BUY')}), "
                f"feature_coverage: {coverage}"
            )
            
            # 檢查是否需要 flush（每 buffer_size 條記錄）
            self._check_and_flush()
            
            return trade_id
            
        except Exception as e:
            logger.error(f"Error logging position entry: {e}")
            logger.exception(e)
            return None
    
    def log_position_exit(self, trade_data: Dict, binance_client=None, timeframe='1m', is_virtual=False):
        """
        記錄平倉時的完整歷史數據，並合併開倉數據生成 ML 訓練樣本
        
        Args:
            trade_data: 交易數據字典，包含：
                - trade_id: 交易ID（與開倉時相同）
                - symbol: 交易對
                - exit_price: 出場價格
                - exit_reason: 平倉理由
                - pnl: 損益（USDT）
                - pnl_percent: 損益百分比
                - holding_duration_minutes: 持倉時長（分鐘）
                - entry_time: 開倉時間（用於獲取 K 線歷史）
                - exit_time: 平倉時間
                - metadata: 平倉時的技術指標
            binance_client: Binance 客戶端（用於獲取 K 線歷史）
            timeframe: 時間框架
            is_virtual: 是否為虛擬倉位（默認 False）
        """
        try:
            # 驗證數據
            is_valid, missing_fields = self.validate_exit_data(trade_data)
            if not is_valid:
                logger.error(f"Exit data validation failed, missing fields: {missing_fields}")
                return
            
            trade_id = trade_data.get('trade_id')
            
            if not trade_id:
                logger.error("Missing trade_id in exit data")
                return
            
            # 檢查是否有對應的開倉記錄
            if trade_id not in self.pending_entries:
                logger.warning(f"⚠️  No entry record found for trade_id: {trade_id} - incomplete trade pair!")
                self.stats['incomplete_pairs'] += 1
                entry_record = None
            else:
                entry_record = self.pending_entries[trade_id]
            
            # 驗證並解析時間戳
            entry_time = trade_data.get('entry_time')
            exit_time = trade_data.get('exit_time')
            
            # 如果是字符串，轉換為 datetime
            if isinstance(entry_time, str):
                try:
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                except Exception as e:
                    logger.error(f"Invalid entry_time timestamp: {entry_time}, error: {e}")
                    entry_time = None
            
            if isinstance(exit_time, str):
                try:
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                except Exception as e:
                    logger.error(f"Invalid exit_time timestamp: {exit_time}, error: {e}")
                    exit_time = None
            
            # 如果沒有提供 exit_time，使用當前時間
            if exit_time is None:
                exit_time = datetime.utcnow()
            
            # 獲取從開倉到平倉的完整 K 線歷史
            kline_history = []
            if binance_client and entry_record and entry_time:
                try:
                    kline_history = self._fetch_kline_history(
                        binance_client,
                        trade_data.get('symbol', 'UNKNOWN'),
                        entry_time,
                        exit_time,
                        timeframe
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch kline history for {trade_data.get('symbol', 'UNKNOWN')}: {e}")
            
            # 計算 MFE/MAE（最大有利/不利波動）
            entry_price = self._safe_float(entry_record.get('entry_price')) if entry_record else self._safe_float(trade_data.get('entry_price'), 0)
            entry_side = entry_record.get('side') if entry_record else trade_data.get('side', 'BUY')
            
            mfe, mae = self._calculate_mfe_mae(
                kline_history,
                entry_price,
                entry_side
            )
            
            # 從 metadata 中提取平倉時的技術指標
            exit_metadata = trade_data.get('metadata', {})
            
            # 構建平倉記錄
            exit_record = {
                'trade_id': trade_id,
                'timestamp': trade_data.get('exit_time', datetime.utcnow()).isoformat() if isinstance(trade_data.get('exit_time'), datetime) else trade_data.get('exit_time', datetime.utcnow().isoformat()),
                'exit_price': float(trade_data.get('exit_price', 0.0)),
                'exit_reason': trade_data.get('exit_reason', 'UNKNOWN'),
                'pnl': float(trade_data.get('pnl', 0.0)),
                'pnl_percent': float(trade_data.get('pnl_percent', 0.0)),
                'holding_duration_minutes': float(trade_data.get('holding_duration_minutes', 0.0)),
                'is_virtual': is_virtual,
                
                # 從開倉到平倉的完整 K 線歷史
                'kline_history': kline_history,
                
                # 平倉時的技術指標
                'exit_features': {
                    'macd': self._safe_float(exit_metadata.get('macd')),
                    'macd_signal': self._safe_float(exit_metadata.get('macd_signal')),
                    'ema_9': self._safe_float(exit_metadata.get('ema_9')),
                    'ema_21': self._safe_float(exit_metadata.get('ema_21')),
                    'ema_50': self._safe_float(exit_metadata.get('ema_50')),
                    'ema_200': self._safe_float(exit_metadata.get('ema_200')),
                    'atr': self._safe_float(exit_metadata.get('atr')),
                    'rsi': self._safe_float(exit_metadata.get('rsi')),
                },
                
                # 交易標籤（供 XGBoost 學習）
                'ml_label': {
                    'outcome': 'WIN' if trade_data.get('pnl', 0.0) > 0 else 'LOSS',
                    'pnl_percent': float(trade_data.get('pnl_percent', 0.0)),
                    'max_favorable_excursion': float(mfe),
                    'max_adverse_excursion': float(mae),
                    'hit_take_profit': 'PROFIT' in trade_data.get('exit_reason', '').upper() or 'TARGET' in trade_data.get('exit_reason', '').upper(),
                    'hit_stop_loss': 'STOP' in trade_data.get('exit_reason', '').upper() or 'LOSS' in trade_data.get('exit_reason', '').upper()
                }
            }
            
            # 更新統計
            self.stats['total_exits'] += 1
            
            # 如果有對應的開倉記錄，合併生成完整的 ML 訓練樣本
            if entry_record:
                ml_sample = self._merge_entry_exit_data(entry_record, exit_record)
                self.ml_data.append(ml_sample)
                
                # 從暫存中移除
                del self.pending_entries[trade_id]
                
                # 更新統計
                self.stats['complete_pairs'] += 1
                self.stats['incomplete_pairs'] = len(self.pending_entries)
                
                # 立即持久化 pending_entries（刪除已完成的條目）
                self.save_pending_entries()
                
                logger.info(
                    f"✅ Logged position exit and created ML sample: {trade_id} "
                    f"(PnL: {trade_data.get('pnl_percent', 0):.2f}%, MFE: {mfe:.2f}%, MAE: {mae:.2f}%)"
                )
                
                # 檢查是否需要 flush
                self._check_and_flush()
            else:
                logger.warning(f"⚠️  No entry record for {trade_id}, ML sample not created - incomplete pair!")
            
        except Exception as e:
            logger.error(f"Error logging position exit: {e}")
            logger.exception(e)
    
    def _check_and_flush(self):
        """檢查並在需要時執行 flush"""
        # 計數觸發
        if self.stats['total_entries'] % self.buffer_size == 0:
            logger.debug(f"Count-based flush triggered (every {self.buffer_size} entries)")
            self.flush()
    
    def log_trade(self, trade_data: Dict):
        """
        記錄交易（保持向後兼容）
        
        這個方法保持原有的簡單記錄功能，用於快速記錄基本交易信息
        """
        trade_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': trade_data.get('symbol'),
            'type': trade_data.get('type'),
            'side': trade_data.get('side'),
            'entry_price': trade_data.get('entry_price'),
            'exit_price': trade_data.get('exit_price'),
            'quantity': trade_data.get('quantity'),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit': trade_data.get('take_profit'),
            'pnl': trade_data.get('pnl'),
            'pnl_percent': trade_data.get('pnl_percent'),
            'reason': trade_data.get('reason'),
            'strategy': trade_data.get('strategy')
        }
        
        self.trades.append(trade_entry)
        self.unsaved_count += 1
        
        if self.unsaved_count >= self.buffer_size or trade_data.get('type') == 'CLOSE':
            self.save_trades()
        
        logger.info(f"Logged trade: {trade_data.get('symbol')} {trade_data.get('type')}")
    
    def check_incomplete_pairs(self) -> List[Dict]:
        """
        檢查未閉合的交易對
        
        Returns:
            未閉合的交易列表
        """
        incomplete = []
        
        for trade_id, entry_record in self.pending_entries.items():
            incomplete.append({
                'trade_id': trade_id,
                'symbol': entry_record.get('symbol'),
                'side': entry_record.get('side'),
                'entry_price': entry_record.get('entry_price'),
                'timestamp': entry_record.get('timestamp'),
                'age_hours': (datetime.utcnow() - datetime.fromisoformat(entry_record.get('timestamp'))).total_seconds() / 3600
            })
        
        if incomplete:
            logger.warning(f"⚠️  Found {len(incomplete)} incomplete trade pairs:")
            for item in incomplete:
                logger.warning(
                    f"  - {item['trade_id']}: {item['symbol']} {item['side']} @ {item['entry_price']}, "
                    f"age: {item['age_hours']:.1f}h"
                )
        
        return incomplete
    
    def _generate_trade_id(self, symbol: str, timestamp: datetime) -> str:
        """
        生成唯一的交易ID
        
        Args:
            symbol: 交易對
            timestamp: 時間戳
            
        Returns:
            唯一的交易ID（格式：SYMBOL_YYYYMMDD_HHMMSS）
        """
        return f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    def _fetch_klines_snapshot(self, binance_client, symbol: str, timeframe: str, limit: int = 20) -> List[Dict]:
        """
        獲取 K 線快照（最近 N 根 K 線）
        
        Args:
            binance_client: Binance 客戶端
            symbol: 交易對
            timeframe: 時間框架
            limit: K 線數量
            
        Returns:
            K 線列表
        """
        try:
            klines_df = binance_client.get_klines(symbol, timeframe, limit=limit)
            
            if klines_df is None or klines_df.empty:
                return []
            
            # 轉換為簡化的字典格式
            klines = []
            for _, row in klines_df.iterrows():
                klines.append({
                    'time': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            
            return klines
            
        except Exception as e:
            logger.error(f"Error fetching klines snapshot: {e}")
            return []
    
    def _fetch_kline_history(self, binance_client, symbol: str, start_time: datetime, end_time: datetime, timeframe: str) -> List[Dict]:
        """
        獲取從開倉到平倉的 K 線歷史
        
        Args:
            binance_client: Binance 客戶端
            symbol: 交易對
            start_time: 開始時間
            end_time: 結束時間
            timeframe: 時間框架
            
        Returns:
            K 線列表
        """
        try:
            # 計算需要多少根 K 線
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            # 根據時間框架計算需要的 K 線數量
            timeframe_minutes = {
                '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '2h': 120, '4h': 240, '1d': 1440
            }
            
            interval_minutes = timeframe_minutes.get(timeframe, 1)
            limit = int(duration_minutes / interval_minutes) + 10  # 加 10 根作為緩衝
            limit = min(limit, 1000)  # Binance API 限制
            
            # 獲取 K 線數據
            klines_df = binance_client.get_klines(symbol, timeframe, limit=limit)
            
            if klines_df is None or klines_df.empty:
                return []
            
            # 過濾時間範圍內的 K 線
            klines = []
            for _, row in klines_df.iterrows():
                kline_time = row['timestamp']
                
                # 確保時間在範圍內
                if kline_time >= start_time and kline_time <= end_time:
                    klines.append({
                        'time': kline_time.isoformat() if hasattr(kline_time, 'isoformat') else str(kline_time),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume'])
                    })
            
            return klines
            
        except Exception as e:
            logger.error(f"Error fetching kline history: {e}")
            return []
    
    def _calculate_mfe_mae(self, kline_history: List[Dict], entry_price: float, side: str) -> tuple:
        """
        計算最大有利波動（MFE）和最大不利波動（MAE）
        
        Args:
            kline_history: K 線歷史
            entry_price: 入場價格
            side: 'BUY' or 'SELL'
            
        Returns:
            (mfe_percent, mae_percent)
        """
        # 添加完整的保護檢查
        if not kline_history:
            logger.debug("Empty kline_history, returning (0.0, 0.0) for MFE/MAE")
            return (0.0, 0.0)
        
        if not entry_price or entry_price == 0:
            logger.warning(f"Invalid entry_price: {entry_price}, returning (0.0, 0.0) for MFE/MAE")
            return (0.0, 0.0)
        
        if not side or side not in ['BUY', 'SELL']:
            logger.warning(f"Invalid entry_side: {side}, returning (0.0, 0.0) for MFE/MAE")
            return (0.0, 0.0)
        
        try:
            max_favorable = 0.0
            max_adverse = 0.0
            
            for kline in kline_history:
                try:
                    high = float(kline.get('high', 0))
                    low = float(kline.get('low', 0))
                    
                    # 跳過無效的 K 線
                    if high == 0 or low == 0:
                        continue
                    
                    if side == 'BUY':
                        # 做多：high 是有利方向，low 是不利方向
                        favorable = (high - entry_price) / entry_price * 100 if entry_price > 0 else 0.0
                        adverse = (low - entry_price) / entry_price * 100 if entry_price > 0 else 0.0
                    else:  # SELL
                        # 做空：low 是有利方向，high 是不利方向
                        favorable = (entry_price - low) / entry_price * 100 if entry_price > 0 else 0.0
                        adverse = (entry_price - high) / entry_price * 100 if entry_price > 0 else 0.0
                    
                    max_favorable = max(max_favorable, favorable)
                    max_adverse = min(max_adverse, adverse)
                    
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Skipping invalid kline in MFE/MAE calculation: {e}")
                    continue
            
            return (max_favorable, max_adverse)
            
        except Exception as e:
            logger.error(f"Error calculating MFE/MAE: {e}")
            return (0.0, 0.0)
    
    def _merge_entry_exit_data(self, entry_data: Dict, exit_data: Dict) -> Dict:
        """
        合併開倉和平倉數據成完整的 ML 訓練樣本
        
        Args:
            entry_data: 開倉數據
            exit_data: 平倉數據
            
        Returns:
            完整的 ML 訓練樣本
        """
        return {
            **entry_data,
            'exit': exit_data,
            'ml_ready': True,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _sanitize_metadata(self, metadata):
        """
        清理 metadata，確保可以序列化為 JSON
        
        處理各種不能直接序列化為 JSON 的對象：
        - NumPy 標量（np.int64, np.float64 等）→ Python float/int
        - pandas Timestamps → ISO 字符串
        - NaN/inf → None
        - NumPy 數組、pandas Series → Python 列表
        - 自定義對象 → 字符串表示
        
        Args:
            metadata: 要清理的數據（可以是任何類型）
            
        Returns:
            可以序列化為 JSON 的數據
        """
        try:
            import numpy as np
            import pandas as pd
            
            # 遞歸處理字典
            if isinstance(metadata, dict):
                return {k: self._sanitize_metadata(v) for k, v in metadata.items()}
            
            # 遞歸處理列表和元組
            elif isinstance(metadata, (list, tuple)):
                return [self._sanitize_metadata(item) for item in metadata]
            
            # NumPy 整數類型
            elif isinstance(metadata, np.integer):
                return int(metadata)
            
            # NumPy 浮點類型（檢查 NaN）
            elif isinstance(metadata, np.floating):
                if np.isnan(metadata):
                    return None
                return float(metadata)
            
            # NumPy 數組和 pandas Series
            elif isinstance(metadata, (np.ndarray, pd.Series)):
                return [self._sanitize_metadata(x) for x in metadata.tolist()]
            
            # pandas Timestamp
            elif isinstance(metadata, pd.Timestamp):
                return metadata.isoformat()
            
            # Python float（檢查 NaN 和 inf）
            elif isinstance(metadata, float):
                if np.isnan(metadata) or np.isinf(metadata):
                    return None
                return metadata
            
            # Python int
            elif isinstance(metadata, int):
                return metadata
            
            # 字符串、布爾值、None
            elif isinstance(metadata, (str, bool, type(None))):
                return metadata
            
            # datetime 對象
            elif isinstance(metadata, datetime):
                return metadata.isoformat()
            
            # 其他不可序列化的對象 → 轉為字符串
            else:
                logger.debug(f"Converting unknown type {type(metadata)} to string: {metadata}")
                return str(metadata)
                
        except Exception as e:
            logger.warning(f"Error sanitizing metadata: {e}, returning string representation")
            return str(metadata)
    
    def _safe_float(self, value, default=None) -> Optional[float]:
        """
        安全地轉換為 float，處理 NaN/None 值
        
        Args:
            value: 要轉換的值
            default: 默認值（如果轉換失敗）
            
        Returns:
            float 或 None
        """
        try:
            if value is None:
                return default
            
            f = float(value)
            
            # 檢查是否為 NaN
            if f != f:  # NaN 不等於自己
                return default
            
            return f
        except (ValueError, TypeError):
            return default
    
    def _calculate_distance_from_ema200(self, current_price, ema_200) -> Optional[float]:
        """計算價格與 EMA200 的距離"""
        if current_price is None or ema_200 is None:
            return None
        
        try:
            return float(current_price) - float(ema_200)
        except (ValueError, TypeError):
            return None
    
    def _calculate_distance_from_ema200_pct(self, current_price, ema_200) -> Optional[float]:
        """計算價格與 EMA200 的距離百分比"""
        if current_price is None or ema_200 is None or float(ema_200) == 0:
            return None
        
        try:
            return (float(current_price) - float(ema_200)) / float(ema_200) * 100
        except (ValueError, TypeError, ZeroDivisionError):
            return None
    
    def flush(self):
        """強制保存所有未保存的數據"""
        logger.info("🔄 Flushing all data to disk...")
        
        # 檢查未閉合的交易
        incomplete = self.check_incomplete_pairs()
        if incomplete:
            logger.warning(f"⚠️  Warning: {len(incomplete)} incomplete trade pairs will be persisted")
        
        # 保存所有數據
        if self.unsaved_count > 0:
            self.save_trades()
        
        if len(self.ml_data) > 0:
            self.save_ml_data()
        
        # 保存待處理的開倉記錄
        self.save_pending_entries()
        
        # 更新統計
        self.stats['total_flushes'] += 1
        self.stats['last_flush_timestamp'] = datetime.utcnow().isoformat()
        self.last_flush_time = time.time()
        
        logger.info(
            f"✅ Flush complete: "
            f"trades={len(self.trades)}, "
            f"ml_samples={len(self.ml_data)}, "
            f"pending_entries={len(self.pending_entries)}"
        )
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """獲取最近的交易"""
        return self.trades[-limit:]
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict]:
        """獲取特定交易對的交易記錄"""
        return [trade for trade in self.trades if trade['symbol'] == symbol]
    
    def get_statistics(self) -> Dict:
        """
        獲取完整的統計信息
        
        Returns:
            統計信息字典，包含：
            - 總樣本數
            - 完整/不完整交易對數量
            - 特徵覆蓋率
            - ML 訓練數據統計
        """
        ml_stats = self.get_ml_statistics()
        
        return {
            'data_integrity': {
                'total_entries': self.stats['total_entries'],
                'total_exits': self.stats['total_exits'],
                'complete_pairs': self.stats['complete_pairs'],
                'incomplete_pairs': self.stats['incomplete_pairs'],
                'pair_completion_rate': (self.stats['complete_pairs'] / self.stats['total_entries'] * 100) if self.stats['total_entries'] > 0 else 0
            },
            'ml_training_data': ml_stats,
            'feature_coverage': self.stats.get('feature_coverage', {}),
            'data_quality': {
                'validation_errors': self.stats['validation_errors'],
                'total_flushes': self.stats['total_flushes'],
                'last_flush': self.stats.get('last_flush_timestamp', 'Never')
            }
        }
    
    def get_ml_statistics(self) -> Dict:
        """
        獲取 ML 訓練數據統計
        
        Returns:
            統計信息字典
        """
        if not self.ml_data:
            return {
                'total_samples': 0,
                'winning_samples': 0,
                'losing_samples': 0,
                'win_rate': 0,
                'avg_mfe': 0,
                'avg_mae': 0,
                'avg_holding_time': 0
            }
        
        winning = sum(1 for sample in self.ml_data if sample['exit']['ml_label']['outcome'] == 'WIN')
        losing = len(self.ml_data) - winning
        
        avg_mfe = sum(sample['exit']['ml_label']['max_favorable_excursion'] for sample in self.ml_data) / len(self.ml_data)
        avg_mae = sum(sample['exit']['ml_label']['max_adverse_excursion'] for sample in self.ml_data) / len(self.ml_data)
        avg_holding = sum(sample['exit']['holding_duration_minutes'] for sample in self.ml_data) / len(self.ml_data)
        
        return {
            'total_samples': len(self.ml_data),
            'winning_samples': winning,
            'losing_samples': losing,
            'win_rate': (winning / len(self.ml_data) * 100) if len(self.ml_data) > 0 else 0,
            'avg_mfe': avg_mfe,
            'avg_mae': avg_mae,
            'avg_holding_time': avg_holding
        }
    
    def calculate_statistics(self) -> Dict:
        """計算交易統計數據（保持向後兼容）"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'average_profit': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        total_trades = len(self.trades)
        winning_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) > 0)
        losing_trades = sum(1 for trade in self.trades if trade.get('pnl', 0) < 0)
        
        total_profit = sum(trade.get('pnl', 0) for trade in self.trades)
        average_profit = total_profit / total_trades if total_trades > 0 else 0
        
        pnls = [trade.get('pnl', 0) for trade in self.trades]
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'average_profit': average_profit,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }

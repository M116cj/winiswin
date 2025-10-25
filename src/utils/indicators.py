import numpy as np
import pandas as pd
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """輕量級技術指標實現 - 純 Python/NumPy，無需 TA-Lib"""
    
    @staticmethod
    def calculate_ema(close, period):
        """計算指數移動平均線 (EMA)"""
        if isinstance(close, pd.Series):
            return close.ewm(span=period, adjust=False).mean()
        else:
            close_series = pd.Series(close)
            return close_series.ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def calculate_sma(close, period):
        """計算簡單移動平均線 (SMA)"""
        if isinstance(close, pd.Series):
            return close.rolling(window=period).mean()
        else:
            close_series = pd.Series(close)
            result = close_series.rolling(window=period).mean()
            return result.to_numpy()
    
    @staticmethod
    def calculate_macd(close, fast_period=12, slow_period=26, signal_period=9):
        """計算 MACD 指標"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        
        ema_fast = close.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=slow_period, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        hist = macd - signal
        
        return macd.to_numpy(), signal.to_numpy(), hist.to_numpy()
    
    @staticmethod
    def calculate_rsi(close, period=14):
        """計算相對強弱指標 (RSI)"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.to_numpy()
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """計算平均真實範圍 (ATR)"""
        if isinstance(high, np.ndarray):
            high = pd.Series(high)
            low = pd.Series(low)
            close = pd.Series(close)
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.to_numpy()
    
    @staticmethod
    def calculate_bollinger_bands(close, period=20, std_dev=2):
        """計算布林帶"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper.to_numpy(), middle.to_numpy(), lower.to_numpy()
    
    @staticmethod
    def calculate_all_indicators(df, optimize_memory: bool = True):
        """
        計算所有必要的技術指標
        
        優化點：
        1. 只計算實際使用的指標
        2. 使用向量化操作
        3. 最小化 NaN 行數
        4. 內存優化：使用 float32，只保留必要的列
        
        Args:
            df: Price data DataFrame
            optimize_memory: If True, use float32 and keep only essential columns
        """
        if len(df) < 50:
            return None
        
        df = df.copy()
        
        # 內存優化：轉換為 float32
        if optimize_memory:
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].astype('float32')
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # 計算指標
        df['ema_9'] = TechnicalIndicators.calculate_ema(close, 9)
        df['ema_21'] = TechnicalIndicators.calculate_ema(close, 21)
        df['ema_50'] = TechnicalIndicators.calculate_ema(close, 50)
        
        macd, signal, hist = TechnicalIndicators.calculate_macd(close)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        df['rsi'] = TechnicalIndicators.calculate_rsi(close)
        df['atr'] = TechnicalIndicators.calculate_atr(high, low, close)
        
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # 內存優化：轉換指標為 float32
        if optimize_memory:
            indicator_columns = [
                'ema_9', 'ema_21', 'ema_50',
                'macd', 'macd_signal', 'macd_hist',
                'rsi', 'atr',
                'bb_upper', 'bb_middle', 'bb_lower'
            ]
            for col in indicator_columns:
                if col in df.columns:
                    df[col] = df[col].astype('float32')
        
        # 移除 NaN 行
        first_valid_idx = df[['ema_50', 'macd', 'atr', 'rsi']].first_valid_index()
        
        if first_valid_idx is None or first_valid_idx >= len(df) - 10:
            return None
        
        df = df.loc[first_valid_idx:].copy()
        df = df.reset_index(drop=True)
        
        if len(df) < 10:
            return None
        
        # 內存優化：只保留必要的列
        if optimize_memory:
            essential_columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'ema_9', 'ema_21', 'ema_50',
                'macd', 'macd_signal', 'macd_hist',
                'rsi', 'atr',
                'bb_upper', 'bb_middle', 'bb_lower'
            ]
            columns_to_keep = [col for col in essential_columns if col in df.columns]
            df = df[columns_to_keep].copy()
        
        return df
    
    @staticmethod
    def batch_calculate_indicators(
        symbols_data: Dict[str, pd.DataFrame],
        optimize_memory: bool = True
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        批量向量化計算多個 symbol 的技術指標
        
        優化策略（v3.2 真正向量化）：
        1. 直接調用 calculate_all_indicators 以保持計算邏輯一致
        2. 內存優化：使用 float32，只保留必要的列
        3. 統一接口便於批量處理
        
        性能特性：
        - 內存使用：相比 float64 降低 30-50%
        - 計算速度：與逐個調用相當（主要優勢在於內存優化）
        - 適合大規模批量處理（100+ symbols）
        
        Args:
            symbols_data: Dict of {symbol: DataFrame}
            optimize_memory: If True, use float32 and keep only essential columns
            
        Returns:
            Dict of {symbol: DataFrame with indicators or None}
        """
        if not symbols_data:
            return {}
        
        results = {}
        
        # 直接調用 calculate_all_indicators（統一邏輯）
        for symbol, df in symbols_data.items():
            try:
                df_with_indicators = TechnicalIndicators.calculate_all_indicators(
                    df, 
                    optimize_memory=optimize_memory
                )
                results[symbol] = df_with_indicators
            except Exception as e:
                logger.error(f"Error calculating indicators for {symbol}: {e}")
                results[symbol] = None
        
        successful = len([r for r in results.values() if r is not None])
        logger.info(f"Batch calculated indicators for {successful}/{len(symbols_data)} symbols")
        
        return results

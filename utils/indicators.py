import numpy as np
import pandas as pd

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
            return close_series.rolling(window=period).mean().values
    
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
        
        return macd.values, signal.values, hist.values
    
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
        
        return rsi.values
    
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
        
        return atr.values
    
    @staticmethod
    def calculate_bollinger_bands(close, period=20, std_dev=2):
        """計算布林帶"""
        if isinstance(close, np.ndarray):
            close = pd.Series(close)
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper.values, middle.values, lower.values
    
    @staticmethod
    def calculate_all_indicators(df):
        """
        計算所有必要的技術指標
        
        優化點：
        1. 只計算實際使用的指標
        2. 使用向量化操作
        3. 最小化 NaN 行數
        """
        if len(df) < 50:
            return None
        
        df = df.copy()
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
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
        
        first_valid_idx = df[['ema_50', 'macd', 'atr', 'rsi']].first_valid_index()
        
        if first_valid_idx is None or first_valid_idx >= len(df) - 10:
            return None
        
        df = df.loc[first_valid_idx:].copy()
        df = df.reset_index(drop=True)
        
        if len(df) < 10:
            return None
        
        return df

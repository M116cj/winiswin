import numpy as np
import pandas as pd
import talib

class TechnicalIndicators:
    @staticmethod
    def calculate_macd(close, fastperiod=12, slowperiod=26, signalperiod=9):
        macd, signal, hist = talib.MACD(close, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return macd, signal, hist
    
    @staticmethod
    def calculate_bollinger_bands(close, timeperiod=20, nbdevup=2, nbdevdn=2):
        upper, middle, lower = talib.BBANDS(close, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn)
        return upper, middle, lower
    
    @staticmethod
    def calculate_ema(close, timeperiod=20):
        return talib.EMA(close, timeperiod=timeperiod)
    
    @staticmethod
    def calculate_sma(close, timeperiod=20):
        return talib.SMA(close, timeperiod=timeperiod)
    
    @staticmethod
    def calculate_atr(high, low, close, timeperiod=14):
        return talib.ATR(high, low, close, timeperiod=timeperiod)
    
    @staticmethod
    def calculate_rsi(close, timeperiod=14):
        return talib.RSI(close, timeperiod=timeperiod)
    
    @staticmethod
    def calculate_all_indicators(df):
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        df['ema_9'] = TechnicalIndicators.calculate_ema(close, 9)
        df['ema_21'] = TechnicalIndicators.calculate_ema(close, 21)
        df['ema_50'] = TechnicalIndicators.calculate_ema(close, 50)
        df['sma_200'] = TechnicalIndicators.calculate_sma(close, 200)
        
        macd, signal, hist = TechnicalIndicators.calculate_macd(close)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_hist'] = hist
        
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        df['atr'] = TechnicalIndicators.calculate_atr(high, low, close)
        df['rsi'] = TechnicalIndicators.calculate_rsi(close)
        
        return df

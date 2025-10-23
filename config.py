import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
    DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID', '')
    
    MAX_POSITION_SIZE_PERCENT = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '0.5'))
    RISK_PER_TRADE_PERCENT = float(os.getenv('RISK_PER_TRADE_PERCENT', '0.3'))
    DEFAULT_LEVERAGE = float(os.getenv('DEFAULT_LEVERAGE', '1.0'))
    ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
    
    # 交易對選擇模式（預設：全量648個）
    SYMBOL_MODE = os.getenv('SYMBOL_MODE', 'all').lower()
    MAX_SYMBOLS = int(os.getenv('MAX_SYMBOLS', '648'))
    
    # 倉位管理（資金拆成3等份，最多同時持有3個倉位）
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))
    CAPITAL_PER_POSITION_PERCENT = 100.0 / MAX_CONCURRENT_POSITIONS  # 33.33% per position
    
    # 靜態交易對列表（備用）
    STATIC_SYMBOLS = [
        'BTCUSDT',   # Bitcoin
        'ETHUSDT',   # Ethereum
        'BNBUSDT',   # Binance Coin
        'SOLUSDT',   # Solana
        'XRPUSDT',   # Ripple
    ]
    
    # SYMBOLS 將在運行時動態設置
    SYMBOLS = STATIC_SYMBOLS
    TIMEFRAME = '15m'  # 15分鐘K線
    
    MODEL_RETRAIN_INTERVAL = 3600
    LOOKBACK_PERIODS = 100
    
    STOP_LOSS_ATR_MULTIPLIER = 2.0
    TAKE_PROFIT_ATR_MULTIPLIER = 3.0
    
    LOG_FILE = 'trading_bot.log'
    TRADES_FILE = 'trades.json'

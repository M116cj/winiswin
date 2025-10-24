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
    DEFAULT_LEVERAGE = float(os.getenv('DEFAULT_LEVERAGE', '3.0'))
    ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
    
    # 訂單執行方式
    ORDER_TYPE = os.getenv('ORDER_TYPE', 'MARKET')  # 'MARKET' = 市價單（立即成交），'LIMIT' = 限價單（掛單等待）
    LIMIT_ORDER_OFFSET_PERCENT = float(os.getenv('LIMIT_ORDER_OFFSET_PERCENT', '0.1'))  # 限價單價格偏移（0.1% = 稍微更好的價格）
    
    # 智能槓桿調整機制
    ENABLE_DYNAMIC_LEVERAGE = os.getenv('ENABLE_DYNAMIC_LEVERAGE', 'true').lower() == 'true'
    MIN_LEVERAGE = float(os.getenv('MIN_LEVERAGE', '3.0'))  # 最小槓桿
    MAX_LEVERAGE = float(os.getenv('MAX_LEVERAGE', '20.0'))  # 最大槓桿
    
    # 槓桿調整參數
    HIGH_CONFIDENCE_THRESHOLD = 90.0  # 高信心度門檻
    MEDIUM_CONFIDENCE_THRESHOLD = 80.0  # 中信心度門檻
    ULTRA_HIGH_CONFIDENCE_THRESHOLD = 100.0  # 超高信心度門檻
    LOW_VOLATILITY_ATR_THRESHOLD = 0.02  # 低波動性門檻（2%）
    HIGH_VOLATILITY_ATR_THRESHOLD = 0.05  # 高波動性門檻（5%）
    
    # 交易對選擇模式（預設：全量648個）
    SYMBOL_MODE = os.getenv('SYMBOL_MODE', 'all').lower()
    MAX_SYMBOLS = int(os.getenv('MAX_SYMBOLS', '648'))
    
    # 倉位管理（資金拆成3等份，最多同時持有3個倉位）
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))
    CAPITAL_PER_POSITION_PERCENT = 100.0 / MAX_CONCURRENT_POSITIONS  # 33.33% per position
    
    # 保證金配置（單個倉位的保證金佔總資金比例）
    MARGIN_MIN_PERCENT = float(os.getenv('MARGIN_MIN_PERCENT', '3.0'))   # 最小保證金 3%
    MARGIN_MAX_PERCENT = float(os.getenv('MARGIN_MAX_PERCENT', '13.0'))  # 最大保證金 13%
    
    # 槓桿計算模式
    LEVERAGE_MODE = os.getenv('LEVERAGE_MODE', 'win_rate')  # 'win_rate' = 勝率模式, 'confidence' = 信心度模式
    
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
    TIMEFRAME = '1m'  # 1分鐘K線（高頻交易）
    
    # 多時間框架配置（Multi-Timeframe Strategy）
    TREND_TIMEFRAME = '15m'  # 15分鐘K線用於判斷趨勢方向
    EXECUTION_TIMEFRAME = '1m'  # 1分鐘K線用於執行交易
    
    # 動態風險回報比配置（根據信心度調整）
    MIN_RISK_REWARD_RATIO = 1.0  # 最小風險回報比（低信心度 70-80%）
    MAX_RISK_REWARD_RATIO = 2.0  # 最大風險回報比（高信心度 90%+）
    MEDIUM_RISK_REWARD_RATIO = 1.5  # 中等風險回報比（中信心度 80-90%）
    
    MODEL_RETRAIN_INTERVAL = 3600
    LOOKBACK_PERIODS = 100
    
    # 止損/止盈策略（基於損益平衡價格）
    RISK_REWARD_RATIO = float(os.getenv('RISK_REWARD_RATIO', '2.0'))  # 風險收益比 1:1 或 1:2
    STOP_LOSS_ATR_MULTIPLIER = 2.0
    TAKE_PROFIT_ATR_MULTIPLIER = 3.0
    
    # 交易手續費（Binance 期貨）
    MAKER_FEE_RATE = float(os.getenv('MAKER_FEE_RATE', '0.0002'))  # 0.02% 掛單手續費
    TAKER_FEE_RATE = float(os.getenv('TAKER_FEE_RATE', '0.0004'))  # 0.04% 吃單手續費
    
    # 高頻交易參數
    USE_BREAKEVEN_STOPS = os.getenv('USE_BREAKEVEN_STOPS', 'true').lower() == 'true'  # 使用損益平衡止損
    
    LOG_FILE = 'trading_bot.log'
    TRADES_FILE = 'trades.json'

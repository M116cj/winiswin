import json
import os
from datetime import datetime
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class TradeLogger:
    def __init__(self, log_file='trades.json'):
        self.log_file = log_file
        self.trades = self.load_trades()
    
    def load_trades(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading trades: {e}")
                return []
        return []
    
    def save_trades(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
            logger.info(f"Saved {len(self.trades)} trades to {self.log_file}")
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
    
    def log_trade(self, trade_data):
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
        self.save_trades()
        logger.info(f"Logged trade: {trade_data.get('symbol')} {trade_data.get('type')}")
    
    def get_recent_trades(self, limit=10):
        return self.trades[-limit:]
    
    def get_trades_by_symbol(self, symbol):
        return [trade for trade in self.trades if trade['symbol'] == symbol]
    
    def calculate_statistics(self):
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

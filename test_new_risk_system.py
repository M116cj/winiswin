"""
測試新的保證金和槓桿系統
展示 3%-13% 保證金配置和基於勝率的槓桿計算
"""

from risk_manager import RiskManager
from config import Config

def test_margin_and_leverage():
    print("=" * 70)
    print("測試新的保證金和槓桿系統")
    print("=" * 70)
    
    # 範例：總資金 $40
    account_balance = 40.0
    rm = RiskManager(account_balance=account_balance)
    
    print(f"\n💰 帳戶總資金: ${account_balance:.2f} USDT")
    print(f"📍 最大同時倉位: {Config.MAX_CONCURRENT_POSITIONS} 個")
    print(f"📊 保證金範圍: {Config.MARGIN_MIN_PERCENT}%-{Config.MARGIN_MAX_PERCENT}%")
    print(f"🎯 槓桿範圍: {Config.MIN_LEVERAGE}x-{Config.MAX_LEVERAGE}x")
    print(f"⚙️  槓桿模式: {Config.LEVERAGE_MODE}")
    
    print("\n" + "=" * 70)
    print("情境 1: 無交易記錄，低信心度信號 (70%)")
    print("=" * 70)
    
    confidence_1 = 70.0
    margin_percent_1 = rm.calculate_margin_percent(confidence_1)
    leverage_1 = rm.calculate_win_rate_based_leverage()
    
    position_params_1 = rm.calculate_position_size(
        symbol="BTCUSDT",
        entry_price=50000.0,
        stop_loss_price=49500.0,
        confidence=confidence_1,
        leverage=leverage_1
    )
    
    print(f"\n結果:")
    print(f"  信心度: {confidence_1}%")
    print(f"  保證金比例: {margin_percent_1:.2f}% → 保證金: ${position_params_1['margin']:.2f}")
    print(f"  槓桿倍數: {leverage_1:.2f}x")
    print(f"  倉位價值: ${position_params_1['position_value']:.2f}")
    print(f"  數量: {position_params_1['quantity']:.6f} BTC")
    print(f"  風險金額: ${position_params_1['risk_amount']:.2f}")
    
    print("\n" + "=" * 70)
    print("情境 2: 模擬交易記錄，中信心度信號 (85%)")
    print("=" * 70)
    
    # 模擬一些交易記錄：12 筆交易，7 勝 5 負 (勝率 58.33%)
    rm.total_trades = 12
    rm.winning_trades = 7
    rm.losing_trades = 5
    
    confidence_2 = 85.0
    margin_percent_2 = rm.calculate_margin_percent(confidence_2)
    leverage_2 = rm.calculate_win_rate_based_leverage()
    
    position_params_2 = rm.calculate_position_size(
        symbol="ETHUSDT",
        entry_price=3000.0,
        stop_loss_price=2950.0,
        confidence=confidence_2,
        leverage=leverage_2
    )
    
    print(f"\n交易記錄: {rm.total_trades} 筆 ({rm.winning_trades} 勝 {rm.losing_trades} 負)")
    print(f"勝率: {rm.get_win_rate():.2f}%")
    print(f"\n結果:")
    print(f"  信心度: {confidence_2}%")
    print(f"  保證金比例: {margin_percent_2:.2f}% → 保證金: ${position_params_2['margin']:.2f}")
    print(f"  槓桿倍數: {leverage_2:.2f}x (基於勝率)")
    print(f"  倉位價值: ${position_params_2['position_value']:.2f}")
    print(f"  數量: {position_params_2['quantity']:.6f} ETH")
    print(f"  風險金額: ${position_params_2['risk_amount']:.2f}")
    
    print("\n" + "=" * 70)
    print("情境 3: 高勝率，高信心度信號 (95%)")
    print("=" * 70)
    
    # 模擬更多交易記錄：30 筆交易，20 勝 10 負 (勝率 66.67%)
    rm.total_trades = 30
    rm.winning_trades = 20
    rm.losing_trades = 10
    
    confidence_3 = 95.0
    margin_percent_3 = rm.calculate_margin_percent(confidence_3)
    leverage_3 = rm.calculate_win_rate_based_leverage()
    
    position_params_3 = rm.calculate_position_size(
        symbol="BNBUSDT",
        entry_price=600.0,
        stop_loss_price=590.0,
        confidence=confidence_3,
        leverage=leverage_3
    )
    
    print(f"\n交易記錄: {rm.total_trades} 筆 ({rm.winning_trades} 勝 {rm.losing_trades} 負)")
    print(f"勝率: {rm.get_win_rate():.2f}%")
    print(f"\n結果:")
    print(f"  信心度: {confidence_3}%")
    print(f"  保證金比例: {margin_percent_3:.2f}% → 保證金: ${position_params_3['margin']:.2f}")
    print(f"  槓桿倍數: {leverage_3:.2f}x (基於勝率)")
    print(f"  倉位價值: ${position_params_3['position_value']:.2f}")
    print(f"  數量: {position_params_3['quantity']:.6f} BNB")
    print(f"  風險金額: ${position_params_3['risk_amount']:.2f}")
    
    print("\n" + "=" * 70)
    print("總結：同時持有3個倉位的情況")
    print("=" * 70)
    
    total_margin = position_params_1['margin'] + position_params_2['margin'] + position_params_3['margin']
    total_position_value = (
        position_params_1['position_value'] + 
        position_params_2['position_value'] + 
        position_params_3['position_value']
    )
    
    print(f"\n  總保證金: ${total_margin:.2f} ({total_margin/account_balance*100:.1f}% of total capital)")
    print(f"  總倉位價值: ${total_position_value:.2f}")
    print(f"  總風險: ${total_margin:.2f} (最大可能損失)")
    print(f"  剩餘資金: ${account_balance - total_margin:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ 測試完成")
    print("=" * 70)

if __name__ == "__main__":
    test_margin_and_leverage()

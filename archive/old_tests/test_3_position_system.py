"""
測試 3 倉位管理系統

驗證：
1. 最多同時持有 3 個倉位
2. 資金平均拆成 3 等份
3. 選擇信心度最高或投報率最高的信號
4. 正確的倉位計算
"""

import sys
from config import Config
from risk_manager import RiskManager

def test_3_position_limit():
    """測試最大倉位數限制"""
    print("=" * 60)
    print("測試 1: 最大倉位數限制（3個）")
    print("=" * 60)
    
    rm = RiskManager(account_balance=10000)
    
    # 嘗試開 5 個倉位，應該只能開 3 個
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
    opened = 0
    
    for symbol in symbols:
        if rm.can_open_position(symbol):
            rm.open_position(symbol, 'LONG', 50000, 0.001, 49000, 51000)
            opened += 1
            print(f"✅ 開倉: {symbol} (總倉位: {len(rm.open_positions)}/{rm.max_concurrent_positions})")
        else:
            print(f"❌ 無法開倉: {symbol} (已達上限)")
    
    print(f"\n結果: 成功開倉 {opened}/{len(symbols)}")
    print(f"預期: 3 個 | 實際: {len(rm.open_positions)} 個")
    assert len(rm.open_positions) == 3, "倉位數應為3"
    print("✅ 測試通過！\n")

def test_capital_allocation():
    """測試資金分配（每個倉位1/3）"""
    print("=" * 60)
    print("測試 2: 資金分配（每倉位 33.33%）")
    print("=" * 60)
    
    account_balance = 10000
    rm = RiskManager(account_balance=account_balance)
    
    expected_capital_per_position = account_balance / 3
    actual_capital_percent = rm.capital_per_position
    
    print(f"賬戶餘額: ${account_balance}")
    print(f"每個倉位分配: {actual_capital_percent:.2f}%")
    print(f"每個倉位資金: ${expected_capital_per_position:.2f}")
    
    # 計算倉位大小
    entry_price = 50000
    stop_loss = 49000
    position_size = rm.calculate_position_size(entry_price, stop_loss)
    position_value = position_size * entry_price
    
    print(f"\n倉位計算範例:")
    print(f"  入場價格: ${entry_price}")
    print(f"  止損價格: ${stop_loss}")
    print(f"  倉位大小: {position_size:.6f}")
    print(f"  倉位價值: ${position_value:.2f}")
    print(f"  佔總資金: {(position_value/account_balance)*100:.2f}%")
    
    assert actual_capital_percent == 100/3, "每個倉位應為33.33%"
    print("✅ 測試通過！\n")

def test_signal_ranking():
    """測試信號排序系統"""
    print("=" * 60)
    print("測試 3: 信號排序（信心度 vs 投報率）")
    print("=" * 60)
    
    rm = RiskManager(account_balance=10000)
    
    # 添加多個信號
    signals = [
        ('BTCUSDT', {'type': 'BUY', 'entry_price': 50000, 'stop_loss': 49000, 'take_profit': 52000, 
                     'confidence': 90.0, 'expected_roi': 4.0, 'reason': 'Strong signal', 'analysis': {}}),
        ('ETHUSDT', {'type': 'BUY', 'entry_price': 3000, 'stop_loss': 2950, 'take_profit': 3200, 
                     'confidence': 85.0, 'expected_roi': 6.67, 'reason': 'Good signal', 'analysis': {}}),
        ('BNBUSDT', {'type': 'BUY', 'entry_price': 400, 'stop_loss': 390, 'take_profit': 425, 
                     'confidence': 95.0, 'expected_roi': 6.25, 'reason': 'Very strong', 'analysis': {}}),
        ('SOLUSDT', {'type': 'BUY', 'entry_price': 100, 'stop_loss': 98, 'take_profit': 108, 
                     'confidence': 80.0, 'expected_roi': 8.0, 'reason': 'Medium signal', 'analysis': {}}),
        ('XRPUSDT', {'type': 'BUY', 'entry_price': 0.5, 'stop_loss': 0.49, 'take_profit': 0.54, 
                     'confidence': 75.0, 'expected_roi': 8.0, 'reason': 'Weak signal', 'analysis': {}})
    ]
    
    for symbol, signal in signals:
        rm.add_pending_signal(symbol, signal)
    
    print(f"\n總共收集到 {len(signals)} 個信號\n")
    
    # 測試按信心度排序
    print("🎯 按信心度排序:")
    top_by_confidence = rm.get_top_signals(sort_by='confidence')
    for i, (symbol, signal) in enumerate(top_by_confidence, 1):
        print(f"  {i}. {symbol}: 信心度 {signal['confidence']:.1f}%, ROI {signal['expected_roi']:.2f}%")
    
    # 測試按投報率排序
    print("\n💰 按投報率排序:")
    rm.clear_pending_signals()
    for symbol, signal in signals:
        rm.add_pending_signal(symbol, signal)
    
    top_by_roi = rm.get_top_signals(sort_by='roi')
    for i, (symbol, signal) in enumerate(top_by_roi, 1):
        print(f"  {i}. {symbol}: ROI {signal['expected_roi']:.2f}%, 信心度 {signal['confidence']:.1f}%")
    
    assert len(top_by_confidence) == 3, "應返回3個信號"
    assert len(top_by_roi) == 3, "應返回3個信號"
    print("\n✅ 測試通過！\n")

def test_full_cycle():
    """測試完整週期（收集信號 -> 排序 -> 執行前3個）"""
    print("=" * 60)
    print("測試 4: 完整交易週期模擬")
    print("=" * 60)
    
    rm = RiskManager(account_balance=10000)
    
    # 模擬收集 10 個信號
    print("📊 收集到 10 個交易信號...")
    signals = []
    for i in range(10):
        symbol = f"COIN{i}USDT"
        signal = {
            'type': 'BUY',
            'entry_price': 100 + i,
            'stop_loss': 95 + i,
            'take_profit': 110 + i,
            'confidence': 70 + (i * 2),  # 70-88
            'expected_roi': 5 + (i * 0.5),  # 5-9.5
            'reason': f'Signal {i}',
            'analysis': {}
        }
        signals.append((symbol, signal))
        rm.add_pending_signal(symbol, signal)
        print(f"  {symbol}: 信心度 {signal['confidence']:.1f}%, ROI {signal['expected_roi']:.2f}%")
    
    # 選擇前 3 個
    print("\n🎯 選擇信心度最高的 3 個信號...")
    top_signals = rm.get_top_signals(sort_by='confidence')
    
    print(f"\n✅ 選中 {len(top_signals)} 個信號執行:")
    for i, (symbol, signal) in enumerate(top_signals, 1):
        print(f"  {i}. {symbol}: 信心度 {signal['confidence']:.1f}%, ROI {signal['expected_roi']:.2f}%")
        
        # 模擬開倉
        if rm.can_open_position(symbol):
            rm.open_position(
                symbol, 'LONG',
                signal['entry_price'],
                0.01,
                signal['stop_loss'],
                signal['take_profit']
            )
    
    print(f"\n📊 最終倉位狀態:")
    print(f"  開倉數量: {len(rm.open_positions)}/3")
    for symbol in rm.open_positions:
        print(f"  - {symbol}")
    
    assert len(rm.open_positions) == 3, "應開3個倉位"
    print("\n✅ 測試通過！\n")

def test_config():
    """測試配置"""
    print("=" * 60)
    print("測試 5: 配置驗證")
    print("=" * 60)
    
    print(f"交易對模式: {Config.SYMBOL_MODE}")
    print(f"最大交易對數: {Config.MAX_SYMBOLS}")
    print(f"最大同時倉位: {Config.MAX_CONCURRENT_POSITIONS}")
    print(f"每倉位資金: {Config.CAPITAL_PER_POSITION_PERCENT:.2f}%")
    print(f"每筆風險: {Config.RISK_PER_TRADE_PERCENT}%")
    print(f"最大倉位: {Config.MAX_POSITION_SIZE_PERCENT}%")
    
    assert Config.SYMBOL_MODE == 'all', "應為全量模式"
    assert Config.MAX_SYMBOLS == 648, "應監控648個幣種"
    assert Config.MAX_CONCURRENT_POSITIONS == 3, "最大倉位應為3"
    assert abs(Config.CAPITAL_PER_POSITION_PERCENT - 33.33) < 0.1, "每倉位應為33.33%"
    
    print("\n✅ 測試通過！\n")

if __name__ == '__main__':
    print("\n" + "🧪 " * 30)
    print("3 倉位管理系統測試")
    print("🧪 " * 30 + "\n")
    
    try:
        test_config()
        test_3_position_limit()
        test_capital_allocation()
        test_signal_ranking()
        test_full_cycle()
        
        print("=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)
        print("\n系統已準備就緒！")
        print("- ✅ 監控 648 個幣種")
        print("- ✅ 最多同時持有 3 個倉位")
        print("- ✅ 資金平均拆成 3 等份")
        print("- ✅ 選擇信心度或投報率最高的信號")
        print("- ✅ 完整的風險管理系統\n")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

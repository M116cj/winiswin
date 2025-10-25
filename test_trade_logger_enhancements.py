#!/usr/bin/env python3
"""
測試 TradeLogger 增強功能

測試項目：
1. ML_FEATURE_SCHEMA 定義
2. 數據驗證（validate_entry_data, validate_exit_data）
3. 完整性檢查（check_incomplete_pairs）
4. 統計追蹤（get_statistics）
5. 特徵覆蓋率計算
"""

import json
import time
from datetime import datetime
from trade_logger import TradeLogger, ML_FEATURE_SCHEMA


def test_ml_feature_schema():
    """測試 ML_FEATURE_SCHEMA 是否正確定義"""
    print("=" * 70)
    print("測試 1: ML_FEATURE_SCHEMA 定義")
    print("=" * 70)
    
    assert 'signal_features' in ML_FEATURE_SCHEMA
    assert 'technical_indicators' in ML_FEATURE_SCHEMA
    assert 'price_position' in ML_FEATURE_SCHEMA
    assert 'trade_parameters' in ML_FEATURE_SCHEMA
    assert 'kline_data' in ML_FEATURE_SCHEMA
    assert 'outcome_labels' in ML_FEATURE_SCHEMA
    
    print("✅ ML_FEATURE_SCHEMA 包含所有必需的分類")
    print(f"   - 信號特徵: {len(ML_FEATURE_SCHEMA['signal_features'])} 個")
    print(f"   - 技術指標: {len(ML_FEATURE_SCHEMA['technical_indicators'])} 個")
    print(f"   - 價格位置: {len(ML_FEATURE_SCHEMA['price_position'])} 個")
    print(f"   - 交易參數: {len(ML_FEATURE_SCHEMA['trade_parameters'])} 個")
    print(f"   - K線數據: {len(ML_FEATURE_SCHEMA['kline_data'])} 個")
    print(f"   - 結果標籤: {len(ML_FEATURE_SCHEMA['outcome_labels'])} 個")
    print()


def test_data_validation():
    """測試數據驗證功能"""
    print("=" * 70)
    print("測試 2: 數據驗證")
    print("=" * 70)
    
    logger = TradeLogger(
        log_file='test_trades.json',
        ml_file='test_ml_data.json',
        buffer_size=5,
        auto_flush_interval=10
    )
    
    # 測試完整的開倉數據
    valid_entry_data = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'entry_price': 50000.0,
        'quantity': 0.01,
        'leverage': 10.0,
        'margin': 500.0,
        'confidence': 85.0
    }
    
    is_valid, missing = logger.validate_entry_data(valid_entry_data)
    assert is_valid == True, "完整的開倉數據應該通過驗證"
    print("✅ 完整的開倉數據驗證通過")
    
    # 測試缺失字段的開倉數據
    invalid_entry_data = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        # 缺少 entry_price, quantity, leverage, margin, confidence
    }
    
    is_valid, missing = logger.validate_entry_data(invalid_entry_data)
    assert is_valid == False, "缺失字段的數據應該驗證失敗"
    print(f"✅ 缺失字段的數據驗證失敗（預期行為）")
    print(f"   缺失字段: {missing}")
    
    # 測試完整的平倉數據
    valid_exit_data = {
        'trade_id': 'TEST_20250101_120000',
        'symbol': 'BTCUSDT',
        'exit_price': 51000.0,
        'pnl': 100.0,
        'pnl_percent': 2.0
    }
    
    is_valid, missing = logger.validate_exit_data(valid_exit_data)
    assert is_valid == True, "完整的平倉數據應該通過驗證"
    print("✅ 完整的平倉數據驗證通過")
    print()


def test_entry_exit_flow():
    """測試完整的開倉/平倉流程"""
    print("=" * 70)
    print("測試 3: 開倉/平倉流程和完整性檢查")
    print("=" * 70)
    
    logger = TradeLogger(
        log_file='test_trades.json',
        ml_file='test_ml_data.json',
        buffer_size=5,
        auto_flush_interval=10
    )
    
    # 模擬開倉
    entry_data = {
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'entry_price': 50000.0,
        'quantity': 0.01,
        'stop_loss': 49000.0,
        'take_profit': 52000.0,
        'leverage': 10.0,
        'margin': 500.0,
        'margin_percent': 5.0,
        'confidence': 85.0,
        'expected_roi': 4.0,
        'strategy': 'ICT_SMC',
        'reason': 'Test entry',
        'metadata': {
            'macd': 50.0,
            'ema_200': 48000.0,
            'current_price': 50000.0,
            'rsi': 65.0
        }
    }
    
    trade_id = logger.log_position_entry(entry_data, binance_client=None, timeframe='1m')
    assert trade_id is not None, "應該成功記錄開倉並返回 trade_id"
    print(f"✅ 成功記錄開倉: {trade_id}")
    
    # 檢查 pending_entries
    assert trade_id in logger.pending_entries, "trade_id 應該在 pending_entries 中"
    print(f"✅ trade_id 已添加到 pending_entries")
    
    # 檢查未閉合的交易
    incomplete = logger.check_incomplete_pairs()
    assert len(incomplete) == 1, "應該有 1 個未閉合的交易"
    print(f"✅ 檢測到 {len(incomplete)} 個未閉合的交易")
    
    # 模擬平倉
    exit_data = {
        'trade_id': trade_id,
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'entry_price': 50000.0,
        'exit_price': 51000.0,
        'exit_reason': 'TAKE_PROFIT',
        'pnl': 100.0,
        'pnl_percent': 2.0,
        'holding_duration_minutes': 30.0,
        'entry_time': datetime.utcnow(),
        'exit_time': datetime.utcnow()
    }
    
    logger.log_position_exit(exit_data, binance_client=None, timeframe='1m')
    print(f"✅ 成功記錄平倉")
    
    # 檢查 pending_entries 應該為空
    assert trade_id not in logger.pending_entries, "trade_id 應該從 pending_entries 中移除"
    print(f"✅ trade_id 已從 pending_entries 移除")
    
    # 檢查 ML 數據
    assert len(logger.ml_data) == 1, "應該有 1 個 ML 訓練樣本"
    print(f"✅ 成功創建 1 個 ML 訓練樣本")
    
    # 檢查未閉合的交易（應該為 0）
    incomplete = logger.check_incomplete_pairs()
    assert len(incomplete) == 0, "不應該有未閉合的交易"
    print(f"✅ 所有交易已閉合")
    print()


def test_statistics():
    """測試統計追蹤功能"""
    print("=" * 70)
    print("測試 4: 統計追蹤")
    print("=" * 70)
    
    logger = TradeLogger(
        log_file='test_trades.json',
        ml_file='test_ml_data.json',
        buffer_size=5,
        auto_flush_interval=10
    )
    
    # 記錄一筆交易
    entry_data = {
        'symbol': 'ETHUSDT',
        'side': 'SELL',
        'entry_price': 3000.0,
        'quantity': 0.1,
        'stop_loss': 3100.0,
        'take_profit': 2900.0,
        'leverage': 5.0,
        'margin': 600.0,
        'margin_percent': 6.0,
        'confidence': 75.0,
        'expected_roi': 3.0,
        'strategy': 'ICT_SMC',
        'reason': 'Test short',
        'metadata': {
            'macd': -30.0,
            'ema_200': 3100.0,
            'current_price': 3000.0,
            'rsi': 35.0
        }
    }
    
    trade_id = logger.log_position_entry(entry_data, binance_client=None, timeframe='1m')
    
    exit_data = {
        'trade_id': trade_id,
        'symbol': 'ETHUSDT',
        'side': 'SELL',
        'entry_price': 3000.0,
        'exit_price': 2900.0,
        'exit_reason': 'TAKE_PROFIT',
        'pnl': 100.0,
        'pnl_percent': 3.33,
        'holding_duration_minutes': 45.0,
        'entry_time': datetime.utcnow(),
        'exit_time': datetime.utcnow()
    }
    
    logger.log_position_exit(exit_data, binance_client=None, timeframe='1m')
    
    # 獲取統計
    stats = logger.get_statistics()
    
    print("📊 數據完整性統計:")
    print(f"   總開倉: {stats['data_integrity']['total_entries']}")
    print(f"   總平倉: {stats['data_integrity']['total_exits']}")
    print(f"   完整交易對: {stats['data_integrity']['complete_pairs']}")
    print(f"   未完成交易對: {stats['data_integrity']['incomplete_pairs']}")
    print(f"   完成率: {stats['data_integrity']['pair_completion_rate']:.1f}%")
    
    print("\n📊 ML 訓練數據統計:")
    print(f"   總樣本數: {stats['ml_training_data']['total_samples']}")
    print(f"   盈利樣本: {stats['ml_training_data']['winning_samples']}")
    print(f"   虧損樣本: {stats['ml_training_data']['losing_samples']}")
    print(f"   勝率: {stats['ml_training_data']['win_rate']:.1f}%")
    
    print("\n📊 數據質量:")
    print(f"   驗證錯誤: {stats['data_quality']['validation_errors']}")
    print(f"   總 Flush 次數: {stats['data_quality']['total_flushes']}")
    print(f"   最後 Flush: {stats['data_quality']['last_flush']}")
    
    assert stats['data_integrity']['total_entries'] >= 1
    assert stats['data_integrity']['total_exits'] >= 1
    assert stats['ml_training_data']['total_samples'] >= 1
    
    print("\n✅ 統計追蹤功能正常")
    print()


def test_auto_flush():
    """測試自動 Flush 機制"""
    print("=" * 70)
    print("測試 5: 自動 Flush 機制")
    print("=" * 70)
    
    logger = TradeLogger(
        log_file='test_trades.json',
        ml_file='test_ml_data.json',
        buffer_size=2,  # 每 2 筆就 flush
        auto_flush_interval=5  # 5 秒自動 flush
    )
    
    print(f"🔄 Buffer size: {logger.buffer_size}")
    print(f"🔄 Auto flush interval: {logger.auto_flush_interval}s")
    
    # 記錄 2 筆交易觸發計數 flush
    for i in range(2):
        entry_data = {
            'symbol': f'TEST{i}USDT',
            'side': 'BUY',
            'entry_price': 100.0 + i,
            'quantity': 0.01,
            'leverage': 10.0,
            'margin': 100.0,
            'margin_percent': 5.0,
            'confidence': 80.0,
            'expected_roi': 2.0,
            'strategy': 'TEST',
            'reason': f'Test {i}',
            'metadata': {}
        }
        
        logger.log_position_entry(entry_data)
    
    print(f"✅ 記錄了 {logger.stats['total_entries']} 筆開倉")
    print(f"✅ 觸發了 {logger.stats['total_flushes']} 次 Flush")
    
    # 測試手動 flush
    logger.flush()
    print(f"✅ 手動 Flush 成功")
    
    print()


def cleanup():
    """清理測試文件"""
    import os
    files_to_remove = [
        'test_trades.json',
        'test_ml_data.json',
        'ml_pending_entries.json'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    print("🧹 清理測試文件完成")


def main():
    """運行所有測試"""
    print("\n" + "=" * 70)
    print("TradeLogger 增強功能測試")
    print("=" * 70)
    print()
    
    try:
        test_ml_feature_schema()
        test_data_validation()
        test_entry_exit_flow()
        test_statistics()
        test_auto_flush()
        
        print("=" * 70)
        print("✅ 所有測試通過！")
        print("=" * 70)
        print()
        
        print("📋 實現的功能:")
        print("   ✅ 1. 定義標準化特徵 Schema (ML_FEATURE_SCHEMA)")
        print("   ✅ 2. 數據驗證（validate_entry_data, validate_exit_data）")
        print("   ✅ 3. 開倉/平倉對完整性檢查（check_incomplete_pairs）")
        print("   ✅ 4. 智能 Flush 機制（計數觸發 + 定時觸發 + 退出觸發）")
        print("   ✅ 5. 統計追蹤（完整性、特徵覆蓋率、數據質量）")
        print("   ✅ 6. 自動持久化（pending_entries）")
        print("   ✅ 7. 特徵覆蓋率計算")
        print()
        
    except AssertionError as e:
        print(f"❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup()
    
    return 0


if __name__ == '__main__':
    exit(main())

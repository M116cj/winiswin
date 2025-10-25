#!/usr/bin/env python3
"""
v3.2 修復驗證腳本

驗證以下修復：
1. 動態保證金計算（3%-13%）
2. 止損/止盈訂單設置
3. 版本號正確
"""

import sys
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_imports():
    """驗證導入是否正確"""
    logger.info("="*70)
    logger.info("🔍 步驟 1: 驗證導入")
    logger.info("="*70)
    
    try:
        # 驗證 RiskManager 沒有導入舊的 calculate_position_size
        import risk_manager
        import inspect
        
        # 獲取 risk_manager 模組中導入的函數
        module_dict = vars(risk_manager)
        
        # 檢查是否導入了 calculate_position_size 函數
        if 'calculate_position_size' in module_dict:
            func = module_dict['calculate_position_size']
            if not inspect.ismethod(func):
                logger.error("❌ FAILED: risk_manager 仍然從 utils.helpers 導入舊的 calculate_position_size")
                logger.error("   請確認 risk_manager.py line 3 已移除 calculate_position_size 導入")
                return False
        
        logger.info("✅ PASSED: RiskManager 未導入舊的 calculate_position_size")
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: 驗證導入時出錯: {e}")
        return False

def verify_risk_manager_calculation():
    """驗證 RiskManager 使用正確的保證金計算"""
    logger.info("\n" + "="*70)
    logger.info("🔍 步驟 2: 驗證保證金計算邏輯")
    logger.info("="*70)
    
    try:
        from risk_manager import RiskManager
        from config import Config
        
        # 創建 RiskManager 實例
        risk_mgr = RiskManager(account_balance=1000.0)
        
        # 測試不同信心度的保證金計算
        test_cases = [
            {'confidence': 70.0, 'expected_min': 3.0, 'expected_max': 3.3},   # 70% 信心度 → 3% 保證金
            {'confidence': 80.0, 'expected_min': 6.0, 'expected_max': 6.3},   # 80% 信心度 → 6% 保證金
            {'confidence': 90.0, 'expected_min': 10.0, 'expected_max': 10.3}, # 90% 信心度 → 10% 保證金
            {'confidence': 95.0, 'expected_min': 11.5, 'expected_max': 11.8}, # 95% 信心度 → 11.5% 保證金
        ]
        
        all_passed = True
        
        for test in test_cases:
            confidence = test['confidence']
            expected_min = test['expected_min']
            expected_max = test['expected_max']
            
            # 計算保證金比例
            margin_percent = risk_mgr.calculate_margin_percent(confidence)
            
            # 驗證保證金比例在預期範圍內
            if expected_min <= margin_percent <= expected_max:
                logger.info(f"✅ 信心度 {confidence:.1f}% → 保證金 {margin_percent:.2f}% (預期: {expected_min}-{expected_max}%)")
            else:
                logger.error(f"❌ 信心度 {confidence:.1f}% → 保證金 {margin_percent:.2f}% (預期: {expected_min}-{expected_max}%)")
                all_passed = False
        
        # 測試完整的倉位計算
        logger.info("\n測試完整倉位計算:")
        
        position_params = risk_mgr.calculate_position_size(
            symbol='BTCUSDT',
            entry_price=50000.0,
            stop_loss_price=49000.0,
            confidence=85.0,
            leverage=10.0
        )
        
        if position_params:
            margin = position_params['margin']
            margin_percent = position_params['margin_percent']
            position_value = position_params['position_value']
            
            logger.info(f"  總資金: $1000.00")
            logger.info(f"  信心度: 85.0%")
            logger.info(f"  保證金比例: {margin_percent:.2f}%")
            logger.info(f"  保證金金額: ${margin:.2f}")
            logger.info(f"  槓桿: 10x")
            logger.info(f"  倉位價值: ${position_value:.2f}")
            
            # 驗證保證金在 3%-13% 範圍內（不是舊的 0.4-0.6）
            if 3.0 <= margin_percent <= 13.0 and 30.0 <= margin <= 130.0:
                logger.info("✅ PASSED: 保證金計算使用 v3.2 邏輯 (3%-13%)")
            else:
                logger.error(f"❌ FAILED: 保證金 ${margin:.2f} ({margin_percent:.2f}%) 不在 v3.2 範圍內")
                logger.error("   可能仍在使用 v3.0 的舊邏輯")
                all_passed = False
        else:
            logger.error("❌ FAILED: calculate_position_size 返回 None")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ FAILED: 驗證保證金計算時出錯: {e}")
        logger.exception(e)
        return False

def verify_version_number():
    """驗證版本號是否為 v3.2"""
    logger.info("\n" + "="*70)
    logger.info("🔍 步驟 3: 驗證版本號")
    logger.info("="*70)
    
    try:
        # 讀取 main_v3.py 檢查版本號
        with open('main_v3.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Cryptocurrency Trading Bot v3.2' in content:
            logger.info("✅ PASSED: 版本號為 v3.2")
            return True
        elif 'Cryptocurrency Trading Bot v3.0' in content:
            logger.error("❌ FAILED: 版本號仍為 v3.0")
            return False
        else:
            logger.warning("⚠️  WARNING: 無法找到版本號")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: 驗證版本號時出錯: {e}")
        return False

async def verify_async_order_execution():
    """驗證止損/止盈訂單使用異步執行"""
    logger.info("\n" + "="*70)
    logger.info("🔍 步驟 4: 驗證異步訂單執行")
    logger.info("="*70)
    
    try:
        # 讀取 execution_service.py 檢查異步調用
        with open('services/execution_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否使用 loop.run_in_executor
        if 'loop.run_in_executor' in content and 'set_stop_loss_order' in content:
            logger.info("✅ PASSED: 止損訂單使用異步執行 (loop.run_in_executor)")
        else:
            logger.error("❌ FAILED: 止損訂單可能未使用異步執行")
            return False
        
        if 'loop.run_in_executor' in content and 'set_take_profit_order' in content:
            logger.info("✅ PASSED: 止盈訂單使用異步執行 (loop.run_in_executor)")
        else:
            logger.error("❌ FAILED: 止盈訂單可能未使用異步執行")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: 驗證異步執行時出錯: {e}")
        return False

async def main():
    """運行所有驗證"""
    logger.info("🚀 開始 v3.2 修復驗證")
    logger.info("")
    
    results = []
    
    # 步驟 1: 驗證導入
    results.append(("導入驗證", verify_imports()))
    
    # 步驟 2: 驗證保證金計算
    results.append(("保證金計算", verify_risk_manager_calculation()))
    
    # 步驟 3: 驗證版本號
    results.append(("版本號", verify_version_number()))
    
    # 步驟 4: 驗證異步訂單執行
    results.append(("異步訂單執行", await verify_async_order_execution()))
    
    # 總結
    logger.info("\n" + "="*70)
    logger.info("📊 驗證結果總結")
    logger.info("="*70)
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {status}: {name}")
    
    logger.info("")
    logger.info(f"總計: {passed_count}/{total_count} 項測試通過")
    logger.info("="*70)
    
    if passed_count == total_count:
        logger.info("🎉 所有驗證通過！v3.2 修復成功！")
        logger.info("")
        logger.info("下一步:")
        logger.info("  1. 提交更改到 Git")
        logger.info("  2. 部署到 Railway")
        logger.info("  3. 監控日誌確認保證金和止損/止盈正常工作")
        return 0
    else:
        logger.error("⚠️  部分驗證失敗！請檢查上述錯誤並修復。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

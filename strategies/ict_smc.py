import numpy as np
import pandas as pd
from utils.helpers import setup_logger, get_market_structure_change

logger = setup_logger(__name__)

class ICTSMCStrategy:
    def __init__(self):
        self.name = "ICT/SMC Strategy"
        self.order_blocks = []
        self.liquidity_zones = []
        self.min_confidence_threshold = 70.0  # 最低信心度門檻
    
    def is_valid_order_block(self, df, idx, direction='bullish'):
        """
        三重驗證訂單塊有效性（v2.0 優化）
        
        驗證 1：反向 K 棒（必須是陰線/陽線）
        驗證 2：突破 K 棒幅度 > 1.2x OB 本體
        驗證 3：5 根 K 棒不回測 OB 低點/高點
        """
        if idx + 1 >= len(df):
            return False
        
        if direction == 'bullish':
            # 驗證 1：OB 必須是陰線
            if df.iloc[idx]['close'] >= df.iloc[idx]['open']:
                return False
            
            # 驗證 2：突破 K 棒幅度 > 1.2x OB 本體
            ob_body = df.iloc[idx]['open'] - df.iloc[idx]['close']
            next_body = df.iloc[idx+1]['close'] - df.iloc[idx+1]['open']
            
            if ob_body <= 0 or next_body < 1.2 * ob_body:
                return False
            
            # 驗證 3：5 根 K 棒不回測 OB 低點
            ob_low = df.iloc[idx]['low']
            for i in range(1, min(6, len(df) - idx)):
                if df.iloc[idx + i]['close'] < ob_low:
                    return False
            
            return True
            
        else:  # bearish
            # 驗證 1：OB 必須是陽線
            if df.iloc[idx]['close'] <= df.iloc[idx]['open']:
                return False
            
            # 驗證 2：突破 K 棒幅度 > 1.2x OB 本體
            ob_body = df.iloc[idx]['close'] - df.iloc[idx]['open']
            next_body = df.iloc[idx+1]['open'] - df.iloc[idx+1]['close']
            
            if ob_body <= 0 or next_body < 1.2 * ob_body:
                return False
            
            # 驗證 3：5 根 K 棒不回測 OB 高點
            ob_high = df.iloc[idx]['high']
            for i in range(1, min(6, len(df) - idx)):
                if df.iloc[idx + i]['close'] > ob_high:
                    return False
            
            return True
    
    def identify_order_blocks(self, df, lookback=20):
        """識別有效的訂單塊（整合三重驗證）"""
        order_blocks = []
        
        for i in range(lookback, len(df) - 6):  # 留出 5 根 K 棒用於驗證
            # 檢查看漲 OB
            if self.is_valid_order_block(df, i, 'bullish'):
                order_block = {
                    'type': 'bullish',
                    'high': df.iloc[i]['high'],
                    'low': df.iloc[i]['low'],
                    'timestamp': df.iloc[i]['timestamp'],
                    'validated': True
                }
                order_blocks.append(order_block)
            
            # 檢查看跌 OB
            elif self.is_valid_order_block(df, i, 'bearish'):
                order_block = {
                    'type': 'bearish',
                    'high': df.iloc[i]['high'],
                    'low': df.iloc[i]['low'],
                    'timestamp': df.iloc[i]['timestamp'],
                    'validated': True
                }
                order_blocks.append(order_block)
        
        self.order_blocks = order_blocks[-5:]
        return self.order_blocks
    
    def identify_liquidity_zones(self, df, lookback=50):
        liquidity_zones = []
        highs = df['high'].values
        lows = df['low'].values
        
        for i in range(lookback, len(df)):
            window_highs = highs[i-lookback:i]
            window_lows = lows[i-lookback:i]
            
            current_high = highs[i]
            current_low = lows[i]
            
            if current_high >= np.max(window_highs):
                liquidity_zones.append({
                    'type': 'resistance',
                    'price': current_high,
                    'timestamp': df.iloc[i]['timestamp']
                })
            
            if current_low <= np.min(window_lows):
                liquidity_zones.append({
                    'type': 'support',
                    'price': current_low,
                    'timestamp': df.iloc[i]['timestamp']
                })
        
        self.liquidity_zones = liquidity_zones[-5:]
        return self.liquidity_zones
    
    def is_msb_confirmed(self, df, structure_type='bullish'):
        """
        MSB 幅度過濾（v2.0 優化）
        
        要求：
        - 突破幅度 > 0.3%
        - 收盤確認突破
        """
        if len(df) < 3:
            return False
        
        if structure_type == 'bullish':
            prev_high = df.iloc[-3]['high']
            current_high = df.iloc[-2]['high']
            current_close = df.iloc[-2]['close']
            
            # 突破幅度 > 0.3%
            if prev_high <= 0:
                return False
            
            breakout_pct = (current_high - prev_high) / prev_high
            
            # 收盤確認
            return breakout_pct >= 0.003 and current_close > prev_high
            
        else:  # bearish
            prev_low = df.iloc[-3]['low']
            current_low = df.iloc[-2]['low']
            current_close = df.iloc[-2]['close']
            
            # 突破幅度 > 0.3%
            if prev_low <= 0:
                return False
            
            breakdown_pct = (prev_low - current_low) / prev_low
            
            # 收盤確認
            return breakdown_pct >= 0.003 and current_close < prev_low
    
    def check_market_structure(self, df):
        """
        檢查市場結構（整合 MSB 幅度過濾）
        """
        if len(df) < 10:
            return None
        
        market_structure = get_market_structure_change(df)
        
        higher_highs = df['high'].iloc[-3:].is_monotonic_increasing
        higher_lows = df['low'].iloc[-3:].is_monotonic_increasing
        
        lower_highs = df['high'].iloc[-3:].is_monotonic_decreasing
        lower_lows = df['low'].iloc[-3:].is_monotonic_decreasing
        
        # 基礎結構判斷
        if higher_highs and higher_lows:
            # 需要 MSB 確認
            if self.is_msb_confirmed(df, 'bullish'):
                return 'bullish_structure'
            else:
                return 'neutral_structure'  # 結構看漲但未確認
                
        elif lower_highs and lower_lows:
            # 需要 MSB 確認
            if self.is_msb_confirmed(df, 'bearish'):
                return 'bearish_structure'
            else:
                return 'neutral_structure'  # 結構看跌但未確認
        else:
            return 'neutral_structure'
    
    def calculate_confidence(self, structure, macd, macd_signal, ema_9, ema_21, 
                           current_price, signal_type, at_liquidity_zone=False):
        """
        多級配重信心度計算系統
        
        參數：
            structure: 市場結構 ('bullish_structure', 'bearish_structure', 'neutral_structure')
            macd, macd_signal: MACD 指標
            ema_9, ema_21: EMA 指標
            current_price: 當前價格
            signal_type: 信號類型 ('BUY' or 'SELL')
            at_liquidity_zone: 是否在流動性區域
        
        信心度配重：
            - 基礎結構: 40%
            - MACD 確認: 20%
            - EMA 確認: 20%
            - 價格位置: 10%
            - 流動性區域: 10%
        """
        confidence = 0.0
        
        # 1. 市場結構配重 (40%)
        if signal_type == 'BUY':
            if structure == 'bullish_structure':
                confidence += 40.0  # 完美看漲結構
            elif structure == 'neutral_structure':
                confidence += 20.0  # 中性結構，可接受
            # bearish_structure = 0分
        else:  # SELL
            if structure == 'bearish_structure':
                confidence += 40.0  # 完美看跌結構
            elif structure == 'neutral_structure':
                confidence += 20.0  # 中性結構，可接受
            # bullish_structure = 0分
        
        # 2. MACD 確認配重 (20%)
        # 防止除以零錯誤
        macd_denominator = max(abs(macd_signal), 1e-6)
        
        if signal_type == 'BUY':
            if macd > macd_signal:
                macd_diff = macd - macd_signal
                macd_strength = min(abs(macd_diff) / macd_denominator * 100, 1.0)
                confidence += 20.0 * macd_strength
        else:  # SELL
            if macd < macd_signal:
                macd_diff = macd_signal - macd
                macd_strength = min(abs(macd_diff) / macd_denominator * 100, 1.0)
                confidence += 20.0 * macd_strength
        
        # 3. EMA 確認配重 (20%)
        # 防止除以零錯誤
        ema_denominator = max(abs(ema_21), 1e-6)
        
        if signal_type == 'BUY':
            if ema_9 > ema_21:
                ema_gap = (ema_9 - ema_21) / ema_denominator
                ema_strength = min(ema_gap * 100, 1.0)
                confidence += 20.0 * max(ema_strength, 0.5)  # 至少給 10%
        else:  # SELL
            if ema_9 < ema_21:
                ema_gap = (ema_21 - ema_9) / ema_denominator
                ema_strength = min(ema_gap * 100, 1.0)
                confidence += 20.0 * max(ema_strength, 0.5)  # 至少給 10%
        
        # 4. 價格位置配重 (10%)
        if signal_type == 'BUY':
            if current_price > ema_9:
                confidence += 10.0  # 價格在趨勢線上方
            elif current_price > ema_21:
                confidence += 5.0   # 價格至少在長期均線上方
        else:  # SELL
            if current_price < ema_9:
                confidence += 10.0  # 價格在趨勢線下方
            elif current_price < ema_21:
                confidence += 5.0   # 價格至少在長期均線下方
        
        # 5. 流動性區域配重 (10%)
        if at_liquidity_zone:
            confidence += 10.0  # 在關鍵流動性區域
        
        return min(confidence, 100.0)  # 上限 100%
    
    def generate_signal(self, df):
        if len(df) < 50:
            logger.warning("Insufficient data for ICT/SMC analysis")
            return None
        
        # 識別市場特徵
        self.identify_order_blocks(df)
        self.identify_liquidity_zones(df)
        structure = self.check_market_structure(df)
        
        # 獲取當前指標並驗證數據完整性
        try:
            current_price = df.iloc[-1]['close']
            macd = df.iloc[-1]['macd']
            macd_signal = df.iloc[-1]['macd_signal']
            ema_9 = df.iloc[-1]['ema_9']
            ema_21 = df.iloc[-1]['ema_21']
            atr = df.iloc[-1]['atr']
        except (KeyError, IndexError) as e:
            logger.error(f"Missing required indicators: {e}")
            return None
        
        # 驗證所有指標數據有效性
        if any(pd.isna(x) or x is None for x in [current_price, macd, macd_signal, ema_9, ema_21, atr]):
            logger.warning("One or more indicators are NaN or None, skipping signal generation")
            return None
        
        # ATR 必須為正數
        if atr <= 0:
            logger.warning(f"Invalid ATR value: {atr}, skipping signal generation")
            return None
        
        # 價格必須為正數
        if current_price <= 0:
            logger.warning(f"Invalid price: {current_price}, skipping signal generation")
            return None
        
        signal = None
        
        # === 做多信號分析 ===
        if structure in ['bullish_structure', 'neutral_structure']:
            # 檢查是否在支撐區域附近
            at_support = False
            for zone in self.liquidity_zones:
                if zone['type'] == 'support':
                    if abs(current_price - zone['price']) < current_price * 0.015:  # 1.5% 誤差範圍
                        at_support = True
                        break
            
            # 計算做多信心度
            confidence = self.calculate_confidence(
                structure=structure,
                macd=macd,
                macd_signal=macd_signal,
                ema_9=ema_9,
                ema_21=ema_21,
                current_price=current_price,
                signal_type='BUY',
                at_liquidity_zone=at_support
            )
            
            # 如果信心度超過門檻，生成信號
            if confidence >= self.min_confidence_threshold:
                # 計算止損和止盈（防禦性檢查）
                try:
                    stop_loss = current_price - (atr * 2.0)
                    take_profit = current_price + (atr * 3.0)
                    
                    # 確保止損和止盈有效
                    if stop_loss <= 0 or take_profit <= 0:
                        logger.warning(f"Invalid stop/take levels: SL={stop_loss}, TP={take_profit}")
                        return None
                    
                    # 計算預期投報率
                    risk = abs(current_price - stop_loss)
                    reward = abs(take_profit - current_price)
                    
                    # 防止除以零並確保合理的風險回報比
                    if risk > 0:
                        expected_roi = reward / risk
                    else:
                        logger.warning("Risk is zero or negative, using default ROI")
                        expected_roi = 1.5
                        
                except Exception as e:
                    logger.error(f"Error calculating trade parameters: {e}")
                    return None
                
                signal = {
                    'type': 'BUY',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'expected_roi': expected_roi,
                    'reason': self._build_reason('BUY', structure, at_support, confidence),
                    'metadata': {
                        'structure': structure,
                        'at_liquidity_zone': at_support,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'ema_9': ema_9,
                        'ema_21': ema_21,
                        'atr': atr,
                        'current_price': current_price
                    }
                }
        
        # === 做空信號分析 ===
        if structure in ['bearish_structure', 'neutral_structure'] and not signal:
            # 檢查是否在阻力區域附近
            at_resistance = False
            for zone in self.liquidity_zones:
                if zone['type'] == 'resistance':
                    if abs(current_price - zone['price']) < current_price * 0.015:  # 1.5% 誤差範圍
                        at_resistance = True
                        break
            
            # 計算做空信心度
            confidence = self.calculate_confidence(
                structure=structure,
                macd=macd,
                macd_signal=macd_signal,
                ema_9=ema_9,
                ema_21=ema_21,
                current_price=current_price,
                signal_type='SELL',
                at_liquidity_zone=at_resistance
            )
            
            # 如果信心度超過門檻，生成信號
            if confidence >= self.min_confidence_threshold:
                # 計算止損和止盈（防禦性檢查）
                try:
                    stop_loss = current_price + (atr * 2.0)
                    take_profit = current_price - (atr * 3.0)
                    
                    # 確保止損和止盈有效
                    if stop_loss <= 0 or take_profit <= 0:
                        logger.warning(f"Invalid stop/take levels: SL={stop_loss}, TP={take_profit}")
                        return None
                    
                    # 計算預期投報率
                    risk = abs(stop_loss - current_price)
                    reward = abs(current_price - take_profit)
                    
                    # 防止除以零並確保合理的風險回報比
                    if risk > 0:
                        expected_roi = reward / risk
                    else:
                        logger.warning("Risk is zero or negative, using default ROI")
                        expected_roi = 1.5
                        
                except Exception as e:
                    logger.error(f"Error calculating trade parameters: {e}")
                    return None
                
                signal = {
                    'type': 'SELL',
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': confidence,
                    'expected_roi': expected_roi,
                    'reason': self._build_reason('SELL', structure, at_resistance, confidence),
                    'metadata': {
                        'structure': structure,
                        'at_liquidity_zone': at_resistance,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'ema_9': ema_9,
                        'ema_21': ema_21,
                        'atr': atr,
                        'current_price': current_price
                    }
                }
        
        if signal:
            logger.info(
                f"ICT/SMC Signal: {signal['type']} at {signal['price']:.4f} "
                f"(信心度: {signal['confidence']:.1f}%) - {signal['reason']}"
            )
        
        return signal
    
    def _build_reason(self, signal_type, structure, at_zone, confidence):
        """構建信號原因描述"""
        reasons = []
        
        if structure == 'bullish_structure':
            reasons.append("看漲結構")
        elif structure == 'bearish_structure':
            reasons.append("看跌結構")
        else:
            reasons.append("中性結構")
        
        if at_zone:
            if signal_type == 'BUY':
                reasons.append("價格在支撐區")
            else:
                reasons.append("價格在阻力區")
        
        if confidence >= 90:
            reasons.append("高信心")
        elif confidence >= 80:
            reasons.append("中高信心")
        else:
            reasons.append("中信心")
        
        return " + ".join(reasons)

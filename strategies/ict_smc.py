import numpy as np
import pandas as pd
from datetime import datetime, timezone
from utils.helpers import setup_logger, get_market_structure_change
from utils.indicators import TechnicalIndicators

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
        # 修復：更嚴格的邊界檢查，確保 idx 和後續至少 6 根 K 棒都在範圍內
        if idx < 0 or idx >= len(df) or idx + 6 >= len(df):
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
            
            # 驗證 3：5 根 K 棒不回測 OB 低點（檢查低點，不是收盤價）
            ob_low = df.iloc[idx]['low']
            for i in range(1, min(6, len(df) - idx)):
                # 任何 K 棒的低點觸及或低於 OB 低點，即為回測
                if df.iloc[idx + i]['low'] <= ob_low:
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
            
            # 驗證 3：5 根 K 棒不回測 OB 高點（檢查高點，不是收盤價）
            ob_high = df.iloc[idx]['high']
            for i in range(1, min(6, len(df) - idx)):
                # 任何 K 棒的高點觸及或高於 OB 高點，即為回測
                if df.iloc[idx + i]['high'] >= ob_high:
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
    
    async def get_1h_trend(self, symbol, data_service):
        """
        獲取 1h 趨勢（v3.1 優化 - 使用 DataService 緩存）
        
        緩存機制：DataService 自動緩存 1 小時（TTL=3600秒）
        趨勢判斷：基於 EMA200
        """
        # 獲取 1h K 線數據（DataService 會自動處理緩存）
        try:
            klines_1h = await data_service.fetch_klines(symbol, '1h', limit=250)
            
            if klines_1h is None or len(klines_1h) < 200:
                logger.warning(f"Insufficient 1h data for {symbol}, using neutral trend")
                return 'neutral'
            
            # 計算 EMA200
            ema200 = TechnicalIndicators.calculate_ema(klines_1h['close'].values, 200)
            
            # 檢查 EMA 是否有效（接受 ndarray/Series/list）
            if not isinstance(ema200, (np.ndarray, pd.Series, list)):
                logger.warning(f"Invalid EMA200 type for {symbol}")
                return 'neutral'
            
            if len(ema200) == 0:
                logger.warning(f"Empty EMA200 for {symbol}")
                return 'neutral'
            
            # 確保取最後一個值（標量），然後檢查 NaN
            last_ema = float(ema200[-1]) if isinstance(ema200, (np.ndarray, list)) else ema200.iloc[-1]
            if pd.isna(last_ema) or np.isnan(last_ema):
                logger.warning(f"NaN EMA200 for {symbol}")
                return 'neutral'
            
            # 判斷趨勢
            current_price = klines_1h['close'].iloc[-1]
            trend = 'bull' if current_price > last_ema else 'bear'
            
            logger.debug(f"1h trend for {symbol}: {trend} (Price: {current_price:.2f}, EMA200: {ema200[-1]:.2f})")
            return trend
            
        except Exception as e:
            logger.error(f"Error fetching 1h trend for {symbol}: {e}")
            return 'neutral'
    
    async def get_15m_trend(self, symbol, data_service):
        """
        獲取 15m 趨勢（v3.1 優化 - 使用 DataService 緩存）
        
        緩存機制：DataService 自動緩存 15 分鐘（TTL=900秒）
        趨勢判斷：基於 EMA200
        返回值：'bull' (多頭), 'bear' (空頭), 'neutral' (中性)
        
        使用場景：
        - 15m K線定義整體趨勢方向
        - 1m K線執行具體交易
        - 只在 15m 趨勢方向一致時才開倉
        """
        # 獲取 15m K 線數據（DataService 會自動處理緩存）
        try:
            from config import Config
            klines_15m = await data_service.fetch_klines(symbol, Config.TREND_TIMEFRAME, limit=250)
            
            if klines_15m is None or len(klines_15m) < 200:
                logger.warning(f"⚠️  15m 數據不足 {symbol}，使用中性趨勢")
                return 'neutral'
            
            # 計算 EMA200
            ema200 = TechnicalIndicators.calculate_ema(klines_15m['close'].values, 200)
            
            # 檢查 EMA 是否有效（接受 ndarray/Series/list）
            if not isinstance(ema200, (np.ndarray, pd.Series, list)):
                logger.warning(f"⚠️  15m EMA200 類型無效 {symbol}，使用中性趨勢")
                return 'neutral'
            
            if len(ema200) == 0:
                logger.warning(f"⚠️  15m EMA200 為空 {symbol}，使用中性趨勢")
                return 'neutral'
            
            # 確保取最後一個值（標量），然後檢查 NaN
            last_ema = float(ema200[-1]) if isinstance(ema200, (np.ndarray, list)) else ema200.iloc[-1]
            if pd.isna(last_ema) or np.isnan(last_ema):
                logger.warning(f"⚠️  15m EMA200 無效 {symbol}，使用中性趨勢")
                return 'neutral'
            
            # 判斷趨勢：價格 > EMA200 = 多頭，否則 = 空頭
            current_price = klines_15m['close'].iloc[-1]
            trend = 'bull' if current_price > last_ema else 'bear'
            
            logger.debug(
                f"📊 15m 趨勢 {symbol}: {trend} "
                f"(價格: {current_price:.2f}, EMA200: {ema200[-1]:.2f})"
            )
            return trend
            
        except Exception as e:
            logger.error(f"❌ 獲取 15m 趨勢失敗 {symbol}: {e}")
            return 'neutral'
    
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
    
    def get_dynamic_risk_reward_ratio(self, confidence):
        """
        根據信心度動態調整風險回報比（v3.0 優化）
        
        參數：
            confidence: 信號信心度 (0-100)
        
        返回：
            風險回報比 (1.0 到 2.0)
        
        邏輯：
            - 高信心度 (90% 及以上)：使用 1:2 風險回報比（最大化收益）
            - 中信心度 (80-90%)：使用 1:1.5 風險回報比（平衡收益與風險）
            - 低信心度 (70-80%)：使用 1:1 風險回報比（保守策略）
            - 低於 70%：不應該生成信號（由 min_confidence_threshold 過濾）
        """
        from config import Config
        
        if confidence >= 90.0:
            # 高信心度：使用最大風險回報比 1:2
            ratio = Config.MAX_RISK_REWARD_RATIO
            logger.debug(f"💎 高信心度 {confidence:.1f}% → 使用 1:{ratio:.1f} 風險回報比")
        elif confidence >= 80.0:
            # 中信心度：使用中等風險回報比 1:1.5
            ratio = Config.MEDIUM_RISK_REWARD_RATIO
            logger.debug(f"⭐ 中信心度 {confidence:.1f}% → 使用 1:{ratio:.1f} 風險回報比")
        else:
            # 低信心度 (70-80%)：使用最小風險回報比 1:1
            ratio = Config.MIN_RISK_REWARD_RATIO
            logger.debug(f"🔹 低信心度 {confidence:.1f}% → 使用 1:{ratio:.1f} 風險回報比")
        
        return ratio
    
    async def generate_signal(self, df, symbol=None, data_service=None):
        """
        生成交易信號（v3.1 優化 - 使用 DataService 緩存）
        
        參數：
            df: 1m K 線數據（用於執行交易）
            symbol: 交易對符號（用於 15m 趨勢過濾）
            data_service: DataService 實例（用於獲取緩存的 15m 數據）
        
        多時間框架策略：
            - 15m K線：定義趨勢方向（EMA200）
            - 1m K線：執行交易信號（技術指標分析）
            - 只在 15m 趨勢一致時才開倉
        """
        if len(df) < 50:
            logger.warning("Insufficient data for ICT/SMC analysis")
            return None
        
        # === v3.1 優化：15m 趨勢過濾（使用 DataService 緩存）===
        trend_15m = 'neutral'
        if symbol and data_service:
            try:
                trend_15m = await self.get_15m_trend(symbol, data_service)
                logger.info(f"📊 {symbol} - 15m趨勢: {trend_15m}")
            except Exception as e:
                logger.warning(f"⚠️  獲取 15m 趨勢失敗 {symbol}: {e}")
                trend_15m = 'neutral'
        
        # 識別市場特徵（已整合 OB 三重驗證 和 MSB 幅度過濾）
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
            
            # === v3.0 優化：15m 趨勢過濾（避免逆勢做多）===
            if trend_15m == 'bear':
                logger.debug(f"🚫 跳過做多信號：15m 趨勢為空頭")
                # 不在空頭趨勢中做多，即使有看漲結構
                pass
            # 如果信心度超過門檻，生成信號
            elif confidence >= self.min_confidence_threshold:
                # 計算動態風險回報比（基於信心度）
                dynamic_rr_ratio = self.get_dynamic_risk_reward_ratio(confidence)
                
                # 計算止損和止盈（基於損益平衡價格和動態風險收益比）
                try:
                    from config import Config
                    
                    if Config.USE_BREAKEVEN_STOPS:
                        # 🎯 高頻交易止損策略：基於損益平衡價格
                        leverage = Config.DEFAULT_LEVERAGE
                        fee_rate = Config.TAKER_FEE_RATE
                        total_fee_percent = fee_rate * 2  # 開倉 + 平倉手續費
                        
                        # 做多：損益平衡價格 = 進場價 * (1 + 總手續費%)
                        breakeven = current_price * (1 + total_fee_percent)
                        
                        # 止損：設在損益平衡價格下方 1.5 ATR
                        stop_loss = breakeven - (atr * 1.5)
                        
                        # 驗證止損必須低於入場價（做多）
                        if stop_loss >= current_price:
                            logger.warning(
                                f"⚠️  無效的做多止損 (止損={stop_loss:.8f} >= 入場={current_price:.8f}), "
                                f"使用傳統 ATR 止損"
                            )
                            stop_loss = current_price - (atr * 2.0)
                        
                        # 確保止損仍然有效
                        if stop_loss >= current_price:
                            logger.error(
                                f"❌ 無法設置有效的做多止損 (止損={stop_loss:.8f} >= 入場={current_price:.8f}), "
                                f"跳過信號"
                            )
                            return None
                        
                        # 止盈：基於動態風險收益比（1:1 到 1:2）
                        risk = abs(current_price - stop_loss)
                        reward = risk * dynamic_rr_ratio
                        take_profit = current_price + reward
                        
                        logger.info(
                            f"🎯 做多止損/止盈: 進場={current_price:.8f}, "
                            f"損益平衡={breakeven:.8f}, 止損={stop_loss:.8f}, "
                            f"止盈={take_profit:.8f}, R:R=1:{dynamic_rr_ratio:.1f} "
                            f"(信心度={confidence:.1f}%)"
                        )
                    else:
                        # 傳統 ATR 止損策略
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
                    'reason': self._build_reason('BUY', structure, at_support, confidence, trend_15m),
                    'metadata': {
                        'structure': structure,
                        'at_liquidity_zone': at_support,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'ema_9': ema_9,
                        'ema_21': ema_21,
                        'atr': atr,
                        'current_price': current_price,
                        'trend_15m': trend_15m,  # v3.0: 記錄 15m 趨勢
                        'dynamic_rr_ratio': dynamic_rr_ratio  # v3.0: 記錄動態風險回報比
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
            
            # === v3.0 優化：15m 趨勢過濾（避免逆勢做空）===
            if trend_15m == 'bull':
                logger.debug(f"🚫 跳過做空信號：15m 趨勢為多頭")
                # 不在多頭趨勢中做空，即使有看跌結構
                pass
            # 如果信心度超過門檻，生成信號
            elif confidence >= self.min_confidence_threshold:
                # 計算動態風險回報比（基於信心度）
                dynamic_rr_ratio = self.get_dynamic_risk_reward_ratio(confidence)
                
                # 計算止損和止盈（基於損益平衡價格和動態風險收益比）
                try:
                    from config import Config
                    
                    if Config.USE_BREAKEVEN_STOPS:
                        # 🎯 高頻交易止損策略：基於損益平衡價格
                        leverage = Config.DEFAULT_LEVERAGE
                        fee_rate = Config.TAKER_FEE_RATE
                        total_fee_percent = fee_rate * 2  # 開倉 + 平倉手續費
                        
                        # 做空：損益平衡價格 = 進場價 * (1 - 總手續費%)
                        breakeven = current_price * (1 - total_fee_percent)
                        
                        # 止損：設在損益平衡價格上方 1.5 ATR
                        stop_loss = breakeven + (atr * 1.5)
                        
                        # 驗證止損必須高於入場價（做空）
                        if stop_loss <= current_price:
                            logger.warning(
                                f"⚠️  無效的做空止損 (止損={stop_loss:.8f} <= 入場={current_price:.8f}), "
                                f"使用傳統 ATR 止損"
                            )
                            stop_loss = current_price + (atr * 2.0)
                        
                        # 確保止損仍然有效
                        if stop_loss <= current_price:
                            logger.error(
                                f"❌ 無法設置有效的做空止損 (止損={stop_loss:.8f} <= 入場={current_price:.8f}), "
                                f"跳過信號"
                            )
                            return None
                        
                        # 止盈：基於動態風險收益比（1:1 到 1:2）
                        risk = abs(stop_loss - current_price)
                        reward = risk * dynamic_rr_ratio
                        take_profit = current_price - reward
                        
                        logger.info(
                            f"🎯 做空止損/止盈: 進場={current_price:.8f}, "
                            f"損益平衡={breakeven:.8f}, 止損={stop_loss:.8f}, "
                            f"止盈={take_profit:.8f}, R:R=1:{dynamic_rr_ratio:.1f} "
                            f"(信心度={confidence:.1f}%)"
                        )
                    else:
                        # 傳統 ATR 止損策略
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
                    'reason': self._build_reason('SELL', structure, at_resistance, confidence, trend_15m),
                    'metadata': {
                        'structure': structure,
                        'at_liquidity_zone': at_resistance,
                        'macd': macd,
                        'macd_signal': macd_signal,
                        'ema_9': ema_9,
                        'ema_21': ema_21,
                        'atr': atr,
                        'current_price': current_price,
                        'trend_15m': trend_15m,  # v3.0: 記錄 15m 趨勢
                        'dynamic_rr_ratio': dynamic_rr_ratio  # v3.0: 記錄動態風險回報比
                    }
                }
        
        if signal:
            logger.info(
                f"ICT/SMC Signal: {signal['type']} at {signal['price']:.4f} "
                f"(信心度: {signal['confidence']:.1f}%) - {signal['reason']}"
            )
        
        return signal
    
    def _build_reason(self, signal_type, structure, at_zone, confidence, trend_15m='neutral'):
        """構建信號原因描述（整合 v2.0 + v3.0 多時間框架）"""
        reasons = []
        
        # v3.0: 添加 15m 趨勢信息
        if trend_15m == 'bull':
            reasons.append("15m多頭")
        elif trend_15m == 'bear':
            reasons.append("15m空頭")
        
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

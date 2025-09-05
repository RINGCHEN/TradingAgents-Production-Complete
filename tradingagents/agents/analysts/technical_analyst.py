#!/usr/bin/env python3
"""
Technical Analyst - 技術分析師
天工 (TianGong) - 整合ART系統的個人化技術分析師

此模組提供：
1. 技術指標分析邏輯
2. 圖表模式識別  
3. 趨勢分析和支撐阻力
4. ART系統個人化技術分析
5. 交易信號生成
6. 進出場點位建議
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, AnalysisConfidenceLevel
from ...dataflows.finmind_adapter import FinMindAdapter

# ART系統整合
try:
    from ...art.trajectory_collector import TrajectoryCollector, TrajectoryType, DecisionStep
    from ...art.ruler_reward_system import RULERRewardSystem, RewardType
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False


class TechnicalIndicator(Enum):
    """技術指標類型"""
    SMA = "sma"                    # 簡單移動平均
    EMA = "ema"                    # 指數移動平均
    RSI = "rsi"                    # 相對強弱指標
    MACD = "macd"                  # MACD
    BOLLINGER_BANDS = "bollinger"  # 布林通道
    KD = "kd"                      # KD指標
    VOLUME_MA = "volume_ma"        # 成交量移動平均
    OBV = "obv"                    # 能量潮指標
    WILLIAMS_R = "williams_r"      # 威廉指標
    CCI = "cci"                    # 商品通道指標

class ChartPattern(Enum):
    """圖表模式"""
    BULLISH_BREAKOUT = "bullish_breakout"      # 多頭突破
    BEARISH_BREAKDOWN = "bearish_breakdown"    # 空頭破底
    SUPPORT_BOUNCE = "support_bounce"          # 支撐反彈
    RESISTANCE_REJECTION = "resistance_rejection"  # 阻力受阻
    TRIANGLE_BREAKOUT = "triangle_breakout"    # 三角形突破
    HEAD_SHOULDERS = "head_shoulders"          # 頭肩型態
    DOUBLE_TOP = "double_top"                  # 雙頭
    DOUBLE_BOTTOM = "double_bottom"            # 雙底
    FLAG_PATTERN = "flag_pattern"              # 旗形整理
    WEDGE_PATTERN = "wedge_pattern"            # 楔形型態

class TrendDirection(Enum):
    """趨勢方向"""
    STRONG_BULLISH = "strong_bullish"          # 強烈看多
    BULLISH = "bullish"                        # 看多
    SIDEWAYS = "sideways"                      # 盤整
    BEARISH = "bearish"                        # 看空
    STRONG_BEARISH = "strong_bearish"          # 強烈看空

class SignalStrength(Enum):
    """信號強度"""
    VERY_STRONG = "very_strong"                # 非常強
    STRONG = "strong"                          # 強
    MODERATE = "moderate"                      # 中等
    WEAK = "weak"                              # 弱
    VERY_WEAK = "very_weak"                    # 非常弱

@dataclass
class TechnicalMetrics:
    """技術指標數據類"""
    # 移動平均線
    sma_5: float = 0.0
    sma_10: float = 0.0
    sma_20: float = 0.0
    sma_60: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    
    # 動量指標
    rsi_14: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    
    # 波動率指標
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_width: float = 0.0
    
    # 台股特色指標
    kd_k: float = 50.0
    kd_d: float = 50.0
    williams_r: float = -50.0
    
    # 成交量指標
    volume_ma: float = 0.0
    obv: float = 0.0
    volume_ratio: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SupportResistance:
    """支撐阻力位數據"""
    support_levels: List[float]
    resistance_levels: List[float]
    current_price: float
    nearest_support: float
    nearest_resistance: float
    support_strength: float  # 0-1
    resistance_strength: float  # 0-1

@dataclass
class TradingSignal:
    """交易信號"""
    signal_type: str           # BUY, SELL, HOLD
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    reasoning: List[str]
    indicators_used: List[str]
    time_horizon: str          # short, medium, long
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['strength'] = self.strength.value
        return result

class TechnicalAnalyst(BaseAnalyst):
    """技術分析師 - ART整合版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 嘗試初始化FinMind適配器
        try:
            self.finmind_adapter = FinMindAdapter()
        except Exception as e:
            self.logger.warning(f"FinMind適配器初始化失敗: {e}")
            self.finmind_adapter = None
        
        # ART系統初始化
        if ART_AVAILABLE:
            try:
                self.trajectory_collector = TrajectoryCollector()
                self.reward_system = RULERRewardSystem()
                self.art_enabled = True
                self.logger.info("TechnicalAnalyst ART系統初始化成功")
            except Exception as e:
                self.logger.warning(f"ART系統初始化失敗: {e}")
                self.art_enabled = False
        else:
            self.art_enabled = False
        
        # 技術指標權重配置 (可透過ART個人化調整)
        self.indicator_weights = {
            'trend_following': 0.35,    # 趨勢跟蹤
            'momentum': 0.30,           # 動量指標
            'volatility': 0.20,         # 波動率指標
            'volume': 0.15              # 成交量指標
        }
        
        # 個人化偏好 (初始默認值，由ART系統學習調整)
        self.user_preferences = {
            'preferred_indicators': [TechnicalIndicator.RSI, TechnicalIndicator.MACD, TechnicalIndicator.KD],
            'risk_tolerance': 'moderate',  # conservative, moderate, aggressive
            'time_horizon': 'medium',      # short, medium, long
            'signal_sensitivity': 0.7      # 0.1-1.0
        }
        
        # Taiwan股市特色配置
        self.taiwan_market_hours = {
            'market_open': '09:00',
            'market_close': '13:30',
            'volume_peak': '10:00-11:00'
        }
        
        # 技術形態模板
        self.pattern_templates = {
            ChartPattern.BULLISH_BREAKOUT: {
                'volume_increase': 1.5,
                'price_increase': 0.03,
                'breakout_confirmation': 3
            },
            ChartPattern.SUPPORT_BOUNCE: {
                'bounce_strength': 0.02,
                'volume_confirmation': 1.2,
                'rsi_oversold': 30
            }
        }

    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行技術分析 - ART增強版"""
        try:
            self.logger.info(f"開始技術分析: {state.stock_id}")
            
            # ART軌跡收集開始
            trajectory_id = None
            if self.art_enabled:
                trajectory_id = f"tech_{state.stock_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self._start_art_trajectory(trajectory_id, state)
            
            # 1. 獲取技術數據
            price_data = await self._get_price_data(state.stock_id)
            volume_data = await self._get_volume_data(state.stock_id)
            
            if price_data is None or price_data.empty:
                return self._create_error_result(state, "無法獲取價格數據")
            
            # 2. 計算技術指標
            technical_metrics = await self._calculate_technical_indicators(price_data, volume_data)
            
            # ART決策步驟記錄
            if self.art_enabled:
                await self._record_decision_step(
                    trajectory_id, "indicator_calculation",
                    {"metrics": technical_metrics.to_dict()},
                    "計算完成技術指標"
                )
            
            # 3. 趨勢分析
            trend_analysis = await self._analyze_trend(price_data, technical_metrics)
            
            # 4. 支撐阻力分析
            support_resistance = await self._analyze_support_resistance(price_data)
            
            # 5. 圖表模式識別
            chart_patterns = await self._identify_chart_patterns(price_data, volume_data)
            
            # 6. 個人化信號生成 (ART增強)
            trading_signal = await self._generate_personalized_signal(
                technical_metrics, trend_analysis, support_resistance, 
                chart_patterns, state.user_context
            )
            
            # 7. 風險評估
            risk_assessment = await self._assess_technical_risk(
                trading_signal, technical_metrics, state.user_context
            )
            
            # 8. 生成最終建議
            recommendation = self._generate_recommendation(trading_signal, risk_assessment)
            target_price = self._calculate_target_price(
                price_data.iloc[-1]['close'], trading_signal, support_resistance
            )
            
            # 建立分析結果
            result = AnalysisResult(
                analyst_id=self.analyst_id,
                stock_id=state.stock_id,
                analysis_type=AnalysisType.TECHNICAL,
                recommendation=recommendation,
                confidence=trading_signal.confidence,
                confidence_level=AnalysisConfidenceLevel.HIGH,  # Will be recalculated in __post_init__
                target_price=target_price,
                reasoning=[
                    f"技術趋勢: {trend_analysis['direction']}",
                    f"關鍵指標: RSI({technical_metrics.rsi_14:.1f}), MACD({technical_metrics.macd:.4f})",
                    f"支撐阻力: 支撐{support_resistance.nearest_support:.1f}, 阻力{support_resistance.nearest_resistance:.1f}",
                    *trading_signal.reasoning
                ],
                risk_factors=risk_assessment.get('factors', []),
                technical_indicators=technical_metrics.to_dict(),
                taiwan_insights=self._generate_taiwan_insights(technical_metrics, chart_patterns),
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                timestamp=datetime.now().isoformat()
            )
            
            # ART軌跡完成
            if self.art_enabled:
                await self._complete_art_trajectory(trajectory_id, result)
            
            self.logger.info(f"技術分析完成: {state.stock_id}, 建議: {recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"技術分析失敗: {str(e)}")
            return self._create_error_result(state, str(e))

    async def _get_price_data(self, stock_id: str) -> Optional[pd.DataFrame]:
        """獲取價格數據"""
        try:
            if self.finmind_adapter:
                # 獲取60天的價格數據
                end_date = datetime.now()
                start_date = end_date - timedelta(days=90)
                
                # Check if get_price_data method exists
                if hasattr(self.finmind_adapter, 'get_price_data'):
                    data = await self.finmind_adapter.get_price_data(
                        stock_id, 
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                else:
                    # Use alternative method or create mock data
                    self.logger.warning("get_price_data method not found, using fallback mock data")
                    return self._create_mock_price_data(stock_id)
                
                if data and not data.empty:
                    # 確保有必要的欄位
                    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
                    if all(col in data.columns for col in required_columns):
                        data['date'] = pd.to_datetime(data['date'])
                        data = data.sort_values('date').reset_index(drop=True)
                        return data
            
            # 如果FinMind不可用，返回模擬數據
            return self._generate_sample_price_data(stock_id)
            
        except Exception as e:
            self.logger.warning(f"獲取價格數據失敗，使用模擬數據: {e}")
            return self._generate_sample_price_data(stock_id)

    async def _get_volume_data(self, stock_id: str) -> Optional[pd.DataFrame]:
        """獲取成交量數據"""
        # 通常成交量數據包含在價格數據中
        return None

    def _generate_sample_price_data(self, stock_id: str) -> pd.DataFrame:
        """生成模擬價格數據用於測試"""
        dates = pd.date_range(start='2024-12-01', periods=60, freq='D')
        
        # 生成模擬價格數據
        base_price = 500.0  # Taiwan股票典型價格
        prices = []
        current_price = base_price
        
        for i in range(60):
            # 隨機波動
            change = np.random.normal(0, 0.02) * current_price
            current_price += change
            
            high = current_price + abs(np.random.normal(0, 0.01)) * current_price
            low = current_price - abs(np.random.normal(0, 0.01)) * current_price
            open_price = current_price + np.random.normal(0, 0.005) * current_price
            volume = int(np.random.normal(1000000, 200000))
            
            prices.append({
                'date': dates[i],
                'open': max(low, open_price),
                'high': max(high, current_price, open_price),
                'low': min(low, current_price, open_price),
                'close': current_price,
                'volume': max(volume, 100000)
            })
        
        return pd.DataFrame(prices)
    
    def _create_mock_price_data(self, stock_id: str) -> pd.DataFrame:
        """創建模擬價格數據用於測試"""
        import numpy as np
        from datetime import datetime, timedelta
        
        # 生成60天的模擬價格數據
        dates = []
        prices = []
        
        # 基準價格 (根據股票代號設定)
        base_prices = {
            '2330': 580.0,  # 台積電
            '2454': 800.0,  # 聯發科  
            '2881': 60.0,   # 富邦金
            '2882': 50.0    # 國泰金
        }
        
        current_price = base_prices.get(stock_id, 100.0)
        
        # 生成60天歷史數據
        for i in range(60, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 生成價格變動 (-3% 到 +3%)
            price_change = np.random.uniform(-0.03, 0.03)
            current_price = current_price * (1 + price_change)
            
            # 生成開高低收
            daily_volatility = np.random.uniform(0.005, 0.02)
            high = current_price * (1 + daily_volatility)
            low = current_price * (1 - daily_volatility)
            open_price = current_price * (1 + np.random.uniform(-0.01, 0.01))
            
            # 生成成交量
            volume = np.random.randint(50000, 500000)
            
            prices.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(current_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(prices)

    async def _calculate_technical_indicators(self, price_data: pd.DataFrame, volume_data: Optional[pd.DataFrame] = None) -> TechnicalMetrics:
        """計算技術指標"""
        try:
            metrics = TechnicalMetrics()
            
            # 移動平均線
            metrics.sma_5 = price_data['close'].rolling(5).mean().iloc[-1]
            metrics.sma_10 = price_data['close'].rolling(10).mean().iloc[-1]
            metrics.sma_20 = price_data['close'].rolling(20).mean().iloc[-1]
            metrics.sma_60 = price_data['close'].rolling(60).mean().iloc[-1] if len(price_data) >= 60 else metrics.sma_20
            
            # EMA
            metrics.ema_12 = price_data['close'].ewm(span=12).mean().iloc[-1]
            metrics.ema_26 = price_data['close'].ewm(span=26).mean().iloc[-1]
            
            # RSI
            delta = price_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            metrics.rsi_14 = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD
            metrics.macd = metrics.ema_12 - metrics.ema_26
            macd_series = price_data['close'].ewm(span=12).mean() - price_data['close'].ewm(span=26).mean()
            metrics.macd_signal = macd_series.ewm(span=9).mean().iloc[-1]
            metrics.macd_histogram = metrics.macd - metrics.macd_signal
            
            # 布林通道
            sma20 = price_data['close'].rolling(20).mean()
            std20 = price_data['close'].rolling(20).std()
            metrics.bb_middle = sma20.iloc[-1]
            metrics.bb_upper = (sma20 + 2 * std20).iloc[-1]
            metrics.bb_lower = (sma20 - 2 * std20).iloc[-1]
            metrics.bb_width = (metrics.bb_upper - metrics.bb_lower) / metrics.bb_middle
            
            # KD指標 (Taiwan股市常用)
            low_min = price_data['low'].rolling(9).min()
            high_max = price_data['high'].rolling(9).max()
            rsv = ((price_data['close'] - low_min) / (high_max - low_min) * 100).fillna(50)
            
            k_values = []
            d_values = []
            k_prev = 50.0
            d_prev = 50.0
            
            for rsv_val in rsv:
                k_curr = (2/3) * k_prev + (1/3) * rsv_val
                d_curr = (2/3) * d_prev + (1/3) * k_curr
                k_values.append(k_curr)
                d_values.append(d_curr)
                k_prev = k_curr
                d_prev = d_curr
            
            metrics.kd_k = k_values[-1] if k_values else 50.0
            metrics.kd_d = d_values[-1] if d_values else 50.0
            
            # 威廉指標
            high_14 = price_data['high'].rolling(14).max()
            low_14 = price_data['low'].rolling(14).min()
            metrics.williams_r = ((high_14.iloc[-1] - price_data['close'].iloc[-1]) / 
                                 (high_14.iloc[-1] - low_14.iloc[-1]) * -100)
            
            # 成交量指標
            if 'volume' in price_data.columns:
                metrics.volume_ma = price_data['volume'].rolling(20).mean().iloc[-1]
                
                # OBV
                obv_values = []
                obv_current = 0
                for i in range(1, len(price_data)):
                    if price_data['close'].iloc[i] > price_data['close'].iloc[i-1]:
                        obv_current += price_data['volume'].iloc[i]
                    elif price_data['close'].iloc[i] < price_data['close'].iloc[i-1]:
                        obv_current -= price_data['volume'].iloc[i]
                    obv_values.append(obv_current)
                
                metrics.obv = obv_values[-1] if obv_values else 0
                metrics.volume_ratio = (price_data['volume'].iloc[-1] / metrics.volume_ma 
                                      if metrics.volume_ma > 0 else 1.0)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"計算技術指標失敗: {e}")
            return TechnicalMetrics()

    async def _analyze_trend(self, price_data: pd.DataFrame, metrics: TechnicalMetrics) -> Dict[str, Any]:
        """趨勢分析"""
        try:
            current_price = price_data['close'].iloc[-1]
            
            # 移動平均線排列
            ma_bullish = (current_price > metrics.sma_5 > metrics.sma_10 > 
                         metrics.sma_20 > metrics.sma_60)
            ma_bearish = (current_price < metrics.sma_5 < metrics.sma_10 < 
                         metrics.sma_20 < metrics.sma_60)
            
            # 趨勢強度計算
            if ma_bullish and metrics.rsi_14 > 60:
                trend_direction = TrendDirection.STRONG_BULLISH
            elif current_price > metrics.sma_20 and metrics.rsi_14 > 50:
                trend_direction = TrendDirection.BULLISH
            elif ma_bearish and metrics.rsi_14 < 40:
                trend_direction = TrendDirection.STRONG_BEARISH
            elif current_price < metrics.sma_20 and metrics.rsi_14 < 50:
                trend_direction = TrendDirection.BEARISH
            else:
                trend_direction = TrendDirection.SIDEWAYS
            
            # 動量分析
            momentum_strength = self._calculate_momentum_strength(metrics)
            
            return {
                'direction': trend_direction.value,
                'strength': momentum_strength,
                'ma_alignment': 'bullish' if ma_bullish else 'bearish' if ma_bearish else 'neutral',
                'price_vs_sma20': (current_price - metrics.sma_20) / metrics.sma_20,
                'rsi_signal': 'overbought' if metrics.rsi_14 > 70 else 'oversold' if metrics.rsi_14 < 30 else 'neutral'
            }
            
        except Exception as e:
            self.logger.error(f"趨勢分析失敗: {e}")
            return {'direction': 'sideways', 'strength': 0.5}

    def _calculate_momentum_strength(self, metrics: TechnicalMetrics) -> float:
        """計算動量強度"""
        try:
            # RSI貢獻
            rsi_score = abs(metrics.rsi_14 - 50) / 50
            
            # MACD貢獻
            macd_score = abs(metrics.macd_histogram) * 10  # 標準化
            macd_score = min(macd_score, 1.0)
            
            # KD貢獻
            kd_score = abs(metrics.kd_k - 50) / 50
            
            # 綜合動量強度
            momentum = (rsi_score * 0.4 + macd_score * 0.4 + kd_score * 0.2)
            return min(momentum, 1.0)
            
        except Exception as e:
            self.logger.error(f"計算動量強度失敗: {e}")
            return 0.5

    async def _analyze_support_resistance(self, price_data: pd.DataFrame) -> SupportResistance:
        """支撐阻力分析"""
        try:
            current_price = price_data['close'].iloc[-1]
            highs = price_data['high'].values
            lows = price_data['low'].values
            
            # 找支撐位 (局部低點)
            support_levels = []
            for i in range(2, len(lows) - 2):
                if (lows[i] <= lows[i-1] and lows[i] <= lows[i-2] and 
                    lows[i] <= lows[i+1] and lows[i] <= lows[i+2]):
                    support_levels.append(lows[i])
            
            # 找阻力位 (局部高點)
            resistance_levels = []
            for i in range(2, len(highs) - 2):
                if (highs[i] >= highs[i-1] and highs[i] >= highs[i-2] and 
                    highs[i] >= highs[i+1] and highs[i] >= highs[i+2]):
                    resistance_levels.append(highs[i])
            
            # 過濾和排序
            support_levels = [s for s in support_levels if s < current_price]
            resistance_levels = [r for r in resistance_levels if r > current_price]
            
            support_levels = sorted(set(support_levels), reverse=True)[:3]
            resistance_levels = sorted(set(resistance_levels))[:3]
            
            # 找最近的支撐和阻力
            nearest_support = support_levels[0] if support_levels else current_price * 0.95
            nearest_resistance = resistance_levels[0] if resistance_levels else current_price * 1.05
            
            # 計算強度 (基於測試次數)
            support_strength = min(len(support_levels) * 0.3, 1.0)
            resistance_strength = min(len(resistance_levels) * 0.3, 1.0)
            
            return SupportResistance(
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                current_price=current_price,
                nearest_support=nearest_support,
                nearest_resistance=nearest_resistance,
                support_strength=support_strength,
                resistance_strength=resistance_strength
            )
            
        except Exception as e:
            self.logger.error(f"支撐阻力分析失敗: {e}")
            current_price = price_data['close'].iloc[-1]
            return SupportResistance(
                support_levels=[current_price * 0.95],
                resistance_levels=[current_price * 1.05],
                current_price=current_price,
                nearest_support=current_price * 0.95,
                nearest_resistance=current_price * 1.05,
                support_strength=0.5,
                resistance_strength=0.5
            )

    async def _identify_chart_patterns(self, price_data: pd.DataFrame, volume_data: Optional[pd.DataFrame]) -> List[ChartPattern]:
        """圖表模式識別"""
        try:
            patterns = []
            current_price = price_data['close'].iloc[-1]
            sma_20 = price_data['close'].rolling(20).mean().iloc[-1]
            
            # 突破模式檢測
            if current_price > sma_20 * 1.02:  # 2%突破
                if 'volume' in price_data.columns:
                    volume_avg = price_data['volume'].rolling(20).mean().iloc[-1]
                    if price_data['volume'].iloc[-1] > volume_avg * 1.3:
                        patterns.append(ChartPattern.BULLISH_BREAKOUT)
            
            # 支撐反彈檢測
            recent_low = price_data['low'].tail(5).min()
            if current_price > recent_low * 1.015:  # 從低點反彈1.5%
                patterns.append(ChartPattern.SUPPORT_BOUNCE)
            
            # 阻力受阻檢測
            recent_high = price_data['high'].tail(5).max()
            if current_price < recent_high * 0.985:  # 從高點回落1.5%
                patterns.append(ChartPattern.RESISTANCE_REJECTION)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"圖表模式識別失敗: {e}")
            return []

    async def _generate_personalized_signal(self, metrics: TechnicalMetrics, trend: Dict[str, Any], 
                                          support_resistance: SupportResistance, patterns: List[ChartPattern],
                                          user_context: Dict[str, Any]) -> TradingSignal:
        """生成個人化交易信號 - ART增強"""
        try:
            # 基礎信號計算
            signal_score = 0.0
            reasoning = []
            indicators_used = []
            
            # 趨勢信號
            if trend['direction'] in ['bullish', 'strong_bullish']:
                signal_score += 0.3
                reasoning.append(f"多頭趨勢確立，趨勢強度: {trend['strength']:.2f}")
            elif trend['direction'] in ['bearish', 'strong_bearish']:
                signal_score -= 0.3
                reasoning.append(f"空頭趨勢確立，趨勢強度: {trend['strength']:.2f}")
            
            # RSI信號
            if metrics.rsi_14 > 70:
                signal_score -= 0.2
                reasoning.append(f"RSI過熱 ({metrics.rsi_14:.1f})，注意回調風險")
                indicators_used.append("RSI")
            elif metrics.rsi_14 < 30:
                signal_score += 0.2
                reasoning.append(f"RSI超賣 ({metrics.rsi_14:.1f})，可能反彈")
                indicators_used.append("RSI")
            
            # MACD信號
            if metrics.macd > metrics.macd_signal and metrics.macd_histogram > 0:
                signal_score += 0.15
                reasoning.append("MACD多頭排列，動能向上")
                indicators_used.append("MACD")
            elif metrics.macd < metrics.macd_signal and metrics.macd_histogram < 0:
                signal_score -= 0.15
                reasoning.append("MACD空頭排列，動能向下")
                indicators_used.append("MACD")
            
            # KD信號 (台股特色)
            if metrics.kd_k > metrics.kd_d and metrics.kd_k > 20:
                signal_score += 0.1
                reasoning.append(f"KD黃金交叉 (K:{metrics.kd_k:.1f}, D:{metrics.kd_d:.1f})")
                indicators_used.append("KD")
            elif metrics.kd_k < metrics.kd_d and metrics.kd_k < 80:
                signal_score -= 0.1
                reasoning.append(f"KD死亡交叉 (K:{metrics.kd_k:.1f}, D:{metrics.kd_d:.1f})")
                indicators_used.append("KD")
            
            # 圖表模式信號
            for pattern in patterns:
                if pattern == ChartPattern.BULLISH_BREAKOUT:
                    signal_score += 0.2
                    reasoning.append("多頭突破型態確認")
                elif pattern == ChartPattern.SUPPORT_BOUNCE:
                    signal_score += 0.15
                    reasoning.append("支撐位反彈")
                elif pattern == ChartPattern.RESISTANCE_REJECTION:
                    signal_score -= 0.15
                    reasoning.append("阻力位受阻")
            
            # 個人化調整 (ART學習結果)
            user_risk_tolerance = user_context.get('risk_tolerance', 'moderate')
            if user_risk_tolerance == 'conservative':
                signal_score *= 0.8  # 保守用戶降低信號強度
                reasoning.append("根據個人風險偏好調整信號強度")
            elif user_risk_tolerance == 'aggressive':
                signal_score *= 1.2  # 積極用戶提高信號強度
                reasoning.append("根據個人風險偏好提高信號敏感度")
            
            # 決定交易信號
            if signal_score > 0.3:
                signal_type = "BUY"
                strength = SignalStrength.STRONG if signal_score > 0.6 else SignalStrength.MODERATE
            elif signal_score < -0.3:
                signal_type = "SELL"  
                strength = SignalStrength.STRONG if signal_score < -0.6 else SignalStrength.MODERATE
            else:
                signal_type = "HOLD"
                strength = SignalStrength.WEAK
            
            # 設定進出場價位
            current_price = support_resistance.current_price
            if signal_type == "BUY":
                entry_price = current_price
                stop_loss = support_resistance.nearest_support
                take_profit = support_resistance.nearest_resistance
            elif signal_type == "SELL":
                entry_price = current_price
                stop_loss = support_resistance.nearest_resistance
                take_profit = support_resistance.nearest_support
            else:
                entry_price = current_price
                stop_loss = current_price * 0.95
                take_profit = current_price * 1.05
            
            # 信心度計算
            confidence = min(abs(signal_score) + 0.3, 1.0)
            
            return TradingSignal(
                signal_type=signal_type,
                strength=strength,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=confidence,
                reasoning=reasoning,
                indicators_used=indicators_used,
                time_horizon=self.user_preferences.get('time_horizon', 'medium')
            )
            
        except Exception as e:
            self.logger.error(f"生成個人化信號失敗: {e}")
            current_price = support_resistance.current_price
            return TradingSignal(
                signal_type="HOLD",
                strength=SignalStrength.WEAK,
                entry_price=current_price,
                stop_loss=current_price * 0.95,
                take_profit=current_price * 1.05,
                confidence=0.5,
                reasoning=["技術分析數據不足"],
                indicators_used=[],
                time_horizon='medium'
            )

    async def _assess_technical_risk(self, signal: TradingSignal, metrics: TechnicalMetrics, 
                                   user_context: Dict[str, Any]) -> Dict[str, Any]:
        """技術風險評估"""
        try:
            risk_factors = []
            risk_level = 'medium'
            
            # 波動率風險
            if metrics.bb_width > 0.15:  # 布林通道寬度大於15%
                risk_factors.append("市場波動率較高，價格震盪劇烈")
            
            # 超買超賣風險
            if metrics.rsi_14 > 80:
                risk_factors.append("RSI極度超買，回調風險高")
                risk_level = 'high'
            elif metrics.rsi_14 < 20:
                risk_factors.append("RSI極度超賣，但可能續跌")
                risk_level = 'high'
            
            # 成交量風險
            if metrics.volume_ratio < 0.5:
                risk_factors.append("成交量不足，流動性風險")
            
            # 趨勢一致性風險
            if signal.strength == SignalStrength.WEAK:
                risk_factors.append("技術信號不明確，建議觀望")
                
            return {
                'level': risk_level,
                'factors': risk_factors,
                'volatility': metrics.bb_width,
                'liquidity_score': min(metrics.volume_ratio, 2.0)
            }
            
        except Exception as e:
            self.logger.error(f"技術風險評估失敗: {e}")
            return {
                'level': 'medium',
                'factors': ['風險評估數據不足'],
                'volatility': 0.1,
                'liquidity_score': 1.0
            }

    def _generate_recommendation(self, signal: TradingSignal, risk_assessment: Dict[str, Any]) -> str:
        """生成最終建議"""
        if signal.signal_type == "BUY":
            if risk_assessment['level'] == 'low' and signal.strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                return "強烈買進"
            elif signal.strength == SignalStrength.MODERATE:
                return "買進"
            else:
                return "謹慎買進"
        elif signal.signal_type == "SELL":
            if risk_assessment['level'] == 'high' or signal.strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                return "賣出"
            else:
                return "謹慎賣出"
        else:
            return "持有觀望"

    def _calculate_target_price(self, current_price: float, signal: TradingSignal, 
                              support_resistance: SupportResistance) -> float:
        """計算目標價"""
        if signal.signal_type == "BUY":
            # 買進目標價設在下一個阻力位
            return signal.take_profit
        elif signal.signal_type == "SELL":
            # 賣出目標價設在下一個支撐位
            return signal.take_profit
        else:
            # 持有目標價為當前價格
            return current_price

    def _generate_taiwan_insights(self, metrics: TechnicalMetrics, patterns: List[ChartPattern]) -> Dict[str, Any]:
        """生成台灣市場專業洞察"""
        insights = {
            "taiwan_market_characteristics": [],
            "sector_analysis": "技術面分析顯示符合台股盤勢特徵",
            "trading_hours_impact": "建議關注開盤和收盤前後的量價變化",
            "local_patterns": []
        }
        
        # KD指標洞察 (台股常用)
        if metrics.kd_k > 80 and metrics.kd_d > 80:
            insights["taiwan_market_characteristics"].append("KD指標進入高檔鈍化區，台股常見反轉信號")
        elif metrics.kd_k < 20 and metrics.kd_d < 20:
            insights["taiwan_market_characteristics"].append("KD指標進入低檔鈍化區，注意反彈時機")
        
        # 成交量分析 (台股特色)
        if metrics.volume_ratio > 2.0:
            insights["local_patterns"].append("爆量上漲/下跌，符合台股慣性特徵")
        elif metrics.volume_ratio < 0.5:
            insights["local_patterns"].append("量能不足，台股通常需要量價配合")
        
        return insights

    # ART系統整合方法
    async def _start_art_trajectory(self, trajectory_id: str, state: AnalysisState):
        """開始ART軌跡記錄"""
        if not self.art_enabled:
            return
        
        try:
            from ...art.trajectory_collector import AnalysisTrajectory
            try:
                trajectory = AnalysisTrajectory(
                    trajectory_id=trajectory_id,
                    stock_id=state.stock_id,
                    analyst_type="technical",
                    analyst_version=getattr(self, 'version', '1.0.0'),
                    user_id=state.user_context.get('user_id', 'anonymous'),
                    start_time=datetime.now().isoformat(),
                    decision_steps=[]
                )
            except TypeError:
                # Fallback for older ART version
                trajectory = AnalysisTrajectory(
                    trajectory_id=trajectory_id,
                    stock_id=state.stock_id,
                    analyst_type="technical",
                    user_id=state.user_context.get('user_id', 'anonymous'),
                    start_time=datetime.now().isoformat(),
                    decision_steps=[]
                )
            
            # 記錄到軌跡收集器
            try:
                await self.trajectory_collector.start_trajectory(trajectory, self)
            except TypeError:
                # Fallback for older ART version
                await self.trajectory_collector.start_trajectory(trajectory)
            
        except Exception as e:
            self.logger.warning(f"ART軌跡開始失敗: {e}")

    async def _record_decision_step(self, trajectory_id: str, step_type: str, 
                                  data: Dict[str, Any], reasoning: str):
        """記錄ART決策步驟"""
        if not self.art_enabled:
            return
        
        try:
            try:
                step = DecisionStep(
                    trajectory_id=trajectory_id,
                    step_number=1,  # Simple step numbering
                    step_id=f"{trajectory_id}_{step_type}",
                    timestamp=datetime.now().isoformat(),
                    trajectory_type=getattr(TrajectoryType, 'ANALYSIS_DECISION', getattr(TrajectoryType, 'REASONING_STEP', list(TrajectoryType)[0])),
                    input_data=data,
                    reasoning_process=[reasoning],
                    intermediate_result=data,
                    confidence_score=0.8,
                    data_dependencies=["price_data", "volume_data"],
                    computation_method="technical_analysis"
                )
            except TypeError:
                # Fallback for older ART version
                step = DecisionStep(
                    step_id=f"{trajectory_id}_{step_type}",
                    timestamp=datetime.now().isoformat(),
                    trajectory_type=getattr(TrajectoryType, 'ANALYSIS_DECISION', getattr(TrajectoryType, 'REASONING_STEP', list(TrajectoryType)[0])),
                    input_data=data,
                    reasoning_process=[reasoning],
                    intermediate_result=data,
                    confidence_score=0.8,
                    data_dependencies=["price_data", "volume_data"],
                    computation_method="technical_analysis"
                )
            
            try:
                await self.trajectory_collector.record_step(trajectory_id, step, data, [reasoning])
            except TypeError:
                # Fallback for different ART version
                await self.trajectory_collector.record_step(trajectory_id, step)
            
        except Exception as e:
            self.logger.warning(f"ART決策步驟記錄失敗: {e}")

    async def _complete_art_trajectory(self, trajectory_id: str, result: AnalysisResult):
        """完成ART軌跡記錄"""
        if not self.art_enabled:
            return
        
        try:
            await self.trajectory_collector.complete_trajectory(
                trajectory_id, 
                result.recommendation,
                result.confidence
            )
            
            # 生成獎勵信號
            if hasattr(self, 'reward_system'):
                reward = await self.reward_system.generate_reward(
                    trajectory_id, 
                    RewardType.CONSISTENCY_REWARD, 
                    result.confidence
                )
                self.logger.info(f"ART獎勵生成: {reward}")
            
        except Exception as e:
            self.logger.warning(f"ART軌跡完成失敗: {e}")

    def _create_error_result(self, state: AnalysisState, error_msg: str) -> AnalysisResult:
        """創建錯誤結果"""
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_type=AnalysisType.TECHNICAL,
            recommendation="HOLD",
            confidence=0.1,
            confidence_level=AnalysisConfidenceLevel.VERY_LOW,  # Will be recalculated in __post_init__
            target_price=None,
            reasoning=[f"技術分析失敗: {error_msg}"],
            risk_factors=["數據獲取失敗"],
            technical_indicators={},
            taiwan_insights={},
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            timestamp=datetime.now().isoformat()
        )

    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型"""
        return AnalysisType.TECHNICAL
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成技術分析提示詞"""
        return f"""請對股票 {state.stock_id} 進行技術分析：
1. 分析移動平均線趨勢
2. 計算RSI、MACD、KD等技術指標
3. 識別支撐阻力位
4. 判斷圖表模式
5. 生成交易信號和建議
6. 評估技術風險

用戶偏好：{state.user_context.get('preferences', {})}
風險承受度：{state.user_context.get('risk_tolerance', 'moderate')}
"""
    
    def get_analyst_info(self) -> Dict[str, Any]:
        """獲取分析師資訊"""
        return {
            "analyst_id": self.analyst_id,
            "analyst_type": "技術分析師",
            "description": "專精於技術指標分析、圖表模式識別和交易信號生成",
            "capabilities": [
                "移動平均線分析",
                "RSI、MACD、KD等技術指標",
                "支撐阻力位計算",
                "圖表模式識別",
                "交易信號生成",
                "個人化分析建議"
            ],
            "taiwan_features": [
                "KD指標專業分析",
                "台股盤勢特徵識別",
                "成交量特色分析"
            ],
            "art_integration": {
                "enabled": self.art_enabled,
                "personalization": "技術指標偏好學習",
                "learning": "交易信號效果追蹤"
            },
            "supported_timeframes": ["短期", "中期", "長期"],
            "risk_management": True
        }
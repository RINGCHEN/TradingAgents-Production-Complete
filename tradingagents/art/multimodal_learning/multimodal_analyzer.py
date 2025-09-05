#!/usr/bin/env python3
"""
Multi-modal Analyzer - 多模態分析器
天工 (TianGong) - 統一的多模態智能分析協調器

此模組提供：
1. 多模態組件的統一協調
2. 智能分析流程管理
3. 結果整合和評分
4. 性能優化和緩存
5. 實時分析調整機制
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
import json
import time
import uuid
from collections import defaultdict, deque

from .multimodal_data_integrator import (
    MultiModalDataIntegrator, 
    DataModality, 
    IntegrationStrategy,
    ModalityData,
    IntegrationResult
)
from .text_processor import TextProcessor, TextAnalysisType, SentimentResult
from .time_series_fusion import TimeSeriesFusion, FusionMethod, TemporalAlignment
from .feature_fusion_engine import FeatureFusionEngine, FusionAlgorithm

class AnalysisMode(Enum):
    """分析模式"""
    REAL_TIME = "real_time"           # 實時分析
    BATCH = "batch"                   # 批次分析
    STREAMING = "streaming"           # 流式分析
    SCHEDULED = "scheduled"           # 定時分析
    TRIGGERED = "triggered"           # 觸發式分析

@dataclass
class ConfidenceMetrics:
    """信心度指標"""
    overall_confidence: float = 0.0
    data_quality_score: float = 0.0
    model_reliability: float = 0.0
    temporal_consistency: float = 0.0
    cross_modal_agreement: float = 0.0
    historical_accuracy: float = 0.0
    
    def calculate_weighted_confidence(self) -> float:
        """計算加權信心度"""
        weights = {
            'overall': 0.3,
            'data_quality': 0.2,
            'model_reliability': 0.2,
            'temporal_consistency': 0.1,
            'cross_modal_agreement': 0.1,
            'historical_accuracy': 0.1
        }
        
        return (
            self.overall_confidence * weights['overall'] +
            self.data_quality_score * weights['data_quality'] +
            self.model_reliability * weights['model_reliability'] +
            self.temporal_consistency * weights['temporal_consistency'] +
            self.cross_modal_agreement * weights['cross_modal_agreement'] +
            self.historical_accuracy * weights['historical_accuracy']
        )

@dataclass
class MultiModalResult:
    """多模態分析結果"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    # 分析結果
    recommendation: str = "neutral"  # positive/negative/neutral/hold
    confidence_metrics: ConfidenceMetrics = field(default_factory=ConfidenceMetrics)
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    
    # 多模態特徵
    integrated_features: Dict[str, Any] = field(default_factory=dict)
    modality_contributions: Dict[DataModality, float] = field(default_factory=dict)
    
    # 詳細分析
    sentiment_analysis: Optional[SentimentResult] = None
    technical_signals: Dict[str, float] = field(default_factory=dict)
    fundamental_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 元數據
    processing_time: float = 0.0
    data_sources: List[str] = field(default_factory=list)
    analysis_version: str = "1.0.0"
    error_messages: List[str] = field(default_factory=list)

class MultiModalAnalyzer:
    """多模態分析器主控組件"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心組件
        self._init_core_components()
        
        # 分析配置
        self.analysis_mode = AnalysisMode(
            self.config.get('analysis_mode', 'real_time')
        )
        self.batch_size = self.config.get('batch_size', 32)
        self.max_workers = self.config.get('max_workers', 4)
        
        # 緩存和性能配置
        self.enable_caching = self.config.get('cache_enabled', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)
        self.analysis_cache: Dict[str, Tuple[MultiModalResult, float]] = {}
        
        # 結果歷史記錄
        self.analysis_history: deque = deque(maxlen=1000)
        self.performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # 實時調整參數
        self.adaptive_thresholds = {
            'confidence_threshold': 0.7,
            'risk_tolerance': 0.5,
            'agreement_threshold': 0.6
        }
        
        # 回調函數
        self.result_callbacks: List[Callable] = []
        
        self.logger.info("MultiModalAnalyzer initialized")
    
    def _init_core_components(self):
        """初始化核心組件"""
        try:
            # 數據整合器
            integrator_config = self.config.get('data_integration', {})
            self.data_integrator = MultiModalDataIntegrator(integrator_config)
            
            # 文本處理器
            text_config = self.config.get('text_processing', {})
            self.text_processor = TextProcessor(text_config)
            
            # 時間序列融合器
            ts_config = self.config.get('time_series', {})
            self.time_series_fusion = TimeSeriesFusion(ts_config)
            
            # 特徵融合引擎
            fusion_config = self.config.get('feature_fusion', {})
            self.feature_fusion_engine = FeatureFusionEngine(fusion_config)
            
            self.logger.info("所有核心組件初始化成功")
            
        except Exception as e:
            self.logger.error(f"核心組件初始化失敗: {e}")
            raise
    
    async def analyze_investment_target(
        self,
        target_symbol: str,
        data_inputs: Dict[DataModality, Any],
        user_context: Dict[str, Any] = None,
        analysis_options: Dict[str, Any] = None
    ) -> MultiModalResult:
        """
        分析投資標的
        
        Args:
            target_symbol: 投資標的代碼
            data_inputs: 各模態的數據輸入
            user_context: 用戶上下文信息
            analysis_options: 分析選項
            
        Returns:
            多模態分析結果
        """
        start_time = time.time()
        result = MultiModalResult()
        
        try:
            # 檢查緩存
            if self.enable_caching:
                cached_result = await self._check_analysis_cache(
                    target_symbol, data_inputs, user_context
                )
                if cached_result:
                    return cached_result
            
            # 第一階段：數據整合
            integration_result = await self._integrate_multimodal_data(
                target_symbol, data_inputs
            )
            
            if not integration_result.alignment_success:
                result.error_messages.extend(integration_result.error_messages)
                return result
            
            # 第二階段：特徵提取和融合
            fused_features = await self._extract_and_fuse_features(
                integration_result, user_context
            )
            
            # 第三階段：智能分析
            analysis_results = await self._perform_intelligent_analysis(
                fused_features, target_symbol, user_context
            )
            
            # 第四階段：結果整合和評估
            final_result = await self._integrate_analysis_results(
                analysis_results, integration_result, user_context
            )
            
            # 第五階段：信心度評估
            confidence_metrics = await self._calculate_confidence_metrics(
                final_result, integration_result
            )
            
            # 組裝最終結果
            result.recommendation = final_result.get('recommendation', 'neutral')
            result.confidence_metrics = confidence_metrics
            result.risk_assessment = final_result.get('risk_assessment', {})
            result.integrated_features = fused_features
            result.modality_contributions = integration_result.modality_contributions
            result.technical_signals = final_result.get('technical_signals', {})
            result.fundamental_metrics = final_result.get('fundamental_metrics', {})
            result.sentiment_analysis = final_result.get('sentiment_analysis')
            result.data_sources = list(data_inputs.keys())
            
            # 緩存結果
            if self.enable_caching:
                await self._cache_analysis_result(
                    target_symbol, data_inputs, user_context, result
                )
            
            # 記錄歷史
            self.analysis_history.append(result)
            
            # 執行回調函數
            await self._execute_result_callbacks(result)
            
            self.logger.info(f"分析完成: {target_symbol}, 推薦: {result.recommendation}")
            
        except Exception as e:
            self.logger.error(f"分析過程失敗: {e}")
            result.error_messages.append(str(e))
        
        finally:
            result.processing_time = time.time() - start_time
            self.performance_metrics['processing_time'].append(result.processing_time)
        
        return result
    
    async def _integrate_multimodal_data(
        self,
        target_symbol: str,
        data_inputs: Dict[DataModality, Any]
    ) -> IntegrationResult:
        """整合多模態數據"""
        try:
            # 添加各模態數據到整合器
            for modality, data in data_inputs.items():
                await self.data_integrator.add_modality_data(
                    modality=modality,
                    data=data,
                    source=target_symbol,
                    metadata={'symbol': target_symbol, 'timestamp': time.time()}
                )
            
            # 執行數據整合
            integration_result = await self.data_integrator.integrate_multimodal_data(
                target_modalities=list(data_inputs.keys())
            )
            
            return integration_result
            
        except Exception as e:
            self.logger.error(f"多模態數據整合失敗: {e}")
            result = IntegrationResult()
            result.alignment_success = False
            result.error_messages.append(str(e))
            return result
    
    async def _extract_and_fuse_features(
        self,
        integration_result: IntegrationResult,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取和融合特徵"""
        try:
            # 準備特徵融合的輸入
            feature_groups = {}
            
            # 從整合結果中提取特徵組
            if integration_result.integrated_features:
                for feature_name, feature_value in integration_result.integrated_features.items():
                    if isinstance(feature_value, (int, float)):
                        group_name = self._categorize_feature(feature_name)
                        if group_name not in feature_groups:
                            feature_groups[group_name] = {}
                        feature_groups[group_name][feature_name] = feature_value
            
            # 如果沒有足夠的特徵，返回基本特徵
            if not feature_groups:
                return {
                    'basic_features': integration_result.integrated_features,
                    'fusion_quality': 0.5
                }
            
            # 執行特徵融合
            fusion_result = await self.feature_fusion_engine.fuse_feature_groups(
                feature_groups=feature_groups,
                user_preferences=user_context or {}
            )
            
            return {
                'fused_features': fusion_result.fused_features,
                'feature_importance': fusion_result.feature_importance,
                'fusion_weights': fusion_result.fusion_weights,
                'fusion_quality': fusion_result.fusion_quality
            }
            
        except Exception as e:
            self.logger.error(f"特徵提取和融合失敗: {e}")
            return {
                'basic_features': integration_result.integrated_features,
                'fusion_quality': 0.0,
                'error': str(e)
            }
    
    def _categorize_feature(self, feature_name: str) -> str:
        """將特徵分類到不同組別"""
        feature_name_lower = feature_name.lower()
        
        if any(keyword in feature_name_lower for keyword in ['price', 'volume', 'market']):
            return 'market_features'
        elif any(keyword in feature_name_lower for keyword in ['sentiment', 'text', 'news']):
            return 'sentiment_features'
        elif any(keyword in feature_name_lower for keyword in ['technical', 'indicator', 'signal']):
            return 'technical_features'
        elif any(keyword in feature_name_lower for keyword in ['fundamental', 'financial', 'ratio']):
            return 'fundamental_features'
        else:
            return 'other_features'
    
    async def _perform_intelligent_analysis(
        self,
        fused_features: Dict[str, Any],
        target_symbol: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """執行智能分析"""
        analysis_results = {
            'recommendation': 'neutral',
            'confidence': 0.5,
            'risk_assessment': {},
            'technical_signals': {},
            'fundamental_metrics': {},
            'sentiment_analysis': None
        }
        
        try:
            # 技術分析
            if 'technical_features' in fused_features:
                technical_analysis = await self._analyze_technical_signals(
                    fused_features['technical_features']
                )
                analysis_results['technical_signals'] = technical_analysis
            
            # 基本面分析
            if 'fundamental_features' in fused_features:
                fundamental_analysis = await self._analyze_fundamental_metrics(
                    fused_features['fundamental_features']
                )
                analysis_results['fundamental_metrics'] = fundamental_analysis
            
            # 情感分析
            if 'sentiment_features' in fused_features:
                sentiment_analysis = await self._analyze_sentiment_signals(
                    fused_features['sentiment_features']
                )
                analysis_results['sentiment_analysis'] = sentiment_analysis
            
            # 市場分析
            if 'market_features' in fused_features:
                market_analysis = await self._analyze_market_signals(
                    fused_features['market_features']
                )
                analysis_results['market_signals'] = market_analysis
            
            # 綜合決策
            final_recommendation = await self._make_integrated_decision(
                analysis_results, user_context
            )
            
            analysis_results.update(final_recommendation)
            
        except Exception as e:
            self.logger.error(f"智能分析失敗: {e}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    async def _analyze_technical_signals(self, technical_features: Dict[str, Any]) -> Dict[str, float]:
        """分析技術指標信號"""
        signals = {}
        
        try:
            # RSI信號
            if 'rsi' in technical_features:
                rsi = technical_features['rsi']
                if rsi > 70:
                    signals['rsi_signal'] = -0.8  # 超買
                elif rsi < 30:
                    signals['rsi_signal'] = 0.8   # 超賣
                else:
                    signals['rsi_signal'] = 0.0   # 中性
            
            # 移動平均信號
            if 'ma_short' in technical_features and 'ma_long' in technical_features:
                ma_short = technical_features['ma_short']
                ma_long = technical_features['ma_long']
                ma_ratio = ma_short / ma_long if ma_long != 0 else 1.0
                
                if ma_ratio > 1.02:
                    signals['ma_signal'] = 0.6   # 短期均線上穿
                elif ma_ratio < 0.98:
                    signals['ma_signal'] = -0.6  # 短期均線下穿
                else:
                    signals['ma_signal'] = 0.0
            
            # MACD信號
            if 'macd' in technical_features and 'macd_signal' in technical_features:
                macd = technical_features['macd']
                macd_signal = technical_features['macd_signal']
                
                if macd > macd_signal:
                    signals['macd_signal'] = 0.5  # 金叉
                else:
                    signals['macd_signal'] = -0.5 # 死叉
            
        except Exception as e:
            self.logger.warning(f"技術分析失敗: {e}")
        
        return signals
    
    async def _analyze_fundamental_metrics(self, fundamental_features: Dict[str, Any]) -> Dict[str, float]:
        """分析基本面指標"""
        metrics = {}
        
        try:
            # P/E比分析
            if 'pe_ratio' in fundamental_features:
                pe = fundamental_features['pe_ratio']
                if pe < 15:
                    metrics['valuation_score'] = 0.8   # 低估
                elif pe > 25:
                    metrics['valuation_score'] = -0.6  # 高估
                else:
                    metrics['valuation_score'] = 0.0   # 合理
            
            # ROE分析
            if 'roe' in fundamental_features:
                roe = fundamental_features['roe']
                if roe > 0.15:
                    metrics['profitability_score'] = 0.8  # 高獲利能力
                elif roe < 0.05:
                    metrics['profitability_score'] = -0.6 # 低獲利能力
                else:
                    metrics['profitability_score'] = 0.2  # 普通獲利能力
            
            # 財務健康度
            if 'debt_ratio' in fundamental_features:
                debt_ratio = fundamental_features['debt_ratio']
                if debt_ratio < 0.3:
                    metrics['financial_health'] = 0.6  # 財務健康
                elif debt_ratio > 0.6:
                    metrics['financial_health'] = -0.8 # 財務風險
                else:
                    metrics['financial_health'] = 0.0  # 中等風險
            
        except Exception as e:
            self.logger.warning(f"基本面分析失敗: {e}")
        
        return metrics
    
    async def _analyze_sentiment_signals(self, sentiment_features: Dict[str, Any]) -> SentimentResult:
        """分析情感信號"""
        try:
            # 如果有情感分數特徵
            if 'sentiment_score' in sentiment_features:
                sentiment_score = sentiment_features['sentiment_score']
                confidence = sentiment_features.get('confidence', 0.7)
                
                if sentiment_score > 0.1:
                    label = "positive"
                elif sentiment_score < -0.1:
                    label = "negative"
                else:
                    label = "neutral"
                
                return SentimentResult(
                    sentiment_score=sentiment_score,
                    sentiment_label=label,
                    confidence=confidence,
                    analysis_method="multimodal_fusion"
                )
            
            # 如果有文本數據
            elif 'text_content' in sentiment_features:
                text_content = sentiment_features['text_content']
                return await self.text_processor.analyze_sentiment(text_content)
            
        except Exception as e:
            self.logger.warning(f"情感分析失敗: {e}")
        
        return SentimentResult(
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.0,
            analysis_method="error"
        )
    
    async def _analyze_market_signals(self, market_features: Dict[str, Any]) -> Dict[str, float]:
        """分析市場信號"""
        signals = {}
        
        try:
            # 成交量分析
            if 'volume' in market_features and 'avg_volume' in market_features:
                volume = market_features['volume']
                avg_volume = market_features['avg_volume']
                
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
                if volume_ratio > 1.5:
                    signals['volume_signal'] = 0.6  # 放量
                elif volume_ratio < 0.5:
                    signals['volume_signal'] = -0.4 # 縮量
                else:
                    signals['volume_signal'] = 0.0  # 正常
            
            # 價格波動性
            if 'volatility' in market_features:
                volatility = market_features['volatility']
                if volatility > 0.3:
                    signals['volatility_signal'] = -0.5 # 高波動風險
                elif volatility < 0.1:
                    signals['volatility_signal'] = 0.3  # 低波動穩定
                else:
                    signals['volatility_signal'] = 0.0  # 正常波動
            
        except Exception as e:
            self.logger.warning(f"市場信號分析失敗: {e}")
        
        return signals
    
    async def _make_integrated_decision(
        self,
        analysis_results: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """做出整合決策"""
        decision = {
            'recommendation': 'neutral',
            'confidence': 0.5,
            'risk_assessment': {
                'overall_risk': 0.5,
                'technical_risk': 0.5,
                'fundamental_risk': 0.5,
                'market_risk': 0.5
            }
        }
        
        try:
            # 收集各種信號
            signals = []
            weights = []
            
            # 技術信號
            if 'technical_signals' in analysis_results:
                tech_signals = analysis_results['technical_signals']
                if tech_signals:
                    avg_tech_signal = np.mean(list(tech_signals.values()))
                    signals.append(avg_tech_signal)
                    weights.append(0.3)
            
            # 基本面信號
            if 'fundamental_metrics' in analysis_results:
                fund_metrics = analysis_results['fundamental_metrics']
                if fund_metrics:
                    avg_fund_signal = np.mean(list(fund_metrics.values()))
                    signals.append(avg_fund_signal)
                    weights.append(0.4)
            
            # 情感信號
            if 'sentiment_analysis' in analysis_results:
                sentiment = analysis_results['sentiment_analysis']
                if sentiment and hasattr(sentiment, 'sentiment_score'):
                    signals.append(sentiment.sentiment_score)
                    weights.append(0.2)
            
            # 市場信號
            if 'market_signals' in analysis_results:
                market_signals = analysis_results['market_signals']
                if market_signals:
                    avg_market_signal = np.mean(list(market_signals.values()))
                    signals.append(avg_market_signal)
                    weights.append(0.1)
            
            # 計算加權綜合信號
            if signals and weights:
                weights = np.array(weights)
                weights = weights / np.sum(weights)  # 標準化權重
                weighted_signal = np.average(signals, weights=weights)
                
                # 確定推薦
                if weighted_signal > 0.3:
                    decision['recommendation'] = 'positive'
                    decision['confidence'] = min(abs(weighted_signal), 0.9)
                elif weighted_signal < -0.3:
                    decision['recommendation'] = 'negative'
                    decision['confidence'] = min(abs(weighted_signal), 0.9)
                else:
                    decision['recommendation'] = 'neutral'
                    decision['confidence'] = 0.5
            
            # 風險評估
            decision['risk_assessment'] = await self._assess_comprehensive_risk(
                analysis_results
            )
            
        except Exception as e:
            self.logger.error(f"整合決策失敗: {e}")
        
        return decision
    
    async def _assess_comprehensive_risk(self, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """綜合風險評估"""
        risk_assessment = {
            'overall_risk': 0.5,
            'technical_risk': 0.5,
            'fundamental_risk': 0.5,
            'market_risk': 0.5,
            'sentiment_risk': 0.5
        }
        
        try:
            # 技術風險
            if 'technical_signals' in analysis_results:
                tech_signals = analysis_results['technical_signals']
                if tech_signals:
                    signal_variance = np.var(list(tech_signals.values()))
                    risk_assessment['technical_risk'] = min(signal_variance * 2, 1.0)
            
            # 基本面風險
            if 'fundamental_metrics' in analysis_results:
                fund_metrics = analysis_results['fundamental_metrics']
                if 'financial_health' in fund_metrics:
                    health_score = fund_metrics['financial_health']
                    risk_assessment['fundamental_risk'] = max(0, 0.5 - health_score)
            
            # 市場風險
            if 'market_signals' in analysis_results:
                market_signals = analysis_results['market_signals']
                if 'volatility_signal' in market_signals:
                    vol_signal = market_signals['volatility_signal']
                    risk_assessment['market_risk'] = max(0, -vol_signal)
            
            # 情感風險
            if 'sentiment_analysis' in analysis_results:
                sentiment = analysis_results['sentiment_analysis']
                if sentiment and hasattr(sentiment, 'confidence'):
                    sentiment_risk = 1.0 - sentiment.confidence
                    risk_assessment['sentiment_risk'] = sentiment_risk
            
            # 綜合風險
            risk_values = [v for k, v in risk_assessment.items() if k != 'overall_risk']
            risk_assessment['overall_risk'] = np.mean(risk_values)
            
        except Exception as e:
            self.logger.warning(f"風險評估失敗: {e}")
        
        return risk_assessment
    
    async def _integrate_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        integration_result: IntegrationResult,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """整合分析結果"""
        try:
            integrated_result = analysis_results.copy()
            
            # 添加數據整合品質信息
            integrated_result['integration_quality'] = integration_result.integration_quality
            integrated_result['modality_contributions'] = integration_result.modality_contributions
            
            # 用戶偏好調整
            if user_context:
                integrated_result = await self._apply_user_preferences(
                    integrated_result, user_context
                )
            
            return integrated_result
            
        except Exception as e:
            self.logger.error(f"結果整合失敗: {e}")
            return analysis_results
    
    async def _apply_user_preferences(
        self,
        analysis_result: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """應用用戶偏好"""
        try:
            # 風險偏好調整
            risk_tolerance = user_context.get('risk_tolerance', 0.5)
            if 'risk_assessment' in analysis_result:
                overall_risk = analysis_result['risk_assessment']['overall_risk']
                
                # 如果用戶風險承受度低，提高風險評估的影響
                if risk_tolerance < 0.3 and overall_risk > 0.6:
                    if analysis_result['recommendation'] == 'positive':
                        analysis_result['recommendation'] = 'neutral'
                        analysis_result['confidence'] *= 0.8
            
            # 投資期間偏好
            investment_horizon = user_context.get('investment_horizon', 'medium')
            if investment_horizon == 'short':
                # 短期投資更重視技術分析
                if 'technical_signals' in analysis_result:
                    analysis_result['technical_weight'] = 0.6
            elif investment_horizon == 'long':
                # 長期投資更重視基本面
                if 'fundamental_metrics' in analysis_result:
                    analysis_result['fundamental_weight'] = 0.6
            
            return analysis_result
            
        except Exception as e:
            self.logger.warning(f"用戶偏好應用失敗: {e}")
            return analysis_result
    
    async def _calculate_confidence_metrics(
        self,
        analysis_result: Dict[str, Any],
        integration_result: IntegrationResult
    ) -> ConfidenceMetrics:
        """計算信心度指標"""
        metrics = ConfidenceMetrics()
        
        try:
            # 整體信心度
            metrics.overall_confidence = analysis_result.get('confidence', 0.5)
            
            # 數據品質分數
            metrics.data_quality_score = integration_result.integration_quality
            
            # 模型可靠性（基於歷史表現）
            if self.performance_metrics['processing_time']:
                recent_times = self.performance_metrics['processing_time'][-10:]
                avg_time = np.mean(recent_times)
                # 處理時間越穩定，可靠性越高
                time_stability = 1.0 / (1.0 + np.std(recent_times))
                metrics.model_reliability = time_stability
            
            # 時間一致性
            if len(self.analysis_history) > 1:
                recent_results = list(self.analysis_history)[-5:]
                recommendations = [r.recommendation for r in recent_results]
                consistency = len(set(recommendations)) / len(recommendations)
                metrics.temporal_consistency = 1.0 - consistency
            
            # 跨模態一致性
            if integration_result.modality_contributions:
                contrib_values = list(integration_result.modality_contributions.values())
                if contrib_values:
                    contrib_variance = np.var(contrib_values)
                    metrics.cross_modal_agreement = max(0, 1.0 - contrib_variance)
            
            # 歷史準確性（簡化實現）
            metrics.historical_accuracy = 0.75  # 默認值，實際應基於回測結果
            
        except Exception as e:
            self.logger.warning(f"信心度計算失敗: {e}")
        
        return metrics
    
    async def _check_analysis_cache(
        self,
        target_symbol: str,
        data_inputs: Dict[DataModality, Any],
        user_context: Dict[str, Any]
    ) -> Optional[MultiModalResult]:
        """檢查分析緩存"""
        try:
            # 生成緩存鍵
            cache_key = self._generate_cache_key(target_symbol, data_inputs, user_context)
            
            if cache_key in self.analysis_cache:
                cached_result, cache_time = self.analysis_cache[cache_key]
                
                # 檢查緩存是否過期
                if time.time() - cache_time < self.cache_ttl:
                    self.logger.debug(f"使用緩存結果: {target_symbol}")
                    return cached_result
                else:
                    # 清除過期緩存
                    del self.analysis_cache[cache_key]
            
        except Exception as e:
            self.logger.warning(f"緩存檢查失敗: {e}")
        
        return None
    
    async def _cache_analysis_result(
        self,
        target_symbol: str,
        data_inputs: Dict[DataModality, Any],
        user_context: Dict[str, Any],
        result: MultiModalResult
    ):
        """緩存分析結果"""
        try:
            cache_key = self._generate_cache_key(target_symbol, data_inputs, user_context)
            self.analysis_cache[cache_key] = (result, time.time())
            
            # 清理過期緩存
            current_time = time.time()
            expired_keys = [
                key for key, (_, cache_time) in self.analysis_cache.items()
                if current_time - cache_time >= self.cache_ttl
            ]
            
            for key in expired_keys:
                del self.analysis_cache[key]
                
        except Exception as e:
            self.logger.warning(f"結果緩存失敗: {e}")
    
    def _generate_cache_key(
        self,
        target_symbol: str,
        data_inputs: Dict[DataModality, Any],
        user_context: Dict[str, Any]
    ) -> str:
        """生成緩存鍵"""
        try:
            # 簡化的緩存鍵生成
            key_components = [
                target_symbol,
                str(sorted(data_inputs.keys())),
                str(user_context.get('risk_tolerance', 0.5)) if user_context else "default"
            ]
            return "_".join(key_components)
        except:
            return f"{target_symbol}_{int(time.time())}"
    
    async def _execute_result_callbacks(self, result: MultiModalResult):
        """執行結果回調函數"""
        for callback in self.result_callbacks:
            try:
                await callback(result)
            except Exception as e:
                self.logger.warning(f"回調執行失敗: {e}")
    
    def add_result_callback(self, callback: Callable):
        """添加結果回調函數"""
        self.result_callbacks.append(callback)
    
    def remove_result_callback(self, callback: Callable):
        """移除結果回調函數"""
        if callback in self.result_callbacks:
            self.result_callbacks.remove(callback)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        try:
            return {
                'total_analyses': len(self.analysis_history),
                'cache_size': len(self.analysis_cache),
                'average_processing_time': np.mean(self.performance_metrics['processing_time']) if self.performance_metrics['processing_time'] else 0,
                'analysis_mode': self.analysis_mode.value,
                'core_components_status': {
                    'data_integrator': bool(self.data_integrator),
                    'text_processor': bool(self.text_processor),
                    'time_series_fusion': bool(self.time_series_fusion),
                    'feature_fusion_engine': bool(self.feature_fusion_engine)
                },
                'recent_recommendations': [
                    r.recommendation for r in list(self.analysis_history)[-10:]
                ] if self.analysis_history else []
            }
        except Exception as e:
            self.logger.error(f"統計信息獲取失敗: {e}")
            return {'error': str(e)}
    
    async def update_adaptive_thresholds(self, performance_feedback: Dict[str, float]):
        """更新自適應閾值"""
        try:
            # 基於性能反饋調整閾值
            accuracy = performance_feedback.get('accuracy', 0.5)
            
            if accuracy > 0.8:
                # 高準確率，可以降低信心度閾值
                self.adaptive_thresholds['confidence_threshold'] *= 0.95
            elif accuracy < 0.6:
                # 低準確率，提高信心度閾值
                self.adaptive_thresholds['confidence_threshold'] *= 1.05
            
            # 限制閾值範圍
            self.adaptive_thresholds['confidence_threshold'] = max(
                0.5, min(0.9, self.adaptive_thresholds['confidence_threshold'])
            )
            
            self.logger.info(f"已更新自適應閾值: {self.adaptive_thresholds}")
            
        except Exception as e:
            self.logger.error(f"閾值更新失敗: {e}")
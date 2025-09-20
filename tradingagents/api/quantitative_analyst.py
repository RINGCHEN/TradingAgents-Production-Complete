"""
量化分析師 - 使用數學模型和統計方法進行投資分析
專注於數據驅動的投資策略和風險量化評估
"""

import json
import asyncio
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class QuantitativeAnalyst:
    """量化分析師"""
    
    def __init__(self):
        self.analyst_id = "quantitative_analyst"
        self.name = "量化分析師"
        self.description = "運用先進數學模型、統計分析和機器學習技術，提供基於數據的精確投資決策"
        self.specialties = [
            "統計套利策略",
            "因子模型分析",
            "風險價值計算(VaR)",
            "動態對沖策略",
            "高頻交易信號",
            "投資組合優化",
            "量化回測驗證"
        ]
        self.version = "1.0.0"

    async def analyze_stock(self, symbol: str, user_tier: str = "free") -> Dict[str, Any]:
        """執行量化分析"""
        try:
            logger.info(f"量化分析師開始分析 {symbol}")
            
            # 模擬分析延遲
            await asyncio.sleep(3)
            
            # 獲取量化數據
            quant_data = await self._get_quantitative_data(symbol)
            
            # 執行量化分析
            analysis_result = {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "analysis_type": "quantitative",
                "timestamp": datetime.now().isoformat(),
                "statistical_metrics": quant_data["statistical_metrics"],
                "factor_analysis": quant_data["factor_analysis"],
                "risk_metrics": quant_data["risk_metrics"],
                "valuation_models": quant_data["valuation_models"],
                "momentum_indicators": quant_data["momentum_indicators"],
                "mean_reversion": quant_data["mean_reversion"],
                "volatility_analysis": quant_data["volatility_analysis"],
                "correlation_analysis": quant_data["correlation_analysis"],
                "trading_signals": self._generate_trading_signals(quant_data, user_tier),
                "key_insights": self._generate_insights(quant_data, user_tier),
                "recommendation": self._generate_recommendation(quant_data),
                "confidence_level": self._calculate_confidence(quant_data),
                "risk_assessment": self._assess_quantitative_risk(quant_data),
                "portfolio_allocation": self._suggest_allocation(quant_data, user_tier),
                "tier_limitations": self._get_tier_limitations(user_tier)
            }
            
            logger.info(f"量化分析師完成分析 {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"量化分析師分析失敗 {symbol}: {str(e)}")
            return {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "error": f"分析過程發生錯誤: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _get_quantitative_data(self, symbol: str) -> Dict[str, Any]:
        """獲取量化分析所需數據"""
        import random
        
        # 模擬價格數據生成統計指標
        returns = [random.gauss(0.001, 0.02) for _ in range(252)]  # 一年的日報酬率
        prices = [100]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
            
        return {
            "statistical_metrics": {
                "mean_return": np.mean(returns),
                "volatility": np.std(returns) * np.sqrt(252),  # 年化波動率
                "sharpe_ratio": (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252)),
                "skewness": self._calculate_skewness(returns),
                "kurtosis": self._calculate_kurtosis(returns),
                "max_drawdown": self._calculate_max_drawdown(prices),
                "calmar_ratio": (np.mean(returns) * 252) / abs(self._calculate_max_drawdown(prices)),
                "sortino_ratio": self._calculate_sortino_ratio(returns)
            },
            "factor_analysis": {
                "beta": round(random.uniform(0.6, 1.8), 3),
                "alpha": round(random.uniform(-0.05, 0.15), 4),
                "size_factor": round(random.uniform(-0.3, 0.5), 3),
                "value_factor": round(random.uniform(-0.4, 0.6), 3),
                "momentum_factor": round(random.uniform(-0.5, 0.7), 3),
                "quality_factor": round(random.uniform(-0.2, 0.8), 3),
                "r_squared": round(random.uniform(0.3, 0.9), 3),
                "information_ratio": round(random.uniform(-0.5, 1.2), 3)
            },
            "risk_metrics": {
                "var_95": round(random.uniform(-0.08, -0.02), 4),  # 95% VaR
                "var_99": round(random.uniform(-0.12, -0.04), 4),  # 99% VaR
                "expected_shortfall": round(random.uniform(-0.15, -0.05), 4),
                "tracking_error": round(random.uniform(0.05, 0.25), 4),
                "downside_deviation": round(random.uniform(0.08, 0.20), 4),
                "ulcer_index": round(random.uniform(2, 15), 2),
                "risk_adjusted_return": round(random.uniform(0.5, 2.5), 3)
            },
            "valuation_models": {
                "dcf_fair_value": round(random.uniform(80, 120), 2),
                "capm_expected_return": round(random.uniform(0.06, 0.18), 4),
                "dividend_discount_model": round(random.uniform(85, 115), 2),
                "relative_valuation": {
                    "pe_percentile": round(random.uniform(10, 90), 1),
                    "pb_percentile": round(random.uniform(15, 85), 1),
                    "ev_ebitda_percentile": round(random.uniform(5, 95), 1)
                }
            },
            "momentum_indicators": {
                "price_momentum_1m": round(random.uniform(-0.15, 0.25), 4),
                "price_momentum_3m": round(random.uniform(-0.20, 0.30), 4),
                "price_momentum_6m": round(random.uniform(-0.25, 0.35), 4),
                "earnings_momentum": round(random.uniform(-0.30, 0.40), 4),
                "revision_momentum": round(random.uniform(-0.20, 0.30), 4),
                "relative_strength": round(random.uniform(20, 80), 1)
            },
            "mean_reversion": {
                "z_score": round(random.uniform(-2.5, 2.5), 2),
                "bollinger_position": round(random.uniform(0, 1), 3),
                "rsi_divergence": random.choice(["正乖離", "負乖離", "無明顯乖離"]),
                "mean_reversion_signal": random.choice(["強烈", "溫和", "無"])
            },
            "volatility_analysis": {
                "implied_volatility": round(random.uniform(0.15, 0.45), 4),
                "historical_volatility": round(random.uniform(0.12, 0.40), 4),
                "volatility_skew": round(random.uniform(-0.1, 0.2), 4),
                "volatility_regime": random.choice(["低波動", "中波動", "高波動"]),
                "garch_forecast": round(random.uniform(0.10, 0.35), 4)
            },
            "correlation_analysis": {
                "market_correlation": round(random.uniform(0.3, 0.9), 3),
                "sector_correlation": round(random.uniform(0.5, 0.95), 3),
                "factor_exposure": {
                    "growth": round(random.uniform(-0.5, 1.2), 3),
                    "value": round(random.uniform(-0.8, 0.8), 3),
                    "momentum": round(random.uniform(-0.6, 1.0), 3),
                    "size": round(random.uniform(-0.4, 0.6), 3)
                }
            }
        }

    def _calculate_skewness(self, returns: List[float]) -> float:
        """計算偏態"""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        n = len(returns)
        skewness = sum([(r - mean_return) ** 3 for r in returns]) / (n * std_return ** 3)
        return round(skewness, 3)

    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """計算峰態"""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        n = len(returns)
        kurtosis = sum([(r - mean_return) ** 4 for r in returns]) / (n * std_return ** 4) - 3
        return round(kurtosis, 3)

    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """計算最大回撤"""
        peak = prices[0]
        max_dd = 0
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        return round(max_dd, 4)

    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """計算Sortino比率"""
        mean_return = np.mean(returns)
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return float('inf')
        downside_std = np.std(downside_returns)
        return round((mean_return * 252) / (downside_std * np.sqrt(252)), 3)

    def _generate_trading_signals(self, quant_data: Dict, user_tier: str) -> Dict[str, Any]:
        """生成交易信號"""
        signals = {}
        
        # 基礎信號 (所有用戶)
        momentum = quant_data["momentum_indicators"]["price_momentum_3m"]
        mean_rev = quant_data["mean_reversion"]["z_score"]
        
        if momentum > 0.1 and mean_rev < -1:
            signals["momentum_signal"] = "STRONG_BUY"
        elif momentum > 0.05:
            signals["momentum_signal"] = "BUY"
        elif momentum < -0.1 and mean_rev > 1:
            signals["momentum_signal"] = "STRONG_SELL"
        else:
            signals["momentum_signal"] = "NEUTRAL"
            
        # 進階信號 (Gold以上)
        if user_tier in ["gold", "diamond"]:
            sharpe = quant_data["statistical_metrics"]["sharpe_ratio"]
            beta = quant_data["factor_analysis"]["beta"]
            
            if sharpe > 1.5 and beta < 1.2:
                signals["risk_adjusted_signal"] = "BUY"
            elif sharpe < 0.5 or beta > 1.8:
                signals["risk_adjusted_signal"] = "SELL"
            else:
                signals["risk_adjusted_signal"] = "NEUTRAL"
                
            # 波動率信號
            vol_regime = quant_data["volatility_analysis"]["volatility_regime"]
            if vol_regime == "低波動":
                signals["volatility_signal"] = "ACCUMULATE"
            elif vol_regime == "高波動":
                signals["volatility_signal"] = "REDUCE"
            else:
                signals["volatility_signal"] = "NEUTRAL"
                
        # 專業信號 (Diamond)
        if user_tier == "diamond":
            var_95 = abs(quant_data["risk_metrics"]["var_95"])
            factor_momentum = quant_data["factor_analysis"]["momentum_factor"]
            
            # 因子信號
            if factor_momentum > 0.3:
                signals["factor_signal"] = "MOMENTUM_BUY"
            elif factor_momentum < -0.3:
                signals["factor_signal"] = "MOMENTUM_SELL"
            else:
                signals["factor_signal"] = "FACTOR_NEUTRAL"
                
            # 風險調整信號
            if var_95 < 0.05:
                signals["risk_signal"] = "LOW_RISK_BUY"
            elif var_95 > 0.1:
                signals["risk_signal"] = "HIGH_RISK_REDUCE"
            else:
                signals["risk_signal"] = "RISK_NEUTRAL"
                
        return signals

    def _generate_insights(self, quant_data: Dict, user_tier: str) -> List[str]:
        """生成量化分析洞察"""
        insights = []
        
        sharpe = quant_data["statistical_metrics"]["sharpe_ratio"]
        vol = quant_data["statistical_metrics"]["volatility"]
        max_dd = quant_data["statistical_metrics"]["max_drawdown"]
        
        # 基礎洞察
        if sharpe > 1.5:
            insights.append("📈 Sharpe比率優秀，風險調整後報酬表現卓越")
        elif sharpe < 0.5:
            insights.append("⚠️ Sharpe比率偏低，風險報酬比不佳")
            
        if max_dd < 0.1:
            insights.append("🛡️ 最大回撤控制良好，下跌風險相對較小")
        elif max_dd > 0.3:
            insights.append("🔴 最大回撤較大，需要關注風險控制")
            
        # 進階洞察 (Gold以上)
        if user_tier in ["gold", "diamond"]:
            beta = quant_data["factor_analysis"]["beta"]
            alpha = quant_data["factor_analysis"]["alpha"]
            
            if alpha > 0.05:
                insights.append("💎 Alpha值顯著為正，具備超額報酬能力")
            elif alpha < -0.03:
                insights.append("📉 Alpha值為負，表現不如大盤")
                
            if beta > 1.3:
                insights.append("⚡ 高Beta係數，市場敏感度高，適合趨勢投資")
            elif beta < 0.7:
                insights.append("🔒 低Beta係數，防禦性較強，適合保守投資")
                
            # 因子分析
            momentum_factor = quant_data["factor_analysis"]["momentum_factor"]
            if momentum_factor > 0.5:
                insights.append("🚀 動能因子暴露度高，趨勢持續性強")
                
        # 專業洞察 (Diamond)
        if user_tier == "diamond":
            var_95 = abs(quant_data["risk_metrics"]["var_95"])
            es = abs(quant_data["risk_metrics"]["expected_shortfall"])
            
            insights.append(f"📊 95% VaR為{var_95:.2%}，預期極端損失風險評估")
            insights.append(f"⚠️ 預期虧損(ES)為{es:.2%}，尾部風險量化指標")
            
            skew = quant_data["statistical_metrics"]["skewness"]
            kurt = quant_data["statistical_metrics"]["kurtosis"]
            
            if skew < -0.5:
                insights.append("📉 負偏態分佈，下跌風險大於上漲潛力")
            elif skew > 0.5:
                insights.append("📈 正偏態分佈，上漲潛力大於下跌風險")
                
            if kurt > 3:
                insights.append("⚡ 高峰態特徵，極端價格變動機率較高")
                
        return insights

    def _generate_recommendation(self, quant_data: Dict) -> str:
        """生成量化投資建議"""
        sharpe = quant_data["statistical_metrics"]["sharpe_ratio"]
        momentum_3m = quant_data["momentum_indicators"]["price_momentum_3m"]
        z_score = quant_data["mean_reversion"]["z_score"]
        beta = quant_data["factor_analysis"]["beta"]
        
        score = 0
        
        # Sharpe比率評分
        if sharpe > 1.5:
            score += 2
        elif sharpe > 1.0:
            score += 1
        elif sharpe < 0.5:
            score -= 2
        elif sharpe < 0.8:
            score -= 1
            
        # 動能評分
        if momentum_3m > 0.15:
            score += 2
        elif momentum_3m > 0.05:
            score += 1
        elif momentum_3m < -0.15:
            score -= 2
        elif momentum_3m < -0.05:
            score -= 1
            
        # 均值回歸評分
        if abs(z_score) > 2:
            score += 1 if z_score < 0 else -1
            
        # Beta風險評分
        if beta > 1.5:
            score -= 1  # 高風險減分
            
        if score >= 4:
            return "STRONG_BUY"
        elif score >= 2:
            return "BUY"
        elif score <= -4:
            return "STRONG_SELL"
        elif score <= -2:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_confidence(self, quant_data: Dict) -> float:
        """計算分析信心度"""
        r_squared = quant_data["factor_analysis"]["r_squared"]
        data_quality = min(1.0, r_squared + 0.2)
        
        # 基於統計顯著性調整信心度
        sharpe = abs(quant_data["statistical_metrics"]["sharpe_ratio"])
        significance = min(1.0, sharpe / 2.0)
        
        confidence = (data_quality * 0.6 + significance * 0.4)
        return min(0.95, max(0.6, confidence))

    def _assess_quantitative_risk(self, quant_data: Dict) -> Dict[str, Any]:
        """評估量化風險"""
        var_95 = abs(quant_data["risk_metrics"]["var_95"])
        max_dd = quant_data["statistical_metrics"]["max_drawdown"]
        vol = quant_data["statistical_metrics"]["volatility"]
        
        if var_95 > 0.08 or max_dd > 0.25 or vol > 0.35:
            risk_level = "HIGH"
        elif var_95 > 0.05 or max_dd > 0.15 or vol > 0.25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        risk_factors = []
        if var_95 > 0.08:
            risk_factors.append("高VaR風險")
        if max_dd > 0.25:
            risk_factors.append("大幅回撤風險")
        if vol > 0.35:
            risk_factors.append("高波動風險")
            
        return {
            "risk_level": risk_level,
            "quantitative_risk_score": round(var_95 * 100 + max_dd * 50 + vol * 30, 2),
            "risk_factors": risk_factors or ["風險控制良好"],
            "recommended_position_size": self._calculate_position_size(quant_data)
        }

    def _calculate_position_size(self, quant_data: Dict) -> str:
        """建議倉位大小"""
        var_95 = abs(quant_data["risk_metrics"]["var_95"])
        sharpe = quant_data["statistical_metrics"]["sharpe_ratio"]
        
        # Kelly公式簡化版本
        if sharpe > 1.5 and var_95 < 0.05:
            return "25-30% (積極)"
        elif sharpe > 1.0 and var_95 < 0.08:
            return "15-20% (中等)"
        elif sharpe > 0.5:
            return "5-10% (保守)"
        else:
            return "0-5% (觀望)"

    def _suggest_allocation(self, quant_data: Dict, user_tier: str) -> Dict[str, Any]:
        """建議投資組合配置"""
        if user_tier == "free":
            return {"message": "升級至Gold可獲得詳細配置建議"}
            
        beta = quant_data["factor_analysis"]["beta"]
        sharpe = quant_data["statistical_metrics"]["sharpe_ratio"]
        correlation = quant_data["correlation_analysis"]["market_correlation"]
        
        allocation = {
            "core_position": "10-15%" if sharpe > 1.0 else "5-10%",
            "satellite_position": "3-5%" if beta < 1.2 else "1-3%",
            "diversification_benefit": "高" if correlation < 0.7 else "中" if correlation < 0.85 else "低",
            "rebalancing_frequency": "月度" if quant_data["statistical_metrics"]["volatility"] > 0.3 else "季度"
        }
        
        if user_tier == "diamond":
            allocation.update({
                "factor_tilt": self._recommend_factor_tilt(quant_data),
                "hedging_strategy": self._recommend_hedging(quant_data),
                "optimization_method": "Mean-Variance" if sharpe > 1.0 else "Risk-Parity"
            })
            
        return allocation

    def _recommend_factor_tilt(self, quant_data: Dict) -> Dict[str, str]:
        """推薦因子傾斜策略"""
        factors = quant_data["factor_analysis"]
        
        tilts = {}
        if factors["momentum_factor"] > 0.3:
            tilts["momentum"] = "增配"
        if factors["value_factor"] > 0.3:
            tilts["value"] = "增配"
        if factors["quality_factor"] > 0.5:
            tilts["quality"] = "增配"
            
        return tilts or {"balanced": "均衡配置"}

    def _recommend_hedging(self, quant_data: Dict) -> str:
        """推薦對沖策略"""
        beta = quant_data["factor_analysis"]["beta"]
        var_95 = abs(quant_data["risk_metrics"]["var_95"])
        
        if beta > 1.5 and var_95 > 0.08:
            return "建議使用ETF或期貨對沖系統性風險"
        elif var_95 > 0.1:
            return "考慮使用選擇權進行尾部風險對沖"
        else:
            return "當前風險水平可接受，無需特殊對沖"

    def _get_tier_limitations(self, user_tier: str) -> List[str]:
        """獲取用戶等級限制"""
        if user_tier == "free":
            return [
                "僅提供基礎統計指標",
                "不包含高級風險指標",
                "限制因子分析深度",
                "無法獲得投資組合優化建議"
            ]
        elif user_tier == "gold":
            return [
                "不包含完整因子暴露分析",
                "投資組合優化功能有限",
                "無高級對沖策略建議"
            ]
        else:  # diamond
            return []

    def get_analyst_info(self) -> Dict[str, Any]:
        """獲取分析師基本資訊"""
        return {
            "analyst_id": self.analyst_id,
            "name": self.name,
            "description": self.description,
            "specialties": self.specialties,
            "analyst_type": "quantitative_analyst",
            "version": self.version,
            "supported_analysis": [
                "statistical_analysis",
                "factor_modeling",
                "risk_metrics",
                "portfolio_optimization",
                "quantitative_signals"
            ]
        }

# 全局實例
quantitative_analyst = QuantitativeAnalyst()
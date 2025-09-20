"""
總體經濟分析師 - 專注於宏觀經濟環境對投資的影響分析
研究央行政策、經濟指標、國際情勢等對市場的影響
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MacroEconomicAnalyst:
    """總體經濟分析師"""
    
    def __init__(self):
        self.analyst_id = "macro_economic_analyst"
        self.name = "總體經濟分析師"
        self.description = "深度分析宏觀經濟環境、貨幣政策、國際情勢對投資市場的影響和機會"
        self.specialties = [
            "央行貨幣政策分析",
            "經濟週期判斷",
            "通脹預期評估",
            "國際貿易影響",
            "地緣政治風險",
            "經濟指標解讀",
            "產業景氣循環"
        ]
        self.version = "1.0.0"

    async def analyze_stock(self, symbol: str, user_tier: str = "free") -> Dict[str, Any]:
        """執行總體經濟分析"""
        try:
            logger.info(f"總體經濟分析師開始分析 {symbol}")
            
            # 模擬分析延遲
            await asyncio.sleep(2.5)
            
            # 獲取總經數據
            macro_data = await self._get_macro_economic_data(symbol)
            
            # 分析結果
            analysis_result = {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "analysis_type": "macro_economic",
                "timestamp": datetime.now().isoformat(),
                "economic_cycle": macro_data["economic_cycle"],
                "monetary_policy": macro_data["monetary_policy"],
                "inflation_analysis": macro_data["inflation_analysis"],
                "trade_environment": macro_data["trade_environment"],
                "geopolitical_risks": macro_data["geopolitical_risks"],
                "sector_impact": macro_data["sector_impact"],
                "currency_effects": macro_data["currency_effects"],
                "economic_indicators": macro_data["economic_indicators"],
                "policy_outlook": macro_data["policy_outlook"],
                "key_insights": self._generate_insights(macro_data, user_tier),
                "recommendation": self._generate_recommendation(macro_data),
                "confidence_level": self._calculate_confidence(macro_data),
                "risk_assessment": self._assess_macro_risk(macro_data),
                "timing_analysis": self._analyze_timing(macro_data, user_tier),
                "tier_limitations": self._get_tier_limitations(user_tier)
            }
            
            logger.info(f"總體經濟分析師完成分析 {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"總體經濟分析師分析失敗 {symbol}: {str(e)}")
            return {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "error": f"分析過程發生錯誤: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _get_macro_economic_data(self, symbol: str) -> Dict[str, Any]:
        """獲取總體經濟數據"""
        import random
        
        # 根據股票代號判斷產業（簡化版）
        sector = self._determine_sector(symbol)
        
        return {
            "economic_cycle": {
                "current_phase": random.choice(["復甦", "擴張", "高峰", "收縮", "衰退"]),
                "cycle_position": round(random.uniform(0.2, 0.9), 2),
                "duration_estimate": f"{random.randint(6, 24)}個月",
                "leading_indicators": {
                    "pmi": round(random.uniform(45, 60), 1),
                    "employment": round(random.uniform(3.5, 6.5), 1),
                    "consumer_confidence": round(random.uniform(80, 120), 1),
                    "yield_curve": random.choice(["正常", "平坦", "倒掛"])
                }
            },
            "monetary_policy": {
                "interest_rate_trend": random.choice(["升息週期", "降息週期", "維持不變"]),
                "current_rate": round(random.uniform(1.0, 5.5), 2),
                "fed_stance": random.choice(["鷹派", "鴿派", "中性"]),
                "qe_status": random.choice(["量化寬鬆", "量化緊縮", "暫停QE"]),
                "next_meeting": "2024-12-18",
                "rate_probability": {
                    "升息25bp": round(random.uniform(0, 70), 1),
                    "維持不變": round(random.uniform(20, 80), 1),
                    "降息25bp": round(random.uniform(0, 60), 1)
                }
            },
            "inflation_analysis": {
                "current_cpi": round(random.uniform(2.0, 6.0), 1),
                "core_cpi": round(random.uniform(1.8, 4.5), 1),
                "pce": round(random.uniform(1.5, 4.0), 1),
                "inflation_expectation": round(random.uniform(2.0, 4.0), 1),
                "trend": random.choice(["上升", "下降", "穩定"]),
                "fed_target_distance": round(random.uniform(-1.5, 2.5), 1)
            },
            "trade_environment": {
                "global_trade_growth": round(random.uniform(-2.0, 6.0), 1),
                "trade_tensions": random.choice(["低", "中", "高"]),
                "tariff_impact": random.choice(["正面", "負面", "中性"]),
                "supply_chain": random.choice(["順暢", "部分中斷", "嚴重中斷"]),
                "shipping_costs": random.choice(["正常", "偏高", "極高"]),
                "taiwan_export_outlook": random.choice(["強勁", "溫和", "疲弱"])
            },
            "geopolitical_risks": {
                "overall_risk_level": random.choice(["低", "中", "高", "極高"]),
                "regional_tensions": {
                    "us_china": random.choice(["緩和", "緊張", "升級"]),
                    "russia_ukraine": random.choice(["持續", "緩解", "惡化"]),
                    "middle_east": random.choice(["穩定", "動盪", "危機"])
                },
                "energy_security": random.choice(["穩定", "關注", "風險"]),
                "taiwan_specific": random.choice(["穩定", "關注", "緊張"])
            },
            "sector_impact": self._get_sector_specific_impact(sector),
            "currency_effects": {
                "usd_strength": random.choice(["強勢", "中性", "弱勢"]),
                "twd_outlook": random.choice(["升值", "貶值", "穩定"]),
                "currency_volatility": random.choice(["低", "中", "高"]),
                "export_competitiveness": random.choice(["改善", "持平", "惡化"])
            },
            "economic_indicators": {
                "gdp_growth": round(random.uniform(-1.0, 5.0), 1),
                "industrial_production": round(random.uniform(-5.0, 8.0), 1),
                "retail_sales": round(random.uniform(-3.0, 10.0), 1),
                "housing_market": random.choice(["強勁", "穩定", "疲弱"]),
                "labor_market": random.choice(["緊俏", "平衡", "鬆弛"])
            },
            "policy_outlook": {
                "fiscal_policy": random.choice(["擴張", "中性", "緊縮"]),
                "regulatory_changes": random.choice(["友善", "中性", "嚴格"]),
                "infrastructure_spending": random.choice(["增加", "維持", "減少"]),
                "tax_policy": random.choice(["減稅", "維持", "增稅"]),
                "green_transition": random.choice(["加速", "穩步", "放緩"])
            }
        }

    def _determine_sector(self, symbol: str) -> str:
        """根據股票代號判斷產業（簡化版）"""
        sector_mapping = {
            "2330": "半導體",
            "2317": "電子製造",
            "2454": "IC設計",
            "2412": "電信",
            "1301": "石化",
            "2382": "電腦設備",
            "2881": "金融",
            "2002": "食品"
        }
        
        code = symbol.replace('.TW', '')
        return sector_mapping.get(code, "科技")

    def _get_sector_specific_impact(self, sector: str) -> Dict[str, Any]:
        """獲取產業特定的總經影響"""
        import random
        
        base_impact = {
            "interest_rate_sensitivity": random.choice(["高", "中", "低"]),
            "inflation_impact": random.choice(["正面", "負面", "中性"]),
            "trade_dependency": random.choice(["高", "中", "低"]),
            "regulatory_risk": random.choice(["高", "中", "低"])
        }
        
        # 產業特定調整
        if sector == "半導體":
            base_impact.update({
                "us_china_tension_impact": "高",
                "tech_export_restrictions": "關注",
                "global_demand_cycle": "關鍵因素"
            })
        elif sector == "金融":
            base_impact.update({
                "interest_rate_sensitivity": "極高",
                "credit_cycle_impact": "重要",
                "regulatory_oversight": "嚴格"
            })
        elif sector == "石化":
            base_impact.update({
                "energy_price_correlation": "高",
                "environmental_regulation": "增強",
                "global_demand": "週期性"
            })
            
        return base_impact

    def _generate_insights(self, macro_data: Dict, user_tier: str) -> List[str]:
        """生成總經分析洞察"""
        insights = []
        
        # 基礎洞察 (所有用戶)
        cycle_phase = macro_data["economic_cycle"]["current_phase"]
        if cycle_phase in ["復甦", "擴張"]:
            insights.append("🟢 經濟週期處於擴張階段，有利於股市表現")
        elif cycle_phase == "收縮":
            insights.append("🟡 經濟週期轉向收縮，需謹慎評估風險")
        elif cycle_phase == "衰退":
            insights.append("🔴 經濟處於衰退階段，防禦性投資策略為宜")
            
        fed_stance = macro_data["monetary_policy"]["fed_stance"]
        if fed_stance == "鴿派":
            insights.append("💰 央行政策偏向寬鬆，流動性環境有利")
        elif fed_stance == "鷹派":
            insights.append("⚠️ 央行政策轉鷹，升息預期對估值形成壓力")
            
        # 進階洞察 (Gold以上)
        if user_tier in ["gold", "diamond"]:
            inflation_trend = macro_data["inflation_analysis"]["trend"]
            current_cpi = macro_data["inflation_analysis"]["current_cpi"]
            
            if inflation_trend == "上升" and current_cpi > 4.0:
                insights.append("📈 通脹壓力持續，央行政策緊縮風險升高")
            elif inflation_trend == "下降" and current_cpi < 3.0:
                insights.append("📉 通脹壓力緩解，政策空間增加")
                
            trade_tensions = macro_data["trade_environment"]["trade_tensions"]
            if trade_tensions == "高":
                insights.append("🌐 國際貿易緊張升溫，出口導向企業面臨挑戰")
                
            yield_curve = macro_data["economic_cycle"]["leading_indicators"]["yield_curve"]
            if yield_curve == "倒掛":
                insights.append("📊 殖利率曲線倒掛，經濟衰退信號值得關注")
                
        # 專業洞察 (Diamond)
        if user_tier == "diamond":
            geopolitical = macro_data["geopolitical_risks"]["overall_risk_level"]
            if geopolitical in ["高", "極高"]:
                insights.append("🌍 地緣政治風險升高，避險資產配置需求增加")
                
            pmi = macro_data["economic_cycle"]["leading_indicators"]["pmi"]
            if pmi < 50:
                insights.append("🏭 PMI跌破50，製造業景氣轉弱信號")
            elif pmi > 55:
                insights.append("🏭 PMI強勁擴張，製造業景氣樂觀")
                
            currency_outlook = macro_data["currency_effects"]["twd_outlook"]
            if currency_outlook == "升值":
                insights.append("💱 新台幣升值預期，降低進口成本但影響出口競爭力")
            elif currency_outlook == "貶值":
                insights.append("💱 新台幣貶值壓力，有利出口但推升進口通脹")
                
            fiscal_policy = macro_data["policy_outlook"]["fiscal_policy"]
            if fiscal_policy == "擴張":
                insights.append("🏛️ 財政政策擴張，政府支出刺激經濟成長")
                
        return insights

    def _generate_recommendation(self, macro_data: Dict) -> str:
        """生成總經投資建議"""
        score = 0
        
        # 經濟週期評分
        cycle_phase = macro_data["economic_cycle"]["current_phase"]
        if cycle_phase in ["復甦", "擴張"]:
            score += 2
        elif cycle_phase == "高峰":
            score += 1
        elif cycle_phase == "收縮":
            score -= 1
        elif cycle_phase == "衰退":
            score -= 2
            
        # 貨幣政策評分
        fed_stance = macro_data["monetary_policy"]["fed_stance"]
        if fed_stance == "鴿派":
            score += 2
        elif fed_stance == "中性":
            score += 0
        elif fed_stance == "鷹派":
            score -= 2
            
        # 通脹評分
        inflation_trend = macro_data["inflation_analysis"]["trend"]
        current_cpi = macro_data["inflation_analysis"]["current_cpi"]
        if inflation_trend == "下降" and current_cpi < 3.0:
            score += 1
        elif inflation_trend == "上升" and current_cpi > 4.0:
            score -= 2
            
        # 地緣政治評分
        geo_risk = macro_data["geopolitical_risks"]["overall_risk_level"]
        if geo_risk == "低":
            score += 1
        elif geo_risk in ["高", "極高"]:
            score -= 2
            
        # 貿易環境評分
        trade_tensions = macro_data["trade_environment"]["trade_tensions"]
        if trade_tensions == "低":
            score += 1
        elif trade_tensions == "高":
            score -= 1
            
        # 總評
        if score >= 5:
            return "STRONG_BUY"
        elif score >= 2:
            return "BUY"
        elif score <= -5:
            return "STRONG_SELL"
        elif score <= -2:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_confidence(self, macro_data: Dict) -> float:
        """計算分析信心度"""
        # 基於經濟指標的一致性評估
        indicators = macro_data["economic_cycle"]["leading_indicators"]
        
        consistency_score = 0
        if indicators["pmi"] > 50:
            consistency_score += 1
        if indicators["employment"] < 5.0:
            consistency_score += 1
        if indicators["consumer_confidence"] > 100:
            consistency_score += 1
        if indicators["yield_curve"] == "正常":
            consistency_score += 1
            
        base_confidence = consistency_score / 4 * 0.6 + 0.3
        
        # 地緣政治風險調整
        geo_risk = macro_data["geopolitical_risks"]["overall_risk_level"]
        if geo_risk in ["高", "極高"]:
            base_confidence *= 0.85
            
        return min(0.95, max(0.5, base_confidence))

    def _assess_macro_risk(self, macro_data: Dict) -> Dict[str, Any]:
        """評估總經風險"""
        risk_factors = []
        risk_score = 0
        
        # 通脹風險
        if macro_data["inflation_analysis"]["current_cpi"] > 4.0:
            risk_factors.append("高通脹風險")
            risk_score += 2
            
        # 利率風險
        if macro_data["monetary_policy"]["fed_stance"] == "鷹派":
            risk_factors.append("升息風險")
            risk_score += 2
            
        # 地緣政治風險
        if macro_data["geopolitical_risks"]["overall_risk_level"] in ["高", "極高"]:
            risk_factors.append("地緣政治風險")
            risk_score += 3
            
        # 貿易風險
        if macro_data["trade_environment"]["trade_tensions"] == "高":
            risk_factors.append("貿易戰風險")
            risk_score += 2
            
        # 經濟衰退風險
        if macro_data["economic_cycle"]["current_phase"] in ["收縮", "衰退"]:
            risk_factors.append("經濟衰退風險")
            risk_score += 3
            
        if risk_score >= 6:
            risk_level = "HIGH"
        elif risk_score >= 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors or ["總經環境相對穩定"],
            "hedging_suggestions": self._get_hedging_suggestions(risk_factors)
        }

    def _get_hedging_suggestions(self, risk_factors: List[str]) -> List[str]:
        """獲取對沖建議"""
        suggestions = []
        
        if "高通脹風險" in risk_factors:
            suggestions.append("考慮配置抗通脹資產（TIPS、黃金、不動產）")
        if "升息風險" in risk_factors:
            suggestions.append("縮短債券存續期間，關注利率敏感產業")
        if "地緣政治風險" in risk_factors:
            suggestions.append("增加避險資產配置，分散地理風險")
        if "貿易戰風險" in risk_factors:
            suggestions.append("關注內需型企業，減少出口依賴標的")
        if "經濟衰退風險" in risk_factors:
            suggestions.append("增加防禦性資產，現金水位提高")
            
        return suggestions or ["當前無特殊對沖需求"]

    def _analyze_timing(self, macro_data: Dict, user_tier: str) -> Dict[str, Any]:
        """分析投資時機"""
        if user_tier == "free":
            return {"message": "升級至Gold可獲得詳細時機分析"}
            
        cycle_phase = macro_data["economic_cycle"]["current_phase"]
        position = macro_data["economic_cycle"]["cycle_position"]
        
        timing_analysis = {
            "cycle_timing": cycle_phase,
            "position_in_cycle": f"{position:.0%}",
            "optimal_entry": "否",
            "risk_reward_ratio": "中等"
        }
        
        if cycle_phase in ["復甦", "擴張"] and position < 0.7:
            timing_analysis.update({
                "optimal_entry": "是",
                "risk_reward_ratio": "有利",
                "recommended_strategy": "積極配置成長型資產"
            })
        elif cycle_phase == "高峰" or position > 0.8:
            timing_analysis.update({
                "optimal_entry": "謹慎",
                "risk_reward_ratio": "不利",
                "recommended_strategy": "獲利了結，增加防禦配置"
            })
        elif cycle_phase in ["收縮", "衰退"]:
            timing_analysis.update({
                "optimal_entry": "等待",
                "risk_reward_ratio": "差",
                "recommended_strategy": "保持現金，等待底部信號"
            })
            
        if user_tier == "diamond":
            timing_analysis.update({
                "sector_rotation": self._get_sector_rotation_advice(macro_data),
                "policy_calendar": self._get_policy_calendar(macro_data),
                "leading_indicators_signal": self._interpret_leading_indicators(macro_data)
            })
            
        return timing_analysis

    def _get_sector_rotation_advice(self, macro_data: Dict) -> Dict[str, str]:
        """獲取產業輪動建議"""
        cycle_phase = macro_data["economic_cycle"]["current_phase"]
        
        rotation_map = {
            "衰退": {"首選": "公用事業、必需消費品", "避開": "原物料、金融"},
            "復甦": {"首選": "科技、工業", "避開": "公用事業"},
            "擴張": {"首選": "非必需消費品、金融", "避開": "防禦型產業"},
            "高峰": {"首選": "能源、原物料", "避開": "成長型科技"},
            "收縮": {"首選": "防禦型產業", "避開": "週期性產業"}
        }
        
        return rotation_map.get(cycle_phase, {"建議": "均衡配置"})

    def _get_policy_calendar(self, macro_data: Dict) -> Dict[str, str]:
        """獲取政策行事曆"""
        return {
            "下次央行會議": macro_data["monetary_policy"]["next_meeting"],
            "重要經濟數據": "每月第一個週五非農就業數據",
            "財報季": "1月、4月、7月、10月",
            "注意事項": "關注政策轉向信號"
        }

    def _interpret_leading_indicators(self, macro_data: Dict) -> str:
        """解讀領先指標"""
        indicators = macro_data["economic_cycle"]["leading_indicators"]
        
        signals = []
        if indicators["pmi"] > 52:
            signals.append("PMI擴張")
        if indicators["employment"] < 4.5:
            signals.append("就業強勁")
        if indicators["consumer_confidence"] > 105:
            signals.append("消費信心佳")
        if indicators["yield_curve"] == "正常":
            signals.append("殖利率曲線正常")
            
        if len(signals) >= 3:
            return "領先指標多數正面，經濟前景樂觀"
        elif len(signals) <= 1:
            return "領先指標轉弱，經濟前景堪憂"
        else:
            return "領先指標好壞參半，維持觀察"

    def _get_tier_limitations(self, user_tier: str) -> List[str]:
        """獲取用戶等級限制"""
        if user_tier == "free":
            return [
                "僅提供基礎總經指標",
                "不包含詳細政策分析",
                "限制地緣政治深度分析",
                "無法獲得投資時機建議"
            ]
        elif user_tier == "gold":
            return [
                "不包含產業輪動策略",
                "政策行事曆功能有限",
                "領先指標解讀不完整"
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
            "analyst_type": "macro_economic_analyst",
            "version": self.version,
            "supported_analysis": [
                "economic_cycle",
                "monetary_policy",
                "inflation_analysis",
                "geopolitical_risk",
                "sector_rotation",
                "investment_timing"
            ]
        }

# 全局實例
macro_economic_analyst = MacroEconomicAnalyst()
"""
TradingAgents Analyst Architecture Integration
TradingAgents分析師架構整合

任務7.3: 金融專業化模型和服務整合 - 分析師整合部分
負責人: Kiro AI Assistant (產品整合團隊)

提供：
- 與現有分析師架構的無縫整合
- 專業化模型服務的統一接口
- 分析師工作流程優化
- 多模型協同分析
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

from .financial_model_service import FinancialModelService, FinancialModelType

logger = logging.getLogger(__name__)

class AnalystType(Enum):
    """分析師類型枚舉"""
    TECHNICAL_ANALYST = "technical_analyst"         # 技術分析師
    FUNDAMENTAL_ANALYST = "fundamental_analyst"     # 基本面分析師
    QUANTITATIVE_ANALYST = "quantitative_analyst"  # 量化分析師
    RISK_ANALYST = "risk_analyst"                   # 風險分析師
    MARKET_ANALYST = "market_analyst"               # 市場分析師
    SECTOR_ANALYST = "sector_analyst"               # 行業分析師

class AnalysisTaskType(Enum):
    """分析任務類型枚舉"""
    STOCK_RESEARCH = "stock_research"               # 股票研究
    MARKET_OUTLOOK = "market_outlook"               # 市場展望
    RISK_ASSESSMENT = "risk_assessment"             # 風險評估
    PORTFOLIO_REVIEW = "portfolio_review"           # 投資組合檢視
    EARNINGS_ANALYSIS = "earnings_analysis"         # 盈利分析
    SECTOR_ANALYSIS = "sector_analysis"             # 行業分析

@dataclass
class AnalysisRequest:
    """分析請求數據結構"""
    request_id: str
    analyst_type: AnalystType
    task_type: AnalysisTaskType
    target_symbol: Optional[str]
    analysis_scope: str
    priority: int = 1  # 1-5, 5最高
    deadline: Optional[datetime] = None
    additional_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['analyst_type'] = self.analyst_type.value
        result['task_type'] = self.task_type.value
        if self.deadline:
            result['deadline'] = self.deadline.isoformat()
        return result

@dataclass
class AnalysisResult:
    """分析結果數據結構"""
    request_id: str
    analyst_type: AnalystType
    analysis_content: str
    confidence_score: float
    key_findings: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    supporting_data: Dict[str, Any]
    model_used: str
    analysis_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['analyst_type'] = self.analyst_type.value
        result['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return result

class AnalystModelMapper:
    """分析師模型映射器"""
    
    def __init__(self):
        # 分析師類型到金融模型類型的映射
        self.analyst_to_model_mapping = {
            AnalystType.TECHNICAL_ANALYST: [
                FinancialModelType.STOCK_ANALYSIS,
                FinancialModelType.TECHNICAL_ANALYSIS
            ],
            AnalystType.FUNDAMENTAL_ANALYST: [
                FinancialModelType.STOCK_ANALYSIS,
                FinancialModelType.EARNINGS_PREDICTION
            ],
            AnalystType.QUANTITATIVE_ANALYST: [
                FinancialModelType.PORTFOLIO_OPTIMIZATION,
                FinancialModelType.RISK_ASSESSMENT
            ],
            AnalystType.RISK_ANALYST: [
                FinancialModelType.RISK_ASSESSMENT,
                FinancialModelType.MARKET_SENTIMENT
            ],
            AnalystType.MARKET_ANALYST: [
                FinancialModelType.MARKET_SENTIMENT,
                FinancialModelType.NEWS_ANALYSIS
            ],
            AnalystType.SECTOR_ANALYST: [
                FinancialModelType.STOCK_ANALYSIS,
                FinancialModelType.GENERAL_FINANCIAL
            ]
        }
        
        # 任務類型到分析提示詞的映射
        self.task_prompts = {
            AnalysisTaskType.STOCK_RESEARCH: "請進行深入的股票研究分析，包括技術面和基本面：",
            AnalysisTaskType.MARKET_OUTLOOK: "請分析當前市場狀況並提供未來展望：",
            AnalysisTaskType.RISK_ASSESSMENT: "請進行全面的風險評估分析：",
            AnalysisTaskType.PORTFOLIO_REVIEW: "請檢視投資組合並提供優化建議：",
            AnalysisTaskType.EARNINGS_ANALYSIS: "請分析盈利狀況和未來預期：",
            AnalysisTaskType.SECTOR_ANALYSIS: "請進行行業分析和比較："
        }
    
    def get_suitable_models(self, analyst_type: AnalystType) -> List[FinancialModelType]:
        """獲取適合的模型類型"""
        return self.analyst_to_model_mapping.get(analyst_type, [FinancialModelType.GENERAL_FINANCIAL])
    
    def get_task_prompt(self, task_type: AnalysisTaskType) -> str:
        """獲取任務提示詞"""
        return self.task_prompts.get(task_type, "請進行專業分析：")

class AnalystWorkflowEngine:
    """分析師工作流程引擎"""
    
    def __init__(self, financial_model_service: FinancialModelService):
        self.financial_model_service = financial_model_service
        self.model_mapper = AnalystModelMapper()
        self.active_requests = {}
        self.completed_analyses = []
        
    async def process_analysis_request(self, request: AnalysisRequest) -> AnalysisResult:
        """處理分析請求"""
        logger.info(f"開始處理分析請求: {request.request_id} - {request.analyst_type.value}")
        
        # 記錄活躍請求
        self.active_requests[request.request_id] = request
        
        try:
            # 構建分析查詢
            analysis_query = self._build_analysis_query(request)
            
            # 確定使用的模型類型
            suitable_models = self.model_mapper.get_suitable_models(request.analyst_type)
            preferred_model_type = suitable_models[0] if suitable_models else None
            
            # 調用金融模型服務
            model_response = await self.financial_model_service.process_financial_request(
                request_text=analysis_query,
                request_type=preferred_model_type.value if preferred_model_type else None,
                user_preferences={'analyst_type': request.analyst_type.value}
            )
            
            if not model_response['success']:
                raise Exception(f"模型服務調用失敗: {model_response.get('error', 'Unknown error')}")
            
            # 後處理分析結果
            analysis_result = await self._post_process_analysis(request, model_response)
            
            # 記錄完成的分析
            self.completed_analyses.append(analysis_result)
            if len(self.completed_analyses) > 1000:
                self.completed_analyses = self.completed_analyses[-1000:]
            
            # 移除活躍請求
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            
            logger.info(f"分析請求處理完成: {request.request_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"處理分析請求失敗: {request.request_id} - {e}")
            # 移除活躍請求
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
            raise
    
    def _build_analysis_query(self, request: AnalysisRequest) -> str:
        """構建分析查詢"""
        # 獲取任務提示詞
        task_prompt = self.model_mapper.get_task_prompt(request.task_type)
        
        # 構建基礎查詢
        query_parts = [task_prompt]
        
        # 添加目標標的
        if request.target_symbol:
            query_parts.append(f"分析標的：{request.target_symbol}")
        
        # 添加分析範圍
        query_parts.append(f"分析範圍：{request.analysis_scope}")
        
        # 添加額外上下文
        if request.additional_context:
            context_info = []
            for key, value in request.additional_context.items():
                context_info.append(f"{key}: {value}")
            if context_info:
                query_parts.append(f"額外信息：{'; '.join(context_info)}")
        
        # 添加分析師特定要求
        analyst_requirements = self._get_analyst_specific_requirements(request.analyst_type)
        if analyst_requirements:
            query_parts.append(f"分析要求：{analyst_requirements}")
        
        return "\n\n".join(query_parts)
    
    def _get_analyst_specific_requirements(self, analyst_type: AnalystType) -> str:
        """獲取分析師特定要求"""
        requirements = {
            AnalystType.TECHNICAL_ANALYST: "請重點關注技術指標、圖表形態、支撐阻力位和交易量分析",
            AnalystType.FUNDAMENTAL_ANALYST: "請重點關注財務數據、營收成長、獲利能力和估值分析",
            AnalystType.QUANTITATIVE_ANALYST: "請提供量化指標、統計分析和數學模型支持",
            AnalystType.RISK_ANALYST: "請重點評估各種風險因素、波動性和風險控制措施",
            AnalystType.MARKET_ANALYST: "請分析市場趨勢、宏觀經濟因素和市場情緒",
            AnalystType.SECTOR_ANALYST: "請進行行業比較、競爭分析和行業前景評估"
        }
        return requirements.get(analyst_type, "")
    
    async def _post_process_analysis(self, request: AnalysisRequest, model_response: Dict[str, Any]) -> AnalysisResult:
        """後處理分析結果"""
        analysis_content = model_response['response']
        
        # 提取關鍵發現
        key_findings = self._extract_key_findings(analysis_content)
        
        # 提取建議
        recommendations = self._extract_recommendations(analysis_content)
        
        # 提取風險因素
        risk_factors = self._extract_risk_factors(analysis_content)
        
        # 計算信心度
        confidence_score = self._calculate_confidence_score(model_response)
        
        # 準備支持數據
        supporting_data = {
            'model_confidence': model_response.get('routing_confidence', 0),
            'response_time': model_response.get('response_time_seconds', 0),
            'model_id': model_response.get('model_id', ''),
            'analysis_timestamp': model_response.get('timestamp', '')
        }
        
        return AnalysisResult(
            request_id=request.request_id,
            analyst_type=request.analyst_type,
            analysis_content=analysis_content,
            confidence_score=confidence_score,
            key_findings=key_findings,
            recommendations=recommendations,
            risk_factors=risk_factors,
            supporting_data=supporting_data,
            model_used=model_response.get('model_used', 'Unknown'),
            analysis_timestamp=datetime.now()
        )
    
    def _extract_key_findings(self, analysis_content: str) -> List[str]:
        """提取關鍵發現"""
        # 簡化實現：尋找包含關鍵詞的句子
        key_indicators = ['發現', '顯示', '表明', '證實', '揭示', '指出']
        findings = []
        
        sentences = analysis_content.split('。')
        for sentence in sentences:
            if any(indicator in sentence for indicator in key_indicators):
                findings.append(sentence.strip() + '。')
        
        return findings[:5]  # 最多返回5個關鍵發現
    
    def _extract_recommendations(self, analysis_content: str) -> List[str]:
        """提取建議"""
        recommendation_indicators = ['建議', '推薦', '應該', '可以考慮', '值得關注']
        recommendations = []
        
        sentences = analysis_content.split('。')
        for sentence in sentences:
            if any(indicator in sentence for indicator in recommendation_indicators):
                recommendations.append(sentence.strip() + '。')
        
        return recommendations[:5]  # 最多返回5個建議
    
    def _extract_risk_factors(self, analysis_content: str) -> List[str]:
        """提取風險因素"""
        risk_indicators = ['風險', '威脅', '挑戰', '不確定', '波動', '下跌']
        risk_factors = []
        
        sentences = analysis_content.split('。')
        for sentence in sentences:
            if any(indicator in sentence for indicator in risk_indicators):
                risk_factors.append(sentence.strip() + '。')
        
        return risk_factors[:5]  # 最多返回5個風險因素
    
    def _calculate_confidence_score(self, model_response: Dict[str, Any]) -> float:
        """計算信心度"""
        # 基於模型路由信心度和響應質量
        routing_confidence = model_response.get('routing_confidence', 0.5)
        response_time = model_response.get('response_time_seconds', 2.0)
        
        # 響應時間越短，信心度越高（在合理範圍內）
        time_factor = max(0.5, min(1.0, 3.0 / max(response_time, 0.5)))
        
        return min(1.0, routing_confidence * 0.7 + time_factor * 0.3)

class TradingAgentsAnalystIntegration:
    """TradingAgents分析師整合主類"""
    
    def __init__(self):
        self.financial_model_service = FinancialModelService()
        self.workflow_engine = AnalystWorkflowEngine(self.financial_model_service)
        self.integration_stats = {
            'total_requests': 0,
            'successful_analyses': 0,
            'analyst_usage_count': {},
            'average_analysis_time': 0.0,
            'start_time': datetime.now()
        }
    
    async def request_analysis(
        self,
        analyst_type: str,
        task_type: str,
        analysis_scope: str,
        target_symbol: Optional[str] = None,
        priority: int = 1,
        deadline: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """請求分析服務"""
        start_time = datetime.now()
        self.integration_stats['total_requests'] += 1
        
        try:
            # 轉換枚舉類型
            analyst_enum = AnalystType(analyst_type)
            task_enum = AnalysisTaskType(task_type)
            
            # 處理截止時間
            deadline_dt = None
            if deadline:
                try:
                    deadline_dt = datetime.fromisoformat(deadline)
                except:
                    logger.warning(f"無效的截止時間格式: {deadline}")
            
            # 創建分析請求
            request = AnalysisRequest(
                request_id=f"analysis_{int(datetime.now().timestamp())}",
                analyst_type=analyst_enum,
                task_type=task_enum,
                target_symbol=target_symbol,
                analysis_scope=analysis_scope,
                priority=priority,
                deadline=deadline_dt,
                additional_context=additional_context or {}
            )
            
            # 處理分析請求
            analysis_result = await self.workflow_engine.process_analysis_request(request)
            
            # 更新統計
            self.integration_stats['successful_analyses'] += 1
            analyst_key = analyst_type
            self.integration_stats['analyst_usage_count'][analyst_key] = (
                self.integration_stats['analyst_usage_count'].get(analyst_key, 0) + 1
            )
            
            # 計算分析時間
            analysis_time = (datetime.now() - start_time).total_seconds()
            self._update_average_analysis_time(analysis_time)
            
            return {
                'success': True,
                'request_id': request.request_id,
                'analysis_result': analysis_result.to_dict(),
                'analysis_time_seconds': analysis_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except ValueError as e:
            logger.error(f"無效的參數: {e}")
            return {
                'success': False,
                'error': f"無效的參數: {e}",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"分析請求處理失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_average_analysis_time(self, new_analysis_time: float):
        """更新平均分析時間"""
        current_avg = self.integration_stats['average_analysis_time']
        total_analyses = self.integration_stats['successful_analyses']
        
        if total_analyses == 1:
            self.integration_stats['average_analysis_time'] = new_analysis_time
        else:
            self.integration_stats['average_analysis_time'] = (
                (current_avg * (total_analyses - 1) + new_analysis_time) / total_analyses
            )
    
    async def batch_analysis(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量分析請求"""
        logger.info(f"開始批量分析，共 {len(requests)} 個請求")
        
        # 並行處理多個分析請求
        tasks = []
        for request_data in requests:
            task = self.request_analysis(**request_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'request_index': i,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """獲取整合統計信息"""
        uptime = datetime.now() - self.integration_stats['start_time']
        
        return {
            'integration_uptime_hours': uptime.total_seconds() / 3600,
            'total_analysis_requests': self.integration_stats['total_requests'],
            'successful_analyses': self.integration_stats['successful_analyses'],
            'success_rate': (
                self.integration_stats['successful_analyses'] / self.integration_stats['total_requests']
                if self.integration_stats['total_requests'] > 0 else 0
            ),
            'average_analysis_time_seconds': self.integration_stats['average_analysis_time'],
            'analyst_usage_distribution': self.integration_stats['analyst_usage_count'],
            'active_requests': len(self.workflow_engine.active_requests),
            'completed_analyses': len(self.workflow_engine.completed_analyses),
            'financial_model_service_stats': self.financial_model_service.get_service_statistics()
        }
    
    def get_analyst_capabilities(self) -> Dict[str, Any]:
        """獲取分析師能力說明"""
        return {
            'supported_analyst_types': [
                {
                    'type': analyst_type.value,
                    'name': self._get_analyst_name(analyst_type),
                    'description': self._get_analyst_description(analyst_type),
                    'suitable_tasks': [task.value for task in self._get_suitable_tasks(analyst_type)]
                }
                for analyst_type in AnalystType
            ],
            'supported_task_types': [
                {
                    'type': task_type.value,
                    'name': self._get_task_name(task_type),
                    'description': self._get_task_description(task_type)
                }
                for task_type in AnalysisTaskType
            ]
        }
    
    def _get_analyst_name(self, analyst_type: AnalystType) -> str:
        """獲取分析師名稱"""
        names = {
            AnalystType.TECHNICAL_ANALYST: "技術分析師",
            AnalystType.FUNDAMENTAL_ANALYST: "基本面分析師",
            AnalystType.QUANTITATIVE_ANALYST: "量化分析師",
            AnalystType.RISK_ANALYST: "風險分析師",
            AnalystType.MARKET_ANALYST: "市場分析師",
            AnalystType.SECTOR_ANALYST: "行業分析師"
        }
        return names.get(analyst_type, analyst_type.value)
    
    def _get_analyst_description(self, analyst_type: AnalystType) -> str:
        """獲取分析師描述"""
        descriptions = {
            AnalystType.TECHNICAL_ANALYST: "專精於技術指標分析、圖表形態識別和交易信號判斷",
            AnalystType.FUNDAMENTAL_ANALYST: "專精於財務報表分析、企業價值評估和基本面研究",
            AnalystType.QUANTITATIVE_ANALYST: "專精於數量化分析、統計模型和風險量化",
            AnalystType.RISK_ANALYST: "專精於風險識別、評估和管理策略制定",
            AnalystType.MARKET_ANALYST: "專精於市場趨勢分析、宏觀經濟研究和市場情緒判斷",
            AnalystType.SECTOR_ANALYST: "專精於特定行業分析、競爭格局研究和行業前景評估"
        }
        return descriptions.get(analyst_type, "專業金融分析師")
    
    def _get_suitable_tasks(self, analyst_type: AnalystType) -> List[AnalysisTaskType]:
        """獲取適合的任務類型"""
        task_mapping = {
            AnalystType.TECHNICAL_ANALYST: [AnalysisTaskType.STOCK_RESEARCH],
            AnalystType.FUNDAMENTAL_ANALYST: [AnalysisTaskType.STOCK_RESEARCH, AnalysisTaskType.EARNINGS_ANALYSIS],
            AnalystType.QUANTITATIVE_ANALYST: [AnalysisTaskType.PORTFOLIO_REVIEW, AnalysisTaskType.RISK_ASSESSMENT],
            AnalystType.RISK_ANALYST: [AnalysisTaskType.RISK_ASSESSMENT, AnalysisTaskType.PORTFOLIO_REVIEW],
            AnalystType.MARKET_ANALYST: [AnalysisTaskType.MARKET_OUTLOOK],
            AnalystType.SECTOR_ANALYST: [AnalysisTaskType.SECTOR_ANALYSIS, AnalysisTaskType.STOCK_RESEARCH]
        }
        return task_mapping.get(analyst_type, list(AnalysisTaskType))
    
    def _get_task_name(self, task_type: AnalysisTaskType) -> str:
        """獲取任務名稱"""
        names = {
            AnalysisTaskType.STOCK_RESEARCH: "股票研究",
            AnalysisTaskType.MARKET_OUTLOOK: "市場展望",
            AnalysisTaskType.RISK_ASSESSMENT: "風險評估",
            AnalysisTaskType.PORTFOLIO_REVIEW: "投資組合檢視",
            AnalysisTaskType.EARNINGS_ANALYSIS: "盈利分析",
            AnalysisTaskType.SECTOR_ANALYSIS: "行業分析"
        }
        return names.get(task_type, task_type.value)
    
    def _get_task_description(self, task_type: AnalysisTaskType) -> str:
        """獲取任務描述"""
        descriptions = {
            AnalysisTaskType.STOCK_RESEARCH: "深入研究特定股票的投資價值和前景",
            AnalysisTaskType.MARKET_OUTLOOK: "分析整體市場趨勢和未來展望",
            AnalysisTaskType.RISK_ASSESSMENT: "評估投資風險和制定風控策略",
            AnalysisTaskType.PORTFOLIO_REVIEW: "檢視投資組合表現和優化建議",
            AnalysisTaskType.EARNINGS_ANALYSIS: "分析企業盈利能力和成長潛力",
            AnalysisTaskType.SECTOR_ANALYSIS: "研究特定行業的發展趨勢和投資機會"
        }
        return descriptions.get(task_type, "專業金融分析任務")

# 便利函數
def create_analyst_integration() -> TradingAgentsAnalystIntegration:
    """創建分析師整合服務的便利函數"""
    return TradingAgentsAnalystIntegration()

async def quick_analyst_request(
    analyst_type: str,
    task_type: str,
    analysis_scope: str,
    target_symbol: Optional[str] = None
) -> Dict[str, Any]:
    """快速分析師請求的便利函數"""
    integration = create_analyst_integration()
    return await integration.request_analysis(
        analyst_type=analyst_type,
        task_type=task_type,
        analysis_scope=analysis_scope,
        target_symbol=target_symbol
    )

# 導出主要類和函數
__all__ = [
    'TradingAgentsAnalystIntegration',
    'AnalystWorkflowEngine',
    'AnalystModelMapper',
    'AnalysisRequest',
    'AnalysisResult',
    'AnalystType',
    'AnalysisTaskType',
    'create_analyst_integration',
    'quick_analyst_request'
]
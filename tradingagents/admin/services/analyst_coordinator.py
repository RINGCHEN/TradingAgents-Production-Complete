#!/usr/bin/env python3
"""
分析師協調器服務 (Analyst Coordinator Service)
天工 (TianGong) - 分析師協調器業務邏輯

此模組提供分析師協調器的核心業務邏輯，包含：
1. 分析師註冊和管理
2. 分析任務協調和調度
3. 分析結果聚合和處理
4. 分析師性能監控
5. 統一的分析師調用機制
"""

import asyncio
import uuid
import importlib
import inspect
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from ..models.analyst_coordinator import (
    AnalystInfo, AnalystRegistry, AnalystCommand, AnalystCommandResult,
    AnalysisRequest, AnalysisExecution, AnalysisResult,
    AnalystCoordinatorConfiguration, AnalystCoordinatorStatistics, AnalystCoordinatorHealth,
    AnalystQuery, AnalysisQuery, AnalystCoordinatorDashboard,
    AnalystStatus, AnalystType, AnalysisType, AnalysisStatus, AnalysisConfidenceLevel
)
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager

# 配置日誌
api_logger = get_api_logger("analyst_coordinator")
security_logger = get_security_logger("analyst_coordinator")


class AnalystCoordinatorService:
    """分析師協調器服務類"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # 分析師註冊表
        self._analyst_registry: Dict[str, AnalystInfo] = {}
        
        # 分析執行記錄
        self._analysis_executions: Dict[str, AnalysisExecution] = {}
        
        # 分析結果記錄
        self._analysis_results: Dict[str, List[AnalysisResult]] = {}
        
        # 協調器配置
        self._coordinator_config = AnalystCoordinatorConfiguration()
        
        # 分析師模組映射
        self._analyst_modules = {
            'fundamentals_analyst': 'tradingagents.agents.analysts.fundamentals_analyst',
            'news_analyst': 'tradingagents.agents.analysts.news_analyst',
            'risk_analyst': 'tradingagents.agents.analysts.risk_analyst',
            'sentiment_analyst': 'tradingagents.agents.analysts.sentiment_analyst',
            'investment_planner': 'tradingagents.agents.analysts.investment_planner',
            'taiwan_market_analyst': 'tradingagents.agents.analysts.taiwan_market_analyst'
        }
        
        # 初始化分析師註冊表
        self._initialize_analyst_registry()
    
    def _initialize_analyst_registry(self):
        """初始化分析師註冊表"""
        try:
            # 註冊分析師模組
            for analyst_id, module_path in self._analyst_modules.items():
                try:
                    module = importlib.import_module(module_path)
                    
                    # 查找分析師類
                    analyst_class = None
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            name.lower().replace('_', '').endswith('analyst') and
                            name != 'BaseAnalyst'):
                            analyst_class = obj
                            break
                    
                    if analyst_class:
                        analyst_info = AnalystInfo(
                            analyst_id=analyst_id,
                            analyst_name=analyst_class.__name__,
                            analyst_type=self._get_analyst_type(analyst_id),
                            version="1.0.0",
                            status=AnalystStatus.ACTIVE,
                            health_status="healthy",
                            last_health_check=datetime.now(),
                            config={},
                            capabilities=self._get_analyst_capabilities(analyst_id),
                            supported_markets=["TWS", "US", "HK"],  # 預設支持的市場
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        self._analyst_registry[analyst_id] = analyst_info
                        
                    else:
                        api_logger.warning(f"在模組 {module_path} 中未找到分析師類")
                        
                except ImportError as e:
                    api_logger.warning(f"無法導入分析師模組 {module_path}: {str(e)}")
                    # 創建錯誤狀態的分析師信息
                    analyst_info = AnalystInfo(
                        analyst_id=analyst_id,
                        analyst_name=analyst_id.replace('_', ' ').title(),
                        analyst_type=self._get_analyst_type(analyst_id),
                        version="1.0.0",
                        status=AnalystStatus.ERROR,
                        health_status="error",
                        last_health_check=datetime.now(),
                        config={},
                        capabilities=[],
                        supported_markets=[],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self._analyst_registry[analyst_id] = analyst_info
            
            api_logger.info(f"分析師註冊表初始化完成，註冊了 {len(self._analyst_registry)} 個分析師")
            
        except Exception as e:
            api_logger.error(f"分析師註冊表初始化失敗: {str(e)}")
    
    def _get_analyst_type(self, analyst_id: str) -> AnalystType:
        """根據分析師ID獲取分析師類型"""
        type_mapping = {
            'fundamentals_analyst': AnalystType.FUNDAMENTALS,
            'news_analyst': AnalystType.NEWS,
            'risk_analyst': AnalystType.RISK,
            'sentiment_analyst': AnalystType.SENTIMENT,
            'investment_planner': AnalystType.INVESTMENT_PLANNER,
            'taiwan_market_analyst': AnalystType.TAIWAN_MARKET
        }
        return type_mapping.get(analyst_id, AnalystType.FUNDAMENTALS)
    
    def _get_analyst_capabilities(self, analyst_id: str) -> List[str]:
        """根據分析師ID獲取分析師能力"""
        capabilities_mapping = {
            'fundamentals_analyst': ['fundamental_analysis', 'financial_metrics', 'valuation'],
            'news_analyst': ['news_analysis', 'sentiment_analysis', 'event_impact'],
            'risk_analyst': ['risk_assessment', 'volatility_analysis', 'portfolio_risk'],
            'sentiment_analyst': ['market_sentiment', 'social_sentiment', 'investor_mood'],
            'investment_planner': ['investment_strategy', 'portfolio_planning', 'asset_allocation'],
            'taiwan_market_analyst': ['taiwan_market', 'local_regulations', 'tws_specific']
        }
        return capabilities_mapping.get(analyst_id, [])
    
    # ==================== 分析師管理 ====================
    
    async def get_analyst_registry(self, query: AnalystQuery) -> AnalystRegistry:
        """獲取分析師註冊表"""
        try:
            analysts = list(self._analyst_registry.values())
            
            # 應用篩選條件
            if query.analyst_types:
                analysts = [a for a in analysts if a.analyst_type in query.analyst_types]
            
            if query.statuses:
                analysts = [a for a in analysts if a.status in query.statuses]
            
            if query.capabilities:
                analysts = [a for a in analysts if 
                          any(cap in a.capabilities for cap in query.capabilities)]
            
            if query.markets:
                analysts = [a for a in analysts if 
                          any(market in a.supported_markets for market in query.markets)]
            
            if query.keyword:
                keyword = query.keyword.lower()
                analysts = [a for a in analysts if 
                          keyword in a.analyst_name.lower() or 
                          keyword in a.analyst_id.lower()]
            
            # 應用限制
            if query.limit:
                analysts = analysts[:query.limit]
            
            # 統計信息
            total_analysts = len(self._analyst_registry)
            active_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.ACTIVE])
            busy_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.BUSY])
            error_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.ERROR])
            
            return AnalystRegistry(
                analysts=analysts,
                total_analysts=total_analysts,
                active_analysts=active_analysts,
                busy_analysts=busy_analysts,
                error_analysts=error_analysts,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            api_logger.error(f"獲取分析師註冊表失敗: {str(e)}")
            raise
    
    async def get_analyst_info(self, analyst_id: str) -> Optional[AnalystInfo]:
        """獲取分析師詳情"""
        try:
            return self._analyst_registry.get(analyst_id)
            
        except Exception as e:
            api_logger.error(f"獲取分析師詳情失敗: {str(e)}")
            raise
    
    async def execute_analyst_command(self, analyst_id: str, command: AnalystCommand) -> AnalystCommandResult:
        """執行分析師命令"""
        try:
            start_time = datetime.now()
            
            analyst_info = self._analyst_registry.get(analyst_id)
            if not analyst_info:
                return AnalystCommandResult(
                    analyst_id=analyst_id,
                    command=command.command,
                    success=False,
                    message="分析師不存在",
                    execution_time=0.0,
                    executed_at=start_time
                )
            
            # 模擬命令執行
            await asyncio.sleep(0.1)  # 模擬執行時間
            
            success = True
            message = f"命令 {command.command} 執行成功"
            
            # 更新分析師狀態
            if command.command == "start":
                analyst_info.status = AnalystStatus.ACTIVE
                analyst_info.health_status = "healthy"
            elif command.command == "stop":
                analyst_info.status = AnalystStatus.INACTIVE
                analyst_info.health_status = "stopped"
            elif command.command == "restart":
                analyst_info.status = AnalystStatus.ACTIVE
                analyst_info.health_status = "healthy"
            elif command.command == "reload":
                # 重新加載配置
                pass
            elif command.command == "reset":
                # 重置統計信息
                analyst_info.total_analyses = 0
                analyst_info.successful_analyses = 0
                analyst_info.failed_analyses = 0
                analyst_info.average_execution_time = 0.0
                analyst_info.success_rate = 0.0
            else:
                success = False
                message = f"不支持的命令: {command.command}"
            
            analyst_info.updated_at = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AnalystCommandResult(
                analyst_id=analyst_id,
                command=command.command,
                success=success,
                message=message,
                execution_time=execution_time,
                executed_at=start_time,
                details=command.parameters
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            api_logger.error(f"執行分析師命令失敗: {str(e)}")
            
            return AnalystCommandResult(
                analyst_id=analyst_id,
                command=command.command,
                success=False,
                message=f"命令執行失敗: {str(e)}",
                execution_time=execution_time,
                executed_at=start_time
            )
    
    async def run_analysts_health_check(self, analyst_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """執行分析師健康檢查"""
        try:
            if analyst_ids is None:
                analyst_ids = list(self._analyst_registry.keys())
            
            results = []
            
            for analyst_id in analyst_ids:
                analyst_info = self._analyst_registry.get(analyst_id)
                if not analyst_info:
                    results.append({
                        "analyst_id": analyst_id,
                        "status": "not_found",
                        "message": "分析師不存在",
                        "checked_at": datetime.now()
                    })
                    continue
                
                # 執行健康檢查
                try:
                    # 模擬健康檢查
                    await asyncio.sleep(0.05)
                    
                    if analyst_info.status == AnalystStatus.ACTIVE:
                        health_status = "healthy"
                        message = "分析師運行正常"
                    elif analyst_info.status == AnalystStatus.ERROR:
                        health_status = "error"
                        message = "分析師運行異常"
                    else:
                        health_status = "inactive"
                        message = "分析師未激活"
                    
                    # 更新健康檢查時間
                    analyst_info.health_status = health_status
                    analyst_info.last_health_check = datetime.now()
                    
                    results.append({
                        "analyst_id": analyst_id,
                        "status": health_status,
                        "message": message,
                        "checked_at": datetime.now(),
                        "response_time": 0.05,
                        "capabilities": analyst_info.capabilities,
                        "success_rate": analyst_info.success_rate
                    })
                    
                except Exception as e:
                    analyst_info.health_status = "error"
                    analyst_info.last_health_check = datetime.now()
                    
                    results.append({
                        "analyst_id": analyst_id,
                        "status": "error",
                        "message": f"健康檢查失敗: {str(e)}",
                        "checked_at": datetime.now()
                    })
            
            return results
            
        except Exception as e:
            api_logger.error(f"分析師健康檢查失敗: {str(e)}")
            raise
    
    # ==================== 分析任務協調 ====================
    
    async def create_analysis_request(self, request: AnalysisRequest) -> AnalysisExecution:
        """創建分析請求"""
        try:
            execution_id = str(uuid.uuid4())
            
            # 選擇分析師
            assigned_analysts = await self._select_analysts(request)
            
            # 創建分析執行記錄
            execution = AnalysisExecution(
                execution_id=execution_id,
                request_id=request.request_id,
                stock_id=request.stock_id,
                status=AnalysisStatus.PENDING,
                progress=0.0,
                assigned_analysts=assigned_analysts,
                user_id=request.user_id
            )
            
            self._analysis_executions[execution_id] = execution
            
            # 異步執行分析
            asyncio.create_task(self._execute_analysis(execution, request))
            
            return execution
            
        except Exception as e:
            api_logger.error(f"創建分析請求失敗: {str(e)}")
            raise
    
    async def _select_analysts(self, request: AnalysisRequest) -> List[str]:
        """選擇分析師"""
        try:
            selected_analysts = []
            
            # 如果指定了分析師，優先使用
            if request.preferred_analysts:
                for analyst_id in request.preferred_analysts:
                    if (analyst_id in self._analyst_registry and 
                        self._analyst_registry[analyst_id].status == AnalystStatus.ACTIVE):
                        selected_analysts.append(analyst_id)
            
            # 如果沒有指定或指定的分析師不可用，自動選擇
            if not selected_analysts:
                # 根據分析類型選擇合適的分析師
                for analysis_type in request.analysis_types:
                    suitable_analysts = self._get_suitable_analysts(analysis_type)
                    for analyst_id in suitable_analysts:
                        if (analyst_id not in selected_analysts and 
                            len(selected_analysts) < self._coordinator_config.max_analysts_per_analysis):
                            selected_analysts.append(analyst_id)
            
            # 確保至少有最少數量的分析師
            if len(selected_analysts) < self._coordinator_config.min_analysts_per_analysis:
                # 添加更多可用的分析師
                available_analysts = [
                    analyst_id for analyst_id, info in self._analyst_registry.items()
                    if info.status == AnalystStatus.ACTIVE and analyst_id not in selected_analysts
                ]
                
                needed = self._coordinator_config.min_analysts_per_analysis - len(selected_analysts)
                selected_analysts.extend(available_analysts[:needed])
            
            return selected_analysts
            
        except Exception as e:
            api_logger.error(f"選擇分析師失敗: {str(e)}")
            return []
    
    def _get_suitable_analysts(self, analysis_type: AnalysisType) -> List[str]:
        """根據分析類型獲取合適的分析師"""
        type_mapping = {
            AnalysisType.FUNDAMENTAL: ['fundamentals_analyst'],
            AnalysisType.NEWS_SENTIMENT: ['news_analyst', 'sentiment_analyst'],
            AnalysisType.MARKET_SENTIMENT: ['sentiment_analyst'],
            AnalysisType.RISK_ASSESSMENT: ['risk_analyst'],
            AnalysisType.INVESTMENT_PLANNING: ['investment_planner'],
            AnalysisType.TAIWAN_SPECIFIC: ['taiwan_market_analyst'],
            AnalysisType.TECHNICAL: ['fundamentals_analyst', 'risk_analyst']  # 技術分析可以由多個分析師處理
        }
        
        return type_mapping.get(analysis_type, list(self._analyst_registry.keys()))
    
    async def _execute_analysis(self, execution: AnalysisExecution, request: AnalysisRequest):
        """執行分析"""
        try:
            execution.status = AnalysisStatus.RUNNING
            execution.started_at = datetime.now()
            execution.progress = 10.0
            
            results = {}
            
            # 並行執行分析師分析
            tasks = []
            for analyst_id in execution.assigned_analysts:
                task = self._run_analyst_analysis(analyst_id, request)
                tasks.append(task)
            
            # 等待所有分析完成
            analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理分析結果
            for i, result in enumerate(analysis_results):
                analyst_id = execution.assigned_analysts[i]
                
                if isinstance(result, Exception):
                    execution.failed_analysts.append(analyst_id)
                    api_logger.error(f"分析師 {analyst_id} 分析失敗: {str(result)}")
                else:
                    execution.completed_analysts.append(analyst_id)
                    results[analyst_id] = result
                    
                    # 更新分析師統計
                    analyst_info = self._analyst_registry.get(analyst_id)
                    if analyst_info:
                        analyst_info.total_analyses += 1
                        if isinstance(result, Exception):
                            analyst_info.failed_analyses += 1
                        else:
                            analyst_info.successful_analyses += 1
                        
                        # 更新成功率
                        if analyst_info.total_analyses > 0:
                            analyst_info.success_rate = (
                                analyst_info.successful_analyses / analyst_info.total_analyses
                            )
                        
                        analyst_info.last_used_at = datetime.now()
                        analyst_info.updated_at = datetime.now()
            
            # 聚合結果
            if results:
                execution.results = results
                execution.final_recommendation = await self._aggregate_recommendations(results)
                execution.confidence_score = await self._calculate_confidence(results)
                execution.status = AnalysisStatus.COMPLETED
            else:
                execution.status = AnalysisStatus.FAILED
                execution.error_message = "所有分析師都執行失敗"
            
            execution.completed_at = datetime.now()
            execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.progress = 100.0
            
        except Exception as e:
            execution.status = AnalysisStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            if execution.started_at:
                execution.duration = (execution.completed_at - execution.started_at).total_seconds()
            
            api_logger.error(f"執行分析失敗: {str(e)}")
    
    async def _run_analyst_analysis(self, analyst_id: str, request: AnalysisRequest) -> Dict[str, Any]:
        """運行單個分析師的分析"""
        try:
            # 模擬分析過程
            await asyncio.sleep(2.0)  # 模擬分析時間
            
            # 模擬分析結果
            recommendations = ["BUY", "SELL", "HOLD"]
            confidence_levels = [0.7, 0.8, 0.6, 0.9, 0.5]
            
            import random
            recommendation = random.choice(recommendations)
            confidence = random.choice(confidence_levels)
            
            result = {
                "analyst_id": analyst_id,
                "stock_id": request.stock_id,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": [f"{analyst_id} 的分析理由 1", f"{analyst_id} 的分析理由 2"],
                "key_factors": [f"關鍵因素 1", f"關鍵因素 2"],
                "analysis_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            api_logger.error(f"分析師 {analyst_id} 分析失敗: {str(e)}")
            raise
    
    async def _aggregate_recommendations(self, results: Dict[str, Any]) -> str:
        """聚合推薦結果"""
        try:
            recommendations = {}
            total_confidence = 0
            
            for analyst_id, result in results.items():
                rec = result.get("recommendation", "HOLD")
                confidence = result.get("confidence", 0.5)
                
                if rec not in recommendations:
                    recommendations[rec] = 0
                
                recommendations[rec] += confidence
                total_confidence += confidence
            
            # 找出加權最高的推薦
            if recommendations:
                final_recommendation = max(recommendations.items(), key=lambda x: x[1])[0]
                return final_recommendation
            
            return "HOLD"
            
        except Exception as e:
            api_logger.error(f"聚合推薦結果失敗: {str(e)}")
            return "HOLD"
    
    async def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """計算整體信心度"""
        try:
            if not results:
                return 0.0
            
            confidences = [result.get("confidence", 0.5) for result in results.values()]
            return sum(confidences) / len(confidences)
            
        except Exception as e:
            api_logger.error(f"計算信心度失敗: {str(e)}")
            return 0.0
    
    # ==================== 查詢和統計 ====================
    
    async def get_analysis_executions(self, query: AnalysisQuery) -> List[AnalysisExecution]:
        """獲取分析執行列表"""
        try:
            executions = list(self._analysis_executions.values())
            
            # 應用篩選條件
            if query.stock_ids:
                executions = [e for e in executions if e.stock_id in query.stock_ids]
            
            if query.statuses:
                executions = [e for e in executions if e.status in query.statuses]
            
            if query.analyst_ids:
                executions = [e for e in executions if 
                            any(analyst_id in e.assigned_analysts for analyst_id in query.analyst_ids)]
            
            if query.user_ids:
                executions = [e for e in executions if e.user_id in query.user_ids]
            
            if query.start_time:
                executions = [e for e in executions if e.started_at and e.started_at >= query.start_time]
            
            if query.end_time:
                executions = [e for e in executions if e.started_at and e.started_at <= query.end_time]
            
            # 排序和限制
            executions.sort(key=lambda x: x.started_at or datetime.min, reverse=True)
            
            if query.limit:
                executions = executions[:query.limit]
            
            return executions
            
        except Exception as e:
            api_logger.error(f"獲取分析執行列表失敗: {str(e)}")
            raise
    
    async def get_analysis_execution(self, execution_id: str) -> Optional[AnalysisExecution]:
        """獲取分析執行詳情"""
        try:
            return self._analysis_executions.get(execution_id)
            
        except Exception as e:
            api_logger.error(f"獲取分析執行詳情失敗: {str(e)}")
            raise
    
    # ==================== 統計和監控 ====================
    
    async def get_coordinator_statistics(self) -> AnalystCoordinatorStatistics:
        """獲取協調器統計信息"""
        try:
            # 分析師統計
            total_analysts = len(self._analyst_registry)
            active_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.ACTIVE])
            busy_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.BUSY])
            error_analysts = len([a for a in self._analyst_registry.values() if a.status == AnalystStatus.ERROR])
            
            # 分析統計
            total_analyses = len(self._analysis_executions)
            pending_analyses = len([e for e in self._analysis_executions.values() if e.status == AnalysisStatus.PENDING])
            running_analyses = len([e for e in self._analysis_executions.values() if e.status == AnalysisStatus.RUNNING])
            completed_analyses = len([e for e in self._analysis_executions.values() if e.status == AnalysisStatus.COMPLETED])
            failed_analyses = len([e for e in self._analysis_executions.values() if e.status == AnalysisStatus.FAILED])
            
            # 性能統計
            completed_executions = [e for e in self._analysis_executions.values() if e.duration is not None]
            average_analysis_time = (
                sum(e.duration for e in completed_executions) / len(completed_executions)
                if completed_executions else 0.0
            )
            
            success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 100.0
            
            # 計算平均信心度
            completed_with_confidence = [e for e in self._analysis_executions.values() if e.confidence_score is not None]
            average_confidence = (
                sum(e.confidence_score for e in completed_with_confidence) / len(completed_with_confidence)
                if completed_with_confidence else 0.0
            )
            
            # 推薦統計（模擬）
            buy_recommendations = len([e for e in self._analysis_executions.values() if e.final_recommendation == "BUY"])
            sell_recommendations = len([e for e in self._analysis_executions.values() if e.final_recommendation == "SELL"])
            hold_recommendations = len([e for e in self._analysis_executions.values() if e.final_recommendation == "HOLD"])
            
            return AnalystCoordinatorStatistics(
                total_analysts=total_analysts,
                active_analysts=active_analysts,
                busy_analysts=busy_analysts,
                error_analysts=error_analysts,
                total_analyses=total_analyses,
                pending_analyses=pending_analyses,
                running_analyses=running_analyses,
                completed_analyses=completed_analyses,
                failed_analyses=failed_analyses,
                average_analysis_time=average_analysis_time,
                success_rate=success_rate,
                average_confidence=average_confidence,
                buy_recommendations=buy_recommendations,
                sell_recommendations=sell_recommendations,
                hold_recommendations=hold_recommendations,
                uptime=int((datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            api_logger.error(f"獲取協調器統計信息失敗: {str(e)}")
            raise
    
    async def get_coordinator_health(self) -> AnalystCoordinatorHealth:
        """獲取協調器健康狀態"""
        try:
            # 檢查各組件狀態
            overall_status = "healthy"
            coordinator_status = "healthy"
            analyst_registry_status = "healthy"
            task_queue_status = "healthy"
            result_aggregator_status = "healthy"
            
            # 分析師健康狀態
            healthy_analysts = len([a for a in self._analyst_registry.values() if a.health_status == "healthy"])
            unhealthy_analysts = len([a for a in self._analyst_registry.values() if a.health_status != "healthy"])
            
            # 執行健康檢查
            health_checks = []
            
            # 分析師註冊表檢查
            health_checks.append({
                "component": "analyst_registry",
                "status": analyst_registry_status,
                "message": f"已註冊 {len(self._analyst_registry)} 個分析師",
                "checked_at": datetime.now()
            })
            
            # 任務隊列檢查
            health_checks.append({
                "component": "task_queue",
                "status": task_queue_status,
                "message": f"當前有 {len(self._analysis_executions)} 個分析任務",
                "checked_at": datetime.now()
            })
            
            # 結果聚合器檢查
            health_checks.append({
                "component": "result_aggregator",
                "status": result_aggregator_status,
                "message": "結果聚合器運行正常",
                "checked_at": datetime.now()
            })
            
            return AnalystCoordinatorHealth(
                overall_status=overall_status,
                coordinator_status=coordinator_status,
                analyst_registry_status=analyst_registry_status,
                task_queue_status=task_queue_status,
                result_aggregator_status=result_aggregator_status,
                healthy_analysts=healthy_analysts,
                unhealthy_analysts=unhealthy_analysts,
                health_checks=health_checks,
                last_check=datetime.now(),
                uptime=int((datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())
            )
            
        except Exception as e:
            api_logger.error(f"獲取協調器健康狀態失敗: {str(e)}")
            raise
    
    # ==================== 分析師實例管理 ====================
    
    async def get_analyst_instance(self, analyst_id: str) -> Optional[Any]:
        """獲取分析師實例"""
        try:
            # 檢查分析師是否存在
            if analyst_id not in self._analyst_registry:
                return None
            
            # 嘗試導入並實例化分析師
            if analyst_id in self._analyst_modules:
                module_path = self._analyst_modules[analyst_id]
                try:
                    module = importlib.import_module(module_path)
                    
                    # 查找分析師類
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            name.lower().replace('_', '').endswith('analyst') and
                            name != 'BaseAnalyst'):
                            return obj()
                    
                    return None
                    
                except ImportError as e:
                    api_logger.error(f"無法導入分析師模組 {module_path}: {str(e)}")
                    return None
            
            return None
            
        except Exception as e:
            api_logger.error(f"獲取分析師實例失敗: {str(e)}")
            return None
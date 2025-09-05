"""分析師協調服務"""
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """分析類型"""
    QUICK = "quick"          # 快速分析
    COMPREHENSIVE = "comprehensive"  # 綜合分析
    RISK = "risk"           # 風險分析
    FUNDAMENTAL = "fundamental"  # 基本面分析
    TECHNICAL = "technical"   # 技術分析

class AnalysisResult:
    """分析結果類"""
    
    def __init__(
        self, 
        analyst_id: str,
        symbol: str,
        analysis_type: AnalysisType,
        result: Dict[str, Any],
        confidence: float = 0.0,
        execution_time: float = 0.0
    ):
        self.analyst_id = analyst_id
        self.symbol = symbol
        self.analysis_type = analysis_type
        self.result = result
        self.confidence = confidence
        self.execution_time = execution_time
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "analyst_id": self.analyst_id,
            "symbol": self.symbol,
            "analysis_type": self.analysis_type.value,
            "result": self.result,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }

class AnalystCoordinator:
    """分析師協調器"""
    
    def __init__(self):
        self.analysts = {}
        self.performance_tracker = {}
        self.analysis_history = []
        
        # 初始化可用分析師
        self._initialize_analysts()
    
    def _initialize_analysts(self):
        """初始化分析師註冊表"""
        self.analysts = {
            "taiwan_market": {
                "name": "台股市場分析師",
                "description": "專精台灣股市分析",
                "supported_types": [AnalysisType.QUICK, AnalysisType.COMPREHENSIVE],
                "average_confidence": 0.75,
                "average_execution_time": 2.5,
                "success_rate": 0.85,
                "available": True
            },
            "risk_analyst": {
                "name": "風險分析師", 
                "description": "專精風險評估和控制",
                "supported_types": [AnalysisType.RISK, AnalysisType.COMPREHENSIVE],
                "average_confidence": 0.80,
                "average_execution_time": 3.0,
                "success_rate": 0.90,
                "available": True
            },
            "fundamental_analyst": {
                "name": "基本面分析師",
                "description": "專精財務基本面分析",
                "supported_types": [AnalysisType.FUNDAMENTAL, AnalysisType.COMPREHENSIVE],
                "average_confidence": 0.78,
                "average_execution_time": 4.0,
                "success_rate": 0.82,
                "available": True
            },
            "investment_planner": {
                "name": "投資規劃師",
                "description": "專精投資策略規劃",
                "supported_types": [AnalysisType.COMPREHENSIVE],
                "average_confidence": 0.73,
                "average_execution_time": 3.5,
                "success_rate": 0.80,
                "available": True
            }
        }
    
    async def coordinate_analysis(
        self, 
        symbol: str, 
        analysis_type: AnalysisType,
        user_permissions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """協調分析師執行分析
        
        Args:
            symbol: 股票代碼
            analysis_type: 分析類型
            user_permissions: 用戶權限
            
        Returns:
            綜合分析結果
        """
        try:
            logger.info(f"開始協調分析: {symbol} ({analysis_type.value})")
            
            # 選擇適合的分析師
            selected_analysts = self._select_analysts(analysis_type, user_permissions)
            
            if not selected_analysts:
                logger.warning(f"沒有可用的分析師: {analysis_type.value}")
                return {
                    "success": False,
                    "error": "沒有可用的分析師",
                    "symbol": symbol,
                    "analysis_type": analysis_type.value
                }
            
            # 並行執行分析
            analysis_tasks = [
                self._execute_analysis(analyst_id, symbol, analysis_type)
                for analyst_id in selected_analysts
            ]
            
            # 等待所有分析完成
            start_time = datetime.now()
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            total_execution_time = (datetime.now() - start_time).total_seconds()
            
            # 處理分析結果
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "analyst_id": selected_analysts[i],
                        "error": str(result)
                    })
                    logger.error(f"分析師 {selected_analysts[i]} 執行失敗: {result}")
                elif result:
                    successful_results.append(result)
            
            # 綜合分析結果
            coordinated_result = self._combine_analysis_results(
                successful_results, 
                symbol, 
                analysis_type
            )
            
            # 記錄分析歷史
            analysis_record = {
                "symbol": symbol,
                "analysis_type": analysis_type.value,
                "selected_analysts": selected_analysts,
                "successful_count": len(successful_results),
                "failed_count": len(failed_results),
                "total_execution_time": total_execution_time,
                "timestamp": datetime.now(),
                "result": coordinated_result
            }
            
            self.analysis_history.append(analysis_record)
            
            # 更新分析師性能記錄
            await self._update_performance_tracking(successful_results, failed_results)
            
            logger.info(f"分析協調完成: {symbol} ({len(successful_results)}/{len(selected_analysts)} 成功)")
            
            return {
                "success": True,
                "result": coordinated_result,
                "metadata": {
                    "analysts_used": selected_analysts,
                    "successful_analyses": len(successful_results),
                    "total_execution_time": total_execution_time,
                    "analysis_id": len(self.analysis_history)
                }
            }
            
        except Exception as e:
            logger.error(f"分析協調失敗 {symbol}: {e}")
            return {
                "success": False,
                "error": f"協調過程發生錯誤: {str(e)}",
                "symbol": symbol,
                "analysis_type": analysis_type.value
            }
    
    async def get_best_analyst(self, analysis_type: AnalysisType) -> Optional[str]:
        """根據歷史表現選擇最佳分析師
        
        Args:
            analysis_type: 分析類型
            
        Returns:
            最佳分析師ID或None
        """
        try:
            # 過濾支援該分析類型的分析師
            candidates = {
                analyst_id: info 
                for analyst_id, info in self.analysts.items()
                if analysis_type in info["supported_types"] and info["available"]
            }
            
            if not candidates:
                return None
            
            # 根據綜合評分選擇最佳分析師
            best_analyst = None
            best_score = 0
            
            for analyst_id, info in candidates.items():
                # 計算綜合評分 (成功率 * 0.4 + 平均信心度 * 0.3 + 速度評分 * 0.3)
                success_score = info["success_rate"] * 0.4
                confidence_score = info["average_confidence"] * 0.3
                
                # 速度評分 (執行時間越短分數越高)
                max_time = 10.0  # 假設最大執行時間為10秒
                speed_score = max(0, 1 - (info["average_execution_time"] / max_time)) * 0.3
                
                total_score = success_score + confidence_score + speed_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_analyst = analyst_id
            
            logger.debug(f"選擇最佳分析師: {best_analyst} (評分: {best_score:.3f})")
            return best_analyst
            
        except Exception as e:
            logger.error(f"選擇最佳分析師失敗: {e}")
            return None
    
    def _select_analysts(
        self, 
        analysis_type: AnalysisType,
        user_permissions: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """選擇適合的分析師"""
        selected = []
        
        # 根據分析類型選擇分析師
        if analysis_type == AnalysisType.COMPREHENSIVE:
            # 綜合分析使用多個分析師
            for analyst_id, info in self.analysts.items():
                if (analysis_type in info["supported_types"] and 
                    info["available"] and
                    self._check_user_permission(analyst_id, user_permissions)):
                    selected.append(analyst_id)
        else:
            # 其他類型選擇最佳分析師
            best_analyst = asyncio.run(self.get_best_analyst(analysis_type))
            if (best_analyst and 
                self._check_user_permission(best_analyst, user_permissions)):
                selected.append(best_analyst)
        
        return selected
    
    def _check_user_permission(
        self, 
        analyst_id: str, 
        user_permissions: Optional[Dict[str, Any]]
    ) -> bool:
        """檢查用戶是否有權限使用該分析師"""
        if not user_permissions:
            return True  # 預設允許
        
        # 根據分析師類型檢查權限
        advanced_analysts = ["fundamental_analyst", "investment_planner"]
        
        if analyst_id in advanced_analysts:
            return user_permissions.get("advanced_features", False)
        
        return True
    
    async def _execute_analysis(
        self, 
        analyst_id: str, 
        symbol: str, 
        analysis_type: AnalysisType
    ) -> Optional[AnalysisResult]:
        """執行單個分析師的分析"""
        try:
            logger.debug(f"執行分析: {analyst_id} -> {symbol}")
            
            # 模擬分析執行時間
            execution_time = self.analysts[analyst_id]["average_execution_time"]
            await asyncio.sleep(min(execution_time * 0.1, 1.0))  # 模擬延遲
            
            # 模擬分析結果
            result = {
                "recommendation": "HOLD",  # BUY, SELL, HOLD
                "target_price": 100.0,
                "analysis_summary": f"{analyst_id} 對 {symbol} 的分析結果",
                "key_factors": [
                    "因素1：市場趨勢",
                    "因素2：基本面指標", 
                    "因素3：技術指標"
                ],
                "risk_level": "MEDIUM",  # LOW, MEDIUM, HIGH
                "timeframe": "1M"  # 1W, 1M, 3M, 6M, 1Y
            }
            
            # 模擬信心度
            base_confidence = self.analysts[analyst_id]["average_confidence"]
            confidence = min(1.0, base_confidence + (hash(symbol) % 20 - 10) / 100)
            
            analysis_result = AnalysisResult(
                analyst_id=analyst_id,
                symbol=symbol,
                analysis_type=analysis_type,
                result=result,
                confidence=confidence,
                execution_time=execution_time
            )
            
            logger.debug(f"分析完成: {analyst_id} -> {symbol} (信心度: {confidence:.2f})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"執行分析失敗 {analyst_id}: {e}")
            raise e
    
    def _combine_analysis_results(
        self, 
        results: List[AnalysisResult], 
        symbol: str,
        analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """綜合多個分析結果"""
        if not results:
            return {
                "recommendation": "HOLD",
                "confidence": 0.0,
                "summary": "無可用分析結果"
            }
        
        # 計算加權平均
        total_weight = sum(result.confidence for result in results)
        
        if total_weight == 0:
            # 等權重處理
            weights = [1/len(results) for _ in results]
        else:
            weights = [result.confidence / total_weight for result in results]
        
        # 綜合推薦
        recommendations = [result.result.get("recommendation", "HOLD") for result in results]
        recommendation_counts = {}
        for i, rec in enumerate(recommendations):
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + weights[i]
        
        final_recommendation = max(recommendation_counts, key=recommendation_counts.get)
        
        # 綜合信心度
        weighted_confidence = sum(result.confidence * weight for result, weight in zip(results, weights))
        
        # 綜合目標價格
        target_prices = [result.result.get("target_price", 0) for result in results]
        weighted_target_price = sum(price * weight for price, weight in zip(target_prices, weights))
        
        # 收集所有關鍵因素
        all_factors = []
        for result in results:
            factors = result.result.get("key_factors", [])
            all_factors.extend(factors)
        
        combined_result = {
            "recommendation": final_recommendation,
            "confidence": round(weighted_confidence, 3),
            "target_price": round(weighted_target_price, 2),
            "summary": f"基於 {len(results)} 個分析師的綜合分析結果",
            "individual_results": [result.to_dict() for result in results],
            "key_factors": list(set(all_factors)),  # 去重
            "analysis_metadata": {
                "analysts_count": len(results),
                "average_execution_time": sum(r.execution_time for r in results) / len(results),
                "confidence_range": {
                    "min": min(r.confidence for r in results),
                    "max": max(r.confidence for r in results)
                }
            }
        }
        
        return combined_result
    
    async def _update_performance_tracking(
        self, 
        successful_results: List[AnalysisResult],
        failed_results: List[Dict[str, Any]]
    ):
        """更新分析師性能追蹤"""
        # 更新成功分析師的記錄
        for result in successful_results:
            if result.analyst_id not in self.performance_tracker:
                self.performance_tracker[result.analyst_id] = {
                    "total_analyses": 0,
                    "successful_analyses": 0,
                    "total_execution_time": 0,
                    "total_confidence": 0,
                    "last_updated": datetime.now()
                }
            
            tracker = self.performance_tracker[result.analyst_id]
            tracker["total_analyses"] += 1
            tracker["successful_analyses"] += 1
            tracker["total_execution_time"] += result.execution_time
            tracker["total_confidence"] += result.confidence
            tracker["last_updated"] = datetime.now()
            
            # 更新平均值
            self.analysts[result.analyst_id]["average_confidence"] = (
                tracker["total_confidence"] / tracker["successful_analyses"]
            )
            self.analysts[result.analyst_id]["average_execution_time"] = (
                tracker["total_execution_time"] / tracker["successful_analyses"]
            )
            self.analysts[result.analyst_id]["success_rate"] = (
                tracker["successful_analyses"] / tracker["total_analyses"]
            )
        
        # 記錄失敗的分析師
        for failed in failed_results:
            analyst_id = failed["analyst_id"]
            if analyst_id not in self.performance_tracker:
                self.performance_tracker[analyst_id] = {
                    "total_analyses": 0,
                    "successful_analyses": 0,
                    "total_execution_time": 0,
                    "total_confidence": 0,
                    "last_updated": datetime.now()
                }
            
            tracker = self.performance_tracker[analyst_id]
            tracker["total_analyses"] += 1
            tracker["last_updated"] = datetime.now()
            
            # 更新成功率
            if tracker["total_analyses"] > 0:
                self.analysts[analyst_id]["success_rate"] = (
                    tracker["successful_analyses"] / tracker["total_analyses"]
                )
    
    async def get_analyst_performance(self, analyst_id: Optional[str] = None) -> Dict[str, Any]:
        """取得分析師性能報告"""
        if analyst_id:
            # 取得特定分析師的性能
            if analyst_id in self.performance_tracker:
                return {
                    "analyst_id": analyst_id,
                    "performance": self.performance_tracker[analyst_id],
                    "current_stats": self.analysts.get(analyst_id, {})
                }
            else:
                return {"error": f"分析師 {analyst_id} 沒有性能記錄"}
        else:
            # 取得所有分析師的性能總覽
            return {
                "total_analysts": len(self.analysts),
                "performance_summary": self.performance_tracker,
                "current_stats": self.analysts
            }
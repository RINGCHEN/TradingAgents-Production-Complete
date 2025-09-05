"""
Intelligence Module - 智能任務團隊
AI Training Expert Team Intelligence System

智能任務團隊模組
負責人: 小k (AI訓練專家團隊)

提供：
- AI任務分析和分類 (Task 6.1)
- 成本效益計算引擎 (Task 6.2)  
- 性能預測和路由決策 (Task 6.3)
"""

from .task_analyzer import (
    TaskAnalyzer,
    TaskAnalysisResult,
    TaskType,
    TaskComplexity,
    TaskPriority,
    ResourceRequirement,
    analyze_single_task,
    create_task_analysis_report
)

from .cost_calculator import (
    CostCalculator,
    CostComparisonResult,
    DeploymentMode,
    HardwareSpec,
    CloudAPISpec,
    TaskWorkload,
    CostBreakdown,
    ROIAnalysis,
    quick_cost_comparison,
    calculate_break_even_point
)

from .performance_predictor import (
    PerformancePredictor,
    LoadForecaster,
    RoutingDecisionEngine,
    PerformanceData,
    PerformancePrediction,
    RoutingDecision,
    LoadForecast,
    PerformanceMetric,
    RoutingStrategy,
    create_performance_data_sample,
    quick_routing_decision
)

__version__ = "1.0.0"
__author__ = "小k (AI訓練專家團隊)"

# 模組級別的便利函數
def create_intelligent_routing_system():
    """創建完整的智能路由系統"""
    return IntelligentRoutingSystem()

class IntelligentRoutingSystem:
    """智能路由系統整合類"""
    
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.cost_calculator = CostCalculator()
        self.performance_predictor = PerformancePredictor()
        self.load_forecaster = LoadForecaster()
        self.routing_engine = RoutingDecisionEngine()
        
        # 系統統計
        self.total_tasks_processed = 0
        self.successful_routes = 0
        self.cost_savings_total = 0.0
    
    def process_task_request(
        self,
        task_name: str,
        task_description: str,
        hardware_model: str = 'rtx_4070',
        api_model: str = 'openai_gpt3_5',
        routing_strategy: RoutingStrategy = RoutingStrategy.BALANCED
    ) -> dict:
        """處理完整的任務請求"""
        
        # 1. 任務分析
        task_analysis = self.task_analyzer.analyze_task(
            task_id=f"task_{self.total_tasks_processed + 1}",
            task_name=task_name,
            task_description=task_description
        )
        
        # 2. 成本對比分析
        hardware_spec = self.cost_calculator.hardware_calculator.hardware_specs.get(hardware_model)
        api_spec = self.cost_calculator.cloud_calculator.api_specs.get(api_model)
        
        if not hardware_spec or not api_spec:
            raise ValueError("Invalid hardware or API model")
        
        # 創建工作負載
        workload = TaskWorkload(
            task_name=task_name,
            input_tokens_per_request=1000,
            output_tokens_per_request=500,
            requests_per_hour=100,
            gpu_utilization_percent=80.0,
            processing_time_seconds=2.0
        )
        
        cost_comparison = self.cost_calculator.compare_deployment_costs(
            hardware_spec, api_spec, workload
        )
        
        # 3. 路由決策
        routing_decision = self.routing_engine.make_routing_decision(
            task_analysis, cost_comparison, routing_strategy
        )
        
        # 4. 更新統計
        self.total_tasks_processed += 1
        if routing_decision.confidence_score > 0.7:
            self.successful_routes += 1
        self.cost_savings_total += float(cost_comparison.cost_savings)
        
        # 5. 返回完整結果
        return {
            "task_analysis": task_analysis.to_dict(),
            "cost_comparison": cost_comparison.to_dict(),
            "routing_decision": routing_decision.to_dict(),
            "system_stats": {
                "total_tasks_processed": self.total_tasks_processed,
                "successful_routes": self.successful_routes,
                "success_rate": self.successful_routes / self.total_tasks_processed if self.total_tasks_processed > 0 else 0,
                "total_cost_savings": self.cost_savings_total
            }
        }
    
    def get_system_status(self) -> dict:
        """獲取系統狀態"""
        return {
            "task_analyzer": {
                "total_analyzed": len(self.task_analyzer.analysis_history),
                "analysis_summary": self.task_analyzer.get_analysis_summary()
            },
            "cost_calculator": {
                "total_calculations": len(self.cost_calculator.calculation_history),
                "average_savings": sum(float(c.cost_savings) for c in self.cost_calculator.calculation_history) / len(self.cost_calculator.calculation_history) if self.cost_calculator.calculation_history else 0
            },
            "routing_engine": self.routing_engine.get_decision_analytics(),
            "system_performance": {
                "total_tasks_processed": self.total_tasks_processed,
                "successful_routes": self.successful_routes,
                "success_rate": self.successful_routes / self.total_tasks_processed if self.total_tasks_processed > 0 else 0,
                "total_cost_savings": self.cost_savings_total
            }
        }

# 導出主要類和函數
__all__ = [
    # Task Analyzer
    'TaskAnalyzer',
    'TaskAnalysisResult', 
    'TaskType',
    'TaskComplexity',
    'TaskPriority',
    'ResourceRequirement',
    'analyze_single_task',
    'create_task_analysis_report',
    
    # Cost Calculator
    'CostCalculator',
    'CostComparisonResult',
    'DeploymentMode',
    'HardwareSpec',
    'CloudAPISpec', 
    'TaskWorkload',
    'CostBreakdown',
    'ROIAnalysis',
    'quick_cost_comparison',
    'calculate_break_even_point',
    
    # Performance Predictor
    'PerformancePredictor',
    'LoadForecaster',
    'RoutingDecisionEngine',
    'PerformanceData',
    'PerformancePrediction',
    'RoutingDecision',
    'LoadForecast',
    'PerformanceMetric',
    'RoutingStrategy',
    'create_performance_data_sample',
    'quick_routing_decision',
    
    # Integrated System
    'IntelligentRoutingSystem',
    'create_intelligent_routing_system'
]
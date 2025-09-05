#!/usr/bin/env python3
"""
Task Standards and Quality Thresholds
任务标准和质量门槛定义
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from .task_metadata_models import TaskType, DataSensitivityLevel, BusinessPriority, TaskCategory

@dataclass
class QualityThreshold:
    """质量门槛定义"""
    min_accuracy: float  # 最低准确率
    min_relevance: float  # 最低相关性
    min_completeness: float  # 最低完整性
    min_coherence: float  # 最低连贯性
    max_hallucination_rate: float  # 最大幻觉率
    
    def overall_score(self) -> float:
        """计算综合质量评分"""
        return (self.min_accuracy + self.min_relevance + self.min_completeness + self.min_coherence) / 4

@dataclass
class LatencyRequirement:
    """延迟要求定义"""
    target_ms: int  # 目标延迟
    max_acceptable_ms: int  # 最大可接受延迟
    p95_threshold_ms: int  # 95%分位延迟阈值
    timeout_ms: int  # 超时阈值
    
    def is_acceptable(self, actual_ms: int) -> bool:
        """判断延迟是否可接受"""
        return actual_ms <= self.max_acceptable_ms

@dataclass
class CostThreshold:
    """成本门槛定义"""
    target_per_1k_tokens: float  # 目标每1K tokens成本
    max_per_1k_tokens: float  # 最大每1K tokens成本
    budget_alert_threshold: float  # 预算警告阈值
    
    def is_acceptable(self, actual_cost: float) -> bool:
        """判断成本是否可接受"""
        return actual_cost <= self.max_per_1k_tokens

@dataclass
class TaskStandard:
    """任务标准定义"""
    task_type: str
    name: str
    description: str
    category: TaskCategory
    quality_threshold: QualityThreshold
    latency_requirement: LatencyRequirement
    cost_threshold: CostThreshold
    data_sensitivity: DataSensitivityLevel
    business_priority: BusinessPriority
    required_features: List[str]
    evaluation_metrics: List[str]
    example_inputs: List[str]
    example_outputs: List[str]
    
class TaskStandardRegistry:
    """任务标准注册表"""
    
    def __init__(self):
        self._standards = {}
        self._initialize_standards()
    
    def _initialize_standards(self):
        """初始化标准任务类型定义"""
        
        # ==================== 摘要任务 ====================
        self._standards["financial_summary"] = TaskStandard(
            task_type="financial_summary",
            name="财务摘要",
            description="对公司财务数据进行摘要分析，提取关键指标和趋势",
            category=TaskCategory.BATCH,
            quality_threshold=QualityThreshold(
                min_accuracy=0.85,
                min_relevance=0.80,
                min_completeness=0.75,
                min_coherence=0.80,
                max_hallucination_rate=0.05
            ),
            latency_requirement=LatencyRequirement(
                target_ms=8000,
                max_acceptable_ms=15000,
                p95_threshold_ms=12000,
                timeout_ms=20000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.01,
                max_per_1k_tokens=0.02,
                budget_alert_threshold=0.015
            ),
            data_sensitivity=DataSensitivityLevel.MEDIUM,
            business_priority=BusinessPriority.IMPORTANT,
            required_features=["reasoning", "math", "analysis"],
            evaluation_metrics=[
                "factual_accuracy", "numerical_precision", "trend_identification",
                "key_metrics_coverage", "executive_summary_quality"
            ],
            example_inputs=[
                "台积电2023年财务报表数据",
                "鸿海季度收益数据和市场表现",
                "台股科技股板块财务指标比较"
            ],
            example_outputs=[
                "台积电2023年营收增长15%，净利润率提升至37%，主要受惠于AI芯片需求增长...",
                "鸿海Q4营收达1.2兆台币，同比增长8%，EPS达4.5元，超出市场预期...",
                "台股科技股板块平均ROE为18.5%，其中半导体子板块表现最优..."
            ]
        )
        
        self._standards["news_summary"] = TaskStandard(
            task_type="news_summary",
            name="新闻摘要",
            description="对财经新闻进行摘要，提取关键信息和市场影响",
            category=TaskCategory.REAL_TIME,
            quality_threshold=QualityThreshold(
                min_accuracy=0.80,
                min_relevance=0.85,
                min_completeness=0.70,
                min_coherence=0.75,
                max_hallucination_rate=0.08
            ),
            latency_requirement=LatencyRequirement(
                target_ms=3000,
                max_acceptable_ms=8000,
                p95_threshold_ms=6000,
                timeout_ms=10000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.005,
                max_per_1k_tokens=0.01,
                budget_alert_threshold=0.008
            ),
            data_sensitivity=DataSensitivityLevel.LOW,
            business_priority=BusinessPriority.STANDARD,
            required_features=["language_understanding", "summarization"],
            evaluation_metrics=[
                "information_completeness", "relevance_score", "readability",
                "market_impact_identification", "timeline_accuracy"
            ],
            example_inputs=[
                "联发科宣布新款5G芯片上市的新闻报导",
                "央行升息对房市影响的相关新闻",
                "美股科技股大跌对台股影响的分析报导"
            ],
            example_outputs=[
                "联发科发布天玑9200芯片，采用台积电4nm制程，性能提升20%，预期将带动Q2营收增长...",
                "央行升息半码至1.875%，房市交易量预期下降15%，建商股价面临压力...",
                "美股那斯达克指数下跌2.5%，台股ADR全面走跌，预期今日开盘承压..."
            ]
        )
        
        # ==================== 分类任务 ====================
        self._standards["news_classification"] = TaskStandard(
            task_type="news_classification",
            name="新闻分类",
            description="对新闻文章进行主题分类和情感分析",
            category=TaskCategory.REAL_TIME,
            quality_threshold=QualityThreshold(
                min_accuracy=0.88,
                min_relevance=0.85,
                min_completeness=0.90,
                min_coherence=0.80,
                max_hallucination_rate=0.03
            ),
            latency_requirement=LatencyRequirement(
                target_ms=2000,
                max_acceptable_ms=5000,
                p95_threshold_ms=3500,
                timeout_ms=8000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.003,
                max_per_1k_tokens=0.008,
                budget_alert_threshold=0.006
            ),
            data_sensitivity=DataSensitivityLevel.LOW,
            business_priority=BusinessPriority.STANDARD,
            required_features=["classification", "sentiment_analysis"],
            evaluation_metrics=[
                "classification_accuracy", "sentiment_accuracy", "confidence_score",
                "multi_label_precision", "category_coverage"
            ],
            example_inputs=[
                "台积电法说会释出积极信号，看好AI晶片前景",
                "通膨持续升温，央行可能再度升息",
                "房地产市场降温，建商推案轉趨保守"
            ],
            example_outputs=[
                "分类: 科技股/半导体, 情感: 正面(0.85), 影响: 个股利好",
                "分类: 总体经济/货币政策, 情感: 中性偏负面(0.35), 影响: 市场不确定性",
                "分类: 房地产/建筑业, 情感: 负面(0.25), 影响: 板块利空"
            ]
        )
        
        self._standards["risk_classification"] = TaskStandard(
            task_type="risk_classification",
            name="风险分类",
            description="对投资风险进行分类和等级评估",
            category=TaskCategory.INTERACTIVE,
            quality_threshold=QualityThreshold(
                min_accuracy=0.92,
                min_relevance=0.90,
                min_completeness=0.88,
                min_coherence=0.85,
                max_hallucination_rate=0.02
            ),
            latency_requirement=LatencyRequirement(
                target_ms=4000,
                max_acceptable_ms=10000,
                p95_threshold_ms=8000,
                timeout_ms=15000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.008,
                max_per_1k_tokens=0.015,
                budget_alert_threshold=0.012
            ),
            data_sensitivity=DataSensitivityLevel.HIGH,
            business_priority=BusinessPriority.CRITICAL,
            required_features=["risk_analysis", "classification", "reasoning"],
            evaluation_metrics=[
                "risk_category_accuracy", "severity_assessment", "probability_estimation",
                "impact_evaluation", "recommendation_quality"
            ],
            example_inputs=[
                "客户投资组合包含80%科技股的风险评估",
                "新兴市场债券基金的风险分析",
                "加密货币投资占总资产30%的风险等级"
            ],
            example_outputs=[
                "风险类型: 集中度风险, 等级: 高风险, 建议: 分散投资至其他板块",
                "风险类型: 信用风险/汇率风险, 等级: 中高风险, 建议: 控制部位在10%以下",
                "风险类型: 市场风险/流动性风险, 等级: 极高风险, 建议: 立即降低至5%以下"
            ]
        )
        
        # ==================== 推理任务 ====================
        self._standards["investment_reasoning"] = TaskStandard(
            task_type="investment_reasoning",
            name="投资推理",
            description="基于市场数据和财务分析进行投资决策推理",
            category=TaskCategory.INTERACTIVE,
            quality_threshold=QualityThreshold(
                min_accuracy=0.90,
                min_relevance=0.92,
                min_completeness=0.85,
                min_coherence=0.88,
                max_hallucination_rate=0.03
            ),
            latency_requirement=LatencyRequirement(
                target_ms=12000,
                max_acceptable_ms=25000,
                p95_threshold_ms=20000,
                timeout_ms=30000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.015,
                max_per_1k_tokens=0.03,
                budget_alert_threshold=0.025
            ),
            data_sensitivity=DataSensitivityLevel.HIGH,
            business_priority=BusinessPriority.CRITICAL,
            required_features=["reasoning", "analysis", "math", "decision_making"],
            evaluation_metrics=[
                "reasoning_logic", "evidence_quality", "conclusion_validity",
                "risk_consideration", "actionability"
            ],
            example_inputs=[
                "台积电股价在AI热潮下是否仍具投资价值？",
                "升息环境下如何配置債券投资？",
                "ESG投資策略在台股市場的適用性分析"
            ],
            example_outputs=[
                "基于以下分析：1)AI晶片需求強勁，預估2024年營收成長15% 2)本益比18倍仍合理 3)技術護城河深厚，建議: 逢低分批買進",
                "升息環境建議：1)縮短久期至3-5年 2)提高信評要求至BBB以上 3)考慮浮動利率債券，目標配置30%",
                "ESG在台股具三大優勢：1)半導體業ESG轉型領先 2)政策支持綠色金融 3)ESG ETF選擇多元，建議配置20%"
            ]
        )
        
        self._standards["market_analysis_reasoning"] = TaskStandard(
            task_type="market_analysis_reasoning",
            name="市场分析推理",
            description="对市场趋势进行深度分析和推理预测",
            category=TaskCategory.BATCH,
            quality_threshold=QualityThreshold(
                min_accuracy=0.85,
                min_relevance=0.88,
                min_completeness=0.80,
                min_coherence=0.85,
                max_hallucination_rate=0.04
            ),
            latency_requirement=LatencyRequirement(
                target_ms=15000,
                max_acceptable_ms=30000,
                p95_threshold_ms=25000,
                timeout_ms=35000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.012,
                max_per_1k_tokens=0.025,
                budget_alert_threshold=0.02
            ),
            data_sensitivity=DataSensitivityLevel.MEDIUM,
            business_priority=BusinessPriority.IMPORTANT,
            required_features=["market_analysis", "reasoning", "trend_prediction"],
            evaluation_metrics=[
                "trend_identification", "causality_analysis", "prediction_reasoning",
                "market_factor_consideration", "scenario_analysis"
            ],
            example_inputs=[
                "分析台股2024年走势和主要影响因素",
                "美中贸易关系对半导体股的长期影响",
                "通胀走势对不同資產類別的影響分析"
            ],
            example_outputs=[
                "台股2024年預期：1)AI續航帶動科技股 2)內需復甦支撐傳產 3)目標區間16000-18000點，關鍵變數為Fed政策轉向時點",
                "美中科技競爭長期化：1)台積電地位更加重要 2)供應鏈在地化趨勢 3)建議聚焦具技術護城河個股",
                "通脹影響分析：1)股票:金融受惠升息 2)債券:短期優於長期 3)商品:能源表現突出，建議動態調整配置"
            ]
        )
        
        # ==================== 生成任务 ====================
        self._standards["report_generation"] = TaskStandard(
            task_type="report_generation",
            name="报告生成",
            description="生成专业的投资分析报告",
            category=TaskCategory.BATCH,
            quality_threshold=QualityThreshold(
                min_accuracy=0.88,
                min_relevance=0.85,
                min_completeness=0.90,
                min_coherence=0.92,
                max_hallucination_rate=0.03
            ),
            latency_requirement=LatencyRequirement(
                target_ms=18000,
                max_acceptable_ms=40000,
                p95_threshold_ms=32000,
                timeout_ms=45000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.018,
                max_per_1k_tokens=0.035,
                budget_alert_threshold=0.028
            ),
            data_sensitivity=DataSensitivityLevel.MEDIUM,
            business_priority=BusinessPriority.IMPORTANT,
            required_features=["report_writing", "formatting", "analysis"],
            evaluation_metrics=[
                "structure_quality", "content_depth", "professional_tone",
                "data_integration", "actionable_insights"
            ],
            example_inputs=[
                "為台積電生成投資分析報告",
                "撰寫台股科技板塊月度報告",
                "製作ESG投資策略報告"
            ],
            example_outputs=[
                "# 台積電投資分析報告\n## 公司概況\n台積電為全球晶圓代工龍頭...\n## 財務分析\n營收連續三季成長...\n## 投資建議\n目標價580元，建議買進",
                "# 台股科技板塊月度分析\n## 市場表現\n科技股指數上漲8.5%...\n## 個股亮點\n台積電、聯發科領漲...\n## 展望\nAI題材續熱",
                "# ESG投資策略報告\n## 市場趨勢\nESG基金規模持續擴大...\n## 投資機會\n綠能、永續科技...\n## 配置建議\n建議配置20-30%"
            ]
        )
        
        self._standards["strategy_generation"] = TaskStandard(
            task_type="strategy_generation",
            name="策略生成",
            description="生成個人化的投資策略建議",
            category=TaskCategory.INTERACTIVE,
            quality_threshold=QualityThreshold(
                min_accuracy=0.86,
                min_relevance=0.90,
                min_completeness=0.85,
                min_coherence=0.88,
                max_hallucination_rate=0.04
            ),
            latency_requirement=LatencyRequirement(
                target_ms=10000,
                max_acceptable_ms=20000,
                p95_threshold_ms=16000,
                timeout_ms=25000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.012,
                max_per_1k_tokens=0.022,
                budget_alert_threshold=0.018
            ),
            data_sensitivity=DataSensitivityLevel.HIGH,
            business_priority=BusinessPriority.CRITICAL,
            required_features=["personalization", "strategy_planning", "risk_assessment"],
            evaluation_metrics=[
                "personalization_quality", "strategy_feasibility", "risk_alignment",
                "goal_alignment", "implementation_clarity"
            ],
            example_inputs=[
                "35歲工程師，月薪10萬，風險承受度中等的投資策略",
                "退休族群，資產1000萬，保守型投資策略",
                "高淨值客戶，積極成長型投資策略"
            ],
            example_outputs=[
                "建議配置：股票60%(台股40%+海外20%)、債券30%、現金10%。重點標的：0050、VTI、台債ETF。每月定期定額5萬元",
                "建議配置：債券60%、股票30%、現金10%。著重穩定收益，年化報酬目標4-6%。重點：高評級債券、股息股",
                "建議配置：股票80%、另類投資15%、現金5%。聚焦成長股、新興科技、私募股權。目標年化報酬12%以上"
            ]
        )
        
        # ==================== 情感分析任务 ====================
        self._standards["market_sentiment"] = TaskStandard(
            task_type="market_sentiment",
            name="市场情感分析",
            description="分析市场新闻和社交媒体的情感倾向",
            category=TaskCategory.REAL_TIME,
            quality_threshold=QualityThreshold(
                min_accuracy=0.82,
                min_relevance=0.85,
                min_completeness=0.78,
                min_coherence=0.80,
                max_hallucination_rate=0.06
            ),
            latency_requirement=LatencyRequirement(
                target_ms=1500,
                max_acceptable_ms=4000,
                p95_threshold_ms=3000,
                timeout_ms=6000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.003,
                max_per_1k_tokens=0.008,
                budget_alert_threshold=0.006
            ),
            data_sensitivity=DataSensitivityLevel.LOW,
            business_priority=BusinessPriority.STANDARD,
            required_features=["sentiment_analysis", "social_media_analysis"],
            evaluation_metrics=[
                "sentiment_accuracy", "intensity_measurement", "market_relevance",
                "temporal_consistency", "source_credibility"
            ],
            example_inputs=[
                "台積電法說會後網路討論情況",
                "央行升息決策的市場反應",
                "科技股回調的投資人情緒"
            ],
            example_outputs=[
                "整體情感: 正面(0.75), 討論熱度: 高, 關鍵字: AI晶片、營收成長、技術領先. 投資人信心指數: 82/100",
                "整體情感: 負面(0.32), 討論熱度: 中高, 關鍵字: 升息壓力、房市降溫、經濟衰退. 不確定性指數: 68/100",
                "整體情感: 恐慌(0.18), 討論熱度: 極高, 關鍵字: 泡沫破裂、技術修正、逢低買進. 恐慌指數: 73/100"
            ]
        )
        
        # ==================== 技术分析任务 ====================
        self._standards["technical_analysis"] = TaskStandard(
            task_type="technical_analysis",
            name="技术分析",
            description="基于技术指标进行股价分析和预测",
            category=TaskCategory.REAL_TIME,
            quality_threshold=QualityThreshold(
                min_accuracy=0.80,
                min_relevance=0.83,
                min_completeness=0.85,
                min_coherence=0.82,
                max_hallucination_rate=0.05
            ),
            latency_requirement=LatencyRequirement(
                target_ms=5000,
                max_acceptable_ms=12000,
                p95_threshold_ms=10000,
                timeout_ms=15000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.008,
                max_per_1k_tokens=0.015,
                budget_alert_threshold=0.012
            ),
            data_sensitivity=DataSensitivityLevel.MEDIUM,
            business_priority=BusinessPriority.IMPORTANT,
            required_features=["technical_analysis", "chart_interpretation", "math"],
            evaluation_metrics=[
                "indicator_interpretation", "pattern_recognition", "signal_accuracy",
                "trend_identification", "support_resistance_accuracy"
            ],
            example_inputs=[
                "分析台積電日線圖的技術訊號",
                "大盤指數的波浪理論分析",
                "半導體指數的技術指標背離現象"
            ],
            example_outputs=[
                "技術分析: RSI(65)偏強勢, MACD黃金交叉, 均線多頭排列. 支撐520, 壓力580. 建議: 突破580追進",
                "波浪分析: 目前處於第5波上漲末段, 預期修正至16200-15800區間後再創高點. 操作: 逢高減碼",
                "背離訊號: 指數創新高但RSI走低, 顯示動能減弱. 建議: 提高警戒, 控制部位至70%"
            ]
        )
        
        # ==================== 风险评估任务 ====================
        self._standards["portfolio_risk_assessment"] = TaskStandard(
            task_type="portfolio_risk_assessment",
            name="投资组合风险评估",
            description="对投资组合进行全面的风险分析和评估",
            category=TaskCategory.BATCH,
            quality_threshold=QualityThreshold(
                min_accuracy=0.92,
                min_relevance=0.90,
                min_completeness=0.88,
                min_coherence=0.86,
                max_hallucination_rate=0.02
            ),
            latency_requirement=LatencyRequirement(
                target_ms=20000,
                max_acceptable_ms=40000,
                p95_threshold_ms=32000,
                timeout_ms=45000
            ),
            cost_threshold=CostThreshold(
                target_per_1k_tokens=0.015,
                max_per_1k_tokens=0.03,
                budget_alert_threshold=0.025
            ),
            data_sensitivity=DataSensitivityLevel.HIGH,
            business_priority=BusinessPriority.CRITICAL,
            required_features=["risk_analysis", "portfolio_analysis", "math", "statistics"],
            evaluation_metrics=[
                "risk_metric_accuracy", "scenario_analysis_quality", "diversification_assessment",
                "correlation_analysis", "recommendation_practicality"
            ],
            example_inputs=[
                "評估包含台積電30%、鴻海20%、聯發科15%的投資組合風險",
                "分析債券60%、股票40%的保守型組合風險特徵",
                "評估多元資產配置組合的尾部風險"
            ],
            example_outputs=[
                "組合風險分析: VaR(95%)=8.2%, 最大回檔風險25%. 風險集中: 科技股65%過度集中. 建議: 分散至金融、傳產板塊",
                "保守組合分析: 波動度12%, 相關性0.3偏低. 風險特徵: 利率敏感度高. 建議: 縮短債券久期至3-5年",
                "多元組合評估: 尾部風險控制良好, 最大損失12%. 各資產相關性<0.6. 建議: 現有配置適當, 持續再平衡"
            ]
        )
    
    def get_standard(self, task_type: str) -> Optional[TaskStandard]:
        """获取任务标准"""
        return self._standards.get(task_type)
    
    def list_all_standards(self) -> Dict[str, TaskStandard]:
        """列出所有任务标准"""
        return self._standards.copy()
    
    def get_standards_by_category(self, category: TaskCategory) -> Dict[str, TaskStandard]:
        """按分类获取任务标准"""
        return {
            task_type: standard
            for task_type, standard in self._standards.items()
            if standard.category == category
        }
    
    def get_standards_by_priority(self, priority: BusinessPriority) -> Dict[str, TaskStandard]:
        """按优先级获取任务标准"""
        return {
            task_type: standard
            for task_type, standard in self._standards.items()
            if standard.business_priority == priority
        }
    
    def validate_task_performance(
        self,
        task_type: str,
        actual_latency: int,
        actual_cost: float,
        quality_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        验证任务性能是否符合标准
        
        Args:
            task_type: 任务类型
            actual_latency: 实际延迟(ms)
            actual_cost: 实际成本(per 1k tokens)
            quality_scores: 质量评分字典
            
        Returns:
            验证结果
        """
        standard = self.get_standard(task_type)
        if not standard:
            return {"valid": False, "reason": f"Unknown task type: {task_type}"}
        
        validation_result = {
            "valid": True,
            "task_type": task_type,
            "violations": [],
            "warnings": [],
            "scores": {}
        }
        
        # 验证延迟
        if actual_latency > standard.latency_requirement.max_acceptable_ms:
            validation_result["valid"] = False
            validation_result["violations"].append(
                f"Latency {actual_latency}ms exceeds maximum {standard.latency_requirement.max_acceptable_ms}ms"
            )
        elif actual_latency > standard.latency_requirement.target_ms:
            validation_result["warnings"].append(
                f"Latency {actual_latency}ms exceeds target {standard.latency_requirement.target_ms}ms"
            )
        
        validation_result["scores"]["latency_score"] = max(0, 1 - (actual_latency / standard.latency_requirement.max_acceptable_ms))
        
        # 验证成本
        if actual_cost > standard.cost_threshold.max_per_1k_tokens:
            validation_result["valid"] = False
            validation_result["violations"].append(
                f"Cost ${actual_cost:.4f} exceeds maximum ${standard.cost_threshold.max_per_1k_tokens:.4f}"
            )
        elif actual_cost > standard.cost_threshold.target_per_1k_tokens:
            validation_result["warnings"].append(
                f"Cost ${actual_cost:.4f} exceeds target ${standard.cost_threshold.target_per_1k_tokens:.4f}"
            )
        
        validation_result["scores"]["cost_score"] = max(0, 1 - (actual_cost / standard.cost_threshold.max_per_1k_tokens))
        
        # 验证质量
        if quality_scores:
            quality_threshold = standard.quality_threshold
            overall_quality = sum(quality_scores.values()) / len(quality_scores)
            target_quality = quality_threshold.overall_score()
            
            if overall_quality < target_quality:
                validation_result["valid"] = False
                validation_result["violations"].append(
                    f"Quality score {overall_quality:.2f} below threshold {target_quality:.2f}"
                )
            
            validation_result["scores"]["quality_score"] = overall_quality
            validation_result["scores"]["quality_breakdown"] = quality_scores
        
        # 计算综合评分
        scores = validation_result["scores"]
        if "quality_score" in scores:
            validation_result["overall_score"] = (
                scores["latency_score"] * 0.3 +
                scores["cost_score"] * 0.3 +
                scores["quality_score"] * 0.4
            )
        else:
            validation_result["overall_score"] = (
                scores["latency_score"] * 0.5 +
                scores["cost_score"] * 0.5
            )
        
        return validation_result

# 全局任务标准注册表实例
task_standard_registry = TaskStandardRegistry()
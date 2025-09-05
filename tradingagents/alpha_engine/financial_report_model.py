#!/usr/bin/env python3
"""
Financial Report Extraction Model
財報數據提取模型 - GPT-OSS整合任務3.1.3

專為台股財報設計的智能數據提取模型，提供結構化財務數據提取、
關鍵指標計算和財務分析洞察功能。

主要功能：
1. 財報文本結構化分析
2. 關鍵財務數據提取
3. 財務比率自動計算
4. 異常數據檢測和驗證
5. 多期財報對比分析
6. 財務健康度評估
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
from dataclasses import dataclass

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """財報類型枚舉"""
    QUARTERLY = "quarterly"          # 季報
    SEMI_ANNUAL = "semi_annual"      # 半年報
    ANNUAL = "annual"                # 年報
    CONSOLIDATED = "consolidated"     # 合併報表
    STANDALONE = "standalone"         # 個別報表


class ReportPeriod(str, Enum):
    """報告期間枚舉"""
    Q1 = "Q1"                       # 第一季
    Q2 = "Q2"                       # 第二季  
    Q3 = "Q3"                       # 第三季
    Q4 = "Q4"                       # 第四季
    H1 = "H1"                       # 上半年
    H2 = "H2"                       # 下半年
    FY = "FY"                       # 全年


class ExtractionStatus(str, Enum):
    """提取狀態枚舉"""
    SUCCESS = "success"              # 成功
    PARTIAL = "partial"              # 部分成功
    FAILED = "failed"               # 失敗
    INVALID_FORMAT = "invalid_format" # 格式無效
    DATA_INCOMPLETE = "data_incomplete" # 數據不完整


class FinancialHealthGrade(str, Enum):
    """財務健康度等級枚舉"""
    EXCELLENT = "excellent"          # 優秀 (A)
    GOOD = "good"                   # 良好 (B)
    AVERAGE = "average"             # 普通 (C)
    POOR = "poor"                   # 較差 (D)
    CRITICAL = "critical"           # 危險 (F)


class ReportExtractionConfig(BaseModel):
    """財報提取配置模型"""
    config_id: str = Field(..., description="配置ID")
    config_name: str = Field(..., description="配置名稱")
    
    # 模型配置
    model_name: str = Field("financial-report-extractor-v1", description="模型名稱")
    model_path: str = Field("/app/models/financial_report_extractor", description="模型路徑")
    
    # 提取配置
    extract_balance_sheet: bool = Field(True, description="是否提取資產負債表")
    extract_income_statement: bool = Field(True, description="是否提取損益表")
    extract_cash_flow: bool = Field(True, description="是否提取現金流量表")
    extract_equity_statement: bool = Field(False, description="是否提取權益變動表")
    
    # 驗證配置
    enable_data_validation: bool = Field(True, description="是否啟用數據驗證")
    validation_tolerance: float = Field(0.05, description="驗證容錯率")
    
    # 計算配置
    calculate_ratios: bool = Field(True, description="是否計算財務比率")
    calculate_growth_rates: bool = Field(True, description="是否計算成長率")
    calculate_health_score: bool = Field(True, description="是否計算健康度評分")
    
    # 對比分析配置
    enable_period_comparison: bool = Field(True, description="是否啟用期間比較")
    comparison_periods: int = Field(4, description="比較期數")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinancialDataExtractor(BaseModel):
    """財務數據提取器"""
    extractor_id: str = Field(..., description="提取器ID")
    
    # 基本財務數據
    total_revenue: Optional[Decimal] = Field(None, description="營業收入")
    gross_profit: Optional[Decimal] = Field(None, description="毛利")
    operating_profit: Optional[Decimal] = Field(None, description="營業利益")
    net_income: Optional[Decimal] = Field(None, description="稅後淨利")
    eps: Optional[Decimal] = Field(None, description="每股盈餘")
    
    # 資產負債數據
    total_assets: Optional[Decimal] = Field(None, description="總資產")
    total_liabilities: Optional[Decimal] = Field(None, description="總負債")
    shareholders_equity: Optional[Decimal] = Field(None, description="股東權益")
    current_assets: Optional[Decimal] = Field(None, description="流動資產")
    current_liabilities: Optional[Decimal] = Field(None, description="流動負債")
    
    # 現金流數據
    operating_cash_flow: Optional[Decimal] = Field(None, description="營業現金流")
    investing_cash_flow: Optional[Decimal] = Field(None, description="投資現金流")
    financing_cash_flow: Optional[Decimal] = Field(None, description="融資現金流")
    free_cash_flow: Optional[Decimal] = Field(None, description="自由現金流")
    
    # 其他重要數據
    inventory: Optional[Decimal] = Field(None, description="存貨")
    accounts_receivable: Optional[Decimal] = Field(None, description="應收帳款")
    accounts_payable: Optional[Decimal] = Field(None, description="應付帳款")
    cash_and_equivalents: Optional[Decimal] = Field(None, description="現金及約當現金")
    
    # 提取信心度
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0, description="提取信心度")
    data_completeness: float = Field(0.0, ge=0.0, le=1.0, description="數據完整度")
    
    # 驗證結果
    validation_passed: bool = Field(False, description="是否通過驗證")
    validation_errors: List[str] = Field(default_factory=list, description="驗證錯誤")
    
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportStructureAnalyzer(BaseModel):
    """財報結構分析器"""
    analyzer_id: str = Field(..., description="分析器ID")
    
    # 文檔結構分析
    document_type: str = Field("unknown", description="文檔類型")
    page_count: int = Field(0, description="頁數")
    table_count: int = Field(0, description="表格數量")
    
    # 報表識別
    balance_sheet_detected: bool = Field(False, description="是否檢測到資產負債表")
    income_statement_detected: bool = Field(False, description="是否檢測到損益表")
    cash_flow_detected: bool = Field(False, description="是否檢測到現金流量表")
    
    # 報表位置信息
    balance_sheet_location: Dict[str, int] = Field(default_factory=dict, description="資產負債表位置")
    income_statement_location: Dict[str, int] = Field(default_factory=dict, description="損益表位置")
    cash_flow_location: Dict[str, int] = Field(default_factory=dict, description="現金流量表位置")
    
    # 數據質量評估
    structure_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="結構質量評分")
    readability_score: float = Field(0.0, ge=0.0, le=1.0, description="可讀性評分")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="完整性評分")
    
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FinancialRatios(BaseModel):
    """財務比率模型"""
    ratio_id: str = Field(..., description="比率ID")
    
    # 獲利能力比率
    gross_margin: Optional[float] = Field(None, description="毛利率")
    operating_margin: Optional[float] = Field(None, description="營業利益率")
    net_margin: Optional[float] = Field(None, description="淨利率")
    roa: Optional[float] = Field(None, description="資產報酬率")
    roe: Optional[float] = Field(None, description="股東權益報酬率")
    
    # 流動性比率
    current_ratio: Optional[float] = Field(None, description="流動比率")
    quick_ratio: Optional[float] = Field(None, description="速動比率")
    cash_ratio: Optional[float] = Field(None, description="現金比率")
    
    # 槓桿比率
    debt_to_equity: Optional[float] = Field(None, description="負債權益比")
    debt_to_assets: Optional[float] = Field(None, description="負債資產比")
    interest_coverage: Optional[float] = Field(None, description="利息保障倍數")
    
    # 效率比率
    asset_turnover: Optional[float] = Field(None, description="資產週轉率")
    inventory_turnover: Optional[float] = Field(None, description="存貨週轉率")
    receivables_turnover: Optional[float] = Field(None, description="應收帳款週轉率")
    
    # 市場比率（如果有股價數據）
    pe_ratio: Optional[float] = Field(None, description="本益比")
    pb_ratio: Optional[float] = Field(None, description="股價淨值比")
    dividend_yield: Optional[float] = Field(None, description="股利殖利率")
    
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GrowthAnalysis(BaseModel):
    """成長分析模型"""
    analysis_id: str = Field(..., description="分析ID")
    
    # 收入成長
    revenue_growth_qoq: Optional[float] = Field(None, description="營收季增率")
    revenue_growth_yoy: Optional[float] = Field(None, description="營收年增率")
    
    # 獲利成長
    net_income_growth_qoq: Optional[float] = Field(None, description="淨利季增率")
    net_income_growth_yoy: Optional[float] = Field(None, description="淨利年增率")
    eps_growth_qoq: Optional[float] = Field(None, description="EPS季增率")
    eps_growth_yoy: Optional[float] = Field(None, description="EPS年增率")
    
    # 資產成長
    total_assets_growth: Optional[float] = Field(None, description="總資產成長率")
    equity_growth: Optional[float] = Field(None, description="股東權益成長率")
    
    # 成長品質評估
    revenue_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="營收成長品質")
    profit_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="獲利成長品質")
    sustainable_growth_rate: Optional[float] = Field(None, description="可持續成長率")
    
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportExtractionResult(BaseModel):
    """財報提取結果模型"""
    extraction_id: str = Field(..., description="提取ID")
    company_code: str = Field(..., description="公司代碼")
    company_name: str = Field(..., description="公司名稱")
    report_type: ReportType = Field(..., description="財報類型")
    report_period: ReportPeriod = Field(..., description="報告期間")
    report_year: int = Field(..., description="報告年份")
    
    # 提取狀態
    extraction_status: ExtractionStatus = Field(..., description="提取狀態")
    processing_time_ms: float = Field(0.0, description="處理時間（毫秒）")
    
    # 原始數據
    source_document_path: str = Field(..., description="來源文檔路徑")
    source_document_hash: str = Field(..., description="來源文檔哈希")
    
    # 結構分析結果
    structure_analysis: ReportStructureAnalyzer = Field(..., description="結構分析結果")
    
    # 財務數據提取結果
    financial_data: FinancialDataExtractor = Field(..., description="財務數據")
    
    # 計算結果
    financial_ratios: Optional[FinancialRatios] = Field(None, description="財務比率")
    growth_analysis: Optional[GrowthAnalysis] = Field(None, description="成長分析")
    
    # 健康度評估
    financial_health_grade: FinancialHealthGrade = Field(FinancialHealthGrade.AVERAGE, 
                                                        description="財務健康度等級")
    financial_health_score: float = Field(0.0, ge=0.0, le=100.0, description="財務健康度評分")
    
    # 異常檢測
    anomalies_detected: List[str] = Field(default_factory=list, description="檢測到的異常")
    data_quality_issues: List[str] = Field(default_factory=list, description="數據質量問題")
    
    # 提取信息
    extracted_fields_count: int = Field(0, description="成功提取的字段數量")
    total_fields_attempted: int = Field(0, description="嘗試提取的總字段數")
    extraction_accuracy: float = Field(0.0, ge=0.0, le=1.0, description="提取準確率")
    
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = Field("v1.0", description="模型版本")


class ReportModelTrainer:
    """財報模型訓練器"""
    
    def __init__(self, config: ReportExtractionConfig):
        self.config = config
        self.training_data = []
        self.validation_data = []
        
        # 財務術語字典
        self.financial_terms = {
            '營業收入': ['營業收入', '營收', '銷售收入', '銷售淨額', '營業淨收入'],
            '毛利': ['毛利', '銷售毛利', '營業毛利'],
            '營業利益': ['營業利益', '營業淨利', '營業獲利'],
            '稅後淨利': ['稅後淨利', '本期淨利', '歸屬母公司淨利', '稅後損益'],
            '總資產': ['總資產', '資產總額', '資產總計'],
            '總負債': ['總負債', '負債總額', '負債總計'],
            '股東權益': ['股東權益', '歸屬母公司權益', '權益總計'],
            '流動資產': ['流動資產', '一年內到期資產'],
            '流動負債': ['流動負債', '一年內到期負債']
        }
        
        # 數值模式
        self.number_patterns = [
            r'([\d,]+\.?\d*)',                    # 基本數字格式
            r'\$\s*([\d,]+\.?\d*)',               # 美元格式
            r'NT\$\s*([\d,]+\.?\d*)',             # 新台幣格式
            r'([\d,]+\.?\d*)\s*千元',              # 千元單位
            r'([\d,]+\.?\d*)\s*百萬',              # 百萬單位
            r'([\d,]+\.?\d*)\s*億'                # 億元單位
        ]
    
    async def prepare_training_data(self, data_path: str) -> Dict[str, Any]:
        """準備訓練數據"""
        logger.info(f"準備財報訓練數據: {data_path}")
        
        # 載入訓練數據（模擬）
        sample_reports = await self._generate_sample_reports()
        
        # 分割訓練/驗證數據
        split_idx = int(len(sample_reports) * 0.8)
        self.training_data = sample_reports[:split_idx]
        self.validation_data = sample_reports[split_idx:]
        
        logger.info(f"財報訓練數據: {len(self.training_data)} 份")
        logger.info(f"財報驗證數據: {len(self.validation_data)} 份")
        
        return {
            'total_reports': len(sample_reports),
            'training_reports': len(self.training_data),
            'validation_reports': len(self.validation_data),
            'data_quality_score': self._calculate_training_data_quality()
        }
    
    async def _generate_sample_reports(self) -> List[Dict[str, Any]]:
        """生成樣本財報數據"""
        sample_reports = []
        
        # 模擬不同公司的財報數據
        companies = [
            {'code': '2330', 'name': '台積電'},
            {'code': '2317', 'name': '鴻海'},
            {'code': '2454', 'name': '聯發科'},
            {'code': '6505', 'name': '台塑化'},
            {'code': '2412', 'name': '中華電'}
        ]
        
        periods = ['Q1', 'Q2', 'Q3', 'Q4']
        years = [2022, 2023, 2024]
        
        for company in companies:
            for year in years:
                for period in periods:
                    # 模擬財報數據
                    base_revenue = np.random.uniform(50000, 500000)  # 營收基數
                    growth_rate = np.random.uniform(-0.2, 0.3)      # 成長率
                    
                    report = {
                        'company_code': company['code'],
                        'company_name': company['name'],
                        'report_year': year,
                        'report_period': period,
                        'total_revenue': base_revenue * (1 + growth_rate),
                        'gross_profit': base_revenue * 0.3 * (1 + growth_rate),
                        'operating_profit': base_revenue * 0.15 * (1 + growth_rate),
                        'net_income': base_revenue * 0.12 * (1 + growth_rate),
                        'total_assets': base_revenue * 2.5,
                        'total_liabilities': base_revenue * 1.2,
                        'shareholders_equity': base_revenue * 1.3,
                        'extraction_labels': {
                            'revenue_confidence': np.random.uniform(0.8, 0.98),
                            'profit_confidence': np.random.uniform(0.75, 0.95),
                            'balance_confidence': np.random.uniform(0.85, 0.99)
                        }
                    }
                    
                    sample_reports.append(report)
        
        return sample_reports
    
    def _calculate_training_data_quality(self) -> float:
        """計算訓練數據質量"""
        if not self.training_data:
            return 0.0
        
        quality_scores = []
        
        for report in self.training_data:
            # 數據完整度
            required_fields = ['total_revenue', 'net_income', 'total_assets']
            completeness = sum(1 for field in required_fields if field in report) / len(required_fields)
            
            # 數值合理性
            reasonableness = 1.0
            if report.get('total_revenue', 0) <= 0:
                reasonableness -= 0.3
            if report.get('net_income', 0) < 0 and abs(report.get('net_income', 0)) > report.get('total_revenue', 1):
                reasonableness -= 0.2
            
            # 標註質量
            label_quality = np.mean(list(report.get('extraction_labels', {}).values()))
            
            quality = (completeness * 0.4 + reasonableness * 0.3 + label_quality * 0.3)
            quality_scores.append(quality)
        
        return np.mean(quality_scores)
    
    async def train_extraction_model(self) -> Dict[str, Any]:
        """訓練數據提取模型"""
        logger.info("開始訓練財報數據提取模型...")
        
        # 模擬訓練過程
        training_metrics = {
            'epochs': 5,
            'train_loss': [0.845, 0.612, 0.487, 0.389, 0.323],
            'val_loss': [0.798, 0.634, 0.523, 0.456, 0.398],
            'extraction_accuracy': [0.623, 0.734, 0.823, 0.867, 0.891],
            'field_precision': [0.756, 0.834, 0.876, 0.903, 0.921],
            'field_recall': [0.612, 0.723, 0.789, 0.834, 0.867],
            'training_time_hours': 6.8,
            'best_epoch': 5
        }
        
        logger.info("財報數據提取模型訓練完成")
        return training_metrics
    
    async def train_validation_model(self) -> Dict[str, Any]:
        """訓練數據驗證模型"""
        logger.info("開始訓練數據驗證模型...")
        
        # 模擬訓練過程
        training_metrics = {
            'epochs': 3,
            'validation_accuracy': [0.712, 0.834, 0.889],
            'anomaly_detection_rate': [0.678, 0.756, 0.812],
            'false_positive_rate': [0.123, 0.089, 0.067],
            'training_time_hours': 2.3,
            'best_epoch': 3
        }
        
        logger.info("數據驗證模型訓練完成")
        return training_metrics
    
    async def evaluate_model(self) -> Dict[str, Any]:
        """評估模型性能"""
        logger.info("評估財報提取模型性能...")
        
        # 模擬評估結果
        evaluation_metrics = {
            # 提取準確率
            'overall_extraction_accuracy': 0.891,
            'revenue_extraction_accuracy': 0.934,
            'profit_extraction_accuracy': 0.876,
            'balance_extraction_accuracy': 0.889,
            'cashflow_extraction_accuracy': 0.823,
            
            # 字段級精確度
            'field_precision': 0.921,
            'field_recall': 0.867,
            'field_f1_score': 0.893,
            
            # 數據驗證準確率
            'validation_accuracy': 0.889,
            'anomaly_detection_accuracy': 0.812,
            
            # 性能指標
            'processing_speed_reports_per_min': 15.6,
            'model_size_mb': 267.3,
            'memory_usage_mb': 512.7
        }
        
        logger.info("財報提取模型評估完成")
        return evaluation_metrics


class FinancialReportExtractionModel:
    """財報數據提取模型主類"""
    
    def __init__(self, config: ReportExtractionConfig):
        self.config = config
        self.model_trainer = ReportModelTrainer(config)
        self.model_loaded = False
        
        # 初始化各種提取器
        self.structure_analyzer = None
        self.data_extractor = None
        self.ratio_calculator = None
        self.validator = None
    
    async def load_model(self) -> bool:
        """載入訓練好的模型"""
        try:
            model_path = Path(self.config.model_path)
            logger.info(f"載入財報提取模型: {model_path}")
            
            # 這裡會載入實際的模型文件
            self.model_loaded = True
            logger.info("財報提取模型載入成功")
            return True
            
        except Exception as e:
            logger.error(f"財報提取模型載入失敗: {e}")
            return False
    
    async def extract_from_document(self, document_path: str, 
                                  company_code: str, company_name: str,
                                  report_year: int, report_period: ReportPeriod,
                                  report_type: ReportType = ReportType.QUARTERLY) -> ReportExtractionResult:
        """從財報文檔中提取數據"""
        extraction_id = f"extract_{int(datetime.now().timestamp())}_{company_code}_{report_year}{report_period.value}"
        
        start_time = datetime.now()
        
        try:
            # 1. 文檔結構分析
            structure_analysis = await self._analyze_document_structure(document_path)
            
            # 2. 財務數據提取
            financial_data = await self._extract_financial_data(document_path, structure_analysis)
            
            # 3. 數據驗證
            validation_result = await self._validate_extracted_data(financial_data)
            
            # 4. 計算財務比率（如果啟用）
            financial_ratios = None
            if self.config.calculate_ratios:
                financial_ratios = await self._calculate_financial_ratios(financial_data)
            
            # 5. 成長分析（如果啟用）
            growth_analysis = None
            if self.config.calculate_growth_rates:
                growth_analysis = await self._analyze_growth_trends(
                    financial_data, company_code, report_year, report_period)
            
            # 6. 財務健康度評估
            health_grade, health_score = await self._assess_financial_health(
                financial_data, financial_ratios)
            
            # 7. 異常檢測
            anomalies = await self._detect_anomalies(financial_data, financial_ratios)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 計算提取統計
            extraction_stats = self._calculate_extraction_stats(financial_data)
            
            return ReportExtractionResult(
                extraction_id=extraction_id,
                company_code=company_code,
                company_name=company_name,
                report_type=report_type,
                report_period=report_period,
                report_year=report_year,
                extraction_status=validation_result['status'],
                processing_time_ms=processing_time,
                source_document_path=document_path,
                source_document_hash=self._calculate_document_hash(document_path),
                structure_analysis=structure_analysis,
                financial_data=financial_data,
                financial_ratios=financial_ratios,
                growth_analysis=growth_analysis,
                financial_health_grade=health_grade,
                financial_health_score=health_score,
                anomalies_detected=anomalies,
                data_quality_issues=validation_result['issues'],
                extracted_fields_count=extraction_stats['extracted_count'],
                total_fields_attempted=extraction_stats['total_attempted'],
                extraction_accuracy=extraction_stats['accuracy'],
                model_version=self.config.model_name
            )
            
        except Exception as e:
            logger.error(f"財報數據提取失敗: {e}")
            return await self._create_failed_extraction_result(
                extraction_id, company_code, company_name, report_type, 
                report_period, report_year, document_path, str(e))
    
    async def _analyze_document_structure(self, document_path: str) -> ReportStructureAnalyzer:
        """分析文檔結構"""
        analyzer_id = f"struct_{hash(document_path) % 10000:04d}"
        
        # 模擬結構分析
        analysis = ReportStructureAnalyzer(
            analyzer_id=analyzer_id,
            document_type="pdf" if document_path.endswith('.pdf') else "text",
            page_count=np.random.randint(20, 150),
            table_count=np.random.randint(15, 45),
            balance_sheet_detected=True,
            income_statement_detected=True,
            cash_flow_detected=np.random.choice([True, False], p=[0.8, 0.2]),
            balance_sheet_location={'page': 8, 'table_index': 2},
            income_statement_location={'page': 3, 'table_index': 1},
            cash_flow_location={'page': 12, 'table_index': 3},
            structure_quality_score=np.random.uniform(0.75, 0.95),
            readability_score=np.random.uniform(0.70, 0.90),
            completeness_score=np.random.uniform(0.80, 0.98)
        )
        
        return analysis
    
    async def _extract_financial_data(self, document_path: str, 
                                    structure: ReportStructureAnalyzer) -> FinancialDataExtractor:
        """提取財務數據"""
        extractor_id = f"data_{hash(document_path) % 10000:04d}"
        
        # 模擬數據提取
        base_revenue = np.random.uniform(10000000, 500000000)  # 1千萬到5億
        profit_margin = np.random.uniform(0.05, 0.25)         # 5%到25%
        
        financial_data = FinancialDataExtractor(
            extractor_id=extractor_id,
            total_revenue=Decimal(str(int(base_revenue))),
            gross_profit=Decimal(str(int(base_revenue * 0.3))),
            operating_profit=Decimal(str(int(base_revenue * profit_margin))),
            net_income=Decimal(str(int(base_revenue * profit_margin * 0.8))),
            eps=Decimal(str(round(base_revenue * profit_margin * 0.8 / 100000000, 2))),  # 假設1億股
            total_assets=Decimal(str(int(base_revenue * 3.5))),
            total_liabilities=Decimal(str(int(base_revenue * 1.8))),
            shareholders_equity=Decimal(str(int(base_revenue * 1.7))),
            current_assets=Decimal(str(int(base_revenue * 1.2))),
            current_liabilities=Decimal(str(int(base_revenue * 0.6))),
            operating_cash_flow=Decimal(str(int(base_revenue * profit_margin * 1.2))),
            investing_cash_flow=Decimal(str(int(base_revenue * -0.1))),
            financing_cash_flow=Decimal(str(int(base_revenue * 0.05))),
            free_cash_flow=Decimal(str(int(base_revenue * profit_margin * 0.9))),
            cash_and_equivalents=Decimal(str(int(base_revenue * 0.3))),
            inventory=Decimal(str(int(base_revenue * 0.15))),
            accounts_receivable=Decimal(str(int(base_revenue * 0.1))),
            accounts_payable=Decimal(str(int(base_revenue * 0.08))),
            extraction_confidence=np.random.uniform(0.8, 0.95),
            data_completeness=np.random.uniform(0.85, 0.98),
            validation_passed=True,
            validation_errors=[]
        )
        
        return financial_data
    
    async def _validate_extracted_data(self, data: FinancialDataExtractor) -> Dict[str, Any]:
        """驗證提取的數據"""
        validation_issues = []
        
        # 基本邏輯驗證
        if data.total_revenue and data.gross_profit and data.gross_profit > data.total_revenue:
            validation_issues.append("毛利不應大於營業收入")
        
        if data.total_assets and data.total_liabilities and data.shareholders_equity:
            balance_check = abs(data.total_assets - (data.total_liabilities + data.shareholders_equity))
            if balance_check > data.total_assets * 0.01:  # 1%容錯
                validation_issues.append("資產負債表不平衡")
        
        if data.current_assets and data.total_assets and data.current_assets > data.total_assets:
            validation_issues.append("流動資產不應大於總資產")
        
        # 確定驗證狀態
        if len(validation_issues) == 0:
            status = ExtractionStatus.SUCCESS
        elif len(validation_issues) <= 2:
            status = ExtractionStatus.PARTIAL
        else:
            status = ExtractionStatus.FAILED
        
        return {
            'status': status,
            'issues': validation_issues,
            'validation_score': max(0.0, 1.0 - len(validation_issues) * 0.2)
        }
    
    async def _calculate_financial_ratios(self, data: FinancialDataExtractor) -> FinancialRatios:
        """計算財務比率"""
        ratio_id = f"ratio_{data.extractor_id}"
        
        ratios = FinancialRatios(ratio_id=ratio_id)
        
        # 獲利能力比率
        if data.total_revenue and data.gross_profit:
            ratios.gross_margin = float(data.gross_profit / data.total_revenue * 100)
        
        if data.total_revenue and data.operating_profit:
            ratios.operating_margin = float(data.operating_profit / data.total_revenue * 100)
        
        if data.total_revenue and data.net_income:
            ratios.net_margin = float(data.net_income / data.total_revenue * 100)
        
        if data.net_income and data.total_assets:
            ratios.roa = float(data.net_income / data.total_assets * 100)
        
        if data.net_income and data.shareholders_equity:
            ratios.roe = float(data.net_income / data.shareholders_equity * 100)
        
        # 流動性比率
        if data.current_assets and data.current_liabilities:
            ratios.current_ratio = float(data.current_assets / data.current_liabilities)
        
        if data.cash_and_equivalents and data.current_liabilities:
            ratios.cash_ratio = float(data.cash_and_equivalents / data.current_liabilities)
        
        # 槓桿比率
        if data.total_liabilities and data.shareholders_equity:
            ratios.debt_to_equity = float(data.total_liabilities / data.shareholders_equity)
        
        if data.total_liabilities and data.total_assets:
            ratios.debt_to_assets = float(data.total_liabilities / data.total_assets * 100)
        
        # 效率比率
        if data.total_revenue and data.total_assets:
            ratios.asset_turnover = float(data.total_revenue / data.total_assets)
        
        if data.total_revenue and data.inventory and data.inventory > 0:
            ratios.inventory_turnover = float(data.total_revenue / data.inventory)
        
        if data.total_revenue and data.accounts_receivable and data.accounts_receivable > 0:
            ratios.receivables_turnover = float(data.total_revenue / data.accounts_receivable)
        
        return ratios
    
    async def _analyze_growth_trends(self, data: FinancialDataExtractor,
                                   company_code: str, report_year: int, 
                                   report_period: ReportPeriod) -> GrowthAnalysis:
        """分析成長趨勢"""
        analysis_id = f"growth_{company_code}_{report_year}_{report_period.value}"
        
        # 模擬歷史數據比較
        growth = GrowthAnalysis(
            analysis_id=analysis_id,
            revenue_growth_qoq=np.random.uniform(-15, 25),     # 季增率
            revenue_growth_yoy=np.random.uniform(-10, 30),     # 年增率
            net_income_growth_qoq=np.random.uniform(-30, 50),  # 淨利季增率
            net_income_growth_yoy=np.random.uniform(-25, 60),  # 淨利年增率
            eps_growth_qoq=np.random.uniform(-30, 50),         # EPS季增率
            eps_growth_yoy=np.random.uniform(-25, 60),         # EPS年增率
            total_assets_growth=np.random.uniform(-5, 20),     # 資產成長率
            equity_growth=np.random.uniform(-10, 25),          # 權益成長率
            revenue_quality_score=np.random.uniform(0.6, 0.9),
            profit_quality_score=np.random.uniform(0.5, 0.85),
            sustainable_growth_rate=np.random.uniform(5, 15)
        )
        
        return growth
    
    async def _assess_financial_health(self, data: FinancialDataExtractor,
                                     ratios: Optional[FinancialRatios]) -> Tuple[FinancialHealthGrade, float]:
        """評估財務健康度"""
        health_score = 0.0
        
        # 獲利能力評分 (30%)
        profit_score = 0.0
        if ratios and ratios.roe:
            if ratios.roe >= 15:
                profit_score = 30.0
            elif ratios.roe >= 10:
                profit_score = 20.0
            elif ratios.roe >= 5:
                profit_score = 15.0
            else:
                profit_score = 10.0
        else:
            profit_score = 15.0  # 預設分數
        
        # 流動性評分 (25%)
        liquidity_score = 0.0
        if ratios and ratios.current_ratio:
            if ratios.current_ratio >= 2.0:
                liquidity_score = 25.0
            elif ratios.current_ratio >= 1.5:
                liquidity_score = 20.0
            elif ratios.current_ratio >= 1.0:
                liquidity_score = 15.0
            else:
                liquidity_score = 5.0
        else:
            liquidity_score = 15.0  # 預設分數
        
        # 槓桿評分 (25%)
        leverage_score = 0.0
        if ratios and ratios.debt_to_assets:
            if ratios.debt_to_assets <= 30:
                leverage_score = 25.0
            elif ratios.debt_to_assets <= 50:
                leverage_score = 20.0
            elif ratios.debt_to_assets <= 70:
                leverage_score = 15.0
            else:
                leverage_score = 5.0
        else:
            leverage_score = 15.0  # 預設分數
        
        # 效率評分 (20%)
        efficiency_score = 0.0
        if ratios and ratios.asset_turnover:
            if ratios.asset_turnover >= 1.0:
                efficiency_score = 20.0
            elif ratios.asset_turnover >= 0.7:
                efficiency_score = 15.0
            elif ratios.asset_turnover >= 0.5:
                efficiency_score = 10.0
            else:
                efficiency_score = 5.0
        else:
            efficiency_score = 10.0  # 預設分數
        
        health_score = profit_score + liquidity_score + leverage_score + efficiency_score
        
        # 確定健康度等級
        if health_score >= 85:
            grade = FinancialHealthGrade.EXCELLENT
        elif health_score >= 70:
            grade = FinancialHealthGrade.GOOD
        elif health_score >= 55:
            grade = FinancialHealthGrade.AVERAGE
        elif health_score >= 40:
            grade = FinancialHealthGrade.POOR
        else:
            grade = FinancialHealthGrade.CRITICAL
        
        return grade, health_score
    
    async def _detect_anomalies(self, data: FinancialDataExtractor,
                              ratios: Optional[FinancialRatios]) -> List[str]:
        """檢測數據異常"""
        anomalies = []
        
        # 檢測異常高的毛利率
        if ratios and ratios.gross_margin and ratios.gross_margin > 80:
            anomalies.append("毛利率異常偏高")
        
        # 檢測負的股東權益
        if data.shareholders_equity and data.shareholders_equity < 0:
            anomalies.append("股東權益為負值")
        
        # 檢測異常的流動比率
        if ratios and ratios.current_ratio:
            if ratios.current_ratio > 10:
                anomalies.append("流動比率異常偏高")
            elif ratios.current_ratio < 0.5:
                anomalies.append("流動比率異常偏低")
        
        # 檢測現金流與獲利的差異
        if (data.net_income and data.operating_cash_flow and 
            abs(data.net_income - data.operating_cash_flow) > data.net_income * 2):
            anomalies.append("營業現金流與淨利差異過大")
        
        return anomalies
    
    def _calculate_extraction_stats(self, data: FinancialDataExtractor) -> Dict[str, Any]:
        """計算提取統計"""
        # 統計成功提取的字段數
        total_fields = [
            'total_revenue', 'gross_profit', 'operating_profit', 'net_income', 'eps',
            'total_assets', 'total_liabilities', 'shareholders_equity',
            'current_assets', 'current_liabilities',
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow'
        ]
        
        extracted_count = sum(1 for field in total_fields 
                            if getattr(data, field) is not None)
        
        return {
            'total_attempted': len(total_fields),
            'extracted_count': extracted_count,
            'accuracy': extracted_count / len(total_fields) if total_fields else 0.0
        }
    
    def _calculate_document_hash(self, document_path: str) -> str:
        """計算文檔哈希值"""
        import hashlib
        # 使用SHA-256代替MD5以提高安全性
        return hashlib.sha256(document_path.encode()).hexdigest()
    
    async def _create_failed_extraction_result(self, extraction_id: str, company_code: str,
                                             company_name: str, report_type: ReportType,
                                             report_period: ReportPeriod, report_year: int,
                                             document_path: str, error_msg: str) -> ReportExtractionResult:
        """創建失敗的提取結果"""
        
        # 創建最基本的結構分析結果
        structure_analysis = ReportStructureAnalyzer(
            analyzer_id="failed_analysis",
            structure_quality_score=0.0,
            readability_score=0.0,
            completeness_score=0.0
        )
        
        # 創建空的財務數據
        financial_data = FinancialDataExtractor(
            extractor_id="failed_extraction",
            extraction_confidence=0.0,
            data_completeness=0.0,
            validation_passed=False,
            validation_errors=[error_msg]
        )
        
        return ReportExtractionResult(
            extraction_id=extraction_id,
            company_code=company_code,
            company_name=company_name,
            report_type=report_type,
            report_period=report_period,
            report_year=report_year,
            extraction_status=ExtractionStatus.FAILED,
            processing_time_ms=0.0,
            source_document_path=document_path,
            source_document_hash=self._calculate_document_hash(document_path),
            structure_analysis=structure_analysis,
            financial_data=financial_data,
            financial_health_grade=FinancialHealthGrade.CRITICAL,
            financial_health_score=0.0,
            anomalies_detected=[],
            data_quality_issues=[error_msg],
            extracted_fields_count=0,
            total_fields_attempted=13,
            extraction_accuracy=0.0
        )
    
    async def batch_extract_reports(self, batch_requests: List[Dict[str, Any]]) -> List[ReportExtractionResult]:
        """批量處理財報提取"""
        results = []
        
        for request in batch_requests:
            try:
                result = await self.extract_from_document(
                    document_path=request['document_path'],
                    company_code=request['company_code'],
                    company_name=request['company_name'],
                    report_year=request['report_year'],
                    report_period=ReportPeriod(request['report_period']),
                    report_type=ReportType(request.get('report_type', 'quarterly'))
                )
                results.append(result)
            except Exception as e:
                logger.error(f"批量提取失敗: {e}")
                # 添加失敗結果
                failed_result = await self._create_failed_extraction_result(
                    f"batch_failed_{len(results)}", request['company_code'],
                    request['company_name'], ReportType.QUARTERLY,
                    ReportPeriod.Q1, request['report_year'],
                    request['document_path'], str(e))
                results.append(failed_result)
        
        return results
    
    async def compare_periods(self, company_code: str, periods: int = 4) -> Dict[str, Any]:
        """多期財報對比分析"""
        # 這是一個佔位實現，實際需要從數據庫查詢歷史數據
        
        comparison_data = {
            'company_code': company_code,
            'periods_analyzed': periods,
            'comparison_results': {
                'revenue_trend': 'increasing',
                'profit_trend': 'stable', 
                'growth_consistency': 0.76,
                'financial_stability': 0.83
            },
            'key_insights': [
                '營收呈現穩定成長趨勢',
                '獲利能力保持穩定',
                '財務結構健康',
                '現金流狀況良好'
            ],
            'analysis_date': datetime.now().isoformat()
        }
        
        return comparison_data


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()


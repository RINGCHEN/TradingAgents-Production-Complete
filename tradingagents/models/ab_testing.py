"""
A/B測試系統數據模型
Task 5.3 - A/B測試系統實現
支援多變量測試、用戶分組、效果監控等功能
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid

Base = declarative_base()

class TestStatus(Enum):
    """測試狀態枚舉"""
    DRAFT = "draft"           # 草稿
    ACTIVE = "active"         # 進行中
    PAUSED = "paused"         # 暫停
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消

class TestType(Enum):
    """測試類型枚舉"""
    AB = "ab"                 # A/B測試
    MULTIVARIATE = "multivariate"  # 多變量測試
    SPLIT_URL = "split_url"   # URL分割測試

class VariantType(Enum):
    """變體類型枚舉"""
    CONTROL = "control"       # 控制組
    TREATMENT = "treatment"   # 實驗組

class ABTest(Base):
    """A/B測試主表"""
    __tablename__ = 'ab_tests'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, comment="測試名稱")
    description = Column(Text, comment="測試描述")
    
    # 測試配置
    test_type = Column(String(50), nullable=False, default=TestType.AB.value, comment="測試類型")
    status = Column(String(50), nullable=False, default=TestStatus.DRAFT.value, comment="測試狀態")
    
    # 測試目標
    primary_metric = Column(String(100), nullable=False, comment="主要指標")
    secondary_metrics = Column(JSON, comment="次要指標列表")
    
    # 測試設置
    traffic_allocation = Column(Float, default=100.0, comment="流量分配百分比")
    confidence_level = Column(Float, default=95.0, comment="置信水平")
    minimum_sample_size = Column(Integer, default=1000, comment="最小樣本量")
    
    # 時間設置
    start_date = Column(DateTime, comment="開始時間")
    end_date = Column(DateTime, comment="結束時間")
    duration_days = Column(Integer, comment="測試持續天數")
    
    # 目標設置
    target_audience = Column(JSON, comment="目標受眾條件")
    url_targeting = Column(JSON, comment="URL定向條件")
    
    # 創建信息
    created_by = Column(String(100), comment="創建者")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新時間")
    
    # 關聯關係
    variants = relationship("ABTestVariant", back_populates="test", cascade="all, delete-orphan")
    assignments = relationship("UserTestAssignment", back_populates="test", cascade="all, delete-orphan")
    events = relationship("ABTestEvent", back_populates="test", cascade="all, delete-orphan")
    results = relationship("ABTestResult", back_populates="test", cascade="all, delete-orphan")

class ABTestVariant(Base):
    """A/B測試變體表"""
    __tablename__ = 'ab_test_variants'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey('ab_tests.id'), nullable=False)
    
    # 變體信息
    name = Column(String(255), nullable=False, comment="變體名稱")
    description = Column(Text, comment="變體描述")
    variant_type = Column(String(50), nullable=False, comment="變體類型")
    
    # 流量分配
    traffic_weight = Column(Float, nullable=False, comment="流量權重")
    
    # 變體配置
    config = Column(JSON, comment="變體配置JSON")
    
    # 前端配置
    css_changes = Column(Text, comment="CSS變更")
    js_changes = Column(Text, comment="JavaScript變更")
    html_changes = Column(Text, comment="HTML變更")
    
    # 統計信息
    is_active = Column(Boolean, default=True, comment="是否啟用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新時間")
    
    # 關聯關係
    test = relationship("ABTest", back_populates="variants")
    assignments = relationship("UserTestAssignment", back_populates="variant")

class UserTestAssignment(Base):
    """用戶測試分組表"""
    __tablename__ = 'user_test_assignments'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey('ab_tests.id'), nullable=False)
    variant_id = Column(String(36), ForeignKey('ab_test_variants.id'), nullable=False)
    
    # 用戶信息
    user_id = Column(Integer, comment="用戶ID")
    session_id = Column(String(255), comment="會話ID")
    anonymous_id = Column(String(255), comment="匿名用戶ID")
    
    # 分組信息
    assignment_method = Column(String(50), comment="分組方法")
    assignment_hash = Column(String(255), comment="分組哈希值")
    
    # 用戶屬性
    user_agent = Column(String(500), comment="用戶代理")
    ip_address = Column(String(45), comment="IP地址")
    country = Column(String(10), comment="國家代碼")
    device_type = Column(String(50), comment="設備類型")
    
    # 時間信息
    assigned_at = Column(DateTime, default=datetime.utcnow, comment="分組時間")
    first_exposure = Column(DateTime, comment="首次曝光時間")
    last_exposure = Column(DateTime, comment="最後曝光時間")
    
    # 狀態信息
    is_active = Column(Boolean, default=True, comment="是否活躍")
    excluded = Column(Boolean, default=False, comment="是否被排除")
    exclusion_reason = Column(String(255), comment="排除原因")
    
    # 關聯關係
    test = relationship("ABTest", back_populates="assignments")
    variant = relationship("ABTestVariant", back_populates="assignments")
    events = relationship("ABTestEvent", back_populates="assignment")

class ABTestEvent(Base):
    """A/B測試事件表"""
    __tablename__ = 'ab_test_events'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey('ab_tests.id'), nullable=False)
    assignment_id = Column(String(36), ForeignKey('user_test_assignments.id'), nullable=False)
    
    # 事件信息
    event_name = Column(String(255), nullable=False, comment="事件名稱")
    event_type = Column(String(100), comment="事件類型")
    event_category = Column(String(100), comment="事件分類")
    
    # 事件數據
    event_data = Column(JSON, comment="事件數據")
    event_value = Column(Float, comment="事件價值")
    
    # 頁面信息
    page_url = Column(String(500), comment="頁面URL")
    page_title = Column(String(255), comment="頁面標題")
    referrer = Column(String(500), comment="來源頁面")
    
    # 時間信息
    timestamp = Column(DateTime, default=datetime.utcnow, comment="事件時間")
    server_timestamp = Column(DateTime, default=datetime.utcnow, comment="服務器時間")
    
    # 技術信息
    user_agent = Column(String(500), comment="用戶代理")
    ip_address = Column(String(45), comment="IP地址")
    
    # 關聯關係
    test = relationship("ABTest", back_populates="events")
    assignment = relationship("UserTestAssignment", back_populates="events")

class ABTestResult(Base):
    """A/B測試結果表"""
    __tablename__ = 'ab_test_results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String(36), ForeignKey('ab_tests.id'), nullable=False)
    
    # 結果信息
    metric_name = Column(String(255), nullable=False, comment="指標名稱")
    variant_id = Column(String(36), ForeignKey('ab_test_variants.id'), comment="變體ID")
    
    # 統計數據
    sample_size = Column(Integer, comment="樣本量")
    conversion_count = Column(Integer, comment="轉換數量")
    conversion_rate = Column(Float, comment="轉換率")
    
    # 統計顯著性
    confidence_interval_lower = Column(Float, comment="置信區間下限")
    confidence_interval_upper = Column(Float, comment="置信區間上限")
    p_value = Column(Float, comment="P值")
    statistical_significance = Column(Boolean, comment="統計顯著性")
    
    # 業務指標
    revenue = Column(Float, comment="收入")
    average_order_value = Column(Float, comment="平均訂單價值")
    lifetime_value = Column(Float, comment="生命週期價值")
    
    # 時間範圍
    date_from = Column(DateTime, comment="開始日期")
    date_to = Column(DateTime, comment="結束日期")
    
    # 計算信息
    calculated_at = Column(DateTime, default=datetime.utcnow, comment="計算時間")
    calculation_method = Column(String(100), comment="計算方法")
    
    # 關聯關係
    test = relationship("ABTest", back_populates="results")

# 數據模型輔助類
class ABTestConfig:
    """A/B測試配置類"""
    
    # 默認配置
    DEFAULT_CONFIDENCE_LEVEL = 95.0
    DEFAULT_MINIMUM_SAMPLE_SIZE = 1000
    DEFAULT_TEST_DURATION = 14  # 天
    
    # 統計顯著性閾值
    SIGNIFICANCE_THRESHOLD = 0.05
    
    # 支持的指標類型
    SUPPORTED_METRICS = [
        'conversion_rate',
        'click_through_rate',
        'bounce_rate',
        'time_on_page',
        'revenue_per_visitor',
        'average_order_value',
        'signup_rate',
        'trial_conversion_rate'
    ]
    
    # 支持的事件類型
    SUPPORTED_EVENTS = [
        'page_view',
        'click',
        'form_submit',
        'purchase',
        'signup',
        'trial_start',
        'conversion'
    ]
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            'confidence_level': cls.DEFAULT_CONFIDENCE_LEVEL,
            'minimum_sample_size': cls.DEFAULT_MINIMUM_SAMPLE_SIZE,
            'test_duration': cls.DEFAULT_TEST_DURATION,
            'significance_threshold': cls.SIGNIFICANCE_THRESHOLD
        }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """驗證配置"""
        errors = []
        
        if 'primary_metric' in config:
            if config['primary_metric'] not in cls.SUPPORTED_METRICS:
                errors.append(f"不支持的主要指標: {config['primary_metric']}")
        
        if 'confidence_level' in config:
            if not 80 <= config['confidence_level'] <= 99:
                errors.append("置信水平必須在80-99之間")
        
        if 'minimum_sample_size' in config:
            if config['minimum_sample_size'] < 100:
                errors.append("最小樣本量不能少於100")
        
        return errors
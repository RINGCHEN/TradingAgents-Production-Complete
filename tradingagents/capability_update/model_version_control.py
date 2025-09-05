#!/usr/bin/env python3
"""
Model Version Control System
模型版本控制系統 - GPT-OSS整合任務1.2.3
"""

import uuid
import logging
import hashlib
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import Column, String, DateTime, Float, JSON, Boolean, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from contextlib import contextmanager

from ..database.database import SessionLocal, engine
from ..database.model_capability_db import ModelCapabilityDB

logger = logging.getLogger(__name__)

# 版本控制數據模型
Base = declarative_base()

class ChangeType(Enum):
    """變更類型"""
    CAPABILITY_SCORE = "capability_score"
    PERFORMANCE_UPDATE = "performance_update"
    CONFIGURATION_CHANGE = "configuration_change"
    BENCHMARK_RESULT = "benchmark_result"
    DEPLOYMENT_UPDATE = "deployment_update"
    METADATA_UPDATE = "metadata_update"

class DeploymentStage(Enum):
    """部署階段"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"

class ModelVersion(Base):
    """模型版本記錄"""
    __tablename__ = "model_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False, index=True)
    model_id = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    version_hash = Column(String, nullable=False, unique=True)
    
    # 能力數據快照
    capability_snapshot = Column(JSON, nullable=False)
    
    # 版本元數據
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String, default="system")
    change_summary = Column(Text)
    change_type = Column(String, nullable=False)
    
    # 部署信息
    deployment_stage = Column(String, default=DeploymentStage.DEVELOPMENT.value)
    is_active = Column(Boolean, default=False)
    
    # 性能基準
    baseline_metrics = Column(JSON)
    
    # 關聯變更記錄
    changes = relationship("ModelChangeRecord", back_populates="version", cascade="all, delete-orphan")

class ModelChangeRecord(Base):
    """模型變更記錄"""
    __tablename__ = "model_change_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("model_versions.id"), nullable=False)
    
    # 變更詳情
    change_type = Column(String, nullable=False)
    field_name = Column(String, nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    change_delta = Column(Float)  # 數值變化量
    
    # 變更原因和上下文
    reason = Column(Text)
    context = Column(JSON)
    confidence_score = Column(Float, default=1.0)
    
    # 時間戳記
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    applied_at = Column(DateTime)
    
    # 影響評估
    impact_assessment = Column(JSON)
    rollback_data = Column(JSON)
    
    # 關聯
    version = relationship("ModelVersion", back_populates="changes")

@dataclass
class VersionUpdateRequest:
    """版本更新請求"""
    provider: str
    model_id: str
    changes: Dict[str, Any]
    change_type: ChangeType
    change_summary: str
    created_by: str = "system"
    reason: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    confidence_score: float = 1.0

@dataclass
class VersionComparisonResult:
    """版本比較結果"""
    current_version: str
    target_version: str
    field_changes: List[Dict[str, Any]]
    performance_delta: Dict[str, float]
    risk_assessment: Dict[str, Any]
    recommendation: str

class ModelVersionControl:
    """
    模型版本控制系統
    
    功能：
    1. 模型能力版本追蹤
    2. 變更歷史管理
    3. 版本比較和分析
    4. 回滾機制
    5. 部署階段管理
    """
    
    def __init__(self, model_db: Optional[ModelCapabilityDB] = None):
        """初始化版本控制系統"""
        self.model_db = model_db or ModelCapabilityDB()
        self.logger = logger
        self._ensure_tables()
    
    def _ensure_tables(self):
        """確保版本控制表存在"""
        try:
            Base.metadata.create_all(bind=engine)
            self.logger.info("✅ Version control tables created/verified successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to create version control tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """獲取數據庫會話"""
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            self.logger.error(f"Version control session error: {e}")
            raise
        finally:
            session.close()
    
    async def create_version(
        self,
        provider: str,
        model_id: str,
        capability_data: Dict[str, Any],
        change_type: ChangeType = ChangeType.CAPABILITY_SCORE,
        change_summary: str = "",
        created_by: str = "system"
    ) -> str:
        """
        創建新版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            capability_data: 能力數據
            change_type: 變更類型
            change_summary: 變更摘要
            created_by: 創建者
            
        Returns:
            版本ID
        """
        try:
            with self.get_session() as session:
                # 生成版本號和哈希
                timestamp = datetime.now(timezone.utc)
                version = f"v{timestamp.strftime('%Y%m%d_%H%M%S')}"
                version_hash = self._generate_version_hash(provider, model_id, capability_data, timestamp)
                
                # 創建版本記錄
                model_version = ModelVersion(
                    provider=provider,
                    model_id=model_id,
                    version=version,
                    version_hash=version_hash,
                    capability_snapshot=capability_data,
                    change_summary=change_summary,
                    change_type=change_type.value,
                    created_by=created_by,
                    baseline_metrics=capability_data.get('benchmark_scores', {})
                )
                
                session.add(model_version)
                session.commit()
                session.refresh(model_version)
                
                self.logger.info(f"✅ Created version {version} for {provider}/{model_id}")
                return model_version.id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create version: {e}")
            raise
    
    def _generate_version_hash(
        self,
        provider: str,
        model_id: str,
        capability_data: Dict[str, Any],
        timestamp: datetime
    ) -> str:
        """生成版本哈希"""
        # 創建可重現的哈希
        hash_input = f"{provider}:{model_id}:{timestamp.isoformat()}:{str(sorted(capability_data.items()))}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def update_model_capability_with_versioning(
        self,
        update_request: VersionUpdateRequest
    ) -> Dict[str, Any]:
        """
        帶版本控制的模型能力更新
        
        Args:
            update_request: 更新請求
            
        Returns:
            更新結果
        """
        try:
            # 獲取當前能力數據
            current_capability = await self.model_db.get_model_capability(
                update_request.provider,
                update_request.model_id
            )
            
            if not current_capability:
                raise ValueError(f"Model {update_request.provider}/{update_request.model_id} not found")
            
            # 準備新的能力數據
            current_data = current_capability.dict()
            new_data = current_data.copy()
            new_data.update(update_request.changes)
            
            # 創建新版本
            version_id = await self.create_version(
                provider=update_request.provider,
                model_id=update_request.model_id,
                capability_data=new_data,
                change_type=update_request.change_type,
                change_summary=update_request.change_summary,
                created_by=update_request.created_by
            )
            
            # 記錄具體變更
            change_records = []
            for field, new_value in update_request.changes.items():
                old_value = current_data.get(field)
                
                if old_value != new_value:
                    change_record = await self._create_change_record(
                        version_id=version_id,
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        change_type=update_request.change_type,
                        reason=update_request.reason,
                        context=update_request.context,
                        confidence_score=update_request.confidence_score
                    )
                    change_records.append(change_record)
            
            # 更新模型能力數據庫
            updated_capability = await self.model_db.update_model_capability(
                provider=update_request.provider,
                model_id=update_request.model_id,
                updates=update_request.changes
            )
            
            return {
                'success': True,
                'version_id': version_id,
                'updated_capability': updated_capability.dict() if updated_capability else None,
                'change_records': len(change_records),
                'changes_applied': list(update_request.changes.keys())
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update model capability with versioning: {e}")
            return {
                'success': False,
                'error': str(e),
                'version_id': None
            }
    
    async def _create_change_record(
        self,
        version_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        change_type: ChangeType,
        reason: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        confidence_score: float = 1.0
    ) -> str:
        """創建變更記錄"""
        try:
            with self.get_session() as session:
                # 計算變化量（對數值字段）
                change_delta = None
                if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                    change_delta = float(new_value - old_value)
                
                # 影響評估
                impact_assessment = self._assess_change_impact(
                    field_name, old_value, new_value, change_delta
                )
                
                # 回滾數據
                rollback_data = {
                    'field_name': field_name,
                    'restore_value': old_value,
                    'restore_instructions': f"Rollback {field_name} to previous value"
                }
                
                change_record = ModelChangeRecord(
                    version_id=version_id,
                    change_type=change_type.value,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    change_delta=change_delta,
                    reason=reason,
                    context=context or {},
                    confidence_score=confidence_score,
                    impact_assessment=impact_assessment,
                    rollback_data=rollback_data
                )
                
                session.add(change_record)
                session.commit()
                session.refresh(change_record)
                
                return change_record.id
                
        except Exception as e:
            self.logger.error(f"❌ Failed to create change record: {e}")
            raise
    
    def _assess_change_impact(
        self,
        field_name: str,
        old_value: Any,
        new_value: Any,
        change_delta: Optional[float]
    ) -> Dict[str, Any]:
        """評估變更影響"""
        impact = {
            'severity': 'low',
            'affected_areas': [],
            'risk_factors': [],
            'recommendations': []
        }
        
        # 根據字段類型評估影響
        if field_name == 'capability_score':
            if change_delta and abs(change_delta) > 0.1:
                impact['severity'] = 'medium'
                impact['affected_areas'].append('model_routing')
                impact['recommendations'].append('Monitor routing decisions')
                
                if change_delta < -0.2:
                    impact['severity'] = 'high'
                    impact['risk_factors'].append('Significant performance degradation')
        
        elif field_name == 'avg_latency_ms':
            if change_delta and change_delta > 1000:  # 增加超過1秒
                impact['severity'] = 'medium'
                impact['affected_areas'].append('user_experience')
                impact['recommendations'].append('Consider optimization')
        
        elif field_name == 'cost_per_1k_input_tokens':
            if change_delta and change_delta > 0.01:  # 成本增加超過0.01
                impact['severity'] = 'medium'
                impact['affected_areas'].append('budget_management')
                impact['recommendations'].append('Review cost optimization')
        
        elif field_name == 'is_available':
            if old_value and not new_value:  # 從可用變為不可用
                impact['severity'] = 'high'
                impact['affected_areas'].extend(['service_availability', 'failover'])
                impact['risk_factors'].append('Service interruption')
                impact['recommendations'].append('Activate backup models')
        
        return impact
    
    async def get_version_history(
        self,
        provider: str,
        model_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """獲取版本歷史"""
        try:
            with self.get_session() as session:
                versions = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id
                ).order_by(ModelVersion.created_at.desc()).limit(limit).all()
                
                history = []
                for version in versions:
                    # 獲取關聯的變更記錄
                    changes = session.query(ModelChangeRecord).filter(
                        ModelChangeRecord.version_id == version.id
                    ).all()
                    
                    history.append({
                        'version_id': version.id,
                        'version': version.version,
                        'version_hash': version.version_hash,
                        'created_at': version.created_at.isoformat(),
                        'created_by': version.created_by,
                        'change_summary': version.change_summary,
                        'change_type': version.change_type,
                        'deployment_stage': version.deployment_stage,
                        'is_active': version.is_active,
                        'changes_count': len(changes),
                        'capability_snapshot': version.capability_snapshot
                    })
                
                return history
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get version history: {e}")
            return []
    
    async def compare_versions(
        self,
        provider: str,
        model_id: str,
        current_version: str,
        target_version: str
    ) -> VersionComparisonResult:
        """比較兩個版本"""
        try:
            with self.get_session() as session:
                # 獲取兩個版本
                current_ver = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == current_version
                ).first()
                
                target_ver = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == target_version
                ).first()
                
                if not current_ver or not target_ver:
                    raise ValueError("Version not found")
                
                # 比較快照
                current_snapshot = current_ver.capability_snapshot
                target_snapshot = target_ver.capability_snapshot
                
                # 找出差異
                field_changes = []
                for field in set(current_snapshot.keys()) | set(target_snapshot.keys()):
                    current_val = current_snapshot.get(field)
                    target_val = target_snapshot.get(field)
                    
                    if current_val != target_val:
                        change_info = {
                            'field': field,
                            'current_value': current_val,
                            'target_value': target_val,
                            'change_type': 'modified' if field in current_snapshot and field in target_snapshot else
                                          'added' if field in target_snapshot else 'removed'
                        }
                        
                        # 計算數值變化
                        if isinstance(current_val, (int, float)) and isinstance(target_val, (int, float)):
                            change_info['delta'] = target_val - current_val
                            change_info['percent_change'] = ((target_val - current_val) / current_val * 100) if current_val != 0 else 0
                        
                        field_changes.append(change_info)
                
                # 性能比較
                performance_delta = self._calculate_performance_delta(
                    current_ver.baseline_metrics or {},
                    target_ver.baseline_metrics or {}
                )
                
                # 風險評估
                risk_assessment = self._assess_version_change_risk(field_changes, performance_delta)
                
                # 生成建議
                recommendation = self._generate_version_recommendation(field_changes, risk_assessment)
                
                return VersionComparisonResult(
                    current_version=current_version,
                    target_version=target_version,
                    field_changes=field_changes,
                    performance_delta=performance_delta,
                    risk_assessment=risk_assessment,
                    recommendation=recommendation
                )
                
        except Exception as e:
            self.logger.error(f"❌ Failed to compare versions: {e}")
            raise
    
    def _calculate_performance_delta(
        self,
        current_metrics: Dict[str, Any],
        target_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """計算性能差異"""
        delta = {}
        
        for metric in ['capability_score', 'accuracy_score', 'speed_score', 'avg_latency_ms']:
            current_val = current_metrics.get(metric)
            target_val = target_metrics.get(metric)
            
            if isinstance(current_val, (int, float)) and isinstance(target_val, (int, float)):
                delta[metric] = target_val - current_val
        
        return delta
    
    def _assess_version_change_risk(
        self,
        field_changes: List[Dict[str, Any]],
        performance_delta: Dict[str, float]
    ) -> Dict[str, Any]:
        """評估版本變更風險"""
        risk_level = 'low'
        risk_factors = []
        
        # 檢查關鍵字段變更
        critical_fields = ['capability_score', 'is_available', 'avg_latency_ms']
        for change in field_changes:
            if change['field'] in critical_fields:
                if change['field'] == 'is_available' and not change['target_value']:
                    risk_level = 'high'
                    risk_factors.append('Model availability will be disabled')
                elif change['field'] == 'capability_score' and change.get('delta', 0) < -0.2:
                    risk_level = 'high' if risk_level != 'high' else risk_level
                    risk_factors.append('Significant capability score decrease')
        
        # 檢查性能變化
        if performance_delta.get('avg_latency_ms', 0) > 1000:
            risk_level = 'medium' if risk_level == 'low' else risk_level
            risk_factors.append('Latency increase detected')
        
        return {
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'change_count': len(field_changes),
            'critical_changes': len([c for c in field_changes if c['field'] in critical_fields])
        }
    
    def _generate_version_recommendation(
        self,
        field_changes: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """生成版本建議"""
        risk_level = risk_assessment['risk_level']
        
        if risk_level == 'high':
            return "High risk change detected. Recommend thorough testing before deployment and prepare rollback plan."
        elif risk_level == 'medium':
            return "Medium risk change. Consider canary deployment and monitor performance metrics closely."
        elif len(field_changes) > 5:
            return "Multiple changes detected. Review each change carefully and test in staging environment."
        else:
            return "Low risk change. Safe to proceed with standard deployment process."
    
    async def rollback_to_version(
        self,
        provider: str,
        model_id: str,
        target_version: str,
        rollback_reason: str = "Manual rollback"
    ) -> Dict[str, Any]:
        """回滾到指定版本"""
        try:
            with self.get_session() as session:
                # 獲取目標版本
                target_ver = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == target_version
                ).first()
                
                if not target_ver:
                    raise ValueError(f"Target version {target_version} not found")
                
                # 獲取目標版本的能力快照
                target_snapshot = target_ver.capability_snapshot
                
                # 執行回滾更新
                rollback_request = VersionUpdateRequest(
                    provider=provider,
                    model_id=model_id,
                    changes=target_snapshot,
                    change_type=ChangeType.DEPLOYMENT_UPDATE,
                    change_summary=f"Rollback to version {target_version}",
                    created_by="system_rollback",
                    reason=rollback_reason,
                    context={'rollback_target': target_version}
                )
                
                result = await self.update_model_capability_with_versioning(rollback_request)
                
                if result['success']:
                    self.logger.info(f"✅ Successfully rolled back {provider}/{model_id} to version {target_version}")
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Failed to rollback to version: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def promote_version_stage(
        self,
        provider: str,
        model_id: str,
        version: str,
        target_stage: DeploymentStage
    ) -> bool:
        """提升版本部署階段"""
        try:
            with self.get_session() as session:
                version_record = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id,
                    ModelVersion.version == version
                ).first()
                
                if not version_record:
                    raise ValueError(f"Version {version} not found")
                
                # 更新部署階段
                old_stage = version_record.deployment_stage
                version_record.deployment_stage = target_stage.value
                
                # 如果提升到生產階段，設為活躍版本
                if target_stage == DeploymentStage.PRODUCTION:
                    # 先將其他版本設為非活躍
                    session.query(ModelVersion).filter(
                        ModelVersion.provider == provider,
                        ModelVersion.model_id == model_id,
                        ModelVersion.is_active == True
                    ).update({'is_active': False})
                    
                    version_record.is_active = True
                
                session.commit()
                
                self.logger.info(f"✅ Promoted {provider}/{model_id} version {version} from {old_stage} to {target_stage.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to promote version stage: {e}")
            return False
    
    async def get_active_version(
        self,
        provider: str,
        model_id: str
    ) -> Optional[Dict[str, Any]]:
        """獲取當前活躍版本"""
        try:
            with self.get_session() as session:
                active_version = session.query(ModelVersion).filter(
                    ModelVersion.provider == provider,
                    ModelVersion.model_id == model_id,
                    ModelVersion.is_active == True
                ).first()
                
                if active_version:
                    return {
                        'version_id': active_version.id,
                        'version': active_version.version,
                        'deployment_stage': active_version.deployment_stage,
                        'created_at': active_version.created_at.isoformat(),
                        'capability_snapshot': active_version.capability_snapshot
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get active version: {e}")
            return None
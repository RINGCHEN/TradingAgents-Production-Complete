#!/usr/bin/env python3
"""
Model Version Manager
模型版本管理器 - GPT-OSS整合任務1.2.3
實現模型版本控制和歷史追蹤
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..database.model_capability_db import ModelCapabilityDB, ModelCapabilityDBError

logger = logging.getLogger(__name__)

class VersionStatus(Enum):
    """版本狀態"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"

class UpdateType(Enum):
    """更新類型"""
    MAJOR = "major"        # 重大功能更新
    MINOR = "minor"        # 小功能更新
    PATCH = "patch"        # 錯誤修復
    HOTFIX = "hotfix"      # 緊急修復
    ROLLBACK = "rollback"  # 回滾

@dataclass
class ModelVersion:
    """模型版本信息"""
    provider: str
    model_id: str
    version: str
    status: VersionStatus
    update_type: UpdateType
    capabilities: Dict[str, Any]
    benchmarks: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    rollback_version: Optional[str] = None
    change_summary: str = ""
    compatibility_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'provider': self.provider,
            'model_id': self.model_id,
            'version': self.version,
            'status': self.status.value,
            'update_type': self.update_type.value,
            'capabilities': self.capabilities,
            'benchmarks': self.benchmarks,
            'performance_metrics': self.performance_metrics,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None,
            'rollback_version': self.rollback_version,
            'change_summary': self.change_summary,
            'compatibility_info': self.compatibility_info
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelVersion':
        """從字典創建實例"""
        return cls(
            provider=data['provider'],
            model_id=data['model_id'],
            version=data['version'],
            status=VersionStatus(data['status']),
            update_type=UpdateType(data['update_type']),
            capabilities=data['capabilities'],
            benchmarks=data.get('benchmarks', {}),
            performance_metrics=data.get('performance_metrics', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            activated_at=datetime.fromisoformat(data['activated_at'].replace('Z', '+00:00')) if data.get('activated_at') else None,
            deactivated_at=datetime.fromisoformat(data['deactivated_at'].replace('Z', '+00:00')) if data.get('deactivated_at') else None,
            rollback_version=data.get('rollback_version'),
            change_summary=data.get('change_summary', ''),
            compatibility_info=data.get('compatibility_info', {})
        )

@dataclass
class VersionComparisonResult:
    """版本比較結果"""
    current_version: ModelVersion
    previous_version: Optional[ModelVersion]
    performance_changes: Dict[str, Dict[str, float]]  # metric -> {change, percentage}
    capability_changes: Dict[str, Any]
    compatibility_impact: str  # "none", "minor", "major", "breaking"
    recommendation: str  # "approve", "caution", "reject"
    reasoning: List[str]
    risk_score: float  # 0-1, 風險評分

class ModelVersionManager:
    """
    模型版本管理器
    
    功能：
    1. 版本創建和管理
    2. 版本比較和分析
    3. 版本切換和回滾
    4. 版本歷史追蹤
    5. 兼容性檢查
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        storage_path: Optional[str] = None
    ):
        """
        初始化版本管理器
        
        Args:
            model_db: 模型能力數據庫
            storage_path: 版本數據存儲路徑
        """
        self.model_db = model_db or ModelCapabilityDB()
        self.storage_path = Path(storage_path or "model_versions")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 版本存儲：{provider/model_id: {version: ModelVersion}}
        self._versions: Dict[str, Dict[str, ModelVersion]] = {}
        
        # 活躍版本映射：{provider/model_id: active_version}
        self._active_versions: Dict[str, str] = {}
        
        self.logger = logger
        self._load_existing_versions()
    
    def _load_existing_versions(self):
        """加載現有版本數據"""
        try:
            versions_file = self.storage_path / "versions.json"
            if versions_file.exists():
                with open(versions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for model_key, versions in data.get('versions', {}).items():
                    self._versions[model_key] = {
                        ver: ModelVersion.from_dict(ver_data)
                        for ver, ver_data in versions.items()
                    }
                
                self._active_versions = data.get('active_versions', {})
                
            self.logger.info(f"✅ Loaded {len(self._versions)} model version histories")
            
        except Exception as e:
            self.logger.error(f"❌ Error loading existing versions: {e}")
    
    def _save_versions(self):
        """保存版本數據"""
        try:
            data = {
                'versions': {
                    model_key: {
                        ver: version.to_dict()
                        for ver, version in versions.items()
                    }
                    for model_key, versions in self._versions.items()
                },
                'active_versions': self._active_versions,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            versions_file = self.storage_path / "versions.json"
            with open(versions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving versions: {e}")
    
    def _get_model_key(self, provider: str, model_id: str) -> str:
        """生成模型鍵"""
        return f"{provider}/{model_id}"
    
    def _generate_next_version(
        self,
        provider: str,
        model_id: str,
        update_type: UpdateType
    ) -> str:
        """生成下一個版本號"""
        model_key = self._get_model_key(provider, model_id)
        existing_versions = list(self._versions.get(model_key, {}).keys())
        
        if not existing_versions:
            return "1.0.0"
        
        # 找到最新版本
        versions = sorted(existing_versions, key=lambda x: [int(i) for i in x.split('.')])
        latest = versions[-1]
        major, minor, patch = map(int, latest.split('.'))
        
        # 根據更新類型遞增版本號
        if update_type == UpdateType.MAJOR:
            return f"{major + 1}.0.0"
        elif update_type == UpdateType.MINOR:
            return f"{major}.{minor + 1}.0"
        else:  # PATCH or HOTFIX
            return f"{major}.{minor}.{patch + 1}"
    
    async def create_model_version(
        self,
        provider: str,
        model_id: str,
        update_type: UpdateType,
        capabilities: Dict[str, Any],
        change_summary: str = "",
        benchmarks: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelVersion:
        """
        創建新模型版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            update_type: 更新類型
            capabilities: 能力數據
            change_summary: 變更摘要
            benchmarks: 基準測試結果
            metadata: 元數據
            
        Returns:
            創建的模型版本
        """
        try:
            model_key = self._get_model_key(provider, model_id)
            version = self._generate_next_version(provider, model_id, update_type)
            
            model_version = ModelVersion(
                provider=provider,
                model_id=model_id,
                version=version,
                status=VersionStatus.DEVELOPMENT,
                update_type=update_type,
                capabilities=capabilities,
                benchmarks=benchmarks or {},
                metadata=metadata or {},
                change_summary=change_summary
            )
            
            # 存儲版本
            if model_key not in self._versions:
                self._versions[model_key] = {}
            
            self._versions[model_key][version] = model_version
            self._save_versions()
            
            self.logger.info(f"✅ Created model version {provider}/{model_id}:{version}")
            return model_version
            
        except Exception as e:
            self.logger.error(f"❌ Error creating model version: {e}")
            raise
    
    async def update_version_status(
        self,
        provider: str,
        model_id: str,
        version: str,
        status: VersionStatus
    ) -> bool:
        """
        更新版本狀態
        
        Args:
            provider: 提供商
            model_id: 模型ID
            version: 版本號
            status: 新狀態
            
        Returns:
            是否更新成功
        """
        try:
            model_key = self._get_model_key(provider, model_id)
            
            if model_key not in self._versions or version not in self._versions[model_key]:
                self.logger.warning(f"Version {provider}/{model_id}:{version} not found")
                return False
            
            model_version = self._versions[model_key][version]
            old_status = model_version.status
            model_version.status = status
            
            # 如果激活到生產環境
            if status == VersionStatus.PRODUCTION:
                model_version.activated_at = datetime.now(timezone.utc)
                self._active_versions[model_key] = version
                
                # 停用其他生產版本
                for ver, ver_obj in self._versions[model_key].items():
                    if ver != version and ver_obj.status == VersionStatus.PRODUCTION:
                        ver_obj.status = VersionStatus.DEPRECATED
                        ver_obj.deactivated_at = datetime.now(timezone.utc)
            
            # 如果從生產環境移除
            elif old_status == VersionStatus.PRODUCTION:
                model_version.deactivated_at = datetime.now(timezone.utc)
                if self._active_versions.get(model_key) == version:
                    del self._active_versions[model_key]
            
            self._save_versions()
            
            self.logger.info(f"✅ Updated version status {provider}/{model_id}:{version}: {old_status.value} -> {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating version status: {e}")
            return False
    
    async def get_version_history(
        self,
        provider: str,
        model_id: str,
        limit: Optional[int] = None
    ) -> List[ModelVersion]:
        """
        獲取版本歷史
        
        Args:
            provider: 提供商
            model_id: 模型ID
            limit: 限制數量
            
        Returns:
            版本歷史列表
        """
        model_key = self._get_model_key(provider, model_id)
        versions = list(self._versions.get(model_key, {}).values())
        
        # 按創建時間排序（最新的在前）
        versions.sort(key=lambda x: x.created_at, reverse=True)
        
        if limit:
            versions = versions[:limit]
        
        return versions
    
    async def get_active_version(
        self,
        provider: str,
        model_id: str
    ) -> Optional[ModelVersion]:
        """
        獲取活躍版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            
        Returns:
            活躍版本，如果沒有則返回None
        """
        model_key = self._get_model_key(provider, model_id)
        active_version = self._active_versions.get(model_key)
        
        if active_version and model_key in self._versions:
            return self._versions[model_key].get(active_version)
        
        return None
    
    async def compare_versions(
        self,
        provider: str,
        model_id: str,
        version1: str,
        version2: str
    ) -> VersionComparisonResult:
        """
        比較兩個版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            version1: 版本1（通常是新版本）
            version2: 版本2（通常是舊版本）
            
        Returns:
            版本比較結果
        """
        try:
            model_key = self._get_model_key(provider, model_id)
            
            if model_key not in self._versions:
                raise ValueError(f"Model {provider}/{model_id} not found")
            
            ver1 = self._versions[model_key].get(version1)
            ver2 = self._versions[model_key].get(version2)
            
            if not ver1:
                raise ValueError(f"Version {version1} not found")
            if not ver2:
                raise ValueError(f"Version {version2} not found")
            
            # 分析性能變化
            performance_changes = self._analyze_performance_changes(ver1, ver2)
            
            # 分析能力變化
            capability_changes = self._analyze_capability_changes(ver1, ver2)
            
            # 評估兼容性影響
            compatibility_impact = self._assess_compatibility_impact(ver1, ver2)
            
            # 生成建議
            recommendation, reasoning, risk_score = self._generate_version_recommendation(
                ver1, ver2, performance_changes, capability_changes, compatibility_impact
            )
            
            return VersionComparisonResult(
                current_version=ver1,
                previous_version=ver2,
                performance_changes=performance_changes,
                capability_changes=capability_changes,
                compatibility_impact=compatibility_impact,
                recommendation=recommendation,
                reasoning=reasoning,
                risk_score=risk_score
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error comparing versions: {e}")
            raise
    
    def _analyze_performance_changes(
        self,
        new_version: ModelVersion,
        old_version: ModelVersion
    ) -> Dict[str, Dict[str, float]]:
        """分析性能變化"""
        changes = {}
        
        new_perf = new_version.performance_metrics
        old_perf = old_version.performance_metrics
        
        # 比較關鍵性能指標
        metrics = ['capability_score', 'avg_latency_ms', 'accuracy_score', 'reasoning_score']
        
        for metric in metrics:
            if metric in new_perf and metric in old_perf:
                old_val = float(old_perf[metric])
                new_val = float(new_perf[metric])
                
                if old_val != 0:
                    change = new_val - old_val
                    percentage = (change / abs(old_val)) * 100
                    
                    changes[metric] = {
                        'change': change,
                        'percentage': percentage,
                        'old_value': old_val,
                        'new_value': new_val
                    }
        
        return changes
    
    def _analyze_capability_changes(
        self,
        new_version: ModelVersion,
        old_version: ModelVersion
    ) -> Dict[str, Any]:
        """分析能力變化"""
        changes = {
            'added_capabilities': [],
            'removed_capabilities': [],
            'modified_capabilities': []
        }
        
        new_caps = new_version.capabilities
        old_caps = old_version.capabilities
        
        # 檢查新增的能力
        for cap in new_caps:
            if cap not in old_caps:
                changes['added_capabilities'].append(cap)
            elif new_caps[cap] != old_caps[cap]:
                changes['modified_capabilities'].append({
                    'capability': cap,
                    'old_value': old_caps[cap],
                    'new_value': new_caps[cap]
                })
        
        # 檢查移除的能力
        for cap in old_caps:
            if cap not in new_caps:
                changes['removed_capabilities'].append(cap)
        
        return changes
    
    def _assess_compatibility_impact(
        self,
        new_version: ModelVersion,
        old_version: ModelVersion
    ) -> str:
        """評估兼容性影響"""
        impact_score = 0
        
        # 基於版本號判斷
        new_major = int(new_version.version.split('.')[0])
        old_major = int(old_version.version.split('.')[0])
        
        if new_major > old_major:
            impact_score += 3  # 主版本更新通常有破壞性變更
        
        # 基於能力變化
        capability_changes = self._analyze_capability_changes(new_version, old_version)
        
        if capability_changes['removed_capabilities']:
            impact_score += len(capability_changes['removed_capabilities']) * 2
        
        if capability_changes['modified_capabilities']:
            impact_score += len(capability_changes['modified_capabilities'])
        
        # 基於性能變化
        performance_changes = self._analyze_performance_changes(new_version, old_version)
        
        for metric, change in performance_changes.items():
            if abs(change['percentage']) > 20:  # 超過20%的性能變化
                impact_score += 1
        
        # 根據評分確定影響程度
        if impact_score >= 5:
            return "breaking"
        elif impact_score >= 3:
            return "major"
        elif impact_score >= 1:
            return "minor"
        else:
            return "none"
    
    def _generate_version_recommendation(
        self,
        new_version: ModelVersion,
        old_version: ModelVersion,
        performance_changes: Dict[str, Dict[str, float]],
        capability_changes: Dict[str, Any],
        compatibility_impact: str
    ) -> Tuple[str, List[str], float]:
        """生成版本建議"""
        reasoning = []
        risk_score = 0.0
        
        # 性能分析
        performance_improvements = 0
        performance_degradations = 0
        
        for metric, change in performance_changes.items():
            if metric == 'avg_latency_ms':  # 延遲越低越好
                if change['change'] < 0:
                    performance_improvements += 1
                    reasoning.append(f"Improved {metric}: {change['percentage']:.1f}% reduction")
                elif change['percentage'] > 10:
                    performance_degradations += 1
                    reasoning.append(f"Degraded {metric}: {change['percentage']:.1f}% increase")
                    risk_score += 0.2
            else:  # 其他指標越高越好
                if change['change'] > 0:
                    performance_improvements += 1
                    reasoning.append(f"Improved {metric}: {change['percentage']:.1f}% increase")
                elif change['percentage'] < -10:
                    performance_degradations += 1
                    reasoning.append(f"Degraded {metric}: {change['percentage']:.1f}% decrease")
                    risk_score += 0.2
        
        # 能力分析
        added_count = len(capability_changes['added_capabilities'])
        removed_count = len(capability_changes['removed_capabilities'])
        
        if added_count > 0:
            reasoning.append(f"Added {added_count} new capabilities")
        
        if removed_count > 0:
            reasoning.append(f"Removed {removed_count} capabilities")
            risk_score += removed_count * 0.1
        
        # 兼容性分析
        if compatibility_impact == "breaking":
            reasoning.append("Breaking changes detected - requires careful migration")
            risk_score += 0.4
        elif compatibility_impact == "major":
            reasoning.append("Major compatibility changes - thorough testing recommended")
            risk_score += 0.2
        elif compatibility_impact == "minor":
            reasoning.append("Minor compatibility changes detected")
            risk_score += 0.1
        
        # 生成最終建議
        if risk_score >= 0.7:
            recommendation = "reject"
            reasoning.append("High risk - reject deployment")
        elif risk_score >= 0.4:
            recommendation = "caution"
            reasoning.append("Medium risk - proceed with caution")
        elif performance_improvements > performance_degradations:
            recommendation = "approve"
            reasoning.append("Performance improvements detected - recommend deployment")
        else:
            recommendation = "approve"
            reasoning.append("Changes appear safe for deployment")
        
        return recommendation, reasoning, min(1.0, risk_score)
    
    async def rollback_to_version(
        self,
        provider: str,
        model_id: str,
        target_version: str,
        reason: str = ""
    ) -> bool:
        """
        回滾到指定版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            target_version: 目標版本
            reason: 回滾原因
            
        Returns:
            是否回滾成功
        """
        try:
            model_key = self._get_model_key(provider, model_id)
            
            if model_key not in self._versions or target_version not in self._versions[model_key]:
                self.logger.error(f"Target version {provider}/{model_id}:{target_version} not found")
                return False
            
            current_active = self._active_versions.get(model_key)
            
            # 創建回滾版本記錄
            rollback_version = await self.create_model_version(
                provider=provider,
                model_id=model_id,
                update_type=UpdateType.ROLLBACK,
                capabilities=self._versions[model_key][target_version].capabilities.copy(),
                change_summary=f"Rollback to {target_version}. Reason: {reason}",
                metadata={
                    'rollback_from': current_active,
                    'rollback_to': target_version,
                    'rollback_reason': reason,
                    'rollback_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            rollback_version.rollback_version = target_version
            
            # 激活回滾版本
            await self.update_version_status(
                provider=provider,
                model_id=model_id,
                version=rollback_version.version,
                status=VersionStatus.PRODUCTION
            )
            
            self.logger.info(f"✅ Rolled back {provider}/{model_id} from {current_active} to {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error rolling back version: {e}")
            return False
    
    async def cleanup_old_versions(
        self,
        provider: str,
        model_id: str,
        keep_count: int = 10,
        keep_days: int = 90
    ) -> int:
        """
        清理舊版本
        
        Args:
            provider: 提供商
            model_id: 模型ID
            keep_count: 保留版本數量
            keep_days: 保留天數
            
        Returns:
            清理的版本數量
        """
        try:
            model_key = self._get_model_key(provider, model_id)
            
            if model_key not in self._versions:
                return 0
            
            versions = list(self._versions[model_key].values())
            versions.sort(key=lambda x: x.created_at, reverse=True)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=keep_days)
            active_version = self._active_versions.get(model_key)
            
            removed_count = 0
            
            for i, version in enumerate(versions):
                # 保護條件：
                # 1. 保留最新的 keep_count 個版本
                # 2. 保留活躍版本
                # 3. 保留生產環境版本
                # 4. 保留最近 keep_days 天的版本
                should_keep = (
                    i < keep_count or
                    version.version == active_version or
                    version.status == VersionStatus.PRODUCTION or
                    version.created_at > cutoff_date
                )
                
                if not should_keep:
                    del self._versions[model_key][version.version]
                    removed_count += 1
            
            if removed_count > 0:
                self._save_versions()
                self.logger.info(f"✅ Cleaned up {removed_count} old versions for {provider}/{model_id}")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up versions: {e}")
            return 0
    
    async def get_version_statistics(self) -> Dict[str, Any]:
        """獲取版本統計信息"""
        try:
            total_models = len(self._versions)
            total_versions = sum(len(versions) for versions in self._versions.values())
            active_versions = len(self._active_versions)
            
            status_counts = {}
            update_type_counts = {}
            
            for model_versions in self._versions.values():
                for version in model_versions.values():
                    status = version.status.value
                    update_type = version.update_type.value
                    
                    status_counts[status] = status_counts.get(status, 0) + 1
                    update_type_counts[update_type] = update_type_counts.get(update_type, 0) + 1
            
            return {
                'total_models': total_models,
                'total_versions': total_versions,
                'active_versions': active_versions,
                'status_distribution': status_counts,
                'update_type_distribution': update_type_counts,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting version statistics: {e}")
            return {}
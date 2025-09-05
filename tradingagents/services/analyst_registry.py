#!/usr/bin/env python3
"""
Analyst Registry - 可插拔的分析師註冊和發現機制
天工 (TianGong) - 智能分析師動態管理系統

此模組提供：
1. 動態分析師註冊和發現
2. 分析師生命週期管理  
3. 熱插拔和版本管理
4. 依賴注入和配置管理
5. 健康檢查和故障恢復
"""

import asyncio
import importlib
import importlib.util
import inspect
import logging
import threading
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Callable, Set
import json
import hashlib
import os
import sys

from ..agents.analysts.base_analyst import BaseAnalyst, AnalysisType


class AnalystStatus(Enum):
    """分析師狀態"""
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"
    UPGRADING = "upgrading"


class LoadStrategy(Enum):
    """加載策略"""
    LAZY = "lazy"          # 懶加載：首次使用時加載
    EAGER = "eager"        # 急切加載：註冊時立即加載
    ON_DEMAND = "on_demand" # 按需加載：根據負載情況決定


@dataclass
class AnalystMetadata:
    """分析師元數據"""
    analyst_id: str
    name: str
    description: str
    version: str
    author: str
    
    # 功能特性
    analysis_types: List[AnalysisType]
    supported_markets: List[str] = field(default_factory=lambda: ['TW'])
    supported_languages: List[str] = field(default_factory=lambda: ['zh-TW', 'en'])
    
    # 依賴信息
    dependencies: List[str] = field(default_factory=list)
    python_version: str = "3.11+"
    
    # 性能特性
    estimated_response_time: float = 5.0  # 秒
    memory_usage_mb: int = 100
    gpu_required: bool = False
    
    # 業務特性
    complexity_level: str = "moderate"  # simple, moderate, complex, expert
    confidence_range: tuple = (0.0, 1.0)
    cost_tier: str = "standard"  # free, standard, premium, enterprise
    
    # 元數據
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'analyst_id': self.analyst_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'analysis_types': [at.value for at in self.analysis_types],
            'supported_markets': self.supported_markets,
            'supported_languages': self.supported_languages,
            'dependencies': self.dependencies,
            'python_version': self.python_version,
            'estimated_response_time': self.estimated_response_time,
            'memory_usage_mb': self.memory_usage_mb,
            'gpu_required': self.gpu_required,
            'complexity_level': self.complexity_level,
            'confidence_range': self.confidence_range,
            'cost_tier': self.cost_tier,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class AnalystRegistration:
    """分析師註冊信息"""
    analyst_id: str
    analyst_class: Type[BaseAnalyst]
    metadata: AnalystMetadata
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 加載信息
    module_path: Optional[str] = None
    module_hash: Optional[str] = None
    load_strategy: LoadStrategy = LoadStrategy.LAZY
    
    # 狀態信息
    status: AnalystStatus = AnalystStatus.UNKNOWN
    instance: Optional[BaseAnalyst] = None
    last_used: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    # 性能統計
    total_calls: int = 0
    success_calls: int = 0
    average_response_time: float = 0.0
    
    def get_success_rate(self) -> float:
        """獲取成功率"""
        if self.total_calls == 0:
            return 0.0
        return self.success_calls / self.total_calls
    
    def update_stats(self, success: bool, response_time: float):
        """更新統計信息"""
        self.total_calls += 1
        self.last_used = datetime.now()
        
        if success:
            self.success_calls += 1
        else:
            self.error_count += 1
        
        # 更新平均響應時間
        if self.total_calls == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                (self.average_response_time * (self.total_calls - 1) + response_time) 
                / self.total_calls
            )


class AnalystDiscovery:
    """分析師發現器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def discover_from_path(self, search_path: str) -> List[Dict[str, Any]]:
        """從路徑發現分析師"""
        
        discovered = []
        search_path = Path(search_path)
        
        if not search_path.exists():
            self.logger.warning(f"搜索路徑不存在: {search_path}")
            return discovered
        
        # 搜索 Python 文件
        for py_file in search_path.rglob("*_analyst.py"):
            try:
                discovery_result = self._discover_from_file(py_file)
                if discovery_result:
                    discovered.extend(discovery_result)
                    
            except Exception as e:
                self.logger.error(f"發現分析師失敗 {py_file}: {str(e)}")
        
        self.logger.info(f"從 {search_path} 發現 {len(discovered)} 個分析師")
        return discovered
    
    def _discover_from_file(self, py_file: Path) -> List[Dict[str, Any]]:
        """從單個文件發現分析師"""
        
        discovered = []
        
        try:
            # 計算文件哈希
            file_hash = self._calculate_file_hash(py_file)
            
            # 動態導入模組
            module_name = py_file.stem
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if not spec or not spec.loader:
                return discovered
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找分析師類
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseAnalyst) and 
                    obj != BaseAnalyst):
                    
                    # 提取元數據
                    metadata = self._extract_metadata(obj, module)
                    if metadata:
                        discovered.append({
                            'analyst_class': obj,
                            'metadata': metadata,
                            'module_path': str(py_file),
                            'module_hash': file_hash,
                            'discovery_time': datetime.now()
                        })
                        
                        self.logger.debug(f"發現分析師: {metadata.analyst_id}")
        
        except Exception as e:
            self.logger.error(f"處理文件失敗 {py_file}: {str(e)}")
        
        return discovered
    
    def _extract_metadata(self, analyst_class: Type[BaseAnalyst], module) -> Optional[AnalystMetadata]:
        """提取分析師元數據"""
        
        try:
            # 基本信息
            class_name = analyst_class.__name__
            analyst_id = class_name.lower().replace('analyst', '_analyst')
            
            # 從類屬性或文檔字符串提取信息
            metadata = AnalystMetadata(
                analyst_id=analyst_id,
                name=getattr(analyst_class, '__analyst_name__', class_name),
                description=getattr(analyst_class, '__doc__', f'{class_name} 分析師'),
                version=getattr(analyst_class, '__version__', '1.0.0'),
                author=getattr(analyst_class, '__author__', 'TianGong Team'),
            )
            
            # 嘗試從類中提取分析類型
            if hasattr(analyst_class, 'get_supported_analysis_types'):
                # 靜態方法獲取支持的分析類型
                try:
                    supported_types = analyst_class.get_supported_analysis_types()
                    metadata.analysis_types = supported_types
                except:
                    pass
            
            # 嘗試創建臨時實例以獲取更多信息
            try:
                temp_instance = analyst_class({})
                if hasattr(temp_instance, 'get_analysis_type'):
                    analysis_type = temp_instance.get_analysis_type()
                    if analysis_type not in metadata.analysis_types:
                        metadata.analysis_types.append(analysis_type)
                del temp_instance
            except:
                pass
            
            # 從模組屬性提取更多信息
            if hasattr(module, '__analyst_config__'):
                config = module.__analyst_config__
                if isinstance(config, dict):
                    metadata.supported_markets = config.get('supported_markets', metadata.supported_markets)
                    metadata.complexity_level = config.get('complexity_level', metadata.complexity_level)
                    metadata.estimated_response_time = config.get('estimated_response_time', metadata.estimated_response_time)
                    metadata.cost_tier = config.get('cost_tier', metadata.cost_tier)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"提取元數據失敗 {analyst_class.__name__}: {str(e)}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """計算文件哈希"""
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.sha256(file_content).hexdigest()  # 安全修復：使用SHA256替換MD5
        except Exception as e:
            self.logger.error(f"計算文件哈希失敗 {file_path}: {str(e)}")
            return ""


class AnalystLifecycleManager:
    """分析師生命週期管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._instances: Dict[str, weakref.ref] = {}
        self._cleanup_lock = threading.Lock()
    
    async def create_instance(self, registration: AnalystRegistration) -> Optional[BaseAnalyst]:
        """創建分析師實例"""
        
        try:
            registration.status = AnalystStatus.INITIALIZING
            
            # 檢查依賴
            if not await self._check_dependencies(registration):
                registration.status = AnalystStatus.ERROR
                registration.last_error = "依賴檢查失敗"
                return None
            
            # 創建實例
            instance = registration.analyst_class(registration.config)
            
            # 驗證實例
            if not await self._validate_instance(instance, registration):
                registration.status = AnalystStatus.ERROR
                registration.last_error = "實例驗證失敗"
                return None
            
            # 註冊弱引用
            self._instances[registration.analyst_id] = weakref.ref(
                instance, 
                lambda ref: self._on_instance_deleted(registration.analyst_id)
            )
            
            registration.instance = instance
            registration.status = AnalystStatus.READY
            
            self.logger.info(f"分析師實例創建成功: {registration.analyst_id}")
            return instance
            
        except Exception as e:
            registration.status = AnalystStatus.ERROR
            registration.last_error = str(e)
            self.logger.error(f"創建分析師實例失敗 {registration.analyst_id}: {str(e)}")
            return None
    
    async def _check_dependencies(self, registration: AnalystRegistration) -> bool:
        """檢查依賴"""
        
        try:
            # 檢查 Python 版本
            python_version = registration.metadata.python_version
            if python_version and not self._check_python_version(python_version):
                self.logger.error(f"Python 版本不滿足要求: {python_version}")
                return False
            
            # 檢查模組依賴
            for dependency in registration.metadata.dependencies:
                try:
                    importlib.import_module(dependency)
                except ImportError:
                    self.logger.error(f"缺少依賴模組: {dependency}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"依賴檢查失敗: {str(e)}")
            return False
    
    def _check_python_version(self, required_version: str) -> bool:
        """檢查 Python 版本"""
        
        try:
            # 簡單的版本檢查邏輯
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            
            if required_version.endswith('+'):
                min_version = required_version[:-1]
                return current_version >= min_version
            else:
                return current_version == required_version
                
        except Exception:
            return True  # 如果檢查失敗，假設兼容
    
    async def _validate_instance(self, instance: BaseAnalyst, registration: AnalystRegistration) -> bool:
        """驗證實例"""
        
        try:
            # 檢查必要方法
            required_methods = ['analyze', 'get_analysis_type', 'get_analysis_prompt']
            for method in required_methods:
                if not hasattr(instance, method) or not callable(getattr(instance, method)):
                    self.logger.error(f"分析師缺少必要方法: {method}")
                    return False
            
            # 檢查分析類型
            try:
                analysis_type = instance.get_analysis_type()
                if not isinstance(analysis_type, AnalysisType):
                    self.logger.error(f"無效的分析類型: {analysis_type}")
                    return False
            except Exception as e:
                self.logger.error(f"獲取分析類型失敗: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"實例驗證失敗: {str(e)}")
            return False
    
    def _on_instance_deleted(self, analyst_id: str):
        """實例被刪除時的回調"""
        
        with self._cleanup_lock:
            if analyst_id in self._instances:
                del self._instances[analyst_id]
                self.logger.debug(f"分析師實例已清理: {analyst_id}")
    
    def get_active_instances(self) -> Dict[str, BaseAnalyst]:
        """獲取活躍實例"""
        
        active_instances = {}
        
        with self._cleanup_lock:
            for analyst_id, instance_ref in list(self._instances.items()):
                instance = instance_ref()
                if instance is not None:
                    active_instances[analyst_id] = instance
                else:
                    # 清理已失效的引用
                    del self._instances[analyst_id]
        
        return active_instances
    
    async def cleanup_unused_instances(self, max_idle_time: timedelta = timedelta(hours=1)):
        """清理未使用的實例"""
        
        current_time = datetime.now()
        cleaned_count = 0
        
        # 這裡需要訪問註冊信息來檢查最後使用時間
        # 實際實現中需要與 AnalystRegistry 配合
        
        self.logger.info(f"清理了 {cleaned_count} 個未使用的分析師實例")


class AnalystRegistry:
    """分析師註冊表"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._registrations: Dict[str, AnalystRegistration] = {}
        self._lock = threading.RLock()
        
        # 組件
        self.discovery = AnalystDiscovery()
        self.lifecycle_manager = AnalystLifecycleManager()
        
        # 配置
        self.auto_cleanup_enabled = True
        self.cleanup_interval = timedelta(minutes=30)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def register(
        self, 
        analyst_class: Type[BaseAnalyst],
        metadata: AnalystMetadata,
        config: Dict[str, Any] = None,
        load_strategy: LoadStrategy = LoadStrategy.LAZY
    ) -> bool:
        """註冊分析師"""
        
        with self._lock:
            try:
                analyst_id = metadata.analyst_id
                
                # 檢查是否已註冊
                if analyst_id in self._registrations:
                    existing = self._registrations[analyst_id]
                    if existing.metadata.version == metadata.version:
                        self.logger.warning(f"分析師已註冊: {analyst_id}")
                        return True
                    else:
                        # 版本升級
                        self.logger.info(f"升級分析師版本: {analyst_id} {existing.metadata.version} -> {metadata.version}")
                        await self._upgrade_analyst(existing, analyst_class, metadata, config)
                        return True
                
                # 創建註冊信息
                registration = AnalystRegistration(
                    analyst_id=analyst_id,
                    analyst_class=analyst_class,
                    metadata=metadata,
                    config=config or {},
                    load_strategy=load_strategy
                )
                
                # 如果是急切加載，立即創建實例
                if load_strategy == LoadStrategy.EAGER:
                    instance = await self.lifecycle_manager.create_instance(registration)
                    if not instance:
                        return False
                
                self._registrations[analyst_id] = registration
                
                self.logger.info(f"分析師註冊成功: {analyst_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"分析師註冊失敗 {metadata.analyst_id}: {str(e)}")
                return False
    
    async def _upgrade_analyst(
        self, 
        existing: AnalystRegistration,
        new_class: Type[BaseAnalyst],
        new_metadata: AnalystMetadata,
        new_config: Dict[str, Any]
    ):
        """升級分析師"""
        
        try:
            existing.status = AnalystStatus.UPGRADING
            
            # 如果有現有實例，先停用
            if existing.instance:
                # 這裡可以添加優雅停止邏輯
                existing.instance = None
            
            # 更新註冊信息
            existing.analyst_class = new_class
            existing.metadata = new_metadata
            existing.config = new_config or existing.config
            existing.status = AnalystStatus.UNKNOWN
            
            # 如果是急切加載，重新創建實例
            if existing.load_strategy == LoadStrategy.EAGER:
                await self.lifecycle_manager.create_instance(existing)
            
            self.logger.info(f"分析師升級完成: {existing.analyst_id}")
            
        except Exception as e:
            existing.status = AnalystStatus.ERROR
            existing.last_error = f"升級失敗: {str(e)}"
            self.logger.error(f"分析師升級失敗: {str(e)}")
    
    def discover_and_register(self, search_paths: List[str]) -> int:
        """發現並註冊分析師"""
        
        total_registered = 0
        
        for search_path in search_paths:
            try:
                discoveries = self.discovery.discover_from_path(search_path)
                
                for discovery in discoveries:
                    analyst_class = discovery['analyst_class']
                    metadata = discovery['metadata']
                    
                    # 檢查模組是否有配置
                    config = {}
                    if 'config' in discovery:
                        config = discovery['config']
                    
                    # 設置模組路徑和哈希
                    metadata.module_path = discovery['module_path']
                    metadata.module_hash = discovery['module_hash']
                    
                    if self.register(analyst_class, metadata, config):
                        total_registered += 1
                        
            except Exception as e:
                self.logger.error(f"發現和註冊過程失敗 {search_path}: {str(e)}")
        
        self.logger.info(f"總共註冊 {total_registered} 個分析師")
        return total_registered
    
    async def get_instance(self, analyst_id: str) -> Optional[BaseAnalyst]:
        """獲取分析師實例"""
        
        with self._lock:
            if analyst_id not in self._registrations:
                return None
            
            registration = self._registrations[analyst_id]
            
            # 如果已有實例且狀態正常
            if registration.instance and registration.status == AnalystStatus.READY:
                return registration.instance
            
            # 懶加載或按需加載
            if registration.load_strategy in [LoadStrategy.LAZY, LoadStrategy.ON_DEMAND]:
                instance = await self.lifecycle_manager.create_instance(registration)
                return instance
            
            return None
    
    def list_registrations(self, filter_by_status: AnalystStatus = None) -> List[Dict[str, Any]]:
        """列出註冊信息"""
        
        with self._lock:
            registrations = []
            
            for analyst_id, registration in self._registrations.items():
                if filter_by_status and registration.status != filter_by_status:
                    continue
                
                info = {
                    'analyst_id': analyst_id,
                    'metadata': registration.metadata.to_dict(),
                    'status': registration.status.value,
                    'load_strategy': registration.load_strategy.value,
                    'instance_available': registration.instance is not None,
                    'last_used': registration.last_used.isoformat() if registration.last_used else None,
                    'total_calls': registration.total_calls,
                    'success_rate': registration.get_success_rate(),
                    'average_response_time': registration.average_response_time,
                    'error_count': registration.error_count,
                    'last_error': registration.last_error
                }
                
                registrations.append(info)
            
            return registrations
    
    def unregister(self, analyst_id: str) -> bool:
        """註銷分析師"""
        
        with self._lock:
            if analyst_id not in self._registrations:
                return False
            
            registration = self._registrations[analyst_id]
            
            # 清理實例
            if registration.instance:
                registration.instance = None
            
            # 移除註冊
            del self._registrations[analyst_id]
            
            self.logger.info(f"分析師註銷成功: {analyst_id}")
            return True
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        
        health_info = {
            'total_registered': len(self._registrations),
            'status_breakdown': {},
            'active_instances': 0,
            'avg_success_rate': 0.0,
            'avg_response_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # 統計狀態分佈
        status_counts = {}
        total_success_rate = 0.0
        total_response_time = 0.0
        active_count = 0
        
        with self._lock:
            for registration in self._registrations.values():
                status = registration.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if registration.instance:
                    active_count += 1
                
                if registration.total_calls > 0:
                    total_success_rate += registration.get_success_rate()
                    total_response_time += registration.average_response_time
        
        health_info['status_breakdown'] = status_counts
        health_info['active_instances'] = active_count
        
        if len(self._registrations) > 0:
            health_info['avg_success_rate'] = total_success_rate / len(self._registrations)
            health_info['avg_response_time'] = total_response_time / len(self._registrations)
        
        return health_info
    
    async def start_auto_cleanup(self):
        """啟動自動清理"""
        
        if self.auto_cleanup_enabled and not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
            self.logger.info("自動清理任務啟動")
    
    async def stop_auto_cleanup(self):
        """停止自動清理"""
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self.logger.info("自動清理任務停止")
    
    async def _auto_cleanup_loop(self):
        """自動清理循環"""
        
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self.lifecycle_manager.cleanup_unused_instances()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"自動清理過程中發生錯誤: {str(e)}")


# 全局註冊表實例
_global_registry: Optional[AnalystRegistry] = None


def get_analyst_registry() -> AnalystRegistry:
    """獲取全局分析師註冊表"""
    global _global_registry
    
    if _global_registry is None:
        _global_registry = AnalystRegistry()
    
    return _global_registry


if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_analyst_registry():
        print("測試分析師註冊表")
        
        registry = get_analyst_registry()
        
        # 測試發現和註冊
        search_paths = [
            str(Path(__file__).parent.parent / 'agents' / 'analysts'),
        ]
        
        registered_count = registry.discover_and_register(search_paths)
        print(f"註冊了 {registered_count} 個分析師")
        
        # 列出註冊信息
        registrations = registry.list_registrations()
        for reg in registrations:
            print(f"  - {reg['analyst_id']}: {reg['status']} ({reg['total_calls']} 次調用)")
        
        # 健康檢查
        health = await registry.health_check()
        print(f"健康狀態: {health}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_analyst_registry())
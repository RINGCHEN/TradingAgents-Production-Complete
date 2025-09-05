#!/usr/bin/env python3
"""
獨立的雙團隊協調演示腳本
不依賴現有系統，展示協調機制的核心功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
import uuid

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TeamType(Enum):
    TIANGONG = "tiangong"
    KIRO = "kiro"

class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SyncState:
    """同步狀態"""
    team_type: TeamType
    last_update: datetime
    active_tasks: List[str]
    completed_tasks: List[str]
    blocked_tasks: List[str]
    resource_usage: Dict[str, float]
    next_milestones: List[str]
    current_focus: str

@dataclass
class ConflictInfo:
    """衝突資訊"""
    conflict_id: str
    conflict_type: str
    severity: ConflictSeverity
    affected_tasks: List[str]
    description: str
    resolution_suggestions: List[str]
    detected_at: datetime

class SimpleDualTeamCoordinator:
    """簡化的雙團隊協調器"""
    
    def __init__(self, workspace_path: str = ".demo_workspace"):
        self.workspace_path = Path(workspace_path)
        self.setup_workspace()
        
        # GPT-OSS 專案任務分配矩陣
        self.task_allocation = {
            "0.1.1": {
                "title": "實現按次付費基礎架構",
                "primary_team": TeamType.KIRO,
                "support_team": TeamType.TIANGONG,
                "work_ratio": (70, 30),
                "estimated_hours": 16
            },
            "0.2.1": {
                "title": "創建獨立投資人格測試網站", 
                "primary_team": TeamType.KIRO,
                "support_team": None,
                "work_ratio": (100, 0),
                "estimated_hours": 20
            },
            "1.1.1": {
                "title": "安裝和配置 GPT-OSS 本地推理服務",
                "primary_team": TeamType.TIANGONG,
                "support_team": None,
                "work_ratio": (100, 0),
                "estimated_hours": 24
            },
            "1.3.1": {
                "title": "實現核心路由決策引擎",
                "primary_team": TeamType.TIANGONG,
                "support_team": TeamType.KIRO,
                "work_ratio": (90, 10),
                "estimated_hours": 32
            },
            "2.1.2": {
                "title": "實現成本追蹤系統",
                "primary_team": TeamType.TIANGONG,
                "support_team": TeamType.KIRO,
                "work_ratio": (75, 25),
                "estimated_hours": 28
            },
            "3.1.2": {
                "title": "開發台股新聞情緒分析模型",
                "primary_team": TeamType.TIANGONG,
                "support_team": None,
                "work_ratio": (100, 0),
                "estimated_hours": 40
            },
            "3.2.2": {
                "title": "開發會員分級訪問控制",
                "primary_team": TeamType.KIRO,
                "support_team": TeamType.TIANGONG,
                "work_ratio": (70, 30),
                "estimated_hours": 24
            }
        }
    
    def setup_workspace(self):
        """設置工作空間"""
        directories = [
            "progress_sync/tiangong_status",
            "progress_sync/kiro_status", 
            "communication/daily_syncs",
            "communication/conflict_logs",
            "resource_coordination"
        ]
        
        for directory in directories:
            (self.workspace_path / directory).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"工作空間已設置: {self.workspace_path}")
    
    async def get_team_state(self, team_type: TeamType) -> SyncState:
        """獲取團隊狀態"""
        state_file = self.workspace_path / "progress_sync" / f"{team_type.value}_status" / "current_state.json"
        
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SyncState(
                    team_type=team_type,
                    last_update=datetime.fromisoformat(data['last_update']),
                    active_tasks=data['active_tasks'],
                    completed_tasks=data['completed_tasks'],
                    blocked_tasks=data['blocked_tasks'],
                    resource_usage=data['resource_usage'],
                    next_milestones=data['next_milestones'],
                    current_focus=data['current_focus']
                )
        else:
            # 返回默認狀態
            return self.create_default_state(team_type)
    
    def create_default_state(self, team_type: TeamType) -> SyncState:
        """創建默認狀態"""
        if team_type == TeamType.TIANGONG:
            return SyncState(
                team_type=team_type,
                last_update=datetime.now(),
                active_tasks=[],
                completed_tasks=[],
                blocked_tasks=[],
                resource_usage={"cpu": 30, "memory": 45, "gpu": 0, "storage": 25},
                next_milestones=["Phase 1 基礎設施建設完成", "GPT-OSS 本地部署測試"],
                current_focus="GPT-OSS 本地部署環境準備"
            )
        else:  # KIRO
            return SyncState(
                team_type=team_type,
                last_update=datetime.now(),
                active_tasks=[],
                completed_tasks=[],
                blocked_tasks=[],
                resource_usage={"cpu": 25, "memory": 35, "gpu": 0, "storage": 20},
                next_milestones=["按次付費系統上線", "病毒式獲客引擎部署"],
                current_focus="即時變現加速器開發"
            )
    
    async def save_team_state(self, state: SyncState):
        """保存團隊狀態"""
        state_dir = self.workspace_path / "progress_sync" / f"{state.team_type.value}_status"
        state_file = state_dir / "current_state.json"
        
        state_data = {
            "team_type": state.team_type.value,
            "last_update": state.last_update.isoformat(),
            "active_tasks": state.active_tasks,
            "completed_tasks": state.completed_tasks,
            "blocked_tasks": state.blocked_tasks,
            "resource_usage": state.resource_usage,
            "next_milestones": state.next_milestones,
            "current_focus": state.current_focus
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    
    async def detect_conflicts(self, tiangong_state: SyncState, kiro_state: SyncState) -> List[ConflictInfo]:
        """檢測衝突"""
        conflicts = []
        
        # 1. 檢測資源衝突
        tiangong_gpu = tiangong_state.resource_usage.get("gpu", 0)
        kiro_gpu = kiro_state.resource_usage.get("gpu", 0)
        
        if tiangong_gpu + kiro_gpu > 100:
            conflicts.append(ConflictInfo(
                conflict_id=str(uuid.uuid4()),
                conflict_type="gpu_resource_overallocation",
                severity=ConflictSeverity.HIGH,
                affected_tasks=tiangong_state.active_tasks + kiro_state.active_tasks,
                description=f"GPU資源超額分配: 天工{tiangong_gpu}% + Kiro{kiro_gpu}% > 100%",
                resolution_suggestions=[
                    "實施時間切片GPU使用",
                    "優先處理高優先級任務",
                    "考慮增加GPU資源"
                ],
                detected_at=datetime.now()
            ))
        
        # 2. 檢測時程衝突
        tiangong_milestones = set(tiangong_state.next_milestones)
        kiro_milestones = set(kiro_state.next_milestones)
        overlapping = tiangong_milestones & kiro_milestones
        
        if overlapping:
            conflicts.append(ConflictInfo(
                conflict_id=str(uuid.uuid4()),
                conflict_type="milestone_schedule_conflict",
                severity=ConflictSeverity.MEDIUM,
                affected_tasks=[],
                description=f"里程碑時程衝突: {list(overlapping)}",
                resolution_suggestions=[
                    "重新協商里程碑時間",
                    "分階段達成里程碑"
                ],
                detected_at=datetime.now()
            ))
        
        # 3. 檢測依賴阻塞
        for task_id in tiangong_state.active_tasks + kiro_state.active_tasks:
            if task_id in self.task_allocation:
                # 簡化的依賴檢查邏輯
                pass
        
        return conflicts
    
    async def coordinate_execution(self) -> Dict[str, Any]:
        """執行協調"""
        logger.info("開始雙團隊協調執行")
        
        # 1. 獲取團隊狀態
        tiangong_state = await self.get_team_state(TeamType.TIANGONG)
        kiro_state = await self.get_team_state(TeamType.KIRO)
        
        # 2. 檢測衝突
        conflicts = await self.detect_conflicts(tiangong_state, kiro_state)
        
        # 3. 生成優化建議
        optimization = self.generate_optimization_suggestions(tiangong_state, kiro_state)
        
        # 4. 生成下一步行動
        next_actions = self.generate_next_actions(tiangong_state, kiro_state, conflicts)
        
        # 5. 創建協調報告
        coordination_report = {
            "timestamp": datetime.now().isoformat(),
            "team_states": {
                "tiangong": {
                    "focus": tiangong_state.current_focus,
                    "active_tasks": tiangong_state.active_tasks,
                    "completed_tasks_count": len(tiangong_state.completed_tasks),
                    "blocked_tasks": tiangong_state.blocked_tasks,
                    "resource_usage": tiangong_state.resource_usage,
                    "last_update": tiangong_state.last_update.isoformat()
                },
                "kiro": {
                    "focus": kiro_state.current_focus,
                    "active_tasks": kiro_state.active_tasks,
                    "completed_tasks_count": len(kiro_state.completed_tasks),
                    "blocked_tasks": kiro_state.blocked_tasks,
                    "resource_usage": kiro_state.resource_usage,
                    "last_update": kiro_state.last_update.isoformat()
                }
            },
            "detected_conflicts": [self.serialize_conflict(c) for c in conflicts],
            "optimization_suggestions": optimization,
            "next_actions": next_actions,
            "coordination_metrics": {
                "sync_health": self.calculate_sync_health(tiangong_state, kiro_state),
                "workload_balance": self.calculate_workload_balance(tiangong_state, kiro_state),
                "collaboration_score": 0.85
            }
        }
        
        # 6. 保存協調結果
        await self.save_coordination_result(coordination_report)
        
        logger.info("雙團隊協調執行完成")
        return coordination_report
    
    def serialize_conflict(self, conflict: ConflictInfo) -> Dict[str, Any]:
        """序列化衝突資訊"""
        return {
            "conflict_id": conflict.conflict_id,
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity.value,
            "affected_tasks": conflict.affected_tasks,
            "description": conflict.description,
            "resolution_suggestions": conflict.resolution_suggestions,
            "detected_at": conflict.detected_at.isoformat()
        }
    
    def generate_optimization_suggestions(self, tiangong_state: SyncState, kiro_state: SyncState) -> Dict[str, Any]:
        """生成優化建議"""
        suggestions = []
        
        # 工作負載平衡建議
        tiangong_load = len(tiangong_state.active_tasks)
        kiro_load = len(kiro_state.active_tasks)
        
        if abs(tiangong_load - kiro_load) > 2:
            if tiangong_load > kiro_load:
                suggestions.append({
                    "type": "load_balancing",
                    "description": "考慮將部分天工團隊任務轉移給Kiro團隊支援",
                    "priority": "medium"
                })
            else:
                suggestions.append({
                    "type": "load_balancing",
                    "description": "考慮增加天工團隊對Kiro任務的技術支援",
                    "priority": "medium"
                })
        
        # 資源優化建議
        total_gpu = tiangong_state.resource_usage.get("gpu", 0) + kiro_state.resource_usage.get("gpu", 0)
        if total_gpu > 80:
            suggestions.append({
                "type": "resource_optimization",
                "description": "GPU使用率較高，建議實施任務排程優化",
                "priority": "high"
            })
        
        # 任務分配建議
        available_tasks = ["0.1.1", "1.1.1", "0.2.1"]  # 示例可分配任務
        task_recommendations = []
        
        for task_id in available_tasks:
            if task_id in self.task_allocation:
                task_info = self.task_allocation[task_id]
                task_recommendations.append({
                    "task_id": task_id,
                    "title": task_info["title"],
                    "recommended_team": task_info["primary_team"].value,
                    "estimated_hours": task_info["estimated_hours"]
                })
        
        return {
            "general_suggestions": suggestions,
            "task_recommendations": task_recommendations,
            "current_workload": {
                "tiangong": tiangong_load,
                "kiro": kiro_load
            }
        }
    
    def generate_next_actions(self, tiangong_state: SyncState, kiro_state: SyncState, conflicts: List[ConflictInfo]) -> List[Dict[str, Any]]:
        """生成下一步行動"""
        actions = []
        
        # 基於衝突生成行動
        for conflict in conflicts:
            if conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]:
                actions.append({
                    "type": "conflict_resolution",
                    "priority": "high",
                    "description": f"解決{conflict.conflict_type}衝突",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                    "suggested_actions": conflict.resolution_suggestions
                })
        
        # 基於阻塞任務生成行動
        if tiangong_state.blocked_tasks:
            actions.append({
                "type": "blocker_resolution", 
                "priority": "medium",
                "description": f"解決天工團隊{len(tiangong_state.blocked_tasks)}個阻塞任務",
                "deadline": (datetime.now() + timedelta(days=2)).isoformat()
            })
        
        if kiro_state.blocked_tasks:
            actions.append({
                "type": "blocker_resolution",
                "priority": "medium",
                "description": f"解決Kiro團隊{len(kiro_state.blocked_tasks)}個阻塞任務",
                "deadline": (datetime.now() + timedelta(days=2)).isoformat()
            })
        
        # 添加定期同步行動
        actions.append({
            "type": "daily_sync",
            "priority": "low",
            "description": "進行每日團隊同步會議",
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat()
        })
        
        return actions
    
    def calculate_sync_health(self, tiangong_state: SyncState, kiro_state: SyncState) -> float:
        """計算同步健康度"""
        time_diff = abs((tiangong_state.last_update - kiro_state.last_update).total_seconds())
        
        if time_diff < 3600:  # 1小時內
            return 1.0
        elif time_diff < 7200:  # 2小時內
            return 0.8
        elif time_diff < 14400:  # 4小時內
            return 0.6
        else:
            return 0.4
    
    def calculate_workload_balance(self, tiangong_state: SyncState, kiro_state: SyncState) -> float:
        """計算工作負載平衡度"""
        tiangong_load = len(tiangong_state.active_tasks)
        kiro_load = len(kiro_state.active_tasks)
        
        if tiangong_load == 0 and kiro_load == 0:
            return 1.0
        
        total_load = tiangong_load + kiro_load
        if total_load == 0:
            return 1.0
        
        balance_ratio = 1.0 - abs(tiangong_load - kiro_load) / total_load
        return balance_ratio
    
    async def save_coordination_result(self, report: Dict[str, Any]):
        """保存協調結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.workspace_path / "communication" / "daily_syncs" / f"coordination_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存最新狀態
        latest_file = self.workspace_path / "communication" / "latest_coordination.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"協調結果已保存: {result_file}")

class DualTeamDemo:
    """演示系統"""
    
    def __init__(self):
        self.coordinator = SimpleDualTeamCoordinator()
    
    async def initialize_demo(self):
        """初始化演示"""
        logger.info("初始化雙團隊協調演示...")
        
        # 創建初始狀態
        tiangong_state = self.coordinator.create_default_state(TeamType.TIANGONG)
        kiro_state = self.coordinator.create_default_state(TeamType.KIRO)
        
        # 保存初始狀態
        await self.coordinator.save_team_state(tiangong_state)
        await self.coordinator.save_team_state(kiro_state)
        
        logger.info("初始狀態已創建")
    
    async def simulate_work_session(self):
        """模擬工作會話"""
        logger.info("模擬團隊工作會話...")
        
        # 1. 天工團隊開始GPT-OSS部署
        tiangong_state = await self.coordinator.get_team_state(TeamType.TIANGONG)
        tiangong_state.active_tasks.append("1.1.1")
        tiangong_state.current_focus = "GPT-OSS 框架安裝和配置"
        tiangong_state.resource_usage["gpu"] = 45.0  # 開始使用GPU
        tiangong_state.last_update = datetime.now()
        await self.coordinator.save_team_state(tiangong_state)
        
        # 2. Kiro團隊開始按次付費系統
        kiro_state = await self.coordinator.get_team_state(TeamType.KIRO)
        kiro_state.active_tasks.append("0.1.1")
        kiro_state.current_focus = "支付系統API整合開發"
        kiro_state.resource_usage["cpu"] = 65.0  # CPU使用增加
        kiro_state.last_update = datetime.now()
        await self.coordinator.save_team_state(kiro_state)
        
        # 3. 模擬一些進度
        await asyncio.sleep(1)
        
        # 4. 增加GPU使用，製造潛在衝突
        tiangong_state = await self.coordinator.get_team_state(TeamType.TIANGONG)
        tiangong_state.resource_usage["gpu"] = 70.0
        await self.coordinator.save_team_state(tiangong_state)
        
        kiro_state = await self.coordinator.get_team_state(TeamType.KIRO) 
        kiro_state.resource_usage["gpu"] = 45.0  # Kiro也開始使用GPU（總計115%，超出100%）
        kiro_state.active_tasks.append("0.2.1")  # 增加新任務
        await self.coordinator.save_team_state(kiro_state)
        
        logger.info("工作會話模擬完成")
    
    async def run_demo(self):
        """運行完整演示"""
        print("GPT-OSS 雙團隊協調機制演示")
        print("=" * 50)
        
        try:
            # 1. 初始化
            print("\nStep 1: 初始化協調系統")
            await self.initialize_demo()
            
            # 2. 模擬工作
            print("\nStep 2: 模擬團隊工作會話")
            await self.simulate_work_session()
            
            # 3. 執行協調
            print("\nStep 3: 執行協調檢查")
            result = await self.coordinator.coordinate_execution()
            
            # 4. 分析結果
            print("\nStep 4: 協調結果分析")
            await self.analyze_results(result)
            
            print(f"\n詳細結果已保存到: {self.coordinator.workspace_path}")
            
        except Exception as e:
            logger.error(f"演示過程中發生錯誤: {e}")
            raise
    
    async def analyze_results(self, result: Dict[str, Any]):
        """分析結果"""
        print("\n協調結果摘要:")
        print("-" * 30)
        
        # 團隊狀態
        tiangong = result["team_states"]["tiangong"]
        kiro = result["team_states"]["kiro"]
        
        print(f"天工團隊:")
        print(f"   當前重點: {tiangong['focus']}")
        print(f"   進行中任務: {len(tiangong['active_tasks'])}")
        print(f"   已完成任務: {tiangong['completed_tasks_count']}")
        print(f"   GPU使用率: {tiangong['resource_usage']['gpu']}%")
        
        print(f"\nKiro團隊:")
        print(f"   當前重點: {kiro['focus']}")
        print(f"   進行中任務: {len(kiro['active_tasks'])}")
        print(f"   已完成任務: {kiro['completed_tasks_count']}")
        print(f"   GPU使用率: {kiro['resource_usage']['gpu']}%")
        
        # 衝突檢測
        conflicts = result["detected_conflicts"]
        print(f"\n檢測到 {len(conflicts)} 個衝突:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"   {i}. [{conflict['severity']}] {conflict['description']}")
            if conflict['resolution_suggestions']:
                print(f"      建議: {conflict['resolution_suggestions'][0]}")
        
        # 協調指標
        metrics = result["coordination_metrics"]
        print(f"\n協調指標:")
        print(f"   同步健康度: {metrics['sync_health']:.2f}")
        print(f"   工作負載平衡: {metrics['workload_balance']:.2f}")
        print(f"   協作評分: {metrics['collaboration_score']:.2f}")
        
        # 下一步行動
        actions = result["next_actions"]
        print(f"\n建議行動 ({len(actions)} 項):")
        for i, action in enumerate(actions, 1):
            print(f"   {i}. [{action['priority']}] {action['description']}")
        
        # 優化建議
        optimization = result["optimization_suggestions"]
        if optimization["general_suggestions"]:
            print(f"\n優化建議:")
            for suggestion in optimization["general_suggestions"]:
                print(f"   - {suggestion['description']}")

async def main():
    """主函數"""
    demo = DualTeamDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
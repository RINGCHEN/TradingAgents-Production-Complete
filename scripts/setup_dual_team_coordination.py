#!/usr/bin/env python3
"""
GPT-OSS 雙團隊協調系統設置和演示腳本
用於初始化和演示雙團隊協調機制
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.append(str(Path(__file__).parent / "TradingAgents"))

from tradingagents.coordination.dual_team_coordinator import (
    DualTeamCoordinator, TeamType, SyncState, TaskPriority
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dual_team_coordination.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DualTeamCoordinationDemo:
    """雙團隊協調演示系統"""
    
    def __init__(self):
        self.coordinator = DualTeamCoordinator()
        self.workspace_path = Path(".shared_workspace")
        
    async def initialize_system(self):
        """初始化協調系統"""
        logger.info("初始化雙團隊協調系統...")
        
        # 1. 創建初始團隊狀態
        await self.create_initial_team_states()
        
        # 2. 設置任務分配策略
        await self.setup_task_allocation_strategies()
        
        # 3. 配置衝突檢測規則
        await self.configure_conflict_detection()
        
        # 4. 初始化通信機制
        await self.setup_communication_channels()
        
        logger.info("系統初始化完成")
    
    async def create_initial_team_states(self):
        """創建初始團隊狀態"""
        # 天工團隊初始狀態
        tiangong_state = SyncState(
            team_type=TeamType.TIANGONG,
            last_update=datetime.now(),
            active_tasks=[],
            completed_tasks=[],
            blocked_tasks=[],
            resource_usage={
                "cpu": 30.0,
                "memory": 45.0,
                "gpu": 0.0,
                "storage": 25.0
            },
            next_milestones=["Phase 1 基礎設施建設完成", "GPT-OSS 本地部署測試"],
            current_focus="GPT-OSS 本地部署環境準備"
        )
        
        # Kiro團隊初始狀態
        kiro_state = SyncState(
            team_type=TeamType.KIRO,
            last_update=datetime.now(),
            active_tasks=[], 
            completed_tasks=[],
            blocked_tasks=[],
            resource_usage={
                "cpu": 25.0,
                "memory": 35.0,
                "gpu": 0.0,
                "storage": 20.0
            },
            next_milestones=["按次付費系統上線", "病毒式獲客引擎部署"],
            current_focus="即時變現加速器開發"
        )
        
        # 保存初始狀態
        await self.save_team_state(tiangong_state)
        await self.save_team_state(kiro_state)
        
        logger.info("初始團隊狀態已創建")
    
    async def save_team_state(self, state: SyncState):
        """保存團隊狀態"""
        state_dir = self.workspace_path / "progress_sync" / f"{state.team_type.value}_status"
        state_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    async def setup_task_allocation_strategies(self):
        """設置任務分配策略"""
        strategies_config = {
            "allocation_principles": {
                "capability_matching_weight": 0.4,
                "workload_balancing_weight": 0.3,
                "collaboration_efficiency_weight": 0.3
            },
            "team_specialization_mapping": {
                "tiangong": [
                    "ai_engine_development",
                    "system_architecture", 
                    "algorithm_optimization",
                    "infrastructure_deployment"
                ],
                "kiro": [
                    "product_development",
                    "user_experience_design",
                    "business_logic",
                    "frontend_development"
                ]
            },
            "collaboration_intensity_rules": {
                "low": {"max_teams": 1, "communication_frequency": "weekly"},
                "medium": {"max_teams": 2, "communication_frequency": "bi-weekly"},
                "high": {"max_teams": 2, "communication_frequency": "daily"}
            }
        }
        
        config_file = self.workspace_path / "specifications" / "task_allocation_strategies.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(strategies_config, f, ensure_ascii=False, indent=2)
        
        logger.info("任務分配策略已配置")
    
    async def configure_conflict_detection(self):
        """配置衝突檢測規則"""
        detection_config = {
            "detection_rules": {
                "resource_conflicts": {
                    "gpu_threshold": 90.0,
                    "memory_threshold": 85.0,
                    "cpu_threshold": 90.0
                },
                "schedule_conflicts": {
                    "milestone_overlap_tolerance": 2,  # days
                    "critical_path_buffer": 1  # days
                },
                "dependency_conflicts": {
                    "blocked_dependency_timeout": 3,  # days
                    "circular_dependency_detection": True
                }
            },
            "escalation_matrix": {
                "low": "auto_resolve",
                "medium": "team_negotiation",
                "high": "manager_intervention",
                "critical": "immediate_escalation"
            }
        }
        
        config_file = self.workspace_path / "specifications" / "conflict_detection_rules.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(detection_config, f, ensure_ascii=False, indent=2)
        
        logger.info("衝突檢測規則已配置")
    
    async def setup_communication_channels(self):
        """設置通信渠道"""
        communication_config = {
            "daily_sync": {
                "time": "09:00",
                "duration_minutes": 15,
                "participants": ["tiangong_lead", "kiro_lead", "master_weaver"],
                "agenda": [
                    "昨日完成事項",
                    "今日計劃事項", 
                    "阻礙和風險",
                    "需要協作的任務"
                ]
            },
            "weekly_planning": {
                "time": "monday_14:00",
                "duration_minutes": 60,
                "participants": ["all_team_members", "stakeholders"],
                "agenda": [
                    "上週成果回顧",
                    "本週任務分配",
                    "資源需求確認",
                    "風險評估和應對"
                ]
            },
            "conflict_resolution": {
                "response_time_sla": "4_hours",
                "escalation_path": [
                    "team_leads",
                    "master_weaver",
                    "project_stakeholders"
                ]
            }
        }
        
        config_file = self.workspace_path / "communication" / "communication_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(communication_config, f, ensure_ascii=False, indent=2)
        
        logger.info("通信機制已設置")
    
    async def simulate_team_work_session(self):
        """模擬團隊工作會話"""
        logger.info("開始模擬團隊工作會話...")
        
        # 1. 模擬天工團隊開始GPT-OSS部署任務
        await self.simulate_task_start("1.1.1", TeamType.TIANGONG)
        
        # 2. 模擬Kiro團隊開始按次付費系統開發
        await self.simulate_task_start("0.1.1", TeamType.KIRO)
        
        # 3. 等待一段時間，模擬工作進行
        await asyncio.sleep(2)
        
        # 4. 更新任務進度
        await self.simulate_progress_update("1.1.1", TeamType.TIANGONG, 30.0)
        await self.simulate_progress_update("0.1.1", TeamType.KIRO, 45.0)
        
        # 5. 模擬資源使用增加（可能導致衝突）
        await self.simulate_resource_usage_increase(TeamType.TIANGONG, "gpu", 60.0)
        await self.simulate_resource_usage_increase(TeamType.KIRO, "gpu", 45.0)
        
        logger.info("團隊工作會話模擬完成")
    
    async def simulate_task_start(self, task_id: str, team: TeamType):
        """模擬任務開始"""
        state = await self.coordinator.get_team_sync_state(team)
        state.active_tasks.append(task_id)
        state.last_update = datetime.now()
        
        if task_id == "1.1.1":
            state.current_focus = "GPT-OSS 框架安裝和配置"
        elif task_id == "0.1.1":
            state.current_focus = "支付系統API整合"
        
        await self.save_team_state(state)
        logger.info(f"{team.value} 團隊開始任務: {task_id}")
    
    async def simulate_progress_update(self, task_id: str, team: TeamType, progress: float):
        """模擬進度更新"""
        logger.info(f"{team.value} 團隊任務 {task_id} 進度更新: {progress}%")
        
        # 這裡可以添加更詳細的進度追蹤邏輯
    
    async def simulate_resource_usage_increase(self, team: TeamType, resource: str, usage: float):
        """模擬資源使用增加"""
        state = await self.coordinator.get_team_sync_state(team)
        state.resource_usage[resource] = usage
        state.last_update = datetime.now()
        
        await self.save_team_state(state)
        logger.info(f"{team.value} 團隊 {resource} 使用率更新: {usage}%")
    
    async def run_coordination_cycle(self):
        """運行協調週期"""
        logger.info("開始運行協調週期...")
        
        # 執行協調
        coordination_result = await self.coordinator.coordinate_team_execution()
        
        # 分析結果
        await self.analyze_coordination_result(coordination_result)
        
        logger.info("協調週期完成")
        
        return coordination_result
    
    async def analyze_coordination_result(self, result: dict):
        """分析協調結果"""
        logger.info("協調結果分析:")
        
        # 檢測到的衝突
        conflicts = result.get('detected_conflicts', [])
        if conflicts:
            logger.warning(f"檢測到 {len(conflicts)} 個衝突:")
            for i, conflict in enumerate(conflicts, 1):
                logger.warning(f"  {i}. {conflict['conflict_type']}: {conflict['description']}")
        else:
            logger.info("  ✓ 未檢測到衝突")
        
        # 優化建議
        allocation = result.get('optimized_allocation', {})
        assignments = allocation.get('optimized_assignments', [])
        if assignments:
            logger.info(f"生成 {len(assignments)} 個優化任務分配建議")
        
        # 下一步行動
        actions = result.get('next_actions', [])
        if actions:
            logger.info(f"建議 {len(actions)} 個下一步行動:")
            for i, action in enumerate(actions, 1):
                logger.info(f"  {i}. [{action['priority']}] {action['description']}")
    
    async def generate_status_report(self):
        """生成狀態報告"""
        logger.info("生成協調狀態報告...")
        
        # 獲取團隊狀態
        tiangong_state = await self.coordinator.get_team_sync_state(TeamType.TIANGONG)
        kiro_state = await self.coordinator.get_team_sync_state(TeamType.KIRO)
        
        # 生成報告
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "team_status": {
                "tiangong": {
                    "focus": tiangong_state.current_focus,
                    "active_tasks_count": len(tiangong_state.active_tasks),
                    "completed_tasks_count": len(tiangong_state.completed_tasks),
                    "blocked_tasks_count": len(tiangong_state.blocked_tasks),
                    "resource_utilization": tiangong_state.resource_usage
                },
                "kiro": {
                    "focus": kiro_state.current_focus,
                    "active_tasks_count": len(kiro_state.active_tasks),
                    "completed_tasks_count": len(kiro_state.completed_tasks), 
                    "blocked_tasks_count": len(kiro_state.blocked_tasks),
                    "resource_utilization": kiro_state.resource_usage
                }
            },
            "coordination_metrics": {
                "sync_health": self.calculate_sync_health(tiangong_state, kiro_state),
                "workload_balance": self.calculate_workload_balance(tiangong_state, kiro_state),
                "collaboration_efficiency": 0.85  # 示例值
            },
            "recommendations": [
                "繼續當前工作重點，進展良好",
                "密切監控GPU資源使用情況",
                "準備下週的里程碑檢查"
            ]
        }
        
        # 保存報告
        report_file = self.workspace_path / "communication" / "daily_syncs" / f"status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"狀態報告已保存: {report_file}")
        return report
    
    def calculate_sync_health(self, tiangong_state: SyncState, kiro_state: SyncState) -> float:
        """計算同步健康度"""
        # 基於最後更新時間計算同步健康度
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
        balance_ratio = 1.0 - abs(tiangong_load - kiro_load) / total_load
        
        return balance_ratio

async def main():
    """主函數"""
    print("🚀 GPT-OSS 雙團隊協調系統演示")
    print("=" * 50)
    
    demo = DualTeamCoordinationDemo()
    
    try:
        # 1. 初始化系統
        print("\n📋 Step 1: 初始化協調系統")
        await demo.initialize_system()
        
        # 2. 模擬團隊工作
        print("\n💼 Step 2: 模擬團隊工作會話")
        await demo.simulate_team_work_session()
        
        # 3. 執行協調
        print("\n🔄 Step 3: 執行協調週期")
        coordination_result = await demo.run_coordination_cycle()
        
        # 4. 生成報告
        print("\n📊 Step 4: 生成狀態報告")
        status_report = await demo.generate_status_report()
        
        # 5. 顯示摘要
        print("\n✨ 協調系統演示完成!")
        print(f"   - 檢測到衝突: {len(coordination_result.get('detected_conflicts', []))}")
        print(f"   - 生成建議: {len(coordination_result.get('next_actions', []))}")
        print(f"   - 同步健康度: {status_report['coordination_metrics']['sync_health']:.2f}")
        print(f"   - 工作負載平衡: {status_report['coordination_metrics']['workload_balance']:.2f}")
        
        print(f"\n📁 詳細結果已保存到: {demo.workspace_path}")
        
    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
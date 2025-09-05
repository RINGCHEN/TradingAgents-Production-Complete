#!/usr/bin/env python3
"""
雙團隊協調管理界面
提供日常操作和監控功能
"""

import asyncio
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent / "TradingAgents"))

from TradingAgents.coordination.dual_team_coordinator import (
    DualTeamCoordinator, TeamType, SyncState
)

class DualTeamManager:
    """雙團隊管理器"""
    
    def __init__(self):
        self.coordinator = DualTeamCoordinator()
    
    async def update_team_status(self, team: str, **kwargs):
        """更新團隊狀態"""
        team_type = TeamType(team.lower())
        state = await self.coordinator.get_team_sync_state(team_type)
        
        # 更新狀態字段
        if 'active_tasks' in kwargs:
            state.active_tasks = kwargs['active_tasks']
        if 'completed_tasks' in kwargs:
            state.completed_tasks.extend(kwargs['completed_tasks'])
        if 'blocked_tasks' in kwargs:
            state.blocked_tasks = kwargs['blocked_tasks']
        if 'resource_usage' in kwargs:
            state.resource_usage.update(kwargs['resource_usage'])
        if 'current_focus' in kwargs:
            state.current_focus = kwargs['current_focus']
        
        state.last_update = datetime.now()
        
        # 保存更新
        await self.save_team_state(state)
        print(f"[更新] {team.capitalize()} 團隊狀態已更新")
    
    async def conduct_pre_execution_analysis(self, task_id: str, team: str):
        """執行前分析"""
        team_type = TeamType(team.lower())
        analysis = await self.coordinator.conduct_pre_execution_analysis(task_id, team_type)
        
        print(f"\n[分析報告] 執行前分析報告 - 任務 {task_id} ({team.capitalize()}團隊)")
        print("=" * 60)
        
        print(f"[準備度] 準備度分數: {analysis.readiness_score:.1f}/100")
        
        if analysis.readiness_score >= 80:
            print("[狀態] 準備就緒，可以開始執行")
        elif analysis.readiness_score >= 60:
            print("[狀態] 基本準備，建議處理部分問題後執行")
        else:
            print("[狀態] 準備不足，建議解決阻礙問題後再執行")
        
        print(f"\n[進度分析]")
        progress = analysis.progress_analysis
        print(f"  - 當前活躍任務: {progress.get('active_tasks_count', 0)}")
        print(f"  - 完成任務: {progress.get('completed_tasks_count', 0)}")
        print(f"  - 阻塞任務: {progress.get('blocked_tasks_count', 0)}")
        print(f"  - 完成率: {progress.get('completion_rate', 0):.1f}%")
        resource_info = progress.get('resource_availability', {})
        print(f"  - 資源利用率: {resource_info.get('utilization_rate', 0):.1f}%")
        
        print(f"\n[技術分析]")
        tech = analysis.development_logic
        print(f"  - 技術匹配分數: {tech.get('technical_match_score', 0)}")
        print(f"  - 預估工時: {tech.get('estimated_hours', 0)}小時")
        print(f"  - 協作強度: {tech.get('collaboration_intensity', 'unknown')}")
        
        if analysis.blocking_issues:
            print(f"\n[阻礙問題]")
            for issue in analysis.blocking_issues:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n[建議]")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis

    async def save_team_state(self, state: SyncState):
        """保存團隊狀態"""
        workspace_path = Path(".shared_workspace")
        state_dir = workspace_path / "progress_sync" / f"{state.team_type.value}_status"
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
    
    async def show_status(self):
        """顯示當前狀態"""
        print("[狀態檢查] 雙團隊協調狀態")
        print("=" * 50)
        
        # 獲取兩團隊狀態
        tiangong_state = await self.coordinator.get_team_sync_state(TeamType.TIANGONG)
        kiro_state = await self.coordinator.get_team_sync_state(TeamType.KIRO)
        
        # 顯示天工團隊狀態
        print(f"\n[天工團隊] Tiangong Team (AI技術深度)")
        print(f"   當前重點: {tiangong_state.current_focus}")
        print(f"   進行中任務: {len(tiangong_state.active_tasks)}")
        print(f"   已完成任務: {len(tiangong_state.completed_tasks)}")
        print(f"   阻礙任務: {len(tiangong_state.blocked_tasks)}")
        print(f"   資源使用: GPU {tiangong_state.resource_usage.get('gpu', 0)}%, CPU {tiangong_state.resource_usage.get('cpu', 0)}%")
        print(f"   最後更新: {tiangong_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 顯示Kiro團隊狀態
        print(f"\n[Kiro團隊] Kiro Team (產品化落地)")
        print(f"   當前重點: {kiro_state.current_focus}")
        print(f"   進行中任務: {len(kiro_state.active_tasks)}")
        print(f"   已完成任務: {len(kiro_state.completed_tasks)}")
        print(f"   阻礙任務: {len(kiro_state.blocked_tasks)}")
        print(f"   資源使用: GPU {kiro_state.resource_usage.get('gpu', 0)}%, CPU {kiro_state.resource_usage.get('cpu', 0)}%")
        print(f"   最後更新: {kiro_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 計算協調指標
        sync_health = self.calculate_sync_health(tiangong_state, kiro_state)
        workload_balance = self.calculate_workload_balance(tiangong_state, kiro_state)
        
        print(f"\n[協調指標]")
        print(f"   同步健康度: {sync_health:.2f}")
        print(f"   工作負載平衡: {workload_balance:.2f}")
    
    def calculate_sync_health(self, tiangong_state: SyncState, kiro_state: SyncState) -> float:
        """計算同步健康度"""
        time_diff = abs((tiangong_state.last_update - kiro_state.last_update).total_seconds())
        
        if time_diff < 3600:  # 1小時內
            return 1.0
        elif time_diff < 7200:  # 2小時內
            return 0.8
        else:
            return 0.6
    
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
    
    async def run_coordination(self):
        """執行協調檢查"""
        print("[執行] 雙團隊協調檢查...")
        
        result = await self.coordinator.coordinate_team_execution()
        
        # 顯示結果摘要
        conflicts = result.get('detected_conflicts', [])
        actions = result.get('next_actions', [])
        
        print(f"✅ 協調完成")
        print(f"   檢測到衝突: {len(conflicts)}")
        print(f"   建議行動: {len(actions)}")
        
        if conflicts:
            print(f"\n⚠️  檢測到的衝突:")
            for i, conflict in enumerate(conflicts, 1):
                print(f"   {i}. [{conflict['severity']}] {conflict['description']}")
        
        if actions:
            print(f"\n📋 建議的行動:")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. [{action['priority']}] {action['description']}")
        
        return result
    
    async def start_task(self, team: str, task_id: str, description: str = ""):
        """開始新任務"""
        team_type = TeamType(team.lower())
        state = await self.coordinator.get_team_sync_state(team_type)
        
        if task_id not in state.active_tasks:
            state.active_tasks.append(task_id)
            state.last_update = datetime.now()
            
            if description:
                state.current_focus = description
            
            await self.save_team_state(state)
            print(f"✅ {team.capitalize()} 團隊開始任務: {task_id}")
        else:
            print(f"⚠️  任務 {task_id} 已在進行中")
    
    async def complete_task(self, team: str, task_id: str):
        """完成任務"""
        team_type = TeamType(team.lower())
        state = await self.coordinator.get_team_sync_state(team_type)
        
        if task_id in state.active_tasks:
            state.active_tasks.remove(task_id)
            if task_id not in state.completed_tasks:
                state.completed_tasks.append(task_id)
            state.last_update = datetime.now()
            
            await self.save_team_state(state)
            print(f"✅ {team.capitalize()} 團隊完成任務: {task_id}")
        else:
            print(f"⚠️  任務 {task_id} 不在進行中列表")
    
    async def block_task(self, team: str, task_id: str, reason: str = ""):
        """阻塞任務"""
        team_type = TeamType(team.lower())
        state = await self.coordinator.get_team_sync_state(team_type)
        
        if task_id in state.active_tasks:
            state.active_tasks.remove(task_id)
            if task_id not in state.blocked_tasks:
                state.blocked_tasks.append(task_id)
            state.last_update = datetime.now()
            
            await self.save_team_state(state)
            print(f"⚠️  {team.capitalize()} 團隊任務被阻塞: {task_id}")
            if reason:
                print(f"   原因: {reason}")
        else:
            print(f"⚠️  任務 {task_id} 不在進行中列表")
    
    async def update_resource_usage(self, team: str, resource: str, usage: float):
        """更新資源使用率"""
        team_type = TeamType(team.lower())
        state = await self.coordinator.get_team_sync_state(team_type)
        
        state.resource_usage[resource] = usage
        state.last_update = datetime.now()
        
        await self.save_team_state(state)
        print(f"📊 {team.capitalize()} 團隊 {resource} 使用率更新: {usage}%")

async def main():
    parser = argparse.ArgumentParser(description='雙團隊協調管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 狀態查看命令
    subparsers.add_parser('status', help='顯示當前狀態')
    
    # 協調執行命令
    subparsers.add_parser('coordinate', help='執行協調檢查')
    
    # 任務管理命令
    task_parser = subparsers.add_parser('task', help='任務管理')
    task_parser.add_argument('action', choices=['start', 'complete', 'block'])
    task_parser.add_argument('team', choices=['tiangong', 'kiro'])
    task_parser.add_argument('task_id')
    task_parser.add_argument('--description', '-d', help='任務描述或阻塞原因')
    
    # 資源更新命令
    resource_parser = subparsers.add_parser('resource', help='更新資源使用')
    resource_parser.add_argument('team', choices=['tiangong', 'kiro'])
    resource_parser.add_argument('resource', choices=['cpu', 'memory', 'gpu', 'storage'])
    resource_parser.add_argument('usage', type=float, help='使用率百分比')
    
    # 團隊狀態更新命令
    update_parser = subparsers.add_parser('update', help='更新團隊狀態')
    update_parser.add_argument('team', choices=['tiangong', 'kiro'])
    update_parser.add_argument('--focus', help='當前工作重點')
    
    # 執行前分析命令
    analysis_parser = subparsers.add_parser('analyze', help='執行前分析')
    analysis_parser.add_argument('team', choices=['tiangong', 'kiro'])
    analysis_parser.add_argument('task_id', help='任務ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DualTeamManager()
    
    try:
        if args.command == 'status':
            await manager.show_status()
        
        elif args.command == 'coordinate':
            await manager.run_coordination()
        
        elif args.command == 'task':
            if args.action == 'start':
                await manager.start_task(args.team, args.task_id, args.description or "")
            elif args.action == 'complete':
                await manager.complete_task(args.team, args.task_id)
            elif args.action == 'block':
                await manager.block_task(args.team, args.task_id, args.description or "")
        
        elif args.command == 'resource':
            await manager.update_resource_usage(args.team, args.resource, args.usage)
        
        elif args.command == 'update':
            kwargs = {}
            if args.focus:
                kwargs['current_focus'] = args.focus
            await manager.update_team_status(args.team, **kwargs)
        
        elif args.command == 'analyze':
            await manager.conduct_pre_execution_analysis(args.task_id, args.team)
    
    except Exception as e:
        print(f"[錯誤] 執行命令時發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
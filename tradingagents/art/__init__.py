#!/usr/bin/env python3
"""
ART System - Analyst Trajectory Collection and RULER Reward System
天工 (TianGong) - 智能交易代理人的軌跡收集與獎勵系統

此模組提供：
1. TrajectoryCollector - 分析師決策軌跡收集
2. RULERRewardSystem - 零樣本獎勵生成系統
3. RewardValidator - 獎勵信號驗證與優化
4. ARTIntegration - 系統無縫整合介面

核心特色：
- 與BaseAnalyst系統完全整合
- 支援多種分析師類型的軌跡收集
- GRPO訓練準備的結構化數據輸出
- 會員等級差異化的獎勵權重系統
- 實時獎勵驗證和模型優化機制
"""

from .trajectory_collector import (
    TrajectoryCollector,
    TrajectoryType,
    DecisionStep,
    AnalysisTrajectory,
    TrajectoryMetrics,
    create_trajectory_collector
)

from .ruler_reward_system import (
    RULERRewardSystem,
    RewardType,
    RewardMetrics,
    RewardSignal,
    MembershipTier,
    create_ruler_reward_system
)

from .reward_validator import (
    RewardValidator,
    ValidationResult,
    ValidationMetrics,
    RewardModelConfig,
    create_reward_validator
)

from .art_integration import (
    ARTIntegration,
    ARTConfig,
    IntegrationStatus,
    AnalysisMode,
    PersonalizationLevel,
    IntegrationMetrics,
    create_art_integration,
    create_default_config
)

from .personalization import *
from .value_engine import *

# Version info
__version__ = "1.0.0"
__author__ = "天工 (TianGong) - Code Artisan 魯班"
__description__ = "ART System - Analyst Trajectory Collection and RULER Reward System"

# Export main classes
__all__ = [
    # Core classes
    'TrajectoryCollector',
    'RULERRewardSystem', 
    'RewardValidator',
    'ARTIntegration',
    
    # Data classes
    'TrajectoryType',
    'RewardType',
    'DecisionStep',
    'AnalysisTrajectory',
    'RewardSignal',
    'ValidationResult',
    'MembershipTier',
    'ARTConfig',
    'IntegrationStatus',
    
    # Metrics classes
    'TrajectoryMetrics',
    'RewardMetrics',
    'ValidationMetrics',
    'RewardModelConfig',
    
    # Factory functions
    'create_trajectory_collector',
    'create_ruler_reward_system',
    'create_reward_validator',
    'create_art_integration',
    'create_default_config'
]

# System metadata
ART_SYSTEM_INFO = {
    'name': 'ART System',
    'version': __version__,
    'description': __description__,
    'components': {
        'trajectory_collector': 'Collects analyst decision trajectories with full reasoning chains',
        'ruler_reward_system': 'Generates zero-shot rewards using multi-dimensional evaluation',
        'reward_validator': 'Validates and optimizes reward signals with A/B testing support',
        'art_integration': 'Seamless integration with existing BaseAnalyst and orchestration systems'
    },
    'features': {
        'real_time_collection': 'Real-time trajectory collection during analysis execution',
        'zero_shot_rewards': 'Zero-shot reward generation without manual labeling',
        'membership_aware': 'Differentiated reward weighting based on membership tiers',
        'grpo_ready': 'Structured data output prepared for GRPO training',
        'a_b_testing': 'Built-in A/B testing framework for reward function optimization',
        'performance_optimized': 'High-performance design for large-scale trajectory processing'
    },
    'integration_points': {
        'base_analyst': 'Direct integration with BaseAnalyst execution pipeline',
        'workflow_orchestrator': 'Compatible with WorkflowOrchestrator coordination',
        'member_system': 'Integrated with membership tier and permission systems',
        'database': 'Persistent storage with proper data versioning'
    }
}

def get_art_system_info():
    """Get comprehensive ART system information."""
    return ART_SYSTEM_INFO.copy()

def validate_art_system():
    """Validate ART system dependencies and configuration."""
    validation_results = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'components': {}
    }
    
    # Check core components
    try:
        from .trajectory_collector import TrajectoryCollector
        validation_results['components']['trajectory_collector'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'TrajectoryCollector import failed: {e}')
        validation_results['components']['trajectory_collector'] = 'failed'
    
    try:
        from .ruler_reward_system import RULERRewardSystem
        validation_results['components']['ruler_reward_system'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'RULERRewardSystem import failed: {e}')
        validation_results['components']['ruler_reward_system'] = 'failed'
    
    try:
        from .reward_validator import RewardValidator
        validation_results['components']['reward_validator'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'RewardValidator import failed: {e}')
        validation_results['components']['reward_validator'] = 'failed'
    
    try:
        from .art_integration import ARTIntegration
        validation_results['components']['art_integration'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'ARTIntegration import failed: {e}')
        validation_results['components']['art_integration'] = 'failed'
    
    # Check external dependencies
    try:
        from ..agents.analysts.base_analyst import BaseAnalyst
        validation_results['components']['base_analyst'] = 'available'
    except ImportError as e:
        validation_results['warnings'].append(f'BaseAnalyst integration may be limited: {e}')
        validation_results['components']['base_analyst'] = 'warning'
    
    # Determine overall status
    if validation_results['errors']:
        validation_results['status'] = 'error'
    elif validation_results['warnings']:
        validation_results['status'] = 'warning'
    
    return validation_results

if __name__ == "__main__":
    # System validation and info display
    print("🎯 ART System - Analyst Trajectory Collection and RULER Reward System")
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print()
    
    # Run system validation
    validation = validate_art_system()
    print(f"System Status: {validation['status'].upper()}")
    
    if validation['errors']:
        print("\n❌ Errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print(f"\n📊 Component Status:")
    for component, status in validation['components'].items():
        status_emoji = {
            'available': '✅',
            'warning': '⚠️',
            'failed': '❌'
        }.get(status, '❓')
        print(f"  {status_emoji} {component}: {status}")
    
    # Display system info
    system_info = get_art_system_info()
    print(f"\n🔧 Features:")
    for feature, description in system_info['features'].items():
        print(f"  • {feature}: {description}")
    
    print("\n✅ ART System initialization check complete")
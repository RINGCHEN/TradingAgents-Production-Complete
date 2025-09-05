#!/usr/bin/env python3
"""
ART Personalization System - 個人化學習系統
天工 (TianGong) - 為ART系統提供個人化學習數據生成和LoRA微調

此模組提供：
1. 個人化學習數據生成
2. LoRA微調準備和管理
3. 用戶行為分析和建模
4. 個人化策略優化
5. 學習效果評估和反饋
"""

from .data_generator import (
    create_personalization_data_generator,
    PersonalizationDataGenerator,
    LearningDataPoint,
    PersonalizationContext,
    DataGenerationConfig,
    LearningObjective,
    PersonalizationStrategy
)

from .lora_trainer import (
    create_lora_trainer,
    create_lora_config,
    LoRATrainer,
    LoRAConfig,
    TrainingConfig,
    ModelAdapter,
    TrainingMetrics,
    AdaptationStrategy,
    FineTuningResult
)

from .user_profile_analyzer import (
    create_user_profile_analyzer,
    UserProfileAnalyzer,
    UserBehaviorModel,
    PreferenceProfile,
    TradingStyleAnalyzer,
    BehaviorPattern,
    PersonalityMetrics
)

from .learning_optimizer import (
    create_learning_optimizer,
    LearningOptimizer,
    OptimizationStrategy,
    LearningPath,
    ProgressTracker,
    AdaptiveLearning,
    PersonalizedRecommendation
)

# Version info
__version__ = "1.0.0" 
__author__ = "天工 (TianGong) - Code Artisan 魯班"
__description__ = "ART Personalization System - Personalized Learning and LoRA Fine-tuning"

# Export main classes
__all__ = [
    # Factory functions
    'create_personalization_data_generator',
    'create_lora_trainer',
    'create_lora_config',
    'create_user_profile_analyzer',
    'create_learning_optimizer',
    
    # Core classes
    'PersonalizationDataGenerator',
    'LoRATrainer',
    'UserProfileAnalyzer',
    'LearningOptimizer',
    
    # Data structures
    'LearningDataPoint',
    'PersonalizationContext',
    'DataGenerationConfig',
    'LoRAConfig',
    'TrainingConfig',
    'ModelAdapter',
    'UserBehaviorModel',
    'PreferenceProfile',
    'TradingStyleAnalyzer',
    'OptimizationStrategy',
    'LearningPath',
    
    # Enums
    'LearningObjective',
    'PersonalizationStrategy',
    'TrainingMetrics',
    'AdaptationStrategy',
    'BehaviorPattern',
    'PersonalityMetrics',
    'ProgressTracker',
    'AdaptiveLearning',
    
    # Result types
    'FineTuningResult',
    'PersonalizedRecommendation'
]

# System metadata
ART_PERSONALIZATION_INFO = {
    'name': 'ART Personalization System',
    'version': __version__,
    'description': __description__,
    'features': {
        'personalized_data_generation': 'Generate personalized learning data based on user behavior and preferences',
        'lora_fine_tuning': 'Low-Rank Adaptation fine-tuning for efficient model personalization',
        'user_behavior_modeling': 'Comprehensive user behavior analysis and modeling',
        'adaptive_learning': 'Adaptive learning paths based on user progress and preferences',
        'trading_style_analysis': 'Analyze and model individual trading styles and preferences',
        'preference_profiling': 'Build detailed preference profiles for personalized recommendations',
        'learning_optimization': 'Optimize learning processes for maximum effectiveness',
        'progress_tracking': 'Track learning progress and adaptation effectiveness',
        'recommendation_engine': 'Generate personalized investment recommendations',
        'feedback_integration': 'Integrate user feedback for continuous improvement'
    },
    'integration_points': {
        'art_storage': 'Direct integration with ART storage system for data persistence',
        'base_analyst': 'Integration with BaseAnalyst for personalized analysis',
        'trajectory_system': 'Integration with trajectory collection for learning data',
        'reward_system': 'Integration with RULER reward system for feedback'
    }
}

def get_personalization_info():
    """Get comprehensive personalization system information."""
    return ART_PERSONALIZATION_INFO.copy()

def validate_personalization_system():
    """Validate personalization system dependencies and configuration."""
    validation_results = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'components': {}
    }
    
    # Check core components
    try:
        from .data_generator import PersonalizationDataGenerator
        validation_results['components']['data_generator'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'DataGenerator import failed: {e}')
        validation_results['components']['data_generator'] = 'failed'
    
    try:
        from .lora_trainer import LoRATrainer
        validation_results['components']['lora_trainer'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'LoRATrainer import failed: {e}')
        validation_results['components']['lora_trainer'] = 'failed'
    
    try:
        from .user_profile_analyzer import UserProfileAnalyzer
        validation_results['components']['user_profile_analyzer'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'UserProfileAnalyzer import failed: {e}')
        validation_results['components']['user_profile_analyzer'] = 'failed'
    
    try:
        from .learning_optimizer import LearningOptimizer
        validation_results['components']['learning_optimizer'] = 'available'
    except ImportError as e:
        validation_results['errors'].append(f'LearningOptimizer import failed: {e}')
        validation_results['components']['learning_optimizer'] = 'failed'
    
    # Check optional dependencies
    try:
        import torch
        validation_results['components']['pytorch'] = 'available'
    except ImportError:
        validation_results['warnings'].append('PyTorch not available - LoRA training disabled')
        validation_results['components']['pytorch'] = 'warning'
    
    try:
        import transformers
        validation_results['components']['transformers'] = 'available'
    except ImportError:
        validation_results['warnings'].append('Transformers not available - Model fine-tuning disabled')
        validation_results['components']['transformers'] = 'warning'
    
    try:
        import numpy as np
        validation_results['components']['numpy'] = 'available'
    except ImportError:
        validation_results['warnings'].append('NumPy not available - Numerical computations limited')
        validation_results['components']['numpy'] = 'warning'
    
    # Determine overall status
    if validation_results['errors']:
        validation_results['status'] = 'error'
    elif validation_results['warnings']:
        validation_results['status'] = 'warning'
    
    return validation_results

if __name__ == "__main__":
    # System validation and info display
    print("🧠 ART Personalization System - Personalized Learning and LoRA Fine-tuning")
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print()
    
    # Run system validation
    validation = validate_personalization_system()
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
    personalization_info = get_personalization_info()
    print(f"\n🚀 Features:")
    for feature, description in personalization_info['features'].items():
        print(f"  • {feature}: {description}")
    
    print(f"\n🔗 Integration Points:")
    for integration, description in personalization_info['integration_points'].items():
        print(f"  • {integration}: {description}")
    
    print("\n✅ ART Personalization System initialization check complete")
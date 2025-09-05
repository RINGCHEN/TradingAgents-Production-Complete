# TradingAgents 整合模組
"""
基於 .kiro 規格的系統整合組件

整合範圍:
- KIRO 監控 Hooks 系統
- 支付系統前端整合
- AI 分析師邏輯實作
- 數據源統一編排
- 權限管理橋接
"""

from .kiro_hooks_integration import KiroHooksManager

# TODO: 待實作的整合模組
# from .payment_frontend_bridge import PaymentFrontendBridge  
# from .ai_analyst_integration import AIAnalystIntegration
# from .data_orchestrator_integration import DataOrchestratorIntegration

__all__ = [
    "KiroHooksManager",
    # "PaymentFrontendBridge", 
    # "AIAnalystIntegration",
    # "DataOrchestratorIntegration"
]
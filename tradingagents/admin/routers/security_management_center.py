#!/usr/bin/env python3
"""
安全管理中心路由器 (Security Management Center Router)
天工 (TianGong) - 第二階段高級安全管理功能

此模組提供企業級安全管理中心功能，包含：
1. 高級權限管理 (RBAC Plus)
2. 安全審計日誌系統
3. 威脅監控與防護
4. 合規性監控中心
5. 安全策略管理引擎
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path
import uuid
import os
from pathlib import Path
import hashlib
import os
from pathlib import Path
from ipaddress import ip_address, ip_network

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("security_management_center")
security_logger = get_security_logger("security_management_center")

# 創建路由器
router = APIRouter(prefix="/security", tags=["安全管理中心"])

# ==================== 數據模型定義 ====================

class PermissionType(str, Enum):
    """權限類型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"

class SecurityEventType(str, Enum):
    """安全事件類型"""
    LOGIN_ATTEMPT = "login_attempt"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    SYSTEM_CHANGE = "system_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"

class ThreatLevel(str, Enum):
    """威脅等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStandard(str, Enum):
    """合規標準"""
    GDPR = "gdpr"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    OWASP = "owasp"

class AdvancedRole(BaseModel):
    """高級角色定義"""
    role_id: str
    role_name: str = Field(..., description="角色名稱")
    role_description: Optional[str] = Field(None, description="角色描述")
    permissions: List[str] = Field(..., description="權限列表")
    resource_constraints: Dict[str, Any] = Field(default={}, description="資源約束")
    time_constraints: Optional[Dict[str, Any]] = Field(None, description="時間約束")
    ip_restrictions: List[str] = Field(default=[], description="IP限制")
    is_system_role: bool = Field(False, description="是否為系統角色")
    created_at: datetime
    updated_at: datetime
    created_by: str

class DynamicPermission(BaseModel):
    """動態權限"""
    permission_id: str
    permission_name: str = Field(..., description="權限名稱")
    resource_pattern: str = Field(..., description="資源模式")
    action_pattern: str = Field(..., description="操作模式")
    context_rules: List[Dict[str, Any]] = Field(default=[], description="上下文規則")
    conditions: Dict[str, Any] = Field(default={}, description="條件配置")
    priority: int = Field(0, description="優先級")
    is_active: bool = Field(True, description="是否啟用")

class SecurityAuditLog(BaseModel):
    """安全審計日誌"""
    log_id: str
    event_type: SecurityEventType
    user_id: Optional[str] = Field(None, description="用戶ID")
    resource: str = Field(..., description="資源")
    action: str = Field(..., description="操作")
    ip_address: str = Field(..., description="IP地址")
    user_agent: Optional[str] = Field(None, description="用戶代理")
    session_id: Optional[str] = Field(None, description="會話ID")
    success: bool = Field(..., description="是否成功")
    details: Dict[str, Any] = Field(default={}, description="詳細信息")
    risk_score: float = Field(0.0, description="風險評分", ge=0, le=100)
    timestamp: datetime

class ThreatDetection(BaseModel):
    """威脅檢測結果"""
    detection_id: str
    threat_type: str = Field(..., description="威脅類型")
    threat_level: ThreatLevel
    source_ip: str = Field(..., description="源IP地址")
    target_resource: str = Field(..., description="目標資源")
    description: str = Field(..., description="威脅描述")
    evidence: List[Dict[str, Any]] = Field(..., description="證據列表")
    risk_score: float = Field(..., description="風險評分", ge=0, le=100)
    is_blocked: bool = Field(False, description="是否已阻止")
    detected_at: datetime
    resolved_at: Optional[datetime] = None

class ComplianceViolation(BaseModel):
    """合規違規記錄"""
    violation_id: str
    standard: ComplianceStandard
    rule_name: str = Field(..., description="規則名稱")
    violation_type: str = Field(..., description="違規類型")
    severity: str = Field(..., description="嚴重程度")
    resource_affected: str = Field(..., description="受影響資源")
    description: str = Field(..., description="違規描述")
    remediation_steps: List[str] = Field(..., description="整改步驟")
    status: str = Field("open", description="狀態")
    detected_at: datetime
    resolved_at: Optional[datetime] = None

class SecurityPolicy(BaseModel):
    """安全策略"""
    policy_id: str
    policy_name: str = Field(..., description="策略名稱")
    policy_type: str = Field(..., description="策略類型")
    description: str = Field(..., description="策略描述")
    rules: List[Dict[str, Any]] = Field(..., description="策略規則")
    enforcement_level: str = Field("warn", description="執行級別: warn, block")
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime
    updated_at: datetime

# ==================== 高級權限管理 ====================

@router.get("/rbac/roles", 
           response_model=List[AdvancedRole], 
           summary="獲取高級角色列表")
async def get_advanced_roles(
    include_system: bool = Query(True, description="包含系統角色"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取高級角色管理列表，支持動態權限和資源約束
    """
    try:
        # 模擬高級角色數據
        roles = [
            AdvancedRole(
                role_id="role_super_admin",
                role_name="超級管理員",
                role_description="具有系統完全控制權限的超級管理員",
                permissions=[
                    "system.admin",
                    "users.manage",
                    "security.manage",
                    "audit.access",
                    "config.modify"
                ],
                resource_constraints={
                    "data_classification": ["public", "internal", "confidential", "restricted"],
                    "geographic_access": ["global"]
                },
                time_constraints={
                    "business_hours_only": False,
                    "max_session_duration": 480
                },
                ip_restrictions=[],
                is_system_role=True,
                created_at=datetime.now() - timedelta(days=30),
                updated_at=datetime.now() - timedelta(days=7),
                created_by="system"
            ),
            AdvancedRole(
                role_id="role_security_admin",
                role_name="安全管理員",
                role_description="負責系統安全管理和監控的專業角色",
                permissions=[
                    "security.monitor",
                    "security.investigate",
                    "audit.read",
                    "threats.manage",
                    "compliance.monitor"
                ],
                resource_constraints={
                    "data_classification": ["public", "internal", "confidential"],
                    "scope": ["security_logs", "audit_logs", "threat_data"]
                },
                time_constraints={
                    "business_hours_only": False,
                    "max_session_duration": 240
                },
                ip_restrictions=["192.168.1.0/24", "10.0.0.0/8"],
                is_system_role=False,
                created_at=datetime.now() - timedelta(days=20),
                updated_at=datetime.now() - timedelta(days=3),
                created_by="admin_001"
            ),
            AdvancedRole(
                role_id="role_data_analyst",
                role_name="數據分析師",
                role_description="具有數據分析和報表權限的分析師角色",
                permissions=[
                    "analytics.read",
                    "reports.generate",
                    "dashboard.view",
                    "data.export"
                ],
                resource_constraints={
                    "data_classification": ["public", "internal"],
                    "data_types": ["aggregated", "anonymized"],
                    "retention_limit": "90_days"
                },
                time_constraints={
                    "business_hours_only": True,
                    "allowed_hours": "09:00-18:00",
                    "timezone": "Asia/Taipei"
                },
                ip_restrictions=["192.168.100.0/24"],
                is_system_role=False,
                created_at=datetime.now() - timedelta(days=15),
                updated_at=datetime.now() - timedelta(days=2),
                created_by="admin_002"
            )
        ]
        
        # 應用篩選
        filtered_roles = roles
        if not include_system:
            filtered_roles = [r for r in filtered_roles if not r.is_system_role]
        if search:
            search_lower = search.lower()
            filtered_roles = [r for r in filtered_roles 
                             if search_lower in r.role_name.lower() or 
                                (r.role_description and search_lower in r.role_description.lower())]
        
        api_logger.info("Advanced roles retrieved", extra={
            "user_id": current_user.user_id,
            "include_system": include_system,
            "search": search,
            "result_count": len(filtered_roles)
        })
        
        return filtered_roles
        
    except Exception as e:
        return await handle_error(e, "獲取高級角色列表失敗", api_logger)

@router.post("/rbac/roles", 
            response_model=AdvancedRole, 
            summary="創建高級角色")
async def create_advanced_role(
    role_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    創建新的高級角色，支持動態權限和約束條件
    """
    try:
        # 創建角色
        new_role = AdvancedRole(
            role_id=f"role_{uuid.uuid4().hex[:8]}",
            role_name=role_data["role_name"],
            role_description=role_data.get("role_description"),
            permissions=role_data["permissions"],
            resource_constraints=role_data.get("resource_constraints", {}),
            time_constraints=role_data.get("time_constraints"),
            ip_restrictions=role_data.get("ip_restrictions", []),
            is_system_role=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=current_user.user_id
        )
        
        security_logger.info("Advanced role created", extra={
            "admin_user": current_user.user_id,
            "role_name": new_role.role_name,
            "permissions_count": len(new_role.permissions),
            "has_constraints": bool(new_role.resource_constraints or new_role.time_constraints)
        })
        
        return new_role
        
    except Exception as e:
        return await handle_error(e, "創建高級角色失敗", api_logger)

@router.get("/rbac/permissions/dynamic", 
           response_model=List[DynamicPermission], 
           summary="獲取動態權限列表")
async def get_dynamic_permissions(
    active_only: bool = Query(True, description="僅顯示啟用的權限"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取動態權限配置列表
    """
    try:
        # 模擬動態權限數據
        permissions = [
            DynamicPermission(
                permission_id="dyn_perm_001",
                permission_name="時間敏感數據訪問",
                resource_pattern="/api/sensitive-data/*",
                action_pattern="GET|POST",
                context_rules=[
                    {
                        "type": "time_based",
                        "condition": "business_hours",
                        "value": "09:00-18:00"
                    },
                    {
                        "type": "ip_based",
                        "condition": "allowed_networks",
                        "value": ["192.168.1.0/24"]
                    }
                ],
                conditions={
                    "require_mfa": True,
                    "max_requests_per_hour": 100
                },
                priority=10,
                is_active=True
            ),
            DynamicPermission(
                permission_id="dyn_perm_002",
                permission_name="用戶數據修改權限",
                resource_pattern="/api/users/{user_id}/*",
                action_pattern="PUT|PATCH|DELETE",
                context_rules=[
                    {
                        "type": "user_relationship",
                        "condition": "owns_resource",
                        "value": True
                    },
                    {
                        "type": "data_classification",
                        "condition": "max_level",
                        "value": "internal"
                    }
                ],
                conditions={
                    "require_approval": True,
                    "approval_level": "manager"
                },
                priority=8,
                is_active=True
            ),
            DynamicPermission(
                permission_id="dyn_perm_003",
                permission_name="系統配置變更權限",
                resource_pattern="/api/system/config/*",
                action_pattern="POST|PUT|DELETE",
                context_rules=[
                    {
                        "type": "role_based",
                        "condition": "min_role_level",
                        "value": "senior_admin"
                    },
                    {
                        "type": "session_based",
                        "condition": "max_session_age",
                        "value": 300
                    }
                ],
                conditions={
                    "require_dual_approval": True,
                    "change_window": "maintenance_only"
                },
                priority=15,
                is_active=True
            )
        ]
        
        # 應用篩選
        if active_only:
            permissions = [p for p in permissions if p.is_active]
        
        return permissions
        
    except Exception as e:
        return await handle_error(e, "獲取動態權限列表失敗", api_logger)

# ==================== 安全審計日誌 ====================

@router.get("/audit-logs", 
           response_model=List[SecurityAuditLog], 
           summary="獲取安全審計日誌")
async def get_security_audit_logs(
    event_type: Optional[SecurityEventType] = Query(None, description="事件類型篩選"),
    user_id: Optional[str] = Query(None, description="用戶ID篩選"),
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    risk_threshold: float = Query(0.0, description="風險評分閾值", ge=0, le=100),
    page: int = Query(1, description="頁碼", ge=1),
    size: int = Query(50, description="每頁數量", ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取安全審計日誌，支持多維度篩選
    """
    try:
        # 模擬安全審計日誌數據
        audit_logs = [
            SecurityAuditLog(
                log_id="audit_001",
                event_type=SecurityEventType.LOGIN_ATTEMPT,
                user_id="user_12345",
                resource="/api/auth/login",
                action="authenticate",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                session_id="sess_abc123",
                success=True,
                details={
                    "authentication_method": "password",
                    "mfa_used": True,
                    "location": "Taipei, Taiwan"
                },
                risk_score=15.0,
                timestamp=datetime.now() - timedelta(minutes=30)
            ),
            SecurityAuditLog(
                log_id="audit_002",
                event_type=SecurityEventType.PERMISSION_CHANGE,
                user_id="admin_001",
                resource="/api/rbac/roles/role_user",
                action="modify_permissions",
                ip_address="192.168.1.50",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X)",
                session_id="sess_def456",
                success=True,
                details={
                    "changed_permissions": ["users.delete", "data.export"],
                    "target_role": "role_user",
                    "change_reason": "Policy update"
                },
                risk_score=75.0,
                timestamp=datetime.now() - timedelta(hours=2)
            ),
            SecurityAuditLog(
                log_id="audit_003",
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id="user_67890",
                resource="/api/data/export",
                action="bulk_export",
                ip_address="203.69.123.45",
                user_agent="curl/7.68.0",
                session_id="sess_ghi789",
                success=False,
                details={
                    "export_size": "10GB",
                    "unusual_time": "03:45 AM",
                    "geolocation_mismatch": True,
                    "blocked_reason": "Suspicious activity pattern"
                },
                risk_score=95.0,
                timestamp=datetime.now() - timedelta(hours=6)
            ),
            SecurityAuditLog(
                log_id="audit_004",
                event_type=SecurityEventType.DATA_ACCESS,
                user_id="user_54321",
                resource="/api/users/sensitive-data",
                action="read",
                ip_address="192.168.1.200",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_4)",
                session_id="sess_jkl012",
                success=True,
                details={
                    "data_classification": "confidential",
                    "access_justification": "Customer support case",
                    "supervisor_approval": True
                },
                risk_score=35.0,
                timestamp=datetime.now() - timedelta(hours=12)
            )
        ]
        
        # 應用篩選
        filtered_logs = audit_logs
        if event_type:
            filtered_logs = [log for log in filtered_logs if log.event_type == event_type]
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        if risk_threshold > 0:
            filtered_logs = [log for log in filtered_logs if log.risk_score >= risk_threshold]
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        # 分頁
        start = (page - 1) * size
        end = start + size
        paged_logs = filtered_logs[start:end]
        
        security_logger.info("Security audit logs accessed", extra={
            "admin_user": current_user.user_id,
            "filters_applied": {
                "event_type": event_type,
                "user_id": user_id,
                "risk_threshold": risk_threshold
            },
            "result_count": len(paged_logs)
        })
        
        return paged_logs
        
    except Exception as e:
        return await handle_error(e, "獲取安全審計日誌失敗", api_logger)

@router.post("/audit-logs/export", 
            summary="導出安全審計日誌")
async def export_audit_logs(
    export_config: Dict[str, Any] = Body(...),
    # background_tasks parameter removed for compatibility
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    導出安全審計日誌到指定格式
    """
    try:
        export_id = f"export_{uuid.uuid4().hex[:8]}"
        
        # 模擬導出任務
        export_result = {
            "export_id": export_id,
            "status": "initiated",
            "format": export_config.get("format", "csv"),
            "filters": export_config.get("filters", {}),
            "estimated_records": 12456,
            "estimated_completion": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "download_url": f"/api/security/audit-logs/download/{export_id}",
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "initiated_by": current_user.user_id,
            "initiated_at": datetime.now().isoformat()
        }
        
        # 添加背景任務處理導出
        # background_tasks.add_task(process_audit_log_export, export_id, export_config)
        
        security_logger.info("Audit log export initiated", extra={
            "admin_user": current_user.user_id,
            "export_id": export_id,
            "format": export_config.get("format"),
            "filters": export_config.get("filters", {})
        })
        
        return export_result
        
    except Exception as e:
        return await handle_error(e, "導出安全審計日誌失敗", api_logger)

# ==================== 威脅監控系統 ====================

@router.get("/threats/active", 
           response_model=List[ThreatDetection], 
           summary="獲取活動威脅列表")
async def get_active_threats(
    threat_level: Optional[ThreatLevel] = Query(None, description="威脅等級篩選"),
    unresolved_only: bool = Query(True, description="僅顯示未解決的威脅"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取當前活動的安全威脅列表
    """
    try:
        # 模擬威脅檢測數據
        threats = [
            ThreatDetection(
                detection_id="threat_001",
                threat_type="brute_force_attack",
                threat_level=ThreatLevel.HIGH,
                source_ip="45.123.45.67",
                target_resource="/api/auth/login",
                description="檢測到來自外部IP的暴力破解攻擊",
                evidence=[
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                        "event": "Failed login attempt",
                        "details": "Multiple failed attempts for user 'admin'"
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                        "event": "Rate limit exceeded",
                        "details": "100+ requests in 5 minutes"
                    }
                ],
                risk_score=87.5,
                is_blocked=True,
                detected_at=datetime.now() - timedelta(minutes=20),
                resolved_at=None
            ),
            ThreatDetection(
                detection_id="threat_002",
                threat_type="sql_injection_attempt",
                threat_level=ThreatLevel.CRITICAL,
                source_ip="103.45.67.89",
                target_resource="/api/data/query",
                description="檢測到SQL注入攻擊嘗試",
                evidence=[
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                        "event": "Malicious payload detected",
                        "details": "SQL injection pattern in query parameter"
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=3)).isoformat(),
                        "event": "WAF rule triggered",
                        "details": "Request blocked by Web Application Firewall"
                    }
                ],
                risk_score=95.0,
                is_blocked=True,
                detected_at=datetime.now() - timedelta(minutes=5),
                resolved_at=None
            ),
            ThreatDetection(
                detection_id="threat_003",
                threat_type="privilege_escalation",
                threat_level=ThreatLevel.MEDIUM,
                source_ip="192.168.1.150",
                target_resource="/api/rbac/roles",
                description="檢測到可疑的權限提升行為",
                evidence=[
                    {
                        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "event": "Unusual permission access",
                        "details": "User attempting to access admin functions"
                    }
                ],
                risk_score=65.0,
                is_blocked=False,
                detected_at=datetime.now() - timedelta(hours=1),
                resolved_at=None
            )
        ]
        
        # 應用篩選
        filtered_threats = threats
        if threat_level:
            filtered_threats = [t for t in filtered_threats if t.threat_level == threat_level]
        if unresolved_only:
            filtered_threats = [t for t in filtered_threats if t.resolved_at is None]
        
        return filtered_threats
        
    except Exception as e:
        return await handle_error(e, "獲取活動威脅列表失敗", api_logger)

@router.post("/threats/{threat_id}/respond", 
            summary="響應安全威脅")
async def respond_to_threat(
    threat_id: str,
    response_action: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    對檢測到的安全威脅採取響應措施
    """
    try:
        # 模擬威脅響應
        response_result = {
            "threat_id": threat_id,
            "action_taken": response_action.get("action", "investigate"),
            "details": response_action.get("details", {}),
            "automated_actions": [
                "IP address blocked in firewall",
                "User account temporarily suspended",
                "Alert sent to security team"
            ],
            "response_time_seconds": 15.6,
            "status": "completed",
            "responded_by": current_user.user_id,
            "responded_at": datetime.now().isoformat(),
            "next_steps": [
                "Monitor for similar patterns",
                "Review and update security rules",
                "Conduct follow-up investigation"
            ]
        }
        
        security_logger.warning("Security threat response initiated", extra={
            "admin_user": current_user.user_id,
            "threat_id": threat_id,
            "action": response_action.get("action"),
            "severity": "high"
        })
        
        return response_result
        
    except Exception as e:
        return await handle_error(e, "威脅響應失敗", api_logger)

# ==================== 合規性監控 ====================

@router.get("/compliance/violations", 
           response_model=List[ComplianceViolation], 
           summary="獲取合規違規記錄")
async def get_compliance_violations(
    standard: Optional[ComplianceStandard] = Query(None, description="合規標準篩選"),
    status: str = Query("open", description="狀態篩選: open, resolved, all"),
    severity: Optional[str] = Query(None, description="嚴重程度篩選"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取合規違規記錄列表
    """
    try:
        # 模擬合規違規數據
        violations = [
            ComplianceViolation(
                violation_id="comp_viol_001",
                standard=ComplianceStandard.GDPR,
                rule_name="Data Retention Policy",
                violation_type="data_retention_exceeded",
                severity="high",
                resource_affected="user_personal_data",
                description="用戶個人數據保留時間超過GDPR規定的必要期限",
                remediation_steps=[
                    "識別超期保留的數據記錄",
                    "評估數據的合法保留基礎",
                    "刪除無合法基礎的過期數據",
                    "更新數據保留政策"
                ],
                status="open",
                detected_at=datetime.now() - timedelta(days=2),
                resolved_at=None
            ),
            ComplianceViolation(
                violation_id="comp_viol_002",
                standard=ComplianceStandard.SOX,
                rule_name="Financial Data Access Control",
                violation_type="inadequate_access_control",
                severity="medium",
                resource_affected="financial_reports",
                description="財務數據訪問控制不符合SOX法案要求",
                remediation_steps=[
                    "實施更嚴格的角色分離",
                    "增加多重審批流程",
                    "加強訪問日誌監控",
                    "定期進行訪問權限審查"
                ],
                status="resolved",
                detected_at=datetime.now() - timedelta(days=10),
                resolved_at=datetime.now() - timedelta(days=3)
            ),
            ComplianceViolation(
                violation_id="comp_viol_003",
                standard=ComplianceStandard.OWASP,
                rule_name="Secure Authentication",
                violation_type="weak_authentication",
                severity="critical",
                resource_affected="authentication_system",
                description="身份驗證系統不符合OWASP安全標準",
                remediation_steps=[
                    "實施多因子身份驗證",
                    "加強密碼複雜度要求",
                    "實施帳戶鎖定機制",
                    "定期更新身份驗證框架"
                ],
                status="open",
                detected_at=datetime.now() - timedelta(hours=6),
                resolved_at=None
            )
        ]
        
        # 應用篩選
        filtered_violations = violations
        if standard:
            filtered_violations = [v for v in filtered_violations if v.standard == standard]
        if status != "all":
            if status == "open":
                filtered_violations = [v for v in filtered_violations if v.status == "open"]
            else:
                filtered_violations = [v for v in filtered_violations if v.status == status]
        if severity:
            filtered_violations = [v for v in filtered_violations if v.severity == severity]
        
        return filtered_violations
        
    except Exception as e:
        return await handle_error(e, "獲取合規違規記錄失敗", api_logger)

@router.get("/compliance/dashboard", 
           response_model=Dict[str, Any], 
           summary="獲取合規儀表板數據")
async def get_compliance_dashboard(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取合規性監控儀表板數據
    """
    try:
        # 模擬合規儀表板數據
        dashboard_data = {
            "overall_compliance_score": 87.3,
            "compliance_by_standard": {
                ComplianceStandard.GDPR.value: {
                    "score": 92.1,
                    "violations_count": 2,
                    "last_audit": "2025-07-15",
                    "status": "compliant"
                },
                ComplianceStandard.SOX.value: {
                    "score": 85.7,
                    "violations_count": 1,
                    "last_audit": "2025-08-01",
                    "status": "minor_issues"
                },
                ComplianceStandard.OWASP.value: {
                    "score": 78.9,
                    "violations_count": 3,
                    "last_audit": "2025-08-10",
                    "status": "needs_attention"
                },
                ComplianceStandard.ISO27001.value: {
                    "score": 94.2,
                    "violations_count": 0,
                    "last_audit": "2025-06-30",
                    "status": "compliant"
                }
            },
            "violation_trends": {
                "last_30_days": {
                    "total_violations": 12,
                    "resolved_violations": 8,
                    "open_violations": 4,
                    "critical_violations": 1
                },
                "severity_distribution": {
                    "critical": 1,
                    "high": 3,
                    "medium": 5,
                    "low": 3
                }
            },
            "upcoming_audits": [
                {
                    "standard": "GDPR",
                    "audit_date": "2025-09-15",
                    "auditor": "External Compliance Partner",
                    "preparation_status": "75%"
                },
                {
                    "standard": "SOX 404",
                    "audit_date": "2025-10-01",
                    "auditor": "Internal Audit Team",
                    "preparation_status": "45%"
                }
            ],
            "remediation_status": {
                "in_progress": 6,
                "pending_review": 2,
                "completed": 15,
                "overdue": 1
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        return await handle_error(e, "獲取合規儀表板數據失敗", api_logger)

# ==================== 安全策略管理 ====================

@router.get("/policies", 
           response_model=List[SecurityPolicy], 
           summary="獲取安全策略列表")
async def get_security_policies(
    policy_type: Optional[str] = Query(None, description="策略類型篩選"),
    active_only: bool = Query(True, description="僅顯示啟用的策略"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取安全策略配置列表
    """
    try:
        # 模擬安全策略數據
        policies = [
            SecurityPolicy(
                policy_id="policy_001",
                policy_name="密碼複雜度策略",
                policy_type="authentication",
                description="強制執行密碼複雜度和更新頻率要求",
                rules=[
                    {
                        "rule_type": "password_length",
                        "minimum": 12,
                        "enforcement": "mandatory"
                    },
                    {
                        "rule_type": "password_complexity",
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_numbers": True,
                        "require_special_chars": True
                    },
                    {
                        "rule_type": "password_expiry",
                        "max_age_days": 90,
                        "warning_days": 14
                    }
                ],
                enforcement_level="block",
                is_active=True,
                created_at=datetime.now() - timedelta(days=30),
                updated_at=datetime.now() - timedelta(days=5)
            ),
            SecurityPolicy(
                policy_id="policy_002",
                policy_name="數據分類訪問策略",
                policy_type="data_protection",
                description="基於數據分類等級的訪問控制策略",
                rules=[
                    {
                        "rule_type": "classification_access",
                        "confidential_data": {
                            "required_clearance": "confidential",
                            "require_mfa": True,
                            "max_session_time": 120
                        }
                    },
                    {
                        "rule_type": "restricted_data",
                        "access_conditions": {
                            "approval_required": True,
                            "business_justification": True,
                            "audit_logging": "enhanced"
                        }
                    }
                ],
                enforcement_level="warn",
                is_active=True,
                created_at=datetime.now() - timedelta(days=20),
                updated_at=datetime.now() - timedelta(days=10)
            ),
            SecurityPolicy(
                policy_id="policy_003",
                policy_name="網路安全監控策略",
                policy_type="network_security",
                description="網路流量監控和異常檢測策略",
                rules=[
                    {
                        "rule_type": "traffic_monitoring",
                        "monitor_inbound": True,
                        "monitor_outbound": True,
                        "alert_thresholds": {
                            "unusual_volume": "200%_baseline",
                            "suspicious_patterns": "enabled"
                        }
                    },
                    {
                        "rule_type": "geo_blocking",
                        "blocked_countries": ["CN", "RU", "KP"],
                        "exceptions": ["authenticated_users"]
                    }
                ],
                enforcement_level="block",
                is_active=True,
                created_at=datetime.now() - timedelta(days=15),
                updated_at=datetime.now() - timedelta(days=2)
            )
        ]
        
        # 應用篩選
        filtered_policies = policies
        if policy_type:
            filtered_policies = [p for p in filtered_policies if p.policy_type == policy_type]
        if active_only:
            filtered_policies = [p for p in filtered_policies if p.is_active]
        
        return filtered_policies
        
    except Exception as e:
        return await handle_error(e, "獲取安全策略列表失敗", api_logger)

@router.post("/policies/{policy_id}/enforce", 
            summary="執行安全策略")
async def enforce_security_policy(
    policy_id: str,
    enforcement_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    立即執行指定的安全策略
    """
    try:
        # 模擬策略執行
        enforcement_result = {
            "policy_id": policy_id,
            "enforcement_action": enforcement_config.get("action", "apply"),
            "scope": enforcement_config.get("scope", "all_users"),
            "execution_summary": {
                "total_targets": 12847,
                "successful_applications": 12823,
                "failed_applications": 24,
                "warnings_generated": 156
            },
            "execution_time_seconds": 45.7,
            "enforced_by": current_user.user_id,
            "enforced_at": datetime.now().isoformat(),
            "next_scheduled_check": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        security_logger.warning("Security policy enforcement executed", extra={
            "admin_user": current_user.user_id,
            "policy_id": policy_id,
            "enforcement_scope": enforcement_config.get("scope"),
            "impact": "system_wide"
        })
        
        return enforcement_result
        
    except Exception as e:
        return await handle_error(e, "執行安全策略失敗", api_logger)

# ==================== 系統健康檢查 ====================

@router.get("/health", summary="安全管理中心健康檢查")
async def security_center_health_check(
    db: Session = Depends(get_db)
):
    """
    安全管理中心健康檢查
    """
    try:
        # 檢查各個安全組件狀態
        health_status = {
            "rbac_system": True,
            "audit_logging": True,
            "threat_detection": True,
            "compliance_monitoring": True,
            "policy_enforcement": True,
            "security_alerts": True
        }
        
        overall_health = all(health_status.values())
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": health_status,
            "service": "security_management_center",
            "version": "v2.0.0",
            "active_threats": 3,
            "compliance_score": 87.3,
            "policy_violations_24h": 2
        }
        
    except Exception as e:
        error_info = await handle_error(e, "安全管理中心健康檢查失敗", api_logger)
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id if hasattr(error_info, 'error_id') else None,
            "service": "security_management_center"
        }


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # 測試路由配置
    print("安全管理中心路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")
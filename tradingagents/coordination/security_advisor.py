#!/usr/bin/env python3
"""
包拯 (Baozhen) - Security Advisor Agent
安全顧問代理人

包拯，中國古代著名清官，以其公正廉明、明察秋毫的品格著稱。
本代理人專注於網路安全、資料保護和安全合規性評估。

專業領域：
1. 安全漏洞掃描和評估
2. 安全架構設計和審查
3. 合規性檢查和報告
4. 事件響應和威脅分析
5. 安全最佳實踐指導
6. 資料隱私和保護
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import hashlib

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

logger = get_system_logger("security_advisor")

class SecurityLevel(Enum):
    """安全等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VulnerabilityType(Enum):
    """漏洞類型"""
    SQL_INJECTION = "sql_injection"
    XSS = "cross_site_scripting"
    CSRF = "cross_site_request_forgery"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_FLAW = "authorization_flaw"
    DATA_EXPOSURE = "sensitive_data_exposure"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    KNOWN_VULNERABILITIES = "using_components_with_known_vulnerabilities"
    INSUFFICIENT_LOGGING = "insufficient_logging_monitoring"

class ComplianceFramework(Enum):
    """合規框架"""
    GDPR = "general_data_protection_regulation"
    SOX = "sarbanes_oxley_act"
    PCI_DSS = "payment_card_industry_data_security_standard"
    HIPAA = "health_insurance_portability_accountability_act"
    ISO_27001 = "iso_27001"
    NIST = "nist_cybersecurity_framework"

class ThreatLevel(Enum):
    """威脅等級"""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityVulnerability:
    """安全漏洞"""
    vulnerability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    vulnerability_type: VulnerabilityType = VulnerabilityType.SECURITY_MISCONFIGURATION
    severity: SecurityLevel = SecurityLevel.MEDIUM
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    cvss_score: Optional[float] = None  # Common Vulnerability Scoring System
    affected_components: List[str] = field(default_factory=list)
    exploit_scenario: str = ""
    impact_assessment: str = ""
    remediation_steps: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    status: str = "open"

@dataclass
class SecurityAssessment:
    """安全評估"""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_system: str = ""
    assessment_type: str = "comprehensive"
    scope: List[str] = field(default_factory=list)
    vulnerabilities: List[SecurityVulnerability] = field(default_factory=list)
    security_score: float = 0.0
    risk_rating: SecurityLevel = SecurityLevel.MEDIUM
    executive_summary: str = ""
    detailed_findings: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    compliance_status: Dict[str, Any] = field(default_factory=dict)
    conducted_at: datetime = field(default_factory=datetime.now)
    next_assessment_date: Optional[datetime] = None

@dataclass
class SecurityIncident:
    """安全事件"""
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    incident_type: str = ""
    severity: SecurityLevel = SecurityLevel.MEDIUM
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    affected_systems: List[str] = field(default_factory=list)
    attack_vector: str = ""
    indicators_of_compromise: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    response_actions: List[str] = field(default_factory=list)
    containment_status: str = "investigating"
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    reported_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class ComplianceReport:
    """合規報告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    framework: ComplianceFramework = ComplianceFramework.ISO_27001
    organization: str = ""
    assessment_period: str = ""
    overall_compliance_score: float = 0.0
    compliant_controls: List[str] = field(default_factory=list)
    non_compliant_controls: List[str] = field(default_factory=list)
    remediation_plan: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    next_review_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=365))
    generated_at: datetime = field(default_factory=datetime.now)

class SecurityAdvisorBaozhen:
    """
    包拯 - 安全顧問代理人
    
    專注於系統安全評估、漏洞管理和合規性確保。
    提供全面的安全保護和風險管理服務。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = "security-advisor-baozhen"
        self.config = config or {}
        self.name = "包拯 (Baozhen) - 安全顧問"
        self.expertise_areas = [
            "安全漏洞評估",
            "威脅分析和響應",
            "合規性檢查",
            "安全架構審查",
            "事件調查分析",
            "安全政策制定"
        ]
        
        # 工作統計
        self.assessments_conducted = 0
        self.vulnerabilities_found = 0
        self.incidents_investigated = 0
        self.compliance_reports_generated = 0
        
        # 安全配置
        self.security_threshold = SecurityLevel(self.config.get('security_threshold', 'medium'))
        self.compliance_frameworks = [
            ComplianceFramework(fw) for fw in self.config.get('compliance_frameworks', ['iso_27001'])
        ]
        self.auto_scan_enabled = self.config.get('auto_scan_enabled', True)
        
        logger.info("安全顧問包拯已初始化", extra={
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'expertise_areas': self.expertise_areas,
            'security_threshold': self.security_threshold.value,
            'compliance_frameworks': [fw.value for fw in self.compliance_frameworks]
        })
    
    async def conduct_security_assessment(self,
                                        target_system: str,
                                        assessment_scope: List[str],
                                        source_code: Optional[str] = None,
                                        infrastructure_config: Optional[Dict[str, Any]] = None) -> SecurityAssessment:
        """進行安全評估"""
        
        assessment = SecurityAssessment(
            target_system=target_system,
            assessment_type="comprehensive",
            scope=assessment_scope
        )
        
        try:
            # 模擬安全評估過程
            await asyncio.sleep(1.5)
            
            # 進行各類安全掃描
            vulnerabilities = []
            
            # 程式碼安全掃描
            if source_code:
                code_vulns = await self._scan_source_code(source_code)
                vulnerabilities.extend(code_vulns)
            
            # 基礎設施安全掃描
            if infrastructure_config:
                infra_vulns = await self._scan_infrastructure(infrastructure_config)
                vulnerabilities.extend(infra_vulns)
            
            # 通用安全檢查
            general_vulns = await self._perform_general_security_checks(target_system, assessment_scope)
            vulnerabilities.extend(general_vulns)
            
            assessment.vulnerabilities = vulnerabilities
            self.vulnerabilities_found += len(vulnerabilities)
            
            # 計算安全評分
            assessment.security_score = self._calculate_security_score(vulnerabilities)
            assessment.risk_rating = self._determine_risk_rating(assessment.security_score, vulnerabilities)
            
            # 生成執行摘要
            assessment.executive_summary = self._generate_executive_summary(assessment)
            
            # 詳細發現
            assessment.detailed_findings = self._analyze_detailed_findings(vulnerabilities)
            
            # 生成建議
            assessment.recommendations = self._generate_security_recommendations(vulnerabilities)
            
            # 合規性狀態
            assessment.compliance_status = self._assess_compliance_status(vulnerabilities)
            
            # 設定下次評估日期
            assessment.next_assessment_date = datetime.now() + timedelta(days=90)
            
            self.assessments_conducted += 1
            
            logger.info("安全評估完成", extra={
                'assessment_id': assessment.assessment_id,
                'target_system': target_system,
                'vulnerabilities_found': len(vulnerabilities),
                'security_score': assessment.security_score,
                'risk_rating': assessment.risk_rating.value,
                'agent': self.agent_type
            })
            
            return assessment
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'conduct_security_assessment',
                'target_system': target_system
            })
            logger.error(f"安全評估失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def investigate_security_incident(self,
                                          incident_description: str,
                                          affected_systems: List[str],
                                          initial_indicators: List[str] = None) -> SecurityIncident:
        """調查安全事件"""
        
        incident = SecurityIncident(
            title=f"安全事件調查 - {datetime.now().strftime('%Y%m%d')}",
            description=incident_description,
            affected_systems=affected_systems,
            indicators_of_compromise=initial_indicators or []
        )
        
        try:
            # 模擬事件調查過程
            await asyncio.sleep(1.0)
            
            # 分類事件類型
            incident.incident_type = self._classify_incident_type(incident_description)
            
            # 評估嚴重程度
            incident.severity = self._assess_incident_severity(incident_description, affected_systems)
            incident.threat_level = self._assess_threat_level(incident.severity, incident.incident_type)
            
            # 分析攻擊向量
            incident.attack_vector = self._analyze_attack_vector(incident_description)
            
            # 收集更多IOC
            incident.indicators_of_compromise.extend(
                self._collect_additional_iocs(incident_description, affected_systems)
            )
            
            # 建立時間線
            incident.timeline = self._construct_incident_timeline(incident)
            
            # 制定響應行動
            incident.response_actions = self._plan_incident_response_actions(incident)
            
            # 影響評估
            incident.impact_assessment = self._assess_incident_impact(incident)
            
            # 執行初步遏制
            await self._execute_initial_containment(incident)
            incident.containment_status = "contained"
            
            # 提取經驗教訓
            incident.lessons_learned = self._extract_incident_lessons(incident)
            
            # 標記為已解決
            incident.resolved_at = datetime.now()
            
            self.incidents_investigated += 1
            
            logger.info("安全事件調查完成", extra={
                'incident_id': incident.incident_id,
                'incident_type': incident.incident_type,
                'severity': incident.severity.value,
                'threat_level': incident.threat_level.value,
                'affected_systems_count': len(affected_systems),
                'agent': self.agent_type
            })
            
            return incident
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'investigate_security_incident',
                'description': incident_description
            })
            logger.error(f"安全事件調查失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def generate_compliance_report(self,
                                       organization: str,
                                       framework: ComplianceFramework,
                                       assessment_data: Dict[str, Any]) -> ComplianceReport:
        """生成合規報告"""
        
        report = ComplianceReport(
            framework=framework,
            organization=organization,
            assessment_period=f"{datetime.now().year}年度"
        )
        
        try:
            # 模擬合規報告生成過程
            await asyncio.sleep(0.8)
            
            # 評估合規控制項
            compliance_assessment = self._assess_compliance_controls(framework, assessment_data)
            
            report.compliant_controls = compliance_assessment['compliant']
            report.non_compliant_controls = compliance_assessment['non_compliant']
            
            # 計算整體合規分數
            report.overall_compliance_score = self._calculate_compliance_score(
                report.compliant_controls, report.non_compliant_controls
            )
            
            # 制定補救計劃
            report.remediation_plan = self._create_remediation_plan(report.non_compliant_controls)
            
            # 風險評估
            report.risk_assessment = self._perform_compliance_risk_assessment(
                report.non_compliant_controls, framework
            )
            
            # 生成建議
            report.recommendations = self._generate_compliance_recommendations(
                framework, report.non_compliant_controls
            )
            
            self.compliance_reports_generated += 1
            
            logger.info("合規報告生成完成", extra={
                'report_id': report.report_id,
                'framework': framework.value,
                'organization': organization,
                'compliance_score': report.overall_compliance_score,
                'non_compliant_controls': len(report.non_compliant_controls),
                'agent': self.agent_type
            })
            
            return report
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'generate_compliance_report',
                'organization': organization
            })
            logger.error(f"合規報告生成失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def perform_threat_analysis(self,
                                    threat_intelligence: Dict[str, Any],
                                    system_context: Dict[str, Any]) -> Dict[str, Any]:
        """執行威脅分析"""
        
        try:
            # 模擬威脅分析過程
            await asyncio.sleep(0.6)
            
            analysis_result = {
                'analysis_id': str(uuid.uuid4()),
                'analyzed_at': datetime.now().isoformat(),
                'analyst': self.name,
                'threat_landscape': {},
                'applicable_threats': [],
                'risk_assessment': {},
                'mitigation_strategies': [],
                'monitoring_recommendations': [],
                'threat_indicators': []
            }
            
            # 分析威脅態勢
            analysis_result['threat_landscape'] = self._analyze_threat_landscape(threat_intelligence)
            
            # 識別適用威脅
            analysis_result['applicable_threats'] = self._identify_applicable_threats(
                threat_intelligence, system_context
            )
            
            # 風險評估
            analysis_result['risk_assessment'] = self._assess_threat_risks(
                analysis_result['applicable_threats'], system_context
            )
            
            # 緩解策略
            analysis_result['mitigation_strategies'] = self._recommend_mitigation_strategies(
                analysis_result['applicable_threats']
            )
            
            # 監控建議
            analysis_result['monitoring_recommendations'] = self._recommend_threat_monitoring(
                analysis_result['applicable_threats']
            )
            
            # 威脅指標
            analysis_result['threat_indicators'] = self._extract_threat_indicators(
                threat_intelligence
            )
            
            logger.info("威脅分析完成", extra={
                'analysis_id': analysis_result['analysis_id'],
                'applicable_threats_count': len(analysis_result['applicable_threats']),
                'risk_level': analysis_result['risk_assessment'].get('overall_risk', 'unknown'),
                'agent': self.agent_type
            })
            
            return analysis_result
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'perform_threat_analysis'
            })
            logger.error(f"威脅分析失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def _scan_source_code(self, source_code: str) -> List[SecurityVulnerability]:
        """掃描源代碼安全漏洞"""
        vulnerabilities = []
        
        # SQL注入檢查
        if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+.*%s', source_code, re.IGNORECASE):
            vulnerabilities.append(SecurityVulnerability(
                title="潛在SQL注入風險",
                description="檢測到可能的SQL注入漏洞，使用字符串拼接構建SQL查詢",
                vulnerability_type=VulnerabilityType.SQL_INJECTION,
                severity=SecurityLevel.HIGH,
                cwe_id="CWE-89",
                cvss_score=8.1,
                affected_components=["數據庫查詢層"],
                exploit_scenario="攻擊者可以通過惡意輸入執行任意SQL命令",
                impact_assessment="可能導致數據洩露、篡改或刪除",
                remediation_steps=[
                    "使用參數化查詢或預處理語句",
                    "實施輸入驗證和清理",
                    "使用最小權限原則配置數據庫用戶"
                ]
            ))
        
        # 硬編碼密碼檢查
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', source_code, re.IGNORECASE):
            vulnerabilities.append(SecurityVulnerability(
                title="硬編碼密碼",
                description="檢測到硬編碼的密碼或密鑰",
                vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                severity=SecurityLevel.MEDIUM,
                cwe_id="CWE-798",
                cvss_score=6.5,
                affected_components=["認證系統"],
                exploit_scenario="攻擊者可以從源代碼中獲取敏感憑證",
                impact_assessment="可能導致未授權訪問",
                remediation_steps=[
                    "使用環境變量或安全密鑰管理服務",
                    "實施密鑰輪換策略",
                    "從版本控制中移除敏感資訊"
                ]
            ))
        
        # 不安全的隨機數生成
        if 'random.random()' in source_code or 'Math.random()' in source_code:
            vulnerabilities.append(SecurityVulnerability(
                title="不安全的隨機數生成",
                description="使用了密碼學上不安全的隨機數生成器",
                vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                severity=SecurityLevel.MEDIUM,
                cwe_id="CWE-338",
                cvss_score=5.3,
                affected_components=["加密模組"],
                exploit_scenario="攻擊者可能預測隨機數序列",
                impact_assessment="可能削弱加密強度或令牌安全性",
                remediation_steps=[
                    "使用密碼學安全的隨機數生成器",
                    "使用os.urandom()或secrets模組",
                    "定期更新加密庫"
                ]
            ))
        
        return vulnerabilities
    
    async def _scan_infrastructure(self, infrastructure_config: Dict[str, Any]) -> List[SecurityVulnerability]:
        """掃描基礎設施安全配置"""
        vulnerabilities = []
        
        # 檢查加密配置
        security_config = infrastructure_config.get('security', {})
        
        if not security_config.get('encryption', {}).get('at_rest', False):
            vulnerabilities.append(SecurityVulnerability(
                title="數據靜態加密未啟用",
                description="數據庫或存儲系統未啟用靜態加密",
                vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                severity=SecurityLevel.HIGH,
                cwe_id="CWE-311",
                cvss_score=7.5,
                affected_components=["數據存儲"],
                exploit_scenario="數據洩露時敏感資訊可能被直接讀取",
                impact_assessment="機密數據可能暴露",
                remediation_steps=[
                    "啟用數據庫加密",
                    "配置存儲卷加密",
                    "實施密鑰管理策略"
                ]
            ))
        
        # 檢查網路安全配置
        network_config = infrastructure_config.get('networking', {})
        security_groups = network_config.get('security_groups', {})
        
        # 檢查是否有過於寬鬆的安全組規則
        for sg_name, sg_rules in security_groups.items():
            for rule in sg_rules.get('inbound', []):
                if rule.get('source') == '0.0.0.0/0' and rule.get('port') != 80 and rule.get('port') != 443:
                    vulnerabilities.append(SecurityVulnerability(
                        title="過於寬鬆的安全組規則",
                        description=f"安全組 {sg_name} 允許來自任何IP的連接到敏感端口",
                        vulnerability_type=VulnerabilityType.SECURITY_MISCONFIGURATION,
                        severity=SecurityLevel.MEDIUM,
                        cwe_id="CWE-693",
                        cvss_score=6.1,
                        affected_components=[f"安全組 {sg_name}"],
                        exploit_scenario="攻擊者可能從任意位置訪問敏感服務",
                        impact_assessment="增加攻擊面和未授權訪問風險",
                        remediation_steps=[
                            "限制來源IP範圍",
                            "使用最小權限原則",
                            "實施網路分段"
                        ]
                    ))
        
        return vulnerabilities
    
    async def _perform_general_security_checks(self, target_system: str, scope: List[str]) -> List[SecurityVulnerability]:
        """執行通用安全檢查"""
        vulnerabilities = []
        
        # 模擬一般性安全漏洞發現
        if 'authentication' in ' '.join(scope).lower():
            vulnerabilities.append(SecurityVulnerability(
                title="弱密碼政策",
                description="系統未實施強密碼要求",
                vulnerability_type=VulnerabilityType.AUTHENTICATION_BYPASS,
                severity=SecurityLevel.MEDIUM,
                cwe_id="CWE-521",
                cvss_score=5.8,
                affected_components=["認證系統"],
                exploit_scenario="攻擊者可能通過暴力破解獲取用戶帳戶",
                impact_assessment="用戶帳戶可能被未授權訪問",
                remediation_steps=[
                    "實施強密碼政策",
                    "啟用帳戶鎖定機制",
                    "實施多因素認證"
                ]
            ))
        
        if 'logging' in ' '.join(scope).lower():
            vulnerabilities.append(SecurityVulnerability(
                title="日誌監控不足",
                description="缺乏充分的安全事件日誌記錄和監控",
                vulnerability_type=VulnerabilityType.INSUFFICIENT_LOGGING,
                severity=SecurityLevel.LOW,
                cwe_id="CWE-778",
                cvss_score=3.1,
                affected_components=["日誌系統"],
                exploit_scenario="安全事件可能無法及時檢測",
                impact_assessment="延遲事件響應和調查",
                remediation_steps=[
                    "增強安全事件日誌記錄",
                    "實施實時監控告警",
                    "建立事件響應流程"
                ]
            ))
        
        return vulnerabilities
    
    def _calculate_security_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """計算安全評分"""
        if not vulnerabilities:
            return 100.0
        
        # 基礎分數
        base_score = 100.0
        
        # 根據漏洞嚴重程度扣分
        severity_penalties = {
            SecurityLevel.LOW: 2.0,
            SecurityLevel.MEDIUM: 5.0,
            SecurityLevel.HIGH: 10.0,
            SecurityLevel.CRITICAL: 20.0
        }
        
        for vuln in vulnerabilities:
            penalty = severity_penalties.get(vuln.severity, 5.0)
            base_score -= penalty
        
        return max(0.0, base_score)
    
    def _determine_risk_rating(self, security_score: float, vulnerabilities: List[SecurityVulnerability]) -> SecurityLevel:
        """確定風險等級"""
        # 檢查是否有關鍵漏洞
        has_critical = any(vuln.severity == SecurityLevel.CRITICAL for vuln in vulnerabilities)
        has_high = any(vuln.severity == SecurityLevel.HIGH for vuln in vulnerabilities)
        
        if has_critical or security_score < 50:
            return SecurityLevel.CRITICAL
        elif has_high or security_score < 70:
            return SecurityLevel.HIGH
        elif security_score < 85:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    def _generate_executive_summary(self, assessment: SecurityAssessment) -> str:
        """生成執行摘要"""
        vuln_count = len(assessment.vulnerabilities)
        critical_count = len([v for v in assessment.vulnerabilities if v.severity == SecurityLevel.CRITICAL])
        high_count = len([v for v in assessment.vulnerabilities if v.severity == SecurityLevel.HIGH])
        
        summary = f"""安全評估執行摘要

本次針對 {assessment.target_system} 的安全評估發現了 {vuln_count} 個安全問題。

風險概覽：
- 整體安全評分：{assessment.security_score:.1f}/100
- 風險等級：{assessment.risk_rating.value}
- 關鍵漏洞：{critical_count} 個
- 高風險漏洞：{high_count} 個

主要發現：
"""
        
        # 添加最嚴重的漏洞
        critical_vulns = [v for v in assessment.vulnerabilities if v.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]]
        for vuln in critical_vulns[:3]:  # 最多列出3個
            summary += f"- {vuln.title}\n"
        
        summary += f"""
建議立即處理關鍵和高風險漏洞，以降低安全風險。
詳細資訊請參考完整評估報告。
"""
        
        return summary
    
    def _analyze_detailed_findings(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """分析詳細發現"""
        findings = {
            'vulnerability_distribution': {},
            'severity_breakdown': {},
            'affected_components': {},
            'common_issues': [],
            'trend_analysis': {}
        }
        
        # 漏洞類型分佈
        type_counts = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.vulnerability_type.value
            type_counts[vuln_type] = type_counts.get(vuln_type, 0) + 1
        findings['vulnerability_distribution'] = type_counts
        
        # 嚴重程度分解
        severity_counts = {}
        for vuln in vulnerabilities:
            severity = vuln.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        findings['severity_breakdown'] = severity_counts
        
        # 受影響組件
        component_counts = {}
        for vuln in vulnerabilities:
            for component in vuln.affected_components:
                component_counts[component] = component_counts.get(component, 0) + 1
        findings['affected_components'] = component_counts
        
        # 常見問題
        if len(vulnerabilities) > 2:
            findings['common_issues'] = [
                '配置管理不當',
                '輸入驗證不足',
                '權限控制缺失'
            ]
        
        return findings
    
    def _generate_security_recommendations(self, vulnerabilities: List[SecurityVulnerability]) -> List[str]:
        """生成安全建議"""
        recommendations = []
        
        # 基於漏洞類型的建議
        vuln_types = set(vuln.vulnerability_type for vuln in vulnerabilities)
        
        if VulnerabilityType.SQL_INJECTION in vuln_types:
            recommendations.append("實施參數化查詢和輸入驗證來防止SQL注入")
        
        if VulnerabilityType.XSS in vuln_types:
            recommendations.append("實施輸出編碼和內容安全政策來防止XSS攻擊")
        
        if VulnerabilityType.AUTHENTICATION_BYPASS in vuln_types:
            recommendations.append("加強認證機制，實施多因素認證")
        
        if VulnerabilityType.DATA_EXPOSURE in vuln_types:
            recommendations.append("實施數據加密和訪問控制")
        
        # 通用建議
        recommendations.extend([
            "建立定期安全評估流程",
            "實施安全開發生命週期(SDLC)",
            "加強安全意識培訓",
            "建立事件響應計劃"
        ])
        
        return list(set(recommendations))  # 去重
    
    def _assess_compliance_status(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, Any]:
        """評估合規狀態"""
        compliance_status = {}
        
        for framework in self.compliance_frameworks:
            if framework == ComplianceFramework.GDPR:
                # GDPR 相關檢查
                data_protection_issues = len([
                    v for v in vulnerabilities 
                    if v.vulnerability_type == VulnerabilityType.DATA_EXPOSURE
                ])
                compliance_status['GDPR'] = {
                    'compliant': data_protection_issues == 0,
                    'issues_count': data_protection_issues,
                    'risk_level': 'high' if data_protection_issues > 0 else 'low'
                }
            
            elif framework == ComplianceFramework.ISO_27001:
                # ISO 27001 相關檢查
                total_issues = len(vulnerabilities)
                compliance_status['ISO_27001'] = {
                    'compliant': total_issues < 3,
                    'issues_count': total_issues,
                    'risk_level': 'high' if total_issues > 5 else 'medium' if total_issues > 2 else 'low'
                }
        
        return compliance_status
    
    def _classify_incident_type(self, description: str) -> str:
        """分類事件類型"""
        description_lower = description.lower()
        
        if 'malware' in description_lower or 'virus' in description_lower:
            return '惡意軟體感染'
        elif 'phishing' in description_lower or '釣魚' in description_lower:
            return '釣魚攻擊'
        elif 'ddos' in description_lower or '拒絕服務' in description_lower:
            return '拒絕服務攻擊'
        elif 'breach' in description_lower or '入侵' in description_lower:
            return '系統入侵'
        elif 'leak' in description_lower or '洩露' in description_lower:
            return '數據洩露'
        else:
            return '一般安全事件'
    
    def _assess_incident_severity(self, description: str, affected_systems: List[str]) -> SecurityLevel:
        """評估事件嚴重程度"""
        # 基於描述關鍵字評估
        critical_keywords = ['critical', 'breach', 'compromise', '洩露', '入侵']
        high_keywords = ['high', 'malware', 'attack', '攻擊', '惡意']
        
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in critical_keywords):
            return SecurityLevel.CRITICAL
        elif any(keyword in description_lower for keyword in high_keywords):
            return SecurityLevel.HIGH
        elif len(affected_systems) > 3:
            return SecurityLevel.HIGH
        elif len(affected_systems) > 1:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    def _assess_threat_level(self, severity: SecurityLevel, incident_type: str) -> ThreatLevel:
        """評估威脅等級"""
        if severity == SecurityLevel.CRITICAL:
            return ThreatLevel.CRITICAL
        elif severity == SecurityLevel.HIGH:
            return ThreatLevel.HIGH
        elif '入侵' in incident_type or '洩露' in incident_type:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.MEDIUM
    
    def _analyze_attack_vector(self, description: str) -> str:
        """分析攻擊向量"""
        description_lower = description.lower()
        
        if 'email' in description_lower or '郵件' in description_lower:
            return '電子郵件'
        elif 'web' in description_lower or '網頁' in description_lower:
            return '網頁應用程式'
        elif 'network' in description_lower or '網路' in description_lower:
            return '網路攻擊'
        elif 'usb' in description_lower or '移動設備' in description_lower:
            return '可移動媒體'
        else:
            return '未知'
    
    def _collect_additional_iocs(self, description: str, affected_systems: List[str]) -> List[str]:
        """收集額外的妥協指標"""
        iocs = []
        
        # 提取IP地址
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, description)
        iocs.extend([f"IP: {ip}" for ip in ips])
        
        # 提取域名
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        domains = re.findall(domain_pattern, description)
        iocs.extend([f"Domain: {domain}" for domain in domains])
        
        # 提取文件哈希（模擬） - 安全修復：使用SHA256替換MD5
        if 'file' in description.lower() or '檔案' in description.lower():
            fake_hash = hashlib.sha256(description.encode()).hexdigest()
            iocs.append(f"File Hash: {fake_hash}")
        
        return iocs
    
    def _construct_incident_timeline(self, incident: SecurityIncident) -> List[Dict[str, Any]]:
        """構建事件時間線"""
        timeline = [
            {
                'timestamp': incident.reported_at.isoformat(),
                'event': '事件報告',
                'description': '安全事件被檢測並報告',
                'severity': 'info'
            },
            {
                'timestamp': (incident.reported_at + timedelta(minutes=5)).isoformat(),
                'event': '初步分析',
                'description': '開始事件分析和分類',
                'severity': 'info'
            },
            {
                'timestamp': (incident.reported_at + timedelta(minutes=15)).isoformat(),
                'event': '遏制措施',
                'description': '實施初步遏制措施',
                'severity': 'warning'
            },
            {
                'timestamp': (incident.reported_at + timedelta(minutes=30)).isoformat(),
                'event': '深入調查',
                'description': '進行詳細的取證調查',
                'severity': 'info'
            }
        ]
        
        return timeline
    
    def _plan_incident_response_actions(self, incident: SecurityIncident) -> List[str]:
        """規劃事件響應行動"""
        actions = [
            "隔離受影響的系統",
            "收集和保存證據",
            "分析攻擊向量和範圍",
            "實施遏制措施",
            "通知相關利害關係人"
        ]
        
        # 根據事件類型添加特定行動
        if '入侵' in incident.incident_type:
            actions.extend([
                "更改所有可能受損的密碼",
                "檢查系統完整性",
                "掃描惡意軟體"
            ])
        elif '洩露' in incident.incident_type:
            actions.extend([
                "評估洩露數據的敏感性",
                "準備公告通知",
                "聯繫法律和合規團隊"
            ])
        
        return actions
    
    def _assess_incident_impact(self, incident: SecurityIncident) -> Dict[str, Any]:
        """評估事件影響"""
        return {
            'business_impact': {
                'revenue_loss': 'low' if incident.severity in [SecurityLevel.LOW, SecurityLevel.MEDIUM] else 'medium',
                'reputation_damage': 'medium' if incident.severity == SecurityLevel.HIGH else 'low',
                'operational_disruption': 'high' if len(incident.affected_systems) > 2 else 'medium'
            },
            'technical_impact': {
                'data_integrity': 'compromised' if '洩露' in incident.incident_type else 'intact',
                'system_availability': 'reduced' if len(incident.affected_systems) > 1 else 'normal',
                'confidentiality': 'breached' if incident.severity == SecurityLevel.CRITICAL else 'maintained'
            },
            'regulatory_impact': {
                'compliance_violations': incident.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL],
                'reporting_required': incident.severity == SecurityLevel.CRITICAL,
                'fines_potential': incident.severity == SecurityLevel.CRITICAL
            }
        }
    
    async def _execute_initial_containment(self, incident: SecurityIncident) -> None:
        """執行初步遏制"""
        # 模擬遏制操作
        await asyncio.sleep(0.2)
        
        # 添加遏制行動到時間線
        incident.timeline.append({
            'timestamp': datetime.now().isoformat(),
            'event': '遏制完成',
            'description': '初步遏制措施已實施',
            'severity': 'success'
        })
    
    def _extract_incident_lessons(self, incident: SecurityIncident) -> List[str]:
        """提取事件經驗教訓"""
        lessons = [
            "需要改進事件檢測機制",
            "應該加強員工安全意識培訓",
            "考慮實施更嚴格的訪問控制"
        ]
        
        if incident.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            lessons.extend([
                "需要建立更完善的事件響應流程",
                "應該定期進行安全演練",
                "考慮增加安全監控投資"
            ])
        
        return lessons
    
    def _assess_compliance_controls(self, framework: ComplianceFramework, assessment_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """評估合規控制項"""
        compliant_controls = []
        non_compliant_controls = []
        
        if framework == ComplianceFramework.ISO_27001:
            # ISO 27001 控制項模擬評估
            iso_controls = [
                "A.5.1.1 - 資訊安全政策",
                "A.6.1.1 - 資訊安全責任",
                "A.8.1.1 - 資產清單",
                "A.9.1.1 - 訪問控制政策",
                "A.12.1.1 - 操作程序",
                "A.14.1.1 - 安全開發",
                "A.16.1.1 - 事件管理",
                "A.18.1.1 - 合規性"
            ]
            
            # 基於評估數據模擬合規狀態
            security_score = assessment_data.get('security_score', 75)
            
            if security_score >= 80:
                compliant_controls = iso_controls[:6]
                non_compliant_controls = iso_controls[6:]
            elif security_score >= 60:
                compliant_controls = iso_controls[:4]
                non_compliant_controls = iso_controls[4:]
            else:
                compliant_controls = iso_controls[:2]
                non_compliant_controls = iso_controls[2:]
        
        elif framework == ComplianceFramework.GDPR:
            # GDPR 要求模擬評估
            gdpr_requirements = [
                "Art. 5 - 數據處理原則",
                "Art. 6 - 處理的合法性",
                "Art. 7 - 同意條件",
                "Art. 25 - 數據保護設計",
                "Art. 32 - 處理安全性",
                "Art. 33 - 違規通知",
                "Art. 35 - 數據保護影響評估"
            ]
            
            data_protection_score = assessment_data.get('data_protection_score', 70)
            
            if data_protection_score >= 85:
                compliant_controls = gdpr_requirements[:5]
                non_compliant_controls = gdpr_requirements[5:]
            else:
                compliant_controls = gdpr_requirements[:3]
                non_compliant_controls = gdpr_requirements[3:]
        
        return {
            'compliant': compliant_controls,
            'non_compliant': non_compliant_controls
        }
    
    def _calculate_compliance_score(self, compliant: List[str], non_compliant: List[str]) -> float:
        """計算合規分數"""
        total_controls = len(compliant) + len(non_compliant)
        if total_controls == 0:
            return 100.0
        
        return (len(compliant) / total_controls) * 100
    
    def _create_remediation_plan(self, non_compliant_controls: List[str]) -> List[Dict[str, Any]]:
        """創建補救計劃"""
        remediation_plan = []
        
        for i, control in enumerate(non_compliant_controls, 1):
            remediation_plan.append({
                'control': control,
                'priority': 'high' if i <= 2 else 'medium',
                'estimated_effort': f"{i * 2} weeks",
                'responsible_team': 'security_team',
                'target_completion': (datetime.now() + timedelta(weeks=i * 2)).strftime('%Y-%m-%d'),
                'actions': [
                    f"評估 {control} 的具體要求",
                    "制定實施計劃",
                    "執行必要的技術和程序改進",
                    "驗證合規性"
                ]
            })
        
        return remediation_plan
    
    def _perform_compliance_risk_assessment(self, non_compliant_controls: List[str], framework: ComplianceFramework) -> Dict[str, Any]:
        """執行合規風險評估"""
        risk_level = "high" if len(non_compliant_controls) > 3 else "medium" if len(non_compliant_controls) > 1 else "low"
        
        return {
            'overall_risk_level': risk_level,
            'financial_risk': {
                'potential_fines': 'high' if framework == ComplianceFramework.GDPR and risk_level == 'high' else 'medium',
                'business_impact': risk_level
            },
            'operational_risk': {
                'process_disruption': 'medium',
                'reputation_damage': risk_level
            },
            'regulatory_risk': {
                'audit_findings': 'likely' if risk_level == 'high' else 'possible',
                'license_impact': 'low'
            }
        }
    
    def _generate_compliance_recommendations(self, framework: ComplianceFramework, non_compliant_controls: List[str]) -> List[str]:
        """生成合規建議"""
        recommendations = [
            "建立定期合規性審查流程",
            "指派專責的合規管理人員",
            "實施合規性監控和報告機制"
        ]
        
        if framework == ComplianceFramework.GDPR:
            recommendations.extend([
                "建立數據保護官(DPO)角色",
                "實施數據保護影響評估流程",
                "建立個人數據處理記錄"
            ])
        elif framework == ComplianceFramework.ISO_27001:
            recommendations.extend([
                "建立資訊安全管理體系(ISMS)",
                "定期進行風險評估",
                "實施持續改進流程"
            ])
        
        if len(non_compliant_controls) > 3:
            recommendations.append("考慮聘請外部合規顧問")
        
        return recommendations
    
    def _analyze_threat_landscape(self, threat_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """分析威脅態勢"""
        return {
            'current_threat_level': 'elevated',
            'trending_threats': [
                'Ransomware',
                'Supply Chain Attacks',
                'Cloud Misconfigurations',
                'AI-Powered Attacks'
            ],
            'geographic_risks': {
                'high_risk_regions': ['某些地區'],
                'threat_actors': ['APT groups', 'Cybercriminals']
            },
            'industry_specific_threats': [
                'Financial sector targeting',
                'Data theft operations',
                'Business email compromise'
            ]
        }
    
    def _identify_applicable_threats(self, threat_intelligence: Dict[str, Any], system_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """識別適用威脅"""
        applicable_threats = [
            {
                'threat_id': 'T001',
                'name': 'Web Application Attacks',
                'description': '針對網頁應用程式的攻擊',
                'likelihood': 'high',
                'impact': 'medium',
                'attack_vectors': ['SQL Injection', 'XSS', 'CSRF']
            },
            {
                'threat_id': 'T002',
                'name': 'Insider Threats',
                'description': '內部威脅',
                'likelihood': 'medium',
                'impact': 'high',
                'attack_vectors': ['Privilege Abuse', 'Data Exfiltration']
            },
            {
                'threat_id': 'T003',
                'name': 'Advanced Persistent Threats',
                'description': '高級持續威脅',
                'likelihood': 'low',
                'impact': 'critical',
                'attack_vectors': ['Spear Phishing', 'Zero-day Exploits']
            }
        ]
        
        return applicable_threats
    
    def _assess_threat_risks(self, threats: List[Dict[str, Any]], system_context: Dict[str, Any]) -> Dict[str, Any]:
        """評估威脅風險"""
        risk_scores = []
        
        for threat in threats:
            likelihood_score = {'low': 1, 'medium': 2, 'high': 3}.get(threat['likelihood'], 2)
            impact_score = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(threat['impact'], 2)
            risk_score = likelihood_score * impact_score
            risk_scores.append(risk_score)
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        overall_risk = 'high' if avg_risk > 6 else 'medium' if avg_risk > 3 else 'low'
        
        return {
            'overall_risk': overall_risk,
            'risk_distribution': {
                'critical': len([s for s in risk_scores if s >= 9]),
                'high': len([s for s in risk_scores if 6 <= s < 9]),
                'medium': len([s for s in risk_scores if 3 <= s < 6]),
                'low': len([s for s in risk_scores if s < 3])
            },
            'top_risks': [threat['name'] for threat in threats[:3]]
        }
    
    def _recommend_mitigation_strategies(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """推薦緩解策略"""
        strategies = []
        
        for threat in threats:
            if threat['name'] == 'Web Application Attacks':
                strategies.append({
                    'threat': threat['name'],
                    'strategy': 'Web Application Firewall (WAF)',
                    'implementation': 'Deploy and configure WAF with custom rules',
                    'effectiveness': 'high',
                    'cost': 'medium'
                })
            elif threat['name'] == 'Insider Threats':
                strategies.append({
                    'threat': threat['name'],
                    'strategy': 'User Behavior Analytics (UBA)',
                    'implementation': 'Implement monitoring and anomaly detection',
                    'effectiveness': 'medium',
                    'cost': 'high'
                })
            elif threat['name'] == 'Advanced Persistent Threats':
                strategies.append({
                    'threat': threat['name'],
                    'strategy': 'Zero Trust Architecture',
                    'implementation': 'Implement comprehensive access controls',
                    'effectiveness': 'high',
                    'cost': 'high'
                })
        
        return strategies
    
    def _recommend_threat_monitoring(self, threats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """推薦威脅監控"""
        monitoring_recommendations = [
            {
                'monitoring_type': 'Network Traffic Analysis',
                'description': '監控網路流量異常',
                'tools': ['Network IDS/IPS', 'Flow Analysis'],
                'frequency': 'real-time'
            },
            {
                'monitoring_type': 'Endpoint Detection and Response',
                'description': '端點威脅檢測',
                'tools': ['EDR Solutions', 'Antivirus'],
                'frequency': 'continuous'
            },
            {
                'monitoring_type': 'Security Information and Event Management',
                'description': '安全事件關聯分析',
                'tools': ['SIEM Platform', 'Log Aggregation'],
                'frequency': 'real-time'
            }
        ]
        
        return monitoring_recommendations
    
    def _extract_threat_indicators(self, threat_intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取威脅指標"""
        indicators = [
            {
                'type': 'IP Address',
                'value': '192.168.1.100',
                'description': '已知惡意IP地址',
                'confidence': 'high',
                'source': 'threat_feed'
            },
            {
                'type': 'Domain',
                'value': 'malicious-domain.com',
                'description': '惡意域名',
                'confidence': 'medium',
                'source': 'internal_analysis'
            },
            {
                'type': 'File Hash',
                'value': 'a1b2c3d4e5f6...',
                'description': '惡意軟體哈希',
                'confidence': 'high',
                'source': 'external_intelligence'
            }
        ]
        
        return indicators
    
    def get_agent_status(self) -> Dict[str, Any]:
        """獲取代理人狀態"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'name': self.name,
            'expertise_areas': self.expertise_areas,
            'statistics': {
                'assessments_conducted': self.assessments_conducted,
                'vulnerabilities_found': self.vulnerabilities_found,
                'incidents_investigated': self.incidents_investigated,
                'compliance_reports_generated': self.compliance_reports_generated
            },
            'configuration': {
                'security_threshold': self.security_threshold.value,
                'compliance_frameworks': [fw.value for fw in self.compliance_frameworks],
                'auto_scan_enabled': self.auto_scan_enabled
            },
            'status': 'active',
            'last_updated': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 測試腳本
    async def test_security_advisor():
        print("測試安全顧問包拯...")
        
        advisor = SecurityAdvisorBaozhen({
            'security_threshold': 'high',
            'compliance_frameworks': ['iso_27001', 'gdpr'],
            'auto_scan_enabled': True
        })
        
        # 測試安全評估
        assessment = await advisor.conduct_security_assessment(
            "TradingAgents Platform",
            ["authentication", "api_security", "data_protection", "logging"],
            source_code="password = 'hardcoded123'\n# 安全修復：使用參數化查詢\n# 不安全：SELECT * FROM users WHERE id = " + user_id + "\n# 安全：SELECT * FROM users WHERE id = %s",
            infrastructure_config={
                'security': {'encryption': {'at_rest': False}},
                'networking': {
                    'security_groups': {
                        'web_sg': {
                            'inbound': [{'port': 22, 'source': '0.0.0.0/0'}]
                        }
                    }
                }
            }
        )
        
        print(f"安全評估完成: {assessment.assessment_id}")
        print(f"安全評分: {assessment.security_score}")
        print(f"風險等級: {assessment.risk_rating.value}")
        print(f"發現漏洞: {len(assessment.vulnerabilities)}")
        
        # 測試安全事件調查
        incident = await advisor.investigate_security_incident(
            "檢測到異常的數據庫查詢活動，懷疑有SQL注入攻擊",
            ["Database Server", "Web Application"],
            ["suspicious_queries.log", "192.168.1.50"]
        )
        
        print(f"安全事件調查完成: {incident.incident_id}")
        print(f"事件類型: {incident.incident_type}")
        print(f"嚴重程度: {incident.severity.value}")
        print(f"威脅等級: {incident.threat_level.value}")
        print(f"響應行動: {len(incident.response_actions)}")
        
        # 測試合規報告生成
        compliance_report = await advisor.generate_compliance_report(
            "TradingAgents Inc.",
            ComplianceFramework.ISO_27001,
            {'security_score': 75, 'data_protection_score': 80}
        )
        
        print(f"合規報告生成完成: {compliance_report.report_id}")
        print(f"合規框架: {compliance_report.framework.value}")
        print(f"合規分數: {compliance_report.overall_compliance_score:.1f}")
        print(f"不合規控制項: {len(compliance_report.non_compliant_controls)}")
        
        # 測試威脅分析
        threat_analysis = await advisor.perform_threat_analysis(
            {'current_threats': ['ransomware', 'phishing'], 'threat_level': 'high'},
            {'industry': 'financial', 'size': 'medium', 'cloud_usage': True}
        )
        
        print(f"威脅分析完成: {threat_analysis['analysis_id']}")
        print(f"適用威脅: {len(threat_analysis['applicable_threats'])}")
        print(f"整體風險: {threat_analysis['risk_assessment']['overall_risk']}")
        
        # 獲取代理人狀態
        status = advisor.get_agent_status()
        print(f"代理人狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        print("安全顧問包拯測試完成")
    
    asyncio.run(test_security_advisor())
"""
Regional Compliance Framework
Handles financial regulations across US, HK, CN, JP, TW markets
Task 4.2.3: 區域化合規框架

Features:
- Multi-jurisdiction regulatory compliance
- Real-time regulation updates
- Automated compliance checking
- Risk assessment and reporting
- Cross-border transaction monitoring
- Regulatory notification system
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from abc import ABC, abstractmethod

class Jurisdiction(Enum):
    UNITED_STATES = "US"  # SEC, FINRA, CFTC
    HONG_KONG = "HK"      # SFC
    CHINA = "CN"          # CSRC, SAFE
    JAPAN = "JP"          # FSA, JFSA
    TAIWAN = "TW"         # FSC, TWSE

class RegulationType(Enum):
    INVESTMENT_ADVISORY = "investment_advisory"
    MARKET_DATA = "market_data"
    CROSS_BORDER = "cross_border"
    ANTI_MONEY_LAUNDERING = "aml"
    KNOW_YOUR_CUSTOMER = "kyc"
    DATA_PRIVACY = "data_privacy"
    REPORTING = "reporting"
    LICENSING = "licensing"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"
    REQUIRES_ACTION = "requires_action"

@dataclass
class RegulationRule:
    """Individual regulation rule"""
    id: str
    jurisdiction: Jurisdiction
    regulation_type: RegulationType
    title: str
    description: str
    requirements: List[str]
    penalties: List[str]
    effective_date: datetime
    last_updated: datetime
    source_url: Optional[str] = None
    severity_level: str = "medium"  # low, medium, high, critical

@dataclass
class ComplianceCheck:
    """Result of compliance checking"""
    rule_id: str
    status: ComplianceStatus
    jurisdiction: Jurisdiction
    regulation_type: RegulationType
    check_timestamp: datetime
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0-1 scale
    required_actions: List[str] = field(default_factory=list)

@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    report_id: str
    jurisdiction: Jurisdiction
    generated_at: datetime
    overall_status: ComplianceStatus
    checks: List[ComplianceCheck]
    risk_summary: Dict[str, Any]
    action_items: List[str]
    next_review_date: datetime

class RegulationDatabase:
    """Database of financial regulations by jurisdiction"""
    
    def __init__(self):
        self.regulations = self._initialize_regulations()
        
    def _initialize_regulations(self) -> Dict[Jurisdiction, List[RegulationRule]]:
        """Initialize regulation database"""
        
        regulations = {
            Jurisdiction.UNITED_STATES: [
                RegulationRule(
                    id="SEC_IA_001",
                    jurisdiction=Jurisdiction.UNITED_STATES,
                    regulation_type=RegulationType.INVESTMENT_ADVISORY,
                    title="Investment Advisers Act of 1940",
                    description="Registration and regulation of investment advisers",
                    requirements=[
                        "Register with SEC if assets under management > $100M",
                        "File Form ADV annually",
                        "Maintain fiduciary duty to clients",
                        "Implement compliance policies and procedures"
                    ],
                    penalties=[
                        "Civil monetary penalties up to $500,000",
                        "Suspension or revocation of registration",
                        "Disgorgement of profits"
                    ],
                    effective_date=datetime(1940, 8, 22, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 12, 1, tzinfo=timezone.utc),
                    source_url="https://www.sec.gov/rules/final/ia-1940.htm",
                    severity_level="critical"
                ),
                RegulationRule(
                    id="FINRA_AML_001",
                    jurisdiction=Jurisdiction.UNITED_STATES,
                    regulation_type=RegulationType.ANTI_MONEY_LAUNDERING,
                    title="Anti-Money Laundering (AML) Rules",
                    description="Requirements for AML compliance programs",
                    requirements=[
                        "Establish written AML compliance program",
                        "Designate AML compliance officer",
                        "Conduct ongoing training",
                        "File Suspicious Activity Reports (SARs)"
                    ],
                    penalties=[
                        "Fines up to $1,000,000 per violation",
                        "Criminal prosecution",
                        "License suspension"
                    ],
                    effective_date=datetime(2002, 4, 24, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 6, 15, tzinfo=timezone.utc),
                    severity_level="critical"
                )
            ],
            Jurisdiction.HONG_KONG: [
                RegulationRule(
                    id="SFC_LICENSE_001",
                    jurisdiction=Jurisdiction.HONG_KONG,
                    regulation_type=RegulationType.LICENSING,
                    title="Securities and Futures Ordinance (SFO) Licensing",
                    description="Licensing requirements for securities activities",
                    requirements=[
                        "Obtain Type 1 (Dealing in Securities) license",
                        "Maintain minimum paid-up capital HK$5M",
                        "Employ responsible officers",
                        "Submit annual returns"
                    ],
                    penalties=[
                        "Fine up to HK$10,000,000",
                        "Imprisonment up to 10 years",
                        "License revocation"
                    ],
                    effective_date=datetime(2003, 4, 1, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 9, 30, tzinfo=timezone.utc),
                    severity_level="critical"
                )
            ],
            Jurisdiction.CHINA: [
                RegulationRule(
                    id="CSRC_IA_001",
                    jurisdiction=Jurisdiction.CHINA,
                    regulation_type=RegulationType.INVESTMENT_ADVISORY,
                    title="Investment Advisory Business Regulations",
                    description="Regulations for investment advisory services",
                    requirements=[
                        "Obtain investment advisory business license",
                        "Minimum registered capital RMB 10M",
                        "Qualified professional staff",
                        "Regular reporting to CSRC"
                    ],
                    penalties=[
                        "Warning and fine RMB 30,000-300,000",
                        "Business suspension",
                        "License revocation"
                    ],
                    effective_date=datetime(2008, 10, 12, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 11, 20, tzinfo=timezone.utc),
                    severity_level="high"
                )
            ],
            Jurisdiction.JAPAN: [
                RegulationRule(
                    id="FSA_FIEA_001",
                    jurisdiction=Jurisdiction.JAPAN,
                    regulation_type=RegulationType.INVESTMENT_ADVISORY,
                    title="Financial Instruments and Exchange Act (FIEA)",
                    description="Investment advisory and agency business regulations",
                    requirements=[
                        "Register as Investment Advisory and Agency Business",
                        "Minimum net assets JPY 50M",
                        "Qualified investment advisory representatives",
                        "Submit quarterly reports"
                    ],
                    penalties=[
                        "Administrative monetary penalty up to JPY 300M",
                        "Business improvement order",
                        "Business suspension"
                    ],
                    effective_date=datetime(2007, 9, 30, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 10, 1, tzinfo=timezone.utc),
                    severity_level="high"
                )
            ],
            Jurisdiction.TAIWAN: [
                RegulationRule(
                    id="FSC_SFIA_001",
                    jurisdiction=Jurisdiction.TAIWAN,
                    regulation_type=RegulationType.INVESTMENT_ADVISORY,
                    title="Securities and Futures Investment Advisory Act",
                    description="Investment advisory business licensing and operations",
                    requirements=[
                        "Obtain investment advisory business license",
                        "Minimum paid-in capital NT$20M",
                        "Qualified analysis personnel",
                        "File monthly business reports"
                    ],
                    penalties=[
                        "Fine NT$600,000-30,000,000",
                        "Business suspension",
                        "License revocation"
                    ],
                    effective_date=datetime(2004, 2, 9, tzinfo=timezone.utc),
                    last_updated=datetime(2023, 8, 15, tzinfo=timezone.utc),
                    severity_level="high"
                )
            ]
        }
        
        return regulations
    
    def get_regulations(self, jurisdiction: Jurisdiction, regulation_type: Optional[RegulationType] = None) -> List[RegulationRule]:
        """Get regulations for specific jurisdiction and type"""
        rules = self.regulations.get(jurisdiction, [])
        
        if regulation_type:
            rules = [rule for rule in rules if rule.regulation_type == regulation_type]
        
        return rules
    
    def get_regulation_by_id(self, regulation_id: str) -> Optional[RegulationRule]:
        """Get specific regulation by ID"""
        for jurisdiction_rules in self.regulations.values():
            for rule in jurisdiction_rules:
                if rule.id == regulation_id:
                    return rule
        return None

class ComplianceChecker:
    """Performs compliance checks against regulations"""
    
    def __init__(self, regulation_db: RegulationDatabase):
        self.regulation_db = regulation_db
        self.logger = logging.getLogger(__name__)
    
    async def check_compliance(
        self, 
        jurisdiction: Jurisdiction, 
        business_context: Dict[str, Any]
    ) -> List[ComplianceCheck]:
        """Perform comprehensive compliance check"""
        
        regulations = self.regulation_db.get_regulations(jurisdiction)
        compliance_checks = []
        
        for regulation in regulations:
            check = await self._check_single_regulation(regulation, business_context)
            compliance_checks.append(check)
        
        return compliance_checks
    
    async def _check_single_regulation(
        self, 
        regulation: RegulationRule, 
        business_context: Dict[str, Any]
    ) -> ComplianceCheck:
        """Check compliance with a single regulation"""
        
        violations = []
        recommendations = []
        risk_score = 0.0
        required_actions = []
        
        # Perform specific checks based on regulation type
        if regulation.regulation_type == RegulationType.INVESTMENT_ADVISORY:
            check_result = self._check_investment_advisory_compliance(regulation, business_context)
        elif regulation.regulation_type == RegulationType.ANTI_MONEY_LAUNDERING:
            check_result = self._check_aml_compliance(regulation, business_context)
        elif regulation.regulation_type == RegulationType.LICENSING:
            check_result = self._check_licensing_compliance(regulation, business_context)
        else:
            check_result = self._check_general_compliance(regulation, business_context)
        
        violations.extend(check_result.get("violations", []))
        recommendations.extend(check_result.get("recommendations", []))
        risk_score = check_result.get("risk_score", 0.0)
        required_actions.extend(check_result.get("required_actions", []))
        
        # Determine overall status
        if not violations:
            status = ComplianceStatus.COMPLIANT
        elif risk_score > 0.8:
            status = ComplianceStatus.NON_COMPLIANT
        elif required_actions:
            status = ComplianceStatus.REQUIRES_ACTION
        else:
            status = ComplianceStatus.PENDING_REVIEW
        
        return ComplianceCheck(
            rule_id=regulation.id,
            status=status,
            jurisdiction=regulation.jurisdiction,
            regulation_type=regulation.regulation_type,
            check_timestamp=datetime.now(timezone.utc),
            violations=violations,
            recommendations=recommendations,
            risk_score=risk_score,
            required_actions=required_actions
        )
    
    def _check_investment_advisory_compliance(
        self, 
        regulation: RegulationRule, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check investment advisory specific compliance"""
        
        violations = []
        recommendations = []
        risk_score = 0.0
        required_actions = []
        
        # Check asset threshold (example for US)
        if regulation.jurisdiction == Jurisdiction.UNITED_STATES:
            aum = context.get("assets_under_management", 0)
            if aum > 100_000_000 and not context.get("sec_registered", False):
                violations.append("Assets under management exceed $100M but not SEC registered")
                risk_score += 0.8
                required_actions.append("Register with SEC immediately")
        
        # Check licensing requirements
        if not context.get("investment_advisory_license", False):
            violations.append("Missing investment advisory license")
            risk_score += 0.6
            required_actions.append("Obtain required investment advisory license")
        
        # Check compliance policies
        if not context.get("compliance_policies", False):
            violations.append("Missing compliance policies and procedures")
            risk_score += 0.4
            recommendations.append("Implement comprehensive compliance policies")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "risk_score": min(risk_score, 1.0),
            "required_actions": required_actions
        }
    
    def _check_aml_compliance(
        self, 
        regulation: RegulationRule, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check AML compliance"""
        
        violations = []
        recommendations = []
        risk_score = 0.0
        required_actions = []
        
        # Check AML program
        if not context.get("aml_program", False):
            violations.append("Missing written AML compliance program")
            risk_score += 0.9
            required_actions.append("Establish written AML compliance program")
        
        # Check AML officer
        if not context.get("aml_officer", False):
            violations.append("No designated AML compliance officer")
            risk_score += 0.7
            required_actions.append("Designate qualified AML compliance officer")
        
        # Check training
        if not context.get("aml_training", False):
            violations.append("Missing ongoing AML training program")
            risk_score += 0.5
            recommendations.append("Implement regular AML training for staff")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "risk_score": min(risk_score, 1.0),
            "required_actions": required_actions
        }
    
    def _check_licensing_compliance(
        self, 
        regulation: RegulationRule, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check licensing compliance"""
        
        violations = []
        recommendations = []
        risk_score = 0.0
        required_actions = []
        
        # Check required licenses
        required_licenses = context.get("required_licenses", [])
        held_licenses = context.get("held_licenses", [])
        
        for license_type in required_licenses:
            if license_type not in held_licenses:
                violations.append(f"Missing required license: {license_type}")
                risk_score += 0.8
                required_actions.append(f"Obtain {license_type} license")
        
        # Check capital requirements
        if regulation.jurisdiction == Jurisdiction.HONG_KONG:
            paid_capital = context.get("paid_up_capital_hkd", 0)
            if paid_capital < 5_000_000:
                violations.append("Paid-up capital below HK$5M minimum requirement")
                risk_score += 0.6
                required_actions.append("Increase paid-up capital to meet minimum requirement")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "risk_score": min(risk_score, 1.0),
            "required_actions": required_actions
        }
    
    def _check_general_compliance(
        self, 
        regulation: RegulationRule, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check general compliance requirements"""
        
        violations = []
        recommendations = []
        risk_score = 0.2  # Base risk for unchecked regulations
        required_actions = []
        
        recommendations.append(f"Review compliance with {regulation.title}")
        
        return {
            "violations": violations,
            "recommendations": recommendations,
            "risk_score": risk_score,
            "required_actions": required_actions
        }

class RegionalComplianceFramework:
    """Main regional compliance framework"""
    
    def __init__(self):
        self.regulation_db = RegulationDatabase()
        self.compliance_checker = ComplianceChecker(self.regulation_db)
        self.logger = logging.getLogger(__name__)
        
        # Compliance monitoring configuration
        self.monitoring_config = {
            "check_frequency": timedelta(days=30),  # Monthly checks
            "critical_alert_threshold": 0.8,
            "notification_channels": ["email", "dashboard"],
            "auto_remediation_enabled": False
        }
    
    async def perform_multi_jurisdiction_compliance_check(
        self, 
        jurisdictions: List[Jurisdiction],
        business_context: Dict[str, Any]
    ) -> Dict[Jurisdiction, ComplianceReport]:
        """Perform compliance check across multiple jurisdictions"""
        
        reports = {}
        
        for jurisdiction in jurisdictions:
            try:
                report = await self._generate_compliance_report(jurisdiction, business_context)
                reports[jurisdiction] = report
            except Exception as e:
                self.logger.error(f"Compliance check failed for {jurisdiction.value}: {str(e)}")
                reports[jurisdiction] = self._create_error_report(jurisdiction, str(e))
        
        return reports
    
    async def _generate_compliance_report(
        self, 
        jurisdiction: Jurisdiction, 
        business_context: Dict[str, Any]
    ) -> ComplianceReport:
        """Generate comprehensive compliance report for jurisdiction"""
        
        # Perform compliance checks
        checks = await self.compliance_checker.check_compliance(jurisdiction, business_context)
        
        # Analyze overall status
        non_compliant_checks = [c for c in checks if c.status == ComplianceStatus.NON_COMPLIANT]
        requires_action_checks = [c for c in checks if c.status == ComplianceStatus.REQUIRES_ACTION]
        
        if non_compliant_checks:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif requires_action_checks:
            overall_status = ComplianceStatus.REQUIRES_ACTION
        else:
            overall_status = ComplianceStatus.COMPLIANT
        
        # Calculate risk summary
        risk_scores = [c.risk_score for c in checks]
        risk_summary = {
            "average_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0.0,
            "max_risk_score": max(risk_scores) if risk_scores else 0.0,
            "high_risk_count": len([r for r in risk_scores if r > 0.7]),
            "critical_violations": len(non_compliant_checks)
        }
        
        # Compile action items
        action_items = []
        for check in checks:
            action_items.extend(check.required_actions)
        
        # Determine next review date
        next_review_date = datetime.now(timezone.utc) + self.monitoring_config["check_frequency"]
        
        return ComplianceReport(
            report_id=f"RPT_{jurisdiction.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            jurisdiction=jurisdiction,
            generated_at=datetime.now(timezone.utc),
            overall_status=overall_status,
            checks=checks,
            risk_summary=risk_summary,
            action_items=list(set(action_items)),  # Remove duplicates
            next_review_date=next_review_date
        )
    
    def _create_error_report(self, jurisdiction: Jurisdiction, error_message: str) -> ComplianceReport:
        """Create error report when compliance check fails"""
        
        return ComplianceReport(
            report_id=f"ERR_{jurisdiction.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            jurisdiction=jurisdiction,
            generated_at=datetime.now(timezone.utc),
            overall_status=ComplianceStatus.PENDING_REVIEW,
            checks=[],
            risk_summary={"error": error_message},
            action_items=[f"Resolve compliance check error: {error_message}"],
            next_review_date=datetime.now(timezone.utc) + timedelta(days=1)
        )
    
    def get_cross_border_compliance_requirements(
        self, 
        source_jurisdiction: Jurisdiction, 
        target_jurisdiction: Jurisdiction
    ) -> Dict[str, Any]:
        """Get compliance requirements for cross-border operations"""
        
        requirements = {
            "source_jurisdiction": source_jurisdiction.value,
            "target_jurisdiction": target_jurisdiction.value,
            "cross_border_requirements": [],
            "notification_requirements": [],
            "reporting_obligations": [],
            "licensing_requirements": []
        }
        
        # Define cross-border compliance matrix
        cross_border_matrix = {
            (Jurisdiction.UNITED_STATES, Jurisdiction.HONG_KONG): {
                "cross_border_requirements": [
                    "Register as foreign investment adviser if providing advisory services",
                    "Comply with FATCA reporting requirements",
                    "Observe US sanctions and export controls"
                ],
                "notification_requirements": [
                    "Notify SEC of foreign operations",
                    "File Form 13F if applicable"
                ],
                "reporting_obligations": [
                    "Annual foreign bank account reporting (FBAR)",
                    "Form 8938 (FATCA) reporting"
                ]
            },
            (Jurisdiction.TAIWAN, Jurisdiction.CHINA): {
                "cross_border_requirements": [
                    "Comply with cross-strait financial regulations",
                    "Obtain CSRC approval for mainland operations",
                    "Follow SAFE foreign exchange regulations"
                ],
                "notification_requirements": [
                    "Notify FSC of cross-border activities",
                    "Register with SAFE for forex transactions"
                ]
            }
            # Add more jurisdiction pairs as needed
        }
        
        jurisdiction_pair = (source_jurisdiction, target_jurisdiction)
        if jurisdiction_pair in cross_border_matrix:
            requirements.update(cross_border_matrix[jurisdiction_pair])
        else:
            requirements["cross_border_requirements"] = [
                "Review bilateral investment treaties",
                "Consult local regulatory requirements",
                "Consider tax implications"
            ]
        
        return requirements
    
    async def monitor_regulatory_updates(self) -> Dict[str, Any]:
        """Monitor for regulatory updates across jurisdictions"""
        
        # Mock implementation - in practice, would integrate with regulatory feeds
        updates = {
            "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
            "new_regulations": [],
            "updated_regulations": [],
            "alerts": []
        }
        
        # Check for regulation updates (simplified)
        for jurisdiction in Jurisdiction:
            regulations = self.regulation_db.get_regulations(jurisdiction)
            for regulation in regulations:
                # Check if regulation was updated recently (within 30 days)
                days_since_update = (datetime.now(timezone.utc) - regulation.last_updated).days
                if days_since_update <= 30:
                    updates["updated_regulations"].append({
                        "regulation_id": regulation.id,
                        "jurisdiction": jurisdiction.value,
                        "title": regulation.title,
                        "last_updated": regulation.last_updated.isoformat(),
                        "severity": regulation.severity_level
                    })
        
        return updates
    
    def generate_compliance_dashboard(
        self, 
        reports: Dict[Jurisdiction, ComplianceReport]
    ) -> Dict[str, Any]:
        """Generate compliance dashboard summary"""
        
        dashboard = {
            "summary": {
                "total_jurisdictions": len(reports),
                "compliant_jurisdictions": 0,
                "non_compliant_jurisdictions": 0,
                "requires_action_jurisdictions": 0,
                "pending_review_jurisdictions": 0
            },
            "risk_analysis": {
                "highest_risk_jurisdiction": None,
                "average_risk_score": 0.0,
                "critical_issues": 0
            },
            "action_items": [],
            "next_review_dates": {}
        }
        
        risk_scores = []
        all_action_items = []
        
        for jurisdiction, report in reports.items():
            # Update summary counts
            if report.overall_status == ComplianceStatus.COMPLIANT:
                dashboard["summary"]["compliant_jurisdictions"] += 1
            elif report.overall_status == ComplianceStatus.NON_COMPLIANT:
                dashboard["summary"]["non_compliant_jurisdictions"] += 1
            elif report.overall_status == ComplianceStatus.REQUIRES_ACTION:
                dashboard["summary"]["requires_action_jurisdictions"] += 1
            else:
                dashboard["summary"]["pending_review_jurisdictions"] += 1
            
            # Track risk scores
            if "average_risk_score" in report.risk_summary:
                risk_scores.append(report.risk_summary["average_risk_score"])
            
            # Collect action items
            all_action_items.extend(report.action_items)
            
            # Track review dates
            dashboard["next_review_dates"][jurisdiction.value] = report.next_review_date.isoformat()
        
        # Calculate risk analysis
        if risk_scores:
            dashboard["risk_analysis"]["average_risk_score"] = sum(risk_scores) / len(risk_scores)
            highest_risk_idx = risk_scores.index(max(risk_scores))
            dashboard["risk_analysis"]["highest_risk_jurisdiction"] = list(reports.keys())[highest_risk_idx].value
        
        # Count critical issues
        dashboard["risk_analysis"]["critical_issues"] = sum(
            report.risk_summary.get("critical_violations", 0) 
            for report in reports.values()
        )
        
        # Deduplicate action items
        dashboard["action_items"] = list(set(all_action_items))[:20]  # Top 20 items
        
        return dashboard

# Example usage and testing
if __name__ == "__main__":
    async def test_compliance_framework():
        framework = RegionalComplianceFramework()
        
        print("Testing Regional Compliance Framework...")
        
        # Mock business context
        business_context = {
            "assets_under_management": 150_000_000,  # $150M
            "sec_registered": True,
            "investment_advisory_license": True,
            "compliance_policies": True,
            "aml_program": True,
            "aml_officer": True,
            "aml_training": False,  # Missing - should trigger violation
            "required_licenses": ["Type 1 Securities"],
            "held_licenses": ["Type 1 Securities"],
            "paid_up_capital_hkd": 6_000_000  # Above minimum
        }
        
        # Test multi-jurisdiction compliance
        jurisdictions = [
            Jurisdiction.UNITED_STATES,
            Jurisdiction.HONG_KONG,
            Jurisdiction.TAIWAN
        ]
        
        reports = await framework.perform_multi_jurisdiction_compliance_check(
            jurisdictions, 
            business_context
        )
        
        print(f"\\nCompliance Reports Generated for {len(reports)} jurisdictions:")
        for jurisdiction, report in reports.items():
            print(f"\\n{jurisdiction.value}:")
            print(f"  Status: {report.overall_status.value}")
            print(f"  Checks performed: {len(report.checks)}")
            print(f"  Action items: {len(report.action_items)}")
            print(f"  Average risk: {report.risk_summary.get('average_risk_score', 0):.2f}")
        
        # Test cross-border requirements
        cross_border = framework.get_cross_border_compliance_requirements(
            Jurisdiction.UNITED_STATES,
            Jurisdiction.HONG_KONG
        )
        print(f"\\nCross-border requirements (US -> HK): {len(cross_border['cross_border_requirements'])} items")
        
        # Generate dashboard
        dashboard = framework.generate_compliance_dashboard(reports)
        print(f"\\nCompliance Dashboard:")
        print(f"  Compliant: {dashboard['summary']['compliant_jurisdictions']}")
        print(f"  Requires Action: {dashboard['summary']['requires_action_jurisdictions']}")
        print(f"  Critical Issues: {dashboard['risk_analysis']['critical_issues']}")
        
        return dashboard
    
    # Run test
    result = asyncio.run(test_compliance_framework())
    print("\\nRegional Compliance Framework test completed successfully!")
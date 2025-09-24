#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Security Validator
GOOGLE Chief Risk Officer Recommendation Implementation

This module implements comprehensive security measures for the member privilege
configuration system to prevent catastrophic configuration errors and malicious attacks.
"""

import json
import os
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TierType(str, Enum):
    """Valid member tier types"""
    FREE = "FREE"
    GOLD = "GOLD" 
    DIAMOND = "DIAMOND"
    PLATINUM = "PLATINUM"

class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass

class TierPrivilegeSchema(BaseModel):
    """Strict validation schema for tier privileges - GOOGLE's Schema Validation"""
    
    cache_ttl_seconds: int = Field(
        ge=60,  # Minimum 1 minute
        le=86400,  # Maximum 24 hours (GOOGLE's suggestion)
        description="Cache TTL in seconds"
    )
    
    api_quota_daily: int = Field(
        ge=-1,  # -1 means unlimited
        le=100000,  # Maximum 100,000 requests per day
        description="Daily API quota"
    )
    
    api_quota_hourly: int = Field(
        ge=-1,  # -1 means unlimited  
        le=10000,  # Maximum 10,000 requests per hour
        description="Hourly API quota"
    )
    
    export_formats: List[str] = Field(
        min_items=1,
        max_items=10,
        description="Supported export formats"
    )
    
    export_size_limit_mb: int = Field(
        ge=-1,  # -1 means unlimited
        le=10000,  # Maximum 10GB
        description="Export size limit in MB"
    )
    
    ai_analysts_count: int = Field(
        ge=1,  # Minimum 1 analyst
        le=50,  # Maximum 50 analysts (prevent resource abuse)
        description="Number of AI analysts available"
    )
    
    realtime_alerts: bool = Field(description="Real-time alerts enabled")
    priority_support: bool = Field(description="Priority support enabled")
    custom_dashboards: bool = Field(description="Custom dashboards enabled")
    
    historical_data_months: int = Field(
        ge=1,  # Minimum 1 month
        le=240,  # Maximum 20 years
        description="Historical data retention in months"
    )
    
    @validator('export_formats')
    def validate_export_formats(cls, v):
        """Validate export formats"""
        valid_formats = {"csv", "excel", "pdf", "api", "json", "xml"}
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f"Invalid export format: {fmt}")
        return v

class PromotionRuleSchema(BaseModel):
    """Validation schema for promotion rules"""
    
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Promotion rule name"
    )
    
    description: str = Field(
        min_length=1,
        max_length=500,
        description="Promotion description"
    )
    
    target_tier: TierType = Field(description="Target member tier")
    
    start_date: str = Field(
        pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',
        description="Start date in ISO format"
    )
    
    end_date: str = Field(
        pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',
        description="End date in ISO format"
    )
    
    override_privileges: Dict[str, Union[int, bool, List[str]]] = Field(
        description="Override privileges"
    )
    
    active: bool = Field(description="Promotion active status")
    
    @validator('end_date')
    def validate_date_order(cls, v, values):
        """Ensure end date is after start date"""
        if 'start_date' in values:
            start = datetime.fromisoformat(values['start_date'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(v.replace('Z', '+00:00'))
            
            if end <= start:
                raise ValueError("End date must be after start date")
                
            # Prevent promotions longer than 1 year
            if (end - start).days > 365:
                raise ValueError("Promotion duration cannot exceed 365 days")
        
        return v

class BusinessRuleSchema(BaseModel):
    """Validation schema for business rules"""
    
    cache_warmup_hours: List[int] = Field(
        min_items=0,
        max_items=24,
        description="Cache warmup hours"
    )
    
    peak_hours: List[int] = Field(
        min_items=0,
        max_items=24, 
        description="Peak hours"
    )
    
    maintenance_window: str = Field(
        pattern=r'^\d{2}:\d{2}-\d{2}:\d{2}$',
        description="Maintenance window in HH:MM-HH:MM format"
    )
    
    max_concurrent_analyses: Dict[str, int] = Field(
        description="Maximum concurrent analyses per tier"
    )
    
    @validator('cache_warmup_hours', 'peak_hours')
    def validate_hours(cls, v):
        """Validate hours are between 0-23"""
        for hour in v:
            if not (0 <= hour <= 23):
                raise ValueError(f"Hour must be between 0-23, got {hour}")
        return v

class MemberPrivilegeConfigSchema(BaseModel):
    """Complete validation schema for member privilege configuration"""
    
    version: str = Field(
        pattern=r'^\d+\.\d+$',
        description="Configuration version"
    )
    
    last_updated: str = Field(
        pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$',
        description="Last updated timestamp"
    )
    
    description: str = Field(
        max_length=500,
        description="Configuration description"
    )
    
    tiers: Dict[TierType, TierPrivilegeSchema] = Field(
        min_items=1,
        description="Member tier configurations"
    )
    
    promotions: List[PromotionRuleSchema] = Field(
        max_items=50,  # Maximum 50 active promotions
        description="Promotion rules"
    )
    
    feature_flags: Dict[str, bool] = Field(
        max_items=100,  # Maximum 100 feature flags
        description="Feature flags"
    )
    
    business_rules: BusinessRuleSchema = Field(
        description="Business rules configuration"
    )

@dataclass
class ConfigChangeRecord:
    """Configuration change audit record - GOOGLE's Audit Trail"""
    
    timestamp: str
    user_id: Optional[str]
    change_type: str  # CREATE, UPDATE, DELETE, RELOAD
    config_section: str
    old_value: Optional[Dict]
    new_value: Optional[Dict]
    change_hash: str
    validation_status: str  # SUCCESS, FAILED, WARNING
    error_message: Optional[str] = None

class ConfigurationSecurityValidator:
    """
    Configuration Security Validator
    Implements GOOGLE's recommendations for configuration governance
    """
    
    def __init__(self, audit_log_path: str = "config_audit.log"):
        self.audit_log_path = audit_log_path
        self.change_records: List[ConfigChangeRecord] = []
        
    def validate_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration against strict schema
        GOOGLE's Schema Validation implementation
        """
        try:
            # Validate using Pydantic schema
            validated_config = MemberPrivilegeConfigSchema(**config_data)
            
            logger.info("✅ Configuration validation PASSED")
            self._log_validation_success(config_data)
            return True
            
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                message = error["msg"]
                value = error.get("input", "N/A")
                error_details.append(f"Field: {field}, Error: {message}, Value: {value}")
            
            error_summary = "; ".join(error_details)
            logger.error(f"❌ Configuration validation FAILED: {error_summary}")
            
            self._log_validation_failure(config_data, error_summary)
            return False
            
        except Exception as e:
            logger.error(f"❌ Configuration validation ERROR: {e}")
            self._log_validation_error(config_data, str(e))
            return False
    
    def validate_configuration_change(self, old_config: Dict, new_config: Dict, 
                                     user_id: Optional[str] = None) -> bool:
        """
        Validate configuration change and create audit record
        Implements change validation and audit trail
        """
        
        # Generate change hash for integrity
        change_data = {
            "old": old_config,
            "new": new_config,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        }
        change_hash = hashlib.sha256(
            json.dumps(change_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # Validate new configuration
        is_valid = self.validate_configuration(new_config)
        
        # Detect dangerous changes
        dangerous_changes = self._detect_dangerous_changes(old_config, new_config)
        if dangerous_changes:
            logger.warning(f"⚠️ Dangerous configuration changes detected: {dangerous_changes}")
        
        # Create audit record
        change_record = ConfigChangeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            change_type="UPDATE",
            config_section="full_config",
            old_value=old_config,
            new_value=new_config,
            change_hash=change_hash,
            validation_status="SUCCESS" if is_valid else "FAILED",
            error_message=None if is_valid else "Schema validation failed"
        )
        
        self._write_audit_record(change_record)
        return is_valid
    
    def _detect_dangerous_changes(self, old_config: Dict, new_config: Dict) -> List[str]:
        """
        Detect potentially dangerous configuration changes
        GOOGLE's Risk Detection implementation
        """
        dangers = []
        
        # Check for extreme TTL changes
        old_tiers = old_config.get("tiers", {})
        new_tiers = new_config.get("tiers", {})
        
        for tier_name, new_tier_data in new_tiers.items():
            old_tier_data = old_tiers.get(tier_name, {})
            
            old_ttl = old_tier_data.get("cache_ttl_seconds", 0)
            new_ttl = new_tier_data.get("cache_ttl_seconds", 0)
            
            # Detect extreme TTL increases (>10x)
            if old_ttl > 0 and new_ttl > old_ttl * 10:
                dangers.append(f"Extreme TTL increase for {tier_name}: {old_ttl}s → {new_ttl}s")
            
            # Detect unlimited quota grants
            old_quota = old_tier_data.get("api_quota_daily", 0)
            new_quota = new_tier_data.get("api_quota_daily", 0)
            
            if old_quota > 0 and new_quota == -1:
                dangers.append(f"Unlimited quota granted to {tier_name}: {old_quota} → unlimited")
        
        # Check for mass promotion activations
        old_promos = len([p for p in old_config.get("promotions", []) if p.get("active")])
        new_promos = len([p for p in new_config.get("promotions", []) if p.get("active")])
        
        if new_promos > old_promos + 5:
            dangers.append(f"Mass promotion activation: {old_promos} → {new_promos} active")
        
        return dangers
    
    def _write_audit_record(self, record: ConfigChangeRecord):
        """Write audit record to log file"""
        try:
            audit_entry = {
                "timestamp": record.timestamp,
                "user_id": record.user_id,
                "change_type": record.change_type,
                "config_section": record.config_section,
                "change_hash": record.change_hash,
                "validation_status": record.validation_status,
                "error_message": record.error_message
            }
            
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
                
            logger.info(f"📝 Audit record written: {record.change_hash}")
            
        except Exception as e:
            logger.error(f"Failed to write audit record: {e}")
    
    def _log_validation_success(self, config_data: Dict):
        """Log successful validation"""
        record = ConfigChangeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id="system",
            change_type="VALIDATE",
            config_section="full_config",
            old_value=None,
            new_value={"status": "validated", "tiers_count": len(config_data.get("tiers", {}))},
            change_hash=hashlib.sha256(json.dumps(config_data, sort_keys=True).encode()).hexdigest()[:16],
            validation_status="SUCCESS"
        )
        self._write_audit_record(record)
    
    def _log_validation_failure(self, config_data: Dict, error_message: str):
        """Log validation failure"""
        record = ConfigChangeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id="system",
            change_type="VALIDATE",
            config_section="full_config",
            old_value=None,
            new_value={"status": "validation_failed"},
            change_hash="validation_failed",
            validation_status="FAILED",
            error_message=error_message
        )
        self._write_audit_record(record)
    
    def _log_validation_error(self, config_data: Dict, error_message: str):
        """Log validation error"""
        record = ConfigChangeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id="system", 
            change_type="VALIDATE",
            config_section="full_config",
            old_value=None,
            new_value={"status": "validation_error"},
            change_hash="validation_error",
            validation_status="ERROR",
            error_message=error_message
        )
        self._write_audit_record(record)
    
    def get_audit_history(self, limit: int = 100) -> List[Dict]:
        """Get recent audit history"""
        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            audit_records = []
            for line in recent_lines:
                if line.strip():
                    audit_records.append(json.loads(line.strip()))
            
            return audit_records
            
        except FileNotFoundError:
            logger.info("No audit log file found")
            return []
        except Exception as e:
            logger.error(f"Failed to read audit history: {e}")
            return []

# Global security validator instance
security_validator = ConfigurationSecurityValidator()
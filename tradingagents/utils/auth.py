#!/usr/bin/env python3
"""
Authentication utilities for TradingAgents
"""

from fastapi import HTTPException, status
from typing import Optional

def get_current_user():
    """Get current authenticated user (mock implementation)"""
    # This is a mock implementation for testing
    # In production, this would validate JWT tokens and return actual user
    class MockUser:
        id = 1
        email = "test@example.com"
        membership_tier = type('Tier', (), {'value': 'FREE'})()
    
    return MockUser()

def verify_admin_user():
    """Verify current user is admin (mock implementation)"""
    # This is a mock implementation for testing
    # In production, this would check actual admin permissions
    class MockAdminUser:
        id = 1
        email = "admin@example.com"
        membership_tier = type('Tier', (), {'value': 'ADMIN'})()
    
    return MockAdminUser()
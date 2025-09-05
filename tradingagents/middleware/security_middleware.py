#!/usr/bin/env python3
"""
安全中間件 (Security Middleware)
TradingAgents 系統 - 企業級安全防護中間件

此模組提供全面的安全防護功能，包含：
1. HTTP安全頭部設置
2. 輸入驗證和清理
3. XSS和CSRF防護
4. 請求限制和防DDoS
5. 安全日誌記錄
6. API安全檢查
"""

import re
import json
import html
import time
import uuid
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from urllib.parse import urlparse, parse_qs

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.logging_config import get_security_logger

# 配置安全日誌
security_logger = get_security_logger("security_middleware")

@dataclass
class SecurityConfig:
    """安全配置"""
    # XSS防護
    enable_xss_protection: bool = True
    xss_filter_mode: str = "strict"  # strict, moderate, basic
    
    # CSRF防護
    enable_csrf_protection: bool = True
    csrf_token_lifetime: int = 3600  # seconds
    
    # 請求限制
    enable_rate_limiting: bool = True
    default_rate_limit: int = 100  # requests per minute
    burst_rate_limit: int = 200
    
    # 輸入驗證
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 10
    max_field_length: int = 10000
    
    # 安全頭部
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000
    csp_policy: Optional[str] = None
    
    # IP白名單/黑名單
    whitelist_ips: Set[str] = None
    blacklist_ips: Set[str] = None
    
    # 安全檢查
    enable_sql_injection_check: bool = True
    enable_path_traversal_check: bool = True
    enable_command_injection_check: bool = True

class XSSProtector:
    """XSS攻擊防護器"""
    
    # 危險的HTML標籤
    DANGEROUS_TAGS = {
        'script', 'iframe', 'object', 'embed', 'applet', 
        'link', 'meta', 'style', 'form', 'input', 'button'
    }
    
    # 危險的屬性
    DANGEROUS_ATTRIBUTES = {
        'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onkeydown',
        'onkeyup', 'onkeypress', 'javascript:', 'vbscript:', 'data:'
    }
    
    # XSS攻擊模式
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'expression\s*\(',
        r'url\s*\(',
        r'<\s*script',
        r'<%.*?%>',
        r'&lt;script',
        r'&lt;iframe',
        r'&#x.*?;',
        r'&#\d+;'
    ]
    
    def __init__(self, mode: str = "strict"):
        self.mode = mode
        self.xss_regex = re.compile('|'.join(self.XSS_PATTERNS), re.IGNORECASE | re.DOTALL)
    
    def detect_xss(self, content: str) -> bool:
        """檢測XSS攻擊"""
        if not content:
            return False
        
        # 檢查XSS模式
        if self.xss_regex.search(content):
            return True
        
        # 檢查編碼的惡意內容
        decoded_content = self._decode_entities(content)
        if self.xss_regex.search(decoded_content):
            return True
        
        return False
    
    def sanitize_input(self, content: str) -> str:
        """清理輸入內容"""
        if not content:
            return content
        
        if self.mode == "strict":
            # 嚴格模式：HTML轉義所有特殊字符
            return html.escape(content, quote=True)
        
        elif self.mode == "moderate":
            # 中等模式：移除危險標籤和屬性
            sanitized = self._remove_dangerous_tags(content)
            sanitized = self._remove_dangerous_attributes(sanitized)
            return sanitized
        
        else:  # basic mode
            # 基本模式：只轉義基本字符
            return content.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    
    def _decode_entities(self, content: str) -> str:
        """解碼HTML實體"""
        import html.parser
        
        try:
            parser = html.parser.HTMLParser()
            return parser.unescape(content)
        except:
            return content
    
    def _remove_dangerous_tags(self, content: str) -> str:
        """移除危險標籤"""
        for tag in self.DANGEROUS_TAGS:
            pattern = f'<{tag}[^>]*>.*?</{tag}>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
            
            # 移除自閉合標籤
            pattern = f'<{tag}[^>]*/?>'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    def _remove_dangerous_attributes(self, content: str) -> str:
        """移除危險屬性"""
        for attr in self.DANGEROUS_ATTRIBUTES:
            pattern = f'{attr}\\s*=\\s*["\'][^"\']*["\']'
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content

class SQLInjectionDetector:
    """SQL注入攻擊檢測器"""
    
    # SQL注入模式
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(\b(UNION|JOIN)\b.*\b(SELECT)\b)',
        r'(--|\#|\/\*|\*\/)',
        r'(\b(OR|AND)\b\s+[\w\'"]+\s*=\s*[\w\'"]+)',
        r'(\bor\b\s+\d+\s*=\s*\d+)',
        r'(\band\b\s+\d+\s*=\s*\d+)',
        r'(\'[\s]*or[\s]*\')',
        r'(\"[\s]*or[\s]*\")',
        r'(\%27|\%22)',
        r'(\bEXEC\b|\bEXECUTE\b)',
        r'(\bSP_\w+)',
        r'(\bXP_\w+)',
        r'(information_schema|sys\.)',
        r'(version\(\)|@@version)',
        r'(load_file\(|into\s+outfile)',
        r'(benchmark\(|sleep\()',
        r'(\bwaitfor\b|\bdelay\b)'
    ]
    
    def __init__(self):
        self.sql_regex = re.compile('|'.join(self.SQL_PATTERNS), re.IGNORECASE)
    
    def detect_sql_injection(self, content: str) -> bool:
        """檢測SQL注入攻擊"""
        if not content:
            return False
        
        return bool(self.sql_regex.search(content))

class RateLimiter:
    """請求限制器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.request_counts: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Dict[str, datetime] = {}
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_ip: str, endpoint: str = "") -> bool:
        """檢查是否允許請求"""
        current_time = time.time()
        
        # 清理過期記錄
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_requests()
        
        # 檢查IP是否被阻止
        if client_ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[client_ip]:
                return False
            else:
                del self.blocked_ips[client_ip]
        
        # 檢查請求頻率
        key = f"{client_ip}:{endpoint}"
        request_times = self.request_counts[key]
        
        # 移除超過1分鐘的記錄
        cutoff_time = current_time - 60
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # 檢查是否超過限制
        if len(request_times) >= self.config.default_rate_limit:
            # 阻止IP 10分鐘
            self.blocked_ips[client_ip] = datetime.now() + timedelta(minutes=10)
            security_logger.warning(f"IP被阻止: {client_ip}, 超過請求限制", extra={
                'client_ip': client_ip,
                'endpoint': endpoint,
                'request_count': len(request_times),
                'security_event': 'rate_limit_exceeded'
            })
            return False
        
        # 記錄當前請求
        request_times.append(current_time)
        return True
    
    def _cleanup_old_requests(self):
        """清理過期請求記錄"""
        current_time = time.time()
        cutoff_time = current_time - 300  # 5分鐘前
        
        keys_to_remove = []
        for key, request_times in self.request_counts.items():
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            if not request_times:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]
        
        self.last_cleanup = current_time

class CSRFProtector:
    """CSRF攻擊防護器"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.tokens: Dict[str, datetime] = {}
    
    def generate_token(self, session_id: str) -> str:
        """生成CSRF token"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = datetime.now() + timedelta(seconds=self.config.csrf_token_lifetime)
        return token
    
    def validate_token(self, token: str) -> bool:
        """驗證CSRF token"""
        if not token or token not in self.tokens:
            return False
        
        if datetime.now() > self.tokens[token]:
            del self.tokens[token]
            return False
        
        return True
    
    def cleanup_expired_tokens(self):
        """清理過期token"""
        current_time = datetime.now()
        expired_tokens = [token for token, expiry in self.tokens.items() if current_time > expiry]
        
        for token in expired_tokens:
            del self.tokens[token]

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中間件"""
    
    def __init__(self, app: ASGIApp, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        
        # 初始化安全組件
        self.xss_protector = XSSProtector(self.config.xss_filter_mode)
        self.sql_detector = SQLInjectionDetector()
        self.rate_limiter = RateLimiter(self.config)
        self.csrf_protector = CSRFProtector(self.config)
        
        # 安全統計
        self.security_stats = {
            'blocked_requests': 0,
            'xss_attempts': 0,
            'sql_injection_attempts': 0,
            'rate_limit_violations': 0,
            'csrf_violations': 0
        }
        
        security_logger.info("安全中間件初始化完成", extra={
            'config': {
                'xss_protection': self.config.enable_xss_protection,
                'csrf_protection': self.config.enable_csrf_protection,
                'rate_limiting': self.config.enable_rate_limiting,
                'sql_injection_check': self.config.enable_sql_injection_check
            }
        })
    
    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        request_id = str(uuid.uuid4())
        
        # 添加請求ID到headers
        request.state.request_id = request_id
        
        try:
            # 安全檢查
            security_result = await self._perform_security_checks(request, client_ip)
            if not security_result['allowed']:
                return self._create_security_response(security_result)
            
            # 處理請求
            response = await call_next(request)
            
            # 添加安全頭部
            if self.config.enable_security_headers:
                self._add_security_headers(response)
            
            # 記錄請求日誌
            self._log_request(request, response, client_ip, time.time() - start_time)
            
            return response
            
        except Exception as e:
            security_logger.error(f"安全中間件錯誤: {str(e)}", extra={
                'request_id': request_id,
                'client_ip': client_ip,
                'path': str(request.url.path)
            })
            
            return JSONResponse(
                status_code=500,
                content={'error': '服務器內部錯誤', 'request_id': request_id}
            )
    
    async def _perform_security_checks(self, request: Request, client_ip: str) -> Dict[str, Any]:
        """執行安全檢查"""
        result = {'allowed': True, 'violations': []}
        
        # IP白名單/黑名單檢查
        if not self._check_ip_access(client_ip):
            result['allowed'] = False
            result['violations'].append('ip_blocked')
            return result
        
        # 請求限制檢查
        if self.config.enable_rate_limiting:
            if not self.rate_limiter.is_allowed(client_ip, request.url.path):
                result['allowed'] = False
                result['violations'].append('rate_limit_exceeded')
                self.security_stats['rate_limit_violations'] += 1
                return result
        
        # 請求大小檢查
        if hasattr(request, 'content_length') and request.content_length:
            if request.content_length > self.config.max_request_size:
                result['allowed'] = False
                result['violations'].append('request_too_large')
                return result
        
        # 獲取請求內容進行檢查
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                if body:
                    await self._check_request_content(body, result)
        except Exception as e:
            security_logger.warning(f"無法讀取請求內容: {str(e)}")
        
        # URL參數檢查
        if request.query_params:
            for key, value in request.query_params.items():
                await self._check_parameter(key, value, result)
        
        return result
    
    async def _check_request_content(self, body: bytes, result: Dict[str, Any]):
        """檢查請求內容"""
        try:
            content = body.decode('utf-8')
            
            # XSS檢查
            if self.config.enable_xss_protection:
                if self.xss_protector.detect_xss(content):
                    result['allowed'] = False
                    result['violations'].append('xss_detected')
                    self.security_stats['xss_attempts'] += 1
            
            # SQL注入檢查
            if self.config.enable_sql_injection_check:
                if self.sql_detector.detect_sql_injection(content):
                    result['allowed'] = False
                    result['violations'].append('sql_injection_detected')
                    self.security_stats['sql_injection_attempts'] += 1
            
            # JSON深度檢查
            if content.strip().startswith('{'):
                try:
                    json_data = json.loads(content)
                    if self._get_json_depth(json_data) > self.config.max_json_depth:
                        result['allowed'] = False
                        result['violations'].append('json_too_deep')
                except json.JSONDecodeError:
                    pass
        
        except UnicodeDecodeError:
            # 非UTF-8內容，可能是攻擊
            result['allowed'] = False
            result['violations'].append('invalid_encoding')
    
    async def _check_parameter(self, key: str, value: str, result: Dict[str, Any]):
        """檢查URL參數"""
        # 長度檢查
        if len(value) > self.config.max_field_length:
            result['allowed'] = False
            result['violations'].append('parameter_too_long')
            return
        
        # XSS檢查
        if self.config.enable_xss_protection:
            if self.xss_protector.detect_xss(value):
                result['allowed'] = False
                result['violations'].append('xss_in_parameter')
                self.security_stats['xss_attempts'] += 1
        
        # SQL注入檢查
        if self.config.enable_sql_injection_check:
            if self.sql_detector.detect_sql_injection(value):
                result['allowed'] = False
                result['violations'].append('sql_injection_in_parameter')
                self.security_stats['sql_injection_attempts'] += 1
        
        # 路徑遍歷檢查
        if self.config.enable_path_traversal_check:
            if '../' in value or '..\' in value or '%2e%2e' in value.lower():
                result['allowed'] = False
                result['violations'].append('path_traversal_detected')
        
        # 命令注入檢查
        if self.config.enable_command_injection_check:
            dangerous_chars = ['|', '&', ';', '$', '`', '$(', '${']
            if any(char in value for char in dangerous_chars):
                result['allowed'] = False
                result['violations'].append('command_injection_detected')
    
    def _check_ip_access(self, client_ip: str) -> bool:
        """檢查IP訪問權限"""
        # 黑名單檢查
        if self.config.blacklist_ips and client_ip in self.config.blacklist_ips:
            return False
        
        # 白名單檢查
        if self.config.whitelist_ips and client_ip not in self.config.whitelist_ips:
            return False
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端IP"""
        # 檢查代理頭部
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else 'unknown'
    
    def _get_json_depth(self, obj, depth=0) -> int:
        """計算JSON深度"""
        if depth > 20:  # 防止無限遞歸
            return depth
        
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth
    
    def _add_security_headers(self, response: Response):
        """添加安全頭部"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), bluetooth=()',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Strict-Transport-Security': f'max-age={self.config.hsts_max_age}; includeSubDomains; preload'
        }
        
        # CSP頭部
        if self.config.csp_policy:
            headers['Content-Security-Policy'] = self.config.csp_policy
        else:
            headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        
        for key, value in headers.items():
            response.headers[key] = value
    
    def _create_security_response(self, security_result: Dict[str, Any]) -> JSONResponse:
        """創建安全響應"""
        self.security_stats['blocked_requests'] += 1
        
        violations = security_result.get('violations', [])
        
        # 記錄安全事件
        security_logger.warning("安全違規請求被阻止", extra={
            'violations': violations,
            'security_event': 'request_blocked'
        })
        
        # 根據違規類型返回不同的響應
        if 'rate_limit_exceeded' in violations:
            return JSONResponse(
                status_code=429,
                content={'error': '請求過於頻繁，請稍後重試'}
            )
        elif 'ip_blocked' in violations:
            return JSONResponse(
                status_code=403,
                content={'error': '訪問被拒絕'}
            )
        elif any(v in violations for v in ['xss_detected', 'sql_injection_detected']):
            return JSONResponse(
                status_code=400,
                content={'error': '請求包含不安全內容'}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={'error': '請求格式不正確'}
            )
    
    def _log_request(self, request: Request, response: Response, client_ip: str, duration: float):
        """記錄請求日誌"""
        log_data = {
            'request_id': getattr(request.state, 'request_id', 'unknown'),
            'client_ip': client_ip,
            'method': request.method,
            'path': str(request.url.path),
            'status_code': response.status_code,
            'duration': round(duration, 3),
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', '')
        }
        
        security_logger.info("HTTP請求", extra=log_data)
    
    def get_security_stats(self) -> Dict[str, Any]:
        """獲取安全統計"""
        return {
            **self.security_stats,
            'active_rate_limits': len(self.rate_limiter.blocked_ips),
            'csrf_tokens': len(self.csrf_protector.tokens)
        }

# 創建默認安全中間件實例
def create_security_middleware(config: SecurityConfig = None) -> SecurityMiddleware:
    """創建安全中間件實例"""
    return SecurityMiddleware(None, config)

# 便利函數用於FastAPI應用
def add_security_middleware(app, config: SecurityConfig = None):
    """為FastAPI應用添加安全中間件"""
    app.add_middleware(SecurityMiddleware, config=config)

if __name__ == "__main__":
    # 測試腳本
    def test_security_components():
        print("測試安全組件...")
        
        # 測試XSS檢測
        xss_protector = XSSProtector()
        test_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "normal text",
            "<b>safe html</b>"
        ]
        
        for test_input in test_inputs:
            is_xss = xss_protector.detect_xss(test_input)
            sanitized = xss_protector.sanitize_input(test_input)
            print(f"輸入: {test_input}")
            print(f"XSS: {is_xss}, 清理後: {sanitized}")
            print()
        
        # 測試SQL注入檢測
        sql_detector = SQLInjectionDetector()
        sql_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "normal query text",
            "user_id = 123"
        ]
        
        for sql_input in sql_inputs:
            is_sql_injection = sql_detector.detect_sql_injection(sql_input)
            print(f"輸入: {sql_input}, SQL注入: {is_sql_injection}")
        
        print("安全組件測試完成")
    
    test_security_components()
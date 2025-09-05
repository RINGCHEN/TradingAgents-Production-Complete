/**
 * 安全性加強器
 * 實施CSRF保護、會話劫持檢測、XSS防護、輸入驗證等安全機制
 */

import { SecureStorage } from '../utils/SecureStorage';
import { TokenManager } from './TokenManager';

interface SecurityConfig {
  enableCSRFProtection: boolean;
  enableSessionHijackingDetection: boolean;
  enableSecurityLogging: boolean;
  enableXSSProtection: boolean;
  enableInputValidation: boolean;
  csrfTokenExpiry: number;
  sessionFingerprintCheck: boolean;
  maxFailedAttempts: number;
  lockoutDuration: number;
  maxInputLength: number;
  allowedDomains: string[];
}

interface SecurityEvent {
  type: 'csrf_violation' | 'session_hijack' | 'failed_auth' | 'suspicious_activity' | 'xss_attempt' | 'sql_injection_attempt' | 'input_validation_failed';
  timestamp: number;
  details: Record<string, any>;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
}

interface SessionFingerprint {
  userAgent: string;
  screenResolution: string;
  timezone: string;
  language: string;
  platform: string;
  hash: string;
}

export class SecurityEnforcer {
  private config: SecurityConfig = {
    enableCSRFProtection: true,
    enableSessionHijackingDetection: true,
    enableSecurityLogging: true,
    enableXSSProtection: true,
    enableInputValidation: true,
    csrfTokenExpiry: 30 * 60 * 1000, // 30分鐘
    sessionFingerprintCheck: true,
    maxFailedAttempts: 5,
    lockoutDuration: 15 * 60 * 1000, // 15分鐘
    maxInputLength: 10000,
    allowedDomains: ['localhost', 'tradingagents.com', 'asia-east1.run.app']
  };
  
  private storage: SecureStorage;
  private tokenManager: TokenManager;
  private securityEvents: SecurityEvent[] = [];
  private failedAttempts = new Map<string, { count: number; lastAttempt: number }>();
  private csrfToken: string | null = null;
  private sessionFingerprint: SessionFingerprint | null = null;
  
  constructor(storage: SecureStorage, tokenManager: TokenManager) {
    this.storage = storage;
    this.tokenManager = tokenManager;
    this.initialize();
  }  

  /**
   * 初始化安全機制
   */
  private async initialize(): Promise<void> {
    if (this.config.enableCSRFProtection) {
      await this.initializeCSRFProtection();
    }
    
    if (this.config.enableSessionHijackingDetection) {
      await this.initializeSessionFingerprinting();
    }
    
    // 定期清理過期的安全事件
    setInterval(() => this.cleanupSecurityEvents(), 60000);
  }
  
  /**
   * 初始化CSRF保護
   */
  private async initializeCSRFProtection(): Promise<void> {
    try {
      // 嘗試從存儲中獲取現有的CSRF token
      const storedToken = await this.storage.getItem('csrf_token');
      const tokenTimestamp = await this.storage.getItem('csrf_token_timestamp');
      
      if (storedToken && tokenTimestamp) {
        const age = Date.now() - parseInt(tokenTimestamp);
        if (age < this.config.csrfTokenExpiry) {
          this.csrfToken = storedToken;
          return;
        }
      }
      
      // 生成新的CSRF token
      await this.generateCSRFToken();
      
    } catch (error) {
      console.warn('CSRF保護初始化失敗:', error);
      this.logSecurityEvent('csrf_violation', 'medium', {
        error: error instanceof Error ? error.message : 'Unknown error',
        action: 'initialization_failed'
      });
    }
  }
  
  /**
   * 生成CSRF token
   */
  private async generateCSRFToken(): Promise<void> {
    const token = this.generateSecureToken();
    const timestamp = Date.now().toString();
    
    await this.storage.setItem('csrf_token', token);
    await this.storage.setItem('csrf_token_timestamp', timestamp);
    
    this.csrfToken = token;
  }
  
  /**
   * 初始化會話指紋識別
   */
  private async initializeSessionFingerprinting(): Promise<void> {
    try {
      const fingerprint = await this.generateSessionFingerprint();
      
      // 檢查是否有存儲的指紋
      const storedFingerprint = await this.storage.getItem('session_fingerprint');
      
      if (storedFingerprint) {
        const stored = JSON.parse(storedFingerprint) as SessionFingerprint;
        
        // 比較指紋，檢測可能的會話劫持
        if (this.config.sessionFingerprintCheck && !this.compareFingerpints(stored, fingerprint)) {
          this.logSecurityEvent('session_hijack', 'high', {
            stored_fingerprint: stored,
            current_fingerprint: fingerprint,
            action: 'fingerprint_mismatch'
          });
          
          // 可能的會話劫持，清除認證狀態
          await this.handleSuspiciousActivity();
          return;
        }
      }
      
      // 存儲當前指紋
      await this.storage.setItem('session_fingerprint', JSON.stringify(fingerprint));
      this.sessionFingerprint = fingerprint;
      
    } catch (error) {
      console.warn('會話指紋識別初始化失敗:', error);
      this.logSecurityEvent('session_hijack', 'medium', {
        error: error instanceof Error ? error.message : 'Unknown error',
        action: 'fingerprint_init_failed'
      });
    }
  }
  
  /**
   * 生成會話指紋
   */
  private async generateSessionFingerprint(): Promise<SessionFingerprint> {
    const userAgent = navigator.userAgent;
    const screenResolution = `${screen.width}x${screen.height}`;
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const language = navigator.language;
    const platform = navigator.platform;
    
    const fingerprintData = {
      userAgent,
      screenResolution,
      timezone,
      language,
      platform
    };
    
    // 生成指紋哈希
    const hash = await this.hashFingerprint(fingerprintData);
    
    return {
      ...fingerprintData,
      hash
    };
  }
  
  /**
   * 生成指紋哈希
   */
  private async hashFingerprint(data: Omit<SessionFingerprint, 'hash'>): Promise<string> {
    const encoder = new TextEncoder();
    const dataString = JSON.stringify(data);
    const dataBuffer = encoder.encode(dataString);
    
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return hashHex;
  }
  
  /**
   * 比較指紋
   */
  private compareFingerpints(stored: SessionFingerprint, current: SessionFingerprint): boolean {
    // 允許某些字段的小幅變化
    const criticalFields = ['userAgent', 'platform', 'timezone'];
    
    for (const field of criticalFields) {
      if (stored[field as keyof SessionFingerprint] !== current[field as keyof SessionFingerprint]) {
        return false;
      }
    }
    
    return true;
  }
  
  /**
   * 獲取CSRF token
   */
  async getCSRFToken(): Promise<string | null> {
    if (!this.config.enableCSRFProtection) {
      return null;
    }
    
    if (!this.csrfToken) {
      await this.generateCSRFToken();
    }
    
    return this.csrfToken;
  }
  
  /**
   * 驗證CSRF token
   */
  async validateCSRFToken(token: string): Promise<boolean> {
    if (!this.config.enableCSRFProtection) {
      return true;
    }
    
    if (!this.csrfToken) {
      this.logSecurityEvent('csrf_violation', 'high', {
        action: 'no_server_token',
        provided_token: token
      });
      return false;
    }
    
    const isValid = token === this.csrfToken;
    
    if (!isValid) {
      this.logSecurityEvent('csrf_violation', 'high', {
        action: 'token_mismatch',
        provided_token: token,
        expected_token: this.csrfToken
      });
    }
    
    return isValid;
  }
  
  /**
   * 記錄失敗的認證嘗試
   */
  recordFailedAuthAttempt(identifier: string): boolean {
    const key = this.hashString(identifier);
    const now = Date.now();
    
    const attempts = this.failedAttempts.get(key) || { count: 0, lastAttempt: 0 };
    
    // 如果距離上次嘗試超過鎖定時間，重置計數
    if (now - attempts.lastAttempt > this.config.lockoutDuration) {
      attempts.count = 0;
    }
    
    attempts.count++;
    attempts.lastAttempt = now;
    
    this.failedAttempts.set(key, attempts);
    
    const isLocked = attempts.count >= this.config.maxFailedAttempts;
    
    this.logSecurityEvent('failed_auth', isLocked ? 'high' : 'medium', {
      identifier: key, // 使用哈希值而不是原始標識符
      attempt_count: attempts.count,
      is_locked: isLocked,
      lockout_until: isLocked ? now + this.config.lockoutDuration : null
    });
    
    return isLocked;
  }
  
  /**
   * 檢查是否被鎖定
   */
  isLocked(identifier: string): boolean {
    const key = this.hashString(identifier);
    const attempts = this.failedAttempts.get(key);
    
    if (!attempts) return false;
    
    const now = Date.now();
    const isLocked = attempts.count >= this.config.maxFailedAttempts &&
                     (now - attempts.lastAttempt) < this.config.lockoutDuration;
    
    return isLocked;
  }
  
  /**
   * 清除失敗嘗試記錄
   */
  clearFailedAttempts(identifier: string): void {
    const key = this.hashString(identifier);
    this.failedAttempts.delete(key);
  }

  /**
   * 驗證輸入內容
   */
  validateInput(input: string, type: 'text' | 'email' | 'url' | 'html' = 'text'): ValidationResult {
    const result: ValidationResult = {
      isValid: true,
      errors: [],
      riskLevel: 'low'
    };

    if (!this.config.enableInputValidation) {
      result.sanitizedValue = input;
      return result;
    }

    // 長度檢查
    if (input.length > this.config.maxInputLength) {
      result.isValid = false;
      result.errors.push(`輸入長度超過限制 (最大: ${this.config.maxInputLength})`);
      result.riskLevel = 'medium';
    }

    // XSS檢查
    if (this.config.enableXSSProtection) {
      const xssResult = this.detectXSS(input);
      if (xssResult.detected) {
        result.isValid = false;
        result.errors.push('檢測到潛在的XSS攻擊');
        result.riskLevel = 'critical';
        
        this.logSecurityEvent('xss_attempt', 'critical', {
          input: input.substring(0, 100),
          patterns: xssResult.matchedPatterns
        });
      }
    }

    // SQL注入檢查
    const sqlResult = this.detectSQLInjection(input);
    if (sqlResult.detected) {
      result.isValid = false;
      result.errors.push('檢測到潛在的SQL注入攻擊');
      result.riskLevel = 'critical';
      
      this.logSecurityEvent('sql_injection_attempt', 'critical', {
        input: input.substring(0, 100),
        patterns: sqlResult.matchedPatterns
      });
    }

    // 根據類型進行特定驗證
    switch (type) {
      case 'email':
        if (!this.validateEmail(input)) {
          result.isValid = false;
          result.errors.push('無效的電子郵件格式');
        }
        break;
      case 'url':
        if (!this.validateURL(input)) {
          result.isValid = false;
          result.errors.push('無效的URL格式');
        }
        break;
      case 'html':
        result.sanitizedValue = this.sanitizeHTML(input);
        break;
      default:
        result.sanitizedValue = this.sanitizeText(input);
    }

    return result;
  }

  /**
   * 檢測XSS攻擊
   */
  private detectXSS(input: string): { detected: boolean; matchedPatterns: string[] } {
    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /javascript:/gi,
      /vbscript:/gi,
      /on\w+\s*=/gi,
      /<iframe[^>]*>/gi,
      /<object[^>]*>/gi,
      /<embed[^>]*>/gi,
      /<link[^>]*>/gi,
      /<meta[^>]*>/gi,
      /expression\s*\(/gi,
      /url\s*\(/gi,
      /&lt;script/gi,
      /&lt;iframe/gi,
      /&#x.*?;/gi,
      /&#\d+;/gi
    ];

    const matchedPatterns: string[] = [];
    
    for (const pattern of xssPatterns) {
      if (pattern.test(input)) {
        matchedPatterns.push(pattern.source);
      }
    }

    return {
      detected: matchedPatterns.length > 0,
      matchedPatterns
    };
  }

  /**
   * 檢測SQL注入攻擊
   */
  private detectSQLInjection(input: string): { detected: boolean; matchedPatterns: string[] } {
    const sqlPatterns = [
      /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)/gi,
      /(\b(UNION|JOIN)\b.*\b(SELECT)\b)/gi,
      /(--|\#|\/\*|\*\/)/gi,
      /(\b(OR|AND)\b\s+[\w'"]+\s*=\s*[\w'"]+)/gi,
      /(\bor\b\s+\d+\s*=\s*\d+)/gi,
      /(\band\b\s+\d+\s*=\s*\d+)/gi,
      /(\'[\s]*or[\s]*\')/gi,
      /(\"[\s]*or[\s]*\")/gi,
      /(\%27|\%22)/gi
    ];

    const matchedPatterns: string[] = [];
    
    for (const pattern of sqlPatterns) {
      if (pattern.test(input)) {
        matchedPatterns.push(pattern.source);
      }
    }

    return {
      detected: matchedPatterns.length > 0,
      matchedPatterns
    };
  }

  /**
   * 清理HTML內容
   */
  sanitizeHTML(html: string): string {
    // 移除危險標籤和屬性
    return html
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '')
      .replace(/<object[^>]*>.*?<\/object>/gi, '')
      .replace(/<embed[^>]*>/gi, '')
      .replace(/<link[^>]*>/gi, '')
      .replace(/<meta[^>]*>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/vbscript:/gi, '')
      .replace(/on\w+\s*=/gi, '')
      .replace(/expression\s*\(/gi, '')
      .trim();
  }

  /**
   * 清理文本內容
   */
  sanitizeText(text: string): string {
    return text
      .replace(/[<>]/g, '')
      .replace(/javascript:/gi, '')
      .replace(/vbscript:/gi, '')
      .trim();
  }

  /**
   * 驗證電子郵件
   */
  private validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * 驗證URL
   */
  private validateURL(url: string): boolean {
    try {
      const urlObj = new URL(url);
      
      // 檢查協議
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return false;
      }

      // 檢查域名是否在允許列表中
      if (this.config.allowedDomains.length > 0) {
        const hostname = urlObj.hostname;
        return this.config.allowedDomains.some(domain => 
          hostname === domain || hostname.endsWith('.' + domain)
        );
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * 創建安全的fetch請求
   */
  async secureFetch(url: string, options: RequestInit = {}): Promise<Response> {
    // 驗證URL
    if (!this.validateURL(url)) {
      throw new Error('不安全的URL');
    }

    // 添加安全頭部
    const secureOptions: RequestInit = {
      ...options,
      headers: {
        ...options.headers,
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache'
      }
    };

    // 添加CSRF token（如果啟用且為狀態改變請求）
    if (this.config.enableCSRFProtection && options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
      const csrfToken = await this.getCSRFToken();
      if (csrfToken) {
        secureOptions.headers = {
          ...secureOptions.headers,
          'X-CSRF-Token': csrfToken
        };
      }
    }

    return fetch(url, secureOptions);
  }
  
  /**
   * 處理可疑活動
   */
  private async handleSuspiciousActivity(): Promise<void> {
    try {
      // 清除認證狀態
      await this.tokenManager.clearTokens();
      
      // 清除會話指紋
      await this.storage.removeItem('session_fingerprint');
      
      // 生成新的CSRF token
      await this.generateCSRFToken();
      
      // 觸發重新認證
      window.dispatchEvent(new CustomEvent('auth:suspicious_activity_detected'));
      
    } catch (error) {
      console.error('處理可疑活動失敗:', error);
    }
  }
  
  /**
   * 記錄安全事件
   */
  private logSecurityEvent(
    type: SecurityEvent['type'],
    severity: SecurityEvent['severity'],
    details: Record<string, any>
  ): void {
    if (!this.config.enableSecurityLogging) return;
    
    const event: SecurityEvent = {
      type,
      severity,
      timestamp: Date.now(),
      details: {
        ...details,
        user_agent: navigator.userAgent,
        url: window.location.href,
        timestamp_iso: new Date().toISOString()
      }
    };
    
    this.securityEvents.push(event);
    
    // 限制事件數量
    if (this.securityEvents.length > 1000) {
      this.securityEvents = this.securityEvents.slice(-500);
    }
    
    // 對於高危事件，立即處理
    if (severity === 'critical' || severity === 'high') {
      console.warn(`安全事件 [${severity.toUpperCase()}]:`, event);
      
      // 可以在這裡添加更多的響應邏輯
      if (type === 'session_hijack') {
        this.handleSuspiciousActivity();
      }
    }
  }
  
  /**
   * 清理過期的安全事件
   */
  private cleanupSecurityEvents(): void {
    const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
    this.securityEvents = this.securityEvents.filter(event => event.timestamp > oneWeekAgo);
  }
  
  /**
   * 生成安全令牌
   */
  private generateSecureToken(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  /**
   * 哈希字符串
   */
  private hashString(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 轉換為32位整數
    }
    return hash.toString(36);
  }
  
  /**
   * 獲取安全統計
   */
  getSecurityStats(): {
    totalEvents: number;
    eventsByType: Record<string, number>;
    eventsBySeverity: Record<string, number>;
    recentEvents: SecurityEvent[];
    failedAttempts: number;
    lockedAccounts: number;
  } {
    const eventsByType: Record<string, number> = {};
    const eventsBySeverity: Record<string, number> = {};
    
    this.securityEvents.forEach(event => {
      eventsByType[event.type] = (eventsByType[event.type] || 0) + 1;
      eventsBySeverity[event.severity] = (eventsBySeverity[event.severity] || 0) + 1;
    });
    
    const recentEvents = this.securityEvents
      .filter(event => Date.now() - event.timestamp < 24 * 60 * 60 * 1000)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 10);
    
    const lockedAccounts = Array.from(this.failedAttempts.values())
      .filter(attempts => attempts.count >= this.config.maxFailedAttempts &&
                         (Date.now() - attempts.lastAttempt) < this.config.lockoutDuration)
      .length;
    
    return {
      totalEvents: this.securityEvents.length,
      eventsByType,
      eventsBySeverity,
      recentEvents,
      failedAttempts: this.failedAttempts.size,
      lockedAccounts
    };
  }
  
  /**
   * 更新安全配置
   */
  updateConfig(newConfig: Partial<SecurityConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
  
  /**
   * 清理資源
   */
  cleanup(): void {
    this.securityEvents.length = 0;
    this.failedAttempts.clear();
    this.csrfToken = null;
    this.sessionFingerprint = null;
  }
}

// 創建全局安全執行器實例
let securityEnforcer: SecurityEnforcer | null = null;

export const createSecurityEnforcer = (
  storage: SecureStorage,
  tokenManager: TokenManager
): SecurityEnforcer => {
  if (!securityEnforcer) {
    securityEnforcer = new SecurityEnforcer(storage, tokenManager);
  }
  return securityEnforcer;
};

export const getSecurityEnforcer = (): SecurityEnforcer | null => {
  return securityEnforcer;
};
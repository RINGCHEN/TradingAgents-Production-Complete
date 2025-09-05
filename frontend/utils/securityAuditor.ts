/**
 * 安全審計系統 - 第二階段Week 4 安全合規強化
 * CSP、HTTPS、OWASP最佳實踐、安全標頭檢查
 * 支援自動化安全檢測、漏洞掃描、合規報告
 */

// 安全檢查類型
export type SecurityCheckType = 
  | 'csp' | 'https' | 'headers' | 'input_validation' | 'authentication'
  | 'authorization' | 'data_protection' | 'xss' | 'csrf' | 'injection';

// 安全級別
export type SecurityLevel = 'low' | 'medium' | 'high' | 'critical';

// 安全檢查結果
export interface SecurityCheckResult {
  id: string;
  type: SecurityCheckType;
  title: string;
  description: string;
  level: SecurityLevel;
  passed: boolean;
  score: number; // 0-100
  details?: Record<string, any>;
  recommendations?: string[];
  references?: string[];
  timestamp: number;
}

// OWASP Top 10 檢查項目
export interface OWASPCheck {
  id: string;
  category: string;
  title: string;
  description: string;
  checkFunction: () => Promise<SecurityCheckResult>;
  priority: number;
}

// CSP 指令類型
export interface CSPDirective {
  name: string;
  values: string[];
  required: boolean;
  description: string;
}

// 安全標頭配置
export interface SecurityHeader {
  name: string;
  expectedValue?: string;
  pattern?: RegExp;
  required: boolean;
  description: string;
}

// 安全審計器類別
class SecurityAuditor {
  private checkResults: SecurityCheckResult[] = [];
  private isRunning = false;
  private observers = new Set<(results: SecurityCheckResult[]) => void>();
  
  // OWASP Top 10 檢查項目
  private owaspChecks: OWASPCheck[] = [
    {
      id: 'broken_access_control',
      category: 'A01:2021',
      title: '破損的存取控制',
      description: '檢查存取控制機制是否正確實施',
      checkFunction: this.checkAccessControl.bind(this),
      priority: 1
    },
    {
      id: 'cryptographic_failures',
      category: 'A02:2021',
      title: '加密失敗',
      description: '檢查資料傳輸和儲存的加密實作',
      checkFunction: this.checkCryptography.bind(this),
      priority: 2
    },
    {
      id: 'injection',
      category: 'A03:2021',
      title: '注入攻擊',
      description: '檢查SQL、NoSQL、OS和LDAP注入漏洞',
      checkFunction: this.checkInjection.bind(this),
      priority: 3
    },
    {
      id: 'insecure_design',
      category: 'A04:2021',
      title: '不安全的設計',
      description: '檢查設計和架構層面的安全風險',
      checkFunction: this.checkInsecureDesign.bind(this),
      priority: 4
    },
    {
      id: 'security_misconfiguration',
      category: 'A05:2021',
      title: '安全設定錯誤',
      description: '檢查安全標頭、CSP、CORS等設定',
      checkFunction: this.checkSecurityConfiguration.bind(this),
      priority: 5
    },
    {
      id: 'vulnerable_components',
      category: 'A06:2021',
      title: '有漏洞的元件',
      description: '檢查第三方套件和依賴項的已知漏洞',
      checkFunction: this.checkVulnerableComponents.bind(this),
      priority: 6
    },
    {
      id: 'identification_failures',
      category: 'A07:2021',
      title: '身份識別和認證失敗',
      description: '檢查認證機制的安全性',
      checkFunction: this.checkAuthentication.bind(this),
      priority: 7
    },
    {
      id: 'integrity_failures',
      category: 'A08:2021',
      title: '軟體和資料完整性失敗',
      description: '檢查CI/CD管道和完整性驗證',
      checkFunction: this.checkIntegrity.bind(this),
      priority: 8
    },
    {
      id: 'logging_failures',
      category: 'A09:2021',
      title: '安全記錄和監控失敗',
      description: '檢查日誌記錄和監控機制',
      checkFunction: this.checkLogging.bind(this),
      priority: 9
    },
    {
      id: 'ssrf',
      category: 'A10:2021',
      title: '伺服器端請求偽造',
      description: '檢查SSRF攻擊防護機制',
      checkFunction: this.checkSSRF.bind(this),
      priority: 10
    }
  ];

  // 必要的安全標頭
  private requiredSecurityHeaders: SecurityHeader[] = [
    {
      name: 'Strict-Transport-Security',
      expectedValue: 'max-age=31536000; includeSubDomains',
      required: true,
      description: 'HSTS強制使用HTTPS連線'
    },
    {
      name: 'Content-Security-Policy',
      pattern: /^default-src/,
      required: true,
      description: 'CSP防止XSS和代碼注入攻擊'
    },
    {
      name: 'X-Frame-Options',
      expectedValue: 'DENY',
      required: true,
      description: '防止點擊劫持攻擊'
    },
    {
      name: 'X-Content-Type-Options',
      expectedValue: 'nosniff',
      required: true,
      description: '防止MIME類型混淆攻擊'
    },
    {
      name: 'Referrer-Policy',
      expectedValue: 'strict-origin-when-cross-origin',
      required: true,
      description: '控制Referrer標頭的傳送'
    },
    {
      name: 'Permissions-Policy',
      pattern: /^(geolocation|microphone|camera)=\(\)/,
      required: false,
      description: '控制瀏覽器功能權限'
    }
  ];

  constructor() {
    this.initializeSecurityChecks();
  }

  // 初始化安全檢查
  private initializeSecurityChecks() {
    // 設置CSP違規報告監聽
    if ('ReportingObserver' in window) {
      const observer = new ReportingObserver((reports) => {
        for (const report of reports) {
          if (report.type === 'csp-violation') {
            this.handleCSPViolation(report);
          }
        }
      });
      observer.observe();
    }

    // 監聽安全相關的控制台錯誤
    const originalConsoleError = console.error;
    console.error = (...args) => {
      this.analyzeConsoleError(args);
      originalConsoleError.apply(console, args);
    };
  }

  // 執行完整安全審計
  async runFullAudit(): Promise<SecurityCheckResult[]> {
    if (this.isRunning) {
      throw new Error('Security audit is already running');
    }

    this.isRunning = true;
    this.checkResults = [];

    try {
      console.log('[SecurityAuditor] Starting comprehensive security audit...');

      // 並行執行所有OWASP檢查
      const owaspPromises = this.owaspChecks
        .sort((a, b) => a.priority - b.priority)
        .map(check => this.executeCheck(check));

      const owaspResults = await Promise.allSettled(owaspPromises);

      // 處理檢查結果
      owaspResults.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          this.checkResults.push(result.value);
        } else {
          console.error(`[SecurityAuditor] Check failed: ${this.owaspChecks[index].id}`, result.reason);
          this.checkResults.push({
            id: this.owaspChecks[index].id,
            type: 'headers',
            title: this.owaspChecks[index].title,
            description: '檢查執行失敗',
            level: 'medium',
            passed: false,
            score: 0,
            details: { error: result.reason?.toString() },
            timestamp: Date.now()
          });
        }
      });

      // 額外的前端特定檢查
      await this.runFrontendSpecificChecks();

      // 計算整體安全評分
      const overallScore = this.calculateOverallScore();
      console.log(`[SecurityAuditor] Security audit completed. Overall score: ${overallScore}/100`);

      // 通知觀察者
      this.notifyObservers();

      return [...this.checkResults];

    } finally {
      this.isRunning = false;
    }
  }

  // 執行單項檢查
  private async executeCheck(check: OWASPCheck): Promise<SecurityCheckResult> {
    try {
      console.log(`[SecurityAuditor] Running check: ${check.title}`);
      const result = await check.checkFunction();
      console.log(`[SecurityAuditor] Check completed: ${check.title} - ${result.passed ? 'PASS' : 'FAIL'}`);
      return result;
    } catch (error) {
      console.error(`[SecurityAuditor] Check error: ${check.title}`, error);
      throw error;
    }
  }

  // A01: 破損的存取控制檢查
  private async checkAccessControl(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查是否有未授權的API端點訪問
    try {
      const unauthorizedEndpoints = [
        '/api/admin/',
        '/api/users/all',
        '/api/internal/'
      ];

      for (const endpoint of unauthorizedEndpoints) {
        try {
          const response = await fetch(endpoint, { method: 'GET' });
          if (response.ok) {
            issues.push(`未授權端點可訪問: ${endpoint}`);
            score -= 30;
          }
        } catch (error) {
          // 預期的錯誤，表示端點受到保護
        }
      }
    } catch (error) {
      issues.push('存取控制檢查失敗');
      score -= 20;
    }

    // 檢查本地存儲中是否有敏感資料
    const sensitiveKeys = ['password', 'token', 'secret', 'key'];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)!;
      if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
        const value = localStorage.getItem(key);
        if (value && value.length > 10) {
          issues.push(`localStorage中發現可能的敏感資料: ${key}`);
          score -= 15;
        }
      }
    }

    return {
      id: 'access_control_check',
      type: 'authorization',
      title: '存取控制檢查',
      description: '檢查存取控制機制是否正確實施',
      level: issues.length > 0 ? 'high' : 'low',
      passed: issues.length === 0,
      score: Math.max(0, score),
      details: { issues },
      recommendations: issues.length > 0 ? [
        '實施適當的存取控制機制',
        '避免在客戶端存儲敏感資料',
        '使用安全的認證和授權系統'
      ] : [],
      references: [
        'https://owasp.org/Top10/A01_2021-Broken_Access_Control/'
      ],
      timestamp: Date.now()
    };
  }

  // A02: 加密失敗檢查
  private async checkCryptography(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查HTTPS使用
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
      issues.push('網站未使用HTTPS協議');
      score -= 40;
    }

    // 檢查混合內容
    const images = document.querySelectorAll('img');
    const scripts = document.querySelectorAll('script');
    const links = document.querySelectorAll('link');

    [...images, ...scripts, ...links].forEach((element: Element) => {
      const src = element.getAttribute('src') || element.getAttribute('href');
      if (src && src.startsWith('http://') && location.protocol === 'https:') {
        issues.push(`發現混合內容: ${src.substring(0, 50)}...`);
        score -= 10;
      }
    });

    // 檢查加密相關的localStorage數據
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)!;
      const value = localStorage.getItem(key);
      
      if (value) {
        // 檢查是否看起來像未加密的敏感數據
        if (this.looksLikeSensitiveData(value) && !this.looksEncrypted(value)) {
          issues.push(`可能的未加密敏感數據: ${key}`);
          score -= 15;
        }
      }
    }

    return {
      id: 'cryptography_check',
      type: 'data_protection',
      title: '加密實作檢查',
      description: '檢查資料傳輸和儲存的加密實作',
      level: score < 70 ? 'high' : score < 90 ? 'medium' : 'low',
      passed: score >= 90,
      score: Math.max(0, score),
      details: { issues, protocol: location.protocol },
      recommendations: issues.length > 0 ? [
        '確保所有資料傳輸使用HTTPS',
        '避免混合內容（HTTP資源在HTTPS頁面中）',
        '對敏感資料進行適當加密後再存儲'
      ] : [],
      references: [
        'https://owasp.org/Top10/A02_2021-Cryptographic_Failures/'
      ],
      timestamp: Date.now()
    };
  }

  // A03: 注入攻擊檢查
  private async checkInjection(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查DOM中是否有可能的XSS漏洞
    const userInputElements = document.querySelectorAll('input, textarea, [contenteditable]');
    
    userInputElements.forEach((element: Element, index) => {
      const tagName = element.tagName.toLowerCase();
      const type = element.getAttribute('type');
      
      // 檢查是否有適當的輸入驗證屬性
      if (!element.hasAttribute('maxlength') && (tagName === 'input' || tagName === 'textarea')) {
        issues.push(`輸入欄位${index + 1}缺少長度限制`);
        score -= 5;
      }

      // 檢查dangerous innerHTML使用
      if ((element as any).innerHTML && this.containsSuspiciousContent((element as any).innerHTML)) {
        issues.push(`發現可疑的HTML內容在元素${index + 1}`);
        score -= 20;
      }
    });

    // 檢查是否有eval或Function的使用
    const scriptElements = document.querySelectorAll('script');
    scriptElements.forEach((script, index) => {
      if (script.textContent) {
        if (script.textContent.includes('eval(') || script.textContent.includes('Function(')) {
          issues.push(`腳本${index + 1}中發現eval或Function使用`);
          score -= 25;
        }
      }
    });

    // 檢查URL參數是否直接用於DOM操作
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.toString() && document.body.innerHTML.includes(urlParams.toString())) {
      issues.push('URL參數可能直接插入到DOM中');
      score -= 30;
    }

    return {
      id: 'injection_check',
      type: 'injection',
      title: '注入攻擊防護檢查',
      description: '檢查XSS、SQL injection等注入攻擊的防護',
      level: score < 60 ? 'critical' : score < 80 ? 'high' : 'medium',
      passed: score >= 80,
      score: Math.max(0, score),
      details: { 
        issues,
        inputElementsCount: userInputElements.length,
        scriptElementsCount: scriptElements.length
      },
      recommendations: issues.length > 0 ? [
        '對所有用戶輸入進行適當的驗證和清理',
        '使用參數化查詢防止SQL注入',
        '避免使用eval和動態代碼執行',
        '實施內容安全策略(CSP)防止XSS'
      ] : [],
      references: [
        'https://owasp.org/Top10/A03_2021-Injection/'
      ],
      timestamp: Date.now()
    };
  }

  // A04: 不安全的設計檢查
  private async checkInsecureDesign(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查是否有適當的錯誤處理
    const hasGlobalErrorHandler = window.onerror !== null || 
                                  window.addEventListener && 
                                  window.addEventListener.toString().includes('error');
    
    if (!hasGlobalErrorHandler) {
      issues.push('缺少全域錯誤處理機制');
      score -= 15;
    }

    // 檢查是否有速率限制指示
    const forms = document.querySelectorAll('form');
    let hasRateLimitingIndication = false;
    
    forms.forEach((form) => {
      const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitButton && (submitButton.hasAttribute('disabled') || 
                          submitButton.classList.contains('loading'))) {
        hasRateLimitingIndication = true;
      }
    });

    if (forms.length > 0 && !hasRateLimitingIndication) {
      issues.push('表單可能缺少適當的提交速率控制');
      score -= 10;
    }

    // 檢查是否有適當的會話管理
    const hasSessionManagement = document.cookie.includes('session') || 
                                 localStorage.getItem('session') || 
                                 sessionStorage.getItem('session');

    if (!hasSessionManagement && this.hasAuthenticationFeatures()) {
      issues.push('認證功能存在但缺少適當的會話管理');
      score -= 20;
    }

    // 檢查是否有安全的預設設定
    if (this.hasInsecureDefaults()) {
      issues.push('發現不安全的預設設定');
      score -= 15;
    }

    return {
      id: 'insecure_design_check',
      type: 'authentication',
      title: '安全設計檢查',
      description: '檢查設計和架構層面的安全風險',
      level: score < 70 ? 'high' : 'medium',
      passed: score >= 80,
      score: Math.max(0, score),
      details: { 
        issues,
        hasGlobalErrorHandler,
        formsCount: forms.length,
        hasSessionManagement
      },
      recommendations: issues.length > 0 ? [
        '實施全域錯誤處理和日誌記錄',
        '在所有表單中實施適當的速率限制',
        '建立安全的會話管理機制',
        '確保安全的預設設定'
      ] : [],
      references: [
        'https://owasp.org/Top10/A04_2021-Insecure_Design/'
      ],
      timestamp: Date.now()
    };
  }

  // A05: 安全設定錯誤檢查
  private async checkSecurityConfiguration(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查安全標頭
    const headerResults = await this.checkSecurityHeaders();
    issues.push(...headerResults.issues);
    score -= (100 - headerResults.score) * 0.5;

    // 檢查CSP設定
    const cspResult = await this.checkCSP();
    issues.push(...cspResult.issues);
    score -= (100 - cspResult.score) * 0.3;

    // 檢查CORS設定（如果可檢測）
    if (this.hasCORSIssues()) {
      issues.push('發現CORS設定問題');
      score -= 10;
    }

    // 檢查調試訊息
    if (this.hasDebugInformation()) {
      issues.push('頁面中發現調試訊息');
      score -= 15;
    }

    return {
      id: 'security_configuration_check',
      type: 'headers',
      title: '安全設定檢查',
      description: '檢查安全標頭、CSP、CORS等設定',
      level: score < 70 ? 'high' : score < 85 ? 'medium' : 'low',
      passed: score >= 85,
      score: Math.max(0, score),
      details: { issues },
      recommendations: issues.length > 0 ? [
        '設定適當的安全標頭',
        '實施嚴格的內容安全策略',
        '正確配置CORS策略',
        '移除生產環境中的調試訊息'
      ] : [],
      references: [
        'https://owasp.org/Top10/A05_2021-Security_Misconfiguration/'
      ],
      timestamp: Date.now()
    };
  }

  // A06: 有漏洞的元件檢查
  private async checkVulnerableComponents(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查已知的有漏洞的JavaScript庫
    const vulnerableLibraries = [
      { name: 'jquery', versions: ['< 3.5.0'], pattern: /jquery[.\-](\d+\.\d+\.\d+)/ },
      { name: 'lodash', versions: ['< 4.17.19'], pattern: /lodash[.\-](\d+\.\d+\.\d+)/ },
      { name: 'moment', versions: ['< 2.29.0'], pattern: /moment[.\-](\d+\.\d+\.\d+)/ }
    ];

    const scripts = document.querySelectorAll('script[src]');
    scripts.forEach((script: Element) => {
      const src = script.getAttribute('src')!;
      
      vulnerableLibraries.forEach(lib => {
        const match = src.match(lib.pattern);
        if (match) {
          const version = match[1];
          // 簡化的版本檢查（實際應用中需要更複雜的版本比較）
          if (this.isVulnerableVersion(version, lib.versions[0])) {
            issues.push(`發現有漏洞的${lib.name}版本: ${version}`);
            score -= 20;
          }
        }
      });
    });

    // 檢查是否使用了不安全的第三方CDN
    const insecureCDNs = ['http://'];
    scripts.forEach((script: Element) => {
      const src = script.getAttribute('src');
      if (src && insecureCDNs.some(cdn => src.startsWith(cdn))) {
        issues.push(`使用不安全的CDN: ${src}`);
        score -= 15;
      }
    });

    return {
      id: 'vulnerable_components_check',
      type: 'headers',
      title: '有漏洞元件檢查',
      description: '檢查第三方套件和依賴項的已知漏洞',
      level: score < 70 ? 'high' : 'medium',
      passed: score >= 85,
      score: Math.max(0, score),
      details: { 
        issues,
        scriptsChecked: scripts.length
      },
      recommendations: issues.length > 0 ? [
        '更新所有第三方庫到最新安全版本',
        '使用安全的CDN並驗證完整性',
        '定期進行依賴項安全掃描'
      ] : [],
      references: [
        'https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/'
      ],
      timestamp: Date.now()
    };
  }

  // A07: 身份識別和認證失敗檢查
  private async checkAuthentication(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查密碼欄位安全性
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach((field: Element, index) => {
      // 檢查自動完成設定
      if (!field.hasAttribute('autocomplete')) {
        issues.push(`密碼欄位${index + 1}缺少autocomplete屬性`);
        score -= 10;
      }

      // 檢查是否在HTTPS下
      if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
        issues.push(`密碼欄位${index + 1}未在HTTPS下使用`);
        score -= 30;
      }
    });

    // 檢查是否有記住密碼的不安全實作
    const rememberCheckboxes = document.querySelectorAll('input[type="checkbox"]');
    rememberCheckboxes.forEach((checkbox: Element) => {
      const label = checkbox.nextElementSibling || checkbox.parentElement;
      if (label && label.textContent && 
          (label.textContent.includes('記住') || label.textContent.includes('remember'))) {
        // 檢查是否有適當的安全警告
        const warningText = document.body.textContent;
        if (!warningText?.includes('安全') && !warningText?.includes('security')) {
          issues.push('記住密碼功能缺少安全警告');
          score -= 15;
        }
      }
    });

    // 檢查會話令牌
    const cookies = document.cookie.split(';');
    let hasSecureSessionCookie = false;
    
    cookies.forEach(cookie => {
      if (cookie.includes('session') || cookie.includes('auth')) {
        if (cookie.includes('Secure') && cookie.includes('HttpOnly')) {
          hasSecureSessionCookie = true;
        }
      }
    });

    if (passwordFields.length > 0 && !hasSecureSessionCookie) {
      issues.push('認證系統缺少安全的會話cookie設定');
      score -= 20;
    }

    return {
      id: 'authentication_check',
      type: 'authentication',
      title: '認證機制檢查',
      description: '檢查認證機制的安全性',
      level: score < 60 ? 'critical' : score < 80 ? 'high' : 'medium',
      passed: score >= 80,
      score: Math.max(0, score),
      details: { 
        issues,
        passwordFieldsCount: passwordFields.length,
        hasSecureSessionCookie
      },
      recommendations: issues.length > 0 ? [
        '確保所有認證操作在HTTPS下進行',
        '實施強密碼政策',
        '使用安全的會話管理',
        '添加多因素認證支援'
      ] : [],
      references: [
        'https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/'
      ],
      timestamp: Date.now()
    };
  }

  // A08: 軟體和資料完整性失敗檢查
  private async checkIntegrity(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查外部資源的完整性驗證
    const externalScripts = document.querySelectorAll('script[src^="http"]');
    const externalLinks = document.querySelectorAll('link[href^="http"]');

    [...externalScripts, ...externalLinks].forEach((element: Element, index) => {
      if (!element.hasAttribute('integrity')) {
        const src = element.getAttribute('src') || element.getAttribute('href');
        issues.push(`外部資源${index + 1}缺少完整性檢查: ${src?.substring(0, 50)}...`);
        score -= 10;
      }
    });

    // 檢查是否有不安全的動態腳本載入
    if (this.hasDynamicScriptLoading()) {
      issues.push('發現動態腳本載入，可能存在完整性風險');
      score -= 20;
    }

    // 檢查Service Worker的更新機制
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration && !registration.update) {
        issues.push('Service Worker缺少適當的更新機制');
        score -= 15;
      }
    }

    return {
      id: 'integrity_check',
      type: 'data_protection',
      title: '軟體和資料完整性檢查',
      description: '檢查CI/CD管道和完整性驗證',
      level: score < 70 ? 'high' : 'medium',
      passed: score >= 80,
      score: Math.max(0, score),
      details: { 
        issues,
        externalResourcesCount: externalScripts.length + externalLinks.length
      },
      recommendations: issues.length > 0 ? [
        '為所有外部資源添加integrity屬性',
        '實施子資源完整性(SRI)',
        '建立安全的軟體更新機制',
        '驗證第三方組件的完整性'
      ] : [],
      references: [
        'https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/'
      ],
      timestamp: Date.now()
    };
  }

  // A09: 安全記錄和監控失敗檢查
  private async checkLogging(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查是否有錯誤日誌記錄
    const hasErrorLogging = window.onerror !== null || 
                           (window as any).__errorHandlers?.length > 0 ||
                           localStorage.getItem('error-log');

    if (!hasErrorLogging) {
      issues.push('缺少錯誤日誌記錄機制');
      score -= 25;
    }

    // 檢查是否有用戶行為監控
    const hasUserTracking = (window as any).gtag || 
                            (window as any).ga || 
                            (window as any)._paq ||
                            localStorage.getItem('user-actions');

    if (!hasUserTracking && this.hasAuthenticationFeatures()) {
      issues.push('認證系統缺少用戶行為監控');
      score -= 20;
    }

    // 檢查是否有安全事件記錄
    const hasSecurityLogging = localStorage.getItem('security-events') ||
                               sessionStorage.getItem('security-events');

    if (!hasSecurityLogging) {
      issues.push('缺少安全事件記錄機制');
      score -= 20;
    }

    // 檢查日誌是否包含敏感信息
    const logs = [
      localStorage.getItem('error-log'),
      localStorage.getItem('debug-log'),
      sessionStorage.getItem('debug-info')
    ].filter(Boolean);

    logs.forEach((log, index) => {
      if (log && this.containsSensitiveInformation(log)) {
        issues.push(`日誌${index + 1}中可能包含敏感信息`);
        score -= 15;
      }
    });

    return {
      id: 'logging_check',
      type: 'headers',
      title: '安全記錄和監控檢查',
      description: '檢查日誌記錄和監控機制',
      level: score < 60 ? 'high' : score < 80 ? 'medium' : 'low',
      passed: score >= 80,
      score: Math.max(0, score),
      details: { 
        issues,
        hasErrorLogging,
        hasUserTracking,
        hasSecurityLogging
      },
      recommendations: issues.length > 0 ? [
        '實施完整的錯誤日誌記錄',
        '建立用戶行為監控機制',
        '記錄所有安全相關事件',
        '確保日誌不包含敏感信息'
      ] : [],
      references: [
        'https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/'
      ],
      timestamp: Date.now()
    };
  }

  // A10: 伺服器端請求偽造檢查
  private async checkSSRF(): Promise<SecurityCheckResult> {
    const issues: string[] = [];
    let score = 100;

    // 檢查是否有用戶可控制的URL請求
    const urlInputs = document.querySelectorAll('input[type="url"], input[name*="url"], input[placeholder*="url"]');
    
    if (urlInputs.length > 0) {
      issues.push(`發現${urlInputs.length}個URL輸入欄位，需要SSRF防護`);
      score -= 30;
    }

    // 檢查fetch或XMLHttpRequest的使用
    const scripts = document.querySelectorAll('script');
    let hasDynamicRequests = false;
    
    scripts.forEach((script) => {
      if (script.textContent) {
        if (script.textContent.includes('fetch(') || 
            script.textContent.includes('XMLHttpRequest') ||
            script.textContent.includes('axios.get')) {
          hasDynamicRequests = true;
        }
      }
    });

    if (hasDynamicRequests && !this.hasSSRFProtection()) {
      issues.push('發現動態請求但缺少SSRF防護');
      score -= 20;
    }

    // 檢查是否有iframe或embed標籤
    const embeddedContent = document.querySelectorAll('iframe, embed, object');
    embeddedContent.forEach((element: Element, index) => {
      const src = element.getAttribute('src') || element.getAttribute('data');
      if (src && !this.isWhitelistedDomain(src)) {
        issues.push(`嵌入內容${index + 1}可能存在SSRF風險: ${src.substring(0, 50)}...`);
        score -= 15;
      }
    });

    return {
      id: 'ssrf_check',
      type: 'injection',
      title: 'SSRF攻擊防護檢查',
      description: '檢查SSRF攻擊防護機制',
      level: score < 70 ? 'high' : 'medium',
      passed: score >= 85,
      score: Math.max(0, score),
      details: { 
        issues,
        urlInputsCount: urlInputs.length,
        embeddedContentCount: embeddedContent.length,
        hasDynamicRequests
      },
      recommendations: issues.length > 0 ? [
        '實施URL白名單驗證',
        '避免直接使用用戶輸入的URL',
        '使用代理服務器進行外部請求',
        '限制內部網路訪問'
      ] : [],
      references: [
        'https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_SSRF/'
      ],
      timestamp: Date.now()
    };
  }

  // 檢查安全標頭
  private async checkSecurityHeaders(): Promise<{ score: number; issues: string[] }> {
    const issues: string[] = [];
    let score = 100;

    // 模擬檢查（實際需要伺服器端支援）
    try {
      const response = await fetch(window.location.href, { method: 'HEAD' });
      
      this.requiredSecurityHeaders.forEach(header => {
        const headerValue = response.headers.get(header.name);
        
        if (!headerValue) {
          if (header.required) {
            issues.push(`缺少必要的安全標頭: ${header.name}`);
            score -= 15;
          }
        } else {
          // 驗證標頭值
          if (header.expectedValue && headerValue !== header.expectedValue) {
            issues.push(`安全標頭值不正確: ${header.name}`);
            score -= 10;
          } else if (header.pattern && !header.pattern.test(headerValue)) {
            issues.push(`安全標頭格式不正確: ${header.name}`);
            score -= 10;
          }
        }
      });
      
    } catch (error) {
      issues.push('無法檢查安全標頭');
      score -= 20;
    }

    return { score: Math.max(0, score), issues };
  }

  // 檢查CSP
  private async checkCSP(): Promise<{ score: number; issues: string[] }> {
    const issues: string[] = [];
    let score = 100;

    // 檢查meta標籤中的CSP
    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    let cspContent = '';

    if (cspMeta) {
      cspContent = cspMeta.getAttribute('content') || '';
    }

    if (!cspContent) {
      issues.push('缺少Content Security Policy');
      score -= 40;
    } else {
      // 檢查CSP指令
      const requiredDirectives = [
        'default-src',
        'script-src',
        'style-src',
        'img-src'
      ];

      requiredDirectives.forEach(directive => {
        if (!cspContent.includes(directive)) {
          issues.push(`CSP缺少${directive}指令`);
          score -= 10;
        }
      });

      // 檢查不安全的CSP設定
      if (cspContent.includes("'unsafe-eval'")) {
        issues.push("CSP包含不安全的'unsafe-eval'指令");
        score -= 15;
      }

      if (cspContent.includes("'unsafe-inline'")) {
        issues.push("CSP包含不安全的'unsafe-inline'指令");
        score -= 15;
      }

      if (cspContent.includes('*')) {
        issues.push('CSP使用了過於寬鬆的通配符');
        score -= 10;
      }
    }

    return { score: Math.max(0, score), issues };
  }

  // 執行前端特定檢查
  private async runFrontendSpecificChecks() {
    // 檢查Console警告
    this.checkConsoleWarnings();
    
    // 檢查開發者工具檢測
    this.checkDevToolsDetection();
    
    // 檢查右鍵禁用（不推薦的安全措施）
    this.checkRightClickDisabling();
  }

  // 檢查Console警告
  private checkConsoleWarnings() {
    // 添加控制台警告檢查結果
    this.checkResults.push({
      id: 'console_warnings_check',
      type: 'headers',
      title: '控制台安全警告',
      description: '檢查是否有適當的控制台安全警告',
      level: 'low',
      passed: true,
      score: 85,
      details: { hasWarning: true },
      recommendations: [
        '在控制台顯示安全警告，提醒用戶不要執行可疑代碼'
      ],
      timestamp: Date.now()
    });
  }

  // 檢查開發者工具檢測
  private checkDevToolsDetection() {
    const hasDevToolsDetection = (window as any).__devtools || 
                                 document.addEventListener.toString().includes('devtools');
    
    this.checkResults.push({
      id: 'devtools_detection_check',
      type: 'headers',
      title: '開發者工具檢測',
      description: '檢查是否有開發者工具檢測機制',
      level: 'low',
      passed: hasDevToolsDetection,
      score: hasDevToolsDetection ? 90 : 70,
      details: { hasDetection: hasDevToolsDetection },
      recommendations: hasDevToolsDetection ? [] : [
        '考慮實施開發者工具檢測機制（可選）'
      ],
      timestamp: Date.now()
    });
  }

  // 檢查右鍵禁用
  private checkRightClickDisabling() {
    const hasRightClickDisable = document.oncontextmenu === null ||
                                 document.body.oncontextmenu === null;
    
    this.checkResults.push({
      id: 'right_click_disable_check',
      type: 'headers',
      title: '右鍵功能檢查',
      description: '檢查是否禁用了右鍵功能（不推薦）',
      level: 'low',
      passed: !hasRightClickDisable,
      score: hasRightClickDisable ? 60 : 95,
      details: { isDisabled: hasRightClickDisable },
      recommendations: hasRightClickDisable ? [
        '不建議禁用右鍵功能，這不能提供真正的安全保護',
        '關注真正的安全措施，如輸入驗證和授權控制'
      ] : [],
      timestamp: Date.now()
    });
  }

  // 輔助方法
  private looksLikeSensitiveData(data: string): boolean {
    const sensitivePatterns = [
      /password/i,
      /token/i,
      /key/i,
      /secret/i,
      /auth/i,
      /\d{16,19}/, // 信用卡號
      /\d{3}-\d{2}-\d{4}/, // SSN格式
      /[A-Za-z0-9+/]{40,}/ // 可能的hash或token
    ];
    
    return sensitivePatterns.some(pattern => pattern.test(data));
  }

  private looksEncrypted(data: string): boolean {
    // 簡單的加密檢測：高熵值、Base64格式等
    const entropy = this.calculateEntropy(data);
    const isBase64Like = /^[A-Za-z0-9+/]+=*$/.test(data) && data.length % 4 === 0;
    const hasRandomPattern = !/(.)\1{3,}/.test(data); // 沒有連續重複字符
    
    return entropy > 4.5 && (isBase64Like || hasRandomPattern);
  }

  private calculateEntropy(str: string): number {
    const freq = new Map<string, number>();
    for (const char of str) {
      freq.set(char, (freq.get(char) || 0) + 1);
    }
    
    let entropy = 0;
    const length = str.length;
    
    for (const count of freq.values()) {
      const p = count / length;
      entropy -= p * Math.log2(p);
    }
    
    return entropy;
  }

  private containsSuspiciousContent(html: string): boolean {
    const suspiciousPatterns = [
      /<script[^>]*>.*<\/script>/i,
      /javascript:/i,
      /on\w+\s*=/i, // 事件處理器
      /eval\s*\(/i,
      /document\.write/i
    ];
    
    return suspiciousPatterns.some(pattern => pattern.test(html));
  }

  private hasAuthenticationFeatures(): boolean {
    return document.querySelectorAll('input[type="password"]').length > 0 ||
           document.body.textContent?.includes('登入') ||
           document.body.textContent?.includes('login') ||
           false;
  }

  private hasInsecureDefaults(): boolean {
    // 檢查一些常見的不安全預設設定
    const forms = document.querySelectorAll('form');
    return Array.from(forms).some(form => 
      form.getAttribute('autocomplete') === 'on' && 
      form.querySelector('input[type="password"]')
    );
  }

  private hasCORSIssues(): boolean {
    // 簡化的CORS檢查
    return false; // 需要實際的伺服器端檢測
  }

  private hasDebugInformation(): boolean {
    const debugPatterns = [
      /console\.(log|debug|info)/,
      /DEBUG/,
      /development/i,
      /stacktrace/i
    ];
    
    const scripts = document.querySelectorAll('script');
    return Array.from(scripts).some(script => 
      script.textContent && 
      debugPatterns.some(pattern => pattern.test(script.textContent!))
    );
  }

  private isVulnerableVersion(current: string, minimum: string): boolean {
    // 簡化的版本比較（實際應用中需要更複雜的邏輯）
    const parseVersion = (v: string) => v.replace(/[^\d.]/g, '').split('.').map(Number);
    const currentParts = parseVersion(current);
    const minimumParts = parseVersion(minimum.replace('< ', ''));
    
    for (let i = 0; i < Math.max(currentParts.length, minimumParts.length); i++) {
      const currentPart = currentParts[i] || 0;
      const minimumPart = minimumParts[i] || 0;
      
      if (currentPart < minimumPart) {
        return true;
      } else if (currentPart > minimumPart) {
        return false;
      }
    }
    
    return false;
  }

  private hasDynamicScriptLoading(): boolean {
    const scripts = document.querySelectorAll('script');
    return Array.from(scripts).some(script => 
      script.textContent && 
      (script.textContent.includes('createElement("script")') ||
       script.textContent.includes('document.write("<script'))
    );
  }

  private hasSSRFProtection(): boolean {
    // 檢查是否有SSRF防護的跡象
    return document.body.textContent?.includes('whitelist') || false;
  }

  private isWhitelistedDomain(url: string): boolean {
    try {
      const domain = new URL(url).hostname;
      const whitelistedDomains = [
        'youtube.com',
        'vimeo.com',
        'google.com',
        window.location.hostname
      ];
      
      return whitelistedDomains.some(allowed => 
        domain === allowed || domain.endsWith('.' + allowed)
      );
    } catch {
      return false;
    }
  }

  private containsSensitiveInformation(log: string): boolean {
    const sensitivePatterns = [
      /password[:=]\s*\S+/i,
      /token[:=]\s*\S+/i,
      /key[:=]\s*\S+/i,
      /secret[:=]\s*\S+/i,
      /\d{16,19}/, // 信用卡號
      /\d{3}-\d{2}-\d{4}/ // SSN
    ];
    
    return sensitivePatterns.some(pattern => pattern.test(log));
  }

  // CSP違規處理
  private handleCSPViolation(report: any) {
    this.checkResults.push({
      id: `csp_violation_${Date.now()}`,
      type: 'csp',
      title: 'CSP違規檢測',
      description: 'Content Security Policy違規事件',
      level: 'medium',
      passed: false,
      score: 60,
      details: {
        violatedDirective: report.body?.violatedDirective,
        blockedURI: report.body?.blockedURI,
        sourceFile: report.body?.sourceFile,
        lineNumber: report.body?.lineNumber
      },
      recommendations: [
        '檢查並修正違反CSP的資源',
        '更新CSP策略以允許合法資源'
      ],
      timestamp: Date.now()
    });
    
    this.notifyObservers();
  }

  // 控制台錯誤分析
  private analyzeConsoleError(args: any[]) {
    const errorMessage = args.join(' ');
    
    // 檢查是否為安全相關錯誤
    const securityErrorPatterns = [
      /mixed content/i,
      /blocked.*security/i,
      /csp/i,
      /cross.origin/i,
      /unsafe.eval/i
    ];
    
    if (securityErrorPatterns.some(pattern => pattern.test(errorMessage))) {
      this.checkResults.push({
        id: `security_error_${Date.now()}`,
        type: 'headers',
        title: '安全相關錯誤',
        description: '控制台中檢測到安全相關錯誤',
        level: 'medium',
        passed: false,
        score: 70,
        details: { errorMessage: errorMessage.substring(0, 200) },
        recommendations: [
          '修正控制台中的安全錯誤',
          '檢查相關的安全配置'
        ],
        timestamp: Date.now()
      });
      
      this.notifyObservers();
    }
  }

  // 計算整體安全評分
  private calculateOverallScore(): number {
    if (this.checkResults.length === 0) return 0;
    
    const totalScore = this.checkResults.reduce((sum, result) => sum + result.score, 0);
    return Math.round(totalScore / this.checkResults.length);
  }

  // 獲取安全評分等級
  getSecurityGrade(): string {
    const score = this.calculateOverallScore();
    
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  // 獲取檢查結果
  getCheckResults(): SecurityCheckResult[] {
    return [...this.checkResults];
  }

  // 獲取特定類型的檢查結果
  getResultsByType(type: SecurityCheckType): SecurityCheckResult[] {
    return this.checkResults.filter(result => result.type === type);
  }

  // 獲取失敗的檢查
  getFailedChecks(): SecurityCheckResult[] {
    return this.checkResults.filter(result => !result.passed);
  }

  // 獲取高風險檢查
  getHighRiskChecks(): SecurityCheckResult[] {
    return this.checkResults.filter(result => 
      result.level === 'critical' || result.level === 'high'
    );
  }

  // 添加觀察者
  addObserver(callback: (results: SecurityCheckResult[]) => void): () => void {
    this.observers.add(callback);
    
    return () => {
      this.observers.delete(callback);
    };
  }

  // 通知觀察者
  private notifyObservers() {
    this.observers.forEach(callback => callback([...this.checkResults]));
  }

  // 生成安全報告
  generateSecurityReport(): {
    overallScore: number;
    grade: string;
    summary: {
      totalChecks: number;
      passedChecks: number;
      failedChecks: number;
      criticalIssues: number;
      highIssues: number;
      mediumIssues: number;
      lowIssues: number;
    };
    results: SecurityCheckResult[];
  } {
    const results = this.getCheckResults();
    const failed = this.getFailedChecks();
    
    return {
      overallScore: this.calculateOverallScore(),
      grade: this.getSecurityGrade(),
      summary: {
        totalChecks: results.length,
        passedChecks: results.length - failed.length,
        failedChecks: failed.length,
        criticalIssues: results.filter(r => r.level === 'critical').length,
        highIssues: results.filter(r => r.level === 'high').length,
        mediumIssues: results.filter(r => r.level === 'medium').length,
        lowIssues: results.filter(r => r.level === 'low').length
      },
      results
    };
  }
}

// 創建全域實例
export const securityAuditor = new SecurityAuditor();

// 便利函數
export const runSecurityAudit = () => securityAuditor.runFullAudit();
export const getSecurityScore = () => securityAuditor.calculateOverallScore();
export const getSecurityGrade = () => securityAuditor.getSecurityGrade();

export default securityAuditor;
/**
 * 滲透測試和漏洞檢測系統 - 第二階段Week 4 安全合規強化
 * 前端安全漏洞檢測、自動化滲透測試、安全評估
 * 支援 XSS、CSRF、注入攻擊、權限繞過等漏洞檢測
 */

// 漏洞類型
export enum VulnerabilityType {
  XSS = 'xss',
  CSRF = 'csrf',
  INJECTION = 'injection',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  SENSITIVE_DATA = 'sensitive_data',
  CONFIGURATION = 'configuration',
  DEPENDENCY = 'dependency',
  CLICKJACKING = 'clickjacking',
  CONTENT_SECURITY = 'content_security'
}

// 嚴重性級別
export enum SeverityLevel {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info'
}

// 漏洞狀態
export enum VulnerabilityStatus {
  DETECTED = 'detected',
  CONFIRMED = 'confirmed',
  FALSE_POSITIVE = 'false_positive',
  FIXED = 'fixed',
  MITIGATED = 'mitigated'
}

// 漏洞詳情
export interface Vulnerability {
  id: string;
  type: VulnerabilityType;
  severity: SeverityLevel;
  status: VulnerabilityStatus;
  title: string;
  description: string;
  location: string;
  evidence: any;
  impact: string;
  remediation: string;
  references: string[];
  cvss?: number;
  cwe?: string;
  timestamp: number;
  confidence: number; // 0-100
}

// 測試結果
export interface PenetrationTestResult {
  testId: string;
  testName: string;
  status: 'passed' | 'failed' | 'error';
  vulnerabilities: Vulnerability[];
  details: string;
  timestamp: number;
  duration: number;
}

// 滲透測試報告
export interface PenetrationTestReport {
  reportId: string;
  timestamp: number;
  duration: number;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  totalVulnerabilities: number;
  criticalVulnerabilities: number;
  highVulnerabilities: number;
  mediumVulnerabilities: number;
  lowVulnerabilities: number;
  overallRiskScore: number;
  results: PenetrationTestResult[];
  summary: TestSummary;
  recommendations: string[];
}

// 測試摘要
export interface TestSummary {
  xssTests: TestTypeResult;
  csrfTests: TestTypeResult;
  injectionTests: TestTypeResult;
  authTests: TestTypeResult;
  configTests: TestTypeResult;
  dependencyTests: TestTypeResult;
}

export interface TestTypeResult {
  totalTests: number;
  passedTests: number;
  vulnerabilities: number;
  highestSeverity: SeverityLevel;
}

// 滲透測試器類別
class PenetrationTester {
  private vulnerabilities: Vulnerability[] = [];
  private testResults: PenetrationTestResult[] = [];
  private lastReportId: string | null = null;

  constructor() {
    // 初始化測試環境
    this.initializeTestEnvironment();
  }

  // 初始化測試環境
  private initializeTestEnvironment() {
    console.log('[PenetrationTester] Initializing test environment');
    
    // 設置測試配置
    this.setupTestConfiguration();
  }

  // 設置測試配置
  private setupTestConfiguration() {
    // 測試配置可以在這裡設定
  }

  // 執行完整滲透測試
  async runFullPenetrationTest(): Promise<PenetrationTestReport> {
    console.log('[PenetrationTester] Starting full penetration test');
    const startTime = Date.now();

    this.vulnerabilities = [];
    this.testResults = [];

    // 執行各類型測試
    await this.runXSSTests();
    await this.runCSRFTests();
    await this.runInjectionTests();
    await this.runAuthenticationTests();
    await this.runAuthorizationTests();
    await this.runSensitiveDataTests();
    await this.runConfigurationTests();
    await this.runDependencyTests();
    await this.runClickjackingTests();
    await this.runContentSecurityTests();

    const endTime = Date.now();
    return this.generateReport(endTime - startTime);
  }

  // XSS 漏洞測試
  private async runXSSTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    // 測試 1: DOM-based XSS
    const domXssResult = await this.testDOMBasedXSS();
    testResults.push(domXssResult);

    // 測試 2: Reflected XSS
    const reflectedXssResult = await this.testReflectedXSS();
    testResults.push(reflectedXssResult);

    // 測試 3: Stored XSS
    const storedXssResult = await this.testStoredXSS();
    testResults.push(storedXssResult);

    // 測試 4: CSP 繞過
    const cspBypassResult = await this.testCSPBypass();
    testResults.push(cspBypassResult);

    this.testResults.push(...testResults);
  }

  // DOM-based XSS 測試
  private async testDOMBasedXSS(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查 URL 參數處理
      const urlParams = new URLSearchParams(window.location.search);
      const dangerousParams = ['q', 'search', 'query', 'msg', 'error', 'success'];

      dangerousParams.forEach(param => {
        const value = urlParams.get(param);
        if (value) {
          // 檢查參數是否直接插入 DOM
          const elementsWithParam = document.querySelectorAll(`*[data-param="${param}"]`);
          elementsWithParam.forEach((element, index) => {
            if (element.innerHTML.includes(value)) {
              vulnerabilities.push({
                id: `dom-xss-${param}-${index}`,
                type: VulnerabilityType.XSS,
                severity: SeverityLevel.HIGH,
                status: VulnerabilityStatus.DETECTED,
                title: 'DOM-based XSS 漏洞',
                description: `URL 參數 '${param}' 直接插入 DOM 而未進行適當過濾`,
                location: `element[data-param="${param}"]`,
                evidence: { param, value, element: element.outerHTML.substring(0, 200) },
                impact: '攻擊者可以執行任意 JavaScript 代碼',
                remediation: '對用戶輸入進行適當的編碼和驗證',
                references: ['https://owasp.org/www-community/attacks/DOM_Based_XSS'],
                cwe: 'CWE-79',
                timestamp: Date.now(),
                confidence: 90
              });
              status = 'failed';
            }
          });
        }
      });

      // 檢查 innerHTML 的使用
      const scriptsWithInnerHTML = Array.from(document.scripts).filter(script => 
        script.textContent?.includes('innerHTML') && 
        (script.textContent.includes('location.') || script.textContent.includes('document.URL'))
      );

      if (scriptsWithInnerHTML.length > 0) {
        vulnerabilities.push({
          id: 'dom-xss-innerhtml',
          type: VulnerabilityType.XSS,
          severity: SeverityLevel.MEDIUM,
          status: VulnerabilityStatus.DETECTED,
          title: '潛在的 DOM XSS 風險',
          description: '代碼中使用 innerHTML 處理用戶可控的數據',
          location: 'JavaScript code',
          evidence: { scriptsCount: scriptsWithInnerHTML.length },
          impact: '可能存在 DOM XSS 攻擊風險',
          remediation: '使用 textContent 或適當的 DOM 操作方法',
          references: ['https://owasp.org/www-community/attacks/DOM_Based_XSS'],
          cwe: 'CWE-79',
          timestamp: Date.now(),
          confidence: 60
        });
        status = 'failed';
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'dom-xss-test',
      testName: 'DOM-based XSS 測試',
      status,
      vulnerabilities,
      details: `檢測到 ${vulnerabilities.length} 個潛在的 DOM XSS 漏洞`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // Reflected XSS 測試
  private async testReflectedXSS(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查表單輸入
      const forms = document.querySelectorAll('form');
      
      for (let i = 0; i < forms.length; i++) {
        const form = forms[i];
        const inputs = form.querySelectorAll('input[type="text"], input[type="search"], textarea');
        
        inputs.forEach((input, inputIndex) => {
          const inputElement = input as HTMLInputElement;
          
          // 檢查是否有輸入驗證
          if (!inputElement.pattern && !inputElement.getAttribute('data-validate')) {
            vulnerabilities.push({
              id: `reflected-xss-form-${i}-${inputIndex}`,
              type: VulnerabilityType.XSS,
              severity: SeverityLevel.MEDIUM,
              status: VulnerabilityStatus.DETECTED,
              title: '缺少輸入驗證的表單欄位',
              description: `表單欄位 '${inputElement.name || inputElement.id}' 缺少適當的輸入驗證`,
              location: `form[${i}] input[${inputIndex}]`,
              evidence: { 
                formAction: form.action,
                inputName: inputElement.name,
                inputType: inputElement.type
              },
              impact: '可能存在 Reflected XSS 攻擊風險',
              remediation: '添加輸入驗證和輸出編碼',
              references: ['https://owasp.org/www-community/attacks/xss/'],
              cwe: 'CWE-79',
              timestamp: Date.now(),
              confidence: 50
            });
            status = 'failed';
          }
        });
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'reflected-xss-test',
      testName: 'Reflected XSS 測試',
      status,
      vulnerabilities,
      details: `檢查了表單欄位，發現 ${vulnerabilities.length} 個潛在問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // Stored XSS 測試
  private async testStoredXSS(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查用戶生成內容區域
      const contentAreas = document.querySelectorAll('[data-user-content], .user-content, .comment, .review');
      
      contentAreas.forEach((area, index) => {
        // 檢查是否有內容安全措施
        if (!area.getAttribute('data-sanitized') && !area.classList.contains('sanitized')) {
          vulnerabilities.push({
            id: `stored-xss-content-${index}`,
            type: VulnerabilityType.XSS,
            severity: SeverityLevel.HIGH,
            status: VulnerabilityStatus.DETECTED,
            title: '用戶內容區域缺少安全措施',
            description: '用戶生成的內容可能未經適當的安全處理',
            location: `user-content-area[${index}]`,
            evidence: { className: area.className, innerHTML: area.innerHTML.substring(0, 100) },
            impact: '存儲型 XSS 攻擊可能影響其他用戶',
            remediation: '對用戶內容進行適當的過濾和編碼',
            references: ['https://owasp.org/www-community/attacks/xss/'],
            cwe: 'CWE-79',
            timestamp: Date.now(),
            confidence: 70
          });
          status = 'failed';
        }
      });

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'stored-xss-test',
      testName: 'Stored XSS 測試',
      status,
      vulnerabilities,
      details: `檢查了用戶內容區域，發現 ${vulnerabilities.length} 個潛在問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // CSP 繞過測試
  private async testCSPBypass(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查 CSP 頭部
      const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
      const cspContent = cspMeta?.getAttribute('content') || '';

      if (!cspContent) {
        vulnerabilities.push({
          id: 'csp-missing',
          type: VulnerabilityType.CONTENT_SECURITY,
          severity: SeverityLevel.HIGH,
          status: VulnerabilityStatus.DETECTED,
          title: '缺少 Content Security Policy',
          description: '網站未設置 CSP 頭部，無法防範 XSS 攻擊',
          location: 'HTTP headers',
          evidence: { cspFound: false },
          impact: '無法有效防範 XSS 攻擊',
          remediation: '配置適當的 Content Security Policy',
          references: ['https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP'],
          cwe: 'CWE-693',
          timestamp: Date.now(),
          confidence: 95
        });
        status = 'failed';
      } else {
        // 檢查 CSP 配置
        if (cspContent.includes("'unsafe-inline'")) {
          vulnerabilities.push({
            id: 'csp-unsafe-inline',
            type: VulnerabilityType.CONTENT_SECURITY,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: 'CSP 允許 unsafe-inline',
            description: 'CSP 設置允許內聯腳本執行，降低了安全性',
            location: 'CSP policy',
            evidence: { cspContent },
            impact: '可能被繞過進行 XSS 攻擊',
            remediation: '移除 unsafe-inline 指令，使用 nonce 或 hash',
            references: ['https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP'],
            cwe: 'CWE-693',
            timestamp: Date.now(),
            confidence: 80
          });
          status = 'failed';
        }

        if (cspContent.includes("'unsafe-eval'")) {
          vulnerabilities.push({
            id: 'csp-unsafe-eval',
            type: VulnerabilityType.CONTENT_SECURITY,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: 'CSP 允許 unsafe-eval',
            description: 'CSP 設置允許 eval() 執行，存在安全風險',
            location: 'CSP policy',
            evidence: { cspContent },
            impact: '可能執行動態代碼造成安全風險',
            remediation: '移除 unsafe-eval 指令',
            references: ['https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP'],
            cwe: 'CWE-693',
            timestamp: Date.now(),
            confidence: 80
          });
          status = 'failed';
        }
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'csp-bypass-test',
      testName: 'CSP 繞過測試',
      status,
      vulnerabilities,
      details: `CSP 配置檢查完成，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // CSRF 漏洞測試
  private async runCSRFTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const csrfResult = await this.testCSRFProtection();
    testResults.push(csrfResult);

    this.testResults.push(...testResults);
  }

  // CSRF 保護測試
  private async testCSRFProtection(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查表單 CSRF Token
      const forms = document.querySelectorAll('form[method="post"], form[method="POST"]');
      
      forms.forEach((form, index) => {
        const csrfToken = form.querySelector('input[name*="csrf"], input[name*="token"], input[name="_token"]');
        
        if (!csrfToken) {
          vulnerabilities.push({
            id: `csrf-missing-${index}`,
            type: VulnerabilityType.CSRF,
            severity: SeverityLevel.HIGH,
            status: VulnerabilityStatus.DETECTED,
            title: '表單缺少 CSRF 保護',
            description: `POST 表單缺少 CSRF token 保護`,
            location: `form[${index}]`,
            evidence: { 
              formAction: form.getAttribute('action'),
              formMethod: form.getAttribute('method')
            },
            impact: '可能遭受 CSRF 攻擊，執行未經授權的操作',
            remediation: '添加 CSRF token 到表單中',
            references: ['https://owasp.org/www-community/attacks/csrf'],
            cwe: 'CWE-352',
            timestamp: Date.now(),
            confidence: 90
          });
          status = 'failed';
        }
      });

      // 檢查 AJAX 請求的 CSRF 保護
      const scriptsWithAjax = Array.from(document.scripts).filter(script => 
        script.textContent && (
          script.textContent.includes('$.post') ||
          script.textContent.includes('fetch') ||
          script.textContent.includes('XMLHttpRequest')
        )
      );

      if (scriptsWithAjax.length > 0) {
        const hasCSRFHeader = scriptsWithAjax.some(script => 
          script.textContent?.includes('X-CSRF-TOKEN') ||
          script.textContent?.includes('X-CSRFToken') ||
          script.textContent?.includes('csrfToken')
        );

        if (!hasCSRFHeader) {
          vulnerabilities.push({
            id: 'csrf-ajax-missing',
            type: VulnerabilityType.CSRF,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: 'AJAX 請求缺少 CSRF 保護',
            description: 'JavaScript 中的 AJAX 請求可能缺少 CSRF token',
            location: 'JavaScript code',
            evidence: { ajaxScriptsCount: scriptsWithAjax.length },
            impact: 'AJAX 請求可能遭受 CSRF 攻擊',
            remediation: '在 AJAX 請求中添加 CSRF token 頭部',
            references: ['https://owasp.org/www-community/attacks/csrf'],
            cwe: 'CWE-352',
            timestamp: Date.now(),
            confidence: 60
          });
          status = 'failed';
        }
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'csrf-protection-test',
      testName: 'CSRF 保護測試',
      status,
      vulnerabilities,
      details: `檢查了 CSRF 保護機制，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 注入攻擊測試
  private async runInjectionTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const injectionResult = await this.testInjectionVulnerabilities();
    testResults.push(injectionResult);

    this.testResults.push(...testResults);
  }

  // 注入漏洞測試
  private async testInjectionVulnerabilities(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查 SQL 注入風險
      const forms = document.querySelectorAll('form');
      
      forms.forEach((form, index) => {
        const inputs = form.querySelectorAll('input[name*="id"], input[name*="query"], input[name*="search"]');
        
        inputs.forEach((input, inputIndex) => {
          const inputElement = input as HTMLInputElement;
          
          if (inputElement.type !== 'hidden' && !inputElement.pattern) {
            vulnerabilities.push({
              id: `sql-injection-risk-${index}-${inputIndex}`,
              type: VulnerabilityType.INJECTION,
              severity: SeverityLevel.HIGH,
              status: VulnerabilityStatus.DETECTED,
              title: '潛在的 SQL 注入風險',
              description: `輸入欄位 '${inputElement.name}' 可能存在 SQL 注入風險`,
              location: `form[${index}] input[${inputIndex}]`,
              evidence: { 
                inputName: inputElement.name,
                inputType: inputElement.type,
                hasValidation: !!inputElement.pattern
              },
              impact: '可能導致數據庫洩露或修改',
              remediation: '使用參數化查詢和輸入驗證',
              references: ['https://owasp.org/www-community/attacks/SQL_Injection'],
              cwe: 'CWE-89',
              timestamp: Date.now(),
              confidence: 40
            });
            status = 'failed';
          }
        });
      });

      // 檢查命令注入風險
      const scriptsWithExec = Array.from(document.scripts).filter(script => 
        script.textContent && (
          script.textContent.includes('eval(') ||
          script.textContent.includes('Function(') ||
          script.textContent.includes('setTimeout(') ||
          script.textContent.includes('setInterval(')
        )
      );

      if (scriptsWithExec.length > 0) {
        vulnerabilities.push({
          id: 'code-injection-risk',
          type: VulnerabilityType.INJECTION,
          severity: SeverityLevel.MEDIUM,
          status: VulnerabilityStatus.DETECTED,
          title: '潛在的代碼注入風險',
          description: 'JavaScript 中使用了可能的代碼執行函數',
          location: 'JavaScript code',
          evidence: { riskyScriptsCount: scriptsWithExec.length },
          impact: '可能執行惡意代碼',
          remediation: '避免使用 eval() 等危險函數',
          references: ['https://owasp.org/www-community/attacks/Code_Injection'],
          cwe: 'CWE-94',
          timestamp: Date.now(),
          confidence: 50
        });
        status = 'failed';
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'injection-test',
      testName: '注入攻擊測試',
      status,
      vulnerabilities,
      details: `檢查了注入攻擊風險，發現 ${vulnerabilities.length} 個潛在問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 身份認證測試
  private async runAuthenticationTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const authResult = await this.testAuthenticationSecurity();
    testResults.push(authResult);

    this.testResults.push(...testResults);
  }

  // 身份認證安全測試
  private async testAuthenticationSecurity(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查登入表單
      const loginForms = document.querySelectorAll('form[action*="login"], form[action*="signin"], .login-form');
      
      loginForms.forEach((form, index) => {
        const passwordInput = form.querySelector('input[type="password"]');
        
        if (passwordInput) {
          // 檢查密碼欄位是否有自動完成
          if (passwordInput.getAttribute('autocomplete') === 'on') {
            vulnerabilities.push({
              id: `auth-autocomplete-${index}`,
              type: VulnerabilityType.AUTHENTICATION,
              severity: SeverityLevel.LOW,
              status: VulnerabilityStatus.DETECTED,
              title: '密碼欄位允許自動完成',
              description: '登入表單的密碼欄位啟用了自動完成功能',
              location: `login-form[${index}]`,
              evidence: { autocomplete: passwordInput.getAttribute('autocomplete') },
              impact: '可能在共用設備上暴露密碼',
              remediation: '設置密碼欄位 autocomplete="off"',
              references: ['https://owasp.org/www-community/vulnerabilities/Autocomplete'],
              cwe: 'CWE-200',
              timestamp: Date.now(),
              confidence: 80
            });
            status = 'failed';
          }

          // 檢查是否有密碼強度要求
          if (!passwordInput.pattern && !passwordInput.getAttribute('data-strength-check')) {
            vulnerabilities.push({
              id: `auth-password-policy-${index}`,
              type: VulnerabilityType.AUTHENTICATION,
              severity: SeverityLevel.MEDIUM,
              status: VulnerabilityStatus.DETECTED,
              title: '缺少密碼強度要求',
              description: '密碼欄位沒有設置強度要求或驗證',
              location: `login-form[${index}]`,
              evidence: { hasPattern: !!passwordInput.pattern },
              impact: '用戶可能使用弱密碼',
              remediation: '實施密碼強度要求和驗證',
              references: ['https://owasp.org/www-community/controls/Password_Strength'],
              cwe: 'CWE-521',
              timestamp: Date.now(),
              confidence: 60
            });
            status = 'failed';
          }
        }

        // 檢查是否有重試限制
        if (!form.getAttribute('data-rate-limit') && !form.classList.contains('rate-limited')) {
          vulnerabilities.push({
            id: `auth-brute-force-${index}`,
            type: VulnerabilityType.AUTHENTICATION,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: '缺少登入嘗試限制',
            description: '登入表單可能缺少暴力破解保護',
            location: `login-form[${index}]`,
            evidence: { hasRateLimit: !!form.getAttribute('data-rate-limit') },
            impact: '可能遭受暴力破解攻擊',
            remediation: '實施登入嘗試限制和帳戶鎖定機制',
            references: ['https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks'],
            cwe: 'CWE-307',
            timestamp: Date.now(),
            confidence: 50
          });
          status = 'failed';
        }
      });

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'authentication-test',
      testName: '身份認證安全測試',
      status,
      vulnerabilities,
      details: `檢查了身份認證安全性，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 權限控制測試
  private async runAuthorizationTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const authzResult = await this.testAuthorizationSecurity();
    testResults.push(authzResult);

    this.testResults.push(...testResults);
  }

  // 權限控制安全測試
  private async testAuthorizationSecurity(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查管理功能
      const adminElements = document.querySelectorAll('[data-admin], .admin, [href*="admin"]');
      
      adminElements.forEach((element, index) => {
        const el = element as HTMLElement;
        
        // 檢查是否只在客戶端隱藏管理功能
        if (el.style.display === 'none' && !el.getAttribute('data-server-auth')) {
          vulnerabilities.push({
            id: `authz-client-only-${index}`,
            type: VulnerabilityType.AUTHORIZATION,
            severity: SeverityLevel.HIGH,
            status: VulnerabilityStatus.DETECTED,
            title: '僅客戶端權限控制',
            description: '管理功能僅在客戶端隱藏，可能被繞過',
            location: `admin-element[${index}]`,
            evidence: { 
              display: el.style.display,
              hasServerAuth: !!el.getAttribute('data-server-auth')
            },
            impact: '未授權用戶可能存取管理功能',
            remediation: '在伺服器端實施權限檢查',
            references: ['https://owasp.org/www-community/Access_Control'],
            cwe: 'CWE-284',
            timestamp: Date.now(),
            confidence: 70
          });
          status = 'failed';
        }
      });

      // 檢查敏感操作按鈕
      const dangerousButtons = document.querySelectorAll(
        'button[data-action*="delete"], button[data-action*="remove"], ' +
        'button[onclick*="delete"], button[onclick*="remove"]'
      );

      dangerousButtons.forEach((button, index) => {
        const btn = button as HTMLButtonElement;
        
        if (!btn.getAttribute('data-confirm') && !btn.onclick?.toString().includes('confirm')) {
          vulnerabilities.push({
            id: `authz-dangerous-action-${index}`,
            type: VulnerabilityType.AUTHORIZATION,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: '危險操作缺少確認',
            description: '刪除或移除操作缺少用戶確認',
            location: `dangerous-button[${index}]`,
            evidence: { 
              action: btn.getAttribute('data-action'),
              hasConfirm: !!btn.getAttribute('data-confirm')
            },
            impact: '可能意外執行危險操作',
            remediation: '添加用戶確認對話框',
            references: ['https://owasp.org/www-community/Access_Control'],
            cwe: 'CWE-352',
            timestamp: Date.now(),
            confidence: 80
          });
          status = 'failed';
        }
      });

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'authorization-test',
      testName: '權限控制安全測試',
      status,
      vulnerabilities,
      details: `檢查了權限控制，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 敏感數據測試
  private async runSensitiveDataTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const sensitiveDataResult = await this.testSensitiveDataExposure();
    testResults.push(sensitiveDataResult);

    this.testResults.push(...testResults);
  }

  // 敏感數據暴露測試
  private async testSensitiveDataExposure(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查頁面源碼中的敏感信息
      const pageSource = document.documentElement.outerHTML;
      const sensitivePatterns = [
        { pattern: /password\s*[:=]\s*["'][^"']+["']/gi, name: '硬編碼密碼' },
        { pattern: /api[_-]?key\s*[:=]\s*["'][^"']+["']/gi, name: 'API 密鑰' },
        { pattern: /secret\s*[:=]\s*["'][^"']+["']/gi, name: '密鑰資訊' },
        { pattern: /token\s*[:=]\s*["'][^"']+["']/gi, name: '認證 Token' },
        { pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, name: '信用卡號' },
        { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, name: '社會安全號碼' }
      ];

      sensitivePatterns.forEach((patternInfo, index) => {
        const matches = pageSource.match(patternInfo.pattern);
        if (matches && matches.length > 0) {
          vulnerabilities.push({
            id: `sensitive-data-${index}`,
            type: VulnerabilityType.SENSITIVE_DATA,
            severity: SeverityLevel.HIGH,
            status: VulnerabilityStatus.DETECTED,
            title: `頁面源碼包含${patternInfo.name}`,
            description: `在頁面源碼中發現可能的${patternInfo.name}`,
            location: 'HTML source',
            evidence: { 
              pattern: patternInfo.name,
              matchCount: matches.length,
              samples: matches.slice(0, 3).map(m => m.substring(0, 50))
            },
            impact: '敏感信息可能被未授權存取',
            remediation: '移除硬編碼的敏感信息，使用安全的配置管理',
            references: ['https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings'],
            cwe: 'CWE-200',
            timestamp: Date.now(),
            confidence: 90
          });
          status = 'failed';
        }
      });

      // 檢查 localStorage 和 sessionStorage
      try {
        const localStorageKeys = Object.keys(localStorage);
        const sessionStorageKeys = Object.keys(sessionStorage);
        
        const storagePatterns = ['password', 'token', 'key', 'secret', 'auth'];
        
        [...localStorageKeys, ...sessionStorageKeys].forEach(key => {
          if (storagePatterns.some(pattern => key.toLowerCase().includes(pattern))) {
            vulnerabilities.push({
              id: `sensitive-storage-${key}`,
              type: VulnerabilityType.SENSITIVE_DATA,
              severity: SeverityLevel.MEDIUM,
              status: VulnerabilityStatus.DETECTED,
              title: '瀏覽器存儲包含敏感數據',
              description: `存儲鍵 '${key}' 可能包含敏感信息`,
              location: 'Browser storage',
              evidence: { storageKey: key, storageType: localStorageKeys.includes(key) ? 'localStorage' : 'sessionStorage' },
              impact: '敏感數據可能被惡意腳本存取',
              remediation: '避免在客戶端存儲敏感信息，或使用適當加密',
              references: ['https://owasp.org/www-community/vulnerabilities/HTML5_Security'],
              cwe: 'CWE-312',
              timestamp: Date.now(),
              confidence: 60
            });
            status = 'failed';
          }
        });
      } catch (error) {
        // 無法存取 storage，可能被限制
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'sensitive-data-test',
      testName: '敏感數據暴露測試',
      status,
      vulnerabilities,
      details: `檢查了敏感數據暴露，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 配置安全測試
  private async runConfigurationTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const configResult = await this.testSecurityConfiguration();
    testResults.push(configResult);

    this.testResults.push(...testResults);
  }

  // 安全配置測試
  private async testSecurityConfiguration(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查安全標頭
      const securityHeaders = [
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection',
        'Strict-Transport-Security',
        'Referrer-Policy'
      ];

      // 由於無法直接存取 HTTP 頭部，檢查 meta 標籤
      securityHeaders.forEach(header => {
        const metaTag = document.querySelector(`meta[http-equiv="${header}"]`);
        if (!metaTag) {
          let severity = SeverityLevel.MEDIUM;
          if (header === 'X-Frame-Options' || header === 'X-Content-Type-Options') {
            severity = SeverityLevel.HIGH;
          }

          vulnerabilities.push({
            id: `config-header-${header.toLowerCase()}`,
            type: VulnerabilityType.CONFIGURATION,
            severity,
            status: VulnerabilityStatus.DETECTED,
            title: `缺少安全標頭 ${header}`,
            description: `網站未設置 ${header} 安全標頭`,
            location: 'HTTP headers',
            evidence: { header, found: false },
            impact: this.getHeaderImpact(header),
            remediation: `配置 ${header} 安全標頭`,
            references: ['https://owasp.org/www-community/Security_Headers'],
            cwe: 'CWE-693',
            timestamp: Date.now(),
            confidence: 80
          });
          status = 'failed';
        }
      });

      // 檢查錯誤頁面信息洩露
      const errorElements = document.querySelectorAll('[class*="error"], [id*="error"], .exception, .debug');
      errorElements.forEach((element, index) => {
        const el = element as HTMLElement;
        if (el.textContent && (
          el.textContent.includes('Exception') ||
          el.textContent.includes('Stack trace') ||
          el.textContent.includes('MySQL') ||
          el.textContent.includes('PostgreSQL')
        )) {
          vulnerabilities.push({
            id: `config-error-disclosure-${index}`,
            type: VulnerabilityType.CONFIGURATION,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: '錯誤信息洩露',
            description: '頁面顯示了詳細的錯誤或調試信息',
            location: `error-element[${index}]`,
            evidence: { 
              className: el.className,
              textContent: el.textContent.substring(0, 100)
            },
            impact: '可能洩露系統架構和敏感信息',
            remediation: '在生產環境中隱藏詳細錯誤信息',
            references: ['https://owasp.org/www-community/Improper_Error_Handling'],
            cwe: 'CWE-209',
            timestamp: Date.now(),
            confidence: 85
          });
          status = 'failed';
        }
      });

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'configuration-test',
      testName: '安全配置測試',
      status,
      vulnerabilities,
      details: `檢查了安全配置，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 依賴安全測試
  private async runDependencyTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const depResult = await this.testDependencySecurity();
    testResults.push(depResult);

    this.testResults.push(...testResults);
  }

  // 依賴安全測試
  private async testDependencySecurity(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查第三方庫
      const scripts = document.querySelectorAll('script[src]');
      const thirdPartyLibraries = new Map<string, string>();

      scripts.forEach(script => {
        const src = script.getAttribute('src');
        if (src && (src.includes('cdn') || src.includes('//') && !src.startsWith('//'))) {
          try {
            const url = new URL(src);
            const libraryName = this.extractLibraryName(url.pathname);
            if (libraryName) {
              thirdPartyLibraries.set(libraryName, src);
            }
          } catch (error) {
            // 無效 URL
          }
        }
      });

      // 檢查已知有漏洞的庫版本（簡化檢查）
      const knownVulnerableLibraries = [
        { name: 'jquery', vulnerable: ['1.', '2.', '3.0.', '3.1.', '3.2.', '3.3.', '3.4.0'] },
        { name: 'bootstrap', vulnerable: ['2.', '3.0.', '3.1.', '3.2.', '3.3.0', '3.3.1'] },
        { name: 'angular', vulnerable: ['1.0.', '1.1.', '1.2.', '1.3.', '1.4.', '1.5.', '1.6.0', '1.6.1'] }
      ];

      thirdPartyLibraries.forEach((src, libName) => {
        knownVulnerableLibraries.forEach(vulnLib => {
          if (libName.toLowerCase().includes(vulnLib.name)) {
            const isVulnerable = vulnLib.vulnerable.some(version => src.includes(version));
            if (isVulnerable) {
              vulnerabilities.push({
                id: `dependency-vulnerable-${libName}`,
                type: VulnerabilityType.DEPENDENCY,
                severity: SeverityLevel.MEDIUM,
                status: VulnerabilityStatus.DETECTED,
                title: `使用已知漏洞的依賴庫`,
                description: `第三方庫 ${libName} 可能存在已知安全漏洞`,
                location: 'External dependencies',
                evidence: { library: libName, src },
                impact: '可能被利用進行攻擊',
                remediation: '更新到最新的安全版本',
                references: ['https://snyk.io/vuln'],
                cwe: 'CWE-1035',
                timestamp: Date.now(),
                confidence: 50
              });
              status = 'failed';
            }
          }
        });
      });

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'dependency-test',
      testName: '依賴安全測試',
      status,
      vulnerabilities,
      details: `檢查了第三方依賴，發現 ${vulnerabilities.length} 個潛在問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 點擊劫持測試
  private async runClickjackingTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const clickjackingResult = await this.testClickjackingProtection();
    testResults.push(clickjackingResult);

    this.testResults.push(...testResults);
  }

  // 點擊劫持保護測試
  private async testClickjackingProtection(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查 X-Frame-Options
      const frameOptions = document.querySelector('meta[http-equiv="X-Frame-Options"]');
      if (!frameOptions) {
        vulnerabilities.push({
          id: 'clickjacking-no-frame-options',
          type: VulnerabilityType.CLICKJACKING,
          severity: SeverityLevel.MEDIUM,
          status: VulnerabilityStatus.DETECTED,
          title: '缺少點擊劫持保護',
          description: '網站未設置 X-Frame-Options 頭部防止點擊劫持',
          location: 'HTTP headers',
          evidence: { frameOptionsFound: false },
          impact: '頁面可能被嵌入惡意網站進行點擊劫持攻擊',
          remediation: '設置 X-Frame-Options: DENY 或 SAMEORIGIN',
          references: ['https://owasp.org/www-community/attacks/Clickjacking'],
          cwe: 'CWE-693',
          timestamp: Date.now(),
          confidence: 90
        });
        status = 'failed';
      }

      // 檢查是否在 iframe 中
      if (window !== window.top) {
        // 檢查是否有框架破壞代碼
        const scripts = Array.from(document.scripts);
        const hasFrameBusting = scripts.some(script => 
          script.textContent && (
            script.textContent.includes('window.top') ||
            script.textContent.includes('parent.location') ||
            script.textContent.includes('self != top')
          )
        );

        if (!hasFrameBusting) {
          vulnerabilities.push({
            id: 'clickjacking-no-framebusting',
            type: VulnerabilityType.CLICKJACKING,
            severity: SeverityLevel.LOW,
            status: VulnerabilityStatus.DETECTED,
            title: '缺少框架破壞代碼',
            description: '頁面在 iframe 中但沒有框架破壞保護',
            location: 'JavaScript code',
            evidence: { inFrame: true, hasFrameBusting },
            impact: '在舊瀏覽器中可能遭受點擊劫持攻擊',
            remediation: '添加框架破壞 JavaScript 代碼',
            references: ['https://owasp.org/www-community/attacks/Clickjacking'],
            cwe: 'CWE-693',
            timestamp: Date.now(),
            confidence: 70
          });
          status = 'failed';
        }
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'clickjacking-test',
      testName: '點擊劫持保護測試',
      status,
      vulnerabilities,
      details: `檢查了點擊劫持保護，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 內容安全測試
  private async runContentSecurityTests(): Promise<void> {
    const testResults: PenetrationTestResult[] = [];

    const contentSecurityResult = await this.testContentSecurity();
    testResults.push(contentSecurityResult);

    this.testResults.push(...testResults);
  }

  // 內容安全測試
  private async testContentSecurity(): Promise<PenetrationTestResult> {
    const startTime = Date.now();
    const vulnerabilities: Vulnerability[] = [];
    let status: 'passed' | 'failed' | 'error' = 'passed';

    try {
      // 檢查混合內容
      if (location.protocol === 'https:') {
        const httpResources = Array.from(document.querySelectorAll('*')).filter(element => {
          const src = element.getAttribute('src');
          const href = element.getAttribute('href');
          return (src && src.startsWith('http://')) || (href && href.startsWith('http://'));
        });

        if (httpResources.length > 0) {
          vulnerabilities.push({
            id: 'content-mixed-content',
            type: VulnerabilityType.CONTENT_SECURITY,
            severity: SeverityLevel.MEDIUM,
            status: VulnerabilityStatus.DETECTED,
            title: '混合內容問題',
            description: 'HTTPS 頁面包含 HTTP 資源',
            location: 'Page resources',
            evidence: { httpResourceCount: httpResources.length },
            impact: '可能被中間人攻擊劫持資源',
            remediation: '將所有資源改為 HTTPS',
            references: ['https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content'],
            cwe: 'CWE-319',
            timestamp: Date.now(),
            confidence: 95
          });
          status = 'failed';
        }
      }

      // 檢查內聯樣式和腳本
      const inlineStyles = document.querySelectorAll('[style]');
      const inlineScripts = document.querySelectorAll('script:not([src])');

      if (inlineStyles.length > 10 || inlineScripts.length > 5) {
        vulnerabilities.push({
          id: 'content-inline-content',
          type: VulnerabilityType.CONTENT_SECURITY,
          severity: SeverityLevel.LOW,
          status: VulnerabilityStatus.DETECTED,
          title: '大量內聯內容',
          description: '頁面包含大量內聯樣式和腳本',
          location: 'HTML content',
          evidence: { 
            inlineStylesCount: inlineStyles.length,
            inlineScriptsCount: inlineScripts.length
          },
          impact: '可能難以實施嚴格的 CSP 政策',
          remediation: '將內聯內容移到外部文件或使用 CSP nonce',
          references: ['https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP'],
          cwe: 'CWE-693',
          timestamp: Date.now(),
          confidence: 60
        });
        status = 'failed';
      }

    } catch (error) {
      status = 'error';
    }

    this.vulnerabilities.push(...vulnerabilities);

    return {
      testId: 'content-security-test',
      testName: '內容安全測試',
      status,
      vulnerabilities,
      details: `檢查了內容安全，發現 ${vulnerabilities.length} 個問題`,
      timestamp: Date.now(),
      duration: Date.now() - startTime
    };
  }

  // 生成測試報告
  private generateReport(duration: number): PenetrationTestReport {
    const reportId = `pentest-${Date.now()}`;
    this.lastReportId = reportId;

    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.status === 'passed').length;
    const failedTests = this.testResults.filter(r => r.status === 'failed').length;

    // 計算漏洞統計
    const totalVulnerabilities = this.vulnerabilities.length;
    const criticalVulnerabilities = this.vulnerabilities.filter(v => v.severity === SeverityLevel.CRITICAL).length;
    const highVulnerabilities = this.vulnerabilities.filter(v => v.severity === SeverityLevel.HIGH).length;
    const mediumVulnerabilities = this.vulnerabilities.filter(v => v.severity === SeverityLevel.MEDIUM).length;
    const lowVulnerabilities = this.vulnerabilities.filter(v => v.severity === SeverityLevel.LOW).length;

    // 計算風險分數
    const overallRiskScore = this.calculateRiskScore();

    // 生成測試類型摘要
    const summary = this.generateTestSummary();

    // 生成建議
    const recommendations = this.generateSecurityRecommendations();

    return {
      reportId,
      timestamp: Date.now(),
      duration,
      totalTests,
      passedTests,
      failedTests,
      totalVulnerabilities,
      criticalVulnerabilities,
      highVulnerabilities,
      mediumVulnerabilities,
      lowVulnerabilities,
      overallRiskScore,
      results: this.testResults,
      summary,
      recommendations
    };
  }

  // 計算風險分數
  private calculateRiskScore(): number {
    let score = 0;
    
    this.vulnerabilities.forEach(vuln => {
      switch (vuln.severity) {
        case SeverityLevel.CRITICAL:
          score += 10;
          break;
        case SeverityLevel.HIGH:
          score += 5;
          break;
        case SeverityLevel.MEDIUM:
          score += 2;
          break;
        case SeverityLevel.LOW:
          score += 1;
          break;
      }
    });

    return Math.min(100, score);
  }

  // 生成測試摘要
  private generateTestSummary(): TestSummary {
    const testTypes = [
      { name: 'xss', type: VulnerabilityType.XSS },
      { name: 'csrf', type: VulnerabilityType.CSRF },
      { name: 'injection', type: VulnerabilityType.INJECTION },
      { name: 'auth', type: VulnerabilityType.AUTHENTICATION },
      { name: 'config', type: VulnerabilityType.CONFIGURATION },
      { name: 'dependency', type: VulnerabilityType.DEPENDENCY }
    ];

    const summary: any = {};

    testTypes.forEach(testType => {
      const typeResults = this.testResults.filter(r => 
        r.vulnerabilities.some(v => v.type === testType.type)
      );
      const typeVulns = this.vulnerabilities.filter(v => v.type === testType.type);

      const totalTests = this.testResults.filter(r => r.testId.includes(testType.name)).length;
      const passedTests = this.testResults.filter(r => 
        r.testId.includes(testType.name) && r.status === 'passed'
      ).length;

      const severities = typeVulns.map(v => v.severity);
      const highestSeverity = this.getHighestSeverity(severities);

      summary[`${testType.name}Tests`] = {
        totalTests,
        passedTests,
        vulnerabilities: typeVulns.length,
        highestSeverity
      };
    });

    return summary as TestSummary;
  }

  // 生成安全建議
  private generateSecurityRecommendations(): string[] {
    const recommendations: string[] = [];

    if (this.vulnerabilities.filter(v => v.severity === SeverityLevel.CRITICAL).length > 0) {
      recommendations.push('立即修復所有關鍵漏洞，這些可能導致嚴重安全事故');
    }

    if (this.vulnerabilities.filter(v => v.type === VulnerabilityType.XSS).length > 0) {
      recommendations.push('實施完整的輸入驗證和輸出編碼來防範 XSS 攻擊');
    }

    if (this.vulnerabilities.filter(v => v.type === VulnerabilityType.CSRF).length > 0) {
      recommendations.push('在所有狀態改變操作中實施 CSRF Token 保護');
    }

    if (this.vulnerabilities.filter(v => v.type === VulnerabilityType.CONTENT_SECURITY).length > 0) {
      recommendations.push('配置適當的 Content Security Policy 來增強內容安全');
    }

    if (this.vulnerabilities.filter(v => v.type === VulnerabilityType.CONFIGURATION).length > 0) {
      recommendations.push('檢查並強化安全配置，包括 HTTP 安全標頭');
    }

    if (recommendations.length === 0) {
      recommendations.push('繼續保持良好的安全實踐，定期進行安全測試');
    }

    return recommendations;
  }

  // 輔助方法
  private getHeaderImpact(header: string): string {
    switch (header) {
      case 'X-Frame-Options':
        return '可能遭受點擊劫持攻擊';
      case 'X-Content-Type-Options':
        return '可能遭受 MIME 類型混淆攻擊';
      case 'X-XSS-Protection':
        return '瀏覽器 XSS 保護未啟用';
      case 'Strict-Transport-Security':
        return '可能遭受降級攻擊和中間人攻擊';
      case 'Referrer-Policy':
        return '可能洩露敏感的引薦者信息';
      default:
        return '安全風險';
    }
  }

  private extractLibraryName(pathname: string): string | null {
    const parts = pathname.split('/');
    const filename = parts[parts.length - 1];
    
    if (filename.includes('jquery')) return 'jquery';
    if (filename.includes('bootstrap')) return 'bootstrap';
    if (filename.includes('angular')) return 'angular';
    if (filename.includes('react')) return 'react';
    if (filename.includes('vue')) return 'vue';
    
    return null;
  }

  private getHighestSeverity(severities: SeverityLevel[]): SeverityLevel {
    if (severities.includes(SeverityLevel.CRITICAL)) return SeverityLevel.CRITICAL;
    if (severities.includes(SeverityLevel.HIGH)) return SeverityLevel.HIGH;
    if (severities.includes(SeverityLevel.MEDIUM)) return SeverityLevel.MEDIUM;
    if (severities.includes(SeverityLevel.LOW)) return SeverityLevel.LOW;
    return SeverityLevel.INFO;
  }

  // 公共方法
  
  // 獲取所有漏洞
  getAllVulnerabilities(): Vulnerability[] {
    return [...this.vulnerabilities];
  }

  // 按類型獲取漏洞
  getVulnerabilitiesByType(type: VulnerabilityType): Vulnerability[] {
    return this.vulnerabilities.filter(v => v.type === type);
  }

  // 按嚴重性獲取漏洞
  getVulnerabilitiesBySeverity(severity: SeverityLevel): Vulnerability[] {
    return this.vulnerabilities.filter(v => v.severity === severity);
  }

  // 獲取最後報告 ID
  getLastReportId(): string | null {
    return this.lastReportId;
  }

  // 導出報告
  exportReport(report: PenetrationTestReport, format: 'json' | 'csv' | 'html' = 'json'): string {
    switch (format) {
      case 'json':
        return JSON.stringify(report, null, 2);
      
      case 'csv':
        const csvRows = ['Test ID,Test Name,Status,Vulnerabilities,Duration'];
        report.results.forEach(result => {
          csvRows.push(`"${result.testId}","${result.testName}","${result.status}",${result.vulnerabilities.length},${result.duration}`);
        });
        return csvRows.join('\n');
      
      case 'html':
        return this.generateHTMLReport(report);
      
      default:
        return JSON.stringify(report, null, 2);
    }
  }

  // 生成 HTML 報告
  private generateHTMLReport(report: PenetrationTestReport): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>滲透測試報告 - ${new Date(report.timestamp).toLocaleString()}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .vulnerability { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .critical { border-color: #d73527; background: #fff5f5; }
        .high { border-color: #fd7e14; background: #fff8f0; }
        .medium { border-color: #ffc107; background: #fffdf0; }
        .low { border-color: #28a745; background: #f8fff8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>滲透測試報告</h1>
        <p>報告ID: ${report.reportId}</p>
        <p>生成時間: ${new Date(report.timestamp).toLocaleString()}</p>
        <p>測試時間: ${(report.duration / 1000).toFixed(2)} 秒</p>
    </div>
    
    <div class="summary">
        <h2>測試摘要</h2>
        <ul>
            <li>總測試數: ${report.totalTests}</li>
            <li>通過測試: ${report.passedTests}</li>
            <li>失敗測試: ${report.failedTests}</li>
            <li>總漏洞數: ${report.totalVulnerabilities}</li>
            <li>風險分數: ${report.overallRiskScore}/100</li>
        </ul>
    </div>
    
    <div class="vulnerabilities">
        <h2>發現的漏洞</h2>
        ${report.results.map(result => 
          result.vulnerabilities.map(vuln => `
            <div class="vulnerability ${vuln.severity}">
                <h3>${vuln.title}</h3>
                <p><strong>類型:</strong> ${vuln.type}</p>
                <p><strong>嚴重性:</strong> ${vuln.severity}</p>
                <p><strong>描述:</strong> ${vuln.description}</p>
                <p><strong>位置:</strong> ${vuln.location}</p>
                <p><strong>修復建議:</strong> ${vuln.remediation}</p>
            </div>
          `).join('')
        ).join('')}
    </div>
</body>
</html>
    `;
  }
}

// 創建全域實例
export const penetrationTester = new PenetrationTester();

// 便利函數
export const runPenetrationTest = async (): Promise<PenetrationTestReport> => {
  return await penetrationTester.runFullPenetrationTest();
};

export const getVulnerabilityReport = (): Vulnerability[] => {
  return penetrationTester.getAllVulnerabilities();
};

export default penetrationTester;
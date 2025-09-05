/**
 * 合規檢查系統 - 第二階段Week 4 安全合規強化
 * GDPR、無障礙法規、金融監管合規檢查
 * 支援多維度合規檢查、自動化合規監控、合規報告生成
 */

// 合規法規類型
export enum ComplianceType {
  GDPR = 'gdpr',
  ACCESSIBILITY = 'accessibility',
  FINANCIAL = 'financial',
  PRIVACY = 'privacy',
  DATA_PROTECTION = 'data_protection'
}

// 合規級別
export enum ComplianceLevel {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info'
}

// 合規檢查結果狀態
export enum ComplianceStatus {
  COMPLIANT = 'compliant',
  NON_COMPLIANT = 'non_compliant',
  PARTIAL_COMPLIANT = 'partial_compliant',
  UNKNOWN = 'unknown',
  ERROR = 'error'
}

// 合規檢查項目
export interface ComplianceCheck {
  id: string;
  name: string;
  description: string;
  type: ComplianceType;
  level: ComplianceLevel;
  regulation: string;
  requirement: string;
  checkFunction: () => Promise<ComplianceResult>;
  autoFix?: () => Promise<boolean>;
}

// 合規檢查結果
export interface ComplianceResult {
  checkId: string;
  status: ComplianceStatus;
  score: number; // 0-100
  details: string;
  issues: ComplianceIssue[];
  recommendations: string[];
  evidence?: any;
  timestamp: number;
}

// 合規問題
export interface ComplianceIssue {
  severity: ComplianceLevel;
  location: string;
  description: string;
  regulation: string;
  remediation: string;
  autoFixable: boolean;
}

// 合規報告
export interface ComplianceReport {
  reportId: string;
  timestamp: number;
  overallScore: number;
  totalChecks: number;
  passedChecks: number;
  failedChecks: number;
  criticalIssues: number;
  highIssues: number;
  mediumIssues: number;
  lowIssues: number;
  summary: ComplianceSummary;
  results: ComplianceResult[];
  recommendations: string[];
}

// 合規摘要
export interface ComplianceSummary {
  gdpr: ComplianceTypeResult;
  accessibility: ComplianceTypeResult;
  financial: ComplianceTypeResult;
  privacy: ComplianceTypeResult;
  dataProtection: ComplianceTypeResult;
}

export interface ComplianceTypeResult {
  score: number;
  status: ComplianceStatus;
  criticalIssues: number;
  totalChecks: number;
  passedChecks: number;
}

// 合規檢查器類別
class ComplianceChecker {
  private checks: Map<string, ComplianceCheck> = new Map();
  private results: Map<string, ComplianceResult> = new Map();
  private lastReportId: string | null = null;

  constructor() {
    this.initializeChecks();
  }

  // 初始化合規檢查項目
  private initializeChecks() {
    // GDPR 檢查項目
    this.addGDPRChecks();
    
    // 無障礙檢查項目
    this.addAccessibilityChecks();
    
    // 金融監管檢查項目
    this.addFinancialChecks();
    
    // 隱私檢查項目
    this.addPrivacyChecks();
    
    // 數據保護檢查項目
    this.addDataProtectionChecks();
  }

  // 添加 GDPR 檢查項目
  private addGDPRChecks() {
    // Cookie 同意檢查
    this.addCheck({
      id: 'gdpr_cookie_consent',
      name: 'Cookie 同意機制',
      description: '檢查是否有適當的 Cookie 同意機制',
      type: ComplianceType.GDPR,
      level: ComplianceLevel.HIGH,
      regulation: 'GDPR Article 7',
      requirement: '必須獲得明確同意才能使用非必要 cookies',
      checkFunction: this.checkCookieConsent.bind(this),
      autoFix: this.fixCookieConsent.bind(this)
    });

    // 隱私政策檢查
    this.addCheck({
      id: 'gdpr_privacy_policy',
      name: '隱私政策',
      description: '檢查隱私政策的存在和內容完整性',
      type: ComplianceType.GDPR,
      level: ComplianceLevel.CRITICAL,
      regulation: 'GDPR Article 13-14',
      requirement: '必須提供清晰完整的隱私政策',
      checkFunction: this.checkPrivacyPolicy.bind(this)
    });

    // 數據處理透明度檢查
    this.addCheck({
      id: 'gdpr_data_transparency',
      name: '數據處理透明度',
      description: '檢查數據處理的透明度和用戶權利說明',
      type: ComplianceType.GDPR,
      level: ComplianceLevel.HIGH,
      regulation: 'GDPR Article 12',
      requirement: '必須清楚說明數據處理方式和用戶權利',
      checkFunction: this.checkDataTransparency.bind(this)
    });

    // 數據最小化檢查
    this.addCheck({
      id: 'gdpr_data_minimization',
      name: '數據最小化原則',
      description: '檢查是否遵循數據最小化原則',
      type: ComplianceType.GDPR,
      level: ComplianceLevel.MEDIUM,
      regulation: 'GDPR Article 5(1)(c)',
      requirement: '只收集和處理必要的個人數據',
      checkFunction: this.checkDataMinimization.bind(this)
    });

    // 用戶權利實施檢查
    this.addCheck({
      id: 'gdpr_user_rights',
      name: '用戶權利實施',
      description: '檢查用戶權利（存取、更正、刪除）的實施',
      type: ComplianceType.GDPR,
      level: ComplianceLevel.HIGH,
      regulation: 'GDPR Articles 15-22',
      requirement: '必須提供用戶權利行使機制',
      checkFunction: this.checkUserRights.bind(this)
    });
  }

  // 添加無障礙檢查項目
  private addAccessibilityChecks() {
    // WCAG 2.1 AA 檢查
    this.addCheck({
      id: 'a11y_wcag_aa',
      name: 'WCAG 2.1 AA 合規性',
      description: '檢查 WCAG 2.1 AA 級別合規性',
      type: ComplianceType.ACCESSIBILITY,
      level: ComplianceLevel.CRITICAL,
      regulation: 'WCAG 2.1',
      requirement: '必須符合 WCAG 2.1 AA 標準',
      checkFunction: this.checkWCAG.bind(this),
      autoFix: this.fixAccessibilityIssues.bind(this)
    });

    // 鍵盤導航檢查
    this.addCheck({
      id: 'a11y_keyboard_nav',
      name: '鍵盤導航',
      description: '檢查鍵盤導航功能',
      type: ComplianceType.ACCESSIBILITY,
      level: ComplianceLevel.HIGH,
      regulation: 'WCAG 2.1.1',
      requirement: '所有功能必須可通過鍵盤存取',
      checkFunction: this.checkKeyboardNavigation.bind(this)
    });

    // 螢幕閱讀器相容性檢查
    this.addCheck({
      id: 'a11y_screen_reader',
      name: '螢幕閱讀器相容性',
      description: '檢查螢幕閱讀器的相容性',
      type: ComplianceType.ACCESSIBILITY,
      level: ComplianceLevel.HIGH,
      regulation: 'WCAG 4.1.2',
      requirement: '必須與輔助技術相容',
      checkFunction: this.checkScreenReaderCompatibility.bind(this)
    });

    // 色彩對比檢查
    this.addCheck({
      id: 'a11y_color_contrast',
      name: '色彩對比度',
      description: '檢查文字和背景的色彩對比度',
      type: ComplianceType.ACCESSIBILITY,
      level: ComplianceLevel.MEDIUM,
      regulation: 'WCAG 1.4.3',
      requirement: '文字對比度必須至少為 4.5:1',
      checkFunction: this.checkColorContrast.bind(this),
      autoFix: this.fixColorContrast.bind(this)
    });

    // 替代文字檢查
    this.addCheck({
      id: 'a11y_alt_text',
      name: '圖片替代文字',
      description: '檢查圖片是否有適當的替代文字',
      type: ComplianceType.ACCESSIBILITY,
      level: ComplianceLevel.MEDIUM,
      regulation: 'WCAG 1.1.1',
      requirement: '所有有意義的圖片必須有替代文字',
      checkFunction: this.checkAltText.bind(this),
      autoFix: this.fixAltText.bind(this)
    });
  }

  // 添加金融監管檢查項目
  private addFinancialChecks() {
    // 風險披露檢查
    this.addCheck({
      id: 'finance_risk_disclosure',
      name: '風險披露',
      description: '檢查投資風險披露的完整性',
      type: ComplianceType.FINANCIAL,
      level: ComplianceLevel.CRITICAL,
      regulation: 'MiFID II',
      requirement: '必須清楚披露所有投資風險',
      checkFunction: this.checkRiskDisclosure.bind(this)
    });

    // 客戶適當性評估檢查
    this.addCheck({
      id: 'finance_suitability',
      name: '客戶適當性評估',
      description: '檢查客戶適當性評估機制',
      type: ComplianceType.FINANCIAL,
      level: ComplianceLevel.HIGH,
      regulation: 'MiFID II Article 25',
      requirement: '必須評估客戶的投資適當性',
      checkFunction: this.checkSuitabilityAssessment.bind(this)
    });

    // 交易記錄檢查
    this.addCheck({
      id: 'finance_trade_records',
      name: '交易記錄保存',
      description: '檢查交易記錄的完整性和保存期限',
      type: ComplianceType.FINANCIAL,
      level: ComplianceLevel.HIGH,
      regulation: 'MiFID II Article 25(2)',
      requirement: '必須保存完整的交易記錄',
      checkFunction: this.checkTradeRecords.bind(this)
    });

    // 反洗錢檢查
    this.addCheck({
      id: 'finance_aml',
      name: '反洗錢合規',
      description: '檢查反洗錢措施的實施',
      type: ComplianceType.FINANCIAL,
      level: ComplianceLevel.CRITICAL,
      regulation: 'AML Directive',
      requirement: '必須實施有效的反洗錢措施',
      checkFunction: this.checkAMLCompliance.bind(this)
    });

    // 資本充足性檢查
    this.addCheck({
      id: 'finance_capital_adequacy',
      name: '資本充足性',
      description: '檢查資本充足性要求',
      type: ComplianceType.FINANCIAL,
      level: ComplianceLevel.HIGH,
      regulation: 'CRR/CRD IV',
      requirement: '必須維持適當的資本比率',
      checkFunction: this.checkCapitalAdequacy.bind(this)
    });
  }

  // 添加隱私檢查項目
  private addPrivacyChecks() {
    // 個人數據加密檢查
    this.addCheck({
      id: 'privacy_data_encryption',
      name: '個人數據加密',
      description: '檢查個人數據的加密保護',
      type: ComplianceType.PRIVACY,
      level: ComplianceLevel.CRITICAL,
      regulation: 'GDPR Article 32',
      requirement: '個人數據必須適當加密保護',
      checkFunction: this.checkDataEncryption.bind(this)
    });

    // 數據傳輸安全檢查
    this.addCheck({
      id: 'privacy_secure_transmission',
      name: '數據傳輸安全',
      description: '檢查數據傳輸的安全性',
      type: ComplianceType.PRIVACY,
      level: ComplianceLevel.HIGH,
      regulation: 'GDPR Article 32',
      requirement: '數據傳輸必須使用安全加密',
      checkFunction: this.checkSecureTransmission.bind(this)
    });

    // 第三方數據共享檢查
    this.addCheck({
      id: 'privacy_third_party_sharing',
      name: '第三方數據共享',
      description: '檢查與第三方的數據共享合規性',
      type: ComplianceType.PRIVACY,
      level: ComplianceLevel.HIGH,
      regulation: 'GDPR Article 28',
      requirement: '第三方數據共享必須有適當協議',
      checkFunction: this.checkThirdPartySharing.bind(this)
    });
  }

  // 添加數據保護檢查項目
  private addDataProtectionChecks() {
    // 數據備份檢查
    this.addCheck({
      id: 'data_backup',
      name: '數據備份機制',
      description: '檢查數據備份和恢復機制',
      type: ComplianceType.DATA_PROTECTION,
      level: ComplianceLevel.HIGH,
      regulation: 'ISO 27001',
      requirement: '必須有定期數據備份機制',
      checkFunction: this.checkDataBackup.bind(this)
    });

    // 數據存取控制檢查
    this.addCheck({
      id: 'data_access_control',
      name: '數據存取控制',
      description: '檢查數據存取權限控制',
      type: ComplianceType.DATA_PROTECTION,
      level: ComplianceLevel.CRITICAL,
      regulation: 'GDPR Article 32',
      requirement: '必須有適當的存取權限控制',
      checkFunction: this.checkAccessControl.bind(this)
    });

    // 數據保留政策檢查
    this.addCheck({
      id: 'data_retention_policy',
      name: '數據保留政策',
      description: '檢查數據保留和刪除政策',
      type: ComplianceType.DATA_PROTECTION,
      level: ComplianceLevel.MEDIUM,
      regulation: 'GDPR Article 5(1)(e)',
      requirement: '數據保留時間不得超過必要期限',
      checkFunction: this.checkDataRetention.bind(this)
    });
  }

  // 添加檢查項目
  addCheck(check: ComplianceCheck) {
    this.checks.set(check.id, check);
  }

  // 執行單一檢查
  async runCheck(checkId: string): Promise<ComplianceResult> {
    const check = this.checks.get(checkId);
    if (!check) {
      throw new Error(`Check not found: ${checkId}`);
    }

    try {
      console.log(`[ComplianceChecker] Running check: ${check.name}`);
      const result = await check.checkFunction();
      this.results.set(checkId, result);
      return result;
    } catch (error) {
      const errorResult: ComplianceResult = {
        checkId,
        status: ComplianceStatus.ERROR,
        score: 0,
        details: `Check execution failed: ${error.message}`,
        issues: [],
        recommendations: ['修復檢查執行錯誤後重新運行'],
        timestamp: Date.now()
      };
      this.results.set(checkId, errorResult);
      return errorResult;
    }
  }

  // 執行所有檢查
  async runAllChecks(): Promise<ComplianceReport> {
    console.log('[ComplianceChecker] Running all compliance checks');
    
    const results: ComplianceResult[] = [];
    const checkPromises = Array.from(this.checks.keys()).map(async (checkId) => {
      return await this.runCheck(checkId);
    });

    const checkResults = await Promise.allSettled(checkPromises);
    
    checkResults.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      } else {
        const checkId = Array.from(this.checks.keys())[index];
        results.push({
          checkId,
          status: ComplianceStatus.ERROR,
          score: 0,
          details: `Check failed: ${result.reason}`,
          issues: [],
          recommendations: ['檢查系統錯誤並重新運行'],
          timestamp: Date.now()
        });
      }
    });

    return this.generateReport(results);
  }

  // 執行特定類型檢查
  async runChecksByType(type: ComplianceType): Promise<ComplianceResult[]> {
    const typeChecks = Array.from(this.checks.entries())
      .filter(([_, check]) => check.type === type);

    const results: ComplianceResult[] = [];
    
    for (const [checkId, _] of typeChecks) {
      const result = await this.runCheck(checkId);
      results.push(result);
    }

    return results;
  }

  // 生成合規報告
  private generateReport(results: ComplianceResult[]): ComplianceReport {
    const reportId = `compliance-${Date.now()}`;
    this.lastReportId = reportId;

    const totalChecks = results.length;
    const passedChecks = results.filter(r => r.status === ComplianceStatus.COMPLIANT).length;
    const failedChecks = results.filter(r => r.status === ComplianceStatus.NON_COMPLIANT).length;

    // 計算問題統計
    let criticalIssues = 0;
    let highIssues = 0;
    let mediumIssues = 0;
    let lowIssues = 0;

    results.forEach(result => {
      result.issues.forEach(issue => {
        switch (issue.severity) {
          case ComplianceLevel.CRITICAL:
            criticalIssues++;
            break;
          case ComplianceLevel.HIGH:
            highIssues++;
            break;
          case ComplianceLevel.MEDIUM:
            mediumIssues++;
            break;
          case ComplianceLevel.LOW:
            lowIssues++;
            break;
        }
      });
    });

    // 計算整體分數
    const totalScore = results.reduce((sum, result) => sum + result.score, 0);
    const overallScore = totalChecks > 0 ? totalScore / totalChecks : 0;

    // 生成各類型摘要
    const summary = this.generateSummary(results);

    // 生成建議
    const recommendations = this.generateRecommendations(results);

    return {
      reportId,
      timestamp: Date.now(),
      overallScore,
      totalChecks,
      passedChecks,
      failedChecks,
      criticalIssues,
      highIssues,
      mediumIssues,
      lowIssues,
      summary,
      results,
      recommendations
    };
  }

  // 生成各類型摘要
  private generateSummary(results: ComplianceResult[]): ComplianceSummary {
    const types = Object.values(ComplianceType);
    const summary: any = {};

    types.forEach(type => {
      const typeResults = results.filter(r => {
        const check = this.checks.get(r.checkId);
        return check?.type === type;
      });

      const totalChecks = typeResults.length;
      const passedChecks = typeResults.filter(r => r.status === ComplianceStatus.COMPLIANT).length;
      const criticalIssues = typeResults.reduce((sum, r) => 
        sum + r.issues.filter(i => i.severity === ComplianceLevel.CRITICAL).length, 0);
      
      const totalScore = typeResults.reduce((sum, r) => sum + r.score, 0);
      const score = totalChecks > 0 ? totalScore / totalChecks : 0;
      
      let status = ComplianceStatus.COMPLIANT;
      if (criticalIssues > 0) {
        status = ComplianceStatus.NON_COMPLIANT;
      } else if (passedChecks < totalChecks) {
        status = ComplianceStatus.PARTIAL_COMPLIANT;
      }

      summary[type] = {
        score,
        status,
        criticalIssues,
        totalChecks,
        passedChecks
      };
    });

    return summary as ComplianceSummary;
  }

  // 生成建議
  private generateRecommendations(results: ComplianceResult[]): string[] {
    const recommendations = new Set<string>();

    results.forEach(result => {
      result.recommendations.forEach(rec => recommendations.add(rec));
    });

    // 添加基於問題統計的一般建議
    const criticalIssues = results.reduce((sum, r) => 
      sum + r.issues.filter(i => i.severity === ComplianceLevel.CRITICAL).length, 0);
    
    if (criticalIssues > 0) {
      recommendations.add('優先處理所有關鍵合規問題，這些可能導致法律責任');
    }

    const failedChecks = results.filter(r => r.status === ComplianceStatus.NON_COMPLIANT).length;
    if (failedChecks > results.length * 0.3) {
      recommendations.add('建議進行全面的合規性審查和改進計劃');
    }

    return Array.from(recommendations);
  }

  // ====== GDPR 檢查實施 ======

  private async checkCookieConsent(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查 Cookie 同意橫幅
    const consentBanner = document.querySelector('[data-consent-banner], .cookie-consent, .consent-banner');
    if (!consentBanner) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'document',
        description: '未找到 Cookie 同意橫幅',
        regulation: 'GDPR Article 7',
        remediation: '添加 Cookie 同意橫幅和管理機制',
        autoFixable: true
      });
      score -= 40;
    }

    // 檢查同意選項
    const acceptButton = document.querySelector('[data-consent-accept], .consent-accept');
    const rejectButton = document.querySelector('[data-consent-reject], .consent-reject');
    
    if (acceptButton && !rejectButton) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'consent banner',
        description: '缺少拒絕 Cookie 的選項',
        regulation: 'GDPR Article 7(4)',
        remediation: '提供明確的拒絕選項',
        autoFixable: true
      });
      score -= 30;
    }

    // 檢查 Cookie 政策連結
    const policyLink = document.querySelector('a[href*="cookie"], a[href*="privacy"]');
    if (!policyLink) {
      issues.push({
        severity: ComplianceLevel.MEDIUM,
        location: 'consent banner',
        description: '缺少 Cookie 政策連結',
        regulation: 'GDPR Article 12',
        remediation: '添加 Cookie 政策頁面連結',
        autoFixable: false
      });
      score -= 20;
    }

    return {
      checkId: 'gdpr_cookie_consent',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.NON_COMPLIANT,
      score: Math.max(0, score),
      details: `Cookie 同意機制檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['實施完整的 Cookie 同意管理系統', '提供明確的接受和拒絕選項', '添加詳細的 Cookie 政策說明'] :
        ['Cookie 同意機制符合 GDPR 要求'],
      timestamp: Date.now()
    };
  }

  private async checkPrivacyPolicy(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查隱私政策頁面
    const privacyLinks = document.querySelectorAll('a[href*="privacy"], a[href*="隱私"]');
    if (privacyLinks.length === 0) {
      issues.push({
        severity: ComplianceLevel.CRITICAL,
        location: 'document',
        description: '未找到隱私政策連結',
        regulation: 'GDPR Article 13',
        remediation: '添加隱私政策頁面和連結',
        autoFixable: false
      });
      score -= 50;
    }

    // 模擬檢查隱私政策內容（實際應用中需要抓取頁面內容）
    try {
      const response = await fetch('/privacy-policy');
      if (!response.ok) {
        issues.push({
          severity: ComplianceLevel.CRITICAL,
          location: '/privacy-policy',
          description: '隱私政策頁面不可存取',
          regulation: 'GDPR Article 12',
          remediation: '確保隱私政策頁面可正常存取',
          autoFixable: false
        });
        score -= 40;
      }
    } catch (error) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: '/privacy-policy',
        description: '無法驗證隱私政策頁面',
        regulation: 'GDPR Article 12',
        remediation: '檢查隱私政策頁面的可用性',
        autoFixable: false
      });
      score -= 30;
    }

    return {
      checkId: 'gdpr_privacy_policy',
      status: issues.filter(i => i.severity === ComplianceLevel.CRITICAL).length > 0 ? 
        ComplianceStatus.NON_COMPLIANT : 
        (issues.length > 0 ? ComplianceStatus.PARTIAL_COMPLIANT : ComplianceStatus.COMPLIANT),
      score: Math.max(0, score),
      details: `隱私政策檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['建立完整的隱私政策頁面', '確保隱私政策內容符合 GDPR 要求', '提供清晰易懂的隱私說明'] :
        ['隱私政策符合基本要求'],
      timestamp: Date.now()
    };
  }

  private async checkDataTransparency(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查數據處理說明
    const dataProcessingInfo = document.querySelector('[data-processing-info], .data-processing, .data-usage');
    if (!dataProcessingInfo) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'document',
        description: '缺少數據處理透明度說明',
        regulation: 'GDPR Article 12',
        remediation: '添加清晰的數據處理說明',
        autoFixable: false
      });
      score -= 40;
    }

    // 檢查用戶權利說明
    const userRightsInfo = document.querySelector('[data-user-rights], .user-rights, .data-rights');
    if (!userRightsInfo) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'document',
        description: '缺少用戶權利說明',
        regulation: 'GDPR Articles 15-22',
        remediation: '添加用戶權利行使說明',
        autoFixable: false
      });
      score -= 30;
    }

    return {
      checkId: 'gdpr_data_transparency',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.NON_COMPLIANT,
      score: Math.max(0, score),
      details: `數據處理透明度檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['提供清晰的數據處理說明', '說明用戶的各項權利', '確保資訊易於理解'] :
        ['數據處理透明度符合要求'],
      timestamp: Date.now()
    };
  }

  private async checkDataMinimization(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查表單欄位
    const forms = document.querySelectorAll('form');
    forms.forEach((form, index) => {
      const inputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"], textarea');
      
      inputs.forEach(input => {
        const element = input as HTMLInputElement;
        if (element.required && !element.dataset.necessary) {
          issues.push({
            severity: ComplianceLevel.MEDIUM,
            location: `form[${index}] input[${element.name || element.id}]`,
            description: '必填欄位未標明必要性',
            regulation: 'GDPR Article 5(1)(c)',
            remediation: '標明數據收集的必要性或改為選填',
            autoFixable: false
          });
          score -= 10;
        }
      });
    });

    return {
      checkId: 'gdpr_data_minimization',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.PARTIAL_COMPLIANT,
      score: Math.max(0, score),
      details: `數據最小化檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['審查所有數據收集需求', '移除非必要的數據欄位', '清楚標明數據收集的目的'] :
        ['數據收集符合最小化原則'],
      timestamp: Date.now()
    };
  }

  private async checkUserRights(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查用戶權利頁面或功能
    const rightsPage = document.querySelector('a[href*="rights"], a[href*="權利"]');
    if (!rightsPage) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'document',
        description: '未找到用戶權利頁面連結',
        regulation: 'GDPR Articles 15-22',
        remediation: '添加用戶權利頁面和行使機制',
        autoFixable: false
      });
      score -= 40;
    }

    // 檢查帳戶設定中的隱私控制
    const privacySettings = document.querySelector('[data-privacy-settings], .privacy-controls, .account-privacy');
    if (!privacySettings) {
      issues.push({
        severity: ComplianceLevel.MEDIUM,
        location: 'account settings',
        description: '帳戶設定中缺少隱私控制選項',
        regulation: 'GDPR Article 20',
        remediation: '在帳戶設定中添加隱私控制功能',
        autoFixable: false
      });
      score -= 25;
    }

    return {
      checkId: 'gdpr_user_rights',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.NON_COMPLIANT,
      score: Math.max(0, score),
      details: `用戶權利實施檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['建立完整的用戶權利行使機制', '提供資料存取和修正功能', '實施資料可攜權和刪除權'] :
        ['用戶權利實施符合要求'],
      timestamp: Date.now()
    };
  }

  // ====== 無障礙檢查實施 ======

  private async checkWCAG(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查 HTML lang 屬性
    const html = document.documentElement;
    if (!html.lang) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'html',
        description: '缺少語言屬性',
        regulation: 'WCAG 3.1.1',
        remediation: '在 <html> 標籤添加 lang 屬性',
        autoFixable: true
      });
      score -= 20;
    }

    // 檢查頁面標題
    const title = document.title;
    if (!title || title.trim() === '') {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'head',
        description: '缺少頁面標題',
        regulation: 'WCAG 2.4.2',
        remediation: '添加描述性的頁面標題',
        autoFixable: true
      });
      score -= 20;
    }

    // 檢查標題結構
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let hasH1 = false;
    let previousLevel = 0;

    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName[1]);
      
      if (level === 1) {
        if (hasH1) {
          issues.push({
            severity: ComplianceLevel.MEDIUM,
            location: `heading[${index}]`,
            description: '頁面有多個 H1 標題',
            regulation: 'WCAG 1.3.1',
            remediation: '每頁只使用一個 H1 標題',
            autoFixable: true
          });
          score -= 10;
        }
        hasH1 = true;
      }

      if (previousLevel > 0 && level > previousLevel + 1) {
        issues.push({
          severity: ComplianceLevel.MEDIUM,
          location: `heading[${index}]`,
          description: '標題層級跳躍',
          regulation: 'WCAG 1.3.1',
          remediation: '使用連續的標題層級',
          autoFixable: true
        });
        score -= 10;
      }

      previousLevel = level;
    });

    if (!hasH1) {
      issues.push({
        severity: ComplianceLevel.HIGH,
        location: 'document',
        description: '缺少 H1 主標題',
        regulation: 'WCAG 1.3.1',
        remediation: '添加 H1 主標題',
        autoFixable: true
      });
      score -= 15;
    }

    return {
      checkId: 'a11y_wcag_aa',
      status: issues.filter(i => i.severity === ComplianceLevel.HIGH).length > 0 ? 
        ComplianceStatus.NON_COMPLIANT : 
        (issues.length > 0 ? ComplianceStatus.PARTIAL_COMPLIANT : ComplianceStatus.COMPLIANT),
      score: Math.max(0, score),
      details: `WCAG 2.1 AA 合規性檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['修正所有無障礙問題', '實施完整的 WCAG 2.1 AA 標準', '進行無障礙測試'] :
        ['基本 WCAG 要求符合標準'],
      timestamp: Date.now()
    };
  }

  private async checkKeyboardNavigation(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查可聚焦元素
    const focusableElements = document.querySelectorAll(
      'a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
    );

    focusableElements.forEach((element, index) => {
      const el = element as HTMLElement;
      
      // 檢查是否有可見焦點指示
      const computedStyle = window.getComputedStyle(el, ':focus');
      if (!computedStyle.outline || computedStyle.outline === 'none') {
        issues.push({
          severity: ComplianceLevel.MEDIUM,
          location: `focusable[${index}]`,
          description: '缺少鍵盤焦點指示',
          regulation: 'WCAG 2.4.7',
          remediation: '添加清楚的焦點指示樣式',
          autoFixable: true
        });
        score -= 5;
      }

      // 檢查 tabindex 使用
      const tabIndex = el.getAttribute('tabindex');
      if (tabIndex && parseInt(tabIndex) > 0) {
        issues.push({
          severity: ComplianceLevel.MEDIUM,
          location: `element[${index}]`,
          description: '使用正數 tabindex',
          regulation: 'WCAG 2.4.3',
          remediation: '避免使用正數 tabindex',
          autoFixable: true
        });
        score -= 10;
      }
    });

    return {
      checkId: 'a11y_keyboard_nav',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.PARTIAL_COMPLIANT,
      score: Math.max(0, score),
      details: `鍵盤導航檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['改善鍵盤焦點指示', '確保所有功能可用鍵盤操作', '避免使用正數 tabindex'] :
        ['鍵盤導航符合基本要求'],
      timestamp: Date.now()
    };
  }

  private async checkScreenReaderCompatibility(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查 ARIA 標籤
    const interactiveElements = document.querySelectorAll('button, input, select, textarea, [role]');
    
    interactiveElements.forEach((element, index) => {
      const el = element as HTMLElement;
      
      // 檢查是否有適當的標籤
      const hasLabel = el.labels?.length > 0 || 
                     el.getAttribute('aria-label') || 
                     el.getAttribute('aria-labelledby') ||
                     el.getAttribute('title');

      if (!hasLabel && el.tagName !== 'BUTTON') {
        issues.push({
          severity: ComplianceLevel.HIGH,
          location: `${el.tagName.toLowerCase()}[${index}]`,
          description: '缺少無障礙標籤',
          regulation: 'WCAG 4.1.2',
          remediation: '添加 aria-label 或相關標籤',
          autoFixable: true
        });
        score -= 15;
      }
    });

    // 檢查圖片 alt 屬性
    const images = document.querySelectorAll('img');
    images.forEach((img, index) => {
      if (!img.alt) {
        issues.push({
          severity: ComplianceLevel.MEDIUM,
          location: `img[${index}]`,
          description: '圖片缺少 alt 屬性',
          regulation: 'WCAG 1.1.1',
          remediation: '添加描述性的 alt 文字',
          autoFixable: false
        });
        score -= 10;
      }
    });

    return {
      checkId: 'a11y_screen_reader',
      status: issues.filter(i => i.severity === ComplianceLevel.HIGH).length > 0 ? 
        ComplianceStatus.NON_COMPLIANT : 
        (issues.length > 0 ? ComplianceStatus.PARTIAL_COMPLIANT : ComplianceStatus.COMPLIANT),
      score: Math.max(0, score),
      details: `螢幕閱讀器相容性檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['添加適當的 ARIA 標籤', '確保所有元素有無障礙標籤', '提供圖片的替代文字'] :
        ['螢幕閱讀器相容性良好'],
      timestamp: Date.now()
    };
  }

  private async checkColorContrast(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 獲取所有文字元素
    const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, a, button, label');
    
    textElements.forEach((element, index) => {
      const el = element as HTMLElement;
      const computedStyle = window.getComputedStyle(el);
      
      // 檢查是否有文字內容
      if (el.textContent?.trim()) {
        const color = computedStyle.color;
        const backgroundColor = computedStyle.backgroundColor;
        
        // 簡化的對比度檢查（實際應用中需要更精確的計算）
        if (color === backgroundColor || 
            (color === 'rgb(0, 0, 0)' && backgroundColor === 'rgba(0, 0, 0, 0)')) {
          issues.push({
            severity: ComplianceLevel.MEDIUM,
            location: `${el.tagName.toLowerCase()}[${index}]`,
            description: '文字顏色對比度可能不足',
            regulation: 'WCAG 1.4.3',
            remediation: '調整文字或背景顏色以提高對比度',
            autoFixable: true
          });
          score -= 10;
        }
      }
    });

    return {
      checkId: 'a11y_color_contrast',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.PARTIAL_COMPLIANT,
      score: Math.max(0, score),
      details: `色彩對比度檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['改善文字對比度至 4.5:1 以上', '使用對比度檢查工具驗證', '考慮深色模式的對比度'] :
        ['色彩對比度符合基本要求'],
      timestamp: Date.now()
    };
  }

  private async checkAltText(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    const images = document.querySelectorAll('img');
    
    images.forEach((img, index) => {
      if (!img.alt) {
        issues.push({
          severity: ComplianceLevel.MEDIUM,
          location: `img[${index}]`,
          description: '圖片缺少 alt 屬性',
          regulation: 'WCAG 1.1.1',
          remediation: '添加描述性的 alt 文字',
          autoFixable: false
        });
        score -= 15;
      } else if (img.alt.trim() === '') {
        // 裝飾性圖片應該有空的 alt 屬性
        if (!img.getAttribute('role') || img.getAttribute('role') !== 'presentation') {
          issues.push({
            severity: ComplianceLevel.LOW,
            location: `img[${index}]`,
            description: '圖片 alt 屬性為空但未標明為裝飾性',
            regulation: 'WCAG 1.1.1',
            remediation: '添加 role="presentation" 或提供 alt 文字',
            autoFixable: true
          });
          score -= 5;
        }
      }
    });

    return {
      checkId: 'a11y_alt_text',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.PARTIAL_COMPLIANT,
      score: Math.max(0, score),
      details: `圖片替代文字檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['為所有有意義的圖片添加 alt 文字', '裝飾性圖片使用空 alt 或 role="presentation"', '確保 alt 文字描述圖片內容'] :
        ['圖片替代文字符合要求'],
      timestamp: Date.now()
    };
  }

  // ====== 金融監管檢查實施 ======

  private async checkRiskDisclosure(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查風險披露頁面
    const riskDisclosure = document.querySelector('[data-risk-disclosure], .risk-warning, a[href*="risk"]');
    if (!riskDisclosure) {
      issues.push({
        severity: ComplianceLevel.CRITICAL,
        location: 'document',
        description: '未找到風險披露資訊',
        regulation: 'MiFID II',
        remediation: '添加完整的風險披露聲明',
        autoFixable: false
      });
      score -= 50;
    }

    // 檢查交易頁面的風險警告
    const tradingForms = document.querySelectorAll('[data-trading-form], .trading-form, form[action*="trade"]');
    tradingForms.forEach((form, index) => {
      const riskWarning = form.querySelector('.risk-warning, [data-risk-warning]');
      if (!riskWarning) {
        issues.push({
          severity: ComplianceLevel.HIGH,
          location: `trading-form[${index}]`,
          description: '交易表單缺少風險警告',
          regulation: 'MiFID II',
          remediation: '在交易表單添加清楚的風險警告',
          autoFixable: false
        });
        score -= 20;
      }
    });

    return {
      checkId: 'finance_risk_disclosure',
      status: issues.filter(i => i.severity === ComplianceLevel.CRITICAL).length > 0 ? 
        ComplianceStatus.NON_COMPLIANT : 
        (issues.length > 0 ? ComplianceStatus.PARTIAL_COMPLIANT : ComplianceStatus.COMPLIANT),
      score: Math.max(0, score),
      details: `風險披露檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['建立完整的風險披露頁面', '在所有交易界面添加風險警告', '確保風險資訊清楚易懂'] :
        ['風險披露符合監管要求'],
      timestamp: Date.now()
    };
  }

  private async checkSuitabilityAssessment(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端 API
    return {
      checkId: 'finance_suitability',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '客戶適當性評估需要後端系統檢查',
      issues: [],
      recommendations: ['實施完整的客戶適當性評估流程', '記錄客戶投資經驗和風險承受度', '定期更新適當性評估'],
      timestamp: Date.now()
    };
  }

  private async checkTradeRecords(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端系統
    return {
      checkId: 'finance_trade_records',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '交易記錄保存需要後端系統檢查',
      issues: [],
      recommendations: ['確保所有交易記錄完整保存', '實施交易記錄的定期備份', '建立交易記錄查詢機制'],
      timestamp: Date.now()
    };
  }

  private async checkAMLCompliance(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端系統
    return {
      checkId: 'finance_aml',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '反洗錢合規需要後端系統檢查',
      issues: [],
      recommendations: ['實施 KYC 客戶身份認證', '建立可疑交易監控機制', '定期進行 AML 合規審查'],
      timestamp: Date.now()
    };
  }

  private async checkCapitalAdequacy(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查財務系統
    return {
      checkId: 'finance_capital_adequacy',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '資本充足性需要財務系統檢查',
      issues: [],
      recommendations: ['監控資本比率', '實施風險管理措施', '定期報告監管機構'],
      timestamp: Date.now()
    };
  }

  // ====== 隱私檢查實施 ======

  private async checkDataEncryption(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查 HTTPS
    if (location.protocol !== 'https:') {
      issues.push({
        severity: ComplianceLevel.CRITICAL,
        location: 'protocol',
        description: '網站未使用 HTTPS',
        regulation: 'GDPR Article 32',
        remediation: '啟用 HTTPS 加密傳輸',
        autoFixable: false
      });
      score -= 40;
    }

    // 檢查表單的加密傳輸
    const forms = document.querySelectorAll('form');
    forms.forEach((form, index) => {
      if (form.action && !form.action.startsWith('https://') && !form.action.startsWith('/')) {
        issues.push({
          severity: ComplianceLevel.HIGH,
          location: `form[${index}]`,
          description: '表單提交未使用 HTTPS',
          regulation: 'GDPR Article 32',
          remediation: '確保表單數據通過 HTTPS 傳輸',
          autoFixable: true
        });
        score -= 20;
      }
    });

    return {
      checkId: 'privacy_data_encryption',
      status: issues.filter(i => i.severity === ComplianceLevel.CRITICAL).length > 0 ? 
        ComplianceStatus.NON_COMPLIANT : 
        (issues.length > 0 ? ComplianceStatus.PARTIAL_COMPLIANT : ComplianceStatus.COMPLIANT),
      score: Math.max(0, score),
      details: `數據加密檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['啟用全站 HTTPS', '確保所有數據傳輸加密', '實施端到端加密'] :
        ['數據加密符合基本要求'],
      timestamp: Date.now()
    };
  }

  private async checkSecureTransmission(): Promise<ComplianceResult> {
    // 與數據加密檢查類似，主要檢查傳輸安全
    return this.checkDataEncryption();
  }

  private async checkThirdPartySharing(): Promise<ComplianceResult> {
    const issues: ComplianceIssue[] = [];
    let score = 100;

    // 檢查第三方腳本
    const scripts = document.querySelectorAll('script[src]');
    const thirdPartyDomains = new Set<string>();

    scripts.forEach(script => {
      const src = script.getAttribute('src');
      if (src && !src.startsWith('/') && !src.startsWith(location.origin)) {
        try {
          const url = new URL(src);
          thirdPartyDomains.add(url.hostname);
        } catch (error) {
          // 忽略無效 URL
        }
      }
    });

    if (thirdPartyDomains.size > 0) {
      issues.push({
        severity: ComplianceLevel.MEDIUM,
        location: 'third-party-scripts',
        description: `發現 ${thirdPartyDomains.size} 個第三方域名：${Array.from(thirdPartyDomains).join(', ')}`,
        regulation: 'GDPR Article 28',
        remediation: '確保所有第三方服務都有適當的數據處理協議',
        autoFixable: false
      });
      score -= 20;
    }

    return {
      checkId: 'privacy_third_party_sharing',
      status: issues.length === 0 ? ComplianceStatus.COMPLIANT : ComplianceStatus.PARTIAL_COMPLIANT,
      score: Math.max(0, score),
      details: `第三方數據共享檢查完成，發現 ${issues.length} 個問題`,
      issues,
      recommendations: issues.length > 0 ? 
        ['審查所有第三方服務', '建立數據處理協議', '實施第三方風險評估'] :
        ['第三方數據共享控制良好'],
      timestamp: Date.now()
    };
  }

  // ====== 數據保護檢查實施 ======

  private async checkDataBackup(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端系統
    return {
      checkId: 'data_backup',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '數據備份機制需要後端系統檢查',
      issues: [],
      recommendations: ['實施定期數據備份', '測試數據恢復流程', '建立災難恢復計劃'],
      timestamp: Date.now()
    };
  }

  private async checkAccessControl(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端系統
    return {
      checkId: 'data_access_control',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '數據存取控制需要後端系統檢查',
      issues: [],
      recommendations: ['實施基於角色的存取控制', '定期審查存取權限', '記錄所有數據存取活動'],
      timestamp: Date.now()
    };
  }

  private async checkDataRetention(): Promise<ComplianceResult> {
    // 簡化實施 - 實際需要檢查後端系統和政策
    return {
      checkId: 'data_retention_policy',
      status: ComplianceStatus.UNKNOWN,
      score: 50,
      details: '數據保留政策需要系統和政策檢查',
      issues: [],
      recommendations: ['建立明確的數據保留政策', '實施自動數據清理', '記錄數據生命週期管理'],
      timestamp: Date.now()
    };
  }

  // ====== 自動修復功能 ======

  private async fixCookieConsent(): Promise<boolean> {
    try {
      // 創建基本的 Cookie 同意橫幅（示例）
      const banner = document.createElement('div');
      banner.className = 'cookie-consent-banner';
      banner.innerHTML = `
        <div class="cookie-consent-content">
          <p>我們使用 cookies 來改善您的體驗。請選擇您的偏好設定。</p>
          <div class="cookie-consent-buttons">
            <button data-consent-accept>接受所有</button>
            <button data-consent-reject>拒絕非必要</button>
            <a href="/cookie-policy">Cookie 政策</a>
          </div>
        </div>
      `;
      
      document.body.appendChild(banner);
      return true;
    } catch (error) {
      return false;
    }
  }

  private async fixAccessibilityIssues(): Promise<boolean> {
    try {
      let fixed = false;

      // 修復 HTML lang 屬性
      if (!document.documentElement.lang) {
        document.documentElement.lang = 'zh-TW';
        fixed = true;
      }

      // 為沒有 alt 的圖片添加空 alt（裝飾性圖片）
      const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
      imagesWithoutAlt.forEach(img => {
        img.setAttribute('alt', '');
        img.setAttribute('role', 'presentation');
        fixed = true;
      });

      return fixed;
    } catch (error) {
      return false;
    }
  }

  private async fixColorContrast(): Promise<boolean> {
    // 簡化實施 - 實際需要更複雜的顏色計算和調整
    return false;
  }

  private async fixAltText(): Promise<boolean> {
    try {
      const images = document.querySelectorAll('img:not([alt])');
      images.forEach(img => {
        // 為裝飾性圖片添加空 alt
        img.setAttribute('alt', '');
        img.setAttribute('role', 'presentation');
      });
      return images.length > 0;
    } catch (error) {
      return false;
    }
  }

  // ====== 公共方法 ======

  // 獲取最後報告
  getLastReport(): string | null {
    return this.lastReportId;
  }

  // 導出報告
  exportReport(report: ComplianceReport, format: 'json' | 'csv' | 'pdf' = 'json'): string {
    switch (format) {
      case 'json':
        return JSON.stringify(report, null, 2);
      
      case 'csv':
        // 簡化的 CSV 導出
        const csvRows = ['Check ID,Status,Score,Issues Count,Details'];
        report.results.forEach(result => {
          csvRows.push(`"${result.checkId}","${result.status}",${result.score},${result.issues.length},"${result.details}"`);
        });
        return csvRows.join('\n');
      
      default:
        return JSON.stringify(report, null, 2);
    }
  }

  // 獲取合規建議
  getComplianceAdvice(report: ComplianceReport): string[] {
    const advice: string[] = [];

    if (report.overallScore < 50) {
      advice.push('整體合規性需要重大改善，建議立即採取行動');
    } else if (report.overallScore < 80) {
      advice.push('合規性有待改善，建議制定改善計劃');
    } else {
      advice.push('合規性良好，繼續維持並定期檢查');
    }

    if (report.criticalIssues > 0) {
      advice.push(`發現 ${report.criticalIssues} 個關鍵問題，需要優先處理`);
    }

    return advice;
  }
}

// 創建全域實例
export const complianceChecker = new ComplianceChecker();

// 便利函數
export const runComplianceCheck = async (type?: ComplianceType): Promise<ComplianceReport | ComplianceResult[]> => {
  if (type) {
    return await complianceChecker.runChecksByType(type);
  }
  return await complianceChecker.runAllChecks();
};

export const getComplianceReport = async (): Promise<ComplianceReport> => {
  return await complianceChecker.runAllChecks();
};

export default complianceChecker;
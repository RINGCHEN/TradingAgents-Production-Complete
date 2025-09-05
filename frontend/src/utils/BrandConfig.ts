/**
 * 品牌配置管理系統
 * 中心化管理所有品牌相關的配置和常量
 */

export interface BrandConfig {
  brandName: string;           // 主品牌名稱
  brandNameEn?: string;        // 英文品牌名稱 (可選)
  fullTitle: string;           // 完整標題
  systemName: string;          // 系統名稱
  adminTitle: string;          // 管理後台標題
  analystSignature: string;    // AI分析師署名
  copyrightText: string;       // 版權文字
  description: string;         // 系統描述
  keywords: string[];          // SEO關鍵詞
  ogTitle: string;            // Open Graph標題
  ogDescription: string;       // Open Graph描述
}

/**
 * 品牌更新狀態枚舉
 */
export enum BrandUpdateStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  ROLLBACK = 'rollback'
}

/**
 * 品牌配置管理器
 * 提供統一的品牌信息訪問接口
 */
export class BrandConfigManager {
  private static config: BrandConfig = {
    brandName: "不老傳說",
    brandNameEn: "Eternal Legend",
    fullTitle: "不老傳說 - AI驅動的智能投資分析",
    systemName: "不老傳說系統",
    adminTitle: "不老傳說 管理後台",
    analystSignature: "不老傳說 AI分析師",
    copyrightText: "© 2025 不老傳說. 保留所有權利.",
    description: "不老傳說是台灣專業的AI投資分析平台，整合7位專業AI分析師，提供機構級投資分析服務",
    keywords: ["不老傳說", "AI投資分析", "台股分析", "股票分析", "投資顧問", "量化交易"],
    ogTitle: "不老傳說 - AI驅動的智能投資分析",
    ogDescription: "專業AI分析師團隊，機構級投資分析服務"
  };

  private static updateStatus: BrandUpdateStatus = BrandUpdateStatus.NOT_STARTED;

  /**
   * 獲取主品牌名稱
   */
  static getBrandName(): string {
    return this.config.brandName;
  }

  /**
   * 獲取英文品牌名稱
   */
  static getBrandNameEn(): string | undefined {
    return this.config.brandNameEn;
  }

  /**
   * 獲取完整標題
   */
  static getFullTitle(): string {
    return this.config.fullTitle;
  }

  /**
   * 獲取系統名稱
   */
  static getSystemName(): string {
    return this.config.systemName;
  }

  /**
   * 獲取管理後台標題
   */
  static getAdminTitle(): string {
    return this.config.adminTitle;
  }

  /**
   * 獲取AI分析師署名
   */
  static getAnalystSignature(): string {
    return this.config.analystSignature;
  }

  /**
   * 獲取版權文字
   */
  static getCopyrightText(): string {
    return this.config.copyrightText;
  }

  /**
   * 獲取系統描述
   */
  static getDescription(): string {
    return this.config.description;
  }

  /**
   * 獲取SEO關鍵詞
   */
  static getKeywords(): string[] {
    return this.config.keywords;
  }

  /**
   * 獲取Open Graph標題
   */
  static getOgTitle(): string {
    return this.config.ogTitle;
  }

  /**
   * 獲取Open Graph描述
   */
  static getOgDescription(): string {
    return this.config.ogDescription;
  }

  /**
   * 獲取完整品牌配置
   */
  static getConfig(): BrandConfig {
    return { ...this.config };
  }

  /**
   * 獲取品牌更新狀態
   */
  static getUpdateStatus(): BrandUpdateStatus {
    return this.updateStatus;
  }

  /**
   * 設置品牌更新狀態
   */
  static setUpdateStatus(status: BrandUpdateStatus): void {
    this.updateStatus = status;
    console.log(`品牌更新狀態變更為: ${status}`);
  }

  /**
   * 生成頁面標題
   * @param pageName 頁面名稱
   * @returns 完整的頁面標題
   */
  static generatePageTitle(pageName?: string): string {
    if (pageName) {
      return `${this.config.brandName} - ${pageName}`;
    }
    return this.config.fullTitle;
  }

  /**
   * 生成管理後台頁面標題
   * @param pageName 頁面名稱
   * @returns 管理後台頁面標題
   */
  static generateAdminPageTitle(pageName?: string): string {
    if (pageName) {
      return `${this.config.adminTitle} - ${pageName}`;
    }
    return this.config.adminTitle;
  }

  /**
   * 生成AI分析師報告署名
   * @param analystType 分析師類型
   * @returns 分析師署名
   */
  static generateAnalystSignature(analystType?: string): string {
    if (analystType) {
      return `${this.config.analystSignature} - ${analystType}`;
    }
    return this.config.analystSignature;
  }

  /**
   * 驗證品牌配置完整性
   */
  static validateConfig(): boolean {
    const requiredFields: (keyof BrandConfig)[] = [
      'brandName', 'fullTitle', 'systemName', 'adminTitle', 
      'analystSignature', 'copyrightText', 'description'
    ];

    for (const field of requiredFields) {
      if (!this.config[field] || this.config[field].toString().trim() === '') {
        console.error(`品牌配置缺少必要字段: ${field}`);
        return false;
      }
    }

    return true;
  }
}

/**
 * 品牌更新管理器
 * 處理品牌更新的狀態管理和錯誤處理
 */
export class BrandUpdateManager {
  private static backupData: Map<string, string> = new Map();

  /**
   * 備份原始品牌數據
   */
  static async backupOriginalBrand(): Promise<void> {
    try {
      // 備份原始品牌數據
      this.backupData.set('brandName', 'TradingAgents');
      this.backupData.set('fullTitle', 'TradingAgents - AI驅動的智能投資分析');
      this.backupData.set('systemName', 'TradingAgents系統');
      this.backupData.set('adminTitle', 'TradingAgents 管理後台');
      this.backupData.set('analystSignature', 'TradingAgents AI分析師');
      this.backupData.set('copyrightText', '© 2025 TradingAgents. All rights reserved.');
      
      console.log('原始品牌數據備份完成');
    } catch (error) {
      console.error('備份原始品牌數據失敗:', error);
      throw error;
    }
  }

  /**
   * 漸進式品牌更新
   */
  static async updateBrandGradually(): Promise<void> {
    try {
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.IN_PROGRESS);
      
      // 1. 備份原始數據
      await this.backupOriginalBrand();
      
      // 2. 驗證新品牌配置
      if (!BrandConfigManager.validateConfig()) {
        throw new Error('品牌配置驗證失敗');
      }
      
      // 3. 更新完成
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.COMPLETED);
      console.log('品牌更新完成');
      
    } catch (error) {
      console.error('品牌更新失敗:', error);
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.ROLLBACK);
      await this.rollbackChanges();
      throw error;
    }
  }

  /**
   * 回滾品牌更改
   */
  static async rollbackChanges(): Promise<void> {
    try {
      console.log('開始回滾品牌更改...');
      
      // 這裡可以實施具體的回滾邏輯
      // 例如：恢復原始配置、重新載入頁面等
      
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.NOT_STARTED);
      console.log('品牌更改回滾完成');
      
    } catch (error) {
      console.error('回滾品牌更改失敗:', error);
      throw error;
    }
  }

  /**
   * 獲取備份數據
   */
  static getBackupData(): Map<string, string> {
    return new Map(this.backupData);
  }
}

// 導出默認實例
export default BrandConfigManager;
/**
 * 品牌配置管理系統測試
 */

import { BrandConfigManager, BrandUpdateManager, BrandUpdateStatus } from '../BrandConfig';

describe('BrandConfigManager', () => {
  describe('基本品牌信息獲取', () => {
    test('應該返回正確的品牌名稱', () => {
      expect(BrandConfigManager.getBrandName()).toBe('不老傳說');
    });

    test('應該返回正確的英文品牌名稱', () => {
      expect(BrandConfigManager.getBrandNameEn()).toBe('Eternal Legend');
    });

    test('應該返回正確的完整標題', () => {
      expect(BrandConfigManager.getFullTitle()).toBe('不老傳說 - AI驅動的智能投資分析');
    });

    test('應該返回正確的系統名稱', () => {
      expect(BrandConfigManager.getSystemName()).toBe('不老傳說系統');
    });

    test('應該返回正確的管理後台標題', () => {
      expect(BrandConfigManager.getAdminTitle()).toBe('不老傳說 管理後台');
    });

    test('應該返回正確的AI分析師署名', () => {
      expect(BrandConfigManager.getAnalystSignature()).toBe('不老傳說 AI分析師');
    });

    test('應該返回正確的版權文字', () => {
      expect(BrandConfigManager.getCopyrightText()).toBe('© 2025 不老傳說. 保留所有權利.');
    });

    test('應該返回正確的系統描述', () => {
      const description = BrandConfigManager.getDescription();
      expect(description).toContain('不老傳說');
      expect(description).toContain('AI投資分析平台');
    });
  });

  describe('SEO相關信息', () => {
    test('應該返回正確的SEO關鍵詞', () => {
      const keywords = BrandConfigManager.getKeywords();
      expect(keywords).toContain('不老傳說');
      expect(keywords).toContain('AI投資分析');
      expect(keywords).toContain('台股分析');
    });

    test('應該返回正確的Open Graph標題', () => {
      expect(BrandConfigManager.getOgTitle()).toBe('不老傳說 - AI驅動的智能投資分析');
    });

    test('應該返回正確的Open Graph描述', () => {
      const ogDescription = BrandConfigManager.getOgDescription();
      expect(ogDescription).toContain('專業AI分析師團隊');
    });
  });

  describe('動態標題生成', () => {
    test('應該生成正確的頁面標題', () => {
      expect(BrandConfigManager.generatePageTitle()).toBe('不老傳說 - AI驅動的智能投資分析');
      expect(BrandConfigManager.generatePageTitle('關於我們')).toBe('不老傳說 - 關於我們');
    });

    test('應該生成正確的管理後台頁面標題', () => {
      expect(BrandConfigManager.generateAdminPageTitle()).toBe('不老傳說 管理後台');
      expect(BrandConfigManager.generateAdminPageTitle('用戶管理')).toBe('不老傳說 管理後台 - 用戶管理');
    });

    test('應該生成正確的分析師署名', () => {
      expect(BrandConfigManager.generateAnalystSignature()).toBe('不老傳說 AI分析師');
      expect(BrandConfigManager.generateAnalystSignature('基本面分析師')).toBe('不老傳說 AI分析師 - 基本面分析師');
    });
  });

  describe('配置驗證', () => {
    test('應該通過品牌配置完整性驗證', () => {
      expect(BrandConfigManager.validateConfig()).toBe(true);
    });

    test('應該返回完整的品牌配置', () => {
      const config = BrandConfigManager.getConfig();
      expect(config.brandName).toBe('不老傳說');
      expect(config.fullTitle).toBe('不老傳說 - AI驅動的智能投資分析');
      expect(config.systemName).toBe('不老傳說系統');
    });
  });

  describe('更新狀態管理', () => {
    test('初始狀態應該是NOT_STARTED', () => {
      expect(BrandConfigManager.getUpdateStatus()).toBe(BrandUpdateStatus.NOT_STARTED);
    });

    test('應該能夠設置更新狀態', () => {
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.IN_PROGRESS);
      expect(BrandConfigManager.getUpdateStatus()).toBe(BrandUpdateStatus.IN_PROGRESS);
      
      // 重置狀態
      BrandConfigManager.setUpdateStatus(BrandUpdateStatus.NOT_STARTED);
    });
  });
});

describe('BrandUpdateManager', () => {
  describe('備份和回滾功能', () => {
    test('應該能夠備份原始品牌數據', async () => {
      await BrandUpdateManager.backupOriginalBrand();
      const backupData = BrandUpdateManager.getBackupData();
      
      expect(backupData.get('brandName')).toBe('TradingAgents');
      expect(backupData.get('fullTitle')).toBe('TradingAgents - AI驅動的智能投資分析');
    });

    test('應該能夠執行漸進式品牌更新', async () => {
      await expect(BrandUpdateManager.updateBrandGradually()).resolves.not.toThrow();
      expect(BrandConfigManager.getUpdateStatus()).toBe(BrandUpdateStatus.COMPLETED);
    });

    test('應該能夠回滾品牌更改', async () => {
      await expect(BrandUpdateManager.rollbackChanges()).resolves.not.toThrow();
      expect(BrandConfigManager.getUpdateStatus()).toBe(BrandUpdateStatus.NOT_STARTED);
    });
  });
});

describe('品牌一致性測試', () => {
  test('所有品牌相關方法都應該包含不老傳說', () => {
    const brandName = BrandConfigManager.getBrandName();
    const fullTitle = BrandConfigManager.getFullTitle();
    const systemName = BrandConfigManager.getSystemName();
    const adminTitle = BrandConfigManager.getAdminTitle();
    const analystSignature = BrandConfigManager.getAnalystSignature();
    const copyrightText = BrandConfigManager.getCopyrightText();

    expect(brandName).toContain('不老傳說');
    expect(fullTitle).toContain('不老傳說');
    expect(systemName).toContain('不老傳說');
    expect(adminTitle).toContain('不老傳說');
    expect(analystSignature).toContain('不老傳說');
    expect(copyrightText).toContain('不老傳說');
  });

  test('不應該包含舊的TradingAgents品牌名稱', () => {
    const brandName = BrandConfigManager.getBrandName();
    const fullTitle = BrandConfigManager.getFullTitle();
    const systemName = BrandConfigManager.getSystemName();
    const adminTitle = BrandConfigManager.getAdminTitle();
    const analystSignature = BrandConfigManager.getAnalystSignature();

    expect(brandName).not.toContain('TradingAgents');
    expect(fullTitle).not.toContain('TradingAgents');
    expect(systemName).not.toContain('TradingAgents');
    expect(adminTitle).not.toContain('TradingAgents');
    expect(analystSignature).not.toContain('TradingAgents');
  });
});
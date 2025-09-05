/**
 * 品牌配置React Hook
 * 提供在React組件中使用品牌配置的便捷方式
 */

import { useEffect, useState } from 'react';
import BrandConfigManager, { BrandConfig, BrandUpdateStatus } from '../utils/BrandConfig';

/**
 * 品牌配置Hook返回類型
 */
export interface UseBrandConfigReturn {
  brandName: string;
  brandNameEn?: string;
  fullTitle: string;
  systemName: string;
  adminTitle: string;
  analystSignature: string;
  copyrightText: string;
  description: string;
  keywords: string[];
  ogTitle: string;
  ogDescription: string;
  updateStatus: BrandUpdateStatus;
  generatePageTitle: (pageName?: string) => string;
  generateAdminPageTitle: (pageName?: string) => string;
  generateAnalystSignature: (analystType?: string) => string;
  config: BrandConfig;
}

/**
 * 品牌配置Hook
 * 提供響應式的品牌配置訪問
 */
export const useBrandConfig = (): UseBrandConfigReturn => {
  const [config, setConfig] = useState<BrandConfig>(BrandConfigManager.getConfig());
  const [updateStatus, setUpdateStatus] = useState<BrandUpdateStatus>(
    BrandConfigManager.getUpdateStatus()
  );

  useEffect(() => {
    // 監聽品牌配置變更（如果需要的話）
    const checkForUpdates = () => {
      const currentConfig = BrandConfigManager.getConfig();
      const currentStatus = BrandConfigManager.getUpdateStatus();
      
      setConfig(currentConfig);
      setUpdateStatus(currentStatus);
    };

    // 設置定期檢查（可選）
    const interval = setInterval(checkForUpdates, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    brandName: config.brandName,
    brandNameEn: config.brandNameEn,
    fullTitle: config.fullTitle,
    systemName: config.systemName,
    adminTitle: config.adminTitle,
    analystSignature: config.analystSignature,
    copyrightText: config.copyrightText,
    description: config.description,
    keywords: config.keywords,
    ogTitle: config.ogTitle,
    ogDescription: config.ogDescription,
    updateStatus,
    generatePageTitle: BrandConfigManager.generatePageTitle.bind(BrandConfigManager),
    generateAdminPageTitle: BrandConfigManager.generateAdminPageTitle.bind(BrandConfigManager),
    generateAnalystSignature: BrandConfigManager.generateAnalystSignature.bind(BrandConfigManager),
    config
  };
};

/**
 * 頁面標題Hook
 * 專門用於管理頁面標題的Hook
 */
export const usePageTitle = (pageName?: string, isAdmin: boolean = false) => {
  const { generatePageTitle, generateAdminPageTitle } = useBrandConfig();
  
  const title = isAdmin 
    ? generateAdminPageTitle(pageName)
    : generatePageTitle(pageName);

  useEffect(() => {
    // 自動更新document.title
    document.title = title;
  }, [title]);

  return title;
};

/**
 * SEO元數據Hook
 * 提供SEO相關的元數據管理
 */
export const useSeoMetadata = (pageName?: string, customDescription?: string) => {
  const { fullTitle, description, keywords, ogTitle, ogDescription, generatePageTitle } = useBrandConfig();
  
  const pageTitle = generatePageTitle(pageName);
  const pageDescription = customDescription || description;
  
  useEffect(() => {
    // 更新頁面標題
    document.title = pageTitle;
    
    // 更新meta描述
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', pageDescription);
    }
    
    // 更新meta關鍵詞
    const metaKeywords = document.querySelector('meta[name="keywords"]');
    if (metaKeywords) {
      metaKeywords.setAttribute('content', keywords.join(', '));
    }
    
    // 更新Open Graph標籤
    const ogTitleMeta = document.querySelector('meta[property="og:title"]');
    if (ogTitleMeta) {
      ogTitleMeta.setAttribute('content', pageTitle);
    }
    
    const ogDescriptionMeta = document.querySelector('meta[property="og:description"]');
    if (ogDescriptionMeta) {
      ogDescriptionMeta.setAttribute('content', pageDescription);
    }
    
  }, [pageTitle, pageDescription, keywords, ogTitle, ogDescription]);

  return {
    title: pageTitle,
    description: pageDescription,
    keywords,
    ogTitle: pageTitle,
    ogDescription: pageDescription
  };
};

export default useBrandConfig;
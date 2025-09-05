/**
 * 國際化系統核心 - 第二階段Week 2 UX優化
 * 支援多語言翻譯、區域化適配、動態語言切換
 * 輕量級實現，無需外部依賴
 */

// 支援的語言類型
export type SupportedLocale = 'zh-TW' | 'zh-CN' | 'en-US' | 'ja-JP';

// 語言配置介面
export interface LanguageConfig {
  code: SupportedLocale;
  name: string;
  nativeName: string;
  flag: string;
  rtl: boolean;
  dateFormat: string;
  numberFormat: Intl.NumberFormatOptions;
  currencyFormat: Intl.NumberFormatOptions;
}

// 翻譯鍵的類型安全
export type TranslationKey = 
  | 'common.loading'
  | 'common.error'
  | 'common.success'
  | 'common.cancel'
  | 'common.confirm'
  | 'common.save'
  | 'common.delete'
  | 'common.edit'
  | 'common.add'
  | 'common.search'
  | 'common.filter'
  | 'common.export'
  | 'common.import'
  | 'common.refresh'
  | 'common.back'
  | 'common.next'
  | 'common.previous'
  | 'common.close'
  | 'common.open'
  | 'navigation.dashboard'
  | 'navigation.markets'
  | 'navigation.analysis'
  | 'navigation.portfolio'
  | 'navigation.news'
  | 'navigation.settings'
  | 'navigation.help'
  | 'navigation.profile'
  | 'navigation.logout'
  | 'auth.login'
  | 'auth.register'
  | 'auth.logout'
  | 'auth.username'
  | 'auth.password'
  | 'auth.email'
  | 'auth.forgotPassword'
  | 'auth.rememberMe'
  | 'auth.loginSuccess'
  | 'auth.loginFailed'
  | 'dashboard.title'
  | 'dashboard.overview'
  | 'dashboard.todayGains'
  | 'dashboard.totalValue'
  | 'dashboard.activePositions'
  | 'dashboard.marketStatus'
  | 'dashboard.topMovers'
  | 'dashboard.recentActivity'
  | 'markets.title'
  | 'markets.taiwanMarket'
  | 'markets.usMarket'
  | 'markets.cryptoMarket'
  | 'markets.searchStocks'
  | 'markets.marketCap'
  | 'markets.volume'
  | 'markets.change'
  | 'markets.changePercent'
  | 'analysis.title'
  | 'analysis.technicalAnalysis'
  | 'analysis.fundamentalAnalysis'
  | 'analysis.aiInsights'
  | 'analysis.recommendations'
  | 'analysis.riskLevel'
  | 'analysis.timeFrame'
  | 'portfolio.title'
  | 'portfolio.holdings'
  | 'portfolio.performance'
  | 'portfolio.allocation'
  | 'portfolio.transactions'
  | 'portfolio.buyOrder'
  | 'portfolio.sellOrder'
  | 'news.title'
  | 'news.marketNews'
  | 'news.companyNews'
  | 'news.economicNews'
  | 'news.filter'
  | 'news.source'
  | 'news.publishedAt'
  | 'admin.title'
  | 'admin.users'
  | 'admin.system'
  | 'admin.security'
  | 'admin.reports'
  | 'admin.settings'
  | 'error.networkError'
  | 'error.serverError'
  | 'error.notFound'
  | 'error.unauthorized'
  | 'error.forbidden'
  | 'error.timeout'
  | 'error.unknown';

// 翻譯資源類型
export type TranslationResources = Record<TranslationKey, string>;

// 語言配置
export const LANGUAGE_CONFIG: Record<SupportedLocale, LanguageConfig> = {
  'zh-TW': {
    code: 'zh-TW',
    name: 'Traditional Chinese',
    nativeName: '繁體中文',
    flag: '🇹🇼',
    rtl: false,
    dateFormat: 'YYYY/MM/DD',
    numberFormat: {},
    currencyFormat: { 
      style: 'currency', 
      currency: 'TWD'
    }
  },
  'zh-CN': {
    code: 'zh-CN',
    name: 'Simplified Chinese',
    nativeName: '简体中文',
    flag: '🇨🇳',
    rtl: false,
    dateFormat: 'YYYY年MM月DD日',
    numberFormat: {},
    currencyFormat: { 
      style: 'currency', 
      currency: 'CNY'
    }
  },
  'en-US': {
    code: 'en-US',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    rtl: false,
    dateFormat: 'MM/DD/YYYY',
    numberFormat: {},
    currencyFormat: { 
      style: 'currency', 
      currency: 'USD'
    }
  },
  'ja-JP': {
    code: 'ja-JP',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵',
    rtl: false,
    dateFormat: 'YYYY年MM月DD日',
    numberFormat: {},
    currencyFormat: { 
      style: 'currency', 
      currency: 'JPY'
    }
  }
};

// 國際化類別
class I18nManager {
  private currentLocale: SupportedLocale;
  private translations: Map<SupportedLocale, TranslationResources>;
  private fallbackLocale: SupportedLocale = 'zh-TW';
  private listeners: Array<(locale: SupportedLocale) => void> = [];

  constructor() {
    this.currentLocale = this.detectLocale();
    this.translations = new Map();
  }

  // 偵測用戶語言
  private detectLocale(): SupportedLocale {
    // 1. 檢查 localStorage 中的設定
    const savedLocale = localStorage.getItem('preferred-locale') as SupportedLocale;
    if (savedLocale && this.isValidLocale(savedLocale)) {
      return savedLocale;
    }

    // 2. 檢查瀏覽器語言
    const browserLang = navigator.language || (navigator as any).userLanguage;
    
    // 語言映射
    const langMap: Record<string, SupportedLocale> = {
      'zh-TW': 'zh-TW',
      'zh-Hant': 'zh-TW',
      'zh-CN': 'zh-CN',
      'zh-Hans': 'zh-CN',
      'zh': 'zh-TW', // 預設為繁體中文
      'en': 'en-US',
      'en-US': 'en-US',
      'ja': 'ja-JP',
      'ja-JP': 'ja-JP'
    };

    // 精確匹配
    if (langMap[browserLang]) {
      return langMap[browserLang];
    }

    // 部分匹配（例如 zh-HK -> zh-TW）
    const langPrefix = browserLang.split('-')[0];
    if (langMap[langPrefix]) {
      return langMap[langPrefix];
    }

    // 預設為繁體中文
    return 'zh-TW';
  }

  // 驗證語言代碼
  private isValidLocale(locale: string): locale is SupportedLocale {
    return Object.keys(LANGUAGE_CONFIG).includes(locale);
  }

  // 載入翻譯資源
  async loadTranslations(locale: SupportedLocale): Promise<void> {
    if (this.translations.has(locale)) {
      return;
    }

    try {
      // 動態載入翻譯文件
      const translations = await import(`../locales/${locale}.json`);
      this.translations.set(locale, translations.default);
    } catch (error) {
      console.warn(`Failed to load translations for ${locale}:`, error);
      
      // 如果載入失敗且不是後備語言，嘗試載入後備語言
      if (locale !== this.fallbackLocale) {
        await this.loadTranslations(this.fallbackLocale);
      }
    }
  }

  // 翻譯文本
  t(key: TranslationKey, params: Record<string, string | number> = {}): string {
    const translations = this.translations.get(this.currentLocale) || 
                        this.translations.get(this.fallbackLocale);
    
    if (!translations) {
      return key;
    }

    let text = translations[key] || key;

    // 參數替換
    Object.entries(params).forEach(([param, value]) => {
      const placeholder = `{{${param}}}`;
      text = text.replace(new RegExp(placeholder, 'g'), String(value));
    });

    return text;
  }

  // 獲取當前語言
  getCurrentLocale(): SupportedLocale {
    return this.currentLocale;
  }

  // 獲取語言配置
  getLanguageConfig(locale?: SupportedLocale): LanguageConfig {
    return LANGUAGE_CONFIG[locale || this.currentLocale];
  }

  // 獲取所有支援的語言
  getSupportedLanguages(): LanguageConfig[] {
    return Object.values(LANGUAGE_CONFIG);
  }

  // 切換語言
  async setLocale(locale: SupportedLocale): Promise<void> {
    if (!this.isValidLocale(locale)) {
      throw new Error(`Unsupported locale: ${locale}`);
    }

    await this.loadTranslations(locale);
    this.currentLocale = locale;
    
    // 保存到 localStorage
    localStorage.setItem('preferred-locale', locale);
    
    // 更新 HTML lang 屬性
    document.documentElement.lang = locale;
    
    // 更新 RTL 方向
    const config = LANGUAGE_CONFIG[locale];
    document.documentElement.dir = config.rtl ? 'rtl' : 'ltr';
    
    // 通知監聽器
    this.listeners.forEach(listener => listener(locale));
  }

  // 添加語言切換監聽器
  onLocaleChange(listener: (locale: SupportedLocale) => void): () => void {
    this.listeners.push(listener);
    
    // 返回取消訂閱函數
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  // 格式化日期
  formatDate(date: Date, format?: string): string {
    const config = this.getLanguageConfig();
    const formatter = new Intl.DateTimeFormat(config.code);
    return formatter.format(date);
  }

  // 格式化數字
  formatNumber(num: number, options?: Intl.NumberFormatOptions): string {
    const config = this.getLanguageConfig();
    const formatter = new Intl.NumberFormat(config.code, {
      ...config.numberFormat,
      ...options
    });
    return formatter.format(num);
  }

  // 格式化貨幣
  formatCurrency(amount: number, currency?: string): string {
    const config = this.getLanguageConfig();
    const formatter = new Intl.NumberFormat(config.code, {
      ...config.currencyFormat,
      ...(currency ? { currency } : {})
    });
    return formatter.format(amount);
  }

  // 格式化百分比
  formatPercent(value: number, options?: Intl.NumberFormatOptions): string {
    const config = this.getLanguageConfig();
    const formatter = new Intl.NumberFormat(config.code, {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      ...options
    });
    return formatter.format(value / 100);
  }

  // 相對時間格式化
  formatRelativeTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    const config = this.getLanguageConfig();
    
    try {
      const formatter = new Intl.RelativeTimeFormat(config.code, { numeric: 'auto' });
      
      if (diffDays > 0) {
        return formatter.format(-diffDays, 'day');
      } else if (diffHours > 0) {
        return formatter.format(-diffHours, 'hour');
      } else if (diffMinutes > 0) {
        return formatter.format(-diffMinutes, 'minute');
      } else {
        return formatter.format(-diffSeconds, 'second');
      }
    } catch (error) {
      // 後備方案
      if (diffDays > 0) return `${diffDays} ${this.t('common.daysAgo' as TranslationKey)}`;
      if (diffHours > 0) return `${diffHours} ${this.t('common.hoursAgo' as TranslationKey)}`;
      if (diffMinutes > 0) return `${diffMinutes} ${this.t('common.minutesAgo' as TranslationKey)}`;
      return this.t('common.justNow' as TranslationKey);
    }
  }

  // 初始化國際化系統
  async initialize(): Promise<void> {
    await this.loadTranslations(this.currentLocale);
    
    // 如果當前語言不是後備語言，也載入後備語言
    if (this.currentLocale !== this.fallbackLocale) {
      await this.loadTranslations(this.fallbackLocale);
    }

    // 設置 HTML 屬性
    document.documentElement.lang = this.currentLocale;
    const config = this.getLanguageConfig();
    document.documentElement.dir = config.rtl ? 'rtl' : 'ltr';
  }
}

// 創建全域實例
export const i18n = new I18nManager();

// 便利函數
export const t = (key: TranslationKey, params?: Record<string, string | number>) => 
  i18n.t(key, params);

export const getCurrentLocale = () => i18n.getCurrentLocale();
export const setLocale = (locale: SupportedLocale) => i18n.setLocale(locale);
export const getSupportedLanguages = () => i18n.getSupportedLanguages();
export const formatCurrency = (amount: number, currency?: string) => 
  i18n.formatCurrency(amount, currency);
export const formatPercent = (value: number) => i18n.formatPercent(value);
export const formatDate = (date: Date) => i18n.formatDate(date);
export const formatRelativeTime = (date: Date) => i18n.formatRelativeTime(date);

// 初始化
export const initializeI18n = () => i18n.initialize();

export default i18n;
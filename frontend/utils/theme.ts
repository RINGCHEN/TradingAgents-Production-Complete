/**
 * 主題系統核心 - 第二階段Week 2 UX優化
 * 個人化主題編輯器、自適應主題切換、無障礙主題支援
 * 支援深色模式、高對比度、自定義顏色方案
 */

// 支援的主題類型
export type ThemeMode = 'light' | 'dark' | 'auto' | 'high-contrast' | 'custom';

// 顏色調色盤定義
export interface ColorPalette {
  // 主要品牌色
  primary: string;
  primaryDark: string;
  primaryLight: string;
  
  // 次要色彩
  secondary: string;
  secondaryDark: string;
  secondaryLight: string;
  
  // 功能性顏色
  success: string;
  warning: string;
  error: string;
  info: string;
  
  // 背景色
  backgroundPrimary: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  
  // 文字色
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;
  
  // 邊框和分隔線
  border: string;
  borderLight: string;
  borderDark: string;
  
  // 表面顏色
  surface: string;
  surfaceHover: string;
  surfaceActive: string;
  
  // 陰影
  shadow: string;
  shadowLight: string;
  shadowDark: string;
}

// 主題配置介面
export interface ThemeConfig {
  mode: ThemeMode;
  name: string;
  displayName: string;
  colors: ColorPalette;
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
      '2xl': string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  borderRadius: {
    none: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    full: string;
  };
  animation: {
    duration: {
      fast: string;
      medium: string;
      slow: string;
    };
    easing: {
      linear: string;
      easeIn: string;
      easeOut: string;
      easeInOut: string;
    };
  };
}

// 預定義主題
export const THEME_PRESETS: Record<ThemeMode, ThemeConfig> = {
  light: {
    mode: 'light',
    name: 'light',
    displayName: '明亮主題',
    colors: {
      primary: '#3498db',
      primaryDark: '#2980b9',
      primaryLight: '#5dade2',
      secondary: '#95a5a6',
      secondaryDark: '#7f8c8d',
      secondaryLight: '#bdc3c7',
      success: '#27ae60',
      warning: '#f39c12',
      error: '#e74c3c',
      info: '#3498db',
      backgroundPrimary: '#ffffff',
      backgroundSecondary: '#f8f9fa',
      backgroundTertiary: '#ecf0f1',
      textPrimary: '#2c3e50',
      textSecondary: '#34495e',
      textTertiary: '#7f8c8d',
      textInverse: '#ffffff',
      border: '#dee2e6',
      borderLight: '#e9ecef',
      borderDark: '#ced4da',
      surface: '#ffffff',
      surfaceHover: '#f8f9fa',
      surfaceActive: '#e9ecef',
      shadow: 'rgba(0, 0, 0, 0.1)',
      shadowLight: 'rgba(0, 0, 0, 0.05)',
      shadowDark: 'rgba(0, 0, 0, 0.15)'
    },
    typography: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        md: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem'
      },
      fontWeight: {
        light: 300,
        normal: 400,
        medium: 500,
        semibold: 600,
        bold: 700
      },
      lineHeight: {
        tight: 1.25,
        normal: 1.5,
        relaxed: 1.75
      }
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      '2xl': '3rem',
      '3xl': '4rem'
    },
    borderRadius: {
      none: '0',
      sm: '0.25rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px'
    },
    animation: {
      duration: {
        fast: '150ms',
        medium: '300ms',
        slow: '500ms'
      },
      easing: {
        linear: 'linear',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
      }
    }
  },
  
  dark: {
    mode: 'dark',
    name: 'dark',
    displayName: '深色主題',
    colors: {
      primary: '#3498db',
      primaryDark: '#2980b9',
      primaryLight: '#5dade2',
      secondary: '#95a5a6',
      secondaryDark: '#7f8c8d',
      secondaryLight: '#bdc3c7',
      success: '#27ae60',
      warning: '#f39c12',
      error: '#e74c3c',
      info: '#3498db',
      backgroundPrimary: '#1a1a1a',
      backgroundSecondary: '#2d3748',
      backgroundTertiary: '#4a5568',
      textPrimary: '#f7fafc',
      textSecondary: '#e2e8f0',
      textTertiary: '#a0aec0',
      textInverse: '#2d3748',
      border: '#4a5568',
      borderLight: '#2d3748',
      borderDark: '#718096',
      surface: '#2d3748',
      surfaceHover: '#4a5568',
      surfaceActive: '#718096',
      shadow: 'rgba(0, 0, 0, 0.3)',
      shadowLight: 'rgba(0, 0, 0, 0.2)',
      shadowDark: 'rgba(0, 0, 0, 0.4)'
    },
    typography: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      fontSize: {
        xs: '0.75rem',
        sm: '0.875rem',
        md: '1rem',
        lg: '1.125rem',
        xl: '1.25rem',
        '2xl': '1.5rem'
      },
      fontWeight: {
        light: 300,
        normal: 400,
        medium: 500,
        semibold: 600,
        bold: 700
      },
      lineHeight: {
        tight: 1.25,
        normal: 1.5,
        relaxed: 1.75
      }
    },
    spacing: {
      xs: '0.25rem',
      sm: '0.5rem',
      md: '1rem',
      lg: '1.5rem',
      xl: '2rem',
      '2xl': '3rem',
      '3xl': '4rem'
    },
    borderRadius: {
      none: '0',
      sm: '0.25rem',
      md: '0.375rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px'
    },
    animation: {
      duration: {
        fast: '150ms',
        medium: '300ms',
        slow: '500ms'
      },
      easing: {
        linear: 'linear',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
      }
    }
  },

  auto: {
    mode: 'auto',
    name: 'auto',
    displayName: '跟隨系統',
    colors: {} as ColorPalette, // 會根據系統偏好動態選擇
    typography: {} as any,
    spacing: {} as any,
    borderRadius: {} as any,
    animation: {} as any
  },

  'high-contrast': {
    mode: 'high-contrast',
    name: 'high-contrast',
    displayName: '高對比度',
    colors: {
      primary: '#0066cc',
      primaryDark: '#004499',
      primaryLight: '#3388dd',
      secondary: '#666666',
      secondaryDark: '#333333',
      secondaryLight: '#999999',
      success: '#008800',
      warning: '#cc6600',
      error: '#cc0000',
      info: '#0066cc',
      backgroundPrimary: '#ffffff',
      backgroundSecondary: '#f0f0f0',
      backgroundTertiary: '#e0e0e0',
      textPrimary: '#000000',
      textSecondary: '#333333',
      textTertiary: '#666666',
      textInverse: '#ffffff',
      border: '#000000',
      borderLight: '#666666',
      borderDark: '#000000',
      surface: '#ffffff',
      surfaceHover: '#f0f0f0',
      surfaceActive: '#e0e0e0',
      shadow: 'rgba(0, 0, 0, 0.5)',
      shadowLight: 'rgba(0, 0, 0, 0.3)',
      shadowDark: 'rgba(0, 0, 0, 0.7)'
    },
    typography: {
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      fontSize: {
        xs: '0.875rem',
        sm: '1rem',
        md: '1.125rem',
        lg: '1.25rem',
        xl: '1.375rem',
        '2xl': '1.625rem'
      },
      fontWeight: {
        light: 400,
        normal: 500,
        medium: 600,
        semibold: 700,
        bold: 800
      },
      lineHeight: {
        tight: 1.5,
        normal: 1.75,
        relaxed: 2
      }
    },
    spacing: {
      xs: '0.375rem',
      sm: '0.75rem',
      md: '1.25rem',
      lg: '1.75rem',
      xl: '2.25rem',
      '2xl': '3.25rem',
      '3xl': '4.25rem'
    },
    borderRadius: {
      none: '0',
      sm: '0.125rem',
      md: '0.25rem',
      lg: '0.375rem',
      xl: '0.5rem',
      full: '9999px'
    },
    animation: {
      duration: {
        fast: '100ms',
        medium: '200ms',
        slow: '300ms'
      },
      easing: {
        linear: 'linear',
        easeIn: 'ease-in',
        easeOut: 'ease-out',
        easeInOut: 'ease-in-out'
      }
    }
  },

  custom: {
    mode: 'custom',
    name: 'custom',
    displayName: '自定義主題',
    colors: {} as ColorPalette, // 由用戶自定義
    typography: {} as any,
    spacing: {} as any,
    borderRadius: {} as any,
    animation: {} as any
  }
};

// 主題管理器
class ThemeManager {
  private currentTheme: ThemeConfig;
  // private customThemes: Map<string, ThemeConfig> = new Map(); // 保留供未來自定義主題功能使用
  private listeners: Array<(theme: ThemeConfig) => void> = [];
  private mediaQuery: MediaQueryList;

  constructor() {
    this.currentTheme = this.getInitialTheme();
    
    // 監聽系統深色模式變化
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    this.mediaQuery.addEventListener('change', this.handleSystemThemeChange.bind(this));
  }

  // 獲取初始主題
  private getInitialTheme(): ThemeConfig {
    // 1. 檢查 localStorage 中的設定
    const savedThemeMode = localStorage.getItem('theme-mode') as ThemeMode;
    if (savedThemeMode && THEME_PRESETS[savedThemeMode]) {
      if (savedThemeMode === 'custom') {
        const customTheme = this.loadCustomTheme();
        if (customTheme) return customTheme;
      }
      
      if (savedThemeMode === 'auto') {
        return this.getSystemTheme();
      }
      
      return THEME_PRESETS[savedThemeMode];
    }

    // 2. 檢查系統偏好
    return this.getSystemTheme();
  }

  // 獲取系統主題
  private getSystemTheme(): ThemeConfig {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    
    if (isHighContrast) {
      return THEME_PRESETS['high-contrast'];
    }
    
    return isDark ? THEME_PRESETS.dark : THEME_PRESETS.light;
  }

  // 處理系統主題變化
  private handleSystemThemeChange() {
    if (this.currentTheme.mode === 'auto') {
      const systemTheme = this.getSystemTheme();
      this.applyTheme(systemTheme);
      this.notifyListeners();
    }
  }

  // 載入自定義主題
  private loadCustomTheme(): ThemeConfig | null {
    try {
      const customThemeData = localStorage.getItem('custom-theme');
      if (customThemeData) {
        return JSON.parse(customThemeData);
      }
    } catch (error) {
      console.warn('Failed to load custom theme:', error);
    }
    return null;
  }

  // 保存自定義主題
  private saveCustomTheme(theme: ThemeConfig) {
    try {
      localStorage.setItem('custom-theme', JSON.stringify(theme));
    } catch (error) {
      console.error('Failed to save custom theme:', error);
    }
  }

  // 應用主題到DOM
  private applyTheme(theme: ThemeConfig) {
    const root = document.documentElement;
    
    // 應用CSS變數
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${this.kebabCase(key)}`, value);
    });

    // 應用字體設定
    Object.entries(theme.typography.fontSize).forEach(([key, value]) => {
      root.style.setProperty(`--font-size-${key}`, value);
    });

    Object.entries(theme.typography.fontWeight).forEach(([key, value]) => {
      root.style.setProperty(`--font-weight-${key}`, value.toString());
    });

    Object.entries(theme.typography.lineHeight).forEach(([key, value]) => {
      root.style.setProperty(`--line-height-${key}`, value.toString());
    });

    // 應用間距設定
    Object.entries(theme.spacing).forEach(([key, value]) => {
      root.style.setProperty(`--spacing-${key}`, value);
    });

    // 應用邊框圓角
    Object.entries(theme.borderRadius).forEach(([key, value]) => {
      root.style.setProperty(`--border-radius-${key}`, value);
    });

    // 應用動畫設定
    Object.entries(theme.animation.duration).forEach(([key, value]) => {
      root.style.setProperty(`--animation-duration-${key}`, value);
    });

    Object.entries(theme.animation.easing).forEach(([key, value]) => {
      root.style.setProperty(`--animation-easing-${key}`, value);
    });

    // 設置主題模式類名
    root.classList.remove('theme-light', 'theme-dark', 'theme-high-contrast', 'theme-custom');
    root.classList.add(`theme-${theme.mode === 'auto' ? this.getSystemTheme().mode : theme.mode}`);

    // 設置字體家族
    root.style.setProperty('--font-family', theme.typography.fontFamily);
  }

  // 轉換為 kebab-case
  private kebabCase(str: string): string {
    return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
  }

  // 通知監聽器
  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.currentTheme));
  }

  // 獲取當前主題
  getCurrentTheme(): ThemeConfig {
    return this.currentTheme;
  }

  // 獲取所有預設主題
  getPresetThemes(): ThemeConfig[] {
    return Object.values(THEME_PRESETS).filter(theme => theme.mode !== 'custom');
  }

  // 設置主題
  setTheme(themeMode: ThemeMode, customTheme?: ThemeConfig): void {
    let newTheme: ThemeConfig;

    if (themeMode === 'custom' && customTheme) {
      newTheme = customTheme;
      this.saveCustomTheme(customTheme);
    } else if (themeMode === 'auto') {
      newTheme = { ...THEME_PRESETS.auto, ...this.getSystemTheme() };
      newTheme.mode = 'auto';
    } else {
      newTheme = THEME_PRESETS[themeMode];
    }

    this.currentTheme = newTheme;
    this.applyTheme(newTheme);
    
    // 保存主題偏好
    localStorage.setItem('theme-mode', themeMode);
    
    this.notifyListeners();
  }

  // 創建自定義主題
  createCustomTheme(baseTheme: ThemeMode, customizations: Partial<ThemeConfig>): ThemeConfig {
    const base = THEME_PRESETS[baseTheme] || THEME_PRESETS.light;
    
    const customTheme: ThemeConfig = {
      ...base,
      ...customizations,
      mode: 'custom',
      name: 'custom',
      displayName: customizations.displayName || '自定義主題',
      colors: {
        ...base.colors,
        ...customizations.colors
      }
    };

    return customTheme;
  }

  // 添加主題變更監聽器
  onThemeChange(listener: (theme: ThemeConfig) => void): () => void {
    this.listeners.push(listener);
    
    // 返回取消訂閱函數
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  // 獲取顏色值
  getColor(colorKey: keyof ColorPalette): string {
    return this.currentTheme.colors[colorKey];
  }

  // 檢查是否為深色主題
  isDarkTheme(): boolean {
    const currentMode = this.currentTheme.mode === 'auto' 
      ? this.getSystemTheme().mode 
      : this.currentTheme.mode;
    return currentMode === 'dark';
  }

  // 初始化主題系統
  initialize(): void {
    this.applyTheme(this.currentTheme);
  }
}

// 創建全域實例
export const themeManager = new ThemeManager();

// 便利函數
export const getCurrentTheme = () => themeManager.getCurrentTheme();
export const setTheme = (mode: ThemeMode, customTheme?: ThemeConfig) => 
  themeManager.setTheme(mode, customTheme);
export const getPresetThemes = () => themeManager.getPresetThemes();
export const createCustomTheme = (baseTheme: ThemeMode, customizations: Partial<ThemeConfig>) => 
  themeManager.createCustomTheme(baseTheme, customizations);
export const getColor = (colorKey: keyof ColorPalette) => themeManager.getColor(colorKey);
export const isDarkTheme = () => themeManager.isDarkTheme();

// 初始化函數
export const initializeTheme = () => themeManager.initialize();

export default themeManager;
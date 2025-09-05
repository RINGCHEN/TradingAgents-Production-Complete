/**
 * HomepageErrorDetector - 首頁錯誤檢測器
 * 專門針對首頁渲染問題進行檢測和診斷
 */

import React, { useEffect, useState } from 'react';
import { useErrorDiagnostics } from './ErrorDiagnosticsProvider';
import { NavigationChecker } from '../utils/NavigationChecker';

interface HomepageErrorDetectorProps {
  onCriticalError?: (errors: any[]) => void;
  enableAutoFix?: boolean;
}

export const HomepageErrorDetector: React.FC<HomepageErrorDetectorProps> = ({
  onCriticalError,
  enableAutoFix = true
}) => {
  const { diagnosticReport, criticalErrors, reportError, refreshDiagnostics } = useErrorDiagnostics();
  const [hasPerformedInitialCheck, setHasPerformedInitialCheck] = useState(false);
  const [autoFixAttempts, setAutoFixAttempts] = useState(0);
  const [apiCheckInProgress, setApiCheckInProgress] = useState(false);
  const [lastApiCheck, setLastApiCheck] = useState(0);

  // 執行首頁特定檢查
  const performHomepageChecks = () => {
    try {
      // 檢查1: React根元素是否存在且已掛載
      const rootElement = document.getElementById('root');
      if (!rootElement) {
        reportError('render', 'Homepage root element not found', {
          check: 'root-element',
          expected: 'div#root',
          actual: 'not found'
        });
        return;
      }

      if (!rootElement.hasChildNodes()) {
        reportError('render', 'Homepage React app not mounted', {
          check: 'react-mount',
          rootElement: rootElement.outerHTML,
          note: 'React SPA may still be loading'
        });
        return;
      }

      // 檢查React應用是否完全載入 (更寬鬆的檢查)
      const landingPageElement = document.querySelector('.landing-page') || 
                                  document.querySelector('[data-testid="app-root"]') ||
                                  document.querySelector('.App') ||
                                  document.querySelector('main');
      if (!landingPageElement) {
        // 只有在完全找不到任何主要容器時才報錯
        const hasAnyContent = document.querySelector('div') || document.querySelector('section');
        if (!hasAnyContent) {
          reportError('render', 'No main content container found', {
            check: 'main-content-container',
            selectors: ['.landing-page', '[data-testid="app-root"]', '.App', 'main'],
            note: 'React components may still be rendering or user is logged in'
          });
        }
        // 不直接返回，繼續其他檢查
      }

      // 檢查2: 導航元素是否存在 (使用專門的NavigationChecker)
      NavigationChecker.checkNavigation().then(result => {
        if (!result.found) {
          reportError('render', 'Homepage navigation not rendered', {
            check: 'navigation',
            selector: result.selector,
            timing: result.timing,
            retryCount: result.retryCount,
            note: 'Navigation not found after multiple retries in React SPA'
          });
        } else {
          console.log(`✅ Navigation found with selector: ${result.selector} (${result.timing}ms, ${result.retryCount} retries)`);
        }
      }).catch(error => {
        reportError('render', 'Error checking navigation', {
          check: 'navigation',
          error: error.message
        });
      });

      // 檢查3: 主要內容區域是否存在
      const mainContent = document.querySelector('main, .main-content, .landing-page');
      if (!mainContent) {
        reportError('render', 'Homepage main content not rendered', {
          check: 'main-content',
          selector: 'main, .main-content, .landing-page'
        });
      }

      // 檢查4: 檢查是否有JavaScript錯誤導致的空白頁面
      const bodyText = document.body.textContent || '';
      if (bodyText.trim().length < 100) {
        reportError('render', 'Homepage appears to be mostly empty', {
          check: 'content-length',
          textLength: bodyText.length,
          bodyHTML: document.body.innerHTML.substring(0, 500)
        });
      }

      // 檢查5: 檢查認證狀態初始化
      checkAuthenticationState();

      // 檢查6: 檢查API連接
      checkApiConnectivity();

      console.log('Homepage checks completed successfully');
      
    } catch (error) {
      reportError('javascript', 'Error during homepage checks', {
        error: error instanceof Error ? error.message : error,
        stack: error instanceof Error ? error.stack : undefined
      });
    }
  };

  // 檢查認證狀態
  const checkAuthenticationState = () => {
    try {
      // 檢查localStorage中的認證信息
      const authToken = localStorage.getItem('authToken') || localStorage.getItem('token');
      const userInfo = localStorage.getItem('userInfo') || localStorage.getItem('user');

      // 檢查是否有React應用程式載入
      const reactAppExists = document.querySelector('#root > div');
      
      if (!reactAppExists) {
        reportError('auth', 'React application not properly loaded', {
          check: 'react-app',
          hasToken: !!authToken,
          hasUserInfo: !!userInfo
        });
        return;
      }

      // 檢查是否有認證相關的元素（更寬鬆的檢查）
      const hasAuthElements = document.querySelector('button, a, input[type="email"], input[type="password"]');
      
      if (!hasAuthElements) {
        reportError('auth', 'Authentication UI elements not found', {
          check: 'auth-ui',
          hasToken: !!authToken,
          hasUserInfo: !!userInfo
        });
      }

      // 記錄導航時間用於性能分析
      const navEntries = performance.getEntriesByType('navigation');
      if (navEntries.length > 0) {
        console.log('Navigation timing:', navEntries[0]);
      }

    } catch (error) {
      reportError('auth', 'Error checking authentication state', {
        error: error instanceof Error ? error.message : error
      });
    }
  };

  // 檢查API連接性 - 針對前端應用優化
  const checkApiConnectivity = async () => {
    try {
      // 防止重複檢查：如果正在進行或最近30秒內已檢查過，則跳過
      const now = Date.now();
      if (apiCheckInProgress || (now - lastApiCheck) < 30000) {
        return;
      }

      setApiCheckInProgress(true);
      setLastApiCheck(now);

      // 對於純前端應用，我們檢查基本的網路連接而不是特定的API端點
      if (!navigator.onLine) {
        reportError('network', 'No internet connection detected', {
          check: 'network-status',
          online: navigator.onLine
        });
        setApiCheckInProgress(false);
        return;
      }

      // 檢查是否能訪問一個已知的外部資源（如Google DNS）
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      try {
        // 使用一個安全的外部端點來測試網路連接
        const response = await fetch('https://www.google.com/favicon.ico', {
          method: 'HEAD',
          mode: 'no-cors',
          signal: controller.signal
        });

        clearTimeout(timeoutId);
        console.log('Network connectivity check passed');
        setApiCheckInProgress(false);

      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          reportError('network', 'Network connectivity check timeout', {
            check: 'api-timeout',
            timeout: 5000
          });
        } else {
          reportError('network', 'Network connectivity check failed', {
            check: 'network-connectivity',
            error: fetchError instanceof Error ? fetchError.message : fetchError
          });
        }
        setApiCheckInProgress(false);
      }

    } catch (error) {
      reportError('network', 'Error during network connectivity check', {
        error: error instanceof Error ? error.message : error
      });
      setApiCheckInProgress(false);
    }
  };

  // 嘗試自動修復常見問題
  const attemptAutoFix = () => {
    if (!enableAutoFix || autoFixAttempts >= 3) {
      return;
    }

    setAutoFixAttempts(prev => prev + 1);

    try {
      console.log(`Attempting auto-fix (attempt ${autoFixAttempts + 1})`);

      // 修復1: 清理可能損壞的localStorage數據
      const suspiciousKeys = ['authToken', 'userInfo', 'couponData'];
      suspiciousKeys.forEach(key => {
        try {
          const value = localStorage.getItem(key);
          if (value && (value.includes('<html') || value.includes('<!DOCTYPE'))) {
            console.log(`Removing corrupted localStorage key: ${key}`);
            localStorage.removeItem(key);
          }
        } catch (e) {
          console.log(`Error checking localStorage key ${key}:`, e);
        }
      });

      // 修復2: 強制刷新React組件
      if (window.location.pathname === '/') {
        setTimeout(() => {
          refreshDiagnostics();
        }, 1000);
      }

      // 修復3: 清理可能的緩存問題
      if ('caches' in window) {
        caches.keys().then(names => {
          names.forEach(name => {
            if (name.includes('api') || name.includes('auth')) {
              caches.delete(name);
            }
          });
        });
      }

      console.log('Auto-fix completed');

    } catch (error) {
      reportError('javascript', 'Error during auto-fix attempt', {
        error: error instanceof Error ? error.message : error,
        attempt: autoFixAttempts + 1
      });
    }
  };

  // 初始檢查 - 等待React應用完全載入
  useEffect(() => {
    if (!hasPerformedInitialCheck) {
      // 先等待React應用載入，然後執行檢查
      NavigationChecker.waitForReactApp(10000).then(reactLoaded => {
        if (reactLoaded) {
          console.log('✅ React app loaded, performing homepage checks...');
          // React應用已載入，再等待一點時間確保所有組件都渲染完成
          setTimeout(() => {
            performHomepageChecks();
            setHasPerformedInitialCheck(true);
          }, 1000);
        } else {
          console.warn('⚠️ React app did not load within timeout, performing checks anyway...');
          performHomepageChecks();
          setHasPerformedInitialCheck(true);
        }
      });
    }
  }, [hasPerformedInitialCheck]);

  // 監聽嚴重錯誤並嘗試自動修復
  useEffect(() => {
    if (criticalErrors.length > 0 && enableAutoFix) {
      console.log('Critical errors detected, attempting auto-fix:', criticalErrors);
      
      // 通知父組件
      if (onCriticalError) {
        onCriticalError(criticalErrors);
      }

      // 嘗試自動修復
      const fixTimer = setTimeout(attemptAutoFix, 2000);
      return () => clearTimeout(fixTimer);
    }
  }, [criticalErrors.length, enableAutoFix, onCriticalError]);

  // 定期重新檢查（僅在有錯誤時）
  useEffect(() => {
    if (diagnosticReport && diagnosticReport.overallHealth !== 'healthy') {
      const recheckTimer = setInterval(() => {
        performHomepageChecks();
      }, 15000); // 每15秒重新檢查

      return () => clearInterval(recheckTimer);
    }
  }, [diagnosticReport?.overallHealth]);

  // 監聽頁面焦點變化，重新檢查
  useEffect(() => {
    const handleFocus = () => {
      if (document.hasFocus()) {
        setTimeout(performHomepageChecks, 500);
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  // 這個組件不渲染任何UI，只是在後台執行檢查
  return null;
};

export default HomepageErrorDetector;
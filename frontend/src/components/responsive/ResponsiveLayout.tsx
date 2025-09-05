/**
 * ResponsiveLayout Component - TradingAgents 響應式佈局系統
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供完整的響應式佈局管理，包含：
 * - Mobile First 設計原則
 * - 觸控操作優化
 * - 無障礙設計支援
 * - 自適應導航系統
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { useMediaQuery } from '../../hooks/useMediaQuery';
import { useWindowSize } from '../../hooks/useWindowSize';

// ==================== 類型定義 ====================

interface ResponsiveLayoutProps {
  children: ReactNode;
  className?: string;
  enableSidebar?: boolean;
  enableBottomNav?: boolean;
  sidebarContent?: ReactNode;
  headerContent?: ReactNode;
  footerContent?: ReactNode;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: ReactNode;
  href: string;
  isActive?: boolean;
}

interface BreakpointConfig {
  mobile: number;
  tablet: number;
  desktop: number;
  wide: number;
}

// ==================== 常數定義 ====================

const BREAKPOINTS: BreakpointConfig = {
  mobile: 480,
  tablet: 768,
  desktop: 1024,
  wide: 1280
};

const MOBILE_NAV_ITEMS: NavigationItem[] = [
  {
    id: 'dashboard',
    label: '儀表板',
    icon: <DashboardIcon />,
    href: '/dashboard',
    isActive: true
  },
  {
    id: 'portfolio',
    label: '投資組合',
    icon: <PortfolioIcon />,
    href: '/portfolio'
  },
  {
    id: 'market',
    label: '市場分析',
    icon: <MarketIcon />,
    href: '/market'
  },
  {
    id: 'alerts',
    label: '提醒',
    icon: <AlertIcon />,
    href: '/alerts'
  },
  {
    id: 'profile',
    label: '個人',
    icon: <ProfileIcon />,
    href: '/profile'
  }
];

// ==================== 圖標組件 ====================

const DashboardIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
  </svg>
);

const PortfolioIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const MarketIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const AlertIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M15 17h5l-5 5v-5zm-5-2H5l5-5v5zm5-10v5h5l-5-5zM5 7h5V2L5 7z" />
  </svg>
);

const ProfileIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const MenuIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const CloseIcon: React.FC = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M6 18L18 6M6 6l12 12" />
  </svg>
);

// ==================== Hook 定義 ====================
// Hooks have been moved to separate files:
// - useMediaQuery: ../../hooks/useMediaQuery.ts  
// - useWindowSize: ../../hooks/useWindowSize.ts

// ==================== 子組件定義 ====================

/**
 * 移動端側邊欄組件
 */
interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
}

const MobileSidebar: React.FC<MobileSidebarProps> = ({ 
  isOpen, 
  onClose, 
  children 
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  return (
    <>
      {/* 背景遮罩 */}
      <div 
        className={`mobile-sidebar-overlay ${isOpen ? 'visible' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* 側邊欄 */}
      <div 
        className={`mobile-sidebar ${isOpen ? 'open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="導航菜單"
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            TradingAgents
          </h2>
          <button
            onClick={onClose}
            className="touch-target focus-ring"
            aria-label="關閉導航菜單"
          >
            <CloseIcon />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </>
  );
};

/**
 * 底部導航組件
 */
interface BottomNavigationProps {
  items: NavigationItem[];
  onItemClick?: (item: NavigationItem) => void;
}

const BottomNavigation: React.FC<BottomNavigationProps> = ({ 
  items, 
  onItemClick 
}) => {
  return (
    <nav 
      className="bottom-navigation"
      role="navigation"
      aria-label="底部導航"
    >
      {items.map((item) => (
        <a
          key={item.id}
          href={item.href}
          className={`bottom-nav-item ${item.isActive ? 'active' : ''}`}
          onClick={() => onItemClick?.(item)}
          aria-current={item.isActive ? 'page' : undefined}
        >
          <div className="bottom-nav-icon">
            {item.icon}
          </div>
          <span>{item.label}</span>
        </a>
      ))}
    </nav>
  );
};

/**
 * 響應式頭部組件
 */
interface ResponsiveHeaderProps {
  onMenuClick: () => void;
  children?: ReactNode;
}

const ResponsiveHeader: React.FC<ResponsiveHeaderProps> = ({ 
  onMenuClick, 
  children 
}) => {
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.desktop - 1}px)`);

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
      <div className="container flex items-center justify-between h-16">
        <div className="flex items-center gap-4">
          {isMobile && (
            <button
              onClick={onMenuClick}
              className="mobile-menu-button focus-ring"
              aria-label="打開導航菜單"
              aria-expanded="false"
            >
              <MenuIcon />
            </button>
          )}
          
          <h1 className="text-xl font-bold text-gray-900">
            TradingAgents
          </h1>
        </div>
        
        {children && (
          <div className="flex items-center gap-4">
            {children}
          </div>
        )}
      </div>
    </header>
  );
};

/**
 * 響應式內容區域組件
 */
interface ResponsiveContentProps {
  children: ReactNode;
  className?: string;
  enablePadding?: boolean;
}

const ResponsiveContent: React.FC<ResponsiveContentProps> = ({ 
  children, 
  className = '',
  enablePadding = true
}) => {
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.desktop - 1}px)`);
  const paddingClass = enablePadding 
    ? (isMobile ? 'p-4 pb-20' : 'p-6') 
    : '';

  return (
    <main 
      className={`flex-1 ${paddingClass} ${className}`}
      role="main"
      id="main-content"
    >
      {children}
    </main>
  );
};

// ==================== 主要組件 ====================

/**
 * ResponsiveLayout 主組件
 * 提供完整的響應式佈局解決方案
 */
const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  className = '',
  enableSidebar = true,
  enableBottomNav = true,
  sidebarContent,
  headerContent,
  footerContent
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.desktop - 1}px)`);
  const isTablet = useMediaQuery(`(max-width: ${BREAKPOINTS.tablet - 1}px)`);
  const windowSize = useWindowSize();

  // 處理側邊欄開關
  const handleMenuClick = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  // 處理底部導航點擊
  const handleBottomNavClick = (item: NavigationItem) => {
    console.log(`導航至: ${item.label}`);
    // 這裡可以加入路由邏輯
  };

  // 檢測設備方向變化
  useEffect(() => {
    const handleOrientationChange = () => {
      // 方向變化時關閉側邊欄
      setIsSidebarOpen(false);
    };

    window.addEventListener('orientationchange', handleOrientationChange);
    return () => window.removeEventListener('orientationchange', handleOrientationChange);
  }, []);

  // 鍵盤事件處理
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isSidebarOpen) {
        setIsSidebarOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscapeKey);
    return () => document.removeEventListener('keydown', handleEscapeKey);
  }, [isSidebarOpen]);

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* 跳過內容連結 - 無障礙功能 */}
      <a 
        href="#main-content" 
        className="skip-to-content"
      >
        跳過導航，直接到內容
      </a>

      {/* 響應式頭部 */}
      <ResponsiveHeader onMenuClick={handleMenuClick}>
        {headerContent}
      </ResponsiveHeader>

      {/* 主要內容區域 */}
      <div className="flex flex-1">
        {/* 桌面版側邊欄 */}
        {enableSidebar && !isMobile && (
          <aside className="w-64 bg-white border-r border-gray-200 sticky top-16 h-[calc(100vh-4rem)] overflow-y-auto">
            <nav className="p-4" role="navigation" aria-label="主要導航">
              {sidebarContent || (
                <div className="space-y-2">
                  {MOBILE_NAV_ITEMS.map((item) => (
                    <a
                      key={item.id}
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                        item.isActive 
                          ? 'bg-primary-100 text-primary-700' 
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                      aria-current={item.isActive ? 'page' : undefined}
                    >
                      {item.icon}
                      <span className="font-medium">{item.label}</span>
                    </a>
                  ))}
                </div>
              )}
            </nav>
          </aside>
        )}

        {/* 響應式內容區域 */}
        <ResponsiveContent>
          {children}
        </ResponsiveContent>
      </div>

      {/* 移動端側邊欄 */}
      {enableSidebar && isMobile && (
        <MobileSidebar 
          isOpen={isSidebarOpen} 
          onClose={handleSidebarClose}
        >
          <nav className="p-4" role="navigation" aria-label="主要導航">
            {sidebarContent || (
              <div className="space-y-2">
                {MOBILE_NAV_ITEMS.map((item) => (
                  <a
                    key={item.id}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                      item.isActive 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={handleSidebarClose}
                    aria-current={item.isActive ? 'page' : undefined}
                  >
                    {item.icon}
                    <span className="font-medium">{item.label}</span>
                  </a>
                ))}
              </div>
            )}
          </nav>
        </MobileSidebar>
      )}

      {/* 移動端底部導航 */}
      {enableBottomNav && isMobile && (
        <BottomNavigation 
          items={MOBILE_NAV_ITEMS} 
          onItemClick={handleBottomNavClick}
        />
      )}

      {/* 頁尾 */}
      {footerContent && (
        <footer className="bg-white border-t border-gray-200 p-4">
          {footerContent}
        </footer>
      )}
    </div>
  );
};

// ==================== 使用示例組件 ====================

/**
 * TradingDashboardLayout - 交易儀表板專用佈局
 */
export const TradingDashboardLayout: React.FC<{children: ReactNode}> = ({ children }) => {
  const sidebarContent = (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          主要功能
        </h3>
        <div className="space-y-1">
          {MOBILE_NAV_ITEMS.map((item) => (
            <a
              key={item.id}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                item.isActive 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </a>
          ))}
        </div>
      </div>
      
      <div>
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          快速統計
        </h3>
        <div className="space-y-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">總資產</div>
            <div className="text-lg font-semibold text-green-600">$125,678</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm text-gray-600">今日收益</div>
            <div className="text-lg font-semibold text-green-600">+$2,341</div>
          </div>
        </div>
      </div>
    </div>
  );

  const headerContent = (
    <div className="flex items-center gap-4">
      <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
        市場開盤中
      </div>
      <button className="btn btn-primary">
        新增交易
      </button>
    </div>
  );

  return (
    <ResponsiveLayout 
      sidebarContent={sidebarContent}
      headerContent={headerContent}
    >
      {children}
    </ResponsiveLayout>
  );
};

export default ResponsiveLayout;
export type { ResponsiveLayoutProps, NavigationItem, BreakpointConfig };
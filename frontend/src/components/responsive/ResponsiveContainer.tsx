/**
 * ResponsiveContainer Component - TradingAgents 響應式容器
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供響應式容器組件，自動適應不同螢幕尺寸
 * - 智能邊距和內距調整
 * - 自適應最大寬度
 * - 支援網格和彈性佈局
 * - 整合設計系統斷點
 */

import React, { ReactNode } from 'react';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

/**
 * 容器變體類型
 */
export type ContainerVariant = 'default' | 'fluid' | 'narrow' | 'wide' | 'full';

/**
 * 容器組件屬性介面
 */
export interface ResponsiveContainerProps {
  /** 子組件 */
  children: ReactNode;
  /** 容器變體 */
  variant?: ContainerVariant;
  /** 自定義 CSS 類名 */
  className?: string;
  /** 是否啟用內距 */
  enablePadding?: boolean;
  /** 是否啟用垂直間距 */
  enableVerticalSpacing?: boolean;
  /** HTML 元素類型 */
  as?: keyof JSX.IntrinsicElements;
  /** 最大寬度覆寫 */
  maxWidth?: string;
  /** 是否居中對齊 */
  centered?: boolean;
}

/**
 * 獲取容器樣式類名
 */
const getContainerClasses = (
  variant: ContainerVariant,
  enablePadding: boolean,
  enableVerticalSpacing: boolean,
  centered: boolean,
  className?: string
): string => {
  const baseClasses = ['responsive-container'];
  
  // 變體樣式
  switch (variant) {
    case 'fluid':
      baseClasses.push('w-full');
      break;
    case 'narrow':
      baseClasses.push('max-w-3xl');
      break;
    case 'wide':
      baseClasses.push('max-w-7xl');
      break;
    case 'full':
      baseClasses.push('w-full', 'h-full');
      break;
    case 'default':
    default:
      baseClasses.push('container');
      break;
  }
  
  // 內距
  if (enablePadding) {
    baseClasses.push('px-4', 'md:px-6', 'lg:px-8');
  }
  
  // 垂直間距
  if (enableVerticalSpacing) {
    baseClasses.push('py-4', 'md:py-6', 'lg:py-8');
  }
  
  // 居中對齊
  if (centered) {
    baseClasses.push('mx-auto');
  }
  
  // 自定義類名
  if (className) {
    baseClasses.push(className);
  }
  
  return baseClasses.join(' ');
};

/**
 * ResponsiveContainer 組件
 * 
 * @example
 * ```tsx
 * // 基本使用
 * <ResponsiveContainer>
 *   <h1>標題內容</h1>
 *   <p>段落內容</p>
 * </ResponsiveContainer>
 * 
 * // 流體容器
 * <ResponsiveContainer variant="fluid" enablePadding>
 *   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
 *     <Card />
 *     <Card />
 *     <Card />
 *   </div>
 * </ResponsiveContainer>
 * 
 * // 窄容器用於文章內容
 * <ResponsiveContainer variant="narrow" enablePadding enableVerticalSpacing>
 *   <article>
 *     <h1>文章標題</h1>
 *     <p>文章內容...</p>
 *   </article>
 * </ResponsiveContainer>
 * ```
 */
export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  variant = 'default',
  className,
  enablePadding = false,
  enableVerticalSpacing = false,
  as: Component = 'div',
  maxWidth,
  centered = true
}) => {
  const breakpoint = useResponsiveBreakpoint();
  
  const containerClasses = getContainerClasses(
    variant,
    enablePadding,
    enableVerticalSpacing,
    centered,
    className
  );

  const style: React.CSSProperties = {
    ...(maxWidth && { maxWidth })
  };

  return (
    <Component 
      className={containerClasses}
      style={style}
      data-breakpoint={breakpoint.current}
      data-mobile={breakpoint.isMobile}
      data-tablet={breakpoint.isTablet}
      data-desktop={breakpoint.isDesktop}
    >
      {children}
    </Component>
  );
};

/**
 * 預定義容器組件變體
 */

/**
 * 頁面容器 - 用於整個頁面的主要內容區域
 */
export const PageContainer: React.FC<Omit<ResponsiveContainerProps, 'variant'>> = (props) => (
  <ResponsiveContainer 
    variant="default" 
    enablePadding 
    enableVerticalSpacing 
    {...props} 
  />
);

/**
 * 內容容器 - 用於文章或詳細內容
 */
export const ContentContainer: React.FC<Omit<ResponsiveContainerProps, 'variant'>> = (props) => (
  <ResponsiveContainer 
    variant="narrow" 
    enablePadding 
    enableVerticalSpacing 
    as="article"
    {...props} 
  />
);

/**
 * 流體容器 - 用於需要全寬的內容
 */
export const FluidContainer: React.FC<Omit<ResponsiveContainerProps, 'variant'>> = (props) => (
  <ResponsiveContainer 
    variant="fluid" 
    enablePadding 
    {...props} 
  />
);

/**
 * 寬容器 - 用於需要更多空間的內容
 */
export const WideContainer: React.FC<Omit<ResponsiveContainerProps, 'variant'>> = (props) => (
  <ResponsiveContainer 
    variant="wide" 
    enablePadding 
    enableVerticalSpacing 
    {...props} 
  />
);

/**
 * 交易儀表板專用容器
 */
export const TradingDashboardContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className,
  ...props
}) => {
  const breakpoint = useResponsiveBreakpoint();
  
  const dashboardClasses = [
    'trading-dashboard',
    breakpoint.isMobile ? 'mobile-dashboard' : '',
    breakpoint.isTablet ? 'tablet-dashboard' : '',
    breakpoint.isDesktop ? 'desktop-dashboard' : '',
    className || ''
  ].filter(Boolean).join(' ');

  return (
    <ResponsiveContainer 
      variant="fluid"
      className={dashboardClasses}
      {...props}
    >
      {children}
    </ResponsiveContainer>
  );
};

export default ResponsiveContainer;
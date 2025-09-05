/**
 * ResponsiveGrid Component - TradingAgents 響應式網格系統
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 提供智能響應式網格佈局組件
 * - Mobile First 設計原則
 * - 自適應欄位數量
 * - 智能間距調整
 * - 支援多種佈局模式
 */

import React, { ReactNode } from 'react';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

/**
 * 網格佈局模式
 */
export type GridMode = 'auto' | 'fixed' | 'masonry' | 'dashboard';

/**
 * 響應式網格配置
 */
export interface ResponsiveGridConfig {
  /** 手機版欄數 */
  mobile?: number;
  /** 平板版欄數 */
  tablet?: number;
  /** 桌面版欄數 */
  desktop?: number;
  /** 大螢幕版欄數 */
  wide?: number;
}

/**
 * 網格項目屬性
 */
export interface GridItemProps {
  /** 子組件 */
  children: ReactNode;
  /** 佔用的欄數 */
  colSpan?: ResponsiveGridConfig;
  /** 佔用的行數 */
  rowSpan?: ResponsiveGridConfig;
  /** 自定義類名 */
  className?: string;
  /** HTML 元素類型 */
  as?: keyof JSX.IntrinsicElements;
}

/**
 * 響應式網格屬性
 */
export interface ResponsiveGridProps {
  /** 子組件 */
  children: ReactNode;
  /** 網格配置 */
  columns?: ResponsiveGridConfig;
  /** 網格模式 */
  mode?: GridMode;
  /** 間距大小 */
  gap?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** 自定義類名 */
  className?: string;
  /** 最小項目寬度 (auto模式) */
  minItemWidth?: string;
  /** 是否填滿容器高度 */
  fillHeight?: boolean;
  /** HTML 元素類型 */
  as?: keyof JSX.IntrinsicElements;
}

/**
 * 獲取響應式欄數
 */
const getResponsiveColumns = (
  config: ResponsiveGridConfig = {},
  breakpoint: ReturnType<typeof useResponsiveBreakpoint>
): number => {
  if (breakpoint.isMobile) return config.mobile || 1;
  if (breakpoint.isTablet) return config.tablet || 2;
  if (breakpoint.isLargeScreen) return config.wide || 4;
  return config.desktop || 3;
};

/**
 * 獲取網格樣式
 */
const getGridStyles = (
  columns: number,
  mode: GridMode,
  gap: string,
  minItemWidth?: string,
  fillHeight?: boolean
): React.CSSProperties => {
  const gapMap = {
    xs: 'var(--spacing-xs)',
    sm: 'var(--spacing-sm)',
    md: 'var(--spacing-md)',
    lg: 'var(--spacing-lg)',
    xl: 'var(--spacing-xl)'
  };

  const baseStyles: React.CSSProperties = {
    display: 'grid',
    gap: gapMap[gap as keyof typeof gapMap] || gapMap.md,
    width: '100%'
  };

  if (fillHeight) {
    baseStyles.height = '100%';
  }

  switch (mode) {
    case 'auto':
      return {
        ...baseStyles,
        gridTemplateColumns: minItemWidth
          ? `repeat(auto-fit, minmax(${minItemWidth}, 1fr))`
          : `repeat(auto-fit, minmax(250px, 1fr))`
      };
    
    case 'masonry':
      return {
        ...baseStyles,
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridTemplateRows: 'masonry' // 實驗性功能，需要 CSS Grid Level 3
      };
    
    case 'dashboard':
      return {
        ...baseStyles,
        gridTemplateColumns: columns === 1 
          ? '1fr' 
          : columns === 2 
          ? '1fr 1fr'
          : '280px 1fr 320px'
      };
    
    case 'fixed':
    default:
      return {
        ...baseStyles,
        gridTemplateColumns: `repeat(${columns}, 1fr)`
      };
  }
};

/**
 * 網格項目組件
 */
export const GridItem: React.FC<GridItemProps> = ({
  children,
  colSpan,
  rowSpan,
  className,
  as: Component = 'div'
}) => {
  const breakpoint = useResponsiveBreakpoint();
  
  const getSpanValue = (spanConfig?: ResponsiveGridConfig): number => {
    if (!spanConfig) return 1;
    return getResponsiveColumns(spanConfig, breakpoint);
  };

  const colSpanValue = getSpanValue(colSpan);
  const rowSpanValue = getSpanValue(rowSpan);

  const style: React.CSSProperties = {
    ...(colSpanValue > 1 && { gridColumn: `span ${colSpanValue}` }),
    ...(rowSpanValue > 1 && { gridRow: `span ${rowSpanValue}` })
  };

  return (
    <Component 
      className={`grid-item ${className || ''}`}
      style={style}
      data-col-span={colSpanValue}
      data-row-span={rowSpanValue}
    >
      {children}
    </Component>
  );
};

/**
 * ResponsiveGrid 組件
 * 
 * @example
 * ```tsx
 * // 基本自適應網格
 * <ResponsiveGrid columns={{ mobile: 1, tablet: 2, desktop: 3 }}>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </ResponsiveGrid>
 * 
 * // 自動填充網格
 * <ResponsiveGrid mode="auto" minItemWidth="300px">
 *   <TradingCard />
 *   <TradingCard />
 *   <TradingCard />
 * </ResponsiveGrid>
 * 
 * // 交易儀表板網格
 * <ResponsiveGrid mode="dashboard" gap="lg">
 *   <GridItem colSpan={{ desktop: 2 }}>
 *     <MainChart />
 *   </GridItem>
 *   <GridItem>
 *     <Sidebar />
 *   </GridItem>
 * </ResponsiveGrid>
 * ```
 */
export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  columns = { mobile: 1, tablet: 2, desktop: 3 },
  mode = 'fixed',
  gap = 'md',
  className,
  minItemWidth,
  fillHeight = false,
  as: Component = 'div'
}) => {
  const breakpoint = useResponsiveBreakpoint();
  const columnsCount = getResponsiveColumns(columns, breakpoint);
  
  const gridStyles = getGridStyles(
    columnsCount,
    mode,
    gap,
    minItemWidth,
    fillHeight
  );

  const gridClasses = [
    'responsive-grid',
    `grid-${mode}`,
    `gap-${gap}`,
    breakpoint.isMobile ? 'grid-mobile' : '',
    breakpoint.isTablet ? 'grid-tablet' : '',
    breakpoint.isDesktop ? 'grid-desktop' : '',
    className || ''
  ].filter(Boolean).join(' ');

  return (
    <Component 
      className={gridClasses}
      style={gridStyles}
      data-columns={columnsCount}
      data-mode={mode}
      data-breakpoint={breakpoint.current}
    >
      {children}
    </Component>
  );
};

/**
 * 預定義網格組件
 */

/**
 * 交易卡片網格 - 用於顯示交易相關卡片
 */
export const TradingCardGrid: React.FC<Omit<ResponsiveGridProps, 'columns' | 'mode'>> = (props) => (
  <ResponsiveGrid 
    columns={{ mobile: 1, tablet: 2, desktop: 3, wide: 4 }}
    mode="auto"
    minItemWidth="280px"
    gap="lg"
    {...props}
  />
);

/**
 * 股票列表網格 - 用於股票列表顯示
 */
export const StockListGrid: React.FC<Omit<ResponsiveGridProps, 'columns' | 'mode'>> = (props) => (
  <ResponsiveGrid 
    columns={{ mobile: 1, tablet: 1, desktop: 2, wide: 3 }}
    mode="fixed"
    gap="md"
    {...props}
  />
);

/**
 * 儀表板主網格 - 用於主要儀表板佈局
 */
export const DashboardMainGrid: React.FC<Omit<ResponsiveGridProps, 'mode'>> = (props) => (
  <ResponsiveGrid 
    mode="dashboard"
    columns={{ mobile: 1, tablet: 1, desktop: 3 }}
    gap="xl"
    fillHeight
    {...props}
  />
);

/**
 * 圖表網格 - 用於顯示多個圖表
 */
export const ChartGrid: React.FC<Omit<ResponsiveGridProps, 'columns'>> = (props) => (
  <ResponsiveGrid 
    columns={{ mobile: 1, tablet: 2, desktop: 2, wide: 3 }}
    gap="lg"
    {...props}
  />
);

export default ResponsiveGrid;
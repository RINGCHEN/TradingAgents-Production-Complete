/**
 * Responsive Components Index - TradingAgents 響應式組件統一導出
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 統一導出所有響應式設計相關組件
 * 提供便利的導入方式和完整的型別支援
 */

// 主要佈局組件
export { default as ResponsiveLayout } from './ResponsiveLayout';
export { TradingDashboardLayout } from './ResponsiveLayout';

// 容器組件
export { 
  ResponsiveContainer as Container,
  PageContainer,
  ContentContainer,
  FluidContainer,
  WideContainer,
  TradingDashboardContainer
} from './ResponsiveContainer';

// 網格組件
export {
  ResponsiveGrid as Grid,
  GridItem,
  TradingCardGrid,
  StockListGrid,
  DashboardMainGrid,
  ChartGrid
} from './ResponsiveGrid';

// 型別定義導出
export type { 
  ResponsiveLayoutProps,
  NavigationItem,
  BreakpointConfig
} from './ResponsiveLayout';

export type {
  ResponsiveContainerProps,
  ContainerVariant
} from './ResponsiveContainer';

export type {
  ResponsiveGridProps,
  ResponsiveGridConfig,
  GridItemProps,
  GridMode
} from './ResponsiveGrid';

/**
 * 使用示例:
 * 
 * ```tsx
 * // 基本佈局
 * import { ResponsiveLayout } from './components/responsive';
 * 
 * // 交易儀表板
 * import { TradingDashboardLayout } from './components/responsive';
 * 
 * // 容器和網格
 * import { 
 *   Container, 
 *   Grid, 
 *   GridItem,
 *   TradingCardGrid 
 * } from './components/responsive';
 * 
 * const TradingDashboard = () => {
 *   return (
 *     <TradingDashboardLayout>
 *       <Container variant="fluid" enablePadding>
 *         <TradingCardGrid>
 *           <TradingCard />
 *           <TradingCard />
 *           <TradingCard />
 *         </TradingCardGrid>
 *       </Container>
 *     </TradingDashboardLayout>
 *   );
 * };
 * ```
 */
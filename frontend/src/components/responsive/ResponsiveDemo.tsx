/**
 * ResponsiveDemo Component - TradingAgents 響應式系統示範
 * 天工(TianGong) - 第二階段Week2 UX優化
 * 
 * 展示響應式設計系統的使用方法
 * - 實際使用案例展示
 * - Hook 功能演示
 * - 組件整合範例
 */

import React from 'react';
import { 
  useMediaQuery, 
  useWindowSize, 
  useResponsiveBreakpoint,
  useIsMobile,
  useIsDesktop 
} from '../../hooks';

import { 
  Container, 
  Grid, 
  GridItem,
  TradingCardGrid 
} from './index';

/**
 * 簡單交易卡片組件用於示範
 */
const DemoTradingCard: React.FC<{ title: string; value: string; color: string }> = ({ 
  title, 
  value, 
  color 
}) => (
  <div className="trading-card">
    <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
  </div>
);

/**
 * Hook 使用示範組件
 */
const HookDemonstration: React.FC = () => {
  // 基本 Hook 使用
  const isMobile = useIsMobile();
  const isDesktop = useIsDesktop();
  const { width, height } = useWindowSize();
  const breakpoint = useResponsiveBreakpoint();
  const isLargeScreen = useMediaQuery('(min-width: 1280px)');

  return (
    <Container variant="narrow" enablePadding>
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">響應式 Hook 狀態</h2>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-gray-700">裝置類型</h3>
              <p>Mobile: {isMobile ? '✅' : '❌'}</p>
              <p>Desktop: {isDesktop ? '✅' : '❌'}</p>
              <p>Large Screen: {isLargeScreen ? '✅' : '❌'}</p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-700">視窗尺寸</h3>
              <p>寬度: {width}px</p>
              <p>高度: {height}px</p>
              <p>比例: {(width/height).toFixed(2)}</p>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700">當前斷點</h3>
            <p className="text-lg font-bold text-primary-600">{breakpoint.current}</p>
            <div className="flex gap-2 mt-2">
              {Object.entries(breakpoint.is).map(([key, value]) => (
                <span 
                  key={key} 
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    value ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {key}: {value ? '✓' : '✗'}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Container>
  );
};

/**
 * 響應式網格示範
 */
const GridDemonstration: React.FC = () => {
  const sampleData = [
    { title: '總資產', value: '$125,678', color: 'text-green-600' },
    { title: '今日收益', value: '+$2,341', color: 'text-green-600' },
    { title: '總收益率', value: '+15.8%', color: 'text-green-600' },
    { title: '持倉股票', value: '12', color: 'text-blue-600' },
    { title: '現金餘額', value: '$45,123', color: 'text-gray-600' },
    { title: '本月交易', value: '28', color: 'text-purple-600' }
  ];

  return (
    <Container variant="wide" enablePadding>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">響應式網格系統</h2>
      
      <TradingCardGrid>
        {sampleData.map((item, index) => (
          <DemoTradingCard 
            key={index}
            title={item.title}
            value={item.value}
            color={item.color}
          />
        ))}
      </TradingCardGrid>
    </Container>
  );
};

/**
 * 自定義網格佈局示範
 */
const CustomGridDemonstration: React.FC = () => {
  return (
    <Container variant="fluid" enablePadding>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">自定義網格佈局</h2>
      
      <Grid 
        columns={{ mobile: 1, tablet: 2, desktop: 3 }}
        gap="lg"
      >
        <GridItem colSpan={{ tablet: 2, desktop: 1 }}>
          <div className="trading-card">
            <h3 className="text-lg font-semibold mb-4">主要圖表</h3>
            <div className="h-32 bg-gray-100 rounded flex items-center justify-center">
              <p className="text-gray-500">圖表內容區域</p>
            </div>
          </div>
        </GridItem>
        
        <GridItem>
          <div className="trading-card">
            <h3 className="text-lg font-semibold mb-4">市場概況</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>上證指數</span>
                <span className="text-green-600">+1.2%</span>
              </div>
              <div className="flex justify-between">
                <span>深證成指</span>
                <span className="text-red-600">-0.5%</span>
              </div>
            </div>
          </div>
        </GridItem>
        
        <GridItem>
          <div className="trading-card">
            <h3 className="text-lg font-semibold mb-4">快速操作</h3>
            <div className="space-y-2">
              <button className="btn btn-primary w-full">買入</button>
              <button className="btn btn-secondary w-full">賣出</button>
            </div>
          </div>
        </GridItem>
      </Grid>
    </Container>
  );
};

/**
 * 主要示範組件
 */
export const ResponsiveDemo: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <Container variant="default" enablePadding>
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            TradingAgents 響應式設計系統
          </h1>
          <p className="text-xl text-gray-600">
            天工(TianGong) - 第二階段Week2 UX優化
          </p>
        </div>
      </Container>

      <div className="space-y-12">
        <HookDemonstration />
        <GridDemonstration />
        <CustomGridDemonstration />
      </div>
    </div>
  );
};

export default ResponsiveDemo;
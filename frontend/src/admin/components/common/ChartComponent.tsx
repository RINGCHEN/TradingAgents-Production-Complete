/**
 * Chart.js整合組件
 * 提供統一的圖表渲染功能
 */

import React, { useEffect, useRef } from 'react';

declare global {
  interface Window {
    Chart: any;
  }
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
  }[];
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    legend?: {
      display?: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display?: boolean;
      text?: string;
    };
  };
  scales?: {
    x?: {
      display?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
    y?: {
      display?: boolean;
      beginAtZero?: boolean;
      title?: {
        display?: boolean;
        text?: string;
      };
    };
  };
}

interface ChartComponentProps {
  type: 'line' | 'bar' | 'doughnut' | 'pie' | 'radar' | 'polarArea';
  data: ChartData;
  options?: ChartOptions;
  width?: number;
  height?: number;
  className?: string;
}

export const ChartComponent: React.FC<ChartComponentProps> = ({
  type,
  data,
  options = {},
  width,
  height,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!canvasRef.current) {
      console.warn('Canvas not available');
      return;
    }

    // 確保 Chart.js 和控制器已載入
    const initChart = () => {
      if (!window.Chart) {
        console.warn('Chart.js not loaded, retrying...');
        setTimeout(initChart, 100);
        return;
      }

      // 註冊必要的 Chart.js 組件
      try {
        if (window.Chart.register) {
          window.Chart.register(
            window.Chart.CategoryScale,
            window.Chart.LinearScale,
            window.Chart.PointElement,
            window.Chart.LineElement,
            window.Chart.BarElement,
            window.Chart.LineController,
            window.Chart.BarController,
            window.Chart.DoughnutController,
            window.Chart.PieController,
            window.Chart.ArcElement,
            window.Chart.Title,
            window.Chart.Tooltip,
            window.Chart.Legend,
            window.Chart.Filler
          );
        }
      } catch (error) {
        console.warn('Chart.js registration error (continuing anyway):', error);
      }

      // 銷毀現有圖表
      if (chartRef.current) {
        chartRef.current.destroy();
      }

      // 默認配置
      const defaultOptions: ChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          }
        },
        scales: type === 'line' || type === 'bar' ? {
          x: {
            display: true
          },
          y: {
            display: true,
            beginAtZero: true
          }
        } : undefined
      };

      // 合併配置
      const finalOptions = {
        ...defaultOptions,
        ...options,
        plugins: {
          ...defaultOptions.plugins,
          ...options.plugins
        }
      };

      // 創建新圖表
      try {
        const ctx = canvasRef.current!.getContext('2d');
        if (ctx) {
          chartRef.current = new window.Chart(ctx, {
            type,
            data,
            options: finalOptions
          });
          console.log(`✅ Chart created successfully: ${type}`);
        }
      } catch (error) {
        console.error(`❌ Failed to create ${type} chart:`, error);
        
        // 降級處理：顯示錯誤信息
        if (canvasRef.current) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            ctx.fillStyle = '#f8f9fa';
            ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            ctx.fillStyle = '#6c757d';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('圖表暫時無法載入', canvasRef.current.width / 2, canvasRef.current.height / 2);
          }
        }
      }
    };

    initChart();

    // 清理函數
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [type, data, options]);

  return (
    <div className={`chart-container ${className}`}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ maxHeight: height || '400px' }}
      />
    </div>
  );
};

// 預設圖表組件
export const LineChart: React.FC<Omit<ChartComponentProps, 'type'>> = (props) => (
  <ChartComponent type="line" {...props} />
);

export const BarChart: React.FC<Omit<ChartComponentProps, 'type'>> = (props) => (
  <ChartComponent type="bar" {...props} />
);

export const DoughnutChart: React.FC<Omit<ChartComponentProps, 'type'>> = (props) => (
  <ChartComponent type="doughnut" {...props} />
);

export const PieChart: React.FC<Omit<ChartComponentProps, 'type'>> = (props) => (
  <ChartComponent type="pie" {...props} />
);

// 預設圖表配置
export const chartConfigs = {
  userGrowth: {
    backgroundColor: 'rgba(102, 126, 234, 0.1)',
    borderColor: 'rgba(102, 126, 234, 1)',
    borderWidth: 2,
    fill: true
  },
  revenue: {
    backgroundColor: 'rgba(40, 167, 69, 0.1)',
    borderColor: 'rgba(40, 167, 69, 1)',
    borderWidth: 2,
    fill: true
  },
  apiUsage: {
    backgroundColor: 'rgba(23, 162, 184, 0.1)',
    borderColor: 'rgba(23, 162, 184, 1)',
    borderWidth: 2,
    fill: true
  },
  systemMetrics: {
    backgroundColor: [
      'rgba(102, 126, 234, 0.8)',
      'rgba(40, 167, 69, 0.8)',
      'rgba(23, 162, 184, 0.8)',
      'rgba(255, 193, 7, 0.8)'
    ],
    borderColor: [
      'rgba(102, 126, 234, 1)',
      'rgba(40, 167, 69, 1)',
      'rgba(23, 162, 184, 1)',
      'rgba(255, 193, 7, 1)'
    ],
    borderWidth: 1
  }
};

export default ChartComponent;
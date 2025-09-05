/**
 * RealTimeChart - 即時數據圖表組件
 * 基於 Chart.js 的高性能即時圖表實現
 * 支援多種圖表類型和即時數據更新
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  LineController,
  BarController,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartConfiguration,
  ChartData,
  ChartOptions
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { adminApiService } from '../../services/AdminApiService_Fixed';

// 註冊 Chart.js 組件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  LineController,
  BarController,
  Title,
  Tooltip,
  Legend,
  Filler
);

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface DataSeries {
  id: string;
  name: string;
  data: ChartDataPoint[];
  color?: string;
  type?: 'line' | 'bar' | 'area';
}

export interface RealTimeChartProps {
  title?: string;
  width?: number;
  height?: number;
  maxDataPoints?: number;
  updateInterval?: number;
  chartType?: 'line' | 'bar' | 'area' | 'mixed';
  dataSeries: DataSeries[];
  onDataUpdate?: (newData: ChartDataPoint[]) => void;
  enableRealTimeUpdate?: boolean;
  showLegend?: boolean;
  showGridLines?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * RealTimeChart - 即時圖表組件
 * 提供高性能的即時數據圖表顯示功能
 */
export const RealTimeChart: React.FC<RealTimeChartProps> = ({
  title = '即時數據圖表',
  width = 800,
  height = 400,
  maxDataPoints = 50,
  updateInterval = 5000,
  chartType = 'line',
  dataSeries,
  onDataUpdate,
  enableRealTimeUpdate = true,
  showLegend = true,
  showGridLines = true,
  className = '',
  style = {}
}) => {
  const chartRef = useRef<ChartJS>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData<'line' | 'bar'>>({
    labels: [],
    datasets: []
  });

  // 生成圖表配置
  const generateChartOptions = useCallback((): ChartOptions<'line' | 'bar'> => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index' as const,
        intersect: false,
      },
      plugins: {
        legend: {
          display: showLegend,
          position: 'top' as const,
        },
        title: {
          display: !!title,
          text: title,
          font: {
            size: 16,
            weight: 'bold'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: 'white',
          bodyColor: 'white',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          borderWidth: 1,
          callbacks: {
            label: function(context) {
              const seriesName = context.dataset.label || '';
              const value = context.parsed.y;
              return `${seriesName}: ${value.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          display: true,
          grid: {
            display: showGridLines,
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            maxRotation: 45,
            color: 'rgba(255, 255, 255, 0.7)'
          }
        },
        y: {
          display: true,
          grid: {
            display: showGridLines,
            color: 'rgba(255, 255, 255, 0.1)'
          },
          ticks: {
            color: 'rgba(255, 255, 255, 0.7)',
            callback: function(value) {
              return typeof value === 'number' ? value.toLocaleString() : value;
            }
          }
        }
      },
      animation: {
        duration: enableRealTimeUpdate ? 300 : 1000,
        easing: 'easeInOutQuart'
      }
    };
  }, [title, showLegend, showGridLines, enableRealTimeUpdate]);

  // 將數據系列轉換為 Chart.js 格式
  const convertDataSeriesToChartData = useCallback((series: DataSeries[]): ChartData<'line' | 'bar'> => {
    if (!series.length) {
      return { labels: [], datasets: [] };
    }

    // 獲取所有時間戳
    const allTimestamps = new Set<string>();
    series.forEach(s => {
      s.data.forEach(point => allTimestamps.add(point.timestamp));
    });

    const labels = Array.from(allTimestamps).sort().slice(-maxDataPoints);
    
    const datasets = series.map((serie, index) => {
      const colors = [
        'rgb(54, 162, 235)',
        'rgb(255, 99, 132)',
        'rgb(75, 192, 192)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)',
        'rgb(255, 205, 86)'
      ];
      
      const color = serie.color || colors[index % colors.length];
      const type = serie.type || chartType;
      
      const data = labels.map(label => {
        const point = serie.data.find(p => p.timestamp === label);
        return point ? point.value : 0;
      });

      const baseConfig = {
        label: serie.name,
        data,
        borderColor: color,
        backgroundColor: type === 'area' 
          ? color.replace('rgb', 'rgba').replace(')', ', 0.2)')
          : color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 6,
        tension: 0.4
      };

      if (type === 'area') {
        return {
          ...baseConfig,
          fill: true,
          type: 'line' as const
        };
      }

      return {
        ...baseConfig,
        type: type === 'line' ? 'line' as const : 'bar' as const
      };
    });

    return { labels, datasets };
  }, [chartType, maxDataPoints]);

  // 模擬即時數據更新
  const generateMockRealTimeData = useCallback(async (): Promise<ChartDataPoint[]> => {
    try {
      setIsLoading(true);
      setError(null);

      // 模擬API調用延遲
      await new Promise(resolve => setTimeout(resolve, 200));

      const timestamp = new Date().toLocaleTimeString();
      const mockData: ChartDataPoint[] = [
        {
          timestamp,
          value: Math.floor(Math.random() * 100) + 50,
          label: 'CPU使用率'
        },
        {
          timestamp,
          value: Math.floor(Math.random() * 80) + 20,
          label: '記憶體使用率'
        },
        {
          timestamp,
          value: Math.floor(Math.random() * 1000) + 100,
          label: '網路流量'
        }
      ];

      return mockData;
    } catch (err) {
      setError(err instanceof Error ? err.message : '獲取數據失敗');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 更新圖表數據
  const updateChartData = useCallback(() => {
    const newChartData = convertDataSeriesToChartData(dataSeries);
    setChartData(newChartData);
  }, [dataSeries, convertDataSeriesToChartData]);

  // 即時數據更新效果
  useEffect(() => {
    if (!enableRealTimeUpdate) return;

    const interval = setInterval(async () => {
      const newData = await generateMockRealTimeData();
      if (newData.length > 0 && onDataUpdate) {
        onDataUpdate(newData);
      }
    }, updateInterval);

    return () => clearInterval(interval);
  }, [enableRealTimeUpdate, updateInterval, generateMockRealTimeData, onDataUpdate]);

  // 初始化和數據變更效果
  useEffect(() => {
    updateChartData();
  }, [dataSeries, updateChartData]);

  const chartOptions = generateChartOptions();

  return (
    <div 
      className={`realtime-chart-container ${className}`}
      style={{
        width: width || '100%',
        height: height || 400,
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.05)',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        ...style
      }}
    >
      {error && (
        <div style={{
          color: 'red',
          backgroundColor: 'rgba(255, 0, 0, 0.1)',
          padding: '8px',
          borderRadius: '4px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          錯誤: {error}
        </div>
      )}

      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: '14px'
        }}>
          正在載入數據...
        </div>
      )}

      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <Chart
          ref={chartRef}
          type={chartType === 'mixed' ? 'line' : chartType}
          data={chartData}
          options={chartOptions}
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {enableRealTimeUpdate && (
        <div style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          backgroundColor: 'rgba(0, 255, 0, 0.2)',
          color: 'lime',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 'bold'
        }}>
          🔴 LIVE
        </div>
      )}
    </div>
  );
};

export default RealTimeChart;
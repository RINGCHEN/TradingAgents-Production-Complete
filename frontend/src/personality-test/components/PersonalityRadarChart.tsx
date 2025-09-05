import React, { useEffect, useRef } from 'react';
import { DimensionScores } from '../services/PersonalityTestAPI';
import './PersonalityRadarChart.css';

interface PersonalityRadarChartProps {
  scores: DimensionScores;
  size?: number;
  animated?: boolean;
  showLabels?: boolean;
  showValues?: boolean;
}

interface RadarPoint {
  x: number;
  y: number;
  value: number;
  label: string;
}

const PersonalityRadarChart: React.FC<PersonalityRadarChartProps> = ({
  scores,
  size = 300,
  animated = true,
  showLabels = true,
  showValues = true
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const progressRef = useRef<number>(0);

  // 維度標籤映射
  const dimensionLabels: Record<keyof DimensionScores, string> = {
    risk_tolerance: '風險承受',
    emotional_control: '情緒控制',
    analytical_thinking: '分析思維',
    market_sensitivity: '市場敏感',
    long_term_vision: '長期視野'
  };

  // 將分數轉換為雷達圖點
  const getRadarPoints = (scores: DimensionScores, progress: number = 1): RadarPoint[] => {
    const dimensions = Object.keys(scores) as (keyof DimensionScores)[];
    const center = size / 2;
    const radius = (size * 0.35) * progress; // 動畫進度控制半徑

    return dimensions.map((dimension, index) => {
      const angle = (index * 2 * Math.PI) / dimensions.length - Math.PI / 2;
      const value = scores[dimension];
      const normalizedValue = value / 100;
      const pointRadius = radius * normalizedValue;

      return {
        x: center + Math.cos(angle) * pointRadius,
        y: center + Math.sin(angle) * pointRadius,
        value: value,
        label: dimensionLabels[dimension]
      };
    });
  };

  // 繪製雷達圖
  const drawRadarChart = (progress: number = 1) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清除畫布
    ctx.clearRect(0, 0, size, size);

    const center = size / 2;
    const maxRadius = size * 0.35;
    const points = getRadarPoints(scores, progress);

    // 繪製背景網格
    ctx.strokeStyle = 'rgba(102, 126, 234, 0.2)';
    ctx.lineWidth = 1;

    // 繪製同心圓
    for (let i = 1; i <= 5; i++) {
      ctx.beginPath();
      ctx.arc(center, center, (maxRadius * i) / 5, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // 繪製軸線
    points.forEach((_, index) => {
      const angle = (index * 2 * Math.PI) / points.length - Math.PI / 2;
      const endX = center + Math.cos(angle) * maxRadius;
      const endY = center + Math.sin(angle) * maxRadius;

      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.lineTo(endX, endY);
      ctx.stroke();
    });

    // 繪製數據區域
    if (points.length > 0) {
      // 填充區域
      ctx.fillStyle = 'rgba(102, 126, 234, 0.2)';
      ctx.strokeStyle = 'rgba(102, 126, 234, 0.8)';
      ctx.lineWidth = 2;

      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.forEach((point, index) => {
        if (index > 0) {
          ctx.lineTo(point.x, point.y);
        }
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // 繪製數據點
      points.forEach((point) => {
        ctx.fillStyle = '#667eea';
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
        ctx.fill();

        // 繪製數值
        if (showValues) {
          ctx.fillStyle = '#1e293b';
          ctx.font = 'bold 12px Arial';
          ctx.textAlign = 'center';
          ctx.fillText(
            point.value.toString(),
            point.x,
            point.y - 8
          );
        }
      });
    }

    // 繪製標籤
    if (showLabels) {
      ctx.fillStyle = '#4a5568';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';

      points.forEach((point, index) => {
        const angle = (index * 2 * Math.PI) / points.length - Math.PI / 2;
        const labelRadius = maxRadius + 20;
        const labelX = center + Math.cos(angle) * labelRadius;
        const labelY = center + Math.sin(angle) * labelRadius;

        // 調整文字對齊
        if (labelX < center - 10) {
          ctx.textAlign = 'right';
        } else if (labelX > center + 10) {
          ctx.textAlign = 'left';
        } else {
          ctx.textAlign = 'center';
        }

        ctx.fillText(point.label, labelX, labelY + 5);
      });
    }
  };

  // 動畫效果
  useEffect(() => {
    if (!animated) {
      drawRadarChart(1);
      return;
    }

    const animate = () => {
      progressRef.current += 0.02;
      
      if (progressRef.current >= 1) {
        progressRef.current = 1;
        drawRadarChart(1);
        return;
      }

      // 使用緩動函數
      const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
      const easedProgress = easeOutCubic(progressRef.current);
      
      drawRadarChart(easedProgress);
      animationRef.current = requestAnimationFrame(animate);
    };

    // 延遲開始動畫
    setTimeout(() => {
      progressRef.current = 0;
      animationRef.current = requestAnimationFrame(animate);
    }, 500);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [scores, animated, size, showLabels, showValues]);

  return (
    <div className="personality-radar-chart">
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="radar-canvas"
      />
      
      {/* 圖例 */}
      <div className="radar-legend">
        {Object.entries(scores).map(([dimension, value]) => (
          <div key={dimension} className="legend-item">
            <div className="legend-color"></div>
            <span className="legend-label">
              {dimensionLabels[dimension as keyof DimensionScores]}
            </span>
            <span className="legend-value">{value}/100</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PersonalityRadarChart;
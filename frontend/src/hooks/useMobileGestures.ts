/**
 * 移動設備手勢支持 Hook (useMobileGestures)
 * TradingAgents 前端會員系統優化 - 階段二核心組件
 * 
 * 功能：
 * 1. 滑動手勢檢測和處理
 * 2. 捏合縮放手勢支持
 * 3. 長按和雙擊檢測
 * 4. 觸控反饋和動畫
 * 5. 自定義手勢配置
 * 
 * @author Claude Team
 * @version 1.0 - 2025-09-08
 */

import { useEffect, useRef, useCallback } from 'react';

interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

interface SwipeGesture {
  direction: 'up' | 'down' | 'left' | 'right';
  distance: number;
  velocity: number;
  duration: number;
}

interface PinchGesture {
  scale: number;
  center: TouchPoint;
  startDistance: number;
  currentDistance: number;
}

interface GestureConfig {
  swipeThreshold: number;
  velocityThreshold: number;
  longPressDelay: number;
  doubleTapDelay: number;
  pinchThreshold: number;
}

interface GestureCallbacks {
  onSwipe?: (gesture: SwipeGesture) => void;
  onPinch?: (gesture: PinchGesture) => void;
  onLongPress?: (point: TouchPoint) => void;
  onDoubleTap?: (point: TouchPoint) => void;
  onTap?: (point: TouchPoint) => void;
  onTouchStart?: (point: TouchPoint) => void;
  onTouchEnd?: (point: TouchPoint) => void;
}

const DEFAULT_CONFIG: GestureConfig = {
  swipeThreshold: 50,
  velocityThreshold: 0.3,
  longPressDelay: 500,
  doubleTapDelay: 300,
  pinchThreshold: 10
};

export const useMobileGestures = (
  elementRef: React.RefObject<HTMLElement>,
  callbacks: GestureCallbacks = {},
  config: Partial<GestureConfig> = {}
) => {
  const fullConfig = { ...DEFAULT_CONFIG, ...config };
  
  // 手勢狀態追蹤
  const gestureState = useRef({
    isTracking: false,
    startPoints: [] as TouchPoint[],
    currentPoints: [] as TouchPoint[],
    lastTapTime: 0,
    longPressTimer: null as NodeJS.Timeout | null,
    initialDistance: 0
  });

  // 獲取觸控點信息
  const getTouchPoint = useCallback((touch: Touch): TouchPoint => ({
    x: touch.clientX,
    y: touch.clientY,
    timestamp: Date.now()
  }), []);

  // 計算兩點距離
  const getDistance = useCallback((point1: TouchPoint, point2: TouchPoint): number => {
    const dx = point1.x - point2.x;
    const dy = point1.y - point2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  // 計算滑動方向
  const getSwipeDirection = useCallback((start: TouchPoint, end: TouchPoint): 'up' | 'down' | 'left' | 'right' => {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    
    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0 ? 'right' : 'left';
    } else {
      return dy > 0 ? 'down' : 'up';
    }
  }, []);

  // 清除長按定時器
  const clearLongPressTimer = useCallback(() => {
    if (gestureState.current.longPressTimer) {
      clearTimeout(gestureState.current.longPressTimer);
      gestureState.current.longPressTimer = null;
    }
  }, []);

  // 觸控開始處理
  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (!elementRef.current?.contains(e.target as Node)) return;
    
    e.preventDefault();
    
    const touches = Array.from(e.touches).map(getTouchPoint);
    gestureState.current.startPoints = touches;
    gestureState.current.currentPoints = touches;
    gestureState.current.isTracking = true;
    
    // 記錄初始距離（用於捏合手勢）
    if (touches.length === 2) {
      gestureState.current.initialDistance = getDistance(touches[0], touches[1]);
    }
    
    // 調用回調
    if (callbacks.onTouchStart && touches.length === 1) {
      callbacks.onTouchStart(touches[0]);
    }
    
    // 設置長按定時器
    if (touches.length === 1) {
      gestureState.current.longPressTimer = setTimeout(() => {
        if (gestureState.current.isTracking && callbacks.onLongPress) {
          console.log('📱 長按手勢檢測');
          callbacks.onLongPress(touches[0]);
          
          // 觸覺反饋
          if ('vibrate' in navigator) {
            navigator.vibrate(100);
          }
        }
      }, fullConfig.longPressDelay);
    }
  }, [elementRef, callbacks, getTouchPoint, getDistance, fullConfig.longPressDelay]);

  // 觸控移動處理
  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!gestureState.current.isTracking) return;
    
    e.preventDefault();
    
    const touches = Array.from(e.touches).map(getTouchPoint);
    gestureState.current.currentPoints = touches;
    
    // 移動時取消長按
    clearLongPressTimer();
    
    // 處理捏合手勢
    if (touches.length === 2 && gestureState.current.startPoints.length === 2) {
      const currentDistance = getDistance(touches[0], touches[1]);
      const startDistance = gestureState.current.initialDistance;
      
      if (Math.abs(currentDistance - startDistance) > fullConfig.pinchThreshold) {
        const scale = currentDistance / startDistance;
        const center: TouchPoint = {
          x: (touches[0].x + touches[1].x) / 2,
          y: (touches[0].y + touches[1].y) / 2,
          timestamp: Date.now()
        };
        
        const pinchGesture: PinchGesture = {
          scale,
          center,
          startDistance,
          currentDistance
        };
        
        if (callbacks.onPinch) {
          callbacks.onPinch(pinchGesture);
        }
      }
    }
  }, [clearLongPressTimer, getDistance, fullConfig.pinchThreshold, callbacks]);

  // 觸控結束處理
  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (!gestureState.current.isTracking) return;
    
    e.preventDefault();
    clearLongPressTimer();
    
    const endTime = Date.now();
    const startPoints = gestureState.current.startPoints;
    const currentPoints = gestureState.current.currentPoints;
    
    // 單指操作
    if (startPoints.length === 1 && currentPoints.length >= 1) {
      const startPoint = startPoints[0];
      const endPoint = currentPoints[0];
      
      const distance = getDistance(startPoint, endPoint);
      const duration = endTime - startPoint.timestamp;
      const velocity = distance / duration;
      
      // 調用觸控結束回調
      if (callbacks.onTouchEnd) {
        callbacks.onTouchEnd(endPoint);
      }
      
      // 判斷是滑動還是點擊
      if (distance > fullConfig.swipeThreshold && velocity > fullConfig.velocityThreshold) {
        // 滑動手勢
        const direction = getSwipeDirection(startPoint, endPoint);
        const swipeGesture: SwipeGesture = {
          direction,
          distance,
          velocity,
          duration
        };
        
        console.log('📱 滑動手勢檢測:', direction, distance, velocity);
        
        if (callbacks.onSwipe) {
          callbacks.onSwipe(swipeGesture);
        }
        
        // 滑動觸覺反饋
        if ('vibrate' in navigator) {
          navigator.vibrate(30);
        }
      } else if (distance < fullConfig.swipeThreshold) {
        // 點擊手勢
        const currentTime = Date.now();
        const timeSinceLastTap = currentTime - gestureState.current.lastTapTime;
        
        if (timeSinceLastTap < fullConfig.doubleTapDelay) {
          // 雙擊
          console.log('📱 雙擊手勢檢測');
          
          if (callbacks.onDoubleTap) {
            callbacks.onDoubleTap(endPoint);
          }
          
          // 雙擊觸覺反饋
          if ('vibrate' in navigator) {
            navigator.vibrate([50, 30, 50]);
          }
          
          gestureState.current.lastTapTime = 0; // 重置以防三擊
        } else {
          // 單擊
          console.log('📱 單擊手勢檢測');
          
          if (callbacks.onTap) {
            callbacks.onTap(endPoint);
          }
          
          // 單擊觸覺反饋
          if ('vibrate' in navigator) {
            navigator.vibrate(20);
          }
          
          gestureState.current.lastTapTime = currentTime;
        }
      }
    }
    
    // 重置狀態
    gestureState.current.isTracking = false;
    gestureState.current.startPoints = [];
    gestureState.current.currentPoints = [];
    gestureState.current.initialDistance = 0;
  }, [
    clearLongPressTimer,
    getDistance,
    getSwipeDirection,
    fullConfig.swipeThreshold,
    fullConfig.velocityThreshold,
    fullConfig.doubleTapDelay,
    callbacks
  ]);

  // 觸控取消處理
  const handleTouchCancel = useCallback(() => {
    clearLongPressTimer();
    gestureState.current.isTracking = false;
    gestureState.current.startPoints = [];
    gestureState.current.currentPoints = [];
    gestureState.current.initialDistance = 0;
  }, [clearLongPressTimer]);

  // 設置事件監聽器
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    // 檢查是否支持觸控
    const supportsTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (!supportsTouch) {
      console.log('📱 當前設備不支持觸控操作');
      return;
    }
    
    console.log('📱 移動手勢監聽器已啟用');
    
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });
    element.addEventListener('touchcancel', handleTouchCancel, { passive: false });
    
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
      element.removeEventListener('touchcancel', handleTouchCancel);
      clearLongPressTimer();
    };
  }, [
    elementRef,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
    handleTouchCancel,
    clearLongPressTimer
  ]);

  // 清理函數
  useEffect(() => {
    return () => {
      clearLongPressTimer();
    };
  }, [clearLongPressTimer]);

  // 返回手勢狀態和控制方法
  return {
    isGestureActive: gestureState.current.isTracking,
    
    // 手動觸發手勢
    triggerTactileFeedback: (pattern: number | number[] = 50) => {
      if ('vibrate' in navigator) {
        navigator.vibrate(pattern);
      }
    },
    
    // 獲取當前觸控點
    getCurrentTouchPoints: () => gestureState.current.currentPoints,
    
    // 重置手勢狀態
    resetGestureState: () => {
      clearLongPressTimer();
      gestureState.current.isTracking = false;
      gestureState.current.startPoints = [];
      gestureState.current.currentPoints = [];
      gestureState.current.initialDistance = 0;
    }
  };
};

export type { SwipeGesture, PinchGesture, TouchPoint, GestureConfig, GestureCallbacks };
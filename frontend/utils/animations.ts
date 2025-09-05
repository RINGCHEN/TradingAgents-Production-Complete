/**
 * 微交互動畫系統 - 第二階段Week 2 UX優化
 * 狀態轉換動畫、數據可視化動畫、導航動畫效果
 * 支援減少動畫偏好、性能優化、無障礙友好
 */

// 動畫類型定義
export type AnimationType = 
  | 'fadeIn' | 'fadeOut' | 'fadeInUp' | 'fadeInDown' | 'fadeInLeft' | 'fadeInRight'
  | 'slideUp' | 'slideDown' | 'slideLeft' | 'slideRight'
  | 'scaleIn' | 'scaleOut' | 'scaleUp' | 'scaleDown'
  | 'bounceIn' | 'bounceOut' | 'shake' | 'pulse'
  | 'rotateIn' | 'rotateOut' | 'flipX' | 'flipY'
  | 'zoomIn' | 'zoomOut' | 'elastic' | 'rubber'
  | 'tada' | 'swing' | 'wobble' | 'jello'
  | 'heartbeat' | 'flash' | 'rubberBand';

// 動畫持續時間
export type AnimationDuration = 'fast' | 'medium' | 'slow' | 'extra-slow';

// 動畫緩動函數
export type AnimationEasing = 
  | 'linear' | 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out'
  | 'bounce' | 'elastic' | 'back' | 'anticipate' | 'overshoot';

// 動畫配置介面
export interface AnimationConfig {
  type: AnimationType;
  duration?: AnimationDuration | number;
  delay?: number;
  easing?: AnimationEasing;
  iterations?: number | 'infinite';
  direction?: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
  fillMode?: 'none' | 'forwards' | 'backwards' | 'both';
  playState?: 'running' | 'paused';
}

// 動畫常數
export const ANIMATION_DURATIONS = {
  fast: 200,
  medium: 400,
  slow: 600,
  'extra-slow': 1000
} as const;

export const EASING_FUNCTIONS = {
  linear: 'linear',
  ease: 'ease',
  'ease-in': 'ease-in',
  'ease-out': 'ease-out',
  'ease-in-out': 'ease-in-out',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  back: 'cubic-bezier(0.6, -0.28, 0.735, 0.045)',
  anticipate: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  overshoot: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
} as const;

// 動畫關鍵幀定義
export const ANIMATION_KEYFRAMES = {
  fadeIn: `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `,
  fadeOut: `
    @keyframes fadeOut {
      from { opacity: 1; }
      to { opacity: 0; }
    }
  `,
  fadeInUp: `
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,
  fadeInDown: `
    @keyframes fadeInDown {
      from {
        opacity: 0;
        transform: translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `,
  fadeInLeft: `
    @keyframes fadeInLeft {
      from {
        opacity: 0;
        transform: translateX(-20px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,
  fadeInRight: `
    @keyframes fadeInRight {
      from {
        opacity: 0;
        transform: translateX(20px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
  `,
  slideUp: `
    @keyframes slideUp {
      from { transform: translateY(100%); }
      to { transform: translateY(0); }
    }
  `,
  slideDown: `
    @keyframes slideDown {
      from { transform: translateY(-100%); }
      to { transform: translateY(0); }
    }
  `,
  slideLeft: `
    @keyframes slideLeft {
      from { transform: translateX(100%); }
      to { transform: translateX(0); }
    }
  `,
  slideRight: `
    @keyframes slideRight {
      from { transform: translateX(-100%); }
      to { transform: translateX(0); }
    }
  `,
  scaleIn: `
    @keyframes scaleIn {
      from { 
        opacity: 0;
        transform: scale(0.8); 
      }
      to { 
        opacity: 1;
        transform: scale(1); 
      }
    }
  `,
  scaleOut: `
    @keyframes scaleOut {
      from { 
        opacity: 1;
        transform: scale(1); 
      }
      to { 
        opacity: 0;
        transform: scale(0.8); 
      }
    }
  `,
  scaleUp: `
    @keyframes scaleUp {
      from { transform: scale(1); }
      to { transform: scale(1.1); }
    }
  `,
  scaleDown: `
    @keyframes scaleDown {
      from { transform: scale(1.1); }
      to { transform: scale(1); }
    }
  `,
  bounceIn: `
    @keyframes bounceIn {
      0% {
        opacity: 0;
        transform: scale(0.3);
      }
      50% {
        opacity: 1;
        transform: scale(1.05);
      }
      70% { transform: scale(0.9); }
      100% {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,
  bounceOut: `
    @keyframes bounceOut {
      0% {
        opacity: 1;
        transform: scale(1);
      }
      25% { transform: scale(0.95); }
      50% {
        opacity: 1;
        transform: scale(1.1);
      }
      100% {
        opacity: 0;
        transform: scale(0.3);
      }
    }
  `,
  shake: `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
      20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
  `,
  pulse: `
    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }
  `,
  rotateIn: `
    @keyframes rotateIn {
      from {
        opacity: 0;
        transform: rotate(-180deg);
      }
      to {
        opacity: 1;
        transform: rotate(0deg);
      }
    }
  `,
  rotateOut: `
    @keyframes rotateOut {
      from {
        opacity: 1;
        transform: rotate(0deg);
      }
      to {
        opacity: 0;
        transform: rotate(180deg);
      }
    }
  `,
  flipX: `
    @keyframes flipX {
      0% { transform: rotateX(0deg); }
      50% { transform: rotateX(-90deg); }
      100% { transform: rotateX(0deg); }
    }
  `,
  flipY: `
    @keyframes flipY {
      0% { transform: rotateY(0deg); }
      50% { transform: rotateY(-90deg); }
      100% { transform: rotateY(0deg); }
    }
  `,
  zoomIn: `
    @keyframes zoomIn {
      from {
        opacity: 0;
        transform: scale(0);
      }
      to {
        opacity: 1;
        transform: scale(1);
      }
    }
  `,
  zoomOut: `
    @keyframes zoomOut {
      from {
        opacity: 1;
        transform: scale(1);
      }
      to {
        opacity: 0;
        transform: scale(0);
      }
    }
  `,
  elastic: `
    @keyframes elastic {
      0% { transform: scale(1); }
      30% { transform: scale(1.25); }
      40% { transform: scale(0.75); }
      60% { transform: scale(1.15); }
      80% { transform: scale(0.95); }
      100% { transform: scale(1); }
    }
  `,
  rubber: `
    @keyframes rubber {
      0% { transform: scale(1); }
      30% { transform: scale(1.25, 0.75); }
      40% { transform: scale(0.75, 1.25); }
      50% { transform: scale(1.15, 0.85); }
      65% { transform: scale(0.95, 1.05); }
      75% { transform: scale(1.05, 0.95); }
      100% { transform: scale(1); }
    }
  `,
  tada: `
    @keyframes tada {
      0% { transform: scale(1); }
      10%, 20% {
        transform: scale(0.9) rotate(-3deg);
      }
      30%, 50%, 70%, 90% {
        transform: scale(1.1) rotate(3deg);
      }
      40%, 60%, 80% {
        transform: scale(1.1) rotate(-3deg);
      }
      100% { transform: scale(1) rotate(0); }
    }
  `,
  swing: `
    @keyframes swing {
      20% { transform: rotate(15deg); }
      40% { transform: rotate(-10deg); }
      60% { transform: rotate(5deg); }
      80% { transform: rotate(-5deg); }
      100% { transform: rotate(0deg); }
    }
  `,
  wobble: `
    @keyframes wobble {
      0% { transform: translateX(0%); }
      15% { transform: translateX(-25%) rotate(-5deg); }
      30% { transform: translateX(20%) rotate(3deg); }
      45% { transform: translateX(-15%) rotate(-3deg); }
      60% { transform: translateX(10%) rotate(2deg); }
      75% { transform: translateX(-5%) rotate(-1deg); }
      100% { transform: translateX(0%); }
    }
  `,
  jello: `
    @keyframes jello {
      0%, 11.1%, 100% { transform: none; }
      22.2% { transform: skewX(-12.5deg) skewY(-12.5deg); }
      33.3% { transform: skewX(6.25deg) skewY(6.25deg); }
      44.4% { transform: skewX(-3.125deg) skewY(-3.125deg); }
      55.5% { transform: skewX(1.5625deg) skewY(1.5625deg); }
      66.6% { transform: skewX(-0.78125deg) skewY(-0.78125deg); }
      77.7% { transform: skewX(0.390625deg) skewY(0.390625deg); }
      88.8% { transform: skewX(-0.1953125deg) skewY(-0.1953125deg); }
    }
  `,
  heartbeat: `
    @keyframes heartbeat {
      0% { transform: scale(1); }
      14% { transform: scale(1.3); }
      28% { transform: scale(1); }
      42% { transform: scale(1.3); }
      70% { transform: scale(1); }
    }
  `,
  flash: `
    @keyframes flash {
      0%, 50%, 100% { opacity: 1; }
      25%, 75% { opacity: 0; }
    }
  `,
  rubberBand: `
    @keyframes rubberBand {
      0% { transform: scale(1); }
      30% { transform: scale(1.25, 0.75); }
      40% { transform: scale(0.75, 1.25); }
      50% { transform: scale(1.15, 0.85); }
      65% { transform: scale(0.95, 1.05); }
      75% { transform: scale(1.05, 0.95); }
      100% { transform: scale(1); }
    }
  `
};

// 動畫管理器類別
class AnimationManager {
  private styleElement: HTMLStyleElement | null = null;
  private animationCounter = 0;
  private prefersReducedMotion = false;

  constructor() {
    this.init();
  }

  // 初始化動畫管理器
  private init() {
    // 檢測減少動畫偏好
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    this.prefersReducedMotion = mediaQuery.matches;
    
    mediaQuery.addEventListener('change', (e: any) => {
      this.prefersReducedMotion = e.matches;
    });

    // 創建樣式元素
    this.createStyleElement();
    
    // 注入關鍵幀
    this.injectKeyframes();
  }

  // 創建樣式元素
  private createStyleElement() {
    this.styleElement = document.createElement('style');
    this.styleElement.id = 'animation-keyframes';
    document.head.appendChild(this.styleElement);
  }

  // 注入關鍵幀動畫
  private injectKeyframes() {
    if (!this.styleElement) return;

    const keyframesCSS = Object.values(ANIMATION_KEYFRAMES).join('\n');
    this.styleElement.textContent = keyframesCSS;
  }

  // 生成動畫CSS
  private generateAnimationCSS(config: AnimationConfig): string {
    const {
      type,
      duration = 'medium',
      delay = 0,
      easing = 'ease-out',
      iterations = 1,
      direction = 'normal',
      fillMode = 'both'
    } = config;

    // 如果用戶偏好減少動畫，返回基本樣式
    if (this.prefersReducedMotion) {
      return 'transition: opacity 0.1s ease;';
    }

    const durationValue = typeof duration === 'number' 
      ? `${duration}ms` 
      : `${ANIMATION_DURATIONS[duration]}ms`;
    
    const easingValue = EASING_FUNCTIONS[easing] || easing;
    const delayValue = delay > 0 ? `${delay}ms` : '0ms';
    const iterationValue = iterations === 'infinite' ? 'infinite' : iterations;

    return `
      animation-name: ${type};
      animation-duration: ${durationValue};
      animation-delay: ${delayValue};
      animation-timing-function: ${easingValue};
      animation-iteration-count: ${iterationValue};
      animation-direction: ${direction};
      animation-fill-mode: ${fillMode};
    `;
  }

  // 應用動畫到元素
  animate(element: HTMLElement, config: AnimationConfig): Promise<void> {
    return new Promise((resolve) => {
      if (this.prefersReducedMotion) {
        resolve();
        return;
      }

      const animationCSS = this.generateAnimationCSS(config);
      const originalStyle = element.style.cssText;
      
      // 應用動畫樣式
      element.style.cssText += ';' + animationCSS;

      // 監聽動畫結束
      const handleAnimationEnd = () => {
        element.removeEventListener('animationend', handleAnimationEnd);
        
        // 恢復原始樣式（如果需要）
        if (config.fillMode === 'none') {
          element.style.cssText = originalStyle;
        }
        
        resolve();
      };

      element.addEventListener('animationend', handleAnimationEnd);

      // 設置超時防止動畫卡住
      const timeout = (typeof config.duration === 'number' ? config.duration : ANIMATION_DURATIONS[config.duration || 'medium']) + (config.delay || 0) + 100;
      
      setTimeout(() => {
        element.removeEventListener('animationend', handleAnimationEnd);
        resolve();
      }, timeout);
    });
  }

  // 創建動畫序列
  sequence(element: HTMLElement, animations: AnimationConfig[]): Promise<void> {
    return animations.reduce(
      (promise, config) => promise.then(() => this.animate(element, config)),
      Promise.resolve()
    );
  }

  // 並行執行多個動畫
  parallel(animations: Array<{ element: HTMLElement; config: AnimationConfig }>): Promise<void[]> {
    return Promise.all(
      animations.map(({ element, config }) => this.animate(element, config))
    );
  }

  // 淡入動畫
  fadeIn(element: HTMLElement, duration: AnimationDuration = 'medium'): Promise<void> {
    return this.animate(element, {
      type: 'fadeIn',
      duration,
      easing: 'ease-out'
    });
  }

  // 淡出動畫
  fadeOut(element: HTMLElement, duration: AnimationDuration = 'medium'): Promise<void> {
    return this.animate(element, {
      type: 'fadeOut',
      duration,
      easing: 'ease-in'
    });
  }

  // 滑入動畫
  slideIn(element: HTMLElement, direction: 'up' | 'down' | 'left' | 'right' = 'up', duration: AnimationDuration = 'medium'): Promise<void> {
    const typeMap = {
      up: 'fadeInUp',
      down: 'fadeInDown',
      left: 'fadeInLeft',
      right: 'fadeInRight'
    };

    return this.animate(element, {
      type: typeMap[direction] as AnimationType,
      duration,
      easing: 'ease-out'
    });
  }

  // 縮放動畫
  scale(element: HTMLElement, direction: 'in' | 'out' = 'in', duration: AnimationDuration = 'medium'): Promise<void> {
    return this.animate(element, {
      type: direction === 'in' ? 'scaleIn' : 'scaleOut',
      duration,
      easing: 'bounce'
    });
  }

  // 彈跳動畫
  bounce(element: HTMLElement, direction: 'in' | 'out' = 'in', duration: AnimationDuration = 'medium'): Promise<void> {
    return this.animate(element, {
      type: direction === 'in' ? 'bounceIn' : 'bounceOut',
      duration,
      easing: 'bounce'
    });
  }

  // 脈衝動畫
  pulse(element: HTMLElement, iterations: number | 'infinite' = 'infinite'): Promise<void> {
    return this.animate(element, {
      type: 'pulse',
      duration: 'slow',
      iterations,
      easing: 'ease-in-out'
    });
  }

  // 震動動畫
  shake(element: HTMLElement): Promise<void> {
    return this.animate(element, {
      type: 'shake',
      duration: 'fast',
      easing: 'ease-in-out'
    });
  }

  // 數字計數動畫
  animateNumber(
    element: HTMLElement, 
    from: number, 
    to: number, 
    duration: number = 1000,
    formatter?: (value: number) => string
  ): Promise<void> {
    return new Promise((resolve) => {
      if (this.prefersReducedMotion) {
        element.textContent = formatter ? formatter(to) : to.toString();
        resolve();
        return;
      }

      const start = Date.now();
      const difference = to - from;

      const step = () => {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        
        // 使用緩動函數
        const easedProgress = this.easeOutCubic(progress);
        const currentValue = from + (difference * easedProgress);
        
        element.textContent = formatter 
          ? formatter(Math.floor(currentValue))
          : Math.floor(currentValue).toString();

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          element.textContent = formatter ? formatter(to) : to.toString();
          resolve();
        }
      };

      requestAnimationFrame(step);
    });
  }

  // 緩動函數
  private easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  // 進度條動畫
  animateProgress(
    element: HTMLElement, 
    from: number, 
    to: number, 
    duration: number = 1000
  ): Promise<void> {
    return new Promise((resolve) => {
      if (this.prefersReducedMotion) {
        element.style.width = `${to}%`;
        resolve();
        return;
      }

      const start = Date.now();
      const difference = to - from;

      const step = () => {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        
        const easedProgress = this.easeOutCubic(progress);
        const currentValue = from + (difference * easedProgress);
        
        element.style.width = `${currentValue}%`;

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          element.style.width = `${to}%`;
          resolve();
        }
      };

      requestAnimationFrame(step);
    });
  }

  // 檢查是否偏好減少動畫
  getPrefersReducedMotion(): boolean {
    return this.prefersReducedMotion;
  }

  // 設置動畫偏好（用於測試）
  setPrefersReducedMotion(value: boolean): void {
    this.prefersReducedMotion = value;
  }
}

// 創建全域實例
export const animationManager = new AnimationManager();

// 便利函數
export const animate = (element: HTMLElement, config: AnimationConfig) => 
  animationManager.animate(element, config);

export const fadeIn = (element: HTMLElement, duration?: AnimationDuration) => 
  animationManager.fadeIn(element, duration);

export const fadeOut = (element: HTMLElement, duration?: AnimationDuration) => 
  animationManager.fadeOut(element, duration);

export const slideIn = (
  element: HTMLElement, 
  direction?: 'up' | 'down' | 'left' | 'right', 
  duration?: AnimationDuration
) => animationManager.slideIn(element, direction, duration);

export const scale = (
  element: HTMLElement, 
  direction?: 'in' | 'out', 
  duration?: AnimationDuration
) => animationManager.scale(element, direction, duration);

export const bounce = (
  element: HTMLElement, 
  direction?: 'in' | 'out', 
  duration?: AnimationDuration
) => animationManager.bounce(element, direction, duration);

export const pulse = (element: HTMLElement, iterations?: number | 'infinite') => 
  animationManager.pulse(element, iterations);

export const shake = (element: HTMLElement) => animationManager.shake(element);

export const animateNumber = (
  element: HTMLElement, 
  from: number, 
  to: number, 
  duration?: number,
  formatter?: (value: number) => string
) => animationManager.animateNumber(element, from, to, duration, formatter);

export const animateProgress = (
  element: HTMLElement, 
  from: number, 
  to: number, 
  duration?: number
) => animationManager.animateProgress(element, from, to, duration);

export const sequence = (element: HTMLElement, animations: AnimationConfig[]) => 
  animationManager.sequence(element, animations);

export const parallel = (animations: Array<{ element: HTMLElement; config: AnimationConfig }>) => 
  animationManager.parallel(animations);

export const getPrefersReducedMotion = () => animationManager.getPrefersReducedMotion();

export default animationManager;
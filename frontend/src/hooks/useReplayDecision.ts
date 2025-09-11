import { useState, useEffect, useCallback } from 'react';

/**
 * 自定義Hook - 管理與GEMINI後端API的分級決策數據交互
 * 配合4層級用戶價值階梯系統
 */

interface ReplayDecisionResponse {
  user_tier: 'visitor' | 'trial' | 'free' | 'paid';
  trial_days_remaining?: number;
  analysis: {
    technical_analysis: string;
    fundamental_analysis: string;
    news_sentiment: string;
    recommendation?: {
      action: 'buy' | 'sell' | 'hold';
      confidence: number;
      target_price?: number;
      reasoning: string;
    };
  };
  upgrade_prompt?: string | {
    title: string;
    value_prop: string;
    cta: string;
  };
}

interface UseReplayDecisionOptions {
  stockSymbol: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseReplayDecisionReturn {
  data: ReplayDecisionResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  isUserTier: (tier: string) => boolean;
  canAccessRecommendation: boolean;
  needsUpgrade: boolean;
  isTrialActive: boolean;
  trialDaysLeft: number;
}

/**
 * API基礎URL配置 - 使用Emergency API進行聯調測試
 */
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8003' 
  : process.env.REACT_APP_API_BASE_URL || '';

/**
 * useReplayDecision Hook
 */
export const useReplayDecision = ({
  stockSymbol,
  autoRefresh = false,
  refreshInterval = 30000, // 30秒自動刷新
}: UseReplayDecisionOptions): UseReplayDecisionReturn => {
  const [data, setData] = useState<ReplayDecisionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 獲取分級決策數據
   */
  const fetchReplayDecision = useCallback(async (): Promise<void> => {
    if (!stockSymbol) {
      setError('股票代號不能為空');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // 準備請求headers
      const token = localStorage.getItem('authToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // 調用GEMINI改造後的API (修改為POST方法配合後端)
      const response = await fetch(
        `${API_BASE_URL}/api/v1/replay/decision`,
        {
          method: 'POST',
          headers,
          credentials: 'include', // 包含cookies
          body: JSON.stringify({
            stock_symbol: stockSymbol
          })
        }
      );

      if (!response.ok) {
        throw new Error(`API錯誤 (${response.status}): ${response.statusText}`);
      }

      const result: ReplayDecisionResponse = await response.json();
      
      // 數據驗證
      if (!result.user_tier || !result.analysis) {
        throw new Error('API返回數據格式錯誤');
      }

      setData(result);
      
      // 記錄使用統計（如果是付費用戶）
      if (result.user_tier === 'paid' || result.user_tier === 'trial') {
        recordAnalysisUsage(stockSymbol, result.user_tier);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '未知錯誤';
      setError(errorMessage);
      console.error('獲取分級決策數據失敗:', err);
      
      // 錯誤統計
      recordError('replay_decision_fetch', errorMessage);
      
    } finally {
      setLoading(false);
    }
  }, [stockSymbol]);

  /**
   * 檢查用戶層級
   */
  const isUserTier = useCallback((tier: string): boolean => {
    return data?.user_tier === tier;
  }, [data]);

  /**
   * 是否可以訪問投資建議
   */
  const canAccessRecommendation = useCallback((): boolean => {
    return data?.user_tier === 'paid' || data?.user_tier === 'trial';
  }, [data]);

  /**
   * 是否需要升級
   */
  const needsUpgrade = useCallback((): boolean => {
    return data?.user_tier === 'free' || data?.user_tier === 'visitor';
  }, [data]);

  /**
   * 試用期是否活躍
   */
  const isTrialActive = useCallback((): boolean => {
    return data?.user_tier === 'trial' && 
           (data?.trial_days_remaining || 0) > 0;
  }, [data]);

  /**
   * 試用期剩餘天數
   */
  const trialDaysLeft = useCallback((): number => {
    return data?.trial_days_remaining || 0;
  }, [data]);

  /**
   * 記錄分析使用統計
   */
  const recordAnalysisUsage = async (symbol: string, userTier: string): Promise<void> => {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) return;

      await fetch(`${API_BASE_URL}/api/v1/analytics/usage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          action: 'replay_decision',
          symbol,
          user_tier: userTier,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (err) {
      console.warn('記錄使用統計失敗:', err);
    }
  };

  /**
   * 記錄錯誤統計
   */
  const recordError = async (type: string, message: string): Promise<void> => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/analytics/error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error_type: type,
          message,
          stock_symbol: stockSymbol,
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent,
        }),
      });
    } catch (err) {
      console.warn('記錄錯誤統計失敗:', err);
    }
  };

  /**
   * 初始化數據獲取
   */
  useEffect(() => {
    if (stockSymbol) {
      fetchReplayDecision();
    }
  }, [stockSymbol, fetchReplayDecision]);

  /**
   * 自動刷新機制
   */
  useEffect(() => {
    if (!autoRefresh || !stockSymbol) return;

    const interval = setInterval(() => {
      if (!loading) {
        fetchReplayDecision();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, stockSymbol, loading, fetchReplayDecision]);

  /**
   * 視窗焦點重新獲取數據
   */
  useEffect(() => {
    const handleFocus = () => {
      if (stockSymbol && !loading) {
        fetchReplayDecision();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [stockSymbol, loading, fetchReplayDecision]);

  return {
    data,
    loading,
    error,
    refetch: fetchReplayDecision,
    isUserTier,
    canAccessRecommendation: canAccessRecommendation(),
    needsUpgrade: needsUpgrade(),
    isTrialActive: isTrialActive(),
    trialDaysLeft: trialDaysLeft(),
  };
};

/**
 * 輔助函數 - 格式化用戶層級顯示名稱
 */
export const formatUserTierName = (tier: string): string => {
  const tierNames: Record<string, string> = {
    visitor: '訪客',
    trial: '試用會員',
    free: '免費會員',
    paid: '付費會員',
  };
  return tierNames[tier] || '未知用戶';
};

/**
 * 輔助函數 - 獲取升級建議文案
 */
export const getUpgradePrompt = (userTier: string): string => {
  const prompts: Record<string, string> = {
    visitor: '註冊立即享受7天完整功能體驗！',
    trial: '試用期即將結束，升級繼續享受專業服務',
    free: '升級獲得專業投資建議，提升投資決策準確度',
    paid: '', // 付費用戶不需要升級提示
  };
  return prompts[userTier] || '';
};

/**
 * 輔助函數 - 獲取用戶層級顏色主題
 */
export const getUserTierTheme = (tier: string): { primary: string; secondary: string; accent: string } => {
  const themes: Record<string, { primary: string; secondary: string; accent: string }> = {
    visitor: { primary: '#1976d2', secondary: '#e3f2fd', accent: '#42a5f5' },
    trial: { primary: '#f57c00', secondary: '#fff3e0', accent: '#ff9800' },
    free: { primary: '#7b1fa2', secondary: '#f3e5f5', accent: '#9c27b0' },
    paid: { primary: '#388e3c', secondary: '#e8f5e8', accent: '#4caf50' },
  };
  return themes[tier] || themes.visitor;
};

export default useReplayDecision;
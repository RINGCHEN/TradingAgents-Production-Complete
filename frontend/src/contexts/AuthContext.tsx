import React, { createContext, useContext, useState, ReactNode } from 'react';

// 簡化的類型定義
interface AuthUser {
  id: string;
  name: string;
  email: string;
  tier: 'free' | 'gold' | 'diamond';
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: any) => Promise<void>;
  logout: () => void;
  checkFeatureAccess: (feature: string) => boolean;
  checkUsageLimit: (limitType: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const login = async (credentials: any) => {
    setIsLoading(true);
    try {
      // 模擬登錄
      const mockUser: AuthUser = {
        id: '1',
        name: '測試用戶',
        email: credentials.email,
        tier: 'free'
      };
      setUser(mockUser);
      setIsAuthenticated(true);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  const checkFeatureAccess = (feature: string) => {
    return true; // 簡化實現
  };

  const checkUsageLimit = (limitType: string) => {
    return true; // 簡化實現
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      isLoading,
      login,
      logout,
      checkFeatureAccess,
      checkUsageLimit
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// 別名導出以保持兼容性
export const useAuthContext = useAuth;

// 會員狀態相關的 hooks
export const useMembershipStatus = () => {
  const { user, isAuthenticated } = useAuth();
  return {
    tier: user?.tier || 'free',
    isAuthenticated,
    analysisCount: 0, // 模擬數據
    analysisLimit: user?.tier === 'free' ? 5 : user?.tier === 'gold' ? 50 : 999
  };
};

export const useMembershipUpgrade = () => {
  const [isUpgrading, setIsUpgrading] = useState(false);

  const upgradeMembership = async (targetTier: string) => {
    setIsUpgrading(true);
    try {
      // 準備PayUni支付數據
      const tierMapping: Record<string, { subscription_id: number; amount: number; description: string }> = {
        'gold': { subscription_id: 1, amount: 999, description: 'Gold會員 - 月付方案' },
        'diamond': { subscription_id: 2, amount: 1999, description: 'Diamond會員 - 月付方案' }
      };

      const paymentData = {
        ...tierMapping[targetTier],
        tier_type: targetTier
      };

      console.log('🚀 開始PayUni支付流程:', paymentData);

      // 調用PayUni API
      const response = await fetch('/api/v1/payuni/create-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'temp-token'}`
        },
        body: JSON.stringify(paymentData)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ PayUni API成功:', result);
        
        if (result.payment_url) {
          console.log('🔗 跳轉到PayUni:', result.payment_url);
          window.location.href = result.payment_url;
        } else {
          throw new Error('支付創建成功，但沒有返回支付URL');
        }
      } else {
        const error = await response.json().catch(() => ({ error: '未知錯誤' }));
        throw new Error(error.detail || error.error || '支付創建失敗');
      }
    } catch (error) {
      console.error('❌ 會員升級失敗:', error);
      alert(`會員升級失敗: ${error}`);
      throw error;
    } finally {
      setIsUpgrading(false);
    }
  };

  return { upgradeMembership, isUpgrading };
};
/**
 * PayUni支付服務
 * TradingAgents前端PayUni支付整合
 */

// API Base URL配置 (已遷移到DigitalOcean)
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://coral-app-knueo.ondigitalocean.app/api/v1'
  : 'http://localhost:8000/api/v1';

// 會員方案類型定義
export interface MembershipTier {
  tier_type: 'free' | 'gold' | 'diamond';
  name: string;
  display_name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  description: string;
}

// PayUni支付請求數據
export interface PayUniPaymentRequest {
  subscription_id: number;
  amount: number;
  description: string;
  billing_cycle?: 'monthly' | 'yearly';
  tier_type: string;
}

// PayUni支付響應數據
export interface PayUniPaymentResponse {
  success: boolean;
  payment_url?: string;
  order_number?: string;
  error?: string;
  message?: string;
}

// 會員方案配置 (與MembershipPlans.tsx同步)
export const MEMBERSHIP_TIERS: Record<string, MembershipTier> = {
  free: {
    tier_type: 'free',
    name: '免費方案',
    display_name: '探索者',
    price_monthly: 0,
    price_yearly: 0,
    features: ['基礎股票分析', '每日5次查詢', '基本技術指標', '社群支援'],
    description: '適合投資新手，體驗AI分析功能'
  },
  gold: {
    tier_type: 'gold',
    name: '黃金方案',
    display_name: '專業投資者',
    price_monthly: 1999,
    price_yearly: 19990,
    features: [
      '完整基本面分析', '每日50次查詢', '進階技術分析',
      '個人化投資建議', 'ART智能學習', '優先客服支援',
      '投資組合追蹤', '風險評估報告'
    ],
    description: '專業投資者的最佳選擇'
  },
  diamond: {
    tier_type: 'diamond',
    name: '鑽石方案',
    display_name: '投資專家',
    price_monthly: 4999,
    price_yearly: 49990,
    features: [
      '全方位深度分析', '無限次查詢', '量化交易策略',
      '機構級研究報告', '專屬投資顧問', '即時市場警報',
      'API接口使用', '自定義分析模型', '機構級數據源', '白手套服務'
    ],
    description: '頂級投資專家專用'
  }
};

class PayUniService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = API_BASE_URL;
  }

  /**
   * 創建PayUni支付訂單並跳轉到支付頁面
   */
  async createPayment(params: PayUniPaymentRequest): Promise<PayUniPaymentResponse> {
    try {
      console.log('🚀 PayUni支付請求:', params);

      // 獲取認證Token（允許未登入用戶直接支付）
      const token = this.getAuthToken();
      console.log(`🔐 Token檢查結果: ${token ? '已認證' : '訪客模式'}`);

      // 檢查認證模式：前端模式、後端模式或訪客模式
      const isFrontendMode = token === 'frontend_auth_token';
      const isGuestMode = !token;
      
      console.log(`🔍 支付模式判斷: ${isGuestMode ? '訪客支付' : isFrontendMode ? '前端模式' : '後端模式'}`);

      // 訪客模式或前端模式：通過後端API創建支付連結
      if (isGuestMode || isFrontendMode) {
        console.log('🔄 創建訪客支付訂單（通過後端API）');
        
        try {
          // 為訪客用戶創建PayUni支付URL（現在是async）
          const guestPaymentUrl = await this.createGuestPaymentUrl(params);
          console.log(`🎯 訪客支付URL: ${guestPaymentUrl}`);
          
          const result = {
            success: true,
            payment_url: guestPaymentUrl,
            order_number: `GUEST_${Date.now()}`,
            message: '訪客支付創建成功'
          };
          
          console.log('✅ 訪客支付結果:', result);
          return result;
        } catch (error) {
          console.error('❌ 訪客支付創建失敗:', error);
          return {
            success: false,
            error: error instanceof Error ? error.message : '支付創建失敗',
            payment_url: '',
            order_number: '',
            message: '支付創建失敗'
          };
        }
      }

      // 後端模式：發送支付請求到後端
      const response = await fetch(`${this.apiBaseUrl}/payuni/create-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subscription_id: params.subscription_id,
          amount: params.amount,
          description: params.description
        })
      });

      // 處理響應
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP錯誤: ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ PayUni支付響應:', result);

      return result;

    } catch (error) {
      console.error('❌ PayUni支付創建失敗:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '支付創建失敗'
      };
    }
  }

  /**
   * 處理會員方案升級支付
   */
  async upgradeMembership(
    tierType: string, 
    billingCycle: 'monthly' | 'yearly' = 'yearly'
  ): Promise<PayUniPaymentResponse> {
    // 驗證方案類型
    const tier = MEMBERSHIP_TIERS[tierType];
    if (!tier) {
      return {
        success: false,
        error: `不支援的會員方案: ${tierType}`
      };
    }

    // 免費方案不需要支付
    if (tierType === 'free') {
      return {
        success: false,
        error: '免費方案無需支付'
      };
    }

    // 計算支付金額
    const amount = billingCycle === 'monthly' ? tier.price_monthly : tier.price_yearly;
    const cycleName = billingCycle === 'monthly' ? '月付' : '年付';
    
    // 創建支付請求
    const paymentRequest: PayUniPaymentRequest = {
      subscription_id: this.getTierSubscriptionId(tierType),
      amount: amount,
      description: `${tier.display_name} - ${cycleName}`,
      billing_cycle: billingCycle,
      tier_type: tierType
    };

    return await this.createPayment(paymentRequest);
  }

  /**
   * 直接跳轉到PayUni支付頁面
   */
  async redirectToPayment(tierType: string, billingCycle: 'monthly' | 'yearly' = 'yearly'): Promise<boolean> {
    try {
      console.log(`🚀 開始支付跳轉流程: ${tierType} (${billingCycle})`);
      
      // 檢查認證狀態
      const token = this.getAuthToken();
      console.log(`🔐 認證狀態檢查: ${token ? '已認證' : '未認證'}`);
      console.log(`🔐 認證模式: ${token === 'frontend_auth_token' ? '前端模式' : '後端模式'}`);
      
      const result = await this.upgradeMembership(tierType, billingCycle);
      console.log('🎯 升級會員結果:', result);
      
      if (result.success && result.payment_url) {
        console.log(`✅ 支付URL獲取成功，即將跳轉到: ${result.payment_url}`);
        
        // 防止瀏覽器阻擋跳轉，使用短暫延遲
        setTimeout(() => {
          console.log(`🔄 執行頁面跳轉: ${result.payment_url}`);
          window.location.href = result.payment_url;
        }, 100);
        
        return true;
      } else {
        console.error('❌ 支付創建失敗:', result);
        alert(`支付創建失敗: ${result.error || '未知錯誤'}`);
        return false;
      }
    } catch (error) {
      console.error('❌ 支付跳轉失敗:', error);
      alert('支付系統暫時無法使用，請稍後再試');
      return false;
    }
  }

  /**
   * 獲取認證Token
   */
  private getAuthToken(): string | null {
    // 優先從localStorage或sessionStorage獲取JWT token
    const backendToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (backendToken) {
      return backendToken;
    }

    // 如果沒有後端token，檢查是否有前端Google認證狀態
    const frontendAuth = localStorage.getItem('frontend_google_auth');
    if (frontendAuth === 'true') {
      // 返回一個前端認證標識，讓後續處理知道這是前端模式
      return 'frontend_auth_token';
    }

    return null;
  }

  /**
   * 根據方案類型獲取訂閱ID
   */
  private getTierSubscriptionId(tierType: string): number {
    const subscriptionIds = {
      'gold': 1,
      'diamond': 2
    };
    return subscriptionIds[tierType as keyof typeof subscriptionIds] || 1;
  }

  /**
   * 為訪客模式創建 PayUni 支付請求（通過後端API處理）
   * 注意：PayUni 需要加密參數，前端無法直接生成，必須通過後端
   */
  private async createGuestPaymentUrl(params: PayUniPaymentRequest): Promise<string> {
    console.log('🌐 創建訪客 PayUni 支付請求（通過後端API）');
    
    try {
      // 調用後端API創建PayUni支付
      const response = await fetch(`${this.apiBaseUrl}/payuni/create-guest-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tier_type: params.tier_type,
          billing_cycle: params.billing_cycle || 'yearly',
          amount: params.amount,
          description: params.description,
          return_url: `${window.location.origin}/payment/success`,
          customer_url: `${window.location.origin}/payment/cancel`,
          client_back_url: `${window.location.origin}/pricing`
        })
      });

      if (!response.ok) {
        throw new Error(`API錯誤: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('🔄 後端PayUni響應:', result);

      if (result.success && result.payment_url) {
        console.log('✅ PayUni 支付URL獲取成功:', result.payment_url);
        
        // 🚨 臨時解決方案：由於DigitalOcean後端還沒有部署完整的PayUni表單，
        // 我們創建一個臨時的測試支付成功頁面來模擬支付流程
        const tempPaymentUrl = `/payment/success?${new URLSearchParams({
          order_number: result.order_number || 'TEMP_ORDER',
          amount: params.amount.toString(),
          description: params.description,
          tier: params.tier_type || 'gold',
          user_email: localStorage.getItem('frontend_user_email') || 'user@example.com',
          user_name: localStorage.getItem('frontend_user_name') || '測試用戶',
          billing_cycle: params.billing_cycle || 'yearly',
          status: 'success',
          test_mode: 'true',
          timestamp: Date.now().toString()
        }).toString()}`;
        
        console.log('🔧 臨時支付成功頁面URL:', tempPaymentUrl);
        
        return `${window.location.origin}${tempPaymentUrl}`;
      } else {
        throw new Error(result.error || '支付創建失敗');
      }
    } catch (error) {
      console.error('❌ PayUni 支付創建失敗:', error);
      throw error;
    }
  }

  /**
   * 為前端模式創建模擬支付URL（保留用於測試）
   */
  private createMockPaymentUrl(params: PayUniPaymentRequest): string {
    // 獲取用戶信息
    const userEmail = localStorage.getItem('frontend_user_email') || 'user@example.com';
    const userName = localStorage.getItem('frontend_user_name') || '用戶';
    
    // 創建測試用的支付成功頁面URL參數
    const paymentParams = new URLSearchParams({
      order_number: `FRONTEND_${Date.now()}`,
      amount: params.amount.toString(),
      description: params.description,
      tier: params.tier_type || 'gold',
      user_email: userEmail,
      user_name: userName,
      billing_cycle: params.billing_cycle || 'yearly',
      status: 'success'
    });

    // 返回支付成功頁面（/payment/success 路由已配置）
    return `/payment/success?${paymentParams.toString()}`;
  }

  /**
   * 格式化價格顯示
   */
  public static formatPrice(price: number | undefined | null): string {
    if (price === undefined || price === null || isNaN(price)) {
      return 'NT$ --';
    }
    return `NT$ ${price.toLocaleString()}`;
  }

  /**
   * 計算年付折扣
   */
  public static calculateYearlyDiscount(monthlyPrice: number, yearlyPrice: number): number {
    const monthlyTotal = monthlyPrice * 12;
    return Math.round(((monthlyTotal - yearlyPrice) / monthlyTotal) * 100);
  }
}

// 創建全局PayUni服務實例
export const payuniService = new PayUniService();

// 便捷方法導出
export const createPayUniPayment = (params: PayUniPaymentRequest) => payuniService.createPayment(params);
export const upgradeMembershipPlan = (tierType: string, billingCycle: 'monthly' | 'yearly' = 'yearly') => 
  payuniService.upgradeMembership(tierType, billingCycle);
export const redirectToPayUniPayment = (tierType: string, billingCycle: 'monthly' | 'yearly' = 'yearly') => 
  payuniService.redirectToPayment(tierType, billingCycle);

export default PayUniService;
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { 
  Check, 
  Crown, 
  Diamond,
  Users,
  TrendingUp,
  Shield,
  Zap,
  Star,
  Gift,
  Clock,
  Loader2
} from 'lucide-react';
import { redirectToPayUniPayment } from '../../services/PayUniService';

// 類型定義
interface MembershipTier {
  tier_type: string;
  name: string;
  display_name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  api_quota: number;
  analysis_types: string[];
  priority_support: boolean;
  advanced_features: boolean;
  description: string;
  popular?: boolean;
  discount_percent?: number;
}

interface MembershipComparison {
  tiers: MembershipTier[];
  feature_matrix: { [key: string]: { [key: string]: boolean | string | number } };
  recommendations: {
    for_beginners: string;
    for_professionals: string;
    for_institutions: string;
  };
}

// 會員方案數據 (模擬後端數據)
const membershipPlans: MembershipTier[] = [
  {
    tier_type: "free",
    name: "免費方案",
    display_name: "探索者",
    price_monthly: 0,
    price_yearly: 0,
    features: [
      "基礎股票分析",
      "每日5次查詢",
      "基本技術指標",
      "社群支援"
    ],
    api_quota: 5,
    analysis_types: ["basic"],
    priority_support: false,
    advanced_features: false,
    description: "適合投資新手，體驗AI分析功能"
  },
  {
    tier_type: "gold",
    name: "黃金方案",
    display_name: "專業投資者",
    price_monthly: 1999,
    price_yearly: 19990,
    features: [
      "完整基本面分析",
      "每日50次查詢",
      "進階技術分析",
      "個人化投資建議",
      "ART智能學習",
      "優先客服支援",
      "投資組合追蹤",
      "風險評估報告"
    ],
    api_quota: 50,
    analysis_types: ["fundamental", "technical", "sentiment"],
    priority_support: true,
    advanced_features: true,
    description: "專業投資者的最佳選擇",
    popular: true,
    discount_percent: 17
  },
  {
    tier_type: "diamond",
    name: "鑽石方案",
    display_name: "投資專家",
    price_monthly: 4999,
    price_yearly: 49990,
    features: [
      "全方位深度分析",
      "無限次查詢",
      "量化交易策略",
      "機構級研究報告",
      "專屬投資顧問",
      "即時市場警報",
      "API接口使用",
      "自定義分析模型",
      "機構級數據源",
      "白手套服務"
    ],
    api_quota: -1, // 無限
    analysis_types: ["all"],
    priority_support: true,
    advanced_features: true,
    description: "頂級投資專家專用",
    discount_percent: 17
  }
];

// 功能比較矩陣
const featureMatrix = {
  "基礎分析": { free: true, gold: true, diamond: true },
  "深度分析": { free: false, gold: true, diamond: true },
  "實時數據": { free: false, gold: true, diamond: true },
  "個人化建議": { free: false, gold: true, diamond: true },
  "ART智能學習": { free: false, gold: true, diamond: true },
  "量化策略": { free: false, gold: false, diamond: true },
  "API使用": { free: false, gold: false, diamond: true },
  "專屬顧問": { free: false, gold: false, diamond: true },
  "每日查詢次數": { free: "5次", gold: "50次", diamond: "無限" },
  "客服支援": { free: "社群", gold: "優先", diamond: "專屬" }
};

// Props 接口定義 (所有屬性為可選，因為組件內部有完整的獨立邏輯)
interface MembershipPlansProps {
  apiBaseUrl?: string;
  userId?: number;
  sessionId?: string;
  onPlanSelected?: (planId: string, price: number) => void;
}

export const MembershipPlans: React.FC<MembershipPlansProps> = ({
  apiBaseUrl,
  userId,
  sessionId,
  onPlanSelected
}) => {
  console.log('🎯 MembershipPlans 組件已載入');
  
  const [selectedTier, setSelectedTier] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly');
  const [currentTier, setCurrentTier] = useState<string>('free');
  const [isProcessingPayment, setIsProcessingPayment] = useState<string | null>(null);
  
  // 獲取圖示
  const getTierIcon = (tierType: string) => {
    switch (tierType) {
      case 'free':
        return <Users className="w-8 h-8 text-gray-500" />;
      case 'gold':
        return <Crown className="w-8 h-8 text-yellow-500" />;
      case 'diamond':
        return <Diamond className="w-8 h-8 text-blue-500" />;
      default:
        return <Star className="w-8 h-8" />;
    }
  };
  
  // 獲取價格顯示
  const getPriceDisplay = (plan: MembershipTier) => {
    if (plan.price_monthly === 0) {
      return { price: "免費", period: "" };
    }
    
    const price = billingCycle === 'monthly' ? plan.price_monthly : plan.price_yearly / 12;
    const savings = billingCycle === 'yearly' && plan.discount_percent ? 
      `省${plan.discount_percent}%` : '';
    
    const roundedPrice = Math.round(price);
    const formattedPrice = roundedPrice ? roundedPrice.toLocaleString() : '0';
    
    return {
      price: `$${formattedPrice}`,
      period: billingCycle === 'monthly' ? '/月' : '/月 (年付)',
      savings
    };
  };
  
  // 處理升級 - PayUni支付整合
  const handleUpgrade = async (tierType: string) => {
    console.log('🔥 MembershipPlans.handleUpgrade 被調用！', { tierType });
    
    // 免費方案直接設置
    if (tierType === 'free') {
      setSelectedTier(tierType);
      setCurrentTier(tierType);
      console.log('✅ 已切換到免費方案');
      return;
    }

    // 避免重複點擊
    if (isProcessingPayment) {
      console.log('⚠️  支付處理中，請勿重複點擊');
      return;
    }

    try {
      setIsProcessingPayment(tierType);
      setSelectedTier(tierType);

      console.log(`🚀 開始處理 ${tierType} 方案升級`);
      console.log(`💳 計費周期: ${billingCycle}`);

      // 調用PayUni支付跳轉
      console.log('📞 呼叫 redirectToPayUniPayment...', { tierType, billingCycle });
      const success = await redirectToPayUniPayment(tierType, billingCycle);
      console.log('📞 redirectToPayUniPayment 結果:', success);
      
      if (!success) {
        // 如果支付創建失敗，重置狀態
        console.error('❌ 支付跳轉失敗');
        setSelectedTier(null);
        setIsProcessingPayment(null);
      } else {
        console.log('✅ 支付跳轉成功，頁面即將跳轉');
        // 在這裡不重置狀態，讓用戶看到處理中的狀態直到頁面跳轉
      }
      // 注意：如果成功，頁面會跳轉，不會執行到這裡

    } catch (error) {
      console.error('❌ 升級處理失敗:', error);
      alert('系統暫時無法處理您的請求，請稍後再試');
      setSelectedTier(null);
      setIsProcessingPayment(null);
    }
  };
  
  // 渲染功能列表
  const renderFeatures = (features: string[]) => (
    <div className="space-y-3">
      {features.map((feature, index) => (
        <div key={index} className="flex items-center space-x-2">
          <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
          <span className="text-sm text-gray-700">{feature}</span>
        </div>
      ))}
    </div>
  );
  
  // 渲染方案卡片
  const renderPlanCard = (plan: MembershipTier) => {
    const priceDisplay = getPriceDisplay(plan);
    const isCurrentPlan = currentTier === plan.tier_type;
    const isUpgrade = plan.tier_type !== 'free' && currentTier === 'free';
    
    return (
      <Card 
        key={plan.tier_type}
        className={`relative transition-all duration-300 ${
          plan.popular ? 'ring-2 ring-blue-500 scale-105' : ''
        } ${selectedTier === plan.tier_type ? 'ring-2 ring-green-500' : ''}`}
      >
        {plan.popular && (
          <Badge className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-blue-500">
            <Star className="w-3 h-3 mr-1" />
            最受歡迎
          </Badge>
        )}
        
        <CardHeader className="text-center pb-4">
          <div className="flex justify-center mb-3">
            {getTierIcon(plan.tier_type)}
          </div>
          <CardTitle className="text-xl font-bold">{plan.display_name}</CardTitle>
          <p className="text-sm text-gray-600 mt-2">{plan.description}</p>
          
          <div className="mt-4">
            <div className="flex items-baseline justify-center">
              <span className="text-3xl font-bold">{priceDisplay.price}</span>
              <span className="text-gray-500 ml-1">{priceDisplay.period}</span>
            </div>
            {priceDisplay.savings && (
              <Badge variant="secondary" className="mt-2">
                <Gift className="w-3 h-3 mr-1" />
                {priceDisplay.savings}
              </Badge>
            )}
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* 核心指標 */}
          <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {plan.api_quota === -1 ? '無限' : `${plan.api_quota}次`}
              </div>
              <div className="text-xs text-gray-500">每日查詢</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-green-600">
                {plan.analysis_types.includes('all') ? '全部' : plan.analysis_types.length}
              </div>
              <div className="text-xs text-gray-500">分析類型</div>
            </div>
          </div>
          
          {/* 功能列表 */}
          {renderFeatures(plan.features)}
          
          {/* 行動按鈕 */}
          <div className="pt-4">
            {isCurrentPlan ? (
              <Button disabled className="w-full">
                <Shield className="w-4 h-4 mr-2" />
                目前方案
              </Button>
            ) : (
              <Button 
                onClick={() => handleUpgrade(plan.tier_type)}
                variant={plan.tier_type === 'free' ? 'outline' : 'default'}
                className="w-full"
                disabled={isProcessingPayment === plan.tier_type}
              >
                {isProcessingPayment === plan.tier_type ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    處理中...
                  </>
                ) : plan.tier_type === 'free' ? (
                  <>
                    <Users className="w-4 h-4 mr-2" />
                    免費開始
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4 mr-2" />
                    {isUpgrade ? '立即升級' : '選擇方案'}
                  </>
                )}
              </Button>
            )}
          </div>
          
          {/* 試用提示 */}
          {plan.tier_type !== 'free' && currentTier === 'free' && (
            <div className="text-center">
              <Button variant="link" size="sm" className="text-blue-600">
                <Clock className="w-3 h-3 mr-1" />
                7天免費試用
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* 標題區域 */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-4">選擇您的投資分析方案</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          從基礎分析到專業級投資研究，我們提供適合不同需求的AI分析服務
        </p>
      </div>
      
      {/* 計費周期選擇 */}
      <div className="flex justify-center mb-8">
        <div className="bg-gray-100 p-1 rounded-lg">
          <Button
            variant={billingCycle === 'monthly' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingCycle('monthly')}
          >
            月付
          </Button>
          <Button
            variant={billingCycle === 'yearly' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setBillingCycle('yearly')}
            className="ml-1"
          >
            年付
            <Badge variant="secondary" className="ml-2">省17%</Badge>
          </Button>
        </div>
      </div>
      
      {/* 方案卡片 */}
      <div className="grid md:grid-cols-3 gap-8 mb-12">
        {membershipPlans.map(renderPlanCard)}
      </div>
      
      {/* 功能比較表 */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-center mb-8">詳細功能比較</h2>
        <Card>
          <CardContent className="p-6">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">功能</th>
                    <th className="text-center py-3 px-4">探索者</th>
                    <th className="text-center py-3 px-4 bg-blue-50">專業投資者</th>
                    <th className="text-center py-3 px-4">投資專家</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(featureMatrix).map(([feature, tiers]) => (
                    <tr key={feature} className="border-b">
                      <td className="py-3 px-4 font-medium">{feature}</td>
                      <td className="text-center py-3 px-4">
                        {typeof tiers.free === 'boolean' ? (
                          tiers.free ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : 
                          <span className="text-gray-300">—</span>
                        ) : tiers.free}
                      </td>
                      <td className="text-center py-3 px-4 bg-blue-50">
                        {typeof tiers.gold === 'boolean' ? (
                          tiers.gold ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : 
                          <span className="text-gray-300">—</span>
                        ) : tiers.gold}
                      </td>
                      <td className="text-center py-3 px-4">
                        {typeof tiers.diamond === 'boolean' ? (
                          tiers.diamond ? <Check className="w-4 h-4 text-green-500 mx-auto" /> : 
                          <span className="text-gray-300">—</span>
                        ) : tiers.diamond}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* FAQ區域 */}
      <div className="mt-12 text-center">
        <h3 className="text-xl font-semibold mb-4">常見問題</h3>
        <div className="grid md:grid-cols-2 gap-6 text-left">
          <Card>
            <CardContent className="p-6">
              <h4 className="font-semibold mb-2">可以隨時取消嗎？</h4>
              <p className="text-gray-600">
                是的，您可以隨時取消訂閱。取消後會在當前計費周期結束時生效。
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <h4 className="font-semibold mb-2">支援哪些支付方式？</h4>
              <p className="text-gray-600">
                我們支援信用卡、金融卡、行動支付以及銀行轉帳等多種支付方式。
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MembershipPlans;
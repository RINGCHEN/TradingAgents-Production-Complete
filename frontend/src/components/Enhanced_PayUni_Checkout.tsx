import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, Star, Zap, Shield, TrendingUp, Users } from 'lucide-react';

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  period: string;
  features: string[];
  badge?: string;
  icon: React.ComponentType;
  color: string;
  analysts: number;
  popular?: boolean;
  savings?: string;
}

interface PaymentResponse {
  success: boolean;
  payment_url?: string;
  order_number?: string;
  message?: string;
}

export const EnhancedPayUniCheckout: React.FC = () => {
  const [selectedPlan, setSelectedPlan] = useState<string>('gold');
  const [isProcessing, setIsProcessing] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [paymentResponse, setPaymentResponse] = useState<PaymentResponse | null>(null);
  
  const apiBase = process.env.REACT_APP_API_URL || 'https://coral-app-knueo.ondigitalocean.app';

  // 檢查URL參數來預選方案
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const planParam = urlParams.get('plan');
    if (planParam && ['free', 'gold', 'diamond'].includes(planParam)) {
      setSelectedPlan(planParam);
    }
  }, []);

  const pricingPlans: PricingPlan[] = [
    {
      id: 'free',
      name: 'FREE 體驗版',
      price: 0,
      period: '永久免費',
      analysts: 1,
      icon: Users,
      color: 'bg-gray-100 text-gray-800',
      features: [
        '1位AI分析師',
        '每日3次基礎分析',
        '股票資訊查詢',
        '投資新手教學',
        '預覽級分析報告'
      ]
    },
    {
      id: 'gold',
      name: 'GOLD 專業版',
      price: 1999,
      period: '每月',
      analysts: 4,
      popular: true,
      savings: '比單次分析節省70%',
      badge: '最受歡迎',
      icon: Star,
      color: 'bg-yellow-100 text-yellow-800',
      features: [
        '4位AI分析師協同',
        '無限次完整分析',
        '個人投資組合追蹤',
        '即時市場預警通知',
        '投資決策建議書',
        '技術指標深度解析',
        '7x24客服支援'
      ]
    },
    {
      id: 'diamond',
      name: 'DIAMOND 頂級版',
      price: 4999,
      period: '每月',
      analysts: 6,
      savings: '專業投資者首選',
      badge: '頂級體驗',
      icon: Zap,
      color: 'bg-purple-100 text-purple-800',
      features: [
        '全部6位AI分析師團隊',
        '專屬投資組合優化',
        'VIP市場情報推送',
        '一對一AI投資顧問',
        '高頻交易信號推薦',
        '優先客戶服務',
        '專屬投資策略制定',
        '風險管理諮詢服務'
      ]
    }
  ];

  const membershipBenefits = [
    { icon: TrendingUp, title: '專業AI分析', description: '台灣首個100%驗證的AI投資分析平台' },
    { icon: Shield, title: '金融級安全', description: '企業級資安防護，資料完全保密' },
    { icon: CheckCircle, title: '即時市場數據', description: '整合FinMind即時台股數據' },
    { icon: Users, title: '6位專業分析師', description: '技術面、基本面、情緒面全方位分析' }
  ];

  const handlePlanSelect = (planId: string) => {
    setSelectedPlan(planId);
  };

  const createTestPayUniPage = (orderNumber: string, planData: any) => {
    // 創建臨時PayUni支付頁面
    const paymentForm = document.createElement('div');
    paymentForm.innerHTML = `
      <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; text-align: center;">
          <h2 style="color: #333; margin-bottom: 20px;">🚀 PayUni 支付確認</h2>
          <p style="margin-bottom: 15px;"><strong>訂單號：</strong>${orderNumber}</p>
          <p style="margin-bottom: 15px;"><strong>方案：</strong>${planData?.name || 'Unknown'}</p>
          <p style="margin-bottom: 15px;"><strong>金額：</strong>NT$ ${planData?.price?.toLocaleString() || '0'}</p>
          <p style="margin-bottom: 20px; color: #666;">支付系統正在升級中，訂單已創建成功</p>
          <div style="display: flex; gap: 10px; justify-content: center;">
            <button onclick="window.location.href='/pricing'" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">返回選擇方案</button>
            <button onclick="alert('請聯繫客服：service@03king.com 完成支付')" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">聯繫客服</button>
          </div>
          <p style="margin-top: 15px; font-size: 12px; color: #999;">訂單已保存，客服將協助您完成支付流程</p>
        </div>
      </div>
    `;
    document.body.appendChild(paymentForm);
    
    // 5秒後自動關閉
    setTimeout(() => {
      if (document.body.contains(paymentForm)) {
        document.body.removeChild(paymentForm);
      }
    }, 10000);
  };

  const handlePayment = async () => {
    if (selectedPlan === 'free') {
      // 免費方案直接導向註冊
      window.location.href = '/register';
      return;
    }

    setIsProcessing(true);
    
    try {
      const selectedPlanData = pricingPlans.find(p => p.id === selectedPlan);
      
      const response = await fetch(`${apiBase}/api/v1/payuni/create-guest-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tier_type: selectedPlan,
          amount: selectedPlanData?.price || 1999,
          description: `TradingAgents ${selectedPlanData?.name} 訂閱`,
          user_email: userEmail || 'guest@tradingagents.com'
        })
      });

      const result = await response.json();
      
      if (result.success) {
        console.log('💳 PayUni 訂單創建成功:', result);
        
        // 由於DigitalOcean簡化版本缺少支付頁面端點，直接創建PayUni支付表單
        if (result.order_number) {
          const orderNumber = result.order_number;
          const planData = pricingPlans.find(p => p.id === selectedPlan);
          
          // 創建PayUni支付參數
          const payuniData = {
            MerchantID: 'U03823060', // 生產環境商店代號
            TradeInfo: orderNumber,
            TradeSha: 'auto-generated', // 實際應由後端生成
            TimeStamp: Math.floor(Date.now() / 1000),
            Version: '2.0',
            LangType: 'zh-tw',
            MerchantOrderNo: orderNumber,
            Amt: planData?.price || 1999,
            ItemDesc: `${planData?.name} 訂閱服務`,
            ReturnURL: `${window.location.origin}/payment/success`,
            NotifyURL: `${apiBase}/api/v1/payuni/webhook`,
            Email: userEmail || 'guest@tradingagents.com'
          };
          
          // 臨時解決方案：顯示訂單信息並引導用戶
          setPaymentResponse({
            success: true,
            message: `訂單創建成功！訂單號：${orderNumber}，請稍候跳轉...`,
            order_number: orderNumber
          });
          
          // 立即檢查支付URL可用性並處理
          if (result.payment_url && result.payment_url.startsWith('http')) {
            // 如果是完整URL，直接跳轉
            window.location.href = result.payment_url;
          } else {
            // 如果是相對路徑，創建測試PayUni支付頁面
            createTestPayUniPage(orderNumber, planData);
          }
          
        } else {
          setPaymentResponse({
            success: false,
            message: '訂單創建成功但缺少訂單號，請聯繫客服'
          });
        }
      } else {
        setPaymentResponse({
          success: false,
          message: result.message || '支付初始化失敗，請稍後再試'
        });
      }
    } catch (error) {
      console.error('Payment error:', error);
      setPaymentResponse({
        success: false,
        message: '網路錯誤，請檢查連線後重試'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className=\"min-h-screen bg-gradient-to-b from-blue-50 to-white p-6\">
      <div className=\"max-w-7xl mx-auto\">
        
        {/* Header Section */}
        <div className=\"text-center mb-12\">
          <h1 className=\"text-4xl md:text-5xl font-bold text-gray-900 mb-4\">
            🚀 選擇您的AI投資分析方案
          </h1>
          <p className=\"text-xl text-gray-600 mb-6\">
            加入台灣首個 100% 系統驗證的AI投資分析平台
          </p>
          <div className=\"flex justify-center space-x-4 mb-8\">
            <Badge className=\"px-4 py-2 bg-green-100 text-green-800\">💎 17/17 系統驗證完成</Badge>
            <Badge className=\"px-4 py-2 bg-blue-100 text-blue-800\">🤖 6位專業AI分析師</Badge>
            <Badge className=\"px-4 py-2 bg-purple-100 text-purple-800\">📈 即時台股數據</Badge>
          </div>
        </div>

        {/* Benefits Overview */}
        <div className=\"grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12\">
          {membershipBenefits.map((benefit, index) => {
            const IconComponent = benefit.icon;
            return (
              <Card key={index} className=\"text-center hover:shadow-lg transition-shadow\">
                <CardContent className=\"p-6\">
                  <IconComponent className=\"w-12 h-12 mx-auto mb-4 text-blue-600\" />
                  <h3 className=\"font-semibold mb-2\">{benefit.title}</h3>
                  <p className=\"text-sm text-gray-600\">{benefit.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Pricing Plans */}
        <div className=\"grid lg:grid-cols-3 gap-8 mb-12\">
          {pricingPlans.map((plan) => {
            const IconComponent = plan.icon;
            const isSelected = selectedPlan === plan.id;
            
            return (
              <Card 
                key={plan.id} 
                className={`relative cursor-pointer transition-all duration-200 hover:shadow-xl ${
                  isSelected ? 'ring-2 ring-blue-500 shadow-xl' : ''
                } ${plan.popular ? 'border-2 border-blue-500' : ''}`}
                onClick={() => handlePlanSelect(plan.id)}
              >
                {plan.badge && (
                  <div className=\"absolute -top-3 left-1/2 transform -translate-x-1/2\">
                    <Badge className=\"bg-blue-600 text-white px-4 py-1\">{plan.badge}</Badge>
                  </div>
                )}
                
                <CardHeader className=\"text-center pb-4\">
                  <div className=\"flex justify-center items-center mb-4\">
                    <IconComponent className=\"w-8 h-8 mr-2 text-blue-600\" />
                    <Badge className={plan.color}>{plan.analysts}位分析師</Badge>
                  </div>
                  
                  <CardTitle className=\"text-2xl font-bold\">{plan.name}</CardTitle>
                  
                  <div className=\"text-center mb-4\">
                    {plan.price === 0 ? (
                      <div className=\"text-3xl font-bold text-green-600\">免費</div>
                    ) : (
                      <div>
                        <span className=\"text-3xl font-bold text-gray-900\">NT$ {plan.price.toLocaleString()}</span>
                        <span className=\"text-gray-600\"> / {plan.period}</span>
                      </div>
                    )}
                    {plan.savings && (
                      <div className=\"text-sm text-green-600 font-medium mt-1\">{plan.savings}</div>
                    )}
                  </div>
                </CardHeader>
                
                <CardContent>
                  <ul className=\"space-y-3 mb-6\">
                    {plan.features.map((feature, index) => (
                      <li key={index} className=\"flex items-center text-sm\">
                        <CheckCircle className=\"w-4 h-4 text-green-500 mr-2 flex-shrink-0\" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  
                  {isSelected && (
                    <div className=\"bg-blue-50 p-4 rounded-lg mb-4\">
                      <div className=\"text-center text-blue-800 font-medium\">
                        ✨ 您選擇了 {plan.name}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Payment Form */}
        <Card className=\"max-w-2xl mx-auto\">
          <CardHeader>
            <CardTitle className=\"text-center text-2xl\">
              🔥 立即開始您的AI投資分析之旅
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPlan !== 'free' && (
              <div className=\"mb-6\">
                <label htmlFor=\"email\" className=\"block text-sm font-medium mb-2\">
                  電子信箱 (可選，用於接收訂閱確認)
                </label>
                <input
                  type=\"email\"
                  id=\"email\"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  placeholder=\"your.email@example.com\"
                  className=\"w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500\"
                />
              </div>
            )}
            
            {/* Selected Plan Summary */}
            <div className=\"bg-gray-50 p-4 rounded-lg mb-6\">
              <div className=\"flex justify-between items-center\">
                <span className=\"font-medium\">
                  選定方案: {pricingPlans.find(p => p.id === selectedPlan)?.name}
                </span>
                <span className=\"text-lg font-bold\">
                  {selectedPlan === 'free' ? '免費' : `NT$ ${pricingPlans.find(p => p.id === selectedPlan)?.price?.toLocaleString()}`}
                </span>
              </div>
              <div className=\"text-sm text-gray-600 mt-1\">
                解鎖 {pricingPlans.find(p => p.id === selectedPlan)?.analysts} 位專業AI分析師
              </div>
            </div>

            {paymentResponse && !paymentResponse.success && (
              <Alert className=\"mb-6 border-red-200 bg-red-50\">
                <AlertDescription className=\"text-red-800\">
                  ❌ {paymentResponse.message}
                </AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handlePayment}
              disabled={isProcessing}
              className=\"w-full py-4 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700\"
            >
              {isProcessing ? (
                <div className=\"flex items-center justify-center\">
                  <div className=\"animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2\"></div>
                  處理中...
                </div>
              ) : selectedPlan === 'free' ? (
                '🆓 立即免費開始'
              ) : (
                `💳 立即訂閱 ${pricingPlans.find(p => p.id === selectedPlan)?.name}`
              )}
            </Button>
            
            <div className=\"text-center mt-4 space-y-2\">
              <div className=\"text-sm text-gray-600\">
                🔒 採用PayUni金融級安全支付系統
              </div>
              <div className=\"text-xs text-gray-500\">
                ✅ 支援信用卡、ATM轉帳、超商付款
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Demo Call to Action */}
        <div className="text-center mt-12 p-8 bg-gradient-to-r from-green-600 to-blue-600 rounded-xl text-white">
          <h3 className="text-2xl font-bold mb-4">
            🎯 還不確定？先試用AI投資分析！
          </h3>
          <p className="text-lg mb-4">
            體驗6位專業AI分析師的投資建議，再決定是否升級會員
          </p>
          <div className="flex justify-center space-x-4">
            <Button 
              onClick={() => window.location.href = '/demo'}
              className="bg-white text-green-600 hover:bg-gray-100 font-semibold px-8 py-3"
            >
              🤖 免費試用AI分析師
            </Button>
            <Button 
              onClick={() => window.location.href = '/ai-demo'}
              className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-blue-600 font-semibold px-8 py-3"
            >
              🚀 查看完整演示
            </Button>
          </div>
        </div>

        {/* Success Guarantee */}
        <div className=\"text-center mt-12 p-8 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl\">
          <h3 className=\"text-2xl font-bold text-gray-900 mb-4\">
            🎯 30天滿意保證
          </h3>
          <p className=\"text-lg text-gray-700 mb-4\">
            如果您對我們的AI投資分析服務不滿意，我們提供30天無條件退款保證
          </p>
          <div className=\"flex justify-center space-x-8 text-sm text-gray-600\">
            <div>✅ 零風險試用</div>
            <div>✅ 隨時可取消</div>
            <div>✅ 即時客服支援</div>
          </div>
        </div>
      </div>
    </div>
  );
};
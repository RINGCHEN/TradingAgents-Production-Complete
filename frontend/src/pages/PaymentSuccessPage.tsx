import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  CreditCard, 
  Calendar, 
  User, 
  ArrowRight,
  Home,
  Settings
} from 'lucide-react';

/**
 * PayUni支付成功頁面
 * 顯示支付完成狀態和會員方案激活信息
 */
const PaymentSuccessPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [paymentInfo, setPaymentInfo] = useState({
    orderNumber: searchParams.get('order_number') || '',
    amount: searchParams.get('amount') || '',
    description: searchParams.get('description') || '',
    membershipTier: searchParams.get('tier') || 'gold'
  });

  // 會員方案映射
  const tierDisplayMap = {
    'gold': { name: '黃金會員', color: 'bg-yellow-500', icon: '👑' },
    'diamond': { name: '鑽石會員', color: 'bg-blue-500', icon: '💎' },
    'free': { name: '免費會員', color: 'bg-gray-500', icon: '👤' }
  };

  useEffect(() => {
    // 頁面載入時檢查支付狀態
    console.log('✅ 支付成功頁面載入', paymentInfo);
    
    // 可以在這裡添加API調用來驗證支付狀態
    // verifyPaymentStatus(paymentInfo.orderNumber);
  }, []);

  const handleGoToMemberCenter = () => {
    navigate('/member/center');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const currentTier = tierDisplayMap[paymentInfo.membershipTier as keyof typeof tierDisplayMap] || 
    tierDisplayMap.gold;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* 成功標題 */}
        <div className="text-center mb-8">
          <div className="mb-4">
            <CheckCircle className="w-20 h-20 text-green-500 mx-auto animate-pulse" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            🎉 支付成功！
          </h1>
          <p className="text-gray-600">
            恭喜您成功升級為TradingAgents會員
          </p>
        </div>

        {/* 支付詳情卡片 */}
        <Card className="mb-6 shadow-lg">
          <CardHeader className="bg-green-500 text-white rounded-t-lg">
            <CardTitle className="flex items-center">
              <CreditCard className="w-6 h-6 mr-2" />
              支付詳情
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid md:grid-cols-2 gap-4">
              {/* 訂單信息 */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">訂單編號:</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {paymentInfo.orderNumber || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">支付金額:</span>
                  <span className="font-bold text-green-600">
                    NT$ {paymentInfo.amount ? Number(paymentInfo.amount)?.toLocaleString() || 'N/A' : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">支付時間:</span>
                  <span className="text-gray-800">
                    {new Date().toLocaleString('zh-TW')}
                  </span>
                </div>
              </div>

              {/* 會員方案信息 */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">會員方案:</span>
                  <Badge className={`${currentTier.color} text-white`}>
                    {currentTier.icon} {currentTier.name}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">方案描述:</span>
                  <span className="text-gray-800">
                    {paymentInfo.description || '會員訂閱服務'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">生效時間:</span>
                  <span className="text-green-600 font-semibold">
                    立即生效
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 會員權益提醒 */}
        <Card className="mb-6 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center text-blue-700">
              <User className="w-6 h-6 mr-2" />
              您的會員權益已激活
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-800">🎯 分析服務</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 完整基本面分析</li>
                  <li>• 進階技術分析</li>
                  <li>• 個人化投資建議</li>
                  <li>• ART智能學習</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-800">💎 專屬服務</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 優先客服支援</li>
                  <li>• 投資組合追蹤</li>
                  <li>• 風險評估報告</li>
                  <li>• 每日50次查詢</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 行動按鈕 */}
        <div className="grid md:grid-cols-2 gap-4">
          <Button 
            onClick={handleGoToMemberCenter}
            className="bg-blue-600 hover:bg-blue-700"
            size="lg"
          >
            <Settings className="w-5 h-5 mr-2" />
            前往會員中心
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
          
          <Button 
            onClick={handleBackToHome}
            variant="outline"
            size="lg"
          >
            <Home className="w-5 h-5 mr-2" />
            返回首頁
          </Button>
        </div>

        {/* 客服信息 */}
        <div className="text-center mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-600 text-sm mb-2">
            如有任何問題，請聯繫我們的客服團隊
          </p>
          <div className="flex justify-center space-x-6 text-sm text-blue-600">
            <a href="mailto:support@tradingagents.com" className="hover:underline">
              📧 support@tradingagents.com
            </a>
            <span>|</span>
            <span>📞 02-1234-5678</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentSuccessPage;
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  XCircle, 
  ArrowLeft, 
  RefreshCw, 
  MessageSquare,
  Home
} from 'lucide-react';

/**
 * PayUni支付取消頁面
 * 用戶取消支付後的提示頁面
 */
const PaymentCancelPage: React.FC = () => {
  const navigate = useNavigate();

  const handleRetryPayment = () => {
    navigate('/pricing');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleContactSupport = () => {
    // 可以開啟客服聊天或郵件
    window.open('mailto:support@tradingagents.com?subject=支付取消諮詢');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* 取消標題 */}
        <div className="text-center mb-8">
          <div className="mb-4">
            <XCircle className="w-20 h-20 text-orange-500 mx-auto" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            支付已取消
          </h1>
          <p className="text-gray-600">
            您已取消此次支付操作，訂單未完成
          </p>
        </div>

        {/* 取消原因和協助 */}
        <Card className="mb-6 shadow-lg">
          <CardHeader className="bg-orange-500 text-white rounded-t-lg">
            <CardTitle>需要協助嗎？</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 mb-2">常見取消原因：</h3>
                <ul className="text-gray-600 space-y-1 text-sm">
                  <li>• 想要重新選擇方案或計費周期</li>
                  <li>• 支付方式有疑慮</li>
                  <li>• 需要更多時間考慮</li>
                  <li>• 遇到技術問題</li>
                </ul>
              </div>
              
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-800 mb-2">我們可以幫您：</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <p>🤝 <strong>免費諮詢</strong></p>
                    <p>了解最適合的方案選擇</p>
                  </div>
                  <div>
                    <p>💳 <strong>支付協助</strong></p>
                    <p>解決支付過程中的問題</p>
                  </div>
                  <div>
                    <p>🎁 <strong>專屬優惠</strong></p>
                    <p>為您提供限時優惠方案</p>
                  </div>
                  <div>
                    <p>⚡ <strong>快速支援</strong></p>
                    <p>即時解答您的疑問</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 會員方案價值提醒 */}
        <Card className="mb-6 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-700">
              💎 別錯過這些會員專屬權益
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl mb-2">🎯</div>
                <h4 className="font-semibold">AI智能分析</h4>
                <p className="text-gray-600">專業級投資分析服務</p>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-2">📊</div>
                <h4 className="font-semibold">投資組合追蹤</h4>
                <p className="text-gray-600">實時監控投資績效</p>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-2">🏆</div>
                <h4 className="font-semibold">優先客服</h4>
                <p className="text-gray-600">專屬客服快速回應</p>
              </div>
            </div>
            
            <div className="mt-4 p-3 bg-blue-50 rounded-lg text-center">
              <p className="text-blue-700 font-semibold">
                🎁 現在訂閱年付方案，享17%折扣優惠
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 行動按鈕 */}
        <div className="grid md:grid-cols-3 gap-4">
          <Button 
            onClick={handleRetryPayment}
            className="bg-blue-600 hover:bg-blue-700"
            size="lg"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            重新選擇方案
          </Button>
          
          <Button 
            onClick={handleContactSupport}
            variant="outline"
            size="lg"
            className="border-orange-500 text-orange-600 hover:bg-orange-50"
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            聯繫客服
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

        {/* 安全保障提醒 */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg text-center">
          <h3 className="font-semibold text-gray-800 mb-2">🔒 支付安全保障</h3>
          <p className="text-gray-600 text-sm mb-2">
            我們採用PayUni金流系統，符合國際PCI DSS安全標準
          </p>
          <div className="flex justify-center space-x-6 text-sm text-gray-500">
            <span>🛡️ SSL加密傳輸</span>
            <span>|</span>
            <span>🔐 不儲存卡號信息</span>
            <span>|</span>
            <span>✅ 金管會認證</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentCancelPage;
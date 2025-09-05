import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Brain, 
  TrendingUp, 
  NewspaperIcon, 
  Shield, 
  Users,
  Zap,
  Crown,
  Diamond,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  MessageSquare,
  Calculator,
  Play
} from 'lucide-react';

// 類型定義
interface AIAnalyst {
  type: string;
  name: string;
  description: string;
  icon?: React.ComponentType<any>;
}

interface TierFeatures {
  membership_tier: string;
  available_analysts: AIAnalyst[];
  max_concurrent_demos: number;
  daily_analysis_limit: number;
  limitations: string[];
  upgrade_benefits: string[];
}

interface DemoRequest {
  stock_symbol: string;
  analyst_preferences?: string[];
}

interface DemoResult {
  success: boolean;
  request_id?: string;
  selected_analysts?: string[];
  status?: string;
  error?: string;
  message?: string;
  demo_limitations?: string[];
}

const MemberAIFeatures: React.FC<{ userTier: string; userId?: string }> = ({ 
  userTier, 
  userId 
}) => {
  const [features, setFeatures] = useState<TierFeatures | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null);
  const [selectedStock, setSelectedStock] = useState('2330.TW');

  // 載入會員AI功能
  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        const response = await fetch(`/api/ai-demo/tier/${userTier}/features`);
        if (response.ok) {
          const data = await response.json();
          setFeatures(data);
        }
      } catch (error) {
        console.error('載入AI功能失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFeatures();
  }, [userTier]);

  // 分析師圖標映射
  const getAnalystIcon = (type: string) => {
    const iconMap: { [key: string]: React.ComponentType<any> } = {
      technical_analyst: TrendingUp,
      fundamentals_analyst: BarChart3,
      news_analyst: NewspaperIcon,
      social_media_analyst: MessageSquare,
      risk_analyst: Shield,
      investment_planner: Calculator
    };
    return iconMap[type] || Brain;
  };

  // 會員等級圖標和顏色
  const getTierDisplay = (tier: string) => {
    const displays = {
      FREE: { icon: Users, color: 'text-gray-600', bg: 'bg-gray-100', name: '免費會員' },
      GOLD: { icon: Crown, color: 'text-yellow-600', bg: 'bg-yellow-100', name: '黃金會員' },
      DIAMOND: { icon: Diamond, color: 'text-purple-600', bg: 'bg-purple-100', name: '鑽石會員' }
    };
    return displays[tier as keyof typeof displays] || displays.FREE;
  };

  // 創建AI演示
  const createAIDemo = async () => {
    if (!userId) {
      alert('請先登入以體驗AI功能');
      return;
    }

    setDemoLoading(true);
    setDemoResult(null);

    try {
      const response = await fetch('/api/ai-demo/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          stock_symbol: selectedStock,
          analyst_preferences: features?.available_analysts.map(a => a.type)
        })
      });

      const result = await response.json();
      setDemoResult(result);

      // 如果成功，輪詢結果
      if (result.success && result.request_id) {
        pollDemoResult(result.request_id);
      }

    } catch (error) {
      console.error('創建AI演示失敗:', error);
      setDemoResult({
        success: false,
        error: 'network_error',
        message: '網路連接失敗，請稍後再試'
      });
    } finally {
      setDemoLoading(false);
    }
  };

  // 輪詢演示結果
  const pollDemoResult = async (requestId: string) => {
    const maxAttempts = 30; // 最多輪詢30次 (5分鐘)
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/ai-demo/result/${requestId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (response.ok) {
          const result = await response.json();
          
          if (result.status === 'completed' || result.status === 'failed') {
            setDemoResult(prev => ({
              ...prev!,
              status: result.status,
              message: result.status === 'completed' ? '分析完成！' : '分析失敗'
            }));
            return;
          }

          // 繼續輪詢
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, 10000); // 10秒後再試
          } else {
            setDemoResult(prev => ({
              ...prev!,
              status: 'timeout',
              message: '分析超時，請稍後查看結果'
            }));
          }
        }
      } catch (error) {
        console.error('輪詢演示結果失敗:', error);
      }
    };

    // 開始輪詢
    setTimeout(poll, 5000); // 5秒後開始第一次輪詢
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">載入AI功能中...</span>
        </CardContent>
      </Card>
    );
  }

  if (!features) {
    return (
      <Card>
        <CardContent className="py-8">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              無法載入AI功能信息，請稍後重試
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const tierDisplay = getTierDisplay(features.membership_tier);

  return (
    <div className="space-y-6">
      {/* 會員等級展示 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <tierDisplay.icon className={`h-6 w-6 ${tierDisplay.color}`} />
            <span>{tierDisplay.name} AI功能</span>
            <Badge className={`${tierDisplay.bg} ${tierDisplay.color}`}>
              {features.membership_tier}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {features.available_analysts.length}
              </div>
              <div className="text-sm text-gray-600">可用分析師</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {features.daily_analysis_limit === -1 ? '無限制' : features.daily_analysis_limit}
              </div>
              <div className="text-sm text-gray-600">每日分析次數</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {features.max_concurrent_demos}
              </div>
              <div className="text-sm text-gray-600">同時分析數量</div>
            </div>
          </div>

          {/* AI分析師列表 */}
          <div className="space-y-3">
            <h3 className="font-semibold text-lg">可用AI分析師</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {features.available_analysts.map((analyst, index) => {
                const IconComponent = getAnalystIcon(analyst.type);
                return (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <IconComponent className="h-5 w-5 text-blue-600" />
                    <div>
                      <div className="font-medium">{analyst.name}</div>
                      <div className="text-sm text-gray-600">{analyst.description}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI功能演示 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Play className="h-5 w-5" />
            <span>體驗AI分析</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">選擇股票</label>
              <select 
                value={selectedStock}
                onChange={(e) => setSelectedStock(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="2330.TW">台積電 (2330)</option>
                <option value="2317.TW">鴻海 (2317)</option>
                <option value="2454.TW">聯發科 (2454)</option>
                <option value="1301.TW">台塑 (1301)</option>
                <option value="2382.TW">廣達 (2382)</option>
              </select>
            </div>
            <div className="flex-shrink-0">
              <Button 
                onClick={createAIDemo}
                disabled={demoLoading}
                className="flex items-center space-x-2"
              >
                {demoLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                <span>{demoLoading ? '分析中...' : '開始分析'}</span>
              </Button>
            </div>
          </div>

          {/* 演示結果 */}
          {demoResult && (
            <Alert className={demoResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              {demoResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-600" />
              )}
              <AlertDescription>
                <div className="space-y-2">
                  <div>{demoResult.message}</div>
                  {demoResult.success && demoResult.selected_analysts && (
                    <div className="text-sm">
                      使用分析師: {demoResult.selected_analysts.join(', ')}
                    </div>
                  )}
                  {demoResult.status && (
                    <div className="flex items-center space-x-2 text-sm">
                      <Clock className="h-3 w-3" />
                      <span>狀態: {demoResult.status}</span>
                    </div>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* 功能限制說明 */}
          {features.limitations.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-medium text-yellow-800 mb-2">當前限制</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                {features.limitations.map((limitation, index) => (
                  <li key={index}>{limitation}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 升級建議 */}
          {features.upgrade_benefits.length > 0 && features.membership_tier !== 'DIAMOND' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-800 mb-2">升級享受更多功能</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-700 mb-3">
                {features.upgrade_benefits.map((benefit, index) => (
                  <li key={index}>{benefit}</li>
                ))}
              </ul>
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                立即升級
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MemberAIFeatures;
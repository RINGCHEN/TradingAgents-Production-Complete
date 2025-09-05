import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Check, 
  X, 
  Crown, 
  Diamond,
  Users,
  Star,
  TrendingUp,
  Zap,
  Shield,
  ArrowRight
} from 'lucide-react';

// 類型定義
interface TierComparison {
  FREE: MembershipFeatures;
  GOLD: MembershipFeatures;
  DIAMOND: MembershipFeatures;
}

interface MembershipFeatures {
  name: string;
  display_name: string;
  price_monthly: number;
  price_yearly: number;
  available_analysts: string[];
  daily_limit: number;
  concurrent_demos: number;
  features: string[];
  limitations: string[];
  popular?: boolean;
}

interface Feature {
  name: string;
  description: string;
  free: boolean | string;
  gold: boolean | string;
  diamond: boolean | string;
}

const MembershipComparison: React.FC<{ currentTier?: string; onUpgrade?: (tier: string) => void }> = ({ 
  currentTier = 'FREE',
  onUpgrade 
}) => {
  const [comparison, setComparison] = useState<TierComparison | null>(null);
  const [loading, setLoading] = useState(true);

  // 載入會員對比數據
  useEffect(() => {
    const fetchComparison = async () => {
      try {
        // 載入三個等級的功能數據
        const [freeRes, goldRes, diamondRes] = await Promise.all([
          fetch('/api/ai-demo/tier/FREE/features'),
          fetch('/api/ai-demo/tier/GOLD/features'),
          fetch('/api/ai-demo/tier/DIAMOND/features')
        ]);

        const [freeData, goldData, diamondData] = await Promise.all([
          freeRes.json(),
          goldRes.json(),
          diamondRes.json()
        ]);

        // 組織對比數據
        setComparison({
          FREE: {
            name: '免費會員',
            display_name: '探索者',
            price_monthly: 0,
            price_yearly: 0,
            available_analysts: freeData.available_analysts?.map((a: any) => a.name) || [],
            daily_limit: freeData.daily_analysis_limit || 5,
            concurrent_demos: freeData.max_concurrent_demos || 1,
            features: [
              '基礎技術分析',
              '每日5次查詢',
              '基本技術指標',
              '社群支援'
            ],
            limitations: freeData.limitations || []
          },
          GOLD: {
            name: '黃金會員',
            display_name: '專業投資者',
            price_monthly: 1999,
            price_yearly: 19990,
            available_analysts: goldData.available_analysts?.map((a: any) => a.name) || [],
            daily_limit: goldData.daily_analysis_limit || 50,
            concurrent_demos: goldData.max_concurrent_demos || 2,
            features: [
              '完整基本面分析',
              '每日50次查詢',
              '進階技術分析',
              '個人化投資建議',
              '新聞情緒分析',
              '優先客服支援',
              '投資組合追蹤'
            ],
            limitations: goldData.limitations || [],
            popular: true
          },
          DIAMOND: {
            name: '鑽石會員',
            display_name: '投資專家',
            price_monthly: 4999,
            price_yearly: 49990,
            available_analysts: diamondData.available_analysts?.map((a: any) => a.name) || [],
            daily_limit: diamondData.daily_analysis_limit || -1,
            concurrent_demos: diamondData.max_concurrent_demos || 5,
            features: [
              '全方位深度分析',
              '無限次查詢',
              '完整6位AI分析師',
              '風險評估報告',
              '投資策略規劃',
              '實時市場監控',
              '專屬客戶經理',
              '優先功能預覽'
            ],
            limitations: diamondData.limitations || []
          }
        });

      } catch (error) {
        console.error('載入會員對比失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, []);

  // 功能對比表
  const featureMatrix: Feature[] = [
    {
      name: 'AI分析師',
      description: '可使用的專業AI分析師數量',
      free: '1位 (技術分析師)',
      gold: '4位 (技術+基本面+新聞+社群)',
      diamond: '6位 (完整團隊)'
    },
    {
      name: '每日分析次數',
      description: '每天可以進行的分析次數',
      free: '5次',
      gold: '50次',
      diamond: '無限制'
    },
    {
      name: '同時分析',
      description: '可同時進行的分析數量',
      free: '1個',
      gold: '2個',
      diamond: '5個'
    },
    {
      name: '基本面分析',
      description: '財務報表和公司基本面分析',
      free: false,
      gold: true,
      diamond: true
    },
    {
      name: '新聞情緒分析',
      description: '實時新聞和市場情緒分析',
      free: false,
      gold: true,
      diamond: true
    },
    {
      name: '風險評估',
      description: '投資風險分析和管理建議',
      free: false,
      gold: false,
      diamond: true
    },
    {
      name: '投資策略規劃',
      description: '個人化投資組合和策略建議',
      free: false,
      gold: false,
      diamond: true
    },
    {
      name: '實時數據',
      description: '即時股價和市場數據',
      free: '延遲15分鐘',
      gold: '延遲5分鐘',
      diamond: '即時'
    },
    {
      name: '導出報告',
      description: '分析報告下載和分享',
      free: false,
      gold: 'PDF格式',
      diamond: '多種格式'
    },
    {
      name: '客戶支援',
      description: '技術支援和客戶服務',
      free: '社群支援',
      gold: '郵件支援',
      diamond: '專屬客戶經理'
    }
  ];

  const getTierIcon = (tier: string) => {
    const icons = {
      FREE: Users,
      GOLD: Crown,
      DIAMOND: Diamond
    };
    return icons[tier as keyof typeof icons] || Users;
  };

  const getTierColor = (tier: string) => {
    const colors = {
      FREE: 'text-gray-600 bg-gray-100',
      GOLD: 'text-yellow-600 bg-yellow-100',
      DIAMOND: 'text-purple-600 bg-purple-100'
    };
    return colors[tier as keyof typeof colors] || colors.FREE;
  };

  const renderFeatureValue = (value: boolean | string) => {
    if (typeof value === 'boolean') {
      return value ? (
        <Check className="h-5 w-5 text-green-600 mx-auto" />
      ) : (
        <X className="h-5 w-5 text-gray-400 mx-auto" />
      );
    }
    return <span className="text-sm text-center">{value}</span>;
  };

  if (loading || !comparison) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="animate-pulse">載入會員方案對比中...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 會員方案卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {(Object.keys(comparison) as (keyof TierComparison)[]).map((tier) => {
          const plan = comparison[tier];
          const TierIcon = getTierIcon(tier);
          const colorClasses = getTierColor(tier);
          const isCurrentTier = currentTier === tier;

          return (
            <Card key={tier} className={`relative ${plan.popular ? 'ring-2 ring-blue-500' : ''}`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-blue-500 text-white">
                    <Star className="h-3 w-3 mr-1" />
                    最受歡迎
                  </Badge>
                </div>
              )}
              
              <CardHeader className="text-center">
                <div className={`w-12 h-12 rounded-full ${colorClasses} mx-auto flex items-center justify-center mb-4`}>
                  <TierIcon className="h-6 w-6" />
                </div>
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <div className="text-sm text-gray-600">{plan.display_name}</div>
                
                <div className="mt-4">
                  <div className="text-3xl font-bold">
                    {plan.price_monthly === 0 ? (
                      '免費'
                    ) : (
                      <>
                        <span className="text-2xl">NT$</span>
                        {plan.price_monthly.toLocaleString()}
                      </>
                    )}
                  </div>
                  {plan.price_monthly > 0 && (
                    <div className="text-sm text-gray-600">每月 / 年付享85折</div>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>AI分析師</span>
                    <span className="font-medium">{plan.available_analysts.length}位</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>每日分析</span>
                    <span className="font-medium">
                      {plan.daily_limit === -1 ? '無限制' : `${plan.daily_limit}次`}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>同時分析</span>
                    <span className="font-medium">{plan.concurrent_demos}個</span>
                  </div>
                </div>

                <div className="space-y-1">
                  {plan.features.slice(0, 4).map((feature, index) => (
                    <div key={index} className="flex items-center text-sm">
                      <Check className="h-4 w-4 text-green-600 mr-2 flex-shrink-0" />
                      <span>{feature}</span>
                    </div>
                  ))}
                  {plan.features.length > 4 && (
                    <div className="text-sm text-gray-600">
                      還有 {plan.features.length - 4} 項功能...
                    </div>
                  )}
                </div>

                <div className="pt-4">
                  {isCurrentTier ? (
                    <Badge className="w-full justify-center py-2 bg-green-100 text-green-800">
                      當前方案
                    </Badge>
                  ) : (
                    <Button 
                      className="w-full"
                      variant={plan.popular ? "default" : "outline"}
                      onClick={() => onUpgrade && onUpgrade(tier)}
                    >
                      {tier === 'FREE' ? '免費開始' : `升級至${plan.name}`}
                      {tier !== 'FREE' && <ArrowRight className="h-4 w-4 ml-2" />}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 詳細功能對比表 */}
      <Card>
        <CardHeader>
          <CardTitle>功能詳細對比</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">功能</th>
                  <th className="text-center py-3 px-4">免費會員</th>
                  <th className="text-center py-3 px-4">黃金會員</th>
                  <th className="text-center py-3 px-4">鑽石會員</th>
                </tr>
              </thead>
              <tbody>
                {featureMatrix.map((feature, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <div>
                        <div className="font-medium">{feature.name}</div>
                        <div className="text-sm text-gray-600">{feature.description}</div>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-center">
                      {renderFeatureValue(feature.free)}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {renderFeatureValue(feature.gold)}
                    </td>
                    <td className="py-4 px-4 text-center">
                      {renderFeatureValue(feature.diamond)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 升級提示 */}
      {currentTier !== 'DIAMOND' && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardContent className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-900">
                  準備提升您的投資分析能力？
                </h3>
                <p className="text-blue-700 mt-1">
                  升級會員享受更多AI分析師和專業功能，讓投資決策更精準
                </p>
              </div>
              <Button 
                size="lg" 
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() => onUpgrade && onUpgrade(currentTier === 'FREE' ? 'GOLD' : 'DIAMOND')}
              >
                <Zap className="h-4 w-4 mr-2" />
                立即升級
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MembershipComparison;
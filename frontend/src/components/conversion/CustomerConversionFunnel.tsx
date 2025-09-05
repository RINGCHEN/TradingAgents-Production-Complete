/**
 * 客戶轉換漏斗系統
 * 追蹤用戶從接觸到付費的完整轉換過程
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Users, 
  Eye, 
  UserPlus, 
  Play, 
  CreditCard,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Calendar,
  Mail,
  Phone,
  MessageSquare,
  Gift,
  Star,
  Clock,
  DollarSign,
  Zap,
  Award,
  ChevronRight
} from 'lucide-react';

// 漏斗階段定義
interface FunnelStage {
  id: string;
  name: string;
  description: string;
  userCount: number;
  conversionRate: number;
  value: number; // 商業價值
  avgTimeSpent: number; // 平均停留時間（小時）
  dropoffReasons: string[];
  optimizationActions: string[];
}

// 用戶行為追蹤
interface UserJourney {
  userId: string;
  email: string;
  currentStage: string;
  entryDate: Date;
  lastActivity: Date;
  touchpoints: Array<{
    stage: string;
    timestamp: Date;
    action: string;
    channel: string;
  }>;
  ltv: number; // 生命週期價值
  score: number; // 轉換分數
}

// 轉換指標
interface ConversionMetrics {
  totalVisitors: number;
  totalSignups: number;
  totalTrialUsers: number;
  totalPaidUsers: number;
  
  visitorToSignup: number;
  signupToTrial: number;
  trialToPaid: number;
  overallConversion: number;
  
  averageDaysToConvert: number;
  revenuePerUser: number;
  customerLifetimeValue: number;
  churnRate: number;
  
  monthlyGrowthRate: number;
  revenueTarget: number;
  revenueActual: number;
}

// 營銷活動
interface MarketingCampaign {
  id: string;
  name: string;
  channel: string;
  status: 'active' | 'paused' | 'completed';
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cpa: number; // Cost per acquisition
  roas: number; // Return on ad spend
  startDate: Date;
  endDate?: Date;
}

const CustomerConversionFunnel: React.FC = () => {
  const [funnelStages, setFunnelStages] = useState<FunnelStage[]>([]);
  const [metrics, setMetrics] = useState<ConversionMetrics | null>(null);
  const [userJourneys, setUserJourneys] = useState<UserJourney[]>([]);
  const [campaigns, setCampaigns] = useState<MarketingCampaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'funnel' | 'users' | 'campaigns' | 'optimization'>('funnel');
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  // 載入轉換數據
  const loadConversionData = useCallback(async () => {
    setLoading(true);
    try {
      const [funnelRes, metricsRes, journeysRes, campaignsRes] = await Promise.all([
        fetch(`/api/conversion/funnel?timeRange=${timeRange}`),
        fetch(`/api/conversion/metrics?timeRange=${timeRange}`),
        fetch(`/api/conversion/user-journeys?timeRange=${timeRange}`),
        fetch(`/api/conversion/campaigns?timeRange=${timeRange}`)
      ]);

      if (funnelRes.ok) {
        const funnelData = await funnelRes.json();
        setFunnelStages(funnelData.stages || []);
      }

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (journeysRes.ok) {
        const journeysData = await journeysRes.json();
        setUserJourneys(journeysData.journeys || []);
      }

      if (campaignsRes.ok) {
        const campaignsData = await campaignsRes.json();
        setCampaigns(campaignsData.campaigns || []);
      }
    } catch (error) {
      console.error('載入轉換數據失敗:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 發送營銷郵件
  const sendMarketingEmail = async (segment: string, template: string) => {
    try {
      const response = await fetch('/api/conversion/send-marketing-email', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ segment, template })
      });
      
      if (response.ok) {
        alert(`${segment}營銷郵件已發送`);
        loadConversionData();
      }
    } catch (error) {
      console.error('發送營銷郵件失敗:', error);
    }
  };

  // 創建重定向廣告
  const createRetargetingCampaign = async (audience: string, budget: number) => {
    try {
      const response = await fetch('/api/conversion/create-retargeting', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ audience, budget })
      });
      
      if (response.ok) {
        alert('重定向廣告已創建');
        loadConversionData();
      }
    } catch (error) {
      console.error('創建重定向廣告失敗:', error);
    }
  };

  useEffect(() => {
    loadConversionData();
  }, [loadConversionData]);

  // 轉換漏斗可視化
  const renderFunnelVisualization = () => (
    <div className="space-y-6">
      {/* 關鍵指標概覽 */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Eye className="w-8 h-8 mx-auto mb-2 text-blue-500" />
              <p className="text-2xl font-bold">{metrics.totalVisitors.toLocaleString()}</p>
              <p className="text-sm text-gray-600">總訪客數</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <UserPlus className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="text-2xl font-bold">{metrics.totalSignups.toLocaleString()}</p>
              <p className="text-sm text-gray-600">註冊用戶</p>
              <p className="text-xs text-green-600">
                轉換率: {metrics.visitorToSignup.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Play className="w-8 h-8 mx-auto mb-2 text-orange-500" />
              <p className="text-2xl font-bold">{metrics.totalTrialUsers.toLocaleString()}</p>
              <p className="text-sm text-gray-600">試用用戶</p>
              <p className="text-xs text-orange-600">
                轉換率: {metrics.signupToTrial.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <CreditCard className="w-8 h-8 mx-auto mb-2 text-purple-500" />
              <p className="text-2xl font-bold">{metrics.totalPaidUsers.toLocaleString()}</p>
              <p className="text-sm text-gray-600">付費用戶</p>
              <p className="text-xs text-purple-600">
                轉換率: {metrics.trialToPaid.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 轉換漏斗圖 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            轉換漏斗分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {funnelStages.map((stage, index) => {
              const isLast = index === funnelStages.length - 1;
              const nextStage = funnelStages[index + 1];
              const dropoffRate = nextStage 
                ? ((stage.userCount - nextStage.userCount) / stage.userCount * 100)
                : 0;
              
              return (
                <div key={stage.id} className="relative">
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-blue-100">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-lg">{stage.name}</h4>
                        <Badge variant="outline">
                          {stage.userCount.toLocaleString()} 用戶
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-2">{stage.description}</p>
                      
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">轉換率: </span>
                          <span className="font-medium">{stage.conversionRate.toFixed(1)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-500">平均停留: </span>
                          <span className="font-medium">{stage.avgTimeSpent.toFixed(1)}小時</span>
                        </div>
                        <div>
                          <span className="text-gray-500">價值: </span>
                          <span className="font-medium">NT${stage.value.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="ml-4 text-right">
                      <div className={`text-2xl font-bold ${
                        stage.conversionRate > 50 ? 'text-green-600' :
                        stage.conversionRate > 20 ? 'text-orange-600' : 'text-red-600'
                      }`}>
                        {stage.conversionRate.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  
                  {/* 流失分析 */}
                  {!isLast && dropoffRate > 0 && (
                    <div className="flex items-center justify-center py-2">
                      <div className="bg-red-100 px-3 py-1 rounded-full text-sm text-red-700">
                        <TrendingDown className="w-4 h-4 inline mr-1" />
                        流失 {dropoffRate.toFixed(1)}% 
                        ({(stage.userCount - (nextStage?.userCount || 0)).toLocaleString()} 用戶)
                      </div>
                    </div>
                  )}
                  
                  {/* 優化建議 */}
                  {stage.optimizationActions.length > 0 && (
                    <div className="mt-2 p-3 bg-yellow-50 rounded-lg">
                      <h5 className="font-medium text-sm mb-2 text-yellow-800">優化建議:</h5>
                      <ul className="text-xs text-yellow-700">
                        {stage.optimizationActions.slice(0, 3).map((action, idx) => (
                          <li key={idx} className="flex items-center">
                            <Target className="w-3 h-3 mr-1" />
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {!isLast && (
                    <div className="flex justify-center py-2">
                      <ChevronRight className="w-6 h-6 text-gray-400" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 收益分析 */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <DollarSign className="w-5 h-5 mr-2" />
                收益指標
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>月收益目標</span>
                  <span className="font-bold">NT${metrics.revenueTarget.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>實際月收益</span>
                  <span className={`font-bold ${
                    metrics.revenueActual >= metrics.revenueTarget ? 'text-green-600' : 'text-red-600'
                  }`}>
                    NT${metrics.revenueActual.toLocaleString()}
                  </span>
                </div>
                <Progress 
                  value={(metrics.revenueActual / metrics.revenueTarget) * 100}
                  className="w-full"
                />
                <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                  <div>
                    <p className="text-sm text-gray-600">平均客單價</p>
                    <p className="text-lg font-bold">NT${metrics.revenuePerUser.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">客戶生命週期價值</p>
                    <p className="text-lg font-bold">NT${metrics.customerLifetimeValue.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="w-5 h-5 mr-2" />
                轉換效率
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>整體轉換率</span>
                  <span className="font-bold text-blue-600">
                    {metrics.overallConversion.toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>平均轉換週期</span>
                  <span className="font-medium">
                    {metrics.averageDaysToConvert} 天
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>用戶流失率</span>
                  <span className={`font-medium ${
                    metrics.churnRate > 10 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {metrics.churnRate.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>月增長率</span>
                  <div className="flex items-center">
                    {metrics.monthlyGrowthRate >= 0 ? (
                      <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                    ) : (
                      <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
                    )}
                    <span className={`font-medium ${
                      metrics.monthlyGrowthRate >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {metrics.monthlyGrowthRate >= 0 ? '+' : ''}{metrics.monthlyGrowthRate.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );

  // 用戶行為分析
  const renderUserJourney = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-5 h-5 mr-2" />
            高價值用戶行為分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {userJourneys.slice(0, 10).map(journey => (
              <div key={journey.userId} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h4 className="font-medium">{journey.email}</h4>
                    <p className="text-sm text-gray-600">
                      當前階段: {journey.currentStage} | 
                      LTV: NT${journey.ltv.toLocaleString()} |
                      評分: {journey.score}/100
                    </p>
                  </div>
                  <Badge variant={
                    journey.score >= 80 ? 'default' :
                    journey.score >= 60 ? 'secondary' : 'outline'
                  }>
                    {journey.score >= 80 ? '高' : journey.score >= 60 ? '中' : '低'}潛力
                  </Badge>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-medium mb-2">用戶軌跡</h5>
                    <div className="space-y-1">
                      {journey.touchpoints.slice(0, 4).map((touchpoint, idx) => (
                        <div key={idx} className="text-sm flex items-center">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                          <span className="text-gray-600">
                            {new Date(touchpoint.timestamp).toLocaleDateString()}
                          </span>
                          <span className="ml-2">{touchpoint.action}</span>
                          <Badge variant="outline" className="ml-2 text-xs">
                            {touchpoint.channel}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="font-medium mb-2">推薦行動</h5>
                    <div className="space-y-1">
                      {journey.score < 40 && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => sendMarketingEmail('low_engagement', 'reactivation')}
                        >
                          <Mail className="w-3 h-3 mr-1" />
                          發送重新激活郵件
                        </Button>
                      )}
                      {journey.score >= 60 && journey.currentStage === 'trial' && (
                        <Button 
                          size="sm"
                          onClick={() => sendMarketingEmail('trial_users', 'upgrade_offer')}
                        >
                          <Gift className="w-3 h-3 mr-1" />
                          發送升級優惠
                        </Button>
                      )}
                      {journey.score >= 80 && (
                        <Button 
                          size="sm" 
                          variant="default"
                          onClick={() => sendMarketingEmail('high_value', 'vip_program')}
                        >
                          <Award className="w-3 h-3 mr-1" />
                          邀請VIP計劃
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // 營銷活動管理
  const renderCampaignManagement = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              營銷活動管理
            </CardTitle>
            <Button onClick={() => createRetargetingCampaign('trial_dropoff', 5000)}>
              創建重定向廣告
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {campaigns.map(campaign => (
              <div key={campaign.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h4 className="font-medium">{campaign.name}</h4>
                    <p className="text-sm text-gray-600">
                      {campaign.channel} | 
                      預算: NT${campaign.budget.toLocaleString()} |
                      已花費: NT${campaign.spent.toLocaleString()}
                    </p>
                  </div>
                  <Badge variant={
                    campaign.status === 'active' ? 'default' :
                    campaign.status === 'paused' ? 'secondary' : 'outline'
                  }>
                    {campaign.status}
                  </Badge>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">曝光次數</p>
                    <p className="font-medium">{campaign.impressions.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">點擊次數</p>
                    <p className="font-medium">{campaign.clicks.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">轉換次數</p>
                    <p className="font-medium">{campaign.conversions.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">獲客成本</p>
                    <p className="font-medium">NT${campaign.cpa.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">廣告投報率</p>
                    <p className={`font-medium ${
                      campaign.roas >= 3 ? 'text-green-600' : 
                      campaign.roas >= 2 ? 'text-orange-600' : 'text-red-600'
                    }`}>
                      {campaign.roas.toFixed(1)}x
                    </p>
                  </div>
                </div>
                
                <Progress 
                  value={(campaign.spent / campaign.budget) * 100}
                  className="mt-3"
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* 頁面標題和控制 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">客戶轉換漏斗</h1>
          <p className="text-gray-600">追蹤用戶轉換過程，優化商業化策略</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select 
            className="border rounded-md p-2"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
          >
            <option value="7d">近7天</option>
            <option value="30d">近30天</option>
            <option value="90d">近90天</option>
          </select>
          
          <Button onClick={loadConversionData} disabled={loading}>
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <BarChart3 className="w-4 h-4" />
            )}
            <span className="ml-2">刷新數據</span>
          </Button>
        </div>
      </div>

      {/* 標籤頁導航 */}
      <div className="flex space-x-1 mb-6 border-b">
        {[
          { key: 'funnel', label: '轉換漏斗', icon: BarChart3 },
          { key: 'users', label: '用戶行為', icon: Users },
          { key: 'campaigns', label: '營銷活動', icon: Zap },
          { key: 'optimization', label: '優化建議', icon: Target }
        ].map(tab => (
          <button
            key={tab.key}
            className={`flex items-center px-4 py-2 font-medium rounded-t-lg transition-colors ${
              activeTab === tab.key
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-blue-500'
            }`}
            onClick={() => setActiveTab(tab.key as any)}
          >
            <tab.icon className="w-4 h-4 mr-2" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* 標籤頁內容 */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3">載入中...</span>
        </div>
      )}

      {!loading && (
        <>
          {activeTab === 'funnel' && renderFunnelVisualization()}
          {activeTab === 'users' && renderUserJourney()}
          {activeTab === 'campaigns' && renderCampaignManagement()}
          {activeTab === 'optimization' && (
            <Card>
              <CardHeader>
                <CardTitle>轉換優化建議</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-800 mb-2">高效策略</h4>
                    <ul className="text-sm text-green-700 space-y-1">
                      <li>• A/B測試不同的註冊流程設計</li>
                      <li>• 優化試用期間的用戶引導體驗</li>
                      <li>• 建立個人化的推薦系統</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <h4 className="font-medium text-yellow-800 mb-2">注意事項</h4>
                    <ul className="text-sm text-yellow-700 space-y-1">
                      <li>• 監控試用到付費階段的流失率</li>
                      <li>• 優化移動端用戶體驗</li>
                      <li>• 加強客戶成功團隊的介入</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 bg-red-50 rounded-lg">
                    <h4 className="font-medium text-red-800 mb-2">緊急改善</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      <li>• 減少註冊流程的摩擦點</li>
                      <li>• 提供更多免費價值內容</li>
                      <li>• 改善定價頁面的說服力</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default CustomerConversionFunnel;
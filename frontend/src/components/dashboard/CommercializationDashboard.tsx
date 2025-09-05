/**
 * TTS商業化運營儀表板
 * 整合收益、用戶、轉換等關鍵業務指標的統一管理中心
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  DollarSign,
  Users,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Star,
  Globe,
  CreditCard,
  UserPlus,
  Activity,
  Award,
  Bell,
  Settings,
  RefreshCw,
  Download,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

// 商業指標定義
interface RevenueMetrics {
  monthlyRecurringRevenue: number;
  monthlyGrowthRate: number;
  yearlyProjection: number;
  averageRevenuePerUser: number;
  customerLifetimeValue: number;
  churnRate: number;
  netRevenueRetention: number;
  revenueTarget: number;
  revenueActual: number;
  targetAchievementRate: number;
}

interface UserMetrics {
  totalUsers: number;
  activeUsers: number;
  newUsersThisMonth: number;
  paidUsers: number;
  trialUsers: number;
  freeUsers: number;
  conversionRate: number;
  userGrowthRate: number;
  averageSessionDuration: number;
  dailyActiveUsers: number;
  monthlyActiveUsers: number;
  userRetentionRate: number;
}

interface ProductMetrics {
  totalTTSRequests: number;
  successRate: number;
  averageProcessingTime: number;
  popularAnalysts: Array<{
    name: string;
    usage: number;
    revenue: number;
  }>;
  featureAdoptionRates: Record<string, number>;
  customerSatisfactionScore: number;
  supportTickets: number;
  bugReports: number;
}

interface MarketingMetrics {
  totalCampaigns: number;
  activeCampaigns: number;
  totalSpend: number;
  totalRevenue: number;
  roas: number; // Return on Ad Spend
  cac: number; // Customer Acquisition Cost
  ltv_cac_ratio: number;
  organicTraffic: number;
  paidTraffic: number;
  conversionsByChannel: Record<string, number>;
}

// 商業警報
interface BusinessAlert {
  id: string;
  type: 'revenue' | 'user' | 'product' | 'marketing';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
  actionRequired: boolean;
  recommendedAction?: string;
}

// 商業目標
interface BusinessGoal {
  id: string;
  category: string;
  description: string;
  target: number;
  current: number;
  deadline: Date;
  status: 'on_track' | 'at_risk' | 'behind' | 'completed';
  progress: number;
}

const CommercializationDashboard: React.FC = () => {
  const [revenueMetrics, setRevenueMetrics] = useState<RevenueMetrics | null>(null);
  const [userMetrics, setUserMetrics] = useState<UserMetrics | null>(null);
  const [productMetrics, setProductMetrics] = useState<ProductMetrics | null>(null);
  const [marketingMetrics, setMarketingMetrics] = useState<MarketingMetrics | null>(null);
  const [alerts, setAlerts] = useState<BusinessAlert[]>([]);
  const [goals, setGoals] = useState<BusinessGoal[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 載入所有業務數據
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [revenueRes, userRes, productRes, marketingRes, alertsRes, goalsRes] = await Promise.all([
        fetch('/api/dashboard/revenue-metrics'),
        fetch('/api/dashboard/user-metrics'),
        fetch('/api/dashboard/product-metrics'),
        fetch('/api/dashboard/marketing-metrics'),
        fetch('/api/dashboard/alerts'),
        fetch('/api/dashboard/goals')
      ]);

      if (revenueRes.ok) {
        const data = await revenueRes.json();
        setRevenueMetrics(data);
      }

      if (userRes.ok) {
        const data = await userRes.json();
        setUserMetrics(data);
      }

      if (productRes.ok) {
        const data = await productRes.json();
        setProductMetrics(data);
      }

      if (marketingRes.ok) {
        const data = await marketingRes.json();
        setMarketingMetrics(data);
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAlerts(data.alerts || []);
      }

      if (goalsRes.ok) {
        const data = await goalsRes.json();
        setGoals(data.goals || []);
      }

      setLastUpdateTime(new Date());
    } catch (error) {
      console.error('載入儀表板數據失敗:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 導出業務報告
  const exportBusinessReport = async () => {
    try {
      const response = await fetch('/api/dashboard/export-report', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `business-report-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('導出報告失敗:', error);
    }
  };

  // 自動刷新機制
  useEffect(() => {
    loadDashboardData();
    
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, 5 * 60 * 1000); // 5分鐘刷新
      return () => clearInterval(interval);
    }
  }, [loadDashboardData, autoRefresh]);

  // 指標卡片組件
  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color: string;
    subtitle?: string;
    trend?: 'up' | 'down' | 'stable';
  }> = ({ title, value, change, icon, color, subtitle, trend }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
            {change !== undefined && (
              <div className={`flex items-center text-sm mt-1 ${
                change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {change >= 0 ? (
                  <ArrowUpRight className="w-3 h-3 mr-1" />
                ) : (
                  <ArrowDownRight className="w-3 h-3 mr-1" />
                )}
                {change >= 0 ? '+' : ''}{change.toFixed(1)}%
              </div>
            )}
          </div>
          <div className={`p-3 rounded-full ${color}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // 警報組件
  const AlertCard: React.FC<{ alert: BusinessAlert }> = ({ alert }) => (
    <div className={`p-3 rounded-lg border-l-4 ${
      alert.severity === 'critical' ? 'border-red-500 bg-red-50' :
      alert.severity === 'high' ? 'border-orange-500 bg-orange-50' :
      alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
      'border-blue-500 bg-blue-50'
    }`}>
      <div className="flex items-start justify-between">
        <div>
          <p className={`font-medium ${
            alert.severity === 'critical' ? 'text-red-800' :
            alert.severity === 'high' ? 'text-orange-800' :
            alert.severity === 'medium' ? 'text-yellow-800' :
            'text-blue-800'
          }`}>
            {alert.message}
          </p>
          {alert.recommendedAction && (
            <p className="text-sm text-gray-600 mt-1">{alert.recommendedAction}</p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            {new Date(alert.timestamp).toLocaleString()}
          </p>
        </div>
        <Badge variant={
          alert.severity === 'critical' ? 'destructive' :
          alert.severity === 'high' ? 'destructive' :
          alert.severity === 'medium' ? 'secondary' : 'outline'
        }>
          {alert.severity}
        </Badge>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* 頁面標題和控制 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">商業化運營儀表板</h1>
          <p className="text-gray-600">
            實時監控業務指標 • 最後更新: {lastUpdateTime.toLocaleTimeString()}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className="w-4 h-4 mr-2" />
            自動刷新
          </Button>
          
          <Button onClick={loadDashboardData} disabled={loading} size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          
          <Button onClick={exportBusinessReport} size="sm">
            <Download className="w-4 h-4 mr-2" />
            導出報告
          </Button>
        </div>
      </div>

      {/* 重要警報 */}
      {alerts.length > 0 && (
        <Card className="mb-6 border-orange-200">
          <CardHeader>
            <CardTitle className="flex items-center text-orange-700">
              <Bell className="w-5 h-5 mr-2" />
              業務警報 ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-40 overflow-y-auto">
              {alerts.slice(0, 5).map(alert => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 收益指標概覽 */}
      {revenueMetrics && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <DollarSign className="w-5 h-5 mr-2" />
            收益指標
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <MetricCard
              title="月經常性收入"
              value={`NT$${revenueMetrics.monthlyRecurringRevenue.toLocaleString()}`}
              change={revenueMetrics.monthlyGrowthRate}
              icon={<DollarSign className="w-6 h-6 text-white" />}
              color="bg-green-500"
              subtitle="MRR"
            />
            <MetricCard
              title="平均客單價"
              value={`NT$${revenueMetrics.averageRevenuePerUser.toLocaleString()}`}
              icon={<Users className="w-6 h-6 text-white" />}
              color="bg-blue-500"
              subtitle="ARPU"
            />
            <MetricCard
              title="客戶生命週期價值"
              value={`NT$${revenueMetrics.customerLifetimeValue.toLocaleString()}`}
              icon={<Award className="w-6 h-6 text-white" />}
              color="bg-purple-500"
              subtitle="LTV"
            />
            <MetricCard
              title="流失率"
              value={`${revenueMetrics.churnRate.toFixed(1)}%`}
              change={-revenueMetrics.churnRate * 0.1}
              icon={<TrendingDown className="w-6 h-6 text-white" />}
              color="bg-red-500"
              subtitle="月流失率"
            />
          </div>
          
          {/* 收益目標進度 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>月收益目標進度</span>
                <Badge variant={
                  revenueMetrics.targetAchievementRate >= 100 ? 'default' :
                  revenueMetrics.targetAchievementRate >= 80 ? 'secondary' : 'destructive'
                }>
                  {revenueMetrics.targetAchievementRate.toFixed(1)}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>目標: NT${revenueMetrics.revenueTarget.toLocaleString()}</span>
                  <span>實際: NT${revenueMetrics.revenueActual.toLocaleString()}</span>
                </div>
                <Progress value={revenueMetrics.targetAchievementRate} className="w-full" />
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">年度預測: </span>
                    <span className="font-medium">NT${revenueMetrics.yearlyProjection.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">淨收入留存: </span>
                    <span className="font-medium">{revenueMetrics.netRevenueRetention.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 用戶指標 */}
      {userMetrics && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            用戶指標
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <MetricCard
              title="總用戶數"
              value={userMetrics.totalUsers.toLocaleString()}
              change={userMetrics.userGrowthRate}
              icon={<Users className="w-6 h-6 text-white" />}
              color="bg-blue-500"
            />
            <MetricCard
              title="月活躍用戶"
              value={userMetrics.monthlyActiveUsers.toLocaleString()}
              icon={<Activity className="w-6 h-6 text-white" />}
              color="bg-green-500"
              subtitle="MAU"
            />
            <MetricCard
              title="付費用戶"
              value={userMetrics.paidUsers.toLocaleString()}
              icon={<CreditCard className="w-6 h-6 text-white" />}
              color="bg-purple-500"
            />
            <MetricCard
              title="轉換率"
              value={`${userMetrics.conversionRate.toFixed(1)}%`}
              change={userMetrics.conversionRate * 0.05}
              icon={<TrendingUp className="w-6 h-6 text-white" />}
              color="bg-orange-500"
            />
          </div>
          
          {/* 用戶分布餅圖 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>用戶分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>付費用戶</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-purple-500 h-2 rounded-full"
                          style={{ width: `${(userMetrics.paidUsers / userMetrics.totalUsers) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{userMetrics.paidUsers.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>試用用戶</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-orange-500 h-2 rounded-full"
                          style={{ width: `${(userMetrics.trialUsers / userMetrics.totalUsers) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{userMetrics.trialUsers.toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>免費用戶</span>
                    <div className="flex items-center">
                      <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${(userMetrics.freeUsers / userMetrics.totalUsers) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">{userMetrics.freeUsers.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>用戶活躍度</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>日活躍用戶 (DAU)</span>
                    <span className="font-medium">{userMetrics.dailyActiveUsers.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>月活躍用戶 (MAU)</span>
                    <span className="font-medium">{userMetrics.monthlyActiveUsers.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均會話時長</span>
                    <span className="font-medium">{Math.round(userMetrics.averageSessionDuration)}分鐘</span>
                  </div>
                  <div className="flex justify-between">
                    <span>用戶留存率</span>
                    <span className={`font-medium ${
                      userMetrics.userRetentionRate >= 80 ? 'text-green-600' : 
                      userMetrics.userRetentionRate >= 60 ? 'text-orange-600' : 'text-red-600'
                    }`}>
                      {userMetrics.userRetentionRate.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* 產品使用指標 */}
      {productMetrics && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Globe className="w-5 h-5 mr-2" />
            產品使用指標
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <MetricCard
              title="TTS請求總數"
              value={productMetrics.totalTTSRequests.toLocaleString()}
              icon={<Zap className="w-6 h-6 text-white" />}
              color="bg-blue-500"
            />
            <MetricCard
              title="成功率"
              value={`${productMetrics.successRate.toFixed(1)}%`}
              icon={<CheckCircle className="w-6 h-6 text-white" />}
              color="bg-green-500"
            />
            <MetricCard
              title="平均處理時間"
              value={`${productMetrics.averageProcessingTime}ms`}
              icon={<Clock className="w-6 h-6 text-white" />}
              color="bg-orange-500"
            />
            <MetricCard
              title="客戶滿意度"
              value={`${productMetrics.customerSatisfactionScore.toFixed(1)}/5`}
              icon={<Star className="w-6 h-6 text-white" />}
              color="bg-yellow-500"
            />
          </div>
          
          {/* 熱門分析師排行 */}
          <Card>
            <CardHeader>
              <CardTitle>熱門語音分析師</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {productMetrics.popularAnalysts.slice(0, 5).map((analyst, index) => (
                  <div key={analyst.name} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Badge variant="outline" className="mr-2">#{index + 1}</Badge>
                      <span>{analyst.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{analyst.usage.toLocaleString()} 次使用</div>
                      <div className="text-sm text-gray-600">NT${analyst.revenue.toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 營銷指標 */}
      {marketingMetrics && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2" />
            營銷指標
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <MetricCard
              title="廣告投報率"
              value={`${marketingMetrics.roas.toFixed(1)}x`}
              icon={<TrendingUp className="w-6 h-6 text-white" />}
              color="bg-green-500"
              subtitle="ROAS"
            />
            <MetricCard
              title="獲客成本"
              value={`NT$${marketingMetrics.cac.toLocaleString()}`}
              icon={<Users className="w-6 h-6 text-white" />}
              color="bg-blue-500"
              subtitle="CAC"
            />
            <MetricCard
              title="LTV/CAC比率"
              value={`${marketingMetrics.ltv_cac_ratio.toFixed(1)}:1`}
              icon={<Award className="w-6 h-6 text-white" />}
              color="bg-purple-500"
            />
            <MetricCard
              title="活躍廣告"
              value={`${marketingMetrics.activeCampaigns}/${marketingMetrics.totalCampaigns}`}
              icon={<Activity className="w-6 h-6 text-white" />}
              color="bg-orange-500"
            />
          </div>
        </div>
      )}

      {/* 業務目標追蹤 */}
      {goals.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              業務目標追蹤
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {goals.slice(0, 5).map(goal => (
                <div key={goal.id} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-medium">{goal.description}</h4>
                      <p className="text-sm text-gray-600">
                        {goal.category} • 截止: {new Date(goal.deadline).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge variant={
                      goal.status === 'completed' ? 'default' :
                      goal.status === 'on_track' ? 'secondary' :
                      goal.status === 'at_risk' ? 'destructive' : 'outline'
                    }>
                      {goal.status === 'completed' ? '已完成' :
                       goal.status === 'on_track' ? '正常' :
                       goal.status === 'at_risk' ? '有風險' : '落後'}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Progress value={goal.progress} className="flex-1" />
                    <span className="text-sm text-gray-600">
                      {goal.current.toLocaleString()} / {goal.target.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CommercializationDashboard;
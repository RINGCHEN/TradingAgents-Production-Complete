/**
 * 會員AI功能管理模組
 * 天工 (TianGong) - 方案A混合架構會員AI系統管理界面
 * 
 * 功能：
 * 1. 會員等級AI功能展示和管理
 * 2. AI演示會話監控和管理
 * 3. 會員權益分級設置
 * 4. AI使用量統計和分析
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Alert, AlertDescription } from '../../components/ui/alert';
import MemberAIFeatures from '../../components/MemberAI/MemberAIFeatures';
import MembershipComparison from '../../components/MemberAI/MembershipComparison';
import { 
  Brain, 
  Users, 
  Crown, 
  Diamond,
  BarChart3,
  Settings,
  Monitor,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Play,
  Pause,
  RefreshCw,
  Download
} from 'lucide-react';

// 類型定義
interface AIUsageStats {
  total_demos: number;
  active_demos: number;
  completed_demos: number;
  failed_demos: number;
  by_tier: {
    FREE: number;
    GOLD: number;
    DIAMOND: number;
  };
  by_analyst: {
    [key: string]: number;
  };
}

interface DemoSession {
  request_id: string;
  user_id: string;
  user_tier: string;
  stock_symbol: string;
  status: string;
  analysts_used: string[];
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
}

interface TierConfig {
  tier: string;
  name: string;
  monthly_price: number;
  yearly_price: number;
  available_analysts: number;
  daily_limit: number;
  concurrent_demos: number;
  is_active: boolean;
}

const MemberAIManagementModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [usageStats, setUsageStats] = useState<AIUsageStats | null>(null);
  const [activeSessions, setActiveSessions] = useState<DemoSession[]>([]);
  const [tierConfigs, setTierConfigs] = useState<TierConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // 載入初始數據
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadUsageStats(),
        loadActiveSessions(),
        loadTierConfigs()
      ]);
    } catch (error) {
      console.error('載入初始數據失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsageStats = async () => {
    try {
      // 模擬API調用 - 實際應該調用後端API
      const mockStats: AIUsageStats = {
        total_demos: 1247,
        active_demos: 23,
        completed_demos: 1198,
        failed_demos: 26,
        by_tier: {
          FREE: 892,
          GOLD: 287,
          DIAMOND: 68
        },
        by_analyst: {
          technical_analyst: 856,
          fundamentals_analyst: 234,
          news_analyst: 157,
          social_media_analyst: 145,
          risk_analyst: 43,
          investment_planner: 31
        }
      };
      setUsageStats(mockStats);
    } catch (error) {
      console.error('載入使用統計失敗:', error);
    }
  };

  const loadActiveSessions = async () => {
    try {
      // 模擬活躍會話數據
      const mockSessions: DemoSession[] = [
        {
          request_id: 'demo_user123_2330TW_1693737600',
          user_id: 'user123',
          user_tier: 'GOLD',
          stock_symbol: '2330.TW',
          status: 'running',
          analysts_used: ['technical_analyst', 'fundamentals_analyst'],
          start_time: new Date(Date.now() - 120000).toISOString()
        },
        {
          request_id: 'demo_user456_2317TW_1693737500',
          user_id: 'user456',
          user_tier: 'DIAMOND',
          stock_symbol: '2317.TW',
          status: 'running',
          analysts_used: ['technical_analyst', 'fundamentals_analyst', 'risk_analyst'],
          start_time: new Date(Date.now() - 300000).toISOString()
        },
        {
          request_id: 'demo_user789_2454TW_1693737400',
          user_id: 'user789',
          user_tier: 'FREE',
          stock_symbol: '2454.TW',
          status: 'completed',
          analysts_used: ['technical_analyst'],
          start_time: new Date(Date.now() - 600000).toISOString(),
          end_time: new Date(Date.now() - 480000).toISOString(),
          duration_seconds: 120
        }
      ];
      setActiveSessions(mockSessions);
    } catch (error) {
      console.error('載入活躍會話失敗:', error);
    }
  };

  const loadTierConfigs = async () => {
    try {
      const mockConfigs: TierConfig[] = [
        {
          tier: 'FREE',
          name: '免費會員',
          monthly_price: 0,
          yearly_price: 0,
          available_analysts: 1,
          daily_limit: 5,
          concurrent_demos: 1,
          is_active: true
        },
        {
          tier: 'GOLD',
          name: '黃金會員',
          monthly_price: 1999,
          yearly_price: 19990,
          available_analysts: 4,
          daily_limit: 50,
          concurrent_demos: 2,
          is_active: true
        },
        {
          tier: 'DIAMOND',
          name: '鑽石會員',
          monthly_price: 4999,
          yearly_price: 49990,
          available_analysts: 6,
          daily_limit: -1,
          concurrent_demos: 5,
          is_active: true
        }
      ];
      setTierConfigs(mockConfigs);
    } catch (error) {
      console.error('載入會員等級配置失敗:', error);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadInitialData();
    setRefreshing(false);
  };

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
      FREE: 'text-gray-600',
      GOLD: 'text-yellow-600',
      DIAMOND: 'text-purple-600'
    };
    return colors[tier as keyof typeof colors] || colors.FREE;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };
    return colors[status as keyof typeof colors] || colors.pending;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const exportUsageReport = () => {
    // 實現使用量報告導出功能
    console.log('導出使用量報告');
    alert('使用量報告導出功能開發中...');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">載入會員AI管理數據中...</span>
      </div>
    );
  }

  return (
    <div className="member-ai-management-module space-y-6">
      {/* 頁面標題和操作 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold">會員AI功能管理</h1>
            <p className="text-gray-600">管理會員AI分析功能和使用統計</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button 
            variant="outline" 
            onClick={refreshData}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            刷新數據
          </Button>
          <Button onClick={exportUsageReport}>
            <Download className="h-4 w-4 mr-2" />
            導出報告
          </Button>
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="tabs-container">
        <div className="flex border-b mb-6">
          {['overview', 'sessions', 'tier-management', 'analytics', 'settings'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 mx-2 border-b-2 transition-colors ${
                activeTab === tab 
                  ? 'border-blue-500 text-blue-600 font-medium' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'overview' && '總覽'}
              {tab === 'sessions' && '演示會話'}
              {tab === 'tier-management' && '等級管理'}
              {tab === 'analytics' && '分析統計'}
              {tab === 'settings' && '系統設置'}
            </button>
          ))}
        </div>

        {/* 總覽頁面 */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* 統計卡片 */}
          {usageStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">總演示次數</p>
                      <p className="text-2xl font-bold">{usageStats.total_demos}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">進行中會話</p>
                      <p className="text-2xl font-bold text-blue-600">{usageStats.active_demos}</p>
                    </div>
                    <Play className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">完成率</p>
                      <p className="text-2xl font-bold text-green-600">
                        {Math.round((usageStats.completed_demos / usageStats.total_demos) * 100)}%
                      </p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">失敗次數</p>
                      <p className="text-2xl font-bold text-red-600">{usageStats.failed_demos}</p>
                    </div>
                    <AlertCircle className="h-8 w-8 text-red-600" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 會員等級分布 */}
          {usageStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>會員等級使用分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(usageStats.by_tier).map(([tier, count]) => {
                      const TierIcon = getTierIcon(tier);
                      const percentage = Math.round((count / usageStats.total_demos) * 100);
                      
                      return (
                        <div key={tier} className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <TierIcon className={`h-5 w-5 ${getTierColor(tier)}`} />
                            <span>{tier} 會員</span>
                          </div>
                          <div className="flex items-center space-x-3">
                            <div className="w-24 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full" 
                                style={{ width: `${percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-medium w-16 text-right">
                              {count} ({percentage}%)
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>分析師使用統計</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(usageStats.by_analyst).map(([analyst, count]) => {
                      const percentage = Math.round((count / usageStats.total_demos) * 100);
                      
                      return (
                        <div key={analyst} className="flex items-center justify-between">
                          <span className="text-sm">{analyst.replace('_', ' ')}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-20 bg-gray-200 rounded-full h-1.5">
                              <div 
                                className="bg-green-600 h-1.5 rounded-full" 
                                style={{ width: `${percentage}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-gray-600 w-10 text-right">{count}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 系統狀態警告 */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>系統狀態：</strong>方案A混合架構運行中。AI演示功能使用本地模型，
              會員權限通過雲端系統驗證。完整雲端部署預計2-4週內完成。
            </AlertDescription>
          </Alert>
        )}

        {/* 演示會話管理 */}
        {activeTab === 'sessions' && (
          <div className="space-y-6">
            <Card>
            <CardHeader>
              <CardTitle>活躍演示會話</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activeSessions.map((session) => {
                  const TierIcon = getTierIcon(session.user_tier);
                  
                  return (
                    <div key={session.request_id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <TierIcon className={`h-5 w-5 ${getTierColor(session.user_tier)}`} />
                          <span className="font-medium">{session.user_id}</span>
                          <Badge className={getStatusColor(session.status)}>
                            {session.status}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <Clock className="h-4 w-4" />
                          <span>{formatDuration(session.duration_seconds)}</span>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">股票代碼:</span>
                          <span className="ml-2 font-medium">{session.stock_symbol}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">分析師:</span>
                          <span className="ml-2">{session.analysts_used.length}位</span>
                        </div>
                        <div>
                          <span className="text-gray-600">開始時間:</span>
                          <span className="ml-2">
                            {new Date(session.start_time).toLocaleString('zh-TW')}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 等級管理 */}
        {activeTab === 'tier-management' && (
          <div className="space-y-6">
            <MembershipComparison currentTier="GOLD" />
          </div>
        )}

        {/* 分析統計 */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <MemberAIFeatures userTier="GOLD" userId="admin" />
              <MemberAIFeatures userTier="DIAMOND" userId="admin" />
            </div>
          </div>
        )}

        {/* 系統設置 */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>AI演示系統設置</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">最大並發演示數量</label>
                  <input 
                    type="number" 
                    defaultValue={3} 
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">演示超時時間 (分鐘)</label>
                  <input 
                    type="number" 
                    defaultValue={5} 
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">清理過期會話間隔 (小時)</label>
                  <input 
                    type="number" 
                    defaultValue={24} 
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">使用實時數據</label>
                  <select className="w-full p-2 border border-gray-300 rounded-md">
                    <option value="true">啟用</option>
                    <option value="false">停用</option>
                  </select>
                </div>
              </div>
              
              <div className="pt-4">
                <Button>保存設置</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MemberAIManagementModule;
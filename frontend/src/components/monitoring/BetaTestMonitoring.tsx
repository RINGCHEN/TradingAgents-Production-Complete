/**
 * TTS Beta測試監控系統
 * 實時監控測試進度、系統性能和用戶活動
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Activity, 
  Users, 
  Clock, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  BarChart3,
  RefreshCw,
  Download,
  Settings,
  Play,
  Pause,
  UserCheck,
  Zap,
  Globe,
  Database
} from 'lucide-react';

// 測試階段定義
interface TestingPhase {
  id: string;
  name: string;
  status: 'upcoming' | 'active' | 'completed' | 'paused';
  startDate: Date;
  endDate: Date;
  targetUsers: number;
  actualUsers: number;
  progress: number;
  objectives: string[];
  successCriteria: Record<string, number>;
}

// 用戶活動指標
interface UserActivity {
  totalUsers: number;
  activeUsers: number;
  newSignups: number;
  retentionRate: number;
  averageSessionTime: number;
  bounceRate: number;
  conversionRate: number;
}

// 系統性能指標
interface SystemMetrics {
  apiResponseTime: number;
  ttsProcessingTime: number;
  errorRate: number;
  uptime: number;
  cpuUsage: number;
  memoryUsage: number;
  storageUsage: number;
  concurrentUsers: number;
  requestsPerSecond: number;
}

// TTS使用統計
interface TTSUsageStats {
  totalRequests: number;
  successfulSynthesis: number;
  failedRequests: number;
  averageCharacterLength: number;
  popularVoices: Array<{
    voiceId: string;
    voiceName: string;
    usage: number;
  }>;
  popularAnalysts: Array<{
    analystId: string;
    analystName: string;
    usage: number;
  }>;
  peakUsageHours: Array<{
    hour: number;
    requests: number;
  }>;
}

// 測試報告
interface TestReport {
  phase: string;
  totalFeedbacks: number;
  averageRating: number;
  criticalIssues: number;
  resolvedIssues: number;
  keyInsights: string[];
  recommendedActions: string[];
  nextMilestones: string[];
}

const BetaTestMonitoring: React.FC = () => {
  const [currentPhase, setCurrentPhase] = useState<TestingPhase | null>(null);
  const [allPhases, setAllPhases] = useState<TestingPhase[]>([]);
  const [userActivity, setUserActivity] = useState<UserActivity | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [ttsStats, setTTSStats] = useState<TTSUsageStats | null>(null);
  const [testReport, setTestReport] = useState<TestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // 秒

  // 載入監控數據
  const loadMonitoringData = useCallback(async () => {
    setLoading(true);
    try {
      // 同時請求所有監控數據
      const [phasesRes, activityRes, metricsRes, ttsRes, reportRes] = await Promise.all([
        fetch('/api/beta-test/phases'),
        fetch('/api/beta-test/user-activity'),
        fetch('/api/beta-test/system-metrics'),
        fetch('/api/beta-test/tts-usage'),
        fetch('/api/beta-test/report')
      ]);

      if (phasesRes.ok) {
        const phases = await phasesRes.json();
        setAllPhases(phases);
        setCurrentPhase(phases.find((p: TestingPhase) => p.status === 'active') || null);
      }

      if (activityRes.ok) {
        const activity = await activityRes.json();
        setUserActivity(activity);
      }

      if (metricsRes.ok) {
        const metrics = await metricsRes.json();
        setSystemMetrics(metrics);
      }

      if (ttsRes.ok) {
        const tts = await ttsRes.json();
        setTTSStats(tts);
      }

      if (reportRes.ok) {
        const report = await reportRes.json();
        setTestReport(report);
      }
    } catch (error) {
      console.error('載入監控數據失敗:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 自動刷新機制
  useEffect(() => {
    loadMonitoringData();
    
    if (autoRefresh) {
      const interval = setInterval(loadMonitoringData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [loadMonitoringData, autoRefresh, refreshInterval]);

  // 階段控制操作
  const handlePhaseControl = async (action: 'start' | 'pause' | 'complete', phaseId: string) => {
    try {
      const response = await fetch(`/api/beta-test/phases/${phaseId}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        loadMonitoringData();
        alert(`階段${action === 'start' ? '開始' : action === 'pause' ? '暫停' : '完成'}成功`);
      }
    } catch (error) {
      console.error('階段控制操作失敗:', error);
    }
  };

  // 導出監控報告
  const exportReport = async () => {
    try {
      const response = await fetch('/api/beta-test/export-report', {
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
        a.download = `beta-test-report-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('導出報告失敗:', error);
    }
  };

  // 階段進度條
  const PhaseProgressBar: React.FC<{ phase: TestingPhase }> = ({ phase }) => (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full transition-all duration-500 ${
          phase.status === 'completed' ? 'bg-green-500' :
          phase.status === 'active' ? 'bg-blue-500' :
          phase.status === 'paused' ? 'bg-yellow-500' : 
          'bg-gray-400'
        }`}
        style={{ width: `${phase.progress}%` }}
      />
    </div>
  );

  // 指標卡片
  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color: string;
  }> = ({ title, value, change, icon, color }) => (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {change !== undefined && (
              <p className={`text-sm flex items-center ${
                change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                <TrendingUp className="w-3 h-3 mr-1" />
                {change >= 0 ? '+' : ''}{change.toFixed(1)}%
              </p>
            )}
          </div>
          <div className={`p-3 rounded-full ${color}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* 頁面標題和控制 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">TTS Beta測試監控中心</h1>
          <p className="text-gray-600">實時監控測試進度和系統狀態</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">
              自動刷新: {refreshInterval}秒
            </span>
            <Button
              variant={autoRefresh ? "default" : "outline"}
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
          </div>
          
          <Button onClick={loadMonitoringData} disabled={loading} size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          
          <Button onClick={exportReport} size="sm">
            <Download className="w-4 h-4 mr-2" />
            導出報告
          </Button>
        </div>
      </div>

      {/* 當前測試階段概覽 */}
      {currentPhase && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                當前測試階段: {currentPhase.name}
              </CardTitle>
              <Badge variant={
                currentPhase.status === 'active' ? 'default' :
                currentPhase.status === 'completed' ? 'secondary' :
                currentPhase.status === 'paused' ? 'destructive' : 'outline'
              }>
                {currentPhase.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-medium mb-2">進度概覽</h4>
                <PhaseProgressBar phase={currentPhase} />
                <div className="flex justify-between text-sm text-gray-600 mt-1">
                  <span>進度: {currentPhase.progress}%</span>
                  <span>用戶: {currentPhase.actualUsers}/{currentPhase.targetUsers}</span>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">測試目標</h4>
                <ul className="text-sm text-gray-600">
                  {currentPhase.objectives.slice(0, 3).map((obj, index) => (
                    <li key={index} className="flex items-center mb-1">
                      <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
                      {obj}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">階段控制</h4>
                <div className="flex space-x-2">
                  {currentPhase.status === 'active' && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handlePhaseControl('pause', currentPhase.id)}
                    >
                      <Pause className="w-4 h-4 mr-1" />
                      暫停
                    </Button>
                  )}
                  {currentPhase.status === 'paused' && (
                    <Button 
                      size="sm"
                      onClick={() => handlePhaseControl('start', currentPhase.id)}
                    >
                      <Play className="w-4 h-4 mr-1" />
                      繼續
                    </Button>
                  )}
                  <Button 
                    size="sm" 
                    variant="default"
                    onClick={() => handlePhaseControl('complete', currentPhase.id)}
                  >
                    <CheckCircle className="w-4 h-4 mr-1" />
                    完成階段
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 關鍵指標概覽 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {userActivity && (
          <>
            <MetricCard
              title="活躍用戶"
              value={userActivity.activeUsers}
              change={15.2}
              icon={<Users className="w-6 h-6 text-white" />}
              color="bg-blue-500"
            />
            <MetricCard
              title="新註冊用戶"
              value={userActivity.newSignups}
              change={8.7}
              icon={<UserCheck className="w-6 h-6 text-white" />}
              color="bg-green-500"
            />
            <MetricCard
              title="留存率"
              value={`${userActivity.retentionRate.toFixed(1)}%`}
              change={12.3}
              icon={<TrendingUp className="w-6 h-6 text-white" />}
              color="bg-purple-500"
            />
            <MetricCard
              title="轉換率"
              value={`${userActivity.conversionRate.toFixed(1)}%`}
              change={-2.1}
              icon={<Zap className="w-6 h-6 text-white" />}
              color="bg-orange-500"
            />
          </>
        )}
      </div>

      {/* 詳細監控面板 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 系統性能監控 */}
        {systemMetrics && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                系統性能監控
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>API響應時間</span>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${Math.min(systemMetrics.apiResponseTime / 1000 * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm">{systemMetrics.apiResponseTime}ms</span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span>TTS處理時間</span>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.min(systemMetrics.ttsProcessingTime / 5000 * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm">{systemMetrics.ttsProcessingTime}ms</span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span>錯誤率</span>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full"
                        style={{ width: `${systemMetrics.errorRate}%` }}
                      />
                    </div>
                    <span className="text-sm">{systemMetrics.errorRate.toFixed(2)}%</span>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span>系統正常運行時間</span>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${systemMetrics.uptime}%` }}
                      />
                    </div>
                    <span className="text-sm">{systemMetrics.uptime.toFixed(2)}%</span>
                  </div>
                </div>
                
                <div className="pt-2 border-t">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">併發用戶:</span>
                      <span className="ml-2 font-medium">{systemMetrics.concurrentUsers}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">請求/秒:</span>
                      <span className="ml-2 font-medium">{systemMetrics.requestsPerSecond}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* TTS使用統計 */}
        {ttsStats && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="w-5 h-5 mr-2" />
                TTS使用統計
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">總請求數</p>
                    <p className="text-xl font-bold">{ttsStats.totalRequests.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">成功率</p>
                    <p className="text-xl font-bold">
                      {((ttsStats.successfulSynthesis / ttsStats.totalRequests) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">熱門語音</h4>
                  <div className="space-y-2">
                    {ttsStats.popularVoices.slice(0, 3).map(voice => (
                      <div key={voice.voiceId} className="flex justify-between items-center">
                        <span className="text-sm">{voice.voiceName}</span>
                        <Badge variant="secondary">{voice.usage}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">熱門分析師</h4>
                  <div className="space-y-2">
                    {ttsStats.popularAnalysts.slice(0, 3).map(analyst => (
                      <div key={analyst.analystId} className="flex justify-between items-center">
                        <span className="text-sm">{analyst.analystName}</span>
                        <Badge variant="outline">{analyst.usage}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 測試階段概覽 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="w-5 h-5 mr-2" />
            測試階段概覽
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {allPhases.map(phase => (
              <div key={phase.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">{phase.name}</h4>
                  <Badge variant={
                    phase.status === 'active' ? 'default' :
                    phase.status === 'completed' ? 'secondary' :
                    phase.status === 'paused' ? 'destructive' : 'outline'
                  }>
                    {phase.status}
                  </Badge>
                </div>
                <PhaseProgressBar phase={phase} />
                <div className="flex justify-between text-sm text-gray-600 mt-1">
                  <span>{phase.startDate.toLocaleDateString()} - {phase.endDate.toLocaleDateString()}</span>
                  <span>用戶: {phase.actualUsers}/{phase.targetUsers}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 測試報告摘要 */}
      {testReport && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="w-5 h-5 mr-2" />
              測試報告摘要
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">關鍵數據</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>總反饋數</span>
                    <span className="font-medium">{testReport.totalFeedbacks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均評分</span>
                    <span className="font-medium">{testReport.averageRating.toFixed(1)}/5</span>
                  </div>
                  <div className="flex justify-between">
                    <span>嚴重問題</span>
                    <span className="font-medium text-red-600">{testReport.criticalIssues}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>已解決問題</span>
                    <span className="font-medium text-green-600">{testReport.resolvedIssues}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">關鍵洞察</h4>
                <ul className="space-y-1">
                  {testReport.keyInsights.slice(0, 4).map((insight, index) => (
                    <li key={index} className="flex items-start text-sm">
                      <CheckCircle className="w-3 h-3 mr-2 text-green-500 mt-0.5 flex-shrink-0" />
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BetaTestMonitoring;
/**
 * TTS Beta測試用戶反饋收集系統
 * 企業級反饋收集、分析和管理組件
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Star, 
  Send, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  Filter,
  Download,
  Search
} from 'lucide-react';

// 反饋類型定義
interface UserFeedback {
  id: string;
  userId: string;
  userEmail: string;
  testingPhase: 'alpha' | 'closed-beta' | 'public-beta';
  feedbackType: 'bug' | 'feature' | 'improvement' | 'complaint' | 'praise';
  category: 'voice-quality' | 'ui-ux' | 'performance' | 'functionality' | 'pricing' | 'other';
  
  // 評分系統 (1-5)
  overallRating: number;
  voiceQualityRating: number;
  easeOfUseRating: number;
  featureCompletenessRating: number;
  performanceRating: number;
  
  // 反饋內容
  title: string;
  description: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  stepsToReproduce?: string;
  
  // 系統資訊
  browserInfo: string;
  deviceInfo: string;
  voiceModelUsed?: string;
  analystUsed?: string;
  sessionId?: string;
  
  // 處理狀態
  status: 'new' | 'reviewing' | 'in-progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignedTo?: string;
  
  // 時間戳記
  submittedAt: Date;
  updatedAt: Date;
  resolvedAt?: Date;
  
  // 附加資訊
  screenshots?: string[];
  audioSamples?: string[];
  tags: string[];
  internalNotes?: string;
}

interface FeedbackStats {
  totalFeedbacks: number;
  averageRating: number;
  ratingDistribution: Record<number, number>;
  categoryDistribution: Record<string, number>;
  statusDistribution: Record<string, number>;
  phaseDistribution: Record<string, number>;
  trendData: Array<{
    date: string;
    count: number;
    rating: number;
  }>;
}

const FeedbackCollectionSystem: React.FC = () => {
  const [feedbacks, setFeedbacks] = useState<UserFeedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'manage' | 'analytics'>('submit');
  const [filters, setFilters] = useState({
    phase: '',
    category: '',
    status: '',
    rating: ''
  });
  
  // 新反饋表單狀態
  const [newFeedback, setNewFeedback] = useState({
    feedbackType: 'improvement' as const,
    category: 'voice-quality' as const,
    title: '',
    description: '',
    overallRating: 5,
    voiceQualityRating: 5,
    easeOfUseRating: 5,
    featureCompletenessRating: 5,
    performanceRating: 5
  });

  // 載入反饋數據
  const loadFeedbacks = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/feedback/list', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data.feedbacks || []);
        setStats(data.stats);
      }
    } catch (error) {
      console.error('載入反饋失敗:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 提交新反饋
  const submitFeedback = async () => {
    try {
      setLoading(true);
      
      const feedbackData = {
        ...newFeedback,
        browserInfo: navigator.userAgent,
        deviceInfo: `${window.screen.width}x${window.screen.height}`,
        testingPhase: 'alpha', // 根據當前階段設定
        tags: [`phase-alpha`, `category-${newFeedback.category}`]
      };
      
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
      });
      
      if (response.ok) {
        alert('反饋提交成功！感謝您的寶貴意見。');
        setNewFeedback({
          feedbackType: 'improvement',
          category: 'voice-quality',
          title: '',
          description: '',
          overallRating: 5,
          voiceQualityRating: 5,
          easeOfUseRating: 5,
          featureCompletenessRating: 5,
          performanceRating: 5
        });
        loadFeedbacks();
      } else {
        alert('反饋提交失敗，請稍後再試。');
      }
    } catch (error) {
      console.error('提交反饋失敗:', error);
      alert('提交失敗，請檢查網路連接。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeedbacks();
  }, [loadFeedbacks]);

  // 評星組件
  const StarRating: React.FC<{ 
    value: number; 
    onChange: (value: number) => void;
    readonly?: boolean;
  }> = ({ value, onChange, readonly = false }) => (
    <div className="flex space-x-1">
      {[1, 2, 3, 4, 5].map(star => (
        <Star
          key={star}
          className={`w-5 h-5 cursor-pointer transition-colors ${
            star <= value 
              ? 'text-yellow-400 fill-yellow-400' 
              : 'text-gray-300'
          }`}
          onClick={() => !readonly && onChange(star)}
        />
      ))}
    </div>
  );

  // 反饋提交表單
  const renderSubmitForm = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageSquare className="w-5 h-5 mr-2" />
            提交測試反饋
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 基本資訊 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">反饋類型</label>
              <select 
                className="w-full border rounded-md p-2"
                value={newFeedback.feedbackType}
                onChange={(e) => setNewFeedback(prev => ({
                  ...prev, 
                  feedbackType: e.target.value as any
                }))}
              >
                <option value="bug">錯誤回報</option>
                <option value="feature">功能建議</option>
                <option value="improvement">改進建議</option>
                <option value="complaint">投訴</option>
                <option value="praise">讚揚</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">分類</label>
              <select 
                className="w-full border rounded-md p-2"
                value={newFeedback.category}
                onChange={(e) => setNewFeedback(prev => ({
                  ...prev, 
                  category: e.target.value as any
                }))}
              >
                <option value="voice-quality">語音品質</option>
                <option value="ui-ux">使用者界面</option>
                <option value="performance">性能表現</option>
                <option value="functionality">功能性</option>
                <option value="pricing">定價</option>
                <option value="other">其他</option>
              </select>
            </div>
          </div>
          
          {/* 標題和描述 */}
          <div>
            <label className="block text-sm font-medium mb-2">標題</label>
            <Input
              value={newFeedback.title}
              onChange={(e) => setNewFeedback(prev => ({
                ...prev, 
                title: e.target.value
              }))}
              placeholder="簡要描述您的反饋..."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">詳細描述</label>
            <Textarea
              value={newFeedback.description}
              onChange={(e) => setNewFeedback(prev => ({
                ...prev, 
                description: e.target.value
              }))}
              placeholder="請詳細描述您遇到的問題或建議..."
              rows={4}
            />
          </div>
          
          {/* 評分系統 */}
          <div className="space-y-3">
            <h4 className="font-medium">請為以下方面評分：</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex justify-between items-center">
                <span>整體滿意度</span>
                <StarRating 
                  value={newFeedback.overallRating}
                  onChange={(value) => setNewFeedback(prev => ({
                    ...prev, 
                    overallRating: value
                  }))}
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span>語音品質</span>
                <StarRating 
                  value={newFeedback.voiceQualityRating}
                  onChange={(value) => setNewFeedback(prev => ({
                    ...prev, 
                    voiceQualityRating: value
                  }))}
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span>易用性</span>
                <StarRating 
                  value={newFeedback.easeOfUseRating}
                  onChange={(value) => setNewFeedback(prev => ({
                    ...prev, 
                    easeOfUseRating: value
                  }))}
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span>功能完整性</span>
                <StarRating 
                  value={newFeedback.featureCompletenessRating}
                  onChange={(value) => setNewFeedback(prev => ({
                    ...prev, 
                    featureCompletenessRating: value
                  }))}
                />
              </div>
              
              <div className="flex justify-between items-center col-span-2">
                <span>性能表現</span>
                <StarRating 
                  value={newFeedback.performanceRating}
                  onChange={(value) => setNewFeedback(prev => ({
                    ...prev, 
                    performanceRating: value
                  }))}
                />
              </div>
            </div>
          </div>
          
          <Button 
            onClick={submitFeedback} 
            disabled={loading || !newFeedback.title || !newFeedback.description}
            className="w-full"
          >
            <Send className="w-4 h-4 mr-2" />
            提交反饋
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  // 反饋管理界面
  const renderManagement = () => (
    <div className="space-y-6">
      {/* 過濾器 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            反饋管理
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <select 
              className="border rounded-md p-2"
              value={filters.phase}
              onChange={(e) => setFilters(prev => ({...prev, phase: e.target.value}))}
            >
              <option value="">所有階段</option>
              <option value="alpha">Alpha測試</option>
              <option value="closed-beta">封閉Beta</option>
              <option value="public-beta">公開Beta</option>
            </select>
            
            <select 
              className="border rounded-md p-2"
              value={filters.category}
              onChange={(e) => setFilters(prev => ({...prev, category: e.target.value}))}
            >
              <option value="">所有分類</option>
              <option value="voice-quality">語音品質</option>
              <option value="ui-ux">使用者界面</option>
              <option value="performance">性能</option>
              <option value="functionality">功能</option>
              <option value="pricing">定價</option>
            </select>
            
            <select 
              className="border rounded-md p-2"
              value={filters.status}
              onChange={(e) => setFilters(prev => ({...prev, status: e.target.value}))}
            >
              <option value="">所有狀態</option>
              <option value="new">新建</option>
              <option value="reviewing">審核中</option>
              <option value="in-progress">處理中</option>
              <option value="resolved">已解決</option>
              <option value="closed">已關閉</option>
            </select>
            
            <Button className="flex items-center">
              <Download className="w-4 h-4 mr-2" />
              匯出數據
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 反饋列表 */}
      <div className="space-y-4">
        {feedbacks.map(feedback => (
          <Card key={feedback.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium">{feedback.title}</h4>
                  <p className="text-sm text-gray-600">
                    來自: {feedback.userEmail} | 
                    測試階段: {feedback.testingPhase} |
                    提交時間: {new Date(feedback.submittedAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={
                    feedback.status === 'resolved' ? 'default' :
                    feedback.status === 'in-progress' ? 'secondary' :
                    feedback.status === 'new' ? 'destructive' : 'outline'
                  }>
                    {feedback.status}
                  </Badge>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                    <span className="ml-1 text-sm">{feedback.overallRating}</span>
                  </div>
                </div>
              </div>
              
              <p className="text-sm mb-3">{feedback.description}</p>
              
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{feedback.category}</Badge>
                <Badge variant="outline">{feedback.feedbackType}</Badge>
                {feedback.tags.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  // 分析報表
  const renderAnalytics = () => (
    <div className="space-y-6">
      {stats && (
        <>
          {/* 總覽統計 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">總反饋數</p>
                    <p className="text-2xl font-bold">{stats.totalFeedbacks}</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">平均評分</p>
                    <p className="text-2xl font-bold">{stats.averageRating.toFixed(1)}</p>
                  </div>
                  <Star className="w-8 h-8 text-yellow-400" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">活躍用戶</p>
                    <p className="text-2xl font-bold">
                      {Object.keys(stats.phaseDistribution).length}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">解決率</p>
                    <p className="text-2xl font-bold">
                      {((stats.statusDistribution.resolved || 0) / stats.totalFeedbacks * 100).toFixed(1)}%
                    </p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* 詳細分析圖表 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>評分分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.ratingDistribution).map(([rating, count]) => (
                    <div key={rating} className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="w-8">{rating}星</span>
                        <div className="ml-2 bg-gray-200 rounded-full h-2 w-32">
                          <div 
                            className="bg-blue-500 h-2 rounded-full"
                            style={{width: `${(count / stats.totalFeedbacks) * 100}%`}}
                          />
                        </div>
                      </div>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>分類分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.categoryDistribution).map(([category, count]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="capitalize">{category}</span>
                      <div className="flex items-center">
                        <div className="ml-2 bg-gray-200 rounded-full h-2 w-32">
                          <div 
                            className="bg-green-500 h-2 rounded-full"
                            style={{width: `${(count / stats.totalFeedbacks) * 100}%`}}
                          />
                        </div>
                        <span className="ml-2 text-sm text-gray-600">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">TTS Beta測試反饋系統</h1>
        <p className="text-gray-600">收集、管理和分析用戶反饋，持續改進產品質量</p>
      </div>

      {/* 標籤頁導航 */}
      <div className="flex space-x-1 mb-6 border-b">
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'submit'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('submit')}
        >
          提交反饋
        </button>
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'manage'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('manage')}
        >
          反饋管理
        </button>
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'analytics'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('analytics')}
        >
          數據分析
        </button>
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
          {activeTab === 'submit' && renderSubmitForm()}
          {activeTab === 'manage' && renderManagement()}
          {activeTab === 'analytics' && renderAnalytics()}
        </>
      )}
    </div>
  );
};

export default FeedbackCollectionSystem;
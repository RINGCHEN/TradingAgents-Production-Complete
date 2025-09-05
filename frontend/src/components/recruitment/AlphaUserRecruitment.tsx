/**
 * Alpha測試用戶招募系統
 * 目標招募系統，篩選優質測試用戶
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  UserPlus, 
  Mail, 
  Phone, 
  Briefcase, 
  Star,
  CheckCircle,
  Clock,
  Users,
  Target,
  TrendingUp,
  Filter,
  Send,
  UserCheck,
  Award,
  MessageSquare,
  Calendar
} from 'lucide-react';

// 用戶申請定義
interface AlphaUserApplication {
  id: string;
  email: string;
  name: string;
  phoneNumber?: string;
  company?: string;
  jobTitle?: string;
  tradingExperience: 'beginner' | 'intermediate' | 'advanced' | 'professional';
  ttsInterest: number; // 1-5
  availableTime: string;
  
  // 背景資訊
  tradingFrequency: 'daily' | 'weekly' | 'monthly' | 'occasionally';
  preferredAnalysts: string[];
  deviceTypes: string[];
  testingExperience: string;
  
  // 動機和期望
  motivation: string;
  expectations: string;
  feedbackCommitment: boolean;
  
  // 篩選分數
  qualityScore: number;
  priority: 'high' | 'medium' | 'low';
  
  // 處理狀態
  status: 'pending' | 'reviewing' | 'approved' | 'rejected' | 'waitlist';
  reviewedBy?: string;
  reviewNotes?: string;
  
  // 測試計劃
  assignedGroup?: 'A' | 'B' | 'C';
  testingSchedule?: string;
  specialInstructions?: string;
  
  submittedAt: Date;
  reviewedAt?: Date;
  approvedAt?: Date;
}

interface RecruitmentStats {
  totalApplications: number;
  pendingReviews: number;
  approvedUsers: number;
  rejectedUsers: number;
  waitlistUsers: number;
  targetReached: boolean;
  qualityDistribution: Record<string, number>;
  experienceDistribution: Record<string, number>;
}

const AlphaUserRecruitment: React.FC = () => {
  const [applications, setApplications] = useState<AlphaUserApplication[]>([]);
  const [stats, setStats] = useState<RecruitmentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'apply' | 'manage' | 'approved'>('apply');
  const [filters, setFilters] = useState({
    status: '',
    experience: '',
    priority: ''
  });
  
  // 申請表單狀態
  const [applicationForm, setApplicationForm] = useState({
    name: '',
    email: '',
    phoneNumber: '',
    company: '',
    jobTitle: '',
    tradingExperience: 'intermediate' as const,
    tradingFrequency: 'weekly' as const,
    ttsInterest: 5,
    availableTime: '',
    preferredAnalysts: [] as string[],
    deviceTypes: [] as string[],
    testingExperience: '',
    motivation: '',
    expectations: '',
    feedbackCommitment: false
  });

  // 載入申請數據
  const loadApplications = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/alpha-recruitment/applications', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setApplications(data.applications || []);
        setStats(data.stats);
      }
    } catch (error) {
      console.error('載入申請數據失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 提交申請
  const submitApplication = async () => {
    if (!applicationForm.name || !applicationForm.email || !applicationForm.motivation) {
      alert('請填寫必要資訊');
      return;
    }
    
    try {
      setLoading(true);
      const response = await fetch('/api/alpha-recruitment/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(applicationForm)
      });
      
      if (response.ok) {
        alert('申請提交成功！我們會在3個工作日內聯繫您。');
        setApplicationForm({
          name: '',
          email: '',
          phoneNumber: '',
          company: '',
          jobTitle: '',
          tradingExperience: 'intermediate',
          tradingFrequency: 'weekly',
          ttsInterest: 5,
          availableTime: '',
          preferredAnalysts: [],
          deviceTypes: [],
          testingExperience: '',
          motivation: '',
          expectations: '',
          feedbackCommitment: false
        });
        loadApplications();
      } else {
        const error = await response.text();
        alert(`申請失敗: ${error}`);
      }
    } catch (error) {
      console.error('提交申請失敗:', error);
      alert('提交失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 審核申請
  const reviewApplication = async (
    applicationId: string, 
    status: 'approved' | 'rejected' | 'waitlist',
    notes?: string
  ) => {
    try {
      const response = await fetch(`/api/alpha-recruitment/review/${applicationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, notes })
      });
      
      if (response.ok) {
        loadApplications();
        alert(`申請已${status === 'approved' ? '通過' : status === 'rejected' ? '拒絕' : '加入候補名單'}`);
      }
    } catch (error) {
      console.error('審核申請失敗:', error);
    }
  };

  // 發送歡迎郵件
  const sendWelcomeEmail = async (applicationId: string) => {
    try {
      const response = await fetch(`/api/alpha-recruitment/welcome-email/${applicationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (response.ok) {
        alert('歡迎郵件已發送');
      }
    } catch (error) {
      console.error('發送歡迎郵件失敗:', error);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

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

  // 申請表單
  const renderApplicationForm = () => (
    <div className="max-w-3xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <UserPlus className="w-5 h-5 mr-2" />
            TTS Alpha測試申請
          </CardTitle>
          <p className="text-gray-600">
            成為我們的Alpha測試用戶，優先體驗革新的語音分析師功能，並享有獨家優惠！
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 基本資訊 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">姓名 *</label>
              <Input
                value={applicationForm.name}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, name: e.target.value
                }))}
                placeholder="請輸入您的姓名"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">電子郵件 *</label>
              <Input
                type="email"
                value={applicationForm.email}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, email: e.target.value
                }))}
                placeholder="your@email.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">聯繫電話</label>
              <Input
                value={applicationForm.phoneNumber}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, phoneNumber: e.target.value
                }))}
                placeholder="0912345678"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">公司/機構</label>
              <Input
                value={applicationForm.company}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, company: e.target.value
                }))}
                placeholder="您的工作單位"
              />
            </div>
          </div>

          {/* 投資經驗 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">投資經驗</label>
              <select 
                className="w-full border rounded-md p-2"
                value={applicationForm.tradingExperience}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, tradingExperience: e.target.value as any
                }))}
              >
                <option value="beginner">初學者 (1年以下)</option>
                <option value="intermediate">中級投資者 (1-3年)</option>
                <option value="advanced">高級投資者 (3-5年)</option>
                <option value="professional">專業投資者 (5年以上)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">交易頻率</label>
              <select 
                className="w-full border rounded-md p-2"
                value={applicationForm.tradingFrequency}
                onChange={(e) => setApplicationForm(prev => ({
                  ...prev, tradingFrequency: e.target.value as any
                }))}
              >
                <option value="daily">每日交易</option>
                <option value="weekly">每週交易</option>
                <option value="monthly">每月交易</option>
                <option value="occasionally">偶爾交易</option>
              </select>
            </div>
          </div>

          {/* TTS興趣度 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              對語音分析師功能的興趣程度
            </label>
            <div className="flex items-center space-x-3">
              <StarRating 
                value={applicationForm.ttsInterest}
                onChange={(value) => setApplicationForm(prev => ({
                  ...prev, ttsInterest: value
                }))}
              />
              <span className="text-sm text-gray-600">
                {applicationForm.ttsInterest}/5
              </span>
            </div>
          </div>

          {/* 偏好分析師 */}
          <div>
            <label className="block text-sm font-medium mb-2">感興趣的分析師類型 (可多選)</label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[
                '基本面分析師', '新聞分析師', '風險管理師', 
                '情感分析師', '投資規劃師', '台股專家'
              ].map(analyst => (
                <label key={analyst} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={applicationForm.preferredAnalysts.includes(analyst)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setApplicationForm(prev => ({
                          ...prev,
                          preferredAnalysts: [...prev.preferredAnalysts, analyst]
                        }));
                      } else {
                        setApplicationForm(prev => ({
                          ...prev,
                          preferredAnalysts: prev.preferredAnalysts.filter(a => a !== analyst)
                        }));
                      }
                    }}
                    className="mr-2"
                  />
                  {analyst}
                </label>
              ))}
            </div>
          </div>

          {/* 使用設備 */}
          <div>
            <label className="block text-sm font-medium mb-2">主要使用設備 (可多選)</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {['桌面電腦', '筆記型電腦', 'iPhone', 'Android手機', 'iPad', 'Android平板'].map(device => (
                <label key={device} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={applicationForm.deviceTypes.includes(device)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setApplicationForm(prev => ({
                          ...prev,
                          deviceTypes: [...prev.deviceTypes, device]
                        }));
                      } else {
                        setApplicationForm(prev => ({
                          ...prev,
                          deviceTypes: prev.deviceTypes.filter(d => d !== device)
                        }));
                      }
                    }}
                    className="mr-2"
                  />
                  {device}
                </label>
              ))}
            </div>
          </div>

          {/* 測試經驗 */}
          <div>
            <label className="block text-sm font-medium mb-2">軟體測試經驗</label>
            <Textarea
              value={applicationForm.testingExperience}
              onChange={(e) => setApplicationForm(prev => ({
                ...prev, testingExperience: e.target.value
              }))}
              placeholder="請描述您參與軟體測試的經驗（如無經驗可填寫'無'）"
              rows={2}
            />
          </div>

          {/* 參與動機 */}
          <div>
            <label className="block text-sm font-medium mb-2">參與Alpha測試的動機 *</label>
            <Textarea
              value={applicationForm.motivation}
              onChange={(e) => setApplicationForm(prev => ({
                ...prev, motivation: e.target.value
              }))}
              placeholder="請告訴我們您為什麼想要參與Alpha測試..."
              rows={3}
            />
          </div>

          {/* 期望 */}
          <div>
            <label className="block text-sm font-medium mb-2">對產品的期望</label>
            <Textarea
              value={applicationForm.expectations}
              onChange={(e) => setApplicationForm(prev => ({
                ...prev, expectations: e.target.value
              }))}
              placeholder="您希望我們的語音分析師能夠為您帶來什麼價值？"
              rows={3}
            />
          </div>

          {/* 可投入時間 */}
          <div>
            <label className="block text-sm font-medium mb-2">每週可投入測試的時間</label>
            <Input
              value={applicationForm.availableTime}
              onChange={(e) => setApplicationForm(prev => ({
                ...prev, availableTime: e.target.value
              }))}
              placeholder="例如：每週2-3小時，主要在晚上"
            />
          </div>

          {/* 反饋承諾 */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="feedback-commitment"
              checked={applicationForm.feedbackCommitment}
              onChange={(e) => setApplicationForm(prev => ({
                ...prev, feedbackCommitment: e.target.checked
              }))}
              className="mr-3"
            />
            <label htmlFor="feedback-commitment" className="text-sm">
              我承諾積極參與測試並提供建設性的反饋意見
            </label>
          </div>

          <Button 
            onClick={submitApplication}
            disabled={loading || !applicationForm.feedbackCommitment}
            className="w-full"
            size="lg"
          >
            <Send className="w-4 h-4 mr-2" />
            提交申請
          </Button>

          <div className="text-sm text-gray-600 text-center">
            <p>提交申請後，我們將在3個工作日內聯繫您。</p>
            <p>Alpha測試期間，您將享有獨家功能體驗和優先客戶支援。</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // 申請管理界面
  const renderApplicationManagement = () => (
    <div className="space-y-6">
      {/* 統計概覽 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Users className="w-8 h-8 mx-auto mb-2 text-blue-500" />
              <p className="text-2xl font-bold">{stats.totalApplications}</p>
              <p className="text-sm text-gray-600">總申請數</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 mx-auto mb-2 text-orange-500" />
              <p className="text-2xl font-bold">{stats.pendingReviews}</p>
              <p className="text-sm text-gray-600">待審核</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="text-2xl font-bold">{stats.approvedUsers}</p>
              <p className="text-sm text-gray-600">已通過</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <UserCheck className="w-8 h-8 mx-auto mb-2 text-purple-500" />
              <p className="text-2xl font-bold">{stats.waitlistUsers}</p>
              <p className="text-sm text-gray-600">候補名單</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Target className="w-8 h-8 mx-auto mb-2 text-red-500" />
              <div className="text-2xl font-bold">
                {stats.targetReached ? '✓' : Math.round((stats.approvedUsers / 50) * 100) + '%'}
              </div>
              <p className="text-sm text-gray-600">目標達成</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 過濾器 */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <select 
              className="border rounded-md p-2"
              value={filters.status}
              onChange={(e) => setFilters(prev => ({...prev, status: e.target.value}))}
            >
              <option value="">所有狀態</option>
              <option value="pending">待審核</option>
              <option value="reviewing">審核中</option>
              <option value="approved">已通過</option>
              <option value="rejected">已拒絕</option>
              <option value="waitlist">候補名單</option>
            </select>
            
            <select 
              className="border rounded-md p-2"
              value={filters.experience}
              onChange={(e) => setFilters(prev => ({...prev, experience: e.target.value}))}
            >
              <option value="">所有經驗</option>
              <option value="beginner">初學者</option>
              <option value="intermediate">中級</option>
              <option value="advanced">高級</option>
              <option value="professional">專業</option>
            </select>
            
            <select 
              className="border rounded-md p-2"
              value={filters.priority}
              onChange={(e) => setFilters(prev => ({...prev, priority: e.target.value}))}
            >
              <option value="">所有優先級</option>
              <option value="high">高優先級</option>
              <option value="medium">中優先級</option>
              <option value="low">低優先級</option>
            </select>
            
            <Button onClick={loadApplications}>
              <Filter className="w-4 h-4 mr-2" />
              刷新數據
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 申請列表 */}
      <div className="space-y-4">
        {applications.filter(app => {
          return (!filters.status || app.status === filters.status) &&
                 (!filters.experience || app.tradingExperience === filters.experience) &&
                 (!filters.priority || app.priority === filters.priority);
        }).map(application => (
          <Card key={application.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-medium text-lg">{application.name}</h4>
                  <p className="text-gray-600">{application.email}</p>
                  <p className="text-sm text-gray-500">
                    {application.company && `${application.company} | `}
                    {application.tradingExperience} | 
                    興趣度: {application.ttsInterest}/5
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={
                    application.status === 'approved' ? 'default' :
                    application.status === 'pending' ? 'secondary' :
                    application.status === 'rejected' ? 'destructive' : 'outline'
                  }>
                    {application.status}
                  </Badge>
                  <Badge variant={
                    application.priority === 'high' ? 'destructive' :
                    application.priority === 'medium' ? 'default' : 'secondary'
                  }>
                    {application.priority}
                  </Badge>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h5 className="font-medium mb-2">參與動機</h5>
                  <p className="text-sm text-gray-600">{application.motivation}</p>
                </div>
                <div>
                  <h5 className="font-medium mb-2">偏好分析師</h5>
                  <div className="flex flex-wrap gap-1">
                    {application.preferredAnalysts.map(analyst => (
                      <Badge key={analyst} variant="outline" className="text-xs">
                        {analyst}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="text-sm text-gray-500">
                  申請時間: {new Date(application.submittedAt).toLocaleDateString()}
                </div>
                
                {application.status === 'pending' && (
                  <div className="flex space-x-2">
                    <Button 
                      size="sm" 
                      onClick={() => reviewApplication(application.id, 'approved')}
                    >
                      <CheckCircle className="w-4 h-4 mr-1" />
                      通過
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => reviewApplication(application.id, 'waitlist')}
                    >
                      候補名單
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => reviewApplication(application.id, 'rejected')}
                    >
                      拒絕
                    </Button>
                  </div>
                )}
                
                {application.status === 'approved' && (
                  <Button 
                    size="sm" 
                    onClick={() => sendWelcomeEmail(application.id)}
                  >
                    <Mail className="w-4 h-4 mr-1" />
                    發送歡迎郵件
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Alpha測試用戶招募</h1>
        <p className="text-gray-600">招募50位優質測試用戶，體驗革新的TTS語音分析師功能</p>
      </div>

      {/* 標籤頁導航 */}
      <div className="flex space-x-1 mb-6 border-b">
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'apply'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('apply')}
        >
          申請參與
        </button>
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'manage'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('manage')}
        >
          申請管理
        </button>
        <button
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'approved'
              ? 'bg-blue-500 text-white'
              : 'text-gray-600 hover:text-blue-500'
          }`}
          onClick={() => setActiveTab('approved')}
        >
          通過名單
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
          {activeTab === 'apply' && renderApplicationForm()}
          {activeTab === 'manage' && renderApplicationManagement()}
          {activeTab === 'approved' && renderApplicationManagement()}
        </>
      )}
    </div>
  );
};

export default AlphaUserRecruitment;
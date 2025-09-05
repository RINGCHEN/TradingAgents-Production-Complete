/**
 * 訂閱管理頁面
 * 提供會員訂閱管理、升級、取消等功能
 */

import React, { useState, useEffect } from 'react';
import { useMembershipStatus, useMembershipUpgrade, useAuthContext } from '../contexts/AuthContext';
import { MemberTier } from '../services/AuthService';
import SubscriptionPlanCard from '../components/SubscriptionPlanCard';
import './SubscriptionManagementPage.css';

interface BillingHistory {
  id: string;
  date: string;
  amount: number;
  tier: MemberTier;
  status: 'paid' | 'pending' | 'failed';
  paymentMethod: string;
  invoiceUrl?: string;
}

const SubscriptionManagementPage: React.FC = () => {
  const { membershipStatus, tier, isActive, usageStats } = useMembershipStatus();
  const { upgradeMembership, isUpgrading } = useMembershipUpgrade();
  const { user } = useAuthContext();
  const [billingHistory, setBillingHistory] = useState<BillingHistory[]>([]);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // 訂閱計劃配置
  const subscriptionPlans = [
    {
      tier: MemberTier.FREE,
      name: 'Free 方案',
      price: 0,
      currency: 'TWD',
      period: 'month',
      features: [
        '每日3次股票分析',
        '基礎技術分析',
        '市場新聞瀏覽',
        '基礎投資建議'
      ],
      limitations: [
        '分析功能有限',
        '無法查看完整報告',
        '無客服支援'
      ],
      popular: false
    },
    {
      tier: MemberTier.GOLD,
      name: 'Gold 方案',
      price: 999,
      currency: 'TWD',
      period: 'month',
      features: [
        '每日20次股票分析',
        '完整技術分析報告',
        '即時市場數據',
        '投資組合追蹤',
        'AI投資建議',
        '自訂價格警報',
        '數據匯出功能',
        '優先客服支援'
      ],
      limitations: [],
      popular: true
    },
    {
      tier: MemberTier.DIAMOND,
      name: 'Diamond 方案',
      price: 1999,
      currency: 'TWD',
      period: 'month',
      features: [
        '無限制股票分析',
        '深度基本面分析',
        '即時市場數據',
        '高級投資組合管理',
        '個人化AI投資顧問',
        '無限制價格警報',
        '完整數據匯出',
        '24/7專屬客服',
        '獨家投資研究報告',
        'VIP社群訪問權限'
      ],
      limitations: [],
      popular: false
    }
  ];

  // 加載帳單歷史
  useEffect(() => {
    const loadBillingHistory = async () => {
      try {
        setLoading(true);
        // 模擬API調用
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const mockHistory: BillingHistory[] = [
          {
            id: '1',
            date: '2025-01-16',
            amount: 999,
            tier: MemberTier.GOLD,
            status: 'paid',
            paymentMethod: '信用卡 ****1234',
            invoiceUrl: '#'
          },
          {
            id: '2',
            date: '2024-12-16',
            amount: 999,
            tier: MemberTier.GOLD,
            status: 'paid',
            paymentMethod: '信用卡 ****1234',
            invoiceUrl: '#'
          }
        ];
        
        setBillingHistory(mockHistory);
      } catch (error) {
        console.error('加載帳單歷史失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    loadBillingHistory();
  }, []);

  // 處理訂閱升級
  const handleUpgrade = async (targetTier: MemberTier) => {
    try {
      await upgradeMembership(targetTier);
    } catch (error) {
      console.error('升級失敗:', error);
    }
  };

  // 處理訂閱取消
  const handleCancelSubscription = async () => {
    try {
      // 實際的取消訂閱邏輯
      console.log('取消訂閱');
      setShowCancelModal(false);
    } catch (error) {
      console.error('取消訂閱失敗:', error);
    }
  };

  // 獲取下次扣款日期
  const getNextBillingDate = () => {
    const nextMonth = new Date();
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    return nextMonth.toLocaleDateString('zh-TW');
  };

  // 計算使用量百分比
  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // 無限制
    return Math.min((used / limit) * 100, 100);
  };

  if (loading) {
    return (
      <div className="subscription-management loading">
        <div className="loading-spinner"></div>
        <p>正在加載訂閱信息...</p>
      </div>
    );
  }

  return (
    <div className="subscription-management">
      <div className="subscription-header">
        <h1>訂閱管理</h1>
        <p>管理您的會員訂閱和帳單設置</p>
      </div>

      {/* 當前訂閱狀態 */}
      <div className="current-subscription">
        <div className="subscription-card">
          <div className="subscription-info">
            <div className="tier-badge tier-{tier.toLowerCase()}">
              {tier === MemberTier.FREE ? 'Free' :
               tier === MemberTier.GOLD ? 'Gold' : 'Diamond'} 會員
            </div>
            <h2>當前訂閱方案</h2>
            <div className="subscription-details">
              <div className="price">
                {tier === MemberTier.FREE ? '免費' :
                 tier === MemberTier.GOLD ? 'NT$ 999/月' : 'NT$ 1,999/月'}
              </div>
              {tier !== MemberTier.FREE && (
                <div className="next-billing">
                  下次扣款日期: {getNextBillingDate()}
                </div>
              )}
              <div className="status">
                狀態: <span className={`status-${isActive ? 'active' : 'inactive'}`}>
                  {isActive ? '正常' : '已暫停'}
                </span>
              </div>
            </div>
          </div>

          {tier !== MemberTier.FREE && (
            <div className="subscription-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowCancelModal(true)}
              >
                取消訂閱
              </button>
            </div>
          )}
        </div>

        {/* 使用量統計 */}
        {usageStats && (
          <div className="usage-stats">
            <h3>本月使用量</h3>
            <div className="usage-items">
              <div className="usage-item">
                <div className="usage-label">股票分析</div>
                <div className="usage-bar">
                  <div 
                    className="usage-fill"
                    style={{ 
                      width: `${getUsagePercentage(
                        usageStats.analysisCount || 0,
                        usageStats.analysisLimit || 0
                      )}%` 
                    }}
                  ></div>
                </div>
                <div className="usage-text">
                  {usageStats.analysisCount || 0}
                  {usageStats.analysisLimit === -1 ? ' / 無限制' : ` / ${usageStats.analysisLimit || 0}`}
                </div>
              </div>

              {usageStats.alertCount !== undefined && (
                <div className="usage-item">
                  <div className="usage-label">價格警報</div>
                  <div className="usage-bar">
                    <div 
                      className="usage-fill"
                      style={{ 
                        width: `${getUsagePercentage(
                          usageStats.alertCount,
                          usageStats.alertLimit || 0
                        )}%` 
                      }}
                    ></div>
                  </div>
                  <div className="usage-text">
                    {usageStats.alertCount}
                    {usageStats.alertLimit === -1 ? ' / 無限制' : ` / ${usageStats.alertLimit || 0}`}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 訂閱方案選擇 */}
      <div className="subscription-plans">
        <div className="plans-header">
          <h2>訂閱方案</h2>
          <p>選擇最適合您的投資分析方案</p>
        </div>

        <div className="plans-grid">
          {subscriptionPlans.map((plan) => (
            <SubscriptionPlanCard
              key={plan.tier}
              tier={plan.tier}
              name={plan.name}
              price={plan.price}
              currency={plan.currency}
              period={plan.period}
              features={plan.features}
              limitations={plan.limitations}
              popular={plan.popular}
              current={tier === plan.tier}
              onSelect={() => {
                if (plan.tier !== tier) {
                  handleUpgrade(plan.tier);
                }
              }}
              disabled={isUpgrading}
            />
          ))}
        </div>
      </div>

      {/* 帳單歷史 */}
      <div className="billing-history">
        <div className="history-header">
          <h2>帳單歷史</h2>
          <button className="btn-secondary">下載所有發票</button>
        </div>

        <div className="history-table">
          <div className="table-header">
            <div>日期</div>
            <div>方案</div>
            <div>金額</div>
            <div>付款方式</div>
            <div>狀態</div>
            <div>發票</div>
          </div>

          {billingHistory.map((item) => (
            <div key={item.id} className="table-row">
              <div>{new Date(item.date).toLocaleDateString('zh-TW')}</div>
              <div>
                {item.tier === MemberTier.GOLD ? 'Gold' : 'Diamond'} 方案
              </div>
              <div>NT$ {item.amount.toLocaleString()}</div>
              <div>{item.paymentMethod}</div>
              <div>
                <span className={`status-badge status-${item.status}`}>
                  {item.status === 'paid' ? '已付款' :
                   item.status === 'pending' ? '處理中' : '失敗'}
                </span>
              </div>
              <div>
                {item.invoiceUrl && (
                  <a href={item.invoiceUrl} className="download-link">
                    下載
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 取消訂閱確認彈窗 */}
      {showCancelModal && (
        <div className="modal-overlay">
          <div className="cancel-modal">
            <div className="modal-header">
              <h3>確認取消訂閱</h3>
              <button 
                className="close-btn"
                onClick={() => setShowCancelModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <p>您確定要取消 {tier === MemberTier.GOLD ? 'Gold' : 'Diamond'} 會員訂閱嗎？</p>
              <div className="cancel-consequences">
                <h4>取消後您將失去以下功能：</h4>
                <ul>
                  <li>高級分析功能訪問權限</li>
                  <li>即時市場數據</li>
                  <li>投資組合追蹤</li>
                  <li>AI投資建議</li>
                  <li>優先客服支援</li>
                </ul>
                <p className="note">
                  * 訂閱將在下個計費週期結束時停止，您可以繼續使用到 {getNextBillingDate()}
                </p>
              </div>
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowCancelModal(false)}
              >
                保留訂閱
              </button>
              <button 
                className="btn-danger"
                onClick={handleCancelSubscription}
              >
                確認取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubscriptionManagementPage;
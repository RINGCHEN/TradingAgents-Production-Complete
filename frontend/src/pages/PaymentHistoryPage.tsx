/**
 * 付款歷史頁面
 * 顯示用戶的付款記錄、發票下載等功能
 */

import React, { useState, useEffect } from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import { MemberTier } from '../services/AuthService';
import './PaymentHistoryPage.css';

interface PaymentRecord {
  id: string;
  date: string;
  amount: number;
  currency: string;
  tier: MemberTier;
  status: 'completed' | 'pending' | 'failed' | 'refunded';
  paymentMethod: string;
  transactionId: string;
  invoiceUrl?: string;
  description: string;
  refundAmount?: number;
  refundDate?: string;
}

interface PaymentStats {
  totalPaid: number;
  totalTransactions: number;
  averageMonthly: number;
  memberSince: string;
}

const PaymentHistoryPage: React.FC = () => {
  const { user } = useAuthContext();
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 加載付款記錄
  useEffect(() => {
    const loadPaymentHistory = async () => {
      try {
        setLoading(true);
        
        // 模擬API調用
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const mockPayments: PaymentRecord[] = [
          {
            id: 'pay_001',
            date: '2025-01-16',
            amount: 999,
            currency: 'TWD',
            tier: MemberTier.GOLD,
            status: 'completed',
            paymentMethod: '信用卡 ****1234',
            transactionId: 'txn_abc123',
            invoiceUrl: '#',
            description: 'Gold 會員月費 - 2025年1月'
          },
          {
            id: 'pay_002',
            date: '2024-12-16',
            amount: 999,
            currency: 'TWD',
            tier: MemberTier.GOLD,
            status: 'completed',
            paymentMethod: '信用卡 ****1234',
            transactionId: 'txn_def456',
            invoiceUrl: '#',
            description: 'Gold 會員月費 - 2024年12月'
          },
          {
            id: 'pay_003',
            date: '2024-11-16',
            amount: 999,
            currency: 'TWD',
            tier: MemberTier.GOLD,
            status: 'completed',
            paymentMethod: '信用卡 ****1234',
            transactionId: 'txn_ghi789',
            invoiceUrl: '#',
            description: 'Gold 會員月費 - 2024年11月'
          },
          {
            id: 'pay_004',
            date: '2024-10-20',
            amount: 499,
            currency: 'TWD',
            tier: MemberTier.GOLD,
            status: 'refunded',
            paymentMethod: '信用卡 ****1234',
            transactionId: 'txn_jkl012',
            description: 'Gold 會員升級費用',
            refundAmount: 499,
            refundDate: '2024-10-25'
          },
          {
            id: 'pay_005',
            date: '2024-10-15',
            amount: 1999,
            currency: 'TWD',
            tier: MemberTier.DIAMOND,
            status: 'failed',
            paymentMethod: '信用卡 ****5678',
            transactionId: 'txn_mno345',
            description: 'Diamond 會員升級'
          }
        ];
        
        const mockStats: PaymentStats = {
          totalPaid: 3496,
          totalTransactions: 5,
          averageMonthly: 999,
          memberSince: '2024-10-15'
        };
        
        setPayments(mockPayments);
        setStats(mockStats);
      } catch (error) {
        console.error('加載付款歷史失敗:', error);
      } finally {
        setLoading(false);
      }
    };

    loadPaymentHistory();
  }, []);

  // 過濾付款記錄
  const filteredPayments = payments.filter(payment => {
    const paymentYear = new Date(payment.date).getFullYear();
    const matchesYear = paymentYear === selectedYear;
    const matchesStatus = filterStatus === 'all' || payment.status === filterStatus;
    const matchesSearch = searchTerm === '' || 
      payment.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.transactionId.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesYear && matchesStatus && matchesSearch;
  });

  // 獲取狀態顯示文字
  const getStatusText = (status: PaymentRecord['status']) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'pending': return '處理中';
      case 'failed': return '失敗';
      case 'refunded': return '已退款';
      default: return status;
    }
  };

  // 獲取狀態樣式類名
  const getStatusClass = (status: PaymentRecord['status']) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'pending': return 'status-pending';
      case 'failed': return 'status-failed';
      case 'refunded': return 'status-refunded';
      default: return '';
    }
  };

  // 獲取會員等級顯示文字
  const getTierText = (tier: MemberTier) => {
    switch (tier) {
      case MemberTier.FREE: return 'Free';
      case MemberTier.GOLD: return 'Gold';
      case MemberTier.DIAMOND: return 'Diamond';
      default: return tier;
    }
  };

  // 下載發票
  const downloadInvoice = (payment: PaymentRecord) => {
    if (payment.invoiceUrl) {
      // 實際實現中這裡會下載PDF發票
      console.log('下載發票:', payment.id);
    }
  };

  // 下載所有發票
  const downloadAllInvoices = () => {
    const completedPayments = filteredPayments.filter(p => p.status === 'completed');
    console.log('下載所有發票:', completedPayments.length, '筆記錄');
  };

  // 申請退款
  const requestRefund = (payment: PaymentRecord) => {
    console.log('申請退款:', payment.id);
  };

  if (loading) {
    return (
      <div className="payment-history loading">
        <div className="loading-spinner"></div>
        <p>正在加載付款記錄...</p>
      </div>
    );
  }

  return (
    <div className="payment-history">
      <div className="payment-header">
        <h1>付款歷史</h1>
        <p>查看您的付款記錄和發票</p>
      </div>

      {/* 付款統計 */}
      {stats && (
        <div className="payment-stats">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">NT$ {stats.totalPaid.toLocaleString()}</div>
              <div className="stat-label">總付款金額</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{stats.totalTransactions}</div>
              <div className="stat-label">交易次數</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">NT$ {stats.averageMonthly.toLocaleString()}</div>
              <div className="stat-label">平均月費</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{new Date(stats.memberSince).toLocaleDateString('zh-TW')}</div>
              <div className="stat-label">會員起始日</div>
            </div>
          </div>
        </div>
      )}

      {/* 篩選控制 */}
      <div className="payment-filters">
        <div className="filters-row">
          <div className="filter-group">
            <label htmlFor="year-select">年份</label>
            <select
              id="year-select"
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="filter-select"
            >
              <option value={2025}>2025</option>
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="status-select">狀態</label>
            <select
              id="status-select"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="filter-select"
            >
              <option value="all">全部狀態</option>
              <option value="completed">已完成</option>
              <option value="pending">處理中</option>
              <option value="failed">失敗</option>
              <option value="refunded">已退款</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="search-input">搜尋</label>
            <input
              id="search-input"
              type="text"
              placeholder="搜尋交易ID或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-actions">
            <button
              onClick={downloadAllInvoices}
              className="btn-secondary"
              disabled={filteredPayments.filter(p => p.status === 'completed').length === 0}
            >
              下載全部發票
            </button>
          </div>
        </div>
      </div>

      {/* 付款記錄表格 */}
      <div className="payment-table-container">
        <div className="payment-table">
          <div className="table-header">
            <div>日期</div>
            <div>描述</div>
            <div>方案</div>
            <div>金額</div>
            <div>付款方式</div>
            <div>狀態</div>
            <div>交易ID</div>
            <div>操作</div>
          </div>

          {filteredPayments.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>沒有付款記錄</h3>
              <p>在選定的條件下沒有找到付款記錄</p>
            </div>
          ) : (
            filteredPayments.map((payment) => (
              <div key={payment.id} className="table-row">
                <div className="payment-date">
                  {new Date(payment.date).toLocaleDateString('zh-TW')}
                </div>
                
                <div className="payment-description">
                  <div className="description-text">{payment.description}</div>
                  {payment.status === 'refunded' && payment.refundDate && (
                    <div className="refund-info">
                      退款日期: {new Date(payment.refundDate).toLocaleDateString('zh-TW')}
                    </div>
                  )}
                </div>
                
                <div className="payment-tier">
                  <span className={`tier-badge tier-${payment.tier.toLowerCase()}`}>
                    {getTierText(payment.tier)}
                  </span>
                </div>
                
                <div className="payment-amount">
                  <div className="amount-primary">
                    {payment.currency} {payment.amount.toLocaleString()}
                  </div>
                  {payment.refundAmount && (
                    <div className="amount-refund">
                      已退款: {payment.currency} {payment.refundAmount.toLocaleString()}
                    </div>
                  )}
                </div>
                
                <div className="payment-method">
                  {payment.paymentMethod}
                </div>
                
                <div className="payment-status">
                  <span className={`status-badge ${getStatusClass(payment.status)}`}>
                    {getStatusText(payment.status)}
                  </span>
                </div>
                
                <div className="transaction-id">
                  <code>{payment.transactionId}</code>
                </div>
                
                <div className="payment-actions">
                  {payment.status === 'completed' && payment.invoiceUrl && (
                    <button
                      onClick={() => downloadInvoice(payment)}
                      className="action-btn download"
                      title="下載發票"
                    >
                      📄
                    </button>
                  )}
                  
                  {payment.status === 'completed' && 
                   new Date(payment.date) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) && (
                    <button
                      onClick={() => requestRefund(payment)}
                      className="action-btn refund"
                      title="申請退款"
                    >
                      🔄
                    </button>
                  )}
                  
                  {payment.status === 'failed' && (
                    <button
                      onClick={() => console.log('重新付款:', payment.id)}
                      className="action-btn retry"
                      title="重新付款"
                    >
                      🔁
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 付款相關說明 */}
      <div className="payment-info">
        <div className="info-section">
          <h3>💡 付款說明</h3>
          <ul>
            <li>會員費用將在每月的訂閱日期自動扣款</li>
            <li>發票將在付款完成後24小時內產生</li>
            <li>如需申請退款，請在付款後30天內提出申請</li>
            <li>退款處理時間為3-7個工作日</li>
          </ul>
        </div>
        
        <div className="info-section">
          <h3>🔒 安全保障</h3>
          <ul>
            <li>我們使用SSL加密保護您的付款資訊</li>
            <li>不會儲存您的完整信用卡號碼</li>
            <li>符合PCI DSS安全標準</li>
            <li>支援多種安全的付款方式</li>
          </ul>
        </div>
        
        <div className="info-section">
          <h3>📞 聯繫我們</h3>
          <p>如果您對付款記錄有任何疑問，請聯繫我們的客服團隊：</p>
          <ul>
            <li>Email: billing@tradingagents.com</li>
            <li>電話: 0800-123-456</li>
            <li>線上客服: 週一至週五 9:00-18:00</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PaymentHistoryPage;
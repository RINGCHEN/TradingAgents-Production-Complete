/**
 * CouponManagerExample - 簡單的優惠券管理器使用示例
 * 展示如何在實際應用中使用CouponManager
 */

import React from 'react';
import { CouponManagerProvider, useCoupons, useCouponCalculator } from './CouponManagerProvider';
import { ApiClientProvider } from './ApiClientProvider';

const CouponDisplay: React.FC = () => {
  const { coupons, loading, error, fallbackMode, refetch } = useCoupons();
  const { getBestCoupon } = useCouponCalculator();
  
  const testAmount = 1000;
  const bestCoupon = getBestCoupon(testAmount);

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>優惠券管理器示例</h2>
      
      {/* 狀態顯示 */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3>系統狀態</h3>
        <p><strong>載入中:</strong> {loading ? '是' : '否'}</p>
        <p><strong>降級模式:</strong> {fallbackMode ? '是' : '否'}</p>
        <p><strong>優惠券數量:</strong> {coupons.length}</p>
        {error && <p style={{ color: 'red' }}><strong>錯誤:</strong> {error}</p>}
        
        <button 
          onClick={refetch}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          重新載入優惠券
        </button>
      </div>

      {/* 優惠券列表 */}
      <div style={{ marginBottom: '20px' }}>
        <h3>可用優惠券</h3>
        {coupons.length === 0 ? (
          <p>暫無優惠券</p>
        ) : (
          <div style={{ display: 'grid', gap: '10px' }}>
            {coupons.map(coupon => (
              <div 
                key={coupon.id}
                style={{
                  padding: '15px',
                  border: '1px solid #dee2e6',
                  borderRadius: '8px',
                  backgroundColor: coupon.isActive ? '#ffffff' : '#f8f9fa'
                }}
              >
                <h4 style={{ margin: '0 0 10px 0', color: coupon.isActive ? '#007bff' : '#6c757d' }}>
                  {coupon.title}
                </h4>
                <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#6c757d' }}>
                  {coupon.description}
                </p>
                <div style={{ display: 'flex', gap: '20px', fontSize: '13px' }}>
                  <span><strong>代碼:</strong> {coupon.code}</span>
                  <span><strong>折扣:</strong> {coupon.discountType === 'percentage' ? `${coupon.discount}%` : `NT$ ${coupon.discount}`}</span>
                  {coupon.minAmount && <span><strong>最低金額:</strong> NT$ {coupon.minAmount}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 最佳優惠券推薦 */}
      {bestCoupon.coupon && (
        <div style={{ padding: '15px', backgroundColor: '#d4edda', borderRadius: '8px', border: '1px solid #c3e6cb' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#155724' }}>💡 最佳優惠推薦</h3>
          <p style={{ margin: '0', color: '#155724' }}>
            購買 NT$ {testAmount.toLocaleString()} 時，使用 <strong>{bestCoupon.coupon.code}</strong> 可節省 <strong>NT$ {bestCoupon.discount}</strong>
          </p>
        </div>
      )}
    </div>
  );
};

const CouponManagerExample: React.FC = () => {
  return (
    <ApiClientProvider>
      <CouponManagerProvider 
        autoLoad={true}
        config={{
          maxRetries: 2,
          cacheTimeout: 5 * 60 * 1000, // 5分鐘
          enableDiagnostics: true
        }}
      >
        <CouponDisplay />
      </CouponManagerProvider>
    </ApiClientProvider>
  );
};

export default CouponManagerExample;
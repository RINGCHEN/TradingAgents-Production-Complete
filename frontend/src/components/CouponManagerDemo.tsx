/**
 * CouponManagerDemo - 優惠券管理器演示組件
 * 展示CouponManager的功能和錯誤處理能力
 */

import React, { useState } from 'react';
import { useCoupons, useAvailableCoupons, useCouponCalculator } from './CouponManagerProvider';

const CouponManagerDemo: React.FC = () => {
  const { coupons, loading, error, fallbackMode, retryCount, isHealthy, refetch, reload } = useCoupons();
  const availableCoupons = useAvailableCoupons();
  const { getApplicableCoupons, calculateDiscount, getBestCoupon } = useCouponCalculator();
  
  const [testAmount, setTestAmount] = useState<number>(1000);
  const [selectedCoupon, setSelectedCoupon] = useState<string>('');

  const applicableCoupons = getApplicableCoupons(testAmount);
  const bestCouponResult = getBestCoupon(testAmount);
  const selectedCouponObj = coupons.find(c => c.id === selectedCoupon);
  const selectedDiscount = selectedCouponObj ? calculateDiscount(selectedCouponObj, testAmount) : 0;

  const formatCurrency = (amount: number) => `NT$ ${amount.toLocaleString()}`;
  const formatDate = (date: Date) => date.toLocaleDateString('zh-TW');

  return (
    <div className="coupon-manager-demo" style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>🎫 優惠券管理器演示</h2>
      
      {/* 系統狀態 */}
      <div className="status-section" style={{ marginBottom: '20px' }}>
        <h3>系統狀態</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
          <div className={`status-card ${isHealthy ? 'healthy' : 'unhealthy'}`} style={{
            padding: '15px',
            border: `2px solid ${isHealthy ? '#28a745' : '#dc3545'}`,
            borderRadius: '8px',
            backgroundColor: isHealthy ? '#d4edda' : '#f8d7da'
          }}>
            <strong>健康狀態:</strong> {isHealthy ? '✅ 正常' : '❌ 異常'}
          </div>
          
          <div className="status-card" style={{
            padding: '15px',
            border: '2px solid #17a2b8',
            borderRadius: '8px',
            backgroundColor: '#d1ecf1'
          }}>
            <strong>載入狀態:</strong> {loading ? '🔄 載入中' : '✅ 完成'}
          </div>
          
          <div className={`status-card ${fallbackMode ? 'fallback' : 'normal'}`} style={{
            padding: '15px',
            border: `2px solid ${fallbackMode ? '#ffc107' : '#28a745'}`,
            borderRadius: '8px',
            backgroundColor: fallbackMode ? '#fff3cd' : '#d4edda'
          }}>
            <strong>運行模式:</strong> {fallbackMode ? '⚠️ 降級模式' : '✅ 正常模式'}
          </div>
          
          <div className="status-card" style={{
            padding: '15px',
            border: '2px solid #6c757d',
            borderRadius: '8px',
            backgroundColor: '#e2e3e5'
          }}>
            <strong>重試次數:</strong> {retryCount}
          </div>
        </div>
        
        {error && (
          <div className="error-message" style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24'
          }}>
            <strong>錯誤信息:</strong> {error}
          </div>
        )}
      </div>

      {/* 控制按鈕 */}
      <div className="controls-section" style={{ marginBottom: '20px' }}>
        <h3>控制操作</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={refetch}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? '載入中...' : '重新載入'}
          </button>
          
          <button
            onClick={reload}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            強制刷新
          </button>
        </div>
      </div>

      {/* 優惠券列表 */}
      <div className="coupons-section" style={{ marginBottom: '20px' }}>
        <h3>優惠券列表 ({coupons.length} 個)</h3>
        {coupons.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
            {loading ? '載入中...' : '暫無優惠券'}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '15px' }}>
            {coupons.map(coupon => (
              <div key={coupon.id} className="coupon-card" style={{
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                padding: '15px',
                backgroundColor: coupon.isActive ? '#ffffff' : '#f8f9fa'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <h4 style={{ margin: 0, color: coupon.isActive ? '#007bff' : '#6c757d' }}>
                    {coupon.title}
                  </h4>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    backgroundColor: coupon.isActive ? '#d4edda' : '#e2e3e5',
                    color: coupon.isActive ? '#155724' : '#6c757d'
                  }}>
                    {coupon.isActive ? '有效' : '無效'}
                  </span>
                </div>
                
                <div style={{ marginBottom: '10px' }}>
                  <strong>優惠碼:</strong> <code style={{ backgroundColor: '#f8f9fa', padding: '2px 4px', borderRadius: '3px' }}>{coupon.code}</code>
                </div>
                
                <div style={{ marginBottom: '10px', color: '#6c757d', fontSize: '14px' }}>
                  {coupon.description}
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '13px' }}>
                  <div><strong>折扣:</strong> {coupon.discountType === 'percentage' ? `${coupon.discount}%` : formatCurrency(coupon.discount)}</div>
                  <div><strong>最低金額:</strong> {coupon.minAmount ? formatCurrency(coupon.minAmount) : '無限制'}</div>
                  <div><strong>有效期:</strong> {formatDate(coupon.validFrom)}</div>
                  <div><strong>到期日:</strong> {formatDate(coupon.validTo)}</div>
                </div>
                
                {coupon.usageLimit && (
                  <div style={{ marginTop: '10px', fontSize: '13px' }}>
                    <strong>使用限制:</strong> {coupon.usedCount || 0} / {coupon.usageLimit}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 可用優惠券 */}
      <div className="available-coupons-section" style={{ marginBottom: '20px' }}>
        <h3>目前可用優惠券 ({availableCoupons.length} 個)</h3>
        {availableCoupons.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
            暫無可用優惠券
          </div>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {availableCoupons.map(coupon => (
              <div key={coupon.id} style={{
                padding: '8px 12px',
                backgroundColor: '#e7f3ff',
                border: '1px solid #b3d7ff',
                borderRadius: '20px',
                fontSize: '14px'
              }}>
                {coupon.code} - {coupon.discountType === 'percentage' ? `${coupon.discount}%` : formatCurrency(coupon.discount)}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 優惠券計算器 */}
      <div className="calculator-section" style={{ marginBottom: '20px' }}>
        <h3>優惠券計算器</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* 輸入區域 */}
          <div className="input-section" style={{
            padding: '20px',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            backgroundColor: '#f8f9fa'
          }}>
            <h4>測試參數</h4>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                購買金額:
              </label>
              <input
                type="number"
                value={testAmount}
                onChange={(e) => setTestAmount(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ced4da',
                  borderRadius: '4px'
                }}
                min="0"
                step="100"
              />
            </div>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                選擇優惠券:
              </label>
              <select
                value={selectedCoupon}
                onChange={(e) => setSelectedCoupon(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ced4da',
                  borderRadius: '4px'
                }}
              >
                <option value="">請選擇優惠券</option>
                {applicableCoupons.map(coupon => (
                  <option key={coupon.id} value={coupon.id}>
                    {coupon.code} - {coupon.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 計算結果 */}
          <div className="result-section" style={{
            padding: '20px',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            backgroundColor: '#ffffff'
          }}>
            <h4>計算結果</h4>
            
            <div style={{ marginBottom: '15px' }}>
              <strong>適用優惠券數量:</strong> {applicableCoupons.length} 個
            </div>
            
            {bestCouponResult.coupon && (
              <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#d4edda', borderRadius: '4px' }}>
                <strong>最佳優惠券:</strong> {bestCouponResult.coupon.code}<br />
                <strong>最大折扣:</strong> {formatCurrency(bestCouponResult.discount)}
              </div>
            )}
            
            {selectedCouponObj && (
              <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#e7f3ff', borderRadius: '4px' }}>
                <strong>選中優惠券:</strong> {selectedCouponObj.code}<br />
                <strong>折扣金額:</strong> {formatCurrency(selectedDiscount)}<br />
                <strong>最終金額:</strong> {formatCurrency(testAmount - selectedDiscount)}
              </div>
            )}
            
            <div style={{ fontSize: '14px', color: '#6c757d' }}>
              <strong>原價:</strong> {formatCurrency(testAmount)}
            </div>
          </div>
        </div>
      </div>

      {/* 診斷信息 */}
      <div className="diagnostics-section">
        <h3>診斷信息</h3>
        <div style={{
          padding: '15px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          fontFamily: 'monospace',
          fontSize: '13px'
        }}>
          <div><strong>總優惠券數:</strong> {coupons.length}</div>
          <div><strong>可用優惠券數:</strong> {availableCoupons.length}</div>
          <div><strong>適用優惠券數:</strong> {applicableCoupons.length}</div>
          <div><strong>降級模式:</strong> {fallbackMode ? '是' : '否'}</div>
          <div><strong>重試次數:</strong> {retryCount}</div>
          <div><strong>健康狀態:</strong> {isHealthy ? '正常' : '異常'}</div>
          {error && <div><strong>錯誤信息:</strong> {error}</div>}
        </div>
      </div>
    </div>
  );
};

export default CouponManagerDemo;
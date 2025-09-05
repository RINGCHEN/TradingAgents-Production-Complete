import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface PaymentData {
  order_number: string;
  amount: number;
  tier_type: string;
  payment_url?: string;
  form_data?: any;
}

const PayUniPaymentPage: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const navigate = useNavigate();
  const [paymentData, setPaymentData] = useState<PaymentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPaymentData = async () => {
      if (!orderNumber) {
        setError('訂單號碼遺失');
        setLoading(false);
        return;
      }

      try {
        console.log('🔄 載入PayUni支付數據...', { orderNumber });
        
        // 調用後端API獲取真正的支付頁面
        const response = await fetch(`https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/payment-page/${orderNumber}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          // 如果後端返回HTML，直接重定向到該頁面
          if (response.headers.get('content-type')?.includes('text/html')) {
            console.log('🔄 重定向到後端PayUni支付頁面');
            window.location.href = `https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/payment-page/${orderNumber}`;
            return;
          }
          
          // 如果是JSON數據，處理支付數據
          const data = await response.json();
          setPaymentData(data);
          console.log('✅ PayUni支付數據載入成功', data);
        } else {
          console.error('❌ PayUni支付數據載入失敗', response.status);
          setError(`支付數據載入失敗 (${response.status})`);
        }
      } catch (err) {
        console.error('❌ PayUni支付數據載入異常', err);
        setError('網路連接失敗，請檢查連線狀態');
      } finally {
        setLoading(false);
      }
    };

    loadPaymentData();
  }, [orderNumber]);

  const handleReturnToPricing = () => {
    console.log('🔙 用戶手動返回定價頁面');
    navigate('/pricing');
  };

  const handleContactSupport = () => {
    console.log('📞 聯繫客服');
    alert('請聯繫客服：service@03king.com 或 Line: @tradingagents');
  };

  // 載入中狀態
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>
        <div style={{
          background: 'white',
          padding: '40px',
          borderRadius: '20px',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)',
          maxWidth: '500px',
          width: '90%'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🔄</div>
          <h1 style={{ color: '#333', marginBottom: '15px' }}>
            正在載入PayUni支付頁面...
          </h1>
          <p style={{ color: '#666', lineHeight: '1.6' }}>
            請稍候，正在準備您的支付資訊
          </p>
          <div style={{
            margin: '20px auto',
            width: '40px',
            height: '40px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #667eea',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>
        <div style={{
          background: 'white',
          padding: '40px',
          borderRadius: '20px',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)',
          maxWidth: '500px',
          width: '90%'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '20px' }}>❌</div>
          <h1 style={{ color: '#333', marginBottom: '15px' }}>
            支付頁面載入失敗
          </h1>
          <p style={{ color: '#666', lineHeight: '1.6', marginBottom: '20px' }}>
            {error}
          </p>
          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
            <button
              onClick={handleReturnToPricing}
              style={{
                background: '#28a745',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              返回定價頁面
            </button>
            <button
              onClick={handleContactSupport}
              style={{
                background: '#17a2b8',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '500'
              }}
            >
              📞 聯繫客服
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 正常情況：如果執行到這裡，表示已經重定向到後端支付頁面
  // 這個return語句通常不會被執行，因為上面的useEffect會重定向
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '20px',
        textAlign: 'center',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.1)',
        maxWidth: '500px',
        width: '90%'
      }}>
        <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🔄</div>
        <h1 style={{ color: '#333', marginBottom: '15px' }}>
          正在重定向到PayUni支付頁面...
        </h1>
        <p style={{ color: '#666', lineHeight: '1.6' }}>
          如果頁面沒有自動跳轉，請點擊下方按鈕
        </p>
        <button
          onClick={() => window.location.href = `https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/payment-page/${orderNumber}`}
          style={{
            background: '#667eea',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '500',
            marginTop: '20px'
          }}
        >
          前往支付頁面
        </button>
      </div>
    </div>
  );
};

export default PayUniPaymentPage;
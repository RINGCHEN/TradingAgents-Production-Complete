import React, { useState } from 'react';

/**
 * 簡單支付測試組件
 * 用於診斷PayUni支付問題
 */
export const SimplePaymentTest: React.FC = () => {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testPayment = async () => {
    setLoading(true);
    setResult('開始測試...');
    
    try {
      const apiBase = 'https://coral-app-knueo.ondigitalocean.app';
      
      const response = await fetch(`${apiBase}/api/v1/payuni/create-guest-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tier_type: 'gold',
          amount: 1999,
          description: 'Test Order from SimplePaymentTest',
          user_email: 'test@diagnosis.com'
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setResult(`✅ API調用成功！
訂單號: ${data.order_number}
支付URL: ${data.payment_url}
狀態: ${data.success ? '成功' : '失敗'}

準備跳轉測試...`);

        // 3秒後測試跳轉
        setTimeout(() => {
          const paymentUrl = data.payment_url;
          if (paymentUrl) {
            if (paymentUrl.startsWith('http')) {
              setResult(prev => prev + '\n\n🔗 完整URL跳轉測試...');
              window.location.href = paymentUrl;
            } else {
              const fullUrl = `${apiBase}${paymentUrl}`;
              setResult(prev => prev + `\n\n🔗 拼接URL跳轉測試: ${fullUrl}`);
              // 先測試URL是否可訪問
              fetch(fullUrl)
                .then(res => {
                  if (res.ok) {
                    window.location.href = fullUrl;
                  } else {
                    setResult(prev => prev + `\n❌ URL不可訪問 (${res.status})`);
                    alert('支付端點不存在，這就是跳回首頁的原因！');
                  }
                })
                .catch(err => {
                  setResult(prev => prev + `\n❌ URL訪問錯誤: ${err.message}`);
                  alert('支付端點訪問失敗，這就是跳回首頁的原因！');
                });
            }
          }
        }, 3000);
      } else {
        setResult(`❌ API調用失敗: ${data.message || '未知錯誤'}`);
      }
    } catch (error) {
      setResult(`❌ 網路錯誤: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      maxWidth: '600px', 
      margin: '0 auto',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ color: '#333', textAlign: 'center' }}>
        🔧 PayUni 支付問題診斷工具
      </h1>
      
      <div style={{ 
        background: '#f5f5f5', 
        padding: '15px', 
        borderRadius: '5px',
        marginBottom: '20px'
      }}>
        <h3>測試說明：</h3>
        <p>此工具會模擬完整的支付流程，幫助診斷「跳回首頁」問題的根本原因。</p>
      </div>

      <button
        onClick={testPayment}
        disabled={loading}
        style={{
          width: '100%',
          padding: '15px',
          fontSize: '18px',
          backgroundColor: loading ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {loading ? '🔄 測試中...' : '🚀 開始支付流程診斷'}
      </button>

      {result && (
        <div style={{
          background: '#fff',
          border: '1px solid #ddd',
          borderRadius: '5px',
          padding: '15px',
          whiteSpace: 'pre-wrap',
          fontSize: '14px',
          lineHeight: '1.6'
        }}>
          <h4>診斷結果：</h4>
          {result}
        </div>
      )}

      <div style={{
        background: '#e7f3ff',
        border: '1px solid #b3d9ff',
        borderRadius: '5px',
        padding: '15px',
        marginTop: '20px'
      }}>
        <h4>🔍 預期診斷結果：</h4>
        <ul style={{ margin: 0, paddingLeft: '20px' }}>
          <li>如果API調用成功但URL不可訪問 → 支付端點缺失問題</li>
          <li>如果跳轉時返回首頁 → 404錯誤導致的重定向</li>
          <li>如果API調用失敗 → 後端問題</li>
        </ul>
      </div>
    </div>
  );
};
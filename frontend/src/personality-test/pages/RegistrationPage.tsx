import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { personalityTestAPI } from '../services/PersonalityTestAPI';
import { userExperienceService } from '../services/UserExperienceService';
import './RegistrationPage.css';

interface RegistrationPageProps {
  // 可以通過props或location state傳入數據
}

interface PrefillData {
  personality_type: string;
  percentile: number;
  investment_style: string;
  recommendations: string[];
  suggested_next_steps: string[];
}

interface FormData {
  name: string;
  email: string;
  phone: string;
  agreeToTerms: boolean;
  subscribeNewsletter: boolean;
}

interface FormErrors {
  name?: string;
  email?: string;
  phone?: string;
  agreeToTerms?: string;
}

const RegistrationPage: React.FC<RegistrationPageProps> = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 從location state獲取數據
  const { resultId, personalityType, sessionId, abVariant } = location.state || {};
  
  const [prefillData, setPrefillData] = useState<PrefillData | null>(null);
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    phone: '',
    agreeToTerms: false,
    subscribeNewsletter: true
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  useEffect(() => {
    // 追蹤註冊頁面訪問
    userExperienceService.trackInteraction({
      type: 'focus',
      element: 'registration_page',
      timestamp: Date.now()
    });
    
    // 追蹤轉換步驟
    if (sessionId) {
      personalityTestAPI.trackConversionStep({
        session_id: sessionId,
        step: 'register_page_view',
        action: 'page_loaded',
        data: { 
          ab_variant: abVariant,
          result_id: resultId,
          referrer: document.referrer
        }
      });
    }
    
    // 載入預填數據
    if (resultId) {
      loadPrefillData();
    }
  }, [resultId, sessionId, abVariant]);
  
  const loadPrefillData = async () => {
    if (!resultId) return;
    
    try {
      const response = await fetch(`/api/conversion/prefill-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ result_id: resultId })
      });
      
      const data = await response.json();
      if (data.success) {
        setPrefillData(data.prefill_data);
      }
    } catch (error) {
      console.error('Failed to load prefill data:', error);
    } finally {
      // Loading finished
    }
  };
  
  const validateForm = (): boolean => {
    const errors: FormErrors = {};
    
    // 驗證姓名
    if (!formData.name.trim()) {
      errors.name = '請輸入您的姓名';
    } else if (formData.name.trim().length < 2) {
      errors.name = '姓名至少需要2個字符';
    }
    
    // 驗證郵箱
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      errors.email = '請輸入您的郵箱地址';
    } else if (!emailRegex.test(formData.email)) {
      errors.email = '請輸入有效的郵箱地址';
    }
    
    // 驗證電話（可選）
    if (formData.phone.trim() && formData.phone.trim().length < 8) {
      errors.phone = '請輸入有效的電話號碼';
    }
    
    // 驗證條款同意
    if (!formData.agreeToTerms) {
      errors.agreeToTerms = '請同意服務條款和隱私政策';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 清除對應的錯誤
    if (formErrors[field as keyof FormErrors]) {
      setFormErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // 追蹤註冊提交
      if (sessionId) {
        await personalityTestAPI.trackConversionStep({
          session_id: sessionId,
          step: 'register_submit',
          action: 'form_submitted',
          data: { 
            ab_variant: abVariant,
            has_phone: !!formData.phone.trim(),
            subscribe_newsletter: formData.subscribeNewsletter
          }
        });
      }
      
      // 提交註冊
      const registrationData = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone: formData.phone.trim() || null,
        result_id: resultId,
        session_id: sessionId,
        utm_params: getUTMParams(),
        referrer: document.referrer,
        ab_variant: abVariant
      };
      
      const response = await fetch('/api/conversion/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        // 追蹤註冊成功
        userExperienceService.trackInteraction({
          type: 'click',
          element: 'registration_success',
          timestamp: Date.now()
        });
        
        setShowSuccess(true);
        
        // 3秒後跳轉到主系統或歡迎頁面
        setTimeout(() => {
          navigate('/personality-test/welcome', {
            state: {
              userId: result.user_id,
              nextSteps: result.next_steps,
              personalityType: personalityType
            }
          });
        }, 3000);
        
      } else {
        // 處理註冊失敗
        if (result.message.includes('已註冊')) {
          setFormErrors({ email: result.message });
        } else {
          alert(`註冊失敗：${result.message}`);
        }
      }
      
    } catch (error) {
      console.error('Registration failed:', error);
      alert('註冊失敗，請稍後再試');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const getUTMParams = (): Record<string, string> => {
    const urlParams = new URLSearchParams(window.location.search);
    const utmParams: Record<string, string> = {};
    
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(param => {
      const value = urlParams.get(param);
      if (value) {
        utmParams[param] = value;
      }
    });
    
    return utmParams;
  };
  
  if (showSuccess) {
    return (
      <div className="registration-page success">
        <div className="success-container">
          <div className="success-icon">🎉</div>
          <h1 className="success-title">註冊成功！</h1>
          <p className="success-message">
            歡迎加入 TradingAgents！我們已經為您發送了歡迎郵件。
          </p>
          <div className="success-animation">
            <div className="loading-spinner"></div>
            <p>正在為您準備個性化投資建議...</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="registration-page">
      <div className="registration-container">
        
        {/* 頁面標題 */}
        <header className="registration-header">
          <h1 className="page-title">完成註冊，開始您的投資之旅</h1>
          {prefillData && (
            <div className="personality-summary">
              <div className="summary-badge">
                <span className="badge-text">您的投資人格：{prefillData.personality_type}</span>
                <span className="badge-percentile">擊敗了 {prefillData.percentile}% 的投資者</span>
              </div>
            </div>
          )}
        </header>
        
        <div className="registration-content">
          
          {/* 註冊表單 */}
          <div className="form-section">
            <form onSubmit={handleSubmit} className="registration-form">
              
              <div className="form-group">
                <label htmlFor="name" className="form-label">
                  姓名 <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  className={`form-input ${formErrors.name ? 'error' : ''}`}
                  value={formData.name}
                  onChange={(e: any) => handleInputChange('name', e.target.value)}
                  placeholder="請輸入您的姓名"
                  disabled={isSubmitting}
                />
                {formErrors.name && (
                  <span className="error-message">{formErrors.name}</span>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  郵箱地址 <span className="required">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  className={`form-input ${formErrors.email ? 'error' : ''}`}
                  value={formData.email}
                  onChange={(e: any) => handleInputChange('email', e.target.value)}
                  placeholder="請輸入您的郵箱地址"
                  disabled={isSubmitting}
                />
                {formErrors.email && (
                  <span className="error-message">{formErrors.email}</span>
                )}
              </div>
              
              <div className="form-group">
                <label htmlFor="phone" className="form-label">
                  電話號碼 <span className="optional">(可選)</span>
                </label>
                <input
                  type="tel"
                  id="phone"
                  className={`form-input ${formErrors.phone ? 'error' : ''}`}
                  value={formData.phone}
                  onChange={(e: any) => handleInputChange('phone', e.target.value)}
                  placeholder="請輸入您的電話號碼"
                  disabled={isSubmitting}
                />
                {formErrors.phone && (
                  <span className="error-message">{formErrors.phone}</span>
                )}
              </div>
              
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.agreeToTerms}
                    onChange={(e: any) => handleInputChange('agreeToTerms', e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-text">
                    我同意 <a href="/terms" target="_blank">服務條款</a> 和 <a href="/privacy" target="_blank">隱私政策</a>
                    <span className="required">*</span>
                  </span>
                </label>
                {formErrors.agreeToTerms && (
                  <span className="error-message">{formErrors.agreeToTerms}</span>
                )}
              </div>
              
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.subscribeNewsletter}
                    onChange={(e: any) => handleInputChange('subscribeNewsletter', e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-text">
                    訂閱投資分析報告和市場動態（推薦）
                  </span>
                </label>
              </div>
              
              <button
                type="submit"
                className="submit-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <span className="loading-spinner small"></span>
                    註冊中...
                  </>
                ) : (
                  '免費註冊'
                )}
              </button>
              
            </form>
          </div>
          
          {/* 價值主張 */}
          <div className="value-proposition">
            <h3 className="value-title">註冊後您將獲得：</h3>
            
            {prefillData ? (
              <div className="personalized-benefits">
                <div className="benefit-item featured">
                  <div className="benefit-icon">🎯</div>
                  <div className="benefit-content">
                    <h4>專為{prefillData.personality_type}設計的投資策略</h4>
                    <p>{prefillData.investment_style}</p>
                  </div>
                </div>
                
                <div className="recommendations-section">
                  <h4>個性化建議：</h4>
                  <ul className="recommendations-list">
                    {prefillData.recommendations.map((rec, index) => (
                      <li key={index} className="recommendation-item">
                        <span className="rec-icon">💡</span>
                        <span className="rec-text">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="next-steps-section">
                  <h4>下一步：</h4>
                  <ol className="next-steps-list">
                    {prefillData.suggested_next_steps.map((step, index) => (
                      <li key={index} className="next-step-item">{step}</li>
                    ))}
                  </ol>
                </div>
              </div>
            ) : (
              <div className="standard-benefits">
                <div className="benefit-item">
                  <div className="benefit-icon">📊</div>
                  <div className="benefit-content">
                    <h4>專業投資分析</h4>
                    <p>獲得專業分析師的個人化投資建議</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">⚡</div>
                  <div className="benefit-content">
                    <h4>實時市場警報</h4>
                    <p>第一時間獲得重要市場動態和投資機會</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">🎯</div>
                  <div className="benefit-content">
                    <h4>投資組合優化</h4>
                    <p>基於您的風險偏好優化投資組合配置</p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="trust-indicators">
              <div className="trust-item">
                <span className="trust-icon">🔒</span>
                <span className="trust-text">資料安全保護</span>
              </div>
              <div className="trust-item">
                <span className="trust-icon">✅</span>
                <span className="trust-text">完全免費</span>
              </div>
              <div className="trust-item">
                <span className="trust-icon">📱</span>
                <span className="trust-text">隨時隨地使用</span>
              </div>
            </div>
          </div>
          
        </div>
        
      </div>
    </div>
  );
};

export default RegistrationPage;
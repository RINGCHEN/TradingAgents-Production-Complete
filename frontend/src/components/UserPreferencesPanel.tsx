import React, { useState, useEffect } from 'react';
import './UserPreferencesPanel.css';

interface UserPreferences {
  notifications: {
    email: boolean;
    browser: boolean;
    sms: boolean;
    priceAlerts: boolean;
    newsAlerts: boolean;
    analysisComplete: boolean;
  };
  display: {
    theme: 'light' | 'dark' | 'auto';
    language: 'zh-TW' | 'zh-CN' | 'en-US';
    currency: 'TWD' | 'USD' | 'CNY';
    timezone: string;
  };
  trading: {
    defaultAnalysisType: 'comprehensive' | 'technical' | 'fundamental';
    riskTolerance: 'conservative' | 'moderate' | 'aggressive';
    autoAnalysis: boolean;
    favoriteAnalysts: string[];
  };
  privacy: {
    profileVisibility: 'public' | 'private';
    shareAnalytics: boolean;
    marketingEmails: boolean;
  };
}

interface UserPreferencesPanelProps {
  userId: string;
  onSave: (preferences: UserPreferences) => void;
}

export const UserPreferencesPanel: React.FC<UserPreferencesPanelProps> = ({ userId, onSave }) => {
  const [preferences, setPreferences] = useState<UserPreferences>({
    notifications: {
      email: true,
      browser: true,
      sms: false,
      priceAlerts: true,
      newsAlerts: true,
      analysisComplete: true,
    },
    display: {
      theme: 'auto',
      language: 'zh-TW',
      currency: 'TWD',
      timezone: 'Asia/Taipei',
    },
    trading: {
      defaultAnalysisType: 'comprehensive',
      riskTolerance: 'moderate',
      autoAnalysis: false,
      favoriteAnalysts: [],
    },
    privacy: {
      profileVisibility: 'private',
      shareAnalytics: true,
      marketingEmails: false,
    },
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // 載入用戶偏好設置
  useEffect(() => {
    const savedPreferences = localStorage.getItem(`user_preferences_${userId}`);
    if (savedPreferences) {
      try {
        const parsedPreferences = JSON.parse(savedPreferences);
        setPreferences({ ...preferences, ...parsedPreferences });
      } catch (error) {
        console.error('Failed to load user preferences:', error);
      }
    }
  }, [userId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // 儲存到 localStorage
      localStorage.setItem(`user_preferences_${userId}`, JSON.stringify(preferences));
      
      // 模擬 API 延遲
      await new Promise(resolve => setTimeout(resolve, 800));
      
      setSaved(true);
      onSave(preferences);
      
      // 顯示成功訊息後隱藏
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
    } finally {
      setSaving(false);
    }
  };

  const updatePreferences = (section: keyof UserPreferences, key: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  return (
    <div className="user-preferences-panel">
      <div className="preferences-content">
        
        {/* 通知設置 */}
        <section className="preference-section">
          <h3 className="section-title">
            <span className="section-icon">🔔</span>
            通知設置
          </h3>
          <div className="preference-grid">
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.notifications.email}
                  onChange={(e) => updatePreferences('notifications', 'email', e.target.checked)}
                />
                <span className="checkmark"></span>
                電子郵件通知
              </label>
              <p className="preference-description">接收重要通知和分析報告</p>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.notifications.browser}
                  onChange={(e) => updatePreferences('notifications', 'browser', e.target.checked)}
                />
                <span className="checkmark"></span>
                瀏覽器推送通知
              </label>
              <p className="preference-description">即時市場警報和分析完成通知</p>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.notifications.priceAlerts}
                  onChange={(e) => updatePreferences('notifications', 'priceAlerts', e.target.checked)}
                />
                <span className="checkmark"></span>
                價格警報
              </label>
              <p className="preference-description">股價達到設定條件時通知</p>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.notifications.newsAlerts}
                  onChange={(e) => updatePreferences('notifications', 'newsAlerts', e.target.checked)}
                />
                <span className="checkmark"></span>
                新聞警報
              </label>
              <p className="preference-description">重要財經新聞和公司公告</p>
            </div>
          </div>
        </section>

        {/* 顯示設置 */}
        <section className="preference-section">
          <h3 className="section-title">
            <span className="section-icon">🎨</span>
            顯示設置
          </h3>
          <div className="preference-grid">
            <div className="preference-item">
              <label className="preference-label">主題外觀</label>
              <select
                value={preferences.display.theme}
                onChange={(e) => updatePreferences('display', 'theme', e.target.value)}
                className="preference-select"
              >
                <option value="light">淺色主題</option>
                <option value="dark">深色主題</option>
                <option value="auto">跟隨系統</option>
              </select>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">語言設置</label>
              <select
                value={preferences.display.language}
                onChange={(e) => updatePreferences('display', 'language', e.target.value)}
                className="preference-select"
              >
                <option value="zh-TW">繁體中文</option>
                <option value="zh-CN">簡體中文</option>
                <option value="en-US">English</option>
              </select>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">貨幣顯示</label>
              <select
                value={preferences.display.currency}
                onChange={(e) => updatePreferences('display', 'currency', e.target.value)}
                className="preference-select"
              >
                <option value="TWD">新台幣 (TWD)</option>
                <option value="USD">美元 (USD)</option>
                <option value="CNY">人民幣 (CNY)</option>
              </select>
            </div>
          </div>
        </section>

        {/* 交易設置 */}
        <section className="preference-section">
          <h3 className="section-title">
            <span className="section-icon">📊</span>
            交易設置
          </h3>
          <div className="preference-grid">
            <div className="preference-item">
              <label className="preference-label">預設分析類型</label>
              <select
                value={preferences.trading.defaultAnalysisType}
                onChange={(e) => updatePreferences('trading', 'defaultAnalysisType', e.target.value)}
                className="preference-select"
              >
                <option value="comprehensive">綜合分析</option>
                <option value="technical">技術分析</option>
                <option value="fundamental">基本面分析</option>
              </select>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">風險承受度</label>
              <select
                value={preferences.trading.riskTolerance}
                onChange={(e) => updatePreferences('trading', 'riskTolerance', e.target.value)}
                className="preference-select"
              >
                <option value="conservative">保守型</option>
                <option value="moderate">穩健型</option>
                <option value="aggressive">積極型</option>
              </select>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.trading.autoAnalysis}
                  onChange={(e) => updatePreferences('trading', 'autoAnalysis', e.target.checked)}
                />
                <span className="checkmark"></span>
                自動分析
              </label>
              <p className="preference-description">關注股票有重大變化時自動進行分析</p>
            </div>
          </div>
        </section>

        {/* 隱私設置 */}
        <section className="preference-section">
          <h3 className="section-title">
            <span className="section-icon">🔐</span>
            隱私設置
          </h3>
          <div className="preference-grid">
            <div className="preference-item">
              <label className="preference-label">個人資料可見性</label>
              <select
                value={preferences.privacy.profileVisibility}
                onChange={(e) => updatePreferences('privacy', 'profileVisibility', e.target.value)}
                className="preference-select"
              >
                <option value="private">私人</option>
                <option value="public">公開</option>
              </select>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.privacy.shareAnalytics}
                  onChange={(e) => updatePreferences('privacy', 'shareAnalytics', e.target.checked)}
                />
                <span className="checkmark"></span>
                分享使用數據
              </label>
              <p className="preference-description">幫助我們改善產品體驗</p>
            </div>
            
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={preferences.privacy.marketingEmails}
                  onChange={(e) => updatePreferences('privacy', 'marketingEmails', e.target.checked)}
                />
                <span className="checkmark"></span>
                行銷郵件
              </label>
              <p className="preference-description">接收產品更新和投資教育內容</p>
            </div>
          </div>
        </section>
      </div>

      {/* 保存按鈕 */}
      <div className="preferences-footer">
        <button
          type="button"
          className={`save-button ${saving ? 'saving' : ''} ${saved ? 'saved' : ''}`}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? (
            <>
              <span className="spinner"></span>
              儲存中...
            </>
          ) : saved ? (
            <>
              <span className="success-icon">✓</span>
              已儲存
            </>
          ) : (
            '儲存設置'
          )}
        </button>
      </div>
    </div>
  );
};
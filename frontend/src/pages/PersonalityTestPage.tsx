import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import './PersonalityTestPage.css';

// 投資人格測試頁面 - 遵循TradingAgents系統設計規範
// 整合Navigation組件，使用統一的設計語言

interface Question {
  id: string;
  scenario: string;
  question: string;
  options: Array<{
    text: string;
    index: number;
  }>;
}

interface TestResult {
  personality_type: {
    type: string;
    title: string;
    description: string;
    celebrity_comparison: string;
    characteristics: string[];
    investment_style: string;
  };
  dimension_scores: {
    risk_tolerance: number;
    emotional_control: number;
    analytical_thinking: number;
    market_sensitivity: number;
    long_term_vision: number;
  };
  percentile: number;
  recommendations: string[];
  share_content: {
    title: string;
    share_text: string;
    celebrity_comparison: string;
    percentile: number;
  };
  session_id: string;
}

interface User {
  id: string;
  name: string;
  email: string;
  tier: 'free' | 'gold' | 'diamond';
  avatar?: string;
}

const PersonalityTestPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<'intro' | 'testing' | 'result'>('intro');
  const [sessionId, setSessionId] = useState<string>('');
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [questionIndex, setQuestionIndex] = useState<number>(0);
  const [totalQuestions, setTotalQuestions] = useState<number>(8);
  const [progress, setProgress] = useState<number>(0);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [user, setUser] = useState<User | null>(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    // 模擬用戶信息獲取
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
      setUser(JSON.parse(userInfo));
    }
  }, []);

  const startTest = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/personality-test/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_info: {
            user_id: user?.id || `guest_${Date.now()}`,
            name: user?.name || 'Guest User',
            started_at: new Date().toISOString()
          }
        }),
      });

      if (!response.ok) {
        throw new Error('測試啟動失敗');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setTotalQuestions(data.total_questions);
      setQuestionIndex(0);
      setCurrentStep('testing');
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知錯誤');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (selectedOption: number) => {
    if (!currentQuestion || !sessionId) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/personality-test/submit-answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: currentQuestion.id,
          selected_option: selectedOption,
        }),
      });

      if (!response.ok) {
        throw new Error('答案提交失敗');
      }

      const data = await response.json();
      
      if (data.completed) {
        setTestResult(data.result);
        setCurrentStep('result');
      } else {
        setCurrentQuestion(data.question);
        setQuestionIndex(data.current_question);
        setProgress(data.progress || 0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知錯誤');
    } finally {
      setLoading(false);
    }
  };

  const restartTest = () => {
    setCurrentStep('intro');
    setSessionId('');
    setCurrentQuestion(null);
    setQuestionIndex(0);
    setProgress(0);
    setTestResult(null);
    setError('');
  };

  const shareResult = () => {
    if (!testResult) return;
    
    const shareText = `${testResult.share_content.share_text}\n\n我的投資人格測試結果：\n${testResult.personality_type.title}\n擊敗了${testResult.percentile.toFixed(1)}%的投資者！\n\n立即測試你的投資人格：${window.location.href}`;
    
    if (navigator.share) {
      navigator.share({
        title: '我的投資人格測試結果',
        text: shareText,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(shareText);
      alert('結果已複製到剪貼板！');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    setUser(null);
    navigate('/');
  };

  const renderIntro = () => (
    <div className="page-container">
      <div className="section-container">
        <div className="intro-header">
          <h1 className="page-title">
            <span className="title-icon">🧠</span>
            投資人格測試
          </h1>
          <p className="page-subtitle">發現你的投資風格，成為更好的投資者</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3 className="feature-title">5維度分析</h3>
            <p className="feature-description">
              全面評估風險承受度、情緒控制、分析思維、市場敏感度和長期視野
            </p>
          </div>
          <div className="feature-card highlight">
            <div className="feature-icon">🎯</div>
            <h3 className="feature-title">6種人格類型</h3>
            <p className="feature-description">
              冷血獵手、智慧長者、敏感雷達、勇敢戰士、謹慎守護者、情緒過山車
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💡</div>
            <h3 className="feature-title">個性化建議</h3>
            <p className="feature-description">
              基於你的人格類型，提供專業的投資策略和風險管理建議
            </p>
          </div>
        </div>

        <div className="test-info-card">
          <div className="info-grid">
            <div className="info-item">
              <span className="info-icon">⏱️</span>
              <div className="info-content">
                <span className="info-label">測試時間</span>
                <span className="info-value">約3-5分鐘</span>
              </div>
            </div>
            <div className="info-item">
              <span className="info-icon">❓</span>
              <div className="info-content">
                <span className="info-label">問題數量</span>
                <span className="info-value">8個情境問題</span>
              </div>
            </div>
            <div className="info-item">
              <span className="info-icon">🎯</span>
              <div className="info-content">
                <span className="info-label">結果準確性</span>
                <span className="info-value">基於心理學原理</span>
              </div>
            </div>
          </div>
        </div>

        <div className="action-section">
          <button 
            className="cta-button primary large"
            onClick={startTest}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                準備中...
              </>
            ) : (
              <>
                開始測試
                <span className="button-icon">🚀</span>
              </>
            )}
          </button>

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderTesting = () => (
    <div className="page-container">
      <div className="section-container">
        <div className="test-header">
          <div className="progress-section">
            <div className="progress-info">
              <span className="progress-text">
                問題 {questionIndex + 1} / {totalQuestions}
              </span>
              <span className="progress-percentage">
                {Math.round(((questionIndex + 1) / totalQuestions) * 100)}%
              </span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${((questionIndex + 1) / totalQuestions) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {currentQuestion && (
          <div className="question-card">
            <div className="scenario-section">
              <div className="scenario-header">
                <span className="scenario-icon">📈</span>
                <h3 className="scenario-title">投資情境</h3>
              </div>
              <p className="scenario-text">{currentQuestion.scenario}</p>
            </div>

            <div className="question-section">
              <h4 className="question-title">{currentQuestion.question}</h4>
              
              <div className="options-grid">
                {currentQuestion.options.map((option) => (
                  <button
                    key={option.index}
                    className="option-button"
                    onClick={() => submitAnswer(option.index)}
                    disabled={loading}
                  >
                    <span className="option-letter">
                      {String.fromCharCode(65 + option.index)}
                    </span>
                    <span className="option-text">{option.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="loading-content">
              <div className="loading-spinner large"></div>
              <p className="loading-text">正在分析您的答案...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}
      </div>
    </div>
  );

  const renderResult = () => {
    if (!testResult) return null;

    const dimensionLabels = {
      risk_tolerance: '風險承受度',
      emotional_control: '情緒控制',
      analytical_thinking: '分析思維',
      market_sensitivity: '市場敏感度',
      long_term_vision: '長期視野'
    };

    return (
      <div className="page-container">
        <div className="section-container">
          <div className="result-header">
            <div className="personality-badge">
              <div className="badge-icon">🎯</div>
              <h1 className="personality-title">{testResult.personality_type.title}</h1>
              <p className="personality-type">{testResult.personality_type.type}</p>
            </div>
            
            <div className="percentile-card">
              <div className="percentile-circle">
                <span className="percentile-number">{testResult.percentile.toFixed(0)}</span>
                <span className="percentile-symbol">%</span>
              </div>
              <p className="percentile-text">擊敗了其他投資者</p>
            </div>
          </div>

          <div className="result-content">
            <div className="description-card">
              <h3 className="card-title">
                <span className="title-icon">🎯</span>
                人格特徵
              </h3>
              <p className="description-text">{testResult.personality_type.description}</p>
              
              <div className="info-section">
                <h4 className="info-title">
                  <span className="info-icon">💫</span>
                  名人對比
                </h4>
                <p className="info-text">{testResult.personality_type.celebrity_comparison}</p>
              </div>

              <div className="info-section">
                <h4 className="info-title">
                  <span className="info-icon">📊</span>
                  投資風格
                </h4>
                <p className="info-text">{testResult.personality_type.investment_style}</p>
              </div>

              <div className="characteristics-section">
                <h4 className="info-title">
                  <span className="info-icon">✨</span>
                  核心特質
                </h4>
                <div className="characteristics-grid">
                  {testResult.personality_type.characteristics.map((char, index) => (
                    <div key={index} className="characteristic-tag">
                      {char}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="scores-card">
              <h3 className="card-title">
                <span className="title-icon">📈</span>
                維度分析
              </h3>
              <div className="scores-grid">
                {Object.entries(testResult.dimension_scores).map(([key, score]) => (
                  <div key={key} className="score-item">
                    <div className="score-header">
                      <span className="score-label">
                        {dimensionLabels[key as keyof typeof dimensionLabels]}
                      </span>
                      <span className="score-value">{score.toFixed(0)}</span>
                    </div>
                    <div className="score-bar">
                      <div 
                        className="score-fill" 
                        style={{ width: `${score}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="recommendations-card">
              <h3 className="card-title">
                <span className="title-icon">💡</span>
                個性化建議
              </h3>
              <div className="recommendations-list">
                {testResult.recommendations.map((recommendation, index) => (
                  <div key={index} className="recommendation-item">
                    <span className="recommendation-number">{index + 1}</span>
                    <span className="recommendation-text">{recommendation}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="result-actions">
            <button className="cta-button primary" onClick={shareResult}>
              <span className="button-icon">📤</span>
              分享結果
            </button>
            <button className="cta-button secondary" onClick={restartTest}>
              <span className="button-icon">🔄</span>
              重新測試
            </button>
            <button 
              className="cta-button secondary" 
              onClick={() => navigate('/dashboard')}
            >
              <span className="button-icon">🏠</span>
              返回儀表板
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="personality-test-page">
      <Navigation user={user} onLogout={handleLogout} />
      
      <main className="main-content">
        {currentStep === 'intro' && renderIntro()}
        {currentStep === 'testing' && renderTesting()}
        {currentStep === 'result' && renderResult()}
      </main>
    </div>
  );
};

export default PersonalityTestPage;
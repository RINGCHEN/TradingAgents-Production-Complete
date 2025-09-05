import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { AnalyticsService } from '../services/AnalyticsService';
import { personalityTestAPI, handleAPIError, PersonalityTestQuestion } from '../services/PersonalityTestAPI';
import { UTMParams } from '../PersonalityTestApp';
import './TestQuestionPage.css';

interface TestQuestionPageProps {
  analytics: AnalyticsService;
  utm_params?: UTMParams;
}

interface LocationState {
  sessionId: string;
  currentQuestion: PersonalityTestQuestion;
  totalQuestions: number;
  questionIndex: number;
}

const TestQuestionPage: React.FC<TestQuestionPageProps> = ({ analytics, utm_params }) => {
  const navigate = useNavigate();
  const { questionId } = useParams<{ questionId: string }>();
  const location = useLocation();
  const state = location.state as LocationState;

  const [sessionId] = useState<string>(state?.sessionId || '');
  const [currentQuestion] = useState<PersonalityTestQuestion | null>(
    state?.currentQuestion || null
  );
  const [totalQuestions] = useState<number>(state?.totalQuestions || 8);
  const [questionIndex] = useState<number>(state?.questionIndex || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  useEffect(() => {
    // 追蹤頁面瀏覽
    analytics.trackPageView('test_question', {
      question_id: questionId,
      question_index: questionIndex,
      session_id: sessionId,
      utm_params
    });

    // 如果沒有狀態數據，嘗試重新獲取
    if (!sessionId || !currentQuestion) {
      // 重定向到測試開始頁面
      navigate('/start', { replace: true });
    }
  }, [analytics, questionId, questionIndex, sessionId, currentQuestion, utm_params, navigate]);

  const handleOptionSelect = (optionIndex: number) => {
    setSelectedOption(optionIndex);
    
    // 追蹤選項選擇
    analytics.track('question_option_selected', {
      question_id: questionId,
      question_index: questionIndex,
      selected_option: optionIndex,
      session_id: sessionId,
      utm_params
    });
  };

  const handleSubmitAnswer = async () => {
    if (selectedOption === null || !currentQuestion || !sessionId) return;

    setIsLoading(true);
    setError('');

    try {
      // 追蹤答案提交
      analytics.track('question_answer_submitted', {
        question_id: currentQuestion.id,
        question_index: questionIndex,
        selected_option: selectedOption,
        session_id: sessionId,
        utm_params
      });

      const response = await personalityTestAPI.submitAnswer(
        sessionId,
        currentQuestion.id,
        selectedOption
      );

      if (response.completed && response.result) {
        // 測試完成，追蹤完成事件
        analytics.track('test_completed', {
          session_id: sessionId,
          total_questions: totalQuestions,
          completion_time: Date.now(),
          personality_type: response.result.personality_type.type,
          utm_params
        });

        // 導航到結果頁面
        navigate(`/result/${sessionId}`, {
          state: {
            result: response.result,
            sessionId: sessionId
          }
        });
      } else if (response.question) {
        // 還有下一個問題
        const nextQuestionIndex = questionIndex + 1;
        
        analytics.track('question_progressed', {
          from_question_id: currentQuestion.id,
          to_question_id: response.question.id,
          question_index: nextQuestionIndex,
          progress: response.progress,
          session_id: sessionId,
          utm_params
        });

        // 導航到下一個問題
        navigate(`/question/${response.question.id}`, {
          state: {
            sessionId: sessionId,
            currentQuestion: response.question,
            totalQuestions: totalQuestions,
            questionIndex: nextQuestionIndex
          },
          replace: true
        });
      }

    } catch (err) {
      const errorMessage = handleAPIError(err);
      setError(errorMessage);
      
      analytics.trackError(new Error(errorMessage), {
        context: 'question_submit',
        question_id: currentQuestion.id,
        session_id: sessionId,
        utm_params
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToPrevious = () => {
    if (questionIndex > 0) {
      analytics.track('question_back_clicked', {
        question_id: questionId,
        question_index: questionIndex,
        session_id: sessionId,
        utm_params
      });
      
      // 這裡可以實現返回上一題的邏輯
      // 目前簡化為返回測試開始頁面
      navigate('/start');
    }
  };

  const handleExitTest = () => {
    analytics.track('test_exit_clicked', {
      question_id: questionId,
      question_index: questionIndex,
      session_id: sessionId,
      utm_params
    });

    if (window.confirm('確定要退出測試嗎？您的進度將會丟失。')) {
      analytics.track('test_exited', {
        question_id: questionId,
        question_index: questionIndex,
        session_id: sessionId,
        utm_params
      });
      
      navigate('/', { replace: true });
    }
  };

  if (!currentQuestion || !sessionId) {
    return (
      <div className="test-question-page">
        <div className="page-container">
          <div className="section-container">
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p className="loading-text">載入測試問題中...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const progress = ((questionIndex + 1) / totalQuestions) * 100;

  return (
    <div className="test-question-page">
      <div className="page-container">
        <div className="section-container">
          {/* 測試標題和進度 */}
          <header className="question-header">
            <div className="header-controls">
              <button 
                type="button"
                className="back-button"
                onClick={handleBackToPrevious}
                disabled={isLoading || questionIndex === 0}
              >
                <span className="back-icon">←</span>
                上一題
              </button>
              
              <button 
                type="button"
                className="exit-button"
                onClick={handleExitTest}
                disabled={isLoading}
              >
                <span className="exit-icon">✕</span>
                退出測試
              </button>
            </div>

            <div className="progress-section">
              <div className="progress-info">
                <span className="progress-text">
                  問題 {questionIndex + 1} / {totalQuestions}
                </span>
                <span className="progress-percentage">
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          </header>

          {/* 問題內容 */}
          <section className="question-content">
            <div className="question-card">
              {/* 情境描述 */}
              <div className="scenario-section">
                <div className="scenario-header">
                  <span className="scenario-icon">📈</span>
                  <h3 className="scenario-title">投資情境</h3>
                </div>
                <p className="scenario-text">{currentQuestion.scenario}</p>
              </div>

              {/* 問題 */}
              <div className="question-section">
                <h4 className="question-title">{currentQuestion.question}</h4>
                
                {/* 選項 */}
                <div className="options-container">
                  {currentQuestion.options.map((option) => (
                    <button
                      key={option.index}
                      type="button"
                      className={`option-button ${selectedOption === option.index ? 'selected' : ''}`}
                      onClick={() => handleOptionSelect(option.index)}
                      disabled={isLoading}
                    >
                      <span className="option-letter">
                        {String.fromCharCode(65 + option.index)}
                      </span>
                      <span className="option-text">{option.text}</span>
                      {selectedOption === option.index && (
                        <span className="option-check">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* 提交按鈕 */}
          <section className="submit-section">
            <button 
              type="button"
              className="submit-button"
              onClick={handleSubmitAnswer}
              disabled={isLoading || selectedOption === null}
            >
              {isLoading ? (
                <>
                  <span className="loading-spinner"></span>
                  提交中...
                </>
              ) : questionIndex === totalQuestions - 1 ? (
                <>
                  完成測試
                  <span className="button-icon">🎯</span>
                </>
              ) : (
                <>
                  下一題
                  <span className="button-icon">→</span>
                </>
              )}
            </button>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
          </section>

          {/* 測試提示 */}
          <section className="test-hints">
            <div className="hints-card">
              <h5 className="hints-title">
                <span className="hints-icon">💡</span>
                答題提示
              </h5>
              <ul className="hints-list">
                <li>請根據您的直覺和真實想法選擇</li>
                <li>沒有標準答案，每個選項都有其意義</li>
                <li>請誠實回答，這樣結果會更準確</li>
              </ul>
            </div>
          </section>
        </div>
      </div>

      {/* 載入覆蓋層 */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="loading-spinner large"></div>
            <p className="loading-text">正在處理您的答案...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestQuestionPage;
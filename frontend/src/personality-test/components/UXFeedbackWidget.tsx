import React, { useState } from 'react';
import { userExperienceService } from '../services/UserExperienceService';
import './UXFeedbackWidget.css';

interface UXFeedbackWidgetProps {
  page: string;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}

const UXFeedbackWidget: React.FC<UXFeedbackWidgetProps> = ({ 
  page, 
  position = 'bottom-right' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'rating' | 'comment' | 'bug_report'>('rating');
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // 收集反饋
      userExperienceService.collectFeedback({
        type: feedbackType,
        content: comment || `Rating: ${rating}/5`,
        rating: feedbackType === 'rating' ? rating : undefined,
        page
      });

      // 追蹤反饋提交
      userExperienceService.trackInteraction({
        type: 'click',
        element: 'feedback_submit',
        timestamp: Date.now(),
        value: `${feedbackType}:${rating || comment.length}`
      });

      setIsSubmitted(true);
      setTimeout(() => {
        setIsOpen(false);
        setIsSubmitted(false);
        setRating(0);
        setComment('');
      }, 2000);

    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    
    userExperienceService.trackInteraction({
      type: 'click',
      element: 'feedback_widget_toggle',
      timestamp: Date.now(),
      value: isOpen ? 'close' : 'open'
    });
  };

  if (isSubmitted) {
    return (
      <div className={`ux-feedback-widget ${position} submitted`}>
        <div className="feedback-success">
          <span className="success-icon">✅</span>
          <span>感謝您的反饋！</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`ux-feedback-widget ${position} ${isOpen ? 'open' : ''}`}>
      {!isOpen ? (
        <button 
          className="feedback-toggle"
          onClick={handleToggle}
          aria-label="提供反饋"
        >
          💬
        </button>
      ) : (
        <div className="feedback-panel">
          <div className="feedback-header">
            <h3>您的體驗如何？</h3>
            <button 
              className="close-button"
              onClick={handleToggle}
              aria-label="關閉反饋"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="feedback-form">
            <div className="feedback-type-selector">
              <button
                type="button"
                className={feedbackType === 'rating' ? 'active' : ''}
                onClick={() => setFeedbackType('rating')}
              >
                評分
              </button>
              <button
                type="button"
                className={feedbackType === 'comment' ? 'active' : ''}
                onClick={() => setFeedbackType('comment')}
              >
                建議
              </button>
              <button
                type="button"
                className={feedbackType === 'bug_report' ? 'active' : ''}
                onClick={() => setFeedbackType('bug_report')}
              >
                問題回報
              </button>
            </div>

            {feedbackType === 'rating' && (
              <div className="rating-section">
                <p>請為此頁面評分：</p>
                <div className="star-rating">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      className={`star ${star <= rating ? 'active' : ''}`}
                      onClick={() => setRating(star)}
                      aria-label={`${star} 星`}
                    >
                      ⭐
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="comment-section">
              <textarea
                value={comment}
                onChange={(e: any) => setComment(e.target.value)}
                placeholder={
                  feedbackType === 'rating' 
                    ? '可選：告訴我們更多詳情...'
                    : feedbackType === 'comment'
                    ? '請分享您的建議...'
                    : '請描述您遇到的問題...'
                }
                rows={3}
                maxLength={500}
              />
              <div className="character-count">
                {comment.length}/500
              </div>
            </div>

            <div className="feedback-actions">
              <button
                type="submit"
                disabled={
                  isSubmitting || 
                  (feedbackType === 'rating' && rating === 0) ||
                  (feedbackType !== 'rating' && comment.trim().length === 0)
                }
                className="submit-button"
              >
                {isSubmitting ? '提交中...' : '提交反饋'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default UXFeedbackWidget;
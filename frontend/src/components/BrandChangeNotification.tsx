import React, { useState, useEffect } from 'react';
import BrandConfigManager from '../utils/BrandConfig';

interface BrandChangeNotificationProps {
  onDismiss?: () => void;
  showInitialNotification?: boolean;
}

/**
 * 品牌變更用戶通知組件
 * 向用戶說明從 TradingAgents 更名為不老傳說
 */
const BrandChangeNotification: React.FC<BrandChangeNotificationProps> = ({ 
  onDismiss, 
  showInitialNotification = true 
}) => {
  const [isVisible, setIsVisible] = useState(showInitialNotification);
  const [hasBeenDismissed, setHasBeenDismissed] = useState(false);

  useEffect(() => {
    // 檢查用戶是否已經看過通知
    const dismissed = localStorage.getItem('brand_change_notification_dismissed');
    if (dismissed === 'true') {
      setHasBeenDismissed(true);
      setIsVisible(false);
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    setHasBeenDismissed(true);
    localStorage.setItem('brand_change_notification_dismissed', 'true');
    localStorage.setItem('brand_change_notification_date', new Date().toISOString());
    if (onDismiss) onDismiss();
  };

  const handleLearnMore = () => {
    // 可以導向詳細說明頁面或FAQ
    window.open('/brand-change-info', '_blank');
  };

  if (!isVisible || hasBeenDismissed) {
    return null;
  }

  return (
    <div className="brand-change-notification">
      <div className="notification-overlay">
        <div className="notification-modal">
          <div className="notification-header">
            <div className="brand-transition">
              <div className="old-brand">TradingAgents</div>
              <div className="arrow">→</div>
              <div className="new-brand">不老傳說</div>
            </div>
            <h2>品牌全新升級！</h2>
          </div>
          
          <div className="notification-content">
            <div className="welcome-message">
              <h3>歡迎體驗全新的{BrandConfigManager.getBrandName()}！</h3>
              <p>
                我們很高興地宣布，TradingAgents 正式更名為<strong>「不老傳說」</strong>！
                這個全新品牌代表著我們對提供永續、卓越投資分析服務的承諾。
              </p>
            </div>

            <div className="key-points">
              <h4>重要變更說明：</h4>
              <ul>
                <li>
                  <span className="icon">🏷️</span>
                  <strong>品牌名稱</strong>：從 TradingAgents 更名為「不老傳說」
                </li>
                <li>
                  <span className="icon">🔧</span>
                  <strong>功能服務</strong>：所有原有功能保持不變，持續為您提供專業AI投資分析
                </li>
                <li>
                  <span className="icon">👤</span>
                  <strong>用戶帳戶</strong>：您的帳戶、數據和設定完全不受影響
                </li>
                <li>
                  <span className="icon">📈</span>
                  <strong>分析師團隊</strong>：7位專業AI分析師繼續為您服務
                </li>
                <li>
                  <span className="icon">🛡️</span>
                  <strong>安全保障</strong>：所有安全措施和隱私保護維持不變
                </li>
              </ul>
            </div>

            <div className="brand-philosophy">
              <h4>「不老傳說」的品牌理念：</h4>
              <p>
                象徵著<strong>永恆的智慧</strong>和<strong>傳奇的成就</strong>，
                我們致力於為每位投資者創造不朽的投資傳奇，
                讓您的財富增值之路成為一段精彩的不老傳說。
              </p>
            </div>

            <div className="assurance">
              <div className="assurance-item">
                <span className="check">✓</span>
                <span>相同的專業團隊</span>
              </div>
              <div className="assurance-item">
                <span className="check">✓</span>
                <span>相同的優質服務</span>
              </div>
              <div className="assurance-item">
                <span className="check">✓</span>
                <span>更好的用戶體驗</span>
              </div>
            </div>
          </div>

          <div className="notification-footer">
            <div className="action-buttons">
              <button 
                className="btn btn-secondary"
                onClick={handleLearnMore}
              >
                了解更多
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleDismiss}
              >
                開始體驗
              </button>
            </div>
            
            <div className="contact-info">
              <p>
                如有任何疑問，請聯繫客服：
                <a href="mailto:support@bulao-chuanshuo.com">support@bulao-chuanshuo.com</a>
              </p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .brand-change-notification {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 10000;
        }

        .notification-overlay {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.8);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .notification-modal {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 20px;
          max-width: 600px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          color: white;
          position: relative;
          animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .notification-header {
          text-align: center;
          padding: 30px 30px 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .brand-transition {
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 20px;
          font-size: 18px;
          font-weight: 600;
        }

        .old-brand {
          color: #ffcccb;
          text-decoration: line-through;
        }

        .arrow {
          margin: 0 20px;
          font-size: 24px;
          color: #ffd700;
        }

        .new-brand {
          color: #ffd700;
          font-weight: bold;
          text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .notification-header h2 {
          margin: 0;
          font-size: 28px;
          background: linear-gradient(45deg, #ffd700, #ffed4e);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .notification-content {
          padding: 30px;
        }

        .welcome-message h3 {
          color: #ffd700;
          margin-bottom: 15px;
          font-size: 22px;
        }

        .welcome-message p {
          line-height: 1.6;
          margin-bottom: 25px;
          font-size: 16px;
        }

        .key-points h4 {
          color: #ffd700;
          margin-bottom: 15px;
          font-size: 18px;
        }

        .key-points ul {
          list-style: none;
          padding: 0;
          margin-bottom: 25px;
        }

        .key-points li {
          display: flex;
          align-items: flex-start;
          margin-bottom: 12px;
          padding: 10px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          font-size: 14px;
          line-height: 1.4;
        }

        .key-points .icon {
          margin-right: 10px;
          font-size: 16px;
        }

        .brand-philosophy h4 {
          color: #ffd700;
          margin-bottom: 15px;
          font-size: 18px;
        }

        .brand-philosophy p {
          line-height: 1.6;
          margin-bottom: 25px;
          font-size: 16px;
          font-style: italic;
          background: rgba(255, 255, 255, 0.1);
          padding: 15px;
          border-radius: 8px;
          border-left: 4px solid #ffd700;
        }

        .assurance {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 10px;
          margin-bottom: 25px;
        }

        .assurance-item {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.15);
          border-radius: 20px;
          font-size: 14px;
        }

        .check {
          color: #4ade80;
          font-weight: bold;
          margin-right: 8px;
        }

        .notification-footer {
          padding: 0 30px 30px;
          text-align: center;
        }

        .action-buttons {
          display: flex;
          gap: 15px;
          justify-content: center;
          margin-bottom: 20px;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 25px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-decoration: none;
        }

        .btn-primary {
          background: linear-gradient(45deg, #ffd700, #ffed4e);
          color: #333;
        }

        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.2);
          color: white;
          border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
        }

        .contact-info {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.8);
        }

        .contact-info a {
          color: #ffd700;
          text-decoration: none;
        }

        .contact-info a:hover {
          text-decoration: underline;
        }

        @media (max-width: 768px) {
          .notification-modal {
            margin: 10px;
            max-height: 95vh;
          }
          
          .notification-header {
            padding: 20px 20px 15px;
          }
          
          .notification-content {
            padding: 20px;
          }
          
          .notification-footer {
            padding: 0 20px 20px;
          }
          
          .brand-transition {
            font-size: 16px;
          }
          
          .notification-header h2 {
            font-size: 24px;
          }
          
          .action-buttons {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default BrandChangeNotification;
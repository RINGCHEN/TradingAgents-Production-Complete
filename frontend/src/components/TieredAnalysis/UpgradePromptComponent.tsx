import React from 'react';

/**
 * 結構化升級提示組件 - 支援GEMINI新的upgrade_prompt格式
 * 同時保持向下兼容舊的字符串格式
 */

interface UpgradePromptData {
  title: string;
  value_prop: string;
  cta: string;
}

interface UpgradePromptComponentProps {
  upgradePrompt?: string | UpgradePromptData;
  userTier?: 'visitor' | 'trial' | 'free' | 'paid';
  className?: string;
  onUpgradeClick?: () => void;
}

const UpgradePromptComponent: React.FC<UpgradePromptComponentProps> = ({
  upgradePrompt,
  userTier = 'free',
  className = '',
  onUpgradeClick
}) => {
  // 如果沒有升級提示或者是付費用戶，不顯示
  if (!upgradePrompt || userTier === 'paid') {
    return null;
  }

  // 處理舊格式的字符串升級提示
  const getPromptData = (): UpgradePromptData => {
    if (typeof upgradePrompt === 'string') {
      // 向下兼容：將字符串轉換為結構化格式
      return {
        title: userTier === 'visitor' ? '體驗完整功能' : '解鎖專業分析',
        value_prop: upgradePrompt,
        cta: userTier === 'visitor' ? '立即註冊' : '立即升級'
      };
    } else {
      // 新的結構化格式
      return upgradePrompt;
    }
  };

  const promptData = getPromptData();

  const handleUpgradeClick = () => {
    if (onUpgradeClick) {
      onUpgradeClick();
    } else {
      // 默認行為：跳轉到對應頁面
      if (userTier === 'visitor') {
        window.location.href = '/auth';
      } else {
        window.location.href = '/pricing';
      }
    }
  };

  // 根據用戶層級確定樣式主題
  const getThemeClass = (): string => {
    const themes = {
      visitor: 'visitor-theme',
      trial: 'trial-theme', 
      free: 'free-theme',
      paid: 'paid-theme'
    };
    return themes[userTier] || themes.free;
  };

  return (
    <div className={`upgrade-prompt-component ${getThemeClass()} ${className}`}>
      <div className="upgrade-content">
        {/* 主標題 */}
        <h4 className="upgrade-title">
          <span className="upgrade-icon">🚀</span>
          {promptData.title}
        </h4>

        {/* 價值主張 */}
        <p className="upgrade-value-prop">
          {promptData.value_prop}
        </p>

        {/* 升級福利列表 */}
        <div className="upgrade-benefits">
          <p className="benefits-title">升級後您將獲得:</p>
          <ul className="benefits-list">
            {userTier === 'visitor' ? (
              <>
                <li>✅ 7天完整功能免費體驗</li>
                <li>✅ 無限次AI分析查詢</li>
                <li>✅ 專業投資建議推薦</li>
                <li>✅ 個人化投資組合</li>
              </>
            ) : (
              <>
                <li>✅ 明確買賣建議 (買入/賣出/持有)</li>
                <li>✅ AI信心度評分</li>
                <li>✅ 具體目標價位</li>
                <li>✅ 詳細投資推理</li>
              </>
            )}
          </ul>
        </div>

        {/* 行動按鈕 */}
        <button 
          className="upgrade-cta-button"
          onClick={handleUpgradeClick}
          type="button"
        >
          <span className="cta-icon">
            {userTier === 'visitor' ? '🎁' : '💎'}
          </span>
          {promptData.cta}
        </button>

        {/* 額外說明 */}
        {userTier === 'visitor' && (
          <p className="additional-note">
            💡 註冊即可免費體驗所有功能7天，無需信用卡
          </p>
        )}

        {userTier === 'free' && (
          <p className="additional-note">
            💡 升級後享受無限制專業投資分析服務
          </p>
        )}
      </div>
    </div>
  );
};

export default UpgradePromptComponent;
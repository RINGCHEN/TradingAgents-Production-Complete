import React, { useState } from 'react';
import { PersonalityTestAPI } from '../services/PersonalityTestAPI';
import { userExperienceService } from '../services/UserExperienceService';
import './SocialShareButtons.css';

interface SocialShareButtonsProps {
  shareData: {
    image_url: string;
    share_text: string;
    share_url: string;
    result_id: string;
  };
  onShareComplete?: (platform: string, success: boolean) => void;
  showLabels?: boolean;
  size?: 'small' | 'medium' | 'large';
  layout?: 'horizontal' | 'vertical' | 'grid';
}

interface SharePlatform {
  id: string;
  name: string;
  icon: string;
  color: string;
  shareUrl: (data: any) => string;
}

const SocialShareButtons: React.FC<SocialShareButtonsProps> = ({
  shareData,
  onShareComplete,
  showLabels = true,
  size = 'medium',
  layout = 'horizontal'
}) => {
  const [isSharing, setIsSharing] = useState<string>('');
  const [shareStats, setShareStats] = useState<Record<string, number>>({});

  // 定義支援的社交平台
  const platforms: SharePlatform[] = [
    {
      id: 'facebook',
      name: 'Facebook',
      icon: '📘',
      color: '#1877f2',
      shareUrl: (data) => {
        const params = new URLSearchParams({
          u: `${window.location.origin}${data.share_url}`,
          quote: data.share_text
        });
        return `https://www.facebook.com/sharer/sharer.php?${params.toString()}`;
      }
    },
    {
      id: 'twitter',
      name: 'Twitter',
      icon: '🐦',
      color: '#1da1f2',
      shareUrl: (data) => {
        const params = new URLSearchParams({
          text: data.share_text,
          url: `${window.location.origin}${data.share_url}`,
          hashtags: '投資人格測試,投資理財'
        });
        return `https://twitter.com/intent/tweet?${params.toString()}`;
      }
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: '💼',
      color: '#0077b5',
      shareUrl: (data) => {
        const params = new URLSearchParams({
          url: `${window.location.origin}${data.share_url}`,
          title: '我的投資人格測試結果',
          summary: data.share_text
        });
        return `https://www.linkedin.com/sharing/share-offsite/?${params.toString()}`;
      }
    },
    {
      id: 'line',
      name: 'Line',
      icon: '💬',
      color: '#00c300',
      shareUrl: (data) => {
        const message = `${data.share_text} ${window.location.origin}${data.share_url}`;
        const params = new URLSearchParams({
          text: message
        });
        return `https://social-plugins.line.me/lineit/share?${params.toString()}`;
      }
    },
    {
      id: 'copy',
      name: '複製連結',
      icon: '🔗',
      color: '#6b7280',
      shareUrl: () => '' // 特殊處理
    },
    {
      id: 'download',
      name: '下載圖片',
      icon: '📥',
      color: '#059669',
      shareUrl: () => '' // 特殊處理
    }
  ];

  const handleShare = async (platform: SharePlatform) => {
    setIsSharing(platform.id);

    try {
      // 追蹤分享意圖
      userExperienceService.trackInteraction({
        type: 'click',
        element: `share_button_${platform.id}`,
        timestamp: Date.now()
      });

      let success = false;

      if (platform.id === 'copy') {
        success = await handleCopyLink();
      } else if (platform.id === 'download') {
        success = await handleDownloadImage();
      } else {
        success = await handleSocialShare(platform);
      }

      // 記錄分享行為到後端
      if (success) {
        await trackShareAction(platform.id);
        
        // 更新本地統計
        setShareStats(prev => ({
          ...prev,
          [platform.id]: (prev[platform.id] || 0) + 1
        }));
      }

      onShareComplete?.(platform.id, success);

    } catch (error) {
      console.error(`Failed to share to ${platform.name}:`, error);
      onShareComplete?.(platform.id, false);
    } finally {
      setIsSharing('');
    }
  };

  const handleSocialShare = async (platform: SharePlatform): Promise<boolean> => {
    try {
      const shareUrl = platform.shareUrl(shareData);
      
      // 檢查是否支援 Web Share API (主要用於移動設備)
      if (navigator.share && platform.id !== 'copy' && platform.id !== 'download') {
        try {
          await navigator.share({
            title: '我的投資人格測試結果',
            text: shareData.share_text,
            url: `${window.location.origin}${shareData.share_url}`
          });
          return true;
        } catch (shareError) {
          // 如果用戶取消分享，fallback 到傳統方式
          if (shareError instanceof Error && shareError.name !== 'AbortError') {
            console.log('Web Share API failed, using fallback');
          }
        }
      }

      // 傳統的彈窗分享方式
      const popup = window.open(
        shareUrl,
        `share-${platform.id}`,
        'width=600,height=400,scrollbars=yes,resizable=yes'
      );

      if (popup) {
        // 監聽彈窗關閉（簡化版本）
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed);
          }
        }, 1000);

        return true;
      }

      return false;

    } catch (error) {
      console.error(`Failed to open share popup for ${platform.name}:`, error);
      return false;
    }
  };

  const handleCopyLink = async (): Promise<boolean> => {
    try {
      const fullUrl = `${window.location.origin}${shareData.share_url}`;
      
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(fullUrl);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = fullUrl;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }

      // 顯示複製成功提示
      showToast('連結已複製到剪貼板！', 'success');
      return true;

    } catch (error) {
      console.error('Failed to copy link:', error);
      showToast('複製連結失敗', 'error');
      return false;
    }
  };

  const handleDownloadImage = async (): Promise<boolean> => {
    try {
      const response = await fetch(shareData.image_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `投資人格測試結果-${shareData.result_id}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(url);
      showToast('圖片下載成功！', 'success');
      return true;

    } catch (error) {
      console.error('Failed to download image:', error);
      showToast('圖片下載失敗', 'error');
      return false;
    }
  };

  const trackShareAction = async (platform: string) => {
    try {
      const api = new PersonalityTestAPI();
      await api.request('/api/share/track-action', 'POST', {
        result_id: shareData.result_id,
        platform: platform,
        share_text: shareData.share_text,
        share_url: shareData.share_url,
        user_agent: navigator.userAgent,
        referrer: document.referrer
      });
    } catch (error) {
      console.error('Failed to track share action:', error);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    // 簡單的 toast 通知實現
    const toast = document.createElement('div');
    toast.className = `share-toast ${type}`;
    toast.textContent = message;
    
    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 20px',
      borderRadius: '6px',
      color: 'white',
      backgroundColor: type === 'success' ? '#22c55e' : '#ef4444',
      zIndex: '10000',
      fontSize: '14px',
      fontWeight: '500',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      animation: 'slideInRight 0.3s ease-out'
    });

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 3000);
  };

  return (
    <div className={`social-share-buttons ${layout} ${size}`}>
      <div className="share-buttons-container">
        {platforms.map((platform) => (
          <button
            key={platform.id}
            className={`share-button ${platform.id} ${isSharing === platform.id ? 'sharing' : ''}`}
            onClick={() => handleShare(platform)}
            disabled={isSharing !== ''}
            style={{ '--platform-color': platform.color } as React.CSSProperties}
            title={`分享到 ${platform.name}`}
          >
            <span className="button-icon">{platform.icon}</span>
            {showLabels && (
              <span className="button-label">{platform.name}</span>
            )}
            {isSharing === platform.id && (
              <span className="sharing-spinner"></span>
            )}
            {shareStats[platform.id] && (
              <span className="share-count">{shareStats[platform.id]}</span>
            )}
          </button>
        ))}
      </div>

      {/* 分享統計 */}
      {Object.keys(shareStats).length > 0 && (
        <div className="share-stats">
          <span className="stats-label">
            已分享 {Object.values(shareStats).reduce((a, b) => a + b, 0)} 次
          </span>
        </div>
      )}
    </div>
  );
};

export default SocialShareButtons;
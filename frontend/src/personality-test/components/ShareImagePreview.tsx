import React, { useState, useEffect } from 'react';
import { PersonalityTestAPI } from '../services/PersonalityTestAPI';
import './ShareImagePreview.css';

interface ShareImagePreviewProps {
  resultId: string;
  templateId?: string;
  onImageGenerated?: (imageData: any) => void;
  onError?: (error: string) => void;
}

interface ShareImageData {
  image_url: string;
  share_text: string;
  share_url: string;
  template_id: string;
  created_at: string;
}

const ShareImagePreview: React.FC<ShareImagePreviewProps> = ({
  resultId,
  templateId = 'personality_result',
  onImageGenerated,
  onError
}) => {
  const [imageData, setImageData] = useState<ShareImageData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string>('');
  const [availableTemplates, setAvailableTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState(templateId);

  useEffect(() => {
    loadAvailableTemplates();
  }, []);

  useEffect(() => {
    if (resultId && selectedTemplate) {
      generateShareImage();
    }
  }, [resultId, selectedTemplate]);

  const loadAvailableTemplates = async () => {
    try {
      const api = new PersonalityTestAPI();
      const response = await api.request('/api/share/templates', 'GET');
      
      if (response.success) {
        setAvailableTemplates(Object.values(response.data));
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const generateShareImage = async (forceRegenerate: boolean = false) => {
    if (!resultId) return;

    setIsGenerating(true);
    setError('');

    try {
      const api = new PersonalityTestAPI();
      const response = await api.request('/api/share/generate-image', 'POST', {
        result_id: resultId,
        template_id: selectedTemplate,
        force_regenerate: forceRegenerate
      });

      if (response.success) {
        setImageData(response.data);
        onImageGenerated?.(response.data);
      } else {
        throw new Error('Failed to generate share image');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '生成分享圖片時發生錯誤';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTemplateChange = (newTemplateId: string) => {
    setSelectedTemplate(newTemplateId);
  };

  const handleRegenerateImage = () => {
    generateShareImage(true);
  };

  const handleDownloadImage = async () => {
    if (!imageData?.image_url) return;

    try {
      const response = await fetch(imageData.image_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `share-image-${resultId}-${selectedTemplate}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download image:', error);
    }
  };

  if (isGenerating) {
    return (
      <div className="share-image-preview generating">
        <div className="generating-content">
          <div className="generating-spinner"></div>
          <p className="generating-text">正在生成分享圖片...</p>
          <div className="generating-progress">
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="share-image-preview error">
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <p className="error-message">{error}</p>
          <button 
            className="retry-button"
            onClick={() => generateShareImage()}
          >
            重新生成
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="share-image-preview">
      {/* 模板選擇器 */}
      {availableTemplates.length > 1 && (
        <div className="template-selector">
          <h3 className="selector-title">選擇分享樣式</h3>
          <div className="template-options">
            {availableTemplates.map((template) => (
              <button
                key={template.id}
                className={`template-option ${selectedTemplate === template.id ? 'active' : ''}`}
                onClick={() => handleTemplateChange(template.id)}
              >
                <div 
                  className="template-preview"
                  style={{
                    backgroundColor: template.background_color,
                    color: template.text_color
                  }}
                >
                  <span className="template-name">{template.id}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 圖片預覽 */}
      {imageData && (
        <div className="image-preview-container">
          <div className="image-preview">
            <img 
              src={imageData.image_url} 
              alt="分享圖片預覽"
              className="preview-image"
            />
            <div className="image-overlay">
              <div className="overlay-actions">
                <button 
                  className="action-button regenerate"
                  onClick={handleRegenerateImage}
                  title="重新生成"
                >
                  🔄
                </button>
                <button 
                  className="action-button download"
                  onClick={handleDownloadImage}
                  title="下載圖片"
                >
                  📥
                </button>
              </div>
            </div>
          </div>

          {/* 分享文案預覽 */}
          <div className="share-text-preview">
            <h4 className="preview-title">分享文案</h4>
            <p className="share-text">{imageData.share_text}</p>
            <div className="share-meta">
              <span className="meta-item">模板: {imageData.template_id}</span>
              <span className="meta-item">
                生成時間: {new Date(imageData.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 生成提示 */}
      {!imageData && !isGenerating && !error && (
        <div className="no-image-placeholder">
          <div className="placeholder-icon">🖼️</div>
          <p className="placeholder-text">準備生成分享圖片...</p>
        </div>
      )}
    </div>
  );
};

export default ShareImagePreview;
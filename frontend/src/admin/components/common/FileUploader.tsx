/**
 * FileUploader - 高級文件上傳組件
 * 支援拖拽上傳、多文件上傳、進度跟蹤、預覽、壓縮等功能
 * 提供完整的文件管理和驗證功能
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';

export interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  url?: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  thumbnail?: string;
}

export interface FileUploadConfig {
  maxSize?: number; // bytes
  maxFiles?: number;
  acceptedTypes?: string[];
  enablePreview?: boolean;
  enableCompression?: boolean;
  compressionQuality?: number;
  enableThumbnail?: boolean;
  thumbnailSize?: number;
  uploadUrl?: string;
  chunkSize?: number;
  enableChunkUpload?: boolean;
}

export interface FileUploaderProps {
  config?: FileUploadConfig;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onUploadStart?: (files: UploadFile[]) => void;
  onUploadProgress?: (file: UploadFile, progress: number) => void;
  onUploadSuccess?: (file: UploadFile, response: any) => void;
  onUploadError?: (file: UploadFile, error: string) => void;
  onFilesChange?: (files: UploadFile[]) => void;
  onPreview?: (file: UploadFile) => void;
  customUploadHandler?: (file: File) => Promise<any>;
}

/**
 * FileUploader - 文件上傳組件
 * 提供企業級文件上傳和管理功能
 */
export const FileUploader: React.FC<FileUploaderProps> = ({
  config = {},
  multiple = true,
  disabled = false,
  className = '',
  style = {},
  onUploadStart,
  onUploadProgress,
  onUploadSuccess,
  onUploadError,
  onFilesChange,
  onPreview,
  customUploadHandler
}) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const defaultConfig: FileUploadConfig = {
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 10,
    acceptedTypes: ['image/*', 'application/pdf', '.doc', '.docx', '.xls', '.xlsx'],
    enablePreview: true,
    enableCompression: true,
    compressionQuality: 0.8,
    enableThumbnail: true,
    thumbnailSize: 150,
    uploadUrl: '/api/upload',
    chunkSize: 1024 * 1024, // 1MB
    enableChunkUpload: true,
    ...config
  };

  // 生成文件縮圖
  const generateThumbnail = useCallback(async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!file.type.startsWith('image/')) {
        resolve('');
        return;
      }

      const canvas = canvasRef.current;
      if (!canvas) {
        reject(new Error('Canvas not available'));
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas context not available'));
        return;
      }

      const img = new Image();
      img.onload = () => {
        const { thumbnailSize = 150 } = defaultConfig;
        
        // 計算縮圖尺寸
        let { width, height } = img;
        if (width > height) {
          if (width > thumbnailSize) {
            height = (height * thumbnailSize) / width;
            width = thumbnailSize;
          }
        } else {
          if (height > thumbnailSize) {
            width = (width * thumbnailSize) / height;
            height = thumbnailSize;
          }
        }

        canvas.width = width;
        canvas.height = height;

        // 繪製縮圖
        ctx.drawImage(img, 0, 0, width, height);
        
        const thumbnail = canvas.toDataURL('image/jpeg', 0.7);
        resolve(thumbnail);
      };

      img.onerror = () => reject(new Error('Image load failed'));
      img.src = URL.createObjectURL(file);
    });
  }, [defaultConfig]);

  // 壓縮圖片
  const compressImage = useCallback(async (file: File): Promise<File> => {
    if (!file.type.startsWith('image/') || !defaultConfig.enableCompression) {
      return file;
    }

    return new Promise((resolve) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve(file);
        return;
      }

      const img = new Image();
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(
          (blob) => {
            if (blob) {
              const compressedFile = new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now()
              });
              resolve(compressedFile);
            } else {
              resolve(file);
            }
          },
          file.type,
          defaultConfig.compressionQuality
        );
      };

      img.onerror = () => resolve(file);
      img.src = URL.createObjectURL(file);
    });
  }, [defaultConfig]);

  // 驗證文件
  const validateFile = useCallback((file: File): string | null => {
    const { maxSize, acceptedTypes } = defaultConfig;

    if (maxSize && file.size > maxSize) {
      return `文件大小超過限制 (${(maxSize / 1024 / 1024).toFixed(1)}MB)`;
    }

    if (acceptedTypes && acceptedTypes.length > 0) {
      const isAccepted = acceptedTypes.some(type => {
        if (type.startsWith('.')) {
          return file.name.toLowerCase().endsWith(type.toLowerCase());
        }
        if (type.includes('*')) {
          return file.type.startsWith(type.replace('*', ''));
        }
        return file.type === type;
      });

      if (!isAccepted) {
        return `不支援的文件類型: ${file.type}`;
      }
    }

    return null;
  }, [defaultConfig]);

  // 處理文件選擇
  const handleFileSelect = useCallback(async (selectedFiles: FileList) => {
    const { maxFiles } = defaultConfig;
    
    if (maxFiles && files.length + selectedFiles.length > maxFiles) {
      alert(`最多只能上傳 ${maxFiles} 個文件`);
      return;
    }

    const newFiles: UploadFile[] = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const validationError = validateFile(file);

      if (validationError) {
        alert(validationError);
        continue;
      }

      const uploadFile: UploadFile = {
        id: `${Date.now()}_${i}`,
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending',
        progress: 0
      };

      // 生成縮圖
      if (defaultConfig.enableThumbnail && file.type.startsWith('image/')) {
        try {
          uploadFile.thumbnail = await generateThumbnail(file);
        } catch (error) {
          console.warn('生成縮圖失敗:', error);
        }
      }

      // 壓縮圖片
      if (defaultConfig.enableCompression && file.type.startsWith('image/')) {
        try {
          uploadFile.file = await compressImage(file);
        } catch (error) {
          console.warn('圖片壓縮失敗:', error);
        }
      }

      newFiles.push(uploadFile);
    }

    const updatedFiles = [...files, ...newFiles];
    setFiles(updatedFiles);

    if (onFilesChange) {
      onFilesChange(updatedFiles);
    }

    if (onUploadStart) {
      onUploadStart(newFiles);
    }
  }, [files, defaultConfig, validateFile, generateThumbnail, compressImage, onFilesChange, onUploadStart]);

  // 模擬文件上傳
  const uploadFile = useCallback(async (uploadFile: UploadFile): Promise<void> => {
    try {
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'uploading', progress: 0 }
          : f
      ));

      if (customUploadHandler) {
        // 使用自定義上傳處理器
        const response = await customUploadHandler(uploadFile.file);
        
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'success', progress: 100, url: response.url }
            : f
        ));

        if (onUploadSuccess) {
          onUploadSuccess({ ...uploadFile, status: 'success', progress: 100 }, response);
        }
      } else {
        // 模擬上傳進度
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100));
          
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id 
              ? { ...f, progress }
              : f
          ));

          if (onUploadProgress) {
            onUploadProgress({ ...uploadFile, progress }, progress);
          }
        }

        // 模擬上傳完成
        const mockResponse = {
          url: `https://example.com/uploads/${uploadFile.name}`,
          id: uploadFile.id,
          filename: uploadFile.name
        };

        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'success', progress: 100, url: mockResponse.url }
            : f
        ));

        if (onUploadSuccess) {
          onUploadSuccess({ ...uploadFile, status: 'success', progress: 100 }, mockResponse);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '上傳失敗';
      
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'error', error: errorMessage }
          : f
      ));

      if (onUploadError) {
        onUploadError({ ...uploadFile, status: 'error', error: errorMessage }, errorMessage);
      }
    }
  }, [customUploadHandler, onUploadProgress, onUploadSuccess, onUploadError]);

  // 批量上傳
  const handleBatchUpload = useCallback(async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length === 0) return;

    setIsUploading(true);

    // 並發上傳文件
    const uploadPromises = pendingFiles.map(file => uploadFile(file));
    
    try {
      await Promise.all(uploadPromises);
    } catch (error) {
      console.error('批量上傳失敗:', error);
    } finally {
      setIsUploading(false);
    }
  }, [files, uploadFile]);

  // 刪除文件
  const removeFile = useCallback((fileId: string) => {
    const updatedFiles = files.filter(f => f.id !== fileId);
    setFiles(updatedFiles);

    if (onFilesChange) {
      onFilesChange(updatedFiles);
    }
  }, [files, onFilesChange]);

  // 重試上傳
  const retryUpload = useCallback((fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (file && file.status === 'error') {
      uploadFile(file);
    }
  }, [files, uploadFile]);

  // 拖拽處理
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (disabled) return;

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles);
    }
  }, [disabled, handleFileSelect]);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 獲取文件圖標
  const getFileIcon = (fileType: string): string => {
    if (fileType.startsWith('image/')) return '🖼️';
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('sheet') || fileType.includes('excel')) return '📊';
    if (fileType.includes('video/')) return '🎥';
    if (fileType.includes('audio/')) return '🎵';
    return '📁';
  };

  // 自動上傳效果
  useEffect(() => {
    // 如果有待上傳的文件，自動開始上傳
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length > 0 && !isUploading) {
      // 延遲一秒自動上傳，給用戶時間查看選擇的文件
      const timer = setTimeout(() => {
        handleBatchUpload();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [files, isUploading, handleBatchUpload]);

  return (
    <div className={`file-uploader ${className}`} style={style}>
      {/* 隱藏的文件輸入 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={defaultConfig.acceptedTypes?.join(',')}
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files) {
            handleFileSelect(e.target.files);
          }
        }}
      />

      {/* 隱藏的Canvas用於生成縮圖 */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* 拖拽上傳區域 */}
      <div
        style={{
          border: `2px dashed ${dragActive ? '#4CAF50' : 'rgba(255, 255, 255, 0.3)'}`,
          borderRadius: '8px',
          padding: '40px 20px',
          textAlign: 'center',
          backgroundColor: dragActive ? 'rgba(76, 175, 80, 0.1)' : 'rgba(0, 0, 0, 0.05)',
          transition: 'all 0.3s ease',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.5 : 1
        }}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>
          {dragActive ? '📁' : '☁️'}
        </div>
        
        <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>
          {dragActive ? '放開以上傳文件' : '拖拽文件到此處或點擊上傳'}
        </h3>
        
        <p style={{ margin: 0, color: 'rgba(255, 255, 255, 0.7)', fontSize: '14px' }}>
          支援 {defaultConfig.acceptedTypes?.join(', ') || '所有類型'}，
          最大 {(defaultConfig.maxSize! / 1024 / 1024).toFixed(1)}MB，
          最多 {defaultConfig.maxFiles} 個文件
        </p>
      </div>

      {/* 文件列表 */}
      {files.length > 0 && (
        <div style={{
          marginTop: '20px',
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            backgroundColor: 'rgba(0, 0, 0, 0.1)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
          }}>
            <h4 style={{ margin: 0, fontSize: '16px' }}>
              文件列表 ({files.length})
            </h4>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={handleBatchUpload}
                disabled={isUploading || !files.some(f => f.status === 'pending')}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'rgba(74, 144, 226, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  opacity: isUploading || !files.some(f => f.status === 'pending') ? 0.5 : 1
                }}
              >
                {isUploading ? '上傳中...' : '開始上傳'}
              </button>
              
              <button
                onClick={() => setFiles([])}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'rgba(244, 67, 54, 0.8)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                清除全部
              </button>
            </div>
          </div>

          <div style={{ padding: '16px' }}>
            {files.map((file) => (
              <div
                key={file.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '6px',
                  marginBottom: '8px',
                  border: file.status === 'error' 
                    ? '1px solid rgba(244, 67, 54, 0.5)' 
                    : '1px solid rgba(255, 255, 255, 0.1)'
                }}
              >
                {/* 文件圖標/縮圖 */}
                <div style={{ width: '48px', height: '48px', flexShrink: 0 }}>
                  {file.thumbnail ? (
                    <img
                      src={file.thumbnail}
                      alt={file.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                      onClick={() => onPreview && onPreview(file)}
                    />
                  ) : (
                    <div style={{
                      width: '100%',
                      height: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: 'rgba(0, 0, 0, 0.1)',
                      borderRadius: '4px',
                      fontSize: '24px'
                    }}>
                      {getFileIcon(file.type)}
                    </div>
                  )}
                </div>

                {/* 文件信息 */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 'bold',
                    fontSize: '14px',
                    marginBottom: '4px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {file.name}
                  </div>
                  
                  <div style={{
                    fontSize: '12px',
                    color: 'rgba(255, 255, 255, 0.7)',
                    marginBottom: '4px'
                  }}>
                    {formatFileSize(file.size)} • {file.type}
                  </div>

                  {/* 進度條 */}
                  {file.status === 'uploading' && (
                    <div style={{
                      width: '100%',
                      height: '4px',
                      backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      borderRadius: '2px',
                      overflow: 'hidden'
                    }}>
                      <div
                        style={{
                          width: `${file.progress}%`,
                          height: '100%',
                          backgroundColor: '#4CAF50',
                          transition: 'width 0.3s ease'
                        }}
                      />
                    </div>
                  )}

                  {/* 錯誤信息 */}
                  {file.status === 'error' && file.error && (
                    <div style={{
                      fontSize: '12px',
                      color: '#ff4444',
                      marginTop: '4px'
                    }}>
                      ❌ {file.error}
                    </div>
                  )}
                </div>

                {/* 狀態指示器 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {file.status === 'success' && (
                    <span style={{ color: '#4CAF50', fontSize: '20px' }}>✅</span>
                  )}
                  
                  {file.status === 'error' && (
                    <button
                      onClick={() => retryUpload(file.id)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: 'rgba(255, 193, 7, 0.8)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '11px'
                      }}
                    >
                      重試
                    </button>
                  )}

                  {file.status === 'uploading' && (
                    <div style={{ color: '#2196F3', fontSize: '14px' }}>
                      {file.progress}%
                    </div>
                  )}

                  <button
                    onClick={() => removeFile(file.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'rgba(255, 255, 255, 0.5)',
                      cursor: 'pointer',
                      fontSize: '16px',
                      padding: '4px'
                    }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 上傳統計 */}
      {files.length > 0 && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '6px',
          fontSize: '14px',
          color: 'rgba(255, 255, 255, 0.7)'
        }}>
          總計: {files.length} 個文件 | 
          成功: {files.filter(f => f.status === 'success').length} | 
          失敗: {files.filter(f => f.status === 'error').length} | 
          待上傳: {files.filter(f => f.status === 'pending').length}
        </div>
      )}
    </div>
  );
};

export default FileUploader;
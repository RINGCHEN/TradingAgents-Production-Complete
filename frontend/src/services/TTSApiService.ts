/**
 * TTS API 服務層 - 企業級TTS服務整合層
 * 提供完整的語音合成和管理功能，整合95%完成的TTS後端系統
 * 支援六大數位分析師語音合成與管理
 * 
 * @author 魯班 (Code Artisan) & 梁建築師 (Code Architect)
 * @version 2.0.0 Enterprise
 */

import { createApiUrl } from '../config/apiConfig';
import { 
  TTSVoice, 
  TTSJob, 
  TTSStats, 
  TTSConfig,
  TTSAudioFile,
  TTSUsageReport,
  TTSQueueStatus,
  CreateTTSJobRequest,
  CreateVoiceRequest,
  UpdateVoiceRequest,
  TTSTestRequest,
  TTSResponse,
  TTSListResponse,
  JobStatus,
  AudioFormat,
  TTSProvider,
  PaginationParams
} from '../admin/types/AdminTypes';

// 企業級API配置介面
export interface TTSApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  apiVersion: string;
}

// 分析師語音配置
export interface AnalystVoiceConfig {
  analystId: string;
  analystName: string;
  defaultVoiceId: string;
  voiceSettings: {
    speakingRate: number;
    pitch: number;
    volumeGainDb: number;
  };
  scenarios: {
    [key: string]: {
      voiceId: string;
      settings?: Partial<AnalystVoiceConfig['voiceSettings']>;
    };
  };
}

export interface TTSJob {
  id?: number;
  job_id: string;
  user_id?: number;
  voice_model_id: number;
  text_content: string;
  ssml_content?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  priority: number;
  
  // 音頻參數
  audio_format: 'mp3' | 'wav' | 'ogg' | 'm4a';
  sample_rate: number;
  speaking_rate: number;
  pitch: number;
  volume_gain_db: number;
  
  // 處理資訊
  estimated_duration?: number;
  actual_duration?: number;
  character_count?: number;
  processing_time?: number;
  
  // 檔案資訊
  output_file_path?: string;
  output_file_url?: string;
  file_size_bytes?: number;
  
  // 錯誤處理
  error_message?: string;
  retry_count: number;
  max_retry: number;
  
  // 時間戳記
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  expires_at?: string;
  
  // 關聯資訊
  voice_name?: string;
  user_email?: string;
}

export interface TTSStats {
  total_jobs: number;
  completed_jobs: number;
  pending_jobs: number;
  failed_jobs: number;
  processing_jobs: number;
  success_rate: number;
  avg_processing_time: number;
  total_characters: number;
  total_duration: number;
  total_voices: number;
  active_voices: number;
  period: string;
}

export interface TTSConfig {
  config_key: string;
  config_value: string;
  data_type: string;
  description?: string;
  category?: string;
  is_public: boolean;
  requires_restart: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AudioFile {
  id?: number;
  file_id: string;
  job_id?: number;
  user_id?: number;
  voice_model_id?: number;
  
  // 檔案資訊
  original_filename?: string;
  stored_filename: string;
  file_path: string;
  file_url?: string;
  mime_type?: string;
  file_size_bytes?: number;
  
  // 音頻屬性
  duration_seconds?: number;
  sample_rate?: number;
  bit_rate?: number;
  channels: number;
  audio_format?: 'mp3' | 'wav' | 'ogg' | 'm4a';
  
  // 存取控制
  is_public: boolean;
  access_token?: string;
  download_count: number;
  last_accessed_at?: string;
  
  // 生命週期
  expires_at?: string;
  is_archived: boolean;
  archived_at?: string;
  
  created_at?: string;
  updated_at?: string;
  
  // 關聯資訊
  text_content?: string;
  voice_name?: string;
  user_email?: string;
}

export interface CreateTTSJobRequest {
  text_content: string;
  voice_model_id: number;
  audio_format?: 'mp3' | 'wav' | 'ogg' | 'm4a';
  speaking_rate?: number;
  pitch?: number;
  priority?: number;
}

export interface TTSTestRequest {
  text: string;
  voice_id: string;
}

export interface TTSResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface TTSListResponse<T = any> extends TTSResponse<T[]> {
  total: number;
  page: number;
  limit: number;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface TTSJobFilters extends PaginationParams {
  status?: string;
  user_id?: string;
  voice_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface AudioFileFilters extends PaginationParams {
  user_id?: string;
  voice_id?: string;
}

/**
 * 企業級TTS API 服務類
 * 提供完整的語音合成和管理功能，支援六大數位分析師
 * 單例模式確保API調用的一致性和效率
 */
class TTSApiService {
  private static instance: TTSApiService;
  private baseUrl: string;
  private config: TTSApiConfig;
  private authToken: string | null = null;
  private requestQueue: Map<string, Promise<any>> = new Map();

  // 六大數位分析師預設語音配置
  private readonly analystVoiceConfigs: AnalystVoiceConfig[] = [
    {
      analystId: 'fundamentals',
      analystName: '基本面分析師',
      defaultVoiceId: 'zh-TW-HsiaoChenNeural',
      voiceSettings: { speakingRate: 0.9, pitch: 0, volumeGainDb: 0 },
      scenarios: {
        'analysis': { voiceId: 'zh-TW-HsiaoChenNeural' },
        'summary': { voiceId: 'zh-TW-YunJheNeural' }
      }
    },
    {
      analystId: 'news',
      analystName: '新聞分析師',
      defaultVoiceId: 'zh-TW-YunJheNeural',
      voiceSettings: { speakingRate: 1.0, pitch: 0.1, volumeGainDb: 0 },
      scenarios: {
        'breaking': { voiceId: 'zh-TW-YunJheNeural', settings: { speakingRate: 1.1 } },
        'summary': { voiceId: 'zh-TW-HsiaoChenNeural' }
      }
    },
    {
      analystId: 'risk',
      analystName: '風險管理分析師',
      defaultVoiceId: 'zh-TW-HsiaoYuNeural',
      voiceSettings: { speakingRate: 0.8, pitch: -0.1, volumeGainDb: 0 },
      scenarios: {
        'warning': { voiceId: 'zh-TW-HsiaoYuNeural', settings: { speakingRate: 0.7, pitch: -0.2 } },
        'report': { voiceId: 'zh-TW-YunJheNeural' }
      }
    },
    {
      analystId: 'sentiment',
      analystName: '情緒分析師',
      defaultVoiceId: 'zh-TW-HsiaoChenNeural',
      voiceSettings: { speakingRate: 0.95, pitch: 0.05, volumeGainDb: 0 },
      scenarios: {
        'positive': { voiceId: 'zh-TW-HsiaoChenNeural', settings: { pitch: 0.1 } },
        'negative': { voiceId: 'zh-TW-HsiaoYuNeural', settings: { pitch: -0.1 } }
      }
    },
    {
      analystId: 'investment',
      analystName: '投資規劃師',
      defaultVoiceId: 'zh-TW-YunJheNeural',
      voiceSettings: { speakingRate: 0.85, pitch: 0, volumeGainDb: 0 },
      scenarios: {
        'recommendation': { voiceId: 'zh-TW-YunJheNeural' },
        'strategy': { voiceId: 'zh-TW-HsiaoChenNeural' }
      }
    },
    {
      analystId: 'taiwan-market',
      analystName: '台股市場分析師',
      defaultVoiceId: 'zh-TW-HsiaoYuNeural',
      voiceSettings: { speakingRate: 1.0, pitch: 0, volumeGainDb: 0 },
      scenarios: {
        'opening': { voiceId: 'zh-TW-HsiaoYuNeural', settings: { speakingRate: 1.1 } },
        'closing': { voiceId: 'zh-TW-YunJheNeural', settings: { speakingRate: 0.9 } }
      }
    }
  ];

  private constructor(config?: Partial<TTSApiConfig>) {
    this.baseUrl = createApiUrl('/admin/tts');
    this.authToken = localStorage.getItem('authToken');
    this.config = {
      baseUrl: this.baseUrl,
      timeout: 30000,
      retryAttempts: 3,
      apiVersion: 'v1',
      ...config
    };
  }

  /**
   * 獲取TTS服務單例實例
   */
  public static getInstance(config?: Partial<TTSApiConfig>): TTSApiService {
    if (!TTSApiService.instance) {
      TTSApiService.instance = new TTSApiService(config);
    }
    return TTSApiService.instance;
  }

  /**
   * 設置認證令牌
   */
  setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('authToken', token);
  }

  /**
   * 獲取認證標頭
   */
  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    return headers;
  }

  /**
   * 處理 API 響應
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        detail: `HTTP ${response.status}: ${response.statusText}` 
      }));
      throw new Error(errorData.detail || errorData.message || '請求失敗');
    }

    return response.json();
  }

  /**
   * 發送 API 請求
   */
  private async request<T>(
    endpoint: string, 
    method: string = 'GET', 
    data?: any
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      method,
      headers: this.getAuthHeaders(),
    };

    if (data && method !== 'GET') {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, config);
      return this.handleResponse<T>(response);
    } catch (error) {
      console.error(`TTS API Error (${method} ${endpoint}):`, error);
      throw error instanceof Error ? error : new Error('未知錯誤');
    }
  }

  // ===== 語音管理 API =====

  /**
   * 獲取 TTS 語音列表
   */
  async getVoices(params?: {
    language?: string;
    gender?: string;
    active_only?: boolean;
  }): Promise<TTSVoice[]> {
    const searchParams = new URLSearchParams();
    if (params?.language) searchParams.append('language', params.language);
    if (params?.gender) searchParams.append('gender', params.gender);
    if (params?.active_only) searchParams.append('active_only', 'true');

    const query = searchParams.toString();
    const endpoint = query ? `/voices?${query}` : '/voices';
    
    return this.request<TTSVoice[]>(endpoint);
  }

  /**
   * 創建新的 TTS 語音
   */
  async createVoice(voiceData: Partial<TTSVoice>): Promise<TTSVoice> {
    return this.request<TTSVoice>('/voices', 'POST', voiceData);
  }

  /**
   * 更新 TTS 語音
   */
  async updateVoice(voiceId: string, voiceData: Partial<TTSVoice>): Promise<TTSVoice> {
    return this.request<TTSVoice>(`/voices/${voiceId}`, 'PUT', voiceData);
  }

  /**
   * 刪除 TTS 語音
   */
  async deleteVoice(voiceId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/voices/${voiceId}`, 'DELETE');
  }

  // ===== 任務管理 API =====

  /**
   * 獲取 TTS 任務列表
   */
  async getJobs(filters?: TTSJobFilters): Promise<TTSJob[]> {
    const searchParams = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = query ? `/jobs?${query}` : '/jobs';
    
    return this.request<TTSJob[]>(endpoint);
  }

  /**
   * 獲取特定 TTS 任務
   */
  async getJob(jobId: string): Promise<TTSJob> {
    return this.request<TTSJob>(`/jobs/${jobId}`);
  }

  /**
   * 創建新的 TTS 任務
   */
  async createJob(jobData: CreateTTSJobRequest): Promise<TTSJob> {
    return this.request<TTSJob>('/jobs', 'POST', jobData);
  }

  /**
   * 重試 TTS 任務
   */
  async retryJob(jobId: string): Promise<{ message: string; job: TTSJob }> {
    return this.request<{ message: string; job: TTSJob }>(`/jobs/${jobId}/retry`, 'POST');
  }

  /**
   * 取消 TTS 任務
   */
  async cancelJob(jobId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/jobs/${jobId}`, 'DELETE');
  }

  // ===== 企業級語音合成 API =====

  /**
   * 直接語音合成（返回音頻Blob）
   */
  async synthesizeSpeech(
    text: string, 
    voiceId: string,
    options?: {
      audioFormat?: AudioFormat;
      speakingRate?: number;
      pitch?: number;
      volumeGainDb?: number;
    }
  ): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/synthesize`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        text,
        voice_id: voiceId,
        audio_format: options?.audioFormat || 'mp3',
        speaking_rate: options?.speakingRate || 1.0,
        pitch: options?.pitch || 0,
        volume_gain_db: options?.volumeGainDb || 0
      })
    });

    if (!response.ok) {
      throw new Error(`語音合成失敗: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * 分析師語音合成（針對六大分析師優化）
   */
  async synthesizeAnalystSpeech(
    analystId: string,
    text: string,
    scenario?: string
  ): Promise<Blob> {
    const analystConfig = this.analystVoiceConfigs.find(
      config => config.analystId === analystId
    );

    if (!analystConfig) {
      throw new Error(`未找到分析師配置: ${analystId}`);
    }

    const scenarioConfig = scenario ? analystConfig.scenarios[scenario] : null;
    const voiceId = scenarioConfig?.voiceId || analystConfig.defaultVoiceId;
    const voiceSettings = {
      ...analystConfig.voiceSettings,
      ...scenarioConfig?.settings
    };

    return this.synthesizeSpeech(text, voiceId, {
      speakingRate: voiceSettings.speakingRate,
      pitch: voiceSettings.pitch,
      volumeGainDb: voiceSettings.volumeGainDb
    });
  }

  /**
   * 測試 TTS 語音合成
   */
  async testSynthesis(text: string, voiceId: string): Promise<{
    success: boolean;
    audio_url?: string;
    job_id?: string;
    message?: string;
  }> {
    const data: TTSTestRequest = { text, voice_id: voiceId };
    return this.request<{
      success: boolean;
      audio_url?: string;
      job_id?: string;
      message?: string;
    }>('/test-synthesis', 'POST', data);
  }

  /**
   * 快速語音合成（適用於短文本）
   */
  async quickSynthesis(
    text: string, 
    voiceId: string, 
    options?: {
      speaking_rate?: number;
      pitch?: number;
      audio_format?: 'mp3' | 'wav' | 'ogg' | 'm4a';
    }
  ): Promise<{
    success: boolean;
    audio_url?: string;
    job_id?: string;
    estimated_duration?: number;
  }> {
    const jobData: CreateTTSJobRequest = {
      text_content: text,
      voice_model_id: parseInt(voiceId),
      speaking_rate: options?.speaking_rate || 1.0,
      pitch: options?.pitch || 0.0,
      audio_format: (options?.audio_format || 'mp3') as AudioFormat,
      priority: 10 // 高優先級用於快速合成
    };

    const job = await this.createJob(jobData);
    
    // 輪詢檢查任務狀態
    return this.pollJobCompletion(job.job_id, 30000); // 30秒超時
  }

  /**
   * 輪詢任務完成狀態
   */
  private async pollJobCompletion(
    jobId: string, 
    timeout: number = 30000
  ): Promise<{
    success: boolean;
    audio_url?: string;
    job_id?: string;
    estimated_duration?: number;
  }> {
    const startTime = Date.now();
    const pollInterval = 1000; // 每秒檢查一次

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          if (Date.now() - startTime > timeout) {
            reject(new Error('語音合成超時'));
            return;
          }

          const job = await this.getJob(jobId);
          
          if (job.status === 'completed') {
            resolve({
              success: true,
              audio_url: job.output_file_url,
              job_id: jobId,
              estimated_duration: job.estimated_duration
            });
          } else if (job.status === 'failed') {
            reject(new Error(job.error_message || '語音合成失敗'));
          } else {
            // 繼續輪詢
            setTimeout(poll, pollInterval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  // ===== 統計和配置 API =====

  /**
   * 獲取 TTS 統計數據
   */
  async getStats(period: string = 'today'): Promise<TTSStats> {
    return this.request<TTSStats>(`/stats?period=${period}`);
  }

  /**
   * 獲取 TTS 配置
   */
  async getConfig(): Promise<TTSConfig[]> {
    return this.request<TTSConfig[]>('/config');
  }

  /**
   * 更新 TTS 配置
   */
  async updateConfig(configData: Record<string, any>): Promise<TTSConfig[]> {
    return this.request<TTSConfig[]>('/config', 'PUT', configData);
  }

  // ===== 音頻文件管理 API =====

  /**
   * 獲取音頻文件列表
   */
  async getAudioFiles(filters?: AudioFileFilters): Promise<AudioFile[]> {
    const searchParams = new URLSearchParams();
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = query ? `/audio-files?${query}` : '/audio-files';
    
    return this.request<AudioFile[]>(endpoint);
  }

  /**
   * 刪除音頻文件
   */
  async deleteAudioFile(fileId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/audio-files/${fileId}`, 'DELETE');
  }

  /**
   * 批量清理舊音頻文件
   */
  async cleanupAudioFiles(daysOld: number = 30): Promise<{
    message: string;
    deleted_count: number;
    freed_space_bytes: number;
  }> {
    return this.request<{
      message: string;
      deleted_count: number;
      freed_space_bytes: number;
    }>(`/batch-cleanup?days_old=${daysOld}`, 'POST');
  }

  // ===== 隊列管理 API =====

  /**
   * 獲取 TTS 任務隊列狀態
   */
  async getQueueStatus(): Promise<{
    queue_size: number;
    queued_jobs: number;
    processing_jobs: number;
    avg_attempts: number;
    is_processing: boolean;
    system_load: number;
    processing_job_samples: Array<Record<string, any>>;
  }> {
    return this.request<{
      queue_size: number;
      queued_jobs: number;
      processing_jobs: number;
      avg_attempts: number;
      is_processing: boolean;
      system_load: number;
      processing_job_samples: Array<Record<string, any>>;
    }>('/queue-status');
  }

  /**
   * 清空 TTS 任務隊列
   */
  async clearQueue(): Promise<{
    message: string;
    cleared_jobs: number;
  }> {
    return this.request<{
      message: string;
      cleared_jobs: number;
    }>('/queue/clear', 'POST');
  }

  // ===== 使用報告 API =====

  /**
   * 獲取 TTS 使用報告
   */
  async getUsageReport(params?: {
    start_date?: string;
    end_date?: string;
    user_id?: string;
  }): Promise<{
    usage_data: Array<Record<string, any>>;
    summary: Record<string, any>;
  }> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value) {
          searchParams.append(key, value);
        }
      });
    }

    const query = searchParams.toString();
    const endpoint = query ? `/usage-report?${query}` : '/usage-report';
    
    return this.request<{
      usage_data: Array<Record<string, any>>;
      summary: Record<string, any>;
    }>(endpoint);
  }

  // ===== 實用工具方法 =====

  /**
   * 估算文本語音合成時長（基於字符數和語速）
   */
  estimateDuration(text: string, speakingRate: number = 1.0): number {
    // 基於平均語速：每分鐘約 150-160 個中文字符或 200-250 個英文單詞
    const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const englishWords = (text.match(/\b[a-zA-Z]+\b/g) || []).length;
    const otherChars = text.length - chineseChars - englishWords;
    
    // 估算基礎時長（秒）
    const baseDuration = (chineseChars * 0.4) + (englishWords * 0.3) + (otherChars * 0.1);
    
    // 根據語速調整
    return Math.max(1, Math.round(baseDuration / speakingRate));
  }

  /**
   * 驗證文本內容
   */
  validateText(text: string): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (!text || text.trim().length === 0) {
      errors.push('文字內容不能為空');
    }
    
    if (text.length > 10000) {
      errors.push('文字內容不能超過 10000 字符');
    }
    
    if (text.length < 1) {
      errors.push('文字內容至少需要 1 個字符');
    }

    // 檢查可能的問題字符
    const problematicChars = text.match(/[^\u0000-\u007F\u4e00-\u9fff\s\p{P}]/gu);
    if (problematicChars && problematicChars.length > 0) {
      errors.push('文字包含不支援的特殊字符');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  /**
   * 格式化持續時間
   */
  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}秒`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}分${remainingSeconds}秒`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}時${minutes}分`;
    }
  }

  // ===== 分析師語音配置工具方法 =====

  /**
   * 獲取分析師語音配置
   */
  getAnalystVoiceConfig(analystId: string): AnalystVoiceConfig | undefined {
    return this.analystVoiceConfigs.find(config => config.analystId === analystId);
  }

  /**
   * 獲取所有分析師語音配置
   */
  getAllAnalystVoiceConfigs(): AnalystVoiceConfig[] {
    return [...this.analystVoiceConfigs];
  }

  /**
   * 檢查服務健康狀態
   */
  async healthCheck(): Promise<TTSResponse<{ status: string }>> {
    return this.request<TTSResponse<{ status: string }>>('/health');
  }

  /**
   * 延遲函數
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 執行HTTP請求，支援重試機制
   */
  private async executeRequest<T>(
    url: string,
    options: RequestInit & { timeout?: number }
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.config.timeout);

        const response = await fetch(url, {
          ...options,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt < this.config.retryAttempts) {
          await this.delay(Math.pow(2, attempt) * 1000); // 指數退避
        }
      }
    }

    throw new Error(`API請求失敗 (${this.config.retryAttempts + 1}次嘗試): ${lastError.message}`);
  }
}

// 創建並導出單例實例 (保持向後兼容)
const ttsApiService = TTSApiService.getInstance();

export default ttsApiService;
export { TTSApiService };
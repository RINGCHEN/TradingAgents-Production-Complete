/**
 * 管理後台核心類型定義
 * 基於API分析結果生成的統一類型系統
 */

// 基礎響應類型
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
  success: boolean;
  timestamp?: string;
}

// 分頁類型
export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// 表格相關類型
export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex: string;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: T, index: number) => React.ReactNode;
  filterOptions?: Array<{ label: string; value: any }>;
  sorter?: (a: any, b: any) => number;
  fixed?: 'left' | 'right';
}

export interface TableFilter {
  [key: string]: any;
}

export interface TableSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface TablePagination {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  pageSizeOptions?: number[];
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[];
  dataSource: T[];
  loading?: boolean;
  pagination?: PaginationParams | false;
  onPaginationChange?: (pagination: PaginationParams) => void;
  rowKey?: string | ((record: T) => string);
  selection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[]) => void;
  };
  className?: string;
}

// 用戶管理類型
export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended'
}

// 系統管理類型
export interface SystemStatus {
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  version: string;
  services: ServiceStatus[];
  metrics: SystemMetrics;
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error';
  uptime: number;
  lastCheck: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    incoming: number;
    outgoing: number;
  };
}

// TTS 管理類型
export enum VoiceGender {
  MALE = 'male',
  FEMALE = 'female',
  NEUTRAL = 'neutral'
}

export enum VoiceType {
  NEURAL = 'neural',
  STANDARD = 'standard',
  WAVENET = 'wavenet'
}

export enum TTSProvider {
  AZURE = 'azure',
  GOOGLE = 'google',
  AMAZON = 'amazon',
  LOCAL = 'local'
}

export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum AudioFormat {
  MP3 = 'mp3',
  WAV = 'wav',
  OGG = 'ogg',
  M4A = 'm4a'
}

export interface TTSVoice {
  id?: number;
  model_id: string;
  name: string;
  description?: string;
  language: string;
  gender: VoiceGender;
  voice_type: VoiceType;
  sample_rate: number;
  audio_format: AudioFormat;
  provider: TTSProvider;
  model_path?: string;
  config_data?: Record<string, any>;
  is_active: boolean;
  is_premium: boolean;
  cost_per_character: number;
  created_at?: string;
  updated_at?: string;
}

export interface TTSJob {
  id?: number;
  job_id: string;
  user_id?: number;
  voice_model_id: number;
  text_content: string;
  ssml_content?: string;
  status: JobStatus;
  priority: number;
  
  // 音頻參數
  audio_format: AudioFormat;
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

export interface TTSAudioFile {
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
  audio_format?: AudioFormat;
  
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

export interface TTSUsageStats {
  id?: number;
  user_id?: number;
  voice_model_id?: number;
  date: string;
  jobs_count: number;
  characters_count: number;
  total_duration: number;
  total_cost: number;
  success_count: number;
  failed_count: number;
  created_at?: string;
}

export interface TTSUsageReport {
  usage_data: TTSUsageStats[];
  summary: Record<string, any>;
}

export interface TTSQueueStatus {
  queue_size: number;
  queued_jobs: number;
  processing_jobs: number;
  avg_attempts: number;
  is_processing: boolean;
  system_load: number;
  processing_job_samples: Array<Record<string, any>>;
}

// TTS 請求類型
export interface CreateTTSJobRequest {
  text_content: string;
  voice_model_id: number;
  audio_format?: AudioFormat;
  speaking_rate?: number;
  pitch?: number;
  priority?: number;
}

export interface CreateVoiceRequest {
  model_id: string;
  name: string;
  description?: string;
  language: string;
  gender: VoiceGender;
  voice_type?: VoiceType;
  provider: TTSProvider;
  is_active?: boolean;
  cost_per_character?: number;
}

export interface UpdateVoiceRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  cost_per_character?: number;
}

export interface TTSTestRequest {
  text: string;
  voice_id: string;
}

// TTS 響應類型
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
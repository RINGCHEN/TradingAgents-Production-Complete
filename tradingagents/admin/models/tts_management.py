"""
TTS (Text-to-Speech) 管理模型
定義 TTS 相關的數據模型和響應格式
"""

from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class VoiceGender(str, Enum):
    """語音性別枚舉"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class VoiceType(str, Enum):
    """語音類型枚舉"""
    NEURAL = "neural"
    STANDARD = "standard"
    WAVENET = "wavenet"

class TTSProvider(str, Enum):
    """TTS 服務提供商枚舉"""
    AZURE = "azure"
    GOOGLE = "google"
    AMAZON = "amazon"
    LOCAL = "local"

class JobStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AudioFormat(str, Enum):
    """音頻格式枚舉"""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    M4A = "m4a"

class TTSVoice(BaseModel):
    """TTS 語音模型"""
    id: Optional[int] = None
    model_id: str
    name: str
    description: Optional[str] = None
    language: str
    gender: VoiceGender
    voice_type: VoiceType
    sample_rate: int = 22050
    audio_format: AudioFormat = AudioFormat.MP3
    provider: TTSProvider
    model_path: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = {}
    is_active: bool = True
    is_premium: bool = False
    cost_per_character: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        if v not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError('不支援的採樣率')
        return v
    
    @validator('cost_per_character')
    def validate_cost(cls, v):
        if v < 0:
            raise ValueError('成本不能為負數')
        return v

class TTSJob(BaseModel):
    """TTS 任務模型"""
    id: Optional[int] = None
    job_id: str
    user_id: Optional[int] = None
    voice_model_id: int
    text_content: str
    ssml_content: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    
    # 音頻參數
    audio_format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 22050
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0
    
    # 處理資訊
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    character_count: Optional[int] = None
    processing_time: Optional[int] = None
    
    # 檔案資訊
    output_file_path: Optional[str] = None
    output_file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    # 錯誤處理
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retry: int = 3
    
    # 時間戳記
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # 關聯資訊
    voice_name: Optional[str] = None
    user_email: Optional[str] = None
    
    @validator('text_content')
    def validate_text_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('文字內容不能為空')
        if len(v) > 10000:
            raise ValueError('文字內容過長')
        return v.strip()
    
    @validator('speaking_rate')
    def validate_speaking_rate(cls, v):
        if not 0.25 <= v <= 4.0:
            raise ValueError('語速必須在 0.25 到 4.0 之間')
        return v
    
    @validator('pitch')
    def validate_pitch(cls, v):
        if not -20.0 <= v <= 20.0:
            raise ValueError('音調必須在 -20.0 到 20.0 之間')
        return v

class TTSConfig(BaseModel):
    """TTS 配置模型"""
    config_key: str
    config_value: str
    data_type: str = "string"
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: bool = False
    requires_restart: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TTSStats(BaseModel):
    """TTS 統計模型"""
    total_jobs: int = 0
    completed_jobs: int = 0
    pending_jobs: int = 0
    failed_jobs: int = 0
    processing_jobs: int = 0
    success_rate: float = 0.0
    avg_processing_time: float = 0.0
    total_characters: int = 0
    total_duration: int = 0
    total_voices: int = 0
    active_voices: int = 0
    period: str = "today"

class VoiceModel(BaseModel):
    """語音模型信息"""
    id: Optional[int] = None
    model_id: str
    name: str
    description: Optional[str] = None
    language: str
    provider: TTSProvider
    is_active: bool = True
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    upload_date: Optional[datetime] = None

class AudioFile(BaseModel):
    """音頻文件模型"""
    id: Optional[int] = None
    file_id: str
    job_id: Optional[int] = None
    user_id: Optional[int] = None
    voice_model_id: Optional[int] = None
    
    # 檔案資訊
    original_filename: Optional[str] = None
    stored_filename: str
    file_path: str
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    # 音頻屬性
    duration_seconds: Optional[int] = None
    sample_rate: Optional[int] = None
    bit_rate: Optional[int] = None
    channels: int = 1
    audio_format: Optional[AudioFormat] = None
    
    # 存取控制
    is_public: bool = False
    access_token: Optional[str] = None
    download_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    # 生命週期
    expires_at: Optional[datetime] = None
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # 關聯資訊
    text_content: Optional[str] = None
    voice_name: Optional[str] = None
    user_email: Optional[str] = None

class TTSUsageStats(BaseModel):
    """TTS 使用統計模型"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    voice_model_id: Optional[int] = None
    date: datetime
    jobs_count: int = 0
    characters_count: int = 0
    total_duration: int = 0
    total_cost: float = 0.0
    success_count: int = 0
    failed_count: int = 0
    created_at: Optional[datetime] = None

class TTSUsageReport(BaseModel):
    """TTS 使用報告模型"""
    usage_data: List[TTSUsageStats]
    summary: Dict[str, Any]

class TTSJobQueue(BaseModel):
    """TTS 任務隊列模型"""
    id: Optional[int] = None
    job_id: int
    queue_name: str = "default"
    priority: int = 0
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    status: str = "queued"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TTSQueueStatus(BaseModel):
    """TTS 隊列狀態模型"""
    queue_size: int = 0
    queued_jobs: int = 0
    processing_jobs: int = 0
    avg_attempts: float = 0.0
    is_processing: bool = False
    system_load: float = 0.0
    processing_job_samples: List[Dict[str, Any]] = []

class TTSSystemMetrics(BaseModel):
    """TTS 系統監控指標模型"""
    id: Optional[int] = None
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = {}
    timestamp: datetime
    created_at: Optional[datetime] = None

class TTSQualityAssessment(BaseModel):
    """TTS 品質評估模型"""
    id: Optional[int] = None
    job_id: int
    audio_file_id: Optional[int] = None
    user_id: Optional[int] = None
    
    # 評估分數 (1-5)
    overall_score: Optional[int] = None
    clarity_score: Optional[int] = None
    naturalness_score: Optional[int] = None
    pronunciation_score: Optional[int] = None
    
    # 評估意見
    feedback_text: Optional[str] = None
    issues_reported: List[str] = []
    
    # 自動評估 (AI)
    auto_assessment_score: Optional[float] = None
    auto_assessment_data: Optional[Dict[str, Any]] = {}
    
    created_at: Optional[datetime] = None
    
    @validator('overall_score', 'clarity_score', 'naturalness_score', 'pronunciation_score')
    def validate_score(cls, v):
        if v is not None and not 1 <= v <= 5:
            raise ValueError('評分必須在 1 到 5 之間')
        return v

# 請求和響應模型
class CreateTTSJobRequest(BaseModel):
    """創建 TTS 任務請求"""
    text_content: str
    voice_model_id: int
    audio_format: AudioFormat = AudioFormat.MP3
    speaking_rate: float = 1.0
    pitch: float = 0.0
    priority: int = 0
    
    @validator('text_content')
    def validate_text(cls, v):
        if len(v) > 5000:
            raise ValueError('文字內容不能超過 5000 字符')
        return v

class CreateVoiceRequest(BaseModel):
    """創建語音請求"""
    model_id: str
    name: str
    description: Optional[str] = None
    language: str
    gender: VoiceGender
    voice_type: VoiceType = VoiceType.NEURAL
    provider: TTSProvider
    is_active: bool = True
    cost_per_character: float = 0.0

class UpdateVoiceRequest(BaseModel):
    """更新語音請求"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    cost_per_character: Optional[float] = None

class TTSTestRequest(BaseModel):
    """TTS 測試請求"""
    text: str
    voice_id: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 200:
            raise ValueError('測試文字不能超過 200 字符')
        return v

class TTSResponse(BaseModel):
    """TTS API 響應基礎模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()

class TTSJobResponse(TTSResponse):
    """TTS 任務響應"""
    data: Optional[TTSJob] = None

class TTSVoiceResponse(TTSResponse):
    """TTS 語音響應"""
    data: Optional[TTSVoice] = None

class TTSStatsResponse(TTSResponse):
    """TTS 統計響應"""
    data: Optional[TTSStats] = None

class TTSListResponse(TTSResponse):
    """TTS 列表響應"""
    data: List[Any] = []
    total: int = 0
    page: int = 1
    limit: int = 20
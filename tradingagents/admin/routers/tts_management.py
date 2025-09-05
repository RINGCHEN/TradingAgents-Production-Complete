"""
TTS (Text-to-Speech) 管理路由
提供完整的語音合成管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
from pathlib import Path
from ..services.tts_management_service import TTSManagementService
from ..models.tts_management import (
    TTSVoice,
    TTSJob,
    TTSStats,
    TTSConfig,
    VoiceModel,
    AudioFile,
    TTSUsageReport
)
from ..middleware.auth_middleware import require_admin_permission

router = APIRouter(prefix="/admin/tts", tags=["tts-management"])
logger = logging.getLogger(__name__)

@router.get("/voices", response_model=List[TTSVoice])
async def get_tts_voices(
    language: Optional[str] = Query(None, description="語言篩選"),
    gender: Optional[str] = Query(None, description="性別篩選"),
    active_only: bool = Query(False, description="只顯示啟用的語音"),
    service: TTSManagementService = Depends()
):
    """獲取 TTS 語音列表"""
    try:
        voices = await service.get_tts_voices(
            language=language,
            gender=gender,
            active_only=active_only
        )
        return voices
    except Exception as e:
        logger.error(f"獲取 TTS 語音列表失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 語音列表失敗")

@router.post("/voices", response_model=TTSVoice)
async def create_tts_voice(
    voice_data: dict,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """創建新的 TTS 語音"""
    try:
        voice = await service.create_tts_voice(voice_data)
        logger.info(f"管理員 {current_user['username']} 創建了 TTS 語音: {voice.name}")
        return voice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"創建 TTS 語音失敗: {e}")
        raise HTTPException(status_code=500, detail="創建 TTS 語音失敗")

@router.put("/voices/{voice_id}", response_model=TTSVoice)
async def update_tts_voice(
    voice_id: str,
    voice_data: dict,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """更新 TTS 語音"""
    try:
        voice = await service.update_tts_voice(voice_id, voice_data)
        logger.info(f"管理員 {current_user['username']} 更新了 TTS 語音: {voice_id}")
        return voice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 TTS 語音失敗: {e}")
        raise HTTPException(status_code=500, detail="更新 TTS 語音失敗")

@router.delete("/voices/{voice_id}")
async def delete_tts_voice(
    voice_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """刪除 TTS 語音"""
    try:
        await service.delete_tts_voice(voice_id)
        logger.info(f"管理員 {current_user['username']} 刪除了 TTS 語音: {voice_id}")
        return {"message": "TTS 語音已刪除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"刪除 TTS 語音失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除 TTS 語音失敗")

@router.get("/jobs", response_model=List[TTSJob])
async def get_tts_jobs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="任務狀態"),
    user_id: Optional[str] = Query(None, description="用戶ID"),
    voice_id: Optional[str] = Query(None, description="語音ID"),
    start_date: Optional[str] = Query(None, description="開始日期"),
    end_date: Optional[str] = Query(None, description="結束日期"),
    service: TTSManagementService = Depends()
):
    """獲取 TTS 任務列表"""
    try:
        jobs = await service.get_tts_jobs(
            page=page,
            limit=limit,
            status=status,
            user_id=user_id,
            voice_id=voice_id,
            start_date=start_date,
            end_date=end_date
        )
        return jobs
    except Exception as e:
        logger.error(f"獲取 TTS 任務列表失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 任務列表失敗")

@router.get("/jobs/{job_id}", response_model=TTSJob)
async def get_tts_job(
    job_id: str,
    service: TTSManagementService = Depends()
):
    """獲取特定 TTS 任務"""
    try:
        job = await service.get_tts_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="TTS 任務不存在")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 TTS 任務失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 任務失敗")

@router.post("/jobs/{job_id}/retry")
async def retry_tts_job(
    job_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """重試 TTS 任務"""
    try:
        result = await service.retry_tts_job(job_id)
        logger.info(f"管理員 {current_user['username']} 重試了 TTS 任務: {job_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"重試 TTS 任務失敗: {e}")
        raise HTTPException(status_code=500, detail="重試 TTS 任務失敗")

@router.delete("/jobs/{job_id}")
async def cancel_tts_job(
    job_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """取消 TTS 任務"""
    try:
        await service.cancel_tts_job(job_id)
        logger.info(f"管理員 {current_user['username']} 取消了 TTS 任務: {job_id}")
        return {"message": "TTS 任務已取消"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消 TTS 任務失敗: {e}")
        raise HTTPException(status_code=500, detail="取消 TTS 任務失敗")

@router.get("/stats", response_model=TTSStats)
async def get_tts_stats(
    period: str = Query("today", description="統計週期: today, week, month, year"),
    service: TTSManagementService = Depends()
):
    """獲取 TTS 統計數據"""
    try:
        stats = await service.get_tts_stats(period)
        return stats
    except Exception as e:
        logger.error(f"獲取 TTS 統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 統計失敗")

@router.get("/config", response_model=TTSConfig)
async def get_tts_config(
    service: TTSManagementService = Depends()
):
    """獲取 TTS 配置"""
    try:
        config = await service.get_tts_config()
        return config
    except Exception as e:
        logger.error(f"獲取 TTS 配置失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 配置失敗")

@router.put("/config", response_model=TTSConfig)
async def update_tts_config(
    config_data: dict,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """更新 TTS 配置"""
    try:
        config = await service.update_tts_config(config_data)
        logger.info(f"管理員 {current_user['username']} 更新了 TTS 配置")
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 TTS 配置失敗: {e}")
        raise HTTPException(status_code=500, detail="更新 TTS 配置失敗")

@router.get("/models", response_model=List[VoiceModel])
async def get_voice_models(
    service: TTSManagementService = Depends()
):
    """獲取語音模型列表"""
    try:
        models = await service.get_voice_models()
        return models
    except Exception as e:
        logger.error(f"獲取語音模型失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取語音模型失敗")

@router.post("/models/upload")
async def upload_voice_model(
    file: UploadFile = File(...),
    name: str = Query(..., description="模型名稱"),
    description: Optional[str] = Query(None, description="模型描述"),
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """上傳語音模型"""
    try:
        model = await service.upload_voice_model(file, name, description)
        logger.info(f"管理員 {current_user['username']} 上傳了語音模型: {name}")
        return model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上傳語音模型失敗: {e}")
        raise HTTPException(status_code=500, detail="上傳語音模型失敗")

@router.delete("/models/{model_id}")
async def delete_voice_model(
    model_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """刪除語音模型"""
    try:
        await service.delete_voice_model(model_id)
        logger.info(f"管理員 {current_user['username']} 刪除了語音模型: {model_id}")
        return {"message": "語音模型已刪除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"刪除語音模型失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除語音模型失敗")

@router.get("/audio-files", response_model=List[AudioFile])
async def get_audio_files(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用戶ID"),
    voice_id: Optional[str] = Query(None, description="語音ID"),
    service: TTSManagementService = Depends()
):
    """獲取音頻文件列表"""
    try:
        files = await service.get_audio_files(
            page=page,
            limit=limit,
            user_id=user_id,
            voice_id=voice_id
        )
        return files
    except Exception as e:
        logger.error(f"獲取音頻文件失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取音頻文件失敗")

@router.delete("/audio-files/{file_id}")
async def delete_audio_file(
    file_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """刪除音頻文件"""
    try:
        await service.delete_audio_file(file_id)
        logger.info(f"管理員 {current_user['username']} 刪除了音頻文件: {file_id}")
        return {"message": "音頻文件已刪除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"刪除音頻文件失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除音頻文件失敗")

@router.get("/usage-report", response_model=TTSUsageReport)
async def get_tts_usage_report(
    start_date: Optional[str] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="結束日期 YYYY-MM-DD"),
    user_id: Optional[str] = Query(None, description="用戶ID"),
    service: TTSManagementService = Depends()
):
    """獲取 TTS 使用報告"""
    try:
        report = await service.get_tts_usage_report(start_date, end_date, user_id)
        return report
    except Exception as e:
        logger.error(f"獲取 TTS 使用報告失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 使用報告失敗")

@router.post("/test-synthesis")
async def test_tts_synthesis(
    text: str,
    voice_id: str,
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """測試 TTS 語音合成"""
    try:
        result = await service.test_tts_synthesis(text, voice_id)
        logger.info(f"管理員 {current_user['username']} 測試了 TTS 語音合成")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"測試 TTS 語音合成失敗: {e}")
        raise HTTPException(status_code=500, detail="測試 TTS 語音合成失敗")

@router.post("/batch-cleanup")
async def batch_cleanup_audio_files(
    days_old: int = Query(30, ge=1, description="清理多少天前的文件"),
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """批量清理舊音頻文件"""
    try:
        result = await service.batch_cleanup_audio_files(days_old)
        logger.info(f"管理員 {current_user['username']} 執行了批量清理音頻文件")
        return result
    except Exception as e:
        logger.error(f"批量清理音頻文件失敗: {e}")
        raise HTTPException(status_code=500, detail="批量清理音頻文件失敗")

@router.get("/queue-status")
async def get_tts_queue_status(
    service: TTSManagementService = Depends()
):
    """獲取 TTS 任務隊列狀態"""
    try:
        status = await service.get_tts_queue_status()
        return status
    except Exception as e:
        logger.error(f"獲取 TTS 隊列狀態失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取 TTS 隊列狀態失敗")

@router.post("/queue/clear")
async def clear_tts_queue(
    service: TTSManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("tts_management"))
):
    """清空 TTS 任務隊列"""
    try:
        result = await service.clear_tts_queue()
        logger.warning(f"管理員 {current_user['username']} 清空了 TTS 任務隊列")
        return result
    except Exception as e:
        logger.error(f"清空 TTS 隊列失敗: {e}")
        raise HTTPException(status_code=500, detail="清空 TTS 隊列失敗")


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()


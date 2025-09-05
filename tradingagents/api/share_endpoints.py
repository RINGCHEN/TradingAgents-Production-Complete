"""
社交分享API端點
提供分享圖片生成、分享追蹤和統計功能
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from ..services.share_service import get_share_service
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/share", tags=["share"])

class ShareImageRequest(BaseModel):
    result_id: str
    template_id: Optional[str] = "personality_result"
    force_regenerate: Optional[bool] = False

class ShareActionRequest(BaseModel):
    result_id: str
    platform: str
    share_text: Optional[str] = ""
    share_url: Optional[str] = ""
    user_agent: Optional[str] = ""
    referrer: Optional[str] = ""

class ShareStatsRequest(BaseModel):
    result_id: Optional[str] = None

@router.post("/generate-image")
async def generate_share_image(request: ShareImageRequest):
    """生成分享圖片"""
    
    try:
        share_service = get_share_service()
        
        result = await share_service.generate_share_image(
            result_id=request.result_id,
            template_id=request.template_id,
            force_regenerate=request.force_regenerate
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request for share image generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Failed to generate share image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate share image")

@router.post("/track-action")
async def track_share_action(request: ShareActionRequest, http_request: Request):
    """追蹤分享行為"""
    
    try:
        share_service = get_share_service()
        
        # 從HTTP請求中獲取額外信息
        share_data = {
            "result_id": request.result_id,
            "platform": request.platform,
            "share_text": request.share_text,
            "share_url": request.share_url,
            "user_agent": request.user_agent or http_request.headers.get("user-agent", ""),
            "referrer": request.referrer or http_request.headers.get("referer", "")
        }
        
        success = await share_service.track_share_action(share_data)
        
        return {
            "success": success,
            "message": "Share action tracked successfully" if success else "Failed to track share action"
        }
        
    except Exception as e:
        logger.error(f"Failed to track share action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track share action")

@router.get("/stats")
async def get_share_stats(result_id: Optional[str] = None):
    """獲取分享統計數據"""
    
    try:
        share_service = get_share_service()
        
        stats = await share_service.get_share_stats(result_id)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get share stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get share stats")

@router.get("/templates")
async def get_share_templates():
    """獲取可用的分享模板"""
    
    try:
        share_service = get_share_service()
        
        templates = {}
        for template_id, template in share_service.templates.items():
            templates[template_id] = {
                "id": template_id,
                "width": template.width,
                "height": template.height,
                "background_color": template.background_color,
                "text_color": template.text_color,
                "accent_color": template.accent_color,
                "layout": template.config.get('layout', 'default')
            }
        
        return {
            "success": True,
            "data": templates
        }
        
    except Exception as e:
        logger.error(f"Failed to get share templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get share templates")

@router.post("/cleanup-images")
async def cleanup_old_images(background_tasks: BackgroundTasks, days_old: int = 30):
    """清理舊的分享圖片（後台任務）"""
    
    try:
        share_service = get_share_service()
        
        # 在後台執行清理任務
        background_tasks.add_task(share_service.cleanup_old_images, days_old)
        
        return {
            "success": True,
            "message": f"Cleanup task scheduled for images older than {days_old} days"
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule cleanup task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule cleanup task")

@router.get("/result/{result_id}")
async def get_share_data(result_id: str, template_id: Optional[str] = "personality_result"):
    """獲取特定結果的分享數據（用於分享頁面）"""
    
    try:
        share_service = get_share_service()
        
        # 生成或獲取分享圖片
        share_data = await share_service.generate_share_image(
            result_id=result_id,
            template_id=template_id,
            force_regenerate=False
        )
        
        # 獲取測試結果數據
        result_data = await share_service._get_test_result(result_id)
        if not result_data:
            raise HTTPException(status_code=404, detail="Test result not found")
        
        return {
            "success": True,
            "data": {
                "share_image": share_data,
                "result": result_data,
                "meta_tags": {
                    "title": f"我的投資人格是 {result_data.get('personality_type', '未知')}",
                    "description": share_data.get('share_text', ''),
                    "image": share_data.get('image_url', ''),
                    "url": share_data.get('share_url', '')
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get share data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get share data")

@router.get("/preview/{result_id}")
async def preview_share_image(result_id: str, template_id: Optional[str] = "personality_result"):
    """預覽分享圖片（用於測試和調試）"""
    
    try:
        share_service = get_share_service()
        
        share_data = await share_service.generate_share_image(
            result_id=result_id,
            template_id=template_id,
            force_regenerate=True  # 強制重新生成以便預覽
        )
        
        return {
            "success": True,
            "data": {
                "image_url": share_data.get('image_url'),
                "share_text": share_data.get('share_text'),
                "template_id": template_id,
                "generated_at": share_data.get('created_at')
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to preview share image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to preview share image")
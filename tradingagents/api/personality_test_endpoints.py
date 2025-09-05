#!/usr/bin/env python3
"""
投資人格測試API端點
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..services.personality_test_service import PersonalityTestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personality-test", tags=["personality-test"])

# 請求模型
class StartTestRequest(BaseModel):
    user_info: Dict[str, Any] = {}

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    selected_option: int

# 響應模型
class TestSessionResponse(BaseModel):
    session_id: str
    total_questions: int
    current_question: int
    question: Dict[str, Any]

class SubmitAnswerResponse(BaseModel):
    completed: bool
    current_question: Optional[int] = None
    total_questions: Optional[int] = None
    question: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

# 服務實例
personality_test_service = PersonalityTestService()

@router.post("/start", response_model=TestSessionResponse)
async def start_test(request: StartTestRequest):
    """
    開始投資人格測試
    
    創建新的測試會話並返回第一個問題
    """
    try:
        result = await personality_test_service.start_test_session(request.user_info)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return TestSessionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"開始測試失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="測試會話創建失敗"
        )

@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    提交測試答案
    
    提交當前問題的答案並獲取下一個問題或測試結果
    """
    try:
        result = await personality_test_service.submit_answer(
            request.session_id,
            request.question_id,
            request.selected_option
        )
        
        if "error" in result:
            if result["error"] == "測試會話不存在":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["error"]
                )
            elif result["error"] in ["問題不存在", "選項無效"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["error"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["error"]
                )
        
        return SubmitAnswerResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交答案失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="答案提交失敗"
        )

@router.get("/result/{session_id}")
async def get_test_result(session_id: str):
    """
    獲取測試結果
    
    根據會話ID獲取完整的測試結果
    """
    try:
        result = await personality_test_service.get_test_result(session_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="測試結果不存在或測試尚未完成"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取測試結果失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取測試結果失敗"
        )

@router.get("/questions/preview")
async def preview_questions():
    """
    預覽測試問題
    
    返回所有測試問題的預覽（不包含權重信息）
    """
    try:
        questions = []
        for question in personality_test_service.questions:
            questions.append({
                "id": question.id,
                "scenario": question.scenario,
                "question": question.question,
                "options": [opt["text"] for opt in question.options]
            })
        
        return {
            "total_questions": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        logger.error(f"預覽問題失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="預覽問題失敗"
        )

@router.get("/personality-types")
async def get_personality_types():
    """
    獲取所有人格類型信息
    
    返回所有可能的投資人格類型及其描述
    """
    try:
        types_info = {}
        for personality_type, info in personality_test_service.personality_types.items():
            types_info[personality_type.value] = {
                "title": info["title"],
                "description": info["description"],
                "celebrity_comparison": info["celebrity_comparison"],
                "characteristics": info["characteristics"],
                "investment_style": info["investment_style"]
            }
        
        return types_info
        
    except Exception as e:
        logger.error(f"獲取人格類型失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取人格類型失敗"
        )

@router.get("/health")
async def health_check():
    """
    健康檢查端點
    
    檢查投資人格測試服務的健康狀態
    """
    try:
        # 簡單的健康檢查
        total_questions = len(personality_test_service.questions)
        total_personality_types = len(personality_test_service.personality_types)
        
        return {
            "status": "healthy",
            "service": "personality_test",
            "total_questions": total_questions,
            "total_personality_types": total_personality_types,
            "timestamp": "2025-01-08T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務健康檢查失敗"
        )
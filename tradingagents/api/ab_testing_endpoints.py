#!/usr/bin/env python3
"""
A/B測試API端點
Task 6.2 - A/B測試框架建立的REST API接口
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..services.ab_testing_service import ABTestingService
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])

# 數據模型
class ABTestCreateRequest(BaseModel):
    name: str = Field(..., description="測試名稱")
    description: str = Field("", description="測試描述")
    primary_metric: str = Field(..., description="主要指標")
    variants: List[Dict[str, Any]] = Field(..., description="變體配置列表")
    test_config: Optional[Dict[str, Any]] = Field(None, description="測試配置")

class UserAssignmentRequest(BaseModel):
    test_id: str = Field(..., description="測試ID")
    user_id: Optional[int] = Field(None, description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    user_attributes: Optional[Dict[str, Any]] = Field(None, description="用戶屬性")

class EventTrackingRequest(BaseModel):
    test_id: str = Field(..., description="測試ID")
    assignment_id: str = Field(..., description="分組ID")
    event_name: str = Field(..., description="事件名稱")
    event_data: Optional[Dict[str, Any]] = Field(None, description="事件數據")

class TestStatusRequest(BaseModel):
    test_id: str = Field(..., description="測試ID")
    action: str = Field(..., description="操作類型")
    reason: Optional[str] = Field(None, description="操作原因")

# 服務實例
ab_testing_service = ABTestingService()

@router.post("/create-test")
async def create_ab_test(request: ABTestCreateRequest):
    """
    創建A/B測試
    開發A/B測試系統：支持多變量測試
    """
    try:
        result = ab_testing_service.create_ab_test(
            name=request.name,
            description=request.description,
            primary_metric=request.primary_metric,
            variants=request.variants,
            test_config=request.test_config
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "創建測試失敗"))
        
        return {
            "success": True,
            "message": "A/B測試創建成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建A/B測試失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="創建A/B測試失敗")

@router.post("/assign-user")
async def assign_user_to_test(request: UserAssignmentRequest):
    """
    用戶測試分組
    實現流量分配：自動分配測試流量
    """
    try:
        result = ab_testing_service.assign_user_to_test(
            test_id=request.test_id,
            user_id=request.user_id,
            session_id=request.session_id,
            user_attributes=request.user_attributes
        )
        
        if not result.get("success"):
            if result.get("excluded"):
                return {
                    "success": False,
                    "excluded": True,
                    "reason": result.get("error", "用戶被排除在測試外")
                }
            raise HTTPException(status_code=400, detail=result.get("error", "用戶分組失敗"))
        
        return {
            "success": True,
            "message": "用戶分組成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用戶分組失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="用戶分組失敗")

@router.post("/track-event")
async def track_test_event(request: EventTrackingRequest):
    """
    追蹤測試事件
    """
    try:
        result = ab_testing_service.track_test_event(
            test_id=request.test_id,
            assignment_id=request.assignment_id,
            event_name=request.event_name,
            event_data=request.event_data
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "事件追蹤失敗"))
        
        return {
            "success": True,
            "message": "事件追蹤成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"事件追蹤失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="事件追蹤失敗")

@router.get("/test-results/{test_id}")
async def get_test_results(
    test_id: str,
    date_from: Optional[str] = Query(None, description="開始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="結束日期 (YYYY-MM-DD)")
):
    """
    獲取測試結果
    創建統計顯著性計算：確保測試結果可靠
    """
    try:
        # 解析日期參數
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
            except ValueError:
                raise HTTPException(status_code=400, detail="無效的開始日期格式")
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to)
            except ValueError:
                raise HTTPException(status_code=400, detail="無效的結束日期格式")
        
        result = ab_testing_service.get_test_results(
            test_id=test_id,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "獲取測試結果失敗"))
        
        return {
            "success": True,
            "message": "測試結果獲取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取測試結果失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取測試結果失敗")

@router.post("/manage-test-status")
async def manage_test_status(request: TestStatusRequest):
    """
    管理測試狀態
    建立測試結果儀表板：清晰展示測試效果
    """
    try:
        result = ab_testing_service.manage_test_status(
            test_id=request.test_id,
            action=request.action,
            reason=request.reason
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "測試狀態管理失敗"))
        
        return {
            "success": True,
            "message": f"測試狀態{request.action}成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測試狀態管理失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="測試狀態管理失敗")

@router.get("/dashboard")
async def get_test_dashboard(
    test_id: Optional[str] = Query(None, description="特定測試ID"),
    status_filter: Optional[str] = Query(None, description="狀態過濾器")
):
    """
    獲取測試儀表板
    建立測試結果儀表板：清晰展示測試效果
    """
    try:
        result = ab_testing_service.get_test_dashboard(
            test_id=test_id,
            status_filter=status_filter
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "獲取儀表板失敗"))
        
        return {
            "success": True,
            "message": "儀表板數據獲取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取儀表板失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取儀表板失敗")

@router.get("/test/{test_id}")
async def get_test_details(test_id: str):
    """
    獲取測試詳情
    """
    try:
        # 這裡應該調用服務獲取測試詳情
        if not hasattr(ab_testing_service, 'tests') or test_id not in ab_testing_service.tests:
            raise HTTPException(status_code=404, detail="測試不存在")
        
        test = ab_testing_service.tests[test_id]
        
        return {
            "success": True,
            "message": "測試詳情獲取成功",
            "data": {
                "id": test.id,
                "name": test.name,
                "description": test.description,
                "status": test.status,
                "primary_metric": test.primary_metric,
                "variants": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "type": v.variant_type,
                        "traffic_weight": v.traffic_weight,
                        "config": v.config
                    } for v in test.variants
                ],
                "created_at": test.created_at.isoformat(),
                "start_date": test.start_date.isoformat() if test.start_date else None,
                "end_date": test.end_date.isoformat() if test.end_date else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取測試詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取測試詳情失敗")

@router.get("/tests")
async def list_tests(
    status: Optional[str] = Query(None, description="狀態過濾"),
    limit: int = Query(10, description="返回數量限制"),
    offset: int = Query(0, description="偏移量")
):
    """
    獲取測試列表
    """
    try:
        # 獲取測試列表
        tests = list(ab_testing_service.tests.values()) if hasattr(ab_testing_service, 'tests') else []
        
        # 應用狀態過濾
        if status:
            tests = [t for t in tests if t.status == status]
        
        # 應用分頁
        total = len(tests)
        tests = tests[offset:offset + limit]
        
        return {
            "success": True,
            "message": "測試列表獲取成功",
            "data": {
                "tests": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "status": t.status,
                        "primary_metric": t.primary_metric,
                        "variant_count": len(t.variants),
                        "created_at": t.created_at.isoformat(),
                        "start_date": t.start_date.isoformat() if t.start_date else None
                    } for t in tests
                ],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"獲取測試列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取測試列表失敗")

@router.get("/health")
async def health_check():
    """
    A/B測試系統健康檢查
    """
    try:
        service_status = {
            "service": "ab_testing",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        if hasattr(ab_testing_service, 'tests'):
            service_status["tests_count"] = len(ab_testing_service.tests)
        else:
            service_status["tests_count"] = 0
        
        return {
            "success": True,
            "data": service_status
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }

@router.get("/statistics")
async def get_statistics():
    """
    獲取A/B測試統計信息
    """
    try:
        tests = list(ab_testing_service.tests.values()) if hasattr(ab_testing_service, 'tests') else []
        assignments = list(ab_testing_service.assignments.values()) if hasattr(ab_testing_service, 'assignments') else []
        events = list(ab_testing_service.events.values()) if hasattr(ab_testing_service, 'events') else []
        
        statistics = {
            "total_tests": len(tests),
            "active_tests": len([t for t in tests if t.status == "active"]),
            "completed_tests": len([t for t in tests if t.status == "completed"]),
            "total_participants": len(assignments),
            "total_events": len(events),
            "tests_by_status": {},
            "events_by_type": {}
        }
        
        # 按狀態統計測試
        for test in tests:
            status = test.status
            statistics["tests_by_status"][status] = statistics["tests_by_status"].get(status, 0) + 1
        
        # 按類型統計事件
        for event in events:
            event_type = event.event_type
            statistics["events_by_type"][event_type] = statistics["events_by_type"].get(event_type, 0) + 1
        
        return {
            "success": True,
            "message": "統計信息獲取成功",
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"獲取統計信息失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="獲取統計信息失敗")
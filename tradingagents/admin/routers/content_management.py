#!/usr/bin/env python3
"""
內容管理路由器 (Content Management Router)
天工 (TianGong) - 內容管理 API 端點
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..models.content_management import (
    ContentItemListResponse, ContentItemResponse, ContentItemCreateRequest, ContentItemUpdateRequest
)
from ...database.database import get_db
from ...auth.dependencies import require_admin_access
from ...utils.logging_config import get_api_logger

# 配置日誌
api_logger = get_api_logger("content_management")

# 創建路由器
router = APIRouter(prefix="/content", tags=["內容管理"])

@router.get("/", response_model=ContentItemListResponse, summary="獲取內容列表")
async def get_content_items(
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(10, ge=1, le=100, description="每頁數量"),
    search: str = Query(None, description="搜索關鍵字"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access())
):
    """獲取內容列表，支持分頁和搜索"""
    from ..services.content_management_service import ContentManagementService
    service = ContentManagementService(db)
    result = await service.get_content_items(page=page, limit=limit, search=search)
    return result

@router.post("/", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED, summary="創建新內容")
async def create_content_item(
    item_data: ContentItemCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access())
):
    """創建一個新的內容項目"""
    from ..services.content_management_service import ContentManagementService
    service = ContentManagementService(db)
    new_item = await service.create_content_item(item_data)
    api_logger.info(f"Admin user {current_user.user_id} created content item {new_item['id']}")
    return new_item

@router.get("/{item_id}", response_model=ContentItemResponse, summary="獲取單個內容")
async def get_content_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access())
):
    """根據ID獲取單個內容項目的詳細信息"""
    from ..services.content_management_service import ContentManagementService
    service = ContentManagementService(db)
    item = await service.get_content_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="內容不存在")
    return item

@router.put("/{item_id}", response_model=ContentItemResponse, summary="更新內容")
async def update_content_item(
    item_id: int,
    item_data: ContentItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access())
):
    """更新一個現有的內容項目"""
    from ..services.content_management_service import ContentManagementService
    service = ContentManagementService(db)
    updated_item = await service.update_content_item(item_id, item_data)
    if not updated_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="內容不存在")
    api_logger.info(f"Admin user {current_user.user_id} updated content item {item_id}")
    return updated_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="刪除內容")
async def delete_content_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access())
):
    """刪除一個內容項目"""
    from ..services.content_management_service import ContentManagementService
    service = ContentManagementService(db)
    success = await service.delete_content_item(item_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="內容不存在")
    api_logger.info(f"Admin user {current_user.user_id} deleted content item {item_id}")
    return

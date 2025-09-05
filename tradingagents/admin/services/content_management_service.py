#!/usr/bin/env python3
"""
內容管理服務 (Content Management Service)
天工 (TianGong) - 處理內容管理的業務邏輯
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any

# 暫時使用模擬數據，未來將替換為真實的數據庫操作
from ..models.mock_data import MOCK_CONTENT_ITEMS
from ..models.content_management import ContentItemCreateRequest, ContentItemUpdateRequest

class ContentManagementService:
    def __init__(self, db: Session):
        self.db = db
        # 在真實應用中，self.db 將被用來與數據庫交互

    async def get_content_items(self, page: int, limit: int, search: str) -> Dict[str, Any]:
        """獲取內容列表 (目前使用模擬數據)"""
        print(f"Fetching content items: page={page}, limit={limit}, search={search}")
        
        items = MOCK_CONTENT_ITEMS
        if search:
            items = [item for item in items if search.lower() in item['title'].lower()]
        
        total = len(items)
        start = (page - 1) * limit
        end = start + limit
        paginated_items = items[start:end]

        return {
            "items": paginated_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def get_content_item(self, item_id: int) -> Dict[str, Any]:
        """獲取單個內容項目 (目前使用模擬數據)"""
        print(f"Fetching content item with id: {item_id}")
        for item in MOCK_CONTENT_ITEMS:
            if item['id'] == item_id:
                return item
        return None

    async def create_content_item(self, item_data: ContentItemCreateRequest) -> Dict[str, Any]:
        """創建內容項目 (目前使用模擬數據)"""
        print(f"Creating content item with title: {item_data.title}")
        new_id = max(item['id'] for item in MOCK_CONTENT_ITEMS) + 1
        new_item = {
            "id": new_id,
            "author": item_data.author or "default_author",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **item_data.dict()
        }
        MOCK_CONTENT_ITEMS.append(new_item)
        return new_item

    async def update_content_item(self, item_id: int, item_data: ContentItemUpdateRequest) -> Dict[str, Any]:
        """更新內容項目 (目前使用模擬數據)"""
        print(f"Updating content item with id: {item_id}")
        for item in MOCK_CONTENT_ITEMS:
            if item['id'] == item_id:
                update_data = item_data.dict(exclude_unset=True)
                item.update(update_data)
                item['updated_at'] = datetime.utcnow()
                return item
        return None

    async def delete_content_item(self, item_id: int) -> bool:
        """刪除內容項目 (目前使用模擬數據)"""
        print(f"Deleting content item with id: {item_id}")
        original_length = len(MOCK_CONTENT_ITEMS)
        MOCK_CONTENT_ITEMS[:] = [item for item in MOCK_CONTENT_ITEMS if item['id'] != item_id]
        return len(MOCK_CONTENT_ITEMS) < original_length

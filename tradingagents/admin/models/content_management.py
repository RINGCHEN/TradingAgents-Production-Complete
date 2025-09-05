#!/usr/bin/env python3
"""
內容管理數據模型 (Content Management Models)
天工 (TianGong) - 定義內容管理的請求和響應數據結構
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- 基礎模型 ---

class ContentItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="內容標題")
    category: str = Field(..., description="內容分類")
    status: str = Field(..., description="內容狀態 (e.g., '草稿', '已發布')")
    content: str = Field(..., description="主要內容")

# --- 請求模型 ---

class ContentItemCreateRequest(ContentItemBase):
    author: Optional[str] = Field(None, description="作者")

class ContentItemUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="內容標題")
    category: Optional[str] = Field(None, description="內容分類")
    status: Optional[str] = Field(None, description="內容狀態")
    content: Optional[str] = Field(None, description="主要內容")

# --- 響應模型 ---

class ContentItemResponse(ContentItemBase):
    id: int
    author: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    pages: int

class ContentItemListResponse(BaseModel):
    items: List[ContentItemResponse]
    pagination: Pagination

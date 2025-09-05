#!/usr/bin/env python3
"""
後端模擬數據 (Backend Mock Data)
"""

from datetime import datetime, timedelta

MOCK_CONTENT_ITEMS = [
    {
        "id": 101,
        "title": "TradingAgents AI 引擎完成重大升級",
        "category": "新聞",
        "status": "已發布",
        "author": "admin",
        "content": "這是一篇關於AI引擎升級的詳細內容...",
        "created_at": datetime.utcnow() - timedelta(days=2),
        "updated_at": datetime.utcnow() - timedelta(days=1),
    },
    {
        "id": 102,
        "title": "系統將於週末進行維護",
        "category": "公告",
        "status": "已發布",
        "author": "system_bot",
        "content": "為了提供更好的服務，系統將於本週末進行維護...",
        "created_at": datetime.utcnow() - timedelta(days=3),
        "updated_at": datetime.utcnow() - timedelta(days=3),
    },
    {
        "id": 103,
        "title": "第三季台股市場趨勢分析報告",
        "category": "分析",
        "status": "草稿",
        "author": "analyst_jane",
        "content": "本報告深入分析了第三季度台灣股市的整體趨勢...",
        "created_at": datetime.utcnow() - timedelta(days=4),
        "updated_at": datetime.utcnow(),
    },
]

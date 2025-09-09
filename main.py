#!/usr/bin/env python3
"""
TradingAgents AI投資分析系統 - Google Cloud Run 簡化啟動點
天工(TianGong) 專業級主要入口點

直接啟動FastAPI應用，避免複雜的初始化
"""

import os
import sys
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置環境變數
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('LOG_LEVEL', 'INFO')

# 直接導入並返回簡化的FastAPI應用
from tradingagents.simple_app import app

# 這就是應用入口點
# Cloud Run會通過gunicorn調用這個模組
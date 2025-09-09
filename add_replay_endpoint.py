#!/usr/bin/env python3
"""
為生產環境添加replay端點的腳本
將我們的Emergency API邏輯整合到生產服務器中
"""

import os
import sys
from pathlib import Path

# 生產環境路徑
PRODUCTION_DIR = Path(__file__).parent
TRADINGAGENTS_DIR = PRODUCTION_DIR / "tradingagents"

def create_replay_endpoints():
    """創建replay_endpoints.py文件"""
    
    replay_content = '''#!/usr/bin/env python3
"""
Replay Decision API端點 - 生產環境版本
實現4層級用戶價值階梯系統
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json
import base64
import logging
from datetime import datetime, timedelta

# 設置日誌
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1", tags=["replay"])

class ReplayDecisionRequest(BaseModel):
    stock_symbol: str = Field(..., description="股票代碼，如：2330")
    
class ReplayDecisionResponse(BaseModel):
    user_tier: str = Field(..., description="用戶層級")
    trial_days_remaining: Optional[int] = Field(None, description="試用期剩餘天數")
    analysis: Dict[str, Any] = Field(..., description="股票分析結果")
    upgrade_prompt: Optional[str] = Field(None, description="升級提示")

def decode_test_token(authorization_header: str) -> Dict[str, Any]:
    """解碼測試Token"""
    try:
        if not authorization_header.startswith("Bearer "):
            return {}
        
        token = authorization_header[7:]  # Remove "Bearer "
        decoded = base64.b64decode(token).decode()
        return json.loads(decoded)
    except Exception as e:
        logger.warning(f"Token解碼失敗: {e}")
        return {}

def determine_user_tier(authorization_header: Optional[str]) -> tuple[str, Optional[int]]:
    """確定用戶層級和試用天數"""
    if not authorization_header:
        return "visitor", None
    
    payload = decode_test_token(authorization_header)
    if not payload:
        return "visitor", None
    
    tier = payload.get("tier", "visitor")
    
    # 計算試用期剩餘天數
    trial_days_remaining = None
    if tier == "trial":
        created_at_str = payload.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                days_since_creation = (datetime.now() - created_at.replace(tzinfo=None)).days
                trial_days_remaining = max(0, 7 - days_since_creation)
            except:
                trial_days_remaining = 5  # 預設值
    
    return tier, trial_days_remaining

def get_stock_analysis(stock_symbol: str, user_tier: str) -> Dict[str, Any]:
    """獲取股票分析（模擬數據）"""
    
    base_analysis = {
        "technical_analysis": f"📈 {stock_symbol} 技術分析顯示目前處於上升趋勢，RSI指標為65，MACD呈現黃金交叉格局。",
        "fundamental_analysis": f"💰 {stock_symbol} 基本面分析：本季EPS成長15%，ROE維持在20%以上，財務結構穩健。",
        "news_sentiment": f"📰 {stock_symbol} 近期新聞情感分析：市場對該股票保持樂觀態度，機構投資人增持。"
    }
    
    # 只有試用和付費用戶才能看到投資建議
    if user_tier in ["trial", "paid"]:
        base_analysis["recommendation"] = {
            "action": "buy",
            "confidence": 85,
            "target_price": 580,
            "reasoning": "基於技術面和基本面分析，建議適量買入並設定停利點於600元。"
        }
    
    return base_analysis

def get_upgrade_prompt(user_tier: str) -> Optional[str]:
    """獲取升級提示"""
    if user_tier == "visitor":
        return "註冊立即享受7天完整功能體驗，包含專業投資建議！"
    elif user_tier == "free":
        return "升級至付費會員，獲得完整投資建議和目標價位分析！"
    return None

@router.post("/replay/decision", response_model=ReplayDecisionResponse)
async def get_replay_decision(
    request: ReplayDecisionRequest,
    http_request: Request
) -> ReplayDecisionResponse:
    """
    獲取股票決策復盤分析
    根據用戶層級返回不同詳細度的分析結果
    """
    try:
        # 獲取Authorization header
        authorization = http_request.headers.get("Authorization")
        
        # 確定用戶層級
        user_tier, trial_days_remaining = determine_user_tier(authorization)
        
        logger.info(f"處理 {request.stock_symbol} 的請求，用戶層級：{user_tier}")
        
        # 獲取分析數據
        analysis = get_stock_analysis(request.stock_symbol, user_tier)
        
        # 構建回應
        response_data = {
            "user_tier": user_tier,
            "analysis": analysis
        }
        
        # 添加試用期資訊
        if trial_days_remaining is not None:
            response_data["trial_days_remaining"] = trial_days_remaining
        
        # 添加升級提示
        upgrade_prompt = get_upgrade_prompt(user_tier)
        if upgrade_prompt:
            response_data["upgrade_prompt"] = upgrade_prompt
        
        return ReplayDecisionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")

# 健康檢查端點
@router.get("/replay/health")
async def replay_health():
    """Replay服務健康檢查"""
    return {
        "service": "replay_decision",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
'''
    
    # 創建文件
    replay_file = TRADINGAGENTS_DIR / "api" / "replay_endpoints.py"
    
    # 確保目錄存在
    replay_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 寫入文件
    with open(replay_file, 'w', encoding='utf-8') as f:
        f.write(replay_content)
    
    print(f"✅ 已創建: {replay_file}")
    return replay_file

def update_main_app():
    """更新主應用以包含replay端點"""
    
    app_file = TRADINGAGENTS_DIR / "app.py"
    
    if not app_file.exists():
        print(f"❌ 找不到主應用文件: {app_file}")
        return False
    
    # 讀取現有內容
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經包含replay_endpoints
    if "replay_endpoints" in content:
        print("✅ app.py 已包含replay_endpoints導入")
        return True
    
    # 添加導入和註冊
    replay_import = "from .api import replay_endpoints"
    replay_register = 'app.include_router(replay_endpoints.router, prefix="", tags=["replay"])'
    
    # 查找合適的位置插入
    lines = content.split('\n')
    new_lines = []
    import_added = False
    router_added = False
    
    for line in lines:
        new_lines.append(line)
        
        # 在其他API導入後添加replay導入
        if not import_added and line.strip().startswith("from .api import") and "replay" not in line:
            new_lines.append(replay_import)
            import_added = True
        
        # 在其他router註冊後添加replay router
        if not router_added and "app.include_router" in line and "replay" not in line:
            new_lines.append(replay_register)
            router_added = True
    
    # 如果沒找到合適位置，在文件末尾添加
    if not import_added:
        new_lines.insert(-5, replay_import)
    if not router_added:
        new_lines.append(replay_register)
    
    # 寫回文件
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✅ 已更新: {app_file}")
    return True

def main():
    """主函數"""
    print("🔧 為生產環境添加Replay端點")
    print("=" * 50)
    
    # 1. 創建replay_endpoints.py
    replay_file = create_replay_endpoints()
    
    # 2. 更新主應用
    if update_main_app():
        print("\n✅ Replay端點添加完成")
        print("🔄 請重啟生產服務器以載入新端點")
        print(f"   python start_production_server_port_8004.py")
        return True
    else:
        print("\n❌ 更新主應用失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
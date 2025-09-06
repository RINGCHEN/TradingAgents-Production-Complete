#!/usr/bin/env python3
"""
PayUni 支付 API 端點
TradingAgents 系統的 PayUni 支付處理端點
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..models.user import User
from ..database.database import get_db
from ..utils.auth import get_current_user
from ..utils.logging_config import get_logger
from ..payments.gateways.payuni import create_payuni_gateway, PayUniWebhookHandler
from ..services.payment_service import PaymentTransactionService
from ..services.refund_service import create_refund_service, RefundStatus, RefundReason, RefundType, get_refund_policy_info

logger = get_logger(__name__)
router = APIRouter(prefix="/payuni", tags=["payuni"])

# PayUni配置 (正式生產環境)
import os
PAYUNI_CONFIG = {
    "merchant_id": os.getenv("PAYUNI_MERCHANT_ID", "U03823060"),
    "hash_key": os.getenv("PAYUNI_HASH_KEY", "kfud6pP4HFbGuJ9T4YBU4p85a7W9OhoU"),
    "hash_iv": os.getenv("PAYUNI_HASH_IV", "maO3kqxZObzGTnBu"),
    "is_sandbox": os.getenv("PAYUNI_SANDBOX", "false").lower() == "true"
}

# 配置驗證
if not PAYUNI_CONFIG["merchant_id"] or not PAYUNI_CONFIG["hash_key"] or not PAYUNI_CONFIG["hash_iv"]:
    logger.warning("PayUni配置不完整，請檢查環境變數設定")

logger.info(f"PayUni配置載入: 商店={PAYUNI_CONFIG['merchant_id']}, 環境={'沙盒' if PAYUNI_CONFIG['is_sandbox'] else '正式'}")

# 專門的 OPTIONS 處理器解決 CORS 問題
@router.options("/create-guest-payment")
async def create_guest_payment_options():
    """處理 PayUni 創建支付的 OPTIONS 預檢請求"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
    )

@router.post("/create-guest-payment")
async def create_guest_payment(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    創建訪客PayUni支付訂單 (無需認證)
    正確處理PayUni API要求的加密參數格式
    """
    try:
        # 獲取請求數據
        body = await request.json()
        logger.info(f"收到訪客支付請求: {body}")

        # 驗證必要參數
        required_fields = ['tier_type', 'amount', 'description']
        for field in required_fields:
            if field not in body:
                raise HTTPException(
                    status_code=400, 
                    detail=f"缺少必要參數: {field}"
                )

        # 生成唯一訂單號
        order_number = f"GUEST_{int(datetime.now().timestamp())}_{body['tier_type']}"
        
        # 準備PayUni支付數據
        payment_data = {
            "order_number": order_number,
            "amount": int(body['amount']),
            "description": body['description'],
            "item_name": f"TradingAgents {body['tier_type'].title()} 方案",
            "return_url": body.get('return_url', 'https://03king.com/payment/success'),
            "notify_url": 'https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/webhook',
            "customer_url": body.get('customer_url', 'https://03king.com/payment/cancel'),
            "client_back_url": body.get('client_back_url', 'https://03king.com/pricing'),
            "email": "guest@03king.com",
            "comment": f"TradingAgents {body['tier_type']} 方案 - {body.get('billing_cycle', 'yearly')}",
            "expire_date": datetime.now().strftime('%Y-%m-%d'),  # 當日有效
        }

        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            merchant_id=PAYUNI_CONFIG["merchant_id"],
            hash_key=PAYUNI_CONFIG["hash_key"], 
            hash_iv=PAYUNI_CONFIG["hash_iv"],
            is_sandbox=PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 創建支付訂單
        payment_result = gateway.create_payment(payment_data)
        
        if payment_result['success']:
            logger.info(f"訪客PayUni支付創建成功: {order_number}")
            
            # 創建本地支付頁面URL，該頁面會自動POST提交到PayUni
            payment_page_url = f"/api/v1/payuni/payment-page/{order_number}"
            
            # 暫存支付數據供支付頁面使用 (在實際應用中應該使用Redis或資料庫)
            import json
            payment_cache = {
                "post_data": payment_result.get('post_data', {}),
                "payment_url": payment_result['payment_url'],
                "order_number": order_number
            }
            
            # 簡化版: 將數據編碼在URL中 (生產環境應使用secure storage)
            import base64
            encoded_data = base64.b64encode(json.dumps(payment_cache).encode()).decode()
            full_payment_url = f"https://coral-app-knueo.ondigitalocean.app{payment_page_url}?data={encoded_data}"
            
            return {
                "success": True,
                "payment_url": full_payment_url,
                "order_number": order_number,
                "message": "訪客支付創建成功"
            }
        else:
            logger.error(f"PayUni支付創建失敗: {payment_result.get('error', '未知錯誤')}")
            raise HTTPException(
                status_code=500,
                detail=f"支付創建失敗: {payment_result.get('error', '未知錯誤')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"訪客支付處理異常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"支付處理失敗: {str(e)}"
        )


@router.get("/payment-page/{order_number}")
async def payuni_payment_page(order_number: str, data: Optional[str] = None):
    """
    PayUni 支付中間頁面 - 自動POST提交到PayUni
    """
    try:
        # 處理沒有data參數的情況 (404錯誤修復)
        if not data:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PayUni 支付確認 - TradingAgents</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .title {{ font-size: 2rem; margin-bottom: 20px; }}
        .message {{ font-size: 1.1rem; line-height: 1.6; margin-bottom: 30px; }}
        .button {{ 
            display: inline-block;
            padding: 12px 30px;
            background: #ff6b6b;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
        }}
        .button:hover {{ background: #ff5252; transform: translateY(-2px); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="title">🔄 PayUni 支付處理中</div>
        <div class="message">
            訂單編號: {order_number}<br>
            正在準備支付資訊，請稍候...
        </div>
        <a href="https://03king.com/pricing" class="button">返回定價頁面</a>
    </div>
    <script>
        // 3秒後自動跳轉回定價頁面
        setTimeout(() => {{
            window.location.href = 'https://03king.com/pricing';
        }}, 3000);
    </script>
</body>
</html>"""
            return HTMLResponse(content=html_content)
        
        import json
        import base64
        
        # 解碼支付數據
        payment_data = json.loads(base64.b64decode(data.encode()).decode())
        
        # 生成HTML頁面，自動POST提交到PayUni
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>跳轉到 PayUni 支付頁面</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .payment-container {{
            text-align: center;
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .loader {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="payment-container">
        <h2>正在跳轉到 PayUni 支付頁面...</h2>
        <div class="loader"></div>
        <p>請稍候，系統正在為您準備安全的支付環境</p>
        <p><small>訂單號: {order_number}</small></p>
    </div>

    <form id="payuniForm" method="post" action="{payment_data['payment_url']}">
        <input type="hidden" name="MerchantID" value="{payment_data['post_data']['MerchantID']}">
        <input type="hidden" name="TradeInfo" value="{payment_data['post_data']['TradeInfo']}">
        <input type="hidden" name="TradeSha" value="{payment_data['post_data']['TradeSha']}">
        <input type="hidden" name="Version" value="{payment_data['post_data']['Version']}">
    </form>

    <script>
        // 自動提交表單
        window.onload = function() {{
            document.getElementById('payuniForm').submit();
        }};
        
        // 3秒後如果沒有自動跳轉，顯示手動提交按鈕
        setTimeout(function() {{
            if (document.getElementById('payuniForm')) {{
                var container = document.querySelector('.payment-container');
                container.innerHTML += '<br><button onclick="document.getElementById(\\'payuniForm\\').submit();" style="padding: 10px 20px; font-size: 16px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">點擊繼續支付</button>';
            }}
        }}, 3000);
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"支付頁面生成失敗: {str(e)}")
        return HTMLResponse(
            content=f"""
            <html><body style="text-align:center; padding:50px;">
                <h2>支付頁面載入失敗</h2>
                <p>錯誤: {str(e)}</p>
                <a href="https://03king.com/pricing">返回定價頁面</a>
            </body></html>
            """,
            status_code=500
        )


@router.post("/test-payment")
async def create_test_payuni_payment(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    測試用PayUni支付訂單創建 (無需認證)
    """
    try:
        # 獲取請求數據
        body = await request.json()
        subscription_id = body.get("subscription_id", 1)
        amount = body.get("amount", 1999)
        description = body.get("description", "TradingAgents會員訂閱")
        tier_type = body.get("tier_type", "gold")
        
        logger.info(f"收到測試PayUni支付請求: {body}")
        
        # 模擬用戶
        test_user_email = "test@tradingagents.com"
        
        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 生成訂單號
        import uuid
        order_number = f"TEST{int(datetime.now().timestamp())}{str(uuid.uuid4())[:8]}"
        
        # 準備支付數據 (測試環境URL)
        payment_data = {
            "order_number": order_number,
            "amount": amount,
            "description": description,
            "item_name": f"{tier_type}會員訂閱",
            "email": test_user_email,
            "return_url": "https://03king.web.app/payment/success",
            "notify_url": "https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/webhook/notify",
            "customer_url": "https://03king.web.app/payment/result",
            "client_back_url": "https://03king.web.app/payment/cancel"
        }
        
        logger.info(f"準備創建PayUni測試支付: {payment_data}")
        
        # 創建支付訂單
        result = gateway.create_payment(payment_data)
        
        if result["success"]:
            logger.info(f"PayUni測試支付訂單創建成功: {order_number}")
            
            return {
                "success": True,
                "order_number": order_number,
                "payment_url": result["payment_url"],
                "post_data": result["post_data"],
                "message": "測試支付訂單創建成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"支付訂單創建失敗: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建PayUni測試支付失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建測試支付失敗"
        )


@router.post("/create-payment")
async def create_payuni_payment(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    創建PayUni支付訂單
    """
    try:
        # 解析 JSON 請求數據
        body = await request.json()
        subscription_id = int(body.get("subscription_id", 1))
        amount = float(body.get("amount", 0))
        description = body.get("description", "TradingAgents會員訂閱")
        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 生成訂單號
        import uuid
        order_number = f"TA{int(datetime.now().timestamp())}{str(uuid.uuid4())[:8]}"
        
        # 準備支付數據 (生產環境URL)
        payment_data = {
            "order_number": order_number,
            "amount": amount,
            "description": description,
            "item_name": "TradingAgents會員訂閱",
            "email": current_user.email,
            "return_url": "https://03king.com/payment/success",
            "notify_url": "https://coral-app-knueo.ondigitalocean.app/api/v1/payuni/webhook/notify",
            "customer_url": "https://03king.com/payment/result",
            "client_back_url": "https://03king.com/payment/cancel"
        }
        
        # 創建支付訂單
        result = gateway.create_payment(payment_data)
        
        if result["success"]:
            # 記錄支付交易到數據庫
            transaction_service = PaymentTransactionService(db)
            
            # 創建交易數據
            transaction_data = {
                "user_id": current_user.id,
                "subscription_id": subscription_id,
                "amount": amount,
                "currency": "TWD",
                "payment_method": "payuni",
                "payuni_trade_no": order_number,
                "idempotency_key": f"payuni_{order_number}",
                "metadata": {
                    "description": description,
                    "item_name": "TradingAgents會員訂閱"
                }
            }
            
            transaction = transaction_service.create_transaction(transaction_data)
            
            if not transaction["success"]:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"交易記錄創建失敗: {transaction['error']}"
                )
            
            logger.info(f"PayUni支付訂單創建成功: {order_number} (用戶: {current_user.email})")
            
            return {
                "success": True,
                "order_number": order_number,
                "payment_url": result["payment_url"],
                "post_data": result["post_data"],
                "message": "支付訂單創建成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"支付訂單創建失敗: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建PayUni支付失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建支付失敗"
        )


@router.post("/webhook/notify")
async def payuni_webhook_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    PayUni支付通知Webhook
    """
    try:
        # 獲取POST數據
        form_data = await request.form()
        callback_data = dict(form_data)
        
        logger.info(f"收到PayUni通知: {callback_data}")
        
        # 創建PayUni閘道和處理器
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        webhook_handler = PayUniWebhookHandler(gateway)
        
        # 處理支付通知
        result = await webhook_handler.handle_payment_notify(callback_data)
        
        if result["success"]:
            # 更新本地交易狀態
            transaction_service = PaymentTransactionService(db)
            
            # 從callback_data解析交易信息
            verification_result = gateway.verify_callback(callback_data)
            if verification_result["success"]:
                trade_data = verification_result["trade_data"]
                payment_status = verification_result["status"]
                trade_no = trade_data.get("TradeNo", "")
                
                # 更新交易狀態
                update_result = transaction_service.update_transaction_status(
                    trade_no, payment_status, trade_data
                )
                
                if update_result["success"]:
                    logger.info(f"支付狀態同步成功: {trade_no} -> {payment_status}")
                else:
                    logger.error(f"支付狀態同步失敗: {update_result['error']}")
            
            # 返回PayUni要求的格式
            return result["response"]
        else:
            return result["response"]
            
    except Exception as e:
        logger.error(f"PayUni通知處理失敗: {str(e)}")
        return "0|處理失敗"


@router.get("/webhook/return")
@router.post("/webhook/return")
async def payuni_return_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    PayUni用戶返回頁面
    """
    try:
        # 獲取返回參數
        if request.method == "GET":
            params = dict(request.query_params)
        else:
            form_data = await request.form()
            params = dict(form_data)
        
        logger.info(f"PayUni用戶返回: {params}")
        
        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 驗證返回數據
        verification_result = gateway.verify_callback(params)
        
        if verification_result["success"]:
            trade_data = verification_result["trade_data"]
            payment_status = verification_result["status"]
            
            # 生成返回頁面HTML
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-TW">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>支付結果 - TradingAgents</title>
                <style>
                    body {{
                        font-family: 'Microsoft JhengHei', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 20px;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{
                        background: white;
                        border-radius: 15px;
                        padding: 40px;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                    }}
                    .success {{ color: #28a745; }}
                    .failed {{ color: #dc3545; }}
                    .pending {{ color: #ffc107; }}
                    .icon {{
                        font-size: 64px;
                        margin-bottom: 20px;
                    }}
                    .btn {{
                        background: #667eea;
                        color: white;
                        padding: 12px 30px;
                        border: none;
                        border-radius: 25px;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 20px;
                        transition: background 0.3s;
                    }}
                    .btn:hover {{
                        background: #5a6fd8;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    {"<div class='icon'>✅</div><h2 class='success'>支付成功！</h2>" if payment_status == "completed" else 
                     "<div class='icon'>❌</div><h2 class='failed'>支付失敗</h2>" if payment_status == "failed" else
                     "<div class='icon'>⏳</div><h2 class='pending'>支付處理中</h2>"}
                    
                    <p><strong>訂單號碼:</strong> {trade_data.get('TradeNo', 'N/A')}</p>
                    <p><strong>支付金額:</strong> NT$ {trade_data.get('TradeAmt', 'N/A')}</p>
                    <p><strong>支付時間:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    {"<p>感謝您的訂閱！您的會員權益已經生效。</p>" if payment_status == "completed" else
                     "<p>支付未成功，請聯繫客服或重新嘗試。</p>" if payment_status == "failed" else
                     "<p>支付正在處理中，請稍候查看結果。</p>"}
                    
                    <a href="http://localhost:3000/dashboard" class="btn">返回首頁</a>
                </div>
                
                <script>
                    // 3秒後自動跳轉
                    setTimeout(function() {{
                        window.location.href = 'http://localhost:3000/dashboard';
                    }}, 3000);
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        else:
            # 驗證失敗，返回錯誤頁面
            error_html = """
            <!DOCTYPE html>
            <html lang="zh-TW">
            <head>
                <meta charset="UTF-8">
                <title>支付驗證失敗 - TradingAgents</title>
            </head>
            <body>
                <div style="text-align: center; padding: 50px;">
                    <h2 style="color: #dc3545;">支付驗證失敗</h2>
                    <p>無法驗證支付結果，請聯繫客服。</p>
                    <a href="http://localhost:3000" style="color: #007bff;">返回首頁</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html)
            
    except Exception as e:
        logger.error(f"PayUni返回頁面處理失敗: {str(e)}")
        return HTMLResponse(content=f"<h2>處理失敗: {str(e)}</h2>")


@router.get("/query/{trade_no}")
async def query_payuni_payment(
    trade_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查詢PayUni支付狀態
    """
    try:
        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 查詢支付狀態
        result = await gateway.query_payment(trade_no)
        
        if result["success"]:
            logger.info(f"PayUni支付查詢成功: {trade_no}")
            return {
                "success": True,
                "trade_no": trade_no,
                "status": result["status"],
                "trade_data": result["trade_data"]
            }
        else:
            return {
                "success": False,
                "trade_no": trade_no,
                "error": result["error"]
            }
            
    except Exception as e:
        logger.error(f"PayUni支付查詢失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢支付狀態失敗"
        )


@router.get("/config")
async def get_payuni_config(
    current_user: User = Depends(get_current_user)
):
    """
    獲取PayUni配置信息（不包含敏感信息）
    """
    try:
        return {
            "merchant_id": PAYUNI_CONFIG["merchant_id"],
            "is_sandbox": PAYUNI_CONFIG["is_sandbox"],
            "supported_methods": [
                "credit_card",
                "webatm",
                "vacc",
                "barcode"
            ],
            "currency": "TWD"
        }
        
    except Exception as e:
        logger.error(f"獲取PayUni配置失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取配置失敗"
        )


# ================================
# 退款相關 API 端點
# ================================

@router.post("/refund/create")
async def create_refund_request(
    transaction_id: str,
    refund_amount: Optional[float] = None,
    refund_reason: RefundReason = RefundReason.USER_REQUEST,
    description: str = "",
    refund_type: RefundType = RefundType.FULL,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    創建退款申請
    """
    try:
        # 創建退款服務
        refund_service = create_refund_service(db, PAYUNI_CONFIG)
        
        # 準備退款數據
        refund_data = {
            "amount": refund_amount,
            "reason": refund_reason,
            "description": description or f"用戶 {current_user.email} 申請退款",
            "refund_type": refund_type
        }
        
        # 創建退款申請
        result = await refund_service.create_refund_request(
            current_user.id,
            transaction_id,
            refund_data
        )
        
        if result["success"]:
            logger.info(f"退款申請創建成功: {result['refund_request_id']} (用戶: {current_user.email})")
            
            return {
                "success": True,
                "refund_request_id": result["refund_request_id"],
                "amount": result["amount"],
                "status": result["status"],
                "auto_approved": result["auto_approved"],
                "message": result["message"],
                "calculation_note": result.get("calculation_note", "")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建退款申請失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建退款申請失敗"
        )


@router.post("/refund/{refund_request_id}/process")
async def process_refund_request(
    refund_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    處理退款申請 (管理員功能或系統自動處理)
    """
    try:
        # 創建退款服務
        refund_service = create_refund_service(db, PAYUNI_CONFIG)
        
        # 處理退款
        result = await refund_service.process_refund(refund_request_id)
        
        if result["success"]:
            logger.info(f"退款處理成功: {refund_request_id} -> {result.get('payuni_refund_no')}")
            
            return {
                "success": True,
                "refund_request_id": refund_request_id,
                "payuni_refund_no": result.get("payuni_refund_no"),
                "status": result["status"],
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理退款申請失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="處理退款申請失敗"
        )


@router.get("/refund/{refund_request_id}/status")
async def get_refund_status(
    refund_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查詢退款狀態
    """
    try:
        # 創建退款服務
        refund_service = create_refund_service(db, PAYUNI_CONFIG)
        
        # 查詢退款狀態
        result = await refund_service.query_refund_status(refund_request_id)
        
        if result["success"]:
            refund_request = result["refund_request"]
            
            # 檢查權限 (用戶只能查詢自己的退款)
            if refund_request["user_id"] != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="無權限查詢此退款申請"
                )
            
            return {
                "success": True,
                "refund_request": refund_request,
                "payuni_status": result.get("payuni_status")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢退款狀態失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢退款狀態失敗"
        )


@router.get("/refund/my-refunds")
async def get_my_refunds(
    status: Optional[RefundStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取當前用戶的退款記錄
    """
    try:
        # 創建退款服務
        refund_service = create_refund_service(db, PAYUNI_CONFIG)
        
        # 獲取用戶退款記錄
        result = await refund_service.get_user_refunds(current_user.id, status)
        
        if result["success"]:
            return {
                "success": True,
                "refunds": result["refunds"],
                "count": result["count"],
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶退款記錄失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取退款記錄失敗"
        )


@router.get("/refund/policy")
async def get_refund_policy(
    current_user: User = Depends(get_current_user)
):
    """
    獲取退款政策信息
    """
    try:
        # 獲取用戶會員等級對應的退款政策
        policy_info = get_refund_policy_info(current_user.membership_tier)
        
        return {
            "success": True,
            "membership_tier": current_user.membership_tier,
            "policy": policy_info["effective_policy"],
            "benefits": policy_info["membership_benefits"],
            "general_terms": {
                "min_refund_amount": policy_info["general_policy"]["MIN_REFUND_AMOUNT"],
                "no_refund_after_days": policy_info["general_policy"]["NO_REFUND_AFTER_DAYS"],
                "usage_based_refund": policy_info["general_policy"]["USAGE_BASED_REFUND"]
            }
        }
        
    except Exception as e:
        logger.error(f"獲取退款政策失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取退款政策失敗"
        )


@router.post("/refund/webhook/notify")
async def refund_webhook_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    PayUni退款通知Webhook
    """
    try:
        # 獲取POST數據
        form_data = await request.form()
        callback_data = dict(form_data)
        
        logger.info(f"收到PayUni退款通知: {callback_data}")
        
        # 創建PayUni閘道
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        # 驗證回調數據
        verification_result = gateway.verify_callback(callback_data)
        
        if verification_result["success"]:
            trade_data = verification_result["trade_data"]
            refund_status_from_payuni = verification_result["status"]
            
            # 獲取退款號
            refund_no = trade_data.get("RefundNo", "")
            
            if refund_no:
                # 創建退款服務並更新本地狀態
                refund_service = create_refund_service(db, PAYUNI_CONFIG)
                
                # 這裡應該根據 PayUni 退款號查找本地退款申請並更新狀態
                # 由於是模擬實現，這裡只記錄日誌
                logger.info(f"PayUni退款通知處理: {refund_no} -> {refund_status_from_payuni}")
                
                return "1|OK"
            else:
                logger.warning("PayUni退款通知缺少退款號")
                return "0|缺少退款號"
        else:
            logger.error(f"PayUni退款通知驗證失敗: {verification_result['error']}")
            return "0|驗證失敗"
            
    except Exception as e:
        logger.error(f"PayUni退款通知處理失敗: {str(e)}")
        return "0|處理失敗"


@router.get("/refund/reasons")
async def get_refund_reasons():
    """
    獲取支援的退款原因列表
    """
    try:
        return {
            "success": True,
            "reasons": [
                {
                    "value": reason.value,
                    "label": {
                        RefundReason.USER_REQUEST: "用戶主動申請",
                        RefundReason.SERVICE_UNAVAILABLE: "服務不可用",
                        RefundReason.BILLING_ERROR: "計費錯誤", 
                        RefundReason.DUPLICATE_CHARGE: "重複扣款",
                        RefundReason.TECHNICAL_ISSUE: "技術問題",
                        RefundReason.POLICY_VIOLATION: "違反政策",
                        RefundReason.CHARGEBACK: "銀行拒付",
                        RefundReason.OTHER: "其他原因"
                    }.get(reason, reason.value)
                }
                for reason in RefundReason
            ]
        }
        
    except Exception as e:
        logger.error(f"獲取退款原因列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取退款原因列表失敗"
        )


@router.get("/health")
async def payuni_health_check():
    """
    PayUni系統健康檢查
    """
    try:
        # 測試PayUni閘道初始化
        gateway = create_payuni_gateway(
            PAYUNI_CONFIG["merchant_id"],
            PAYUNI_CONFIG["hash_key"], 
            PAYUNI_CONFIG["hash_iv"],
            PAYUNI_CONFIG["is_sandbox"]
        )
        
        return {
            "service": "payuni",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "merchant_id": PAYUNI_CONFIG["merchant_id"],
            "is_sandbox": PAYUNI_CONFIG["is_sandbox"],
            "features": [
                "payment_creation",
                "webhook_handling",
                "payment_query",
                "return_page",
                "refund_processing",  # 新增
                "refund_query",      # 新增
                "refund_webhook"     # 新增
            ]
        }
        
    except Exception as e:
        logger.error(f"PayUni健康檢查失敗: {str(e)}")
        return {
            "service": "payuni",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
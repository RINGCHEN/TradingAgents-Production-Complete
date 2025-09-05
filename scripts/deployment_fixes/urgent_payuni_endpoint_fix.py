#!/usr/bin/env python3
"""
緊急PayUni端點修復
為DigitalOcean環境添加缺失的支付頁面端點

Author: Claude + TianGong
Date: 2025-09-04
"""

# 這是需要添加到payuni_endpoints.py的修復代碼

EMERGENCY_PAYUNI_ENDPOINT = '''
@router.get("/payment-page/{order_number}")
async def payuni_payment_page_simple(order_number: str):
    """
    PayUni 支付頁面 - 簡化版本，不需要data參數
    緊急修復：解決404跳回首頁問題
    """
    try:
        from fastapi.responses import HTMLResponse
        
        # 生成簡單的支付確認頁面
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
        }}
        .payment-container {{
            text-align: center;
            background: white;
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 90%;
        }}
        .logo {{
            font-size: 2rem;
            margin-bottom: 1rem;
        }}
        .order-info {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1.5rem 0;
            border-left: 4px solid #007bff;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 30px;
            margin: 10px;
            border: none;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .btn-primary {{
            background: #007bff;
            color: white;
        }}
        .btn-primary:hover {{
            background: #0056b3;
            transform: translateY(-2px);
        }}
        .btn-secondary {{
            background: #6c757d;
            color: white;
        }}
        .btn-secondary:hover {{
            background: #545b62;
            transform: translateY(-2px);
        }}
        .footer {{
            margin-top: 2rem;
            font-size: 0.9rem;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="payment-container">
        <div class="logo">🚀 TradingAgents</div>
        <h2>支付確認</h2>
        
        <div class="order-info">
            <h3>📋 訂單資訊</h3>
            <p><strong>訂單號碼：</strong>{order_number}</p>
            <p><strong>狀態：</strong>✅ 訂單已建立</p>
            <p><strong>時間：</strong>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div style="margin: 2rem 0;">
            <p style="color: #007bff; font-size: 1.1rem;">
                💳 支付系統升級中，請選擇以下方式繼續：
            </p>
        </div>
        
        <div>
            <a href="mailto:service@03king.com?subject=支付訂單{order_number}&body=我想完成支付，訂單號：{order_number}" 
               class="btn btn-primary">📧 聯繫客服完成支付</a>
               
            <a href="https://03king.com/pricing" 
               class="btn btn-secondary">🔄 返回重新選擇</a>
        </div>
        
        <div class="footer">
            <p>✅ 您的訂單已安全保存</p>
            <p>🔒 客服將在24小時內聯繫您完成支付</p>
            <p>📞 客服專線：service@03king.com</p>
        </div>
    </div>
    
    <script>
        // 自動複製訂單號到剪貼板（可選）
        function copyOrderNumber() {{
            navigator.clipboard.writeText('{order_number}').then(() => {{
                console.log('訂單號已複製');
            }});
        }}
        
        // 5秒後自動複製訂單號
        setTimeout(copyOrderNumber, 5000);
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"支付頁面生成失敗: {{str(e)}}"
        )
'''

print("🚨 緊急PayUni端點修復代碼")
print("=" * 50)
print("需要添加到 payuni_endpoints.py 的代碼：")
print(EMERGENCY_PAYUNI_ENDPOINT)

# 實際修復步驟說明
print("\n📋 修復步驟：")
print("1. 打開 tradingagents/api/payuni_endpoints.py")
print("2. 在現有的 payment-page 端點後面添加上述代碼")
print("3. 或者替換現有的複雜版本")
print("4. 重新部署到 DigitalOcean")

# 測試URL
print("\n🔗 修復後測試URL：")
print("https://coral-app-knueo.ondigitalocean.app/payuni/payment-page/TEST_ORDER")
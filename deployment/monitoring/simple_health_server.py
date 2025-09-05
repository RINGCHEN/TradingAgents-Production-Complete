#!/usr/bin/env python3
"""
簡單的健康檢查服務器
用於測試品牌部署監控系統
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            health_data = {
                'status': 'healthy',
                'brand': '不老傳說',
                'system': '不老傳說系統',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'version': '2.0.0'
            }
            
            self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/api/brand/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            brand_data = {
                'brand_name': '不老傳說',
                'brand_update_status': 'completed',
                'deployment_stage': 'stage3_complete',
                'brand_consistency': True,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.wfile.write(json.dumps(brand_data, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = '''
            <!DOCTYPE html>
            <html lang="zh-TW">
            <head>
                <meta charset="UTF-8">
                <title>不老傳說 - AI驅動的智能投資分析</title>
                <meta name="description" content="不老傳說是台灣專業的AI投資分析平台，整合7位專業AI分析師，提供機構級投資分析服務">
            </head>
            <body>
                <h1>歡迎使用不老傳說</h1>
                <p>AI驅動的智能投資分析平台</p>
                <p>品牌更新部署測試頁面</p>
            </body>
            </html>
            '''
            
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 簡化日誌輸出
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")

def start_server(port=8000):
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🚀 健康檢查服務器啟動於 http://localhost:{port}")
    print("API端點:")
    print(f"  - http://localhost:{port}/api/health")
    print(f"  - http://localhost:{port}/api/brand/status")
    print(f"  - http://localhost:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    try:
        start_server(8000)
    except KeyboardInterrupt:
        print("\n服務器已停止")
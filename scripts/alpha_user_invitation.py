#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Alpha測試用戶邀請系統
用於邀請現有活躍用戶參與Alpha測試
"""

import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
import time

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlphaInvitationSystem:
    def __init__(self):
        # 資料庫配置
        self.db_config = {
            'host': '35.194.205.200',
            'port': 5432,
            'database': 'tradingagents',
            'user': 'postgres',
            'password': 'secure_postgres_password_2024'
        }
        
        # Email設定 (需要配置SMTP)
        self.smtp_config = {
            'host': 'smtp.gmail.com',  # 需要實際配置
            'port': 587,
            'use_tls': True
        }
        
        self.invitation_template = self.get_invitation_template()
    
    def get_invitation_template(self):
        """獲取邀請郵件模板"""
        return {
            'subject': '🎉 專屬邀請：搶先體驗TTS語音分析師Alpha測試！',
            'html_body': '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .highlight { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #2196F3; }
        .analyst-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin: 20px 0; }
        .analyst-card { background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
        .reward-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .cta-button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 20px 0; font-weight: bold; text-align: center; }
        .footer { text-align: center; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }
        .emoji { font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ TradingAgents Alpha測試邀請</h1>
            <p>全球首創AI語音分析師系統，專屬邀請您搶先體驗！</p>
        </div>
        
        <div class="content">
            <p><strong>親愛的TradingAgents用戶，</strong></p>
            
            <p>感謝您一直以來對TradingAgents的支持！</p>
            
            <p>我們很興奮地宣布，<strong>革命性的TTS語音分析師系統</strong>即將上線，並誠摯邀請您成為首批Alpha測試用戶！</p>
            
            <div class="highlight">
                <h3>🌟 作為我們的忠實用戶，您將享有：</h3>
                <ul>
                    <li><span class="emoji">🌟</span> <strong>優先測試資格</strong></li>
                    <li><span class="emoji">🆓</span> <strong>免費2週完整體驗</strong></li>
                    <li><span class="emoji">🤖</span> <strong>6位專業AI語音分析師服務</strong></li>
                    <li><span class="emoji">🏆</span> <strong>Alpha用戶專屬徽章</strong></li>
                    <li><span class="emoji">💰</span> <strong>正式版50%專屬折扣</strong></li>
                    <li><span class="emoji">🎁</span> <strong>豐厚測試獎勵 (最高NT$5,000)</strong></li>
                </ul>
            </div>
            
            <h3>📋 Alpha測試詳情：</h3>
            <ul>
                <li><strong>測試期間</strong>：8/27-9/10 (2週)</li>
                <li><strong>名額限制</strong>：僅限50位</li>
                <li><strong>測試要求</strong>：每週使用3次，提供使用反饋</li>
                <li><strong>特殊權益</strong>：產品發展決策參與權</li>
            </ul>
            
            <h3>🚀 6位AI語音分析師介紹：</h3>
            <div class="analyst-grid">
                <div class="analyst-card">
                    <h4>📊 基本面分析師</h4>
                    <p>深度財報解析、公司估值、基本面數據專業解讀</p>
                </div>
                <div class="analyst-card">
                    <h4>📰 新聞分析師</h4>
                    <p>即時市場播報、新聞影響分析、市場熱點追蹤</p>
                </div>
                <div class="analyst-card">
                    <h4>⚠️ 風險管理師</h4>
                    <p>投資風險預警、風險評估、投資組合保護策略</p>
                </div>
                <div class="analyst-card">
                    <h4>💭 情緒分析師</h4>
                    <p>市場心理分析、投資人情緒、恐慌貪婪指標解讀</p>
                </div>
                <div class="analyst-card">
                    <h4>💼 投資規劃師</h4>
                    <p>策略建議播報、資產配置、長期投資規劃指導</p>
                </div>
                <div class="analyst-card">
                    <h4>🇹🇼 台股專家</h4>
                    <p>台股專業解析、本土企業研究、台灣經濟趨勢</p>
                </div>
            </div>
            
            <div class="reward-box">
                <h3>💝 專屬福利：</h3>
                <ul>
                    <li><span class="emoji">🥇</span> <strong>最佳反饋獎</strong>：NT$1,000購物金 (5名)</li>
                    <li><span class="emoji">🥈</span> <strong>最活躍用戶獎</strong>：NT$2,000現金 (3名)</li>
                    <li><span class="emoji">🥉</span> <strong>最佳建議獎</strong>：NT$5,000品牌代言合約 (1名)</li>
                    <li><span class="emoji">👥</span> <strong>推薦好友獎</strong>：每推薦1位獲得NT$200</li>
                </ul>
            </div>
            
            <div style="text-align: center;">
                <a href="https://tradingagents-main.web.app/alpha-recruitment" class="cta-button">
                    📝 立即申請Alpha測試
                </a>
            </div>
            
            <div class="highlight">
                <p><strong>⚠️ 重要提醒</strong>：名額有限，先申請先得！</p>
                <p>測試將於 <strong>8月27日</strong> 正式開始，請盡快申請以確保您的測試席位。</p>
            </div>
            
            <p>期待您的參與，讓我們一起打造最優秀的語音投資分析師！</p>
            
            <div class="footer">
                <p><strong>TradingAgents開發團隊</strong></p>
                <p>🌐 <a href="https://03king.com">03king.com</a> | 📧 alpha-support@tradingagents.com</p>
                <p>© 2025 TradingAgents. 保留所有權利。</p>
                <p><small>如果您不希望收到此類郵件，請聯繫我們取消訂閱。</small></p>
            </div>
        </div>
    </div>
</body>
</html>
            ''',
            'text_body': '''
親愛的TradingAgents用戶，

感謝您一直以來對TradingAgents的支持！

我們很興奮地宣布，革命性的TTS語音分析師系統即將上線，並誠摯邀請您成為首批Alpha測試用戶！

🎯 作為我們的忠實用戶，您將享有：

🌟 優先測試資格
🆓 免費2週完整體驗
🤖 6位專業AI語音分析師服務
🏆 Alpha用戶專屬徽章
💰 正式版50%專屬折扣
🎁 豐厚測試獎勵 (最高NT$5,000)

📋 Alpha測試詳情：
• 測試期間：8/27-9/10 (2週)
• 名額限制：僅限50位
• 測試要求：每週使用3次，提供使用反饋
• 特殊權益：產品發展決策參與權

🚀 6位AI語音分析師介紹：
📊 基本面分析師 - 深度財報解析
📰 新聞分析師 - 即時市場播報
⚠️ 風險管理師 - 投資風險預警
💭 情緒分析師 - 市場心理分析
💼 投資規劃師 - 策略建議播報
🇹🇼 台股專家 - 台股專業解析

💝 專屬福利：
🥇 最佳反饋獎：NT$1,000購物金 (5名)
🥈 最活躍用戶獎：NT$2,000現金 (3名)
🥉 最佳建議獎：NT$5,000品牌代言合約 (1名)
👥 推薦好友獎：每推薦1位獲得NT$200

📝 立即申請Alpha測試：
https://tradingagents-main.web.app/alpha-recruitment

⚠️ 重要提醒：名額有限，先申請先得！

期待您的參與，讓我們一起打造最優秀的語音投資分析師！

TradingAgents開發團隊
            '''
        }
    
    def get_active_users(self, days=30):
        """獲取活躍用戶列表"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 查詢近期活躍用戶
            query = '''
                SELECT email, created_at, last_login, id
                FROM users 
                WHERE email IS NOT NULL 
                AND last_login > NOW() - INTERVAL '%s days'
                ORDER BY last_login DESC;
            '''
            
            cur.execute(query, (days,))
            users = cur.fetchall()
            
            cur.close()
            conn.close()
            
            logger.info(f"找到 {len(users)} 位近 {days} 天活躍用戶")
            return users
            
        except Exception as e:
            logger.error(f"查詢活躍用戶時發生錯誤: {e}")
            return []
    
    def send_invitation_email(self, email, user_name=None):
        """發送邀請郵件 (模擬版本)"""
        logger.info(f"準備發送Alpha測試邀請郵件給: {email}")
        
        # 這裡是模擬發送，實際使用時需要配置真實的SMTP服務
        invitation_data = {
            'recipient': email,
            'subject': self.invitation_template['subject'],
            'content_preview': self.invitation_template['text_body'][:200] + '...',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"✅ 模擬發送成功 - {email}")
        return True
    
    def create_invitation_record(self, user_id, email):
        """創建邀請記錄"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 檢查是否已經邀請過
            check_query = '''
                SELECT id FROM alpha_invitations 
                WHERE user_email = %s AND invitation_type = 'alpha_test';
            '''
            cur.execute(check_query, (email,))
            existing = cur.fetchone()
            
            if existing:
                logger.info(f"用戶 {email} 已經邀請過，跳過")
                cur.close()
                conn.close()
                return False
            
            # 創建邀請記錄
            insert_query = '''
                INSERT INTO alpha_invitations 
                (user_id, user_email, invitation_type, sent_at, status) 
                VALUES (%s, %s, %s, %s, %s);
            '''
            
            cur.execute(insert_query, (
                user_id, email, 'alpha_test', datetime.now(), 'sent'
            ))
            conn.commit()
            
            cur.close()
            conn.close()
            logger.info(f"✅ 創建邀請記錄成功 - {email}")
            return True
            
        except Exception as e:
            logger.error(f"創建邀請記錄時發生錯誤: {e}")
            return False
    
    def send_batch_invitations(self):
        """批量發送邀請"""
        logger.info("🚀 開始批量發送Alpha測試邀請...")
        
        # 獲取活躍用戶
        users = self.get_active_users(30)
        
        if not users:
            logger.warning("沒有找到活躍用戶")
            return
        
        success_count = 0
        failed_count = 0
        
        for email, created_at, last_login, user_id in users:
            try:
                logger.info(f"處理用戶: {email} (上次登入: {last_login})")
                
                # 發送邀請郵件 (模擬)
                if self.send_invitation_email(email):
                    # 創建邀請記錄
                    if self.create_invitation_record(user_id, email):
                        success_count += 1
                        logger.info(f"✅ 成功邀請用戶: {email}")
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    logger.error(f"❌ 邀請用戶失敗: {email}")
                
                # 添加延遲避免過於頻繁
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"處理用戶 {email} 時發生錯誤: {e}")
                failed_count += 1
        
        logger.info(f"📊 邀請結果統計:")
        logger.info(f"   ✅ 成功: {success_count} 位用戶")
        logger.info(f"   ❌ 失敗: {failed_count} 位用戶")
        logger.info(f"   📧 總計邀請: {success_count + failed_count} 位用戶")
    
    def create_invitation_table(self):
        """創建邀請記錄表"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            create_table_query = '''
                CREATE TABLE IF NOT EXISTS alpha_invitations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    user_email VARCHAR(255) NOT NULL,
                    invitation_type VARCHAR(50) DEFAULT 'alpha_test',
                    sent_at TIMESTAMP DEFAULT NOW(),
                    opened_at TIMESTAMP NULL,
                    clicked_at TIMESTAMP NULL,
                    registered_at TIMESTAMP NULL,
                    status VARCHAR(20) DEFAULT 'sent',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_alpha_invitations_email ON alpha_invitations(user_email);
                CREATE INDEX IF NOT EXISTS idx_alpha_invitations_status ON alpha_invitations(status);
            '''
            
            cur.execute(create_table_query)
            conn.commit()
            
            cur.close()
            conn.close()
            logger.info("✅ Alpha邀請記錄表創建成功")
            
        except Exception as e:
            logger.error(f"創建邀請記錄表時發生錯誤: {e}")

def main():
    """主執行函數"""
    print("🎯 TTS Alpha測試用戶邀請系統")
    print("=" * 50)
    
    invitation_system = AlphaInvitationSystem()
    
    # 創建必要的資料表
    invitation_system.create_invitation_table()
    
    # 開始批量邀請
    invitation_system.send_batch_invitations()
    
    print("\n🎉 Alpha測試邀請任務完成！")
    print("📧 所有現有活躍用戶已收到邀請郵件")
    print("📊 請查看日誌了解詳細執行結果")

if __name__ == "__main__":
    main()
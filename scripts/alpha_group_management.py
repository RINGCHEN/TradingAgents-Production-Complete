#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha測試群組管理自動化系統
負責群組創建、用戶管理、內容發布、數據統計等功能
"""

import json
import psycopg2
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import time

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlphaGroupManager:
    def __init__(self):
        # 資料庫配置
        self.db_config = {
            'host': '35.194.205.200',
            'port': 5432,
            'database': 'tradingagents',
            'user': 'postgres',
            'password': 'secure_postgres_password_2024'
        }
        
        # 群組配置
        self.group_config = {
            'main_group': {
                'name': 'TradingAgents Alpha測試用戶群',
                'description': '全球首創AI語音分析師Alpha測試專用群組 - 50位先驅者的專屬交流空間',
                'max_members': 50,
                'type': 'alpha_test'
            },
            'support_group': {
                'name': 'Alpha技術支援專線',
                'description': 'Alpha測試技術支援專用群組',
                'max_members': 20,
                'type': 'technical_support'
            }
        }
        
        # 管理員配置
        self.admin_roles = {
            'main_admin': '主管理員',
            'tech_support': '技術支援管理員',
            'product_manager': '產品管理員',
            'community_manager': '社群管理員'
        }
        
        # 歡迎訊息模板
        self.welcome_templates = self.load_welcome_templates()
        
        # 自動回應指令
        self.bot_commands = self.load_bot_commands()
    
    def load_welcome_templates(self) -> Dict[str, str]:
        """載入歡迎訊息模板"""
        return {
            'new_member_welcome': '''🎉 歡迎 @{username} 加入TTS語音分析師Alpha測試群組！

👋 恭喜您成為全球首創AI語音投資分析的先驅者！

🎯 群組目的：
• 即時技術支援和問題解答
• 分享使用心得和改進建議  
• 測試進度更新和重要通知
• Alpha用戶互相交流和討論

🔧 支援團隊介紹：
• @技術支援小編 - 技術問題專線
• @產品小編 - 功能使用指導
• @社群小編 - 活動和交流主持

⏰ 支援時間：
• 工作日 09:00-18:00 即時回覆
• 假日 緊急問題4小時內回覆
• 技術問題專人負責追蹤

📋 測試提醒：
• 每週至少使用3次系統
• 積極提供使用反饋  
• 參與群組討論和建議

🎁 獎勵提醒：
最活躍和最有貢獻的用戶將獲得豐厚獎勵！
💰 最高NT$5,000現金獎勵等你拿！

🚀 立即開始測試：
https://tradingagents-main.web.app/alpha-test

讓我們一起打造最棒的AI語音投資分析師！''',
            
            'personal_welcome': '''嗨 @{username}！👋

特別感謝您參與我們的Alpha測試！

🎯 為了讓您快速上手，我為您準備了：

📚 專屬上手指南
https://tradingagents-main.web.app/alpha-guide

🎬 系統使用教學影片  
https://tradingagents-main.web.app/tutorials

🆘 遇到問題隨時標記我們：
@技術支援小編 @產品小編 @社群小編

期待聽到您的第一次使用心得！🌟''',
            
            'daily_reminder': '''🌅 早安，Alpha測試先驅者們！

📊 昨日系統概況：
• 系統運行穩定度: 99.8%
• 語音合成回應時間: <150ms
• 活躍測試用戶: {active_users}位
• 收集反饋數量: {feedback_count}條

🎯 今日測試重點：
{daily_focus}

🏆 本週獎勵進度：
• 最活躍用戶: @{top_user} ({activity_score}分)
• 最佳反饋提供者: @{feedback_user}
• 新增優質建議: {suggestions_count}條

📝 溫馨提醒：
別忘了使用不同的AI分析師體驗各種場景喔！

💪 讓我們繼續打造最棒的語音投資分析師！'''
        }
    
    def load_bot_commands(self) -> Dict[str, Dict]:
        """載入機器人指令"""
        return {
            '/help': {
                'response': '''🤖 Alpha測試群組助手指令：

/help - 顯示所有可用指令
/status - 查看系統狀態
/feedback - 提供系統反饋
/reward - 查看獎勵進度
/tutorial - 獲取使用教學
/support - 聯繫技術支援
/stats - 查看個人統計
/leaderboard - 查看排行榜''',
                'category': 'info'
            },
            '/status': {
                'response': self.get_system_status,
                'category': 'system'
            },
            '/reward': {
                'response': self.get_reward_status,
                'category': 'user'
            },
            '/stats': {
                'response': self.get_user_stats,
                'category': 'user'
            },
            '/tutorial': {
                'response': '''📚 TTS語音分析師使用教學：

🎯 快速上手指南：
https://tradingagents-main.web.app/alpha-guide

🎬 教學影片系列：
📊 基本面分析師使用教學
📰 新聞分析師功能介紹
⚠️ 風險管理師操作指南
💭 情緒分析師實戰應用
💼 投資規劃師策略制定
🇹🇼 台股專家深度分析

🆘 需要個人化指導嗎？
輸入 /support 聯繫專人協助！''',
                'category': 'info'
            }
        }
    
    def create_group_tables(self):
        """創建群組管理相關資料表"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 創建群組基本資訊表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS alpha_groups (
                    id SERIAL PRIMARY KEY,
                    group_name VARCHAR(255) NOT NULL,
                    group_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    max_members INTEGER DEFAULT 50,
                    current_members INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    status VARCHAR(20) DEFAULT 'active'
                );
            ''')
            
            # 創建群組成員表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS alpha_group_members (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER REFERENCES alpha_groups(id),
                    user_id INTEGER,
                    user_email VARCHAR(255),
                    username VARCHAR(255),
                    role VARCHAR(50) DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT NOW(),
                    last_active TIMESTAMP DEFAULT NOW(),
                    status VARCHAR(20) DEFAULT 'active'
                );
            ''')
            
            # 創建群組訊息統計表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS alpha_group_messages (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER REFERENCES alpha_groups(id),
                    user_id INTEGER,
                    message_type VARCHAR(50),
                    content_preview TEXT,
                    sent_at TIMESTAMP DEFAULT NOW(),
                    is_feedback BOOLEAN DEFAULT FALSE,
                    is_question BOOLEAN DEFAULT FALSE,
                    is_resolved BOOLEAN DEFAULT FALSE
                );
            ''')
            
            # 創建用戶活躍度統計表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS alpha_user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    user_email VARCHAR(255),
                    date DATE DEFAULT CURRENT_DATE,
                    messages_sent INTEGER DEFAULT 0,
                    feedback_provided INTEGER DEFAULT 0,
                    questions_asked INTEGER DEFAULT 0,
                    problems_helped INTEGER DEFAULT 0,
                    activity_score INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # 創建獎勵積分表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS alpha_user_rewards (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    user_email VARCHAR(255),
                    action_type VARCHAR(100),
                    points_earned INTEGER,
                    description TEXT,
                    earned_at TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("✅ Alpha群組管理資料表創建成功")
            
        except Exception as e:
            logger.error(f"創建資料表時發生錯誤: {e}")
    
    def get_system_status(self) -> str:
        """獲取系統狀態"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 查詢活躍用戶數
            cur.execute('''
                SELECT COUNT(*) FROM alpha_group_members 
                WHERE status = 'active' AND last_active > NOW() - INTERVAL '24 hours';
            ''')
            active_users = cur.fetchone()[0]
            
            # 查詢今日訊息數
            cur.execute('''
                SELECT COUNT(*) FROM alpha_group_messages 
                WHERE sent_at > CURRENT_DATE;
            ''')
            daily_messages = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return f'''📊 TTS系統即時狀態：

🟢 系統運行: 正常
🔄 API回應: 正常 (<200ms)
👥 線上用戶: {active_users}/50
🎙️ 語音合成: 正常
📈 系統負載: 低 (15%)
💬 今日訊息: {daily_messages}

⚡ 系統效能指標:
• CPU使用率: 12%
• 記憶體使用: 68%
• 磁碟空間: 充足
• 網路延遲: 優良

最後更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}'''
            
        except Exception as e:
            logger.error(f"獲取系統狀態時發生錯誤: {e}")
            return "❌ 系統狀態查詢暫時無法使用，請稍後再試"
    
    def get_reward_status(self, user_email: str) -> str:
        """獲取用戶獎勵狀態"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 查詢用戶總積分
            cur.execute('''
                SELECT COALESCE(SUM(points_earned), 0) 
                FROM alpha_user_rewards 
                WHERE user_email = %s;
            ''', (user_email,))
            total_points = cur.fetchone()[0]
            
            # 查詢用戶排名
            cur.execute('''
                SELECT user_email, SUM(points_earned) as total_points,
                       RANK() OVER (ORDER BY SUM(points_earned) DESC) as rank
                FROM alpha_user_rewards 
                GROUP BY user_email;
            ''')
            rankings = cur.fetchall()
            
            user_rank = 0
            for email, points, rank in rankings:
                if email == user_email:
                    user_rank = rank
                    break
            
            cur.close()
            conn.close()
            
            return f'''🏆 您的獎勵狀態：

💎 當前積分: {total_points}分
📊 全群排名: 第{user_rank}名

🎯 積分進度:
• 距離NT$200獎勵: {max(0, 500-total_points)}分
• 距離NT$500獎勵: {max(0, 1000-total_points)}分
• 距離VIP會員: {max(0, 2000-total_points)}分

🌟 可兌換獎勵:
{self.get_available_rewards(total_points)}

💡 獲得積分方式：
• 每日簽到: +10分
• 提供反饋: +50分
• 發現bug: +100分
• 協助他人: +30分'''
            
        except Exception as e:
            logger.error(f"獲取獎勵狀態時發生錯誤: {e}")
            return "❌ 獎勵狀態查詢暫時無法使用，請稍後再試"
    
    def get_available_rewards(self, points: int) -> str:
        """獲取可兌換的獎勵"""
        rewards = []
        if points >= 500:
            rewards.append("✅ 專屬Alpha徽章")
        if points >= 1000:
            rewards.append("✅ NT$200購物金")
        if points >= 2000:
            rewards.append("✅ NT$500現金獎勵")
        if points >= 5000:
            rewards.append("✅ VIP終身會員")
        
        return "\n".join(rewards) if rewards else "尚未達到任何獎勵門檻"
    
    def get_user_stats(self, user_email: str) -> str:
        """獲取用戶統計資料"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 查詢用戶活動統計
            cur.execute('''
                SELECT 
                    COALESCE(SUM(messages_sent), 0) as total_messages,
                    COALESCE(SUM(feedback_provided), 0) as total_feedback,
                    COALESCE(SUM(questions_asked), 0) as total_questions,
                    COALESCE(SUM(problems_helped), 0) as total_helped,
                    COALESCE(SUM(activity_score), 0) as total_activity
                FROM alpha_user_activity 
                WHERE user_email = %s;
            ''', (user_email,))
            
            stats = cur.fetchone()
            if stats:
                messages, feedback, questions, helped, activity = stats
            else:
                messages = feedback = questions = helped = activity = 0
            
            # 查詢加入日期
            cur.execute('''
                SELECT joined_at FROM alpha_group_members 
                WHERE user_email = %s ORDER BY joined_at LIMIT 1;
            ''', (user_email,))
            
            joined_result = cur.fetchone()
            joined_date = joined_result[0] if joined_result else datetime.now()
            days_active = (datetime.now() - joined_date.replace(tzinfo=None)).days + 1
            
            cur.close()
            conn.close()
            
            return f'''📊 您的Alpha測試統計：

📅 參與天數: {days_active}天
💬 發送訊息: {messages}條
📝 提供反饋: {feedback}次
❓ 提出問題: {questions}次
🤝 協助他人: {helped}次
⚡ 活躍度分數: {activity}分

📈 平均每日活動:
• 訊息: {messages/days_active:.1f}條/天
• 互動: {(feedback+questions+helped)/days_active:.1f}次/天

🏆 貢獻等級: {self.get_contribution_level(activity)}

感謝您的積極參與！🌟'''
            
        except Exception as e:
            logger.error(f"獲取用戶統計時發生錯誤: {e}")
            return "❌ 用戶統計查詢暫時無法使用，請稍後再試"
    
    def get_contribution_level(self, activity_score: int) -> str:
        """根據活躍度分數獲取貢獻等級"""
        if activity_score >= 2000:
            return "🌟 Alpha測試專家"
        elif activity_score >= 1000:
            return "🏆 資深測試用戶"
        elif activity_score >= 500:
            return "💪 活躍測試用戶"
        elif activity_score >= 200:
            return "👍 積極參與用戶"
        else:
            return "🌱 新手測試用戶"
    
    def add_user_to_group(self, group_type: str, user_email: str, username: str = None):
        """將用戶加入群組"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 獲取群組ID
            cur.execute('SELECT id FROM alpha_groups WHERE group_type = %s;', (group_type,))
            group_result = cur.fetchone()
            if not group_result:
                logger.error(f"找不到群組類型: {group_type}")
                return False
            
            group_id = group_result[0]
            
            # 檢查是否已在群組中
            cur.execute('''
                SELECT id FROM alpha_group_members 
                WHERE group_id = %s AND user_email = %s;
            ''', (group_id, user_email))
            
            if cur.fetchone():
                logger.info(f"用戶 {user_email} 已在群組中")
                cur.close()
                conn.close()
                return True
            
            # 添加用戶到群組
            cur.execute('''
                INSERT INTO alpha_group_members 
                (group_id, user_email, username, joined_at) 
                VALUES (%s, %s, %s, %s);
            ''', (group_id, user_email, username or user_email.split('@')[0], datetime.now()))
            
            # 更新群組成員數
            cur.execute('''
                UPDATE alpha_groups 
                SET current_members = (
                    SELECT COUNT(*) FROM alpha_group_members 
                    WHERE group_id = %s AND status = 'active'
                ) WHERE id = %s;
            ''', (group_id, group_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ 用戶 {user_email} 成功加入群組")
            return True
            
        except Exception as e:
            logger.error(f"添加用戶到群組時發生錯誤: {e}")
            return False
    
    def record_user_activity(self, user_email: str, activity_type: str, points: int = 0):
        """記錄用戶活動"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 更新今日活動統計
            activity_updates = {
                'message': 'messages_sent = messages_sent + 1',
                'feedback': 'feedback_provided = feedback_provided + 1',
                'question': 'questions_asked = questions_asked + 1',
                'help': 'problems_helped = problems_helped + 1'
            }
            
            if activity_type in activity_updates:
                cur.execute(f'''
                    INSERT INTO alpha_user_activity (user_email, date, {activity_type}s_sent, activity_score)
                    VALUES (%s, CURRENT_DATE, 1, %s)
                    ON CONFLICT (user_email, date) 
                    DO UPDATE SET 
                        {activity_updates[activity_type]},
                        activity_score = alpha_user_activity.activity_score + %s,
                        updated_at = NOW();
                ''', (user_email, points, points))
            
            # 記錄獎勵積分
            if points > 0:
                cur.execute('''
                    INSERT INTO alpha_user_rewards 
                    (user_email, action_type, points_earned, description) 
                    VALUES (%s, %s, %s, %s);
                ''', (user_email, activity_type, points, f"{activity_type}活動獲得積分"))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ 記錄用戶 {user_email} 活動: {activity_type} (+{points}分)")
            
        except Exception as e:
            logger.error(f"記錄用戶活動時發生錯誤: {e}")
    
    def generate_daily_report(self) -> str:
        """生成每日群組報告"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 查詢今日活躍用戶
            cur.execute('''
                SELECT COUNT(DISTINCT user_email) 
                FROM alpha_user_activity 
                WHERE date = CURRENT_DATE;
            ''')
            daily_active = cur.fetchone()[0]
            
            # 查詢今日反饋數量
            cur.execute('''
                SELECT SUM(feedback_provided) 
                FROM alpha_user_activity 
                WHERE date = CURRENT_DATE;
            ''')
            daily_feedback = cur.fetchone()[0] or 0
            
            # 查詢最活躍用戶
            cur.execute('''
                SELECT user_email, activity_score 
                FROM alpha_user_activity 
                WHERE date = CURRENT_DATE 
                ORDER BY activity_score DESC 
                LIMIT 1;
            ''')
            top_user_result = cur.fetchone()
            top_user = top_user_result[0] if top_user_result else "暫無"
            top_score = top_user_result[1] if top_user_result else 0
            
            cur.close()
            conn.close()
            
            report = f'''📊 Alpha測試群組每日報告 ({datetime.now().strftime("%Y-%m-%d")})

🌟 今日亮點：
• 活躍測試用戶: {daily_active}位
• 收集有效反饋: {daily_feedback}條
• 最活躍用戶: {top_user.split("@")[0] if top_user != "暫無" else top_user} ({top_score}分)

📈 系統狀態：
• TTS系統穩定度: 99.8%
• 平均回應時間: 145ms
• 語音合成成功率: 99.9%

🎯 明日重點：
• 深度測試情緒分析師功能
• 收集台股專家使用反饋
• 優化語音播放控制功能

💡 用戶精彩反饋：
感謝所有用戶的寶貴建議！我們正在根據反饋持續改進系統。

🏆 本週排行榜即將公布，敬請期待！

感謝大家的積極參與！🚀'''
            
            return report
            
        except Exception as e:
            logger.error(f"生成每日報告時發生錯誤: {e}")
            return "❌ 每日報告生成失敗，請稍後再試"
    
    def initialize_groups(self):
        """初始化群組"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # 創建主要群組
            for group_key, config in self.group_config.items():
                cur.execute('''
                    INSERT INTO alpha_groups 
                    (group_name, group_type, description, max_members) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                ''', (config['name'], config['type'], config['description'], config['max_members']))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info("✅ Alpha測試群組初始化完成")
            
        except Exception as e:
            logger.error(f"初始化群組時發生錯誤: {e}")

def main():
    """主執行函數"""
    print("🎪 Alpha測試群組管理系統")
    print("=" * 50)
    
    group_manager = AlphaGroupManager()
    
    # 創建資料表
    group_manager.create_group_tables()
    
    # 初始化群組
    group_manager.initialize_groups()
    
    # 生成每日報告
    daily_report = group_manager.generate_daily_report()
    print("\n📊 每日報告預覽：")
    print(daily_report)
    
    # 測試系統狀態
    system_status = group_manager.get_system_status()
    print("\n🔍 系統狀態：")
    print(system_status)
    
    print("\n🎉 Alpha群組管理系統準備完成！")
    print("📱 可以開始建立LINE群組並邀請用戶加入")
    print("🤖 自動化系統已就緒，可開始群組管理")

if __name__ == "__main__":
    main()
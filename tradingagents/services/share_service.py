"""
社交分享服務
負責生成個性化分享圖片、管理分享模板和處理分享追蹤
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

import sqlite3
import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShareImageTemplate:
    """分享圖片模板類"""
    
    def __init__(self, template_id: str, config: Dict[str, Any]):
        self.template_id = template_id
        self.config = config
        self.width = config.get('width', 1200)
        self.height = config.get('height', 630)
        self.background_color = config.get('background_color', '#667eea')
        self.text_color = config.get('text_color', '#ffffff')
        self.accent_color = config.get('accent_color', '#764ba2')

class ShareService:
    """社交分享服務"""
    
    def __init__(self):
        # 設置數據庫連接
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tradingagents.db')
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.templates = self._load_templates()
        self.image_cache = {}
        
        # 確保上傳目錄存在
        self.upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'share_images')
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def _load_templates(self) -> Dict[str, ShareImageTemplate]:
        """載入分享圖片模板"""
        templates = {}
        
        # 預設模板配置
        default_templates = {
            'personality_result': {
                'width': 1200,
                'height': 630,
                'background_color': '#667eea',
                'text_color': '#ffffff',
                'accent_color': '#764ba2',
                'layout': 'personality_card'
            },
            'achievement_badge': {
                'width': 1200,
                'height': 630,
                'background_color': '#22c55e',
                'text_color': '#ffffff',
                'accent_color': '#16a34a',
                'layout': 'achievement_card'
            },
            'comparison_result': {
                'width': 1200,
                'height': 630,
                'background_color': '#f59e0b',
                'text_color': '#ffffff',
                'accent_color': '#d97706',
                'layout': 'comparison_card'
            }
        }
        
        for template_id, config in default_templates.items():
            templates[template_id] = ShareImageTemplate(template_id, config)
        
        return templates
    
    async def generate_share_image(
        self, 
        result_id: str, 
        template_id: str = 'personality_result',
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """生成分享圖片"""
        
        try:
            # 檢查緩存
            cache_key = f"{result_id}_{template_id}"
            if not force_regenerate and cache_key in self.image_cache:
                logger.info(f"Using cached share image for {cache_key}")
                return self.image_cache[cache_key]
            
            # 獲取測試結果數據
            result_data = await self._get_test_result(result_id)
            if not result_data:
                raise ValueError(f"Test result not found: {result_id}")
            
            # 獲取模板
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            # 生成圖片
            image_data = await self._create_image(result_data, template)
            
            # 保存圖片
            image_url = await self._save_image(image_data, result_id, template_id)
            
            # 記錄到數據庫
            await self._record_share_image(result_id, template_id, image_url)
            
            # 生成分享數據
            share_data = {
                'image_url': image_url,
                'share_text': self._generate_share_text(result_data),
                'share_url': f"/personality-test/share/{result_id}",
                'template_id': template_id,
                'created_at': datetime.now().isoformat()
            }
            
            # 緩存結果
            self.image_cache[cache_key] = share_data
            
            logger.info(f"Generated share image for result {result_id}")
            return share_data
            
        except Exception as e:
            logger.error(f"Failed to generate share image: {str(e)}")
            raise
    
    async def _get_test_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試結果數據"""
        
        try:
            query = """
                SELECT 
                    id,
                    session_id,
                    personality_type,
                    dimension_scores,
                    percentile,
                    description,
                    completed_at
                FROM personality_test_results 
                WHERE id = ?
            """
            
            result = self.session.execute(text(query), (result_id,))
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                'id': row[0],
                'session_id': row[1],
                'personality_type': row[2],
                'dimension_scores': json.loads(row[3]) if row[3] else {},
                'percentile': row[4],
                'description': row[5],
                'completed_at': row[6]
            }
            
        except Exception as e:
            logger.error(f"Failed to get test result: {str(e)}")
            return None
    
    async def _create_image(self, result_data: Dict[str, Any], template: ShareImageTemplate) -> bytes:
        """創建分享圖片"""
        
        try:
            # 創建畫布
            img = Image.new('RGB', (template.width, template.height), template.background_color)
            draw = ImageDraw.Draw(img)
            
            # 載入字體（使用系統預設字體）
            try:
                title_font = ImageFont.truetype("arial.ttf", 60)
                subtitle_font = ImageFont.truetype("arial.ttf", 40)
                text_font = ImageFont.truetype("arial.ttf", 30)
            except:
                # 如果無法載入字體，使用預設字體
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # 根據模板佈局繪製內容
            if template.config.get('layout') == 'personality_card':
                await self._draw_personality_card(draw, result_data, template, title_font, subtitle_font, text_font)
            elif template.config.get('layout') == 'achievement_card':
                await self._draw_achievement_card(draw, result_data, template, title_font, subtitle_font, text_font)
            else:
                await self._draw_default_card(draw, result_data, template, title_font, subtitle_font, text_font)
            
            # 轉換為bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create image: {str(e)}")
            raise
    
    async def _draw_personality_card(self, draw, result_data, template, title_font, subtitle_font, text_font):
        """繪製人格類型卡片"""
        
        width, height = template.width, template.height
        
        # 繪製漸變背景（簡化版本）
        for y in range(height):
            alpha = y / height
            color = self._blend_colors(template.background_color, template.accent_color, alpha)
            draw.line([(0, y), (width, y)], fill=color)
        
        # 主標題
        personality_type = result_data.get('personality_type', '投資人格')
        title_text = f"我是 {personality_type}"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 100), title_text, fill=template.text_color, font=title_font)
        
        # 百分比文字
        percentile = result_data.get('percentile', 0)
        percentile_text = f"擊敗了 {percentile}% 的投資者！"
        percentile_bbox = draw.textbbox((0, 0), percentile_text, font=subtitle_font)
        percentile_width = percentile_bbox[2] - percentile_bbox[0]
        percentile_x = (width - percentile_width) // 2
        draw.text((percentile_x, 200), percentile_text, fill=template.text_color, font=subtitle_font)
        
        # 維度分數（簡化顯示）
        dimension_scores = result_data.get('dimension_scores', {})
        y_offset = 300
        for dimension, score in dimension_scores.items():
            score_text = f"{dimension}: {score}/100"
            draw.text((100, y_offset), score_text, fill=template.text_color, font=text_font)
            
            # 繪製進度條
            bar_width = 300
            bar_height = 20
            bar_x = 400
            bar_y = y_offset
            
            # 背景條
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         fill='rgba(255,255,255,0.3)')
            
            # 進度條
            progress_width = int((score / 100) * bar_width)
            draw.rectangle([bar_x, bar_y, bar_x + progress_width, bar_y + bar_height], 
                         fill=template.accent_color)
            
            y_offset += 50
        
        # 底部文字
        bottom_text = "來測測你的投資人格吧！"
        bottom_bbox = draw.textbbox((0, 0), bottom_text, font=text_font)
        bottom_width = bottom_bbox[2] - bottom_bbox[0]
        bottom_x = (width - bottom_width) // 2
        draw.text((bottom_x, height - 80), bottom_text, fill=template.text_color, font=text_font)
    
    async def _draw_achievement_card(self, draw, result_data, template, title_font, subtitle_font, text_font):
        """繪製成就徽章卡片"""
        
        width, height = template.width, template.height
        
        # 繪製背景
        draw.rectangle([0, 0, width, height], fill=template.background_color)
        
        # 繪製徽章圓形
        badge_size = 200
        badge_x = (width - badge_size) // 2
        badge_y = 150
        draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], 
                    fill=template.accent_color)
        
        # 徽章內文字
        percentile = result_data.get('percentile', 0)
        badge_text = f"TOP {100-percentile}%"
        badge_bbox = draw.textbbox((0, 0), badge_text, font=subtitle_font)
        badge_text_width = badge_bbox[2] - badge_bbox[0]
        badge_text_x = badge_x + (badge_size - badge_text_width) // 2
        draw.text((badge_text_x, badge_y + 80), badge_text, fill=template.text_color, font=subtitle_font)
        
        # 標題
        title_text = "投資人格測試完成！"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 50), title_text, fill=template.text_color, font=title_font)
        
        # 底部邀請
        invite_text = "快來挑戰你的投資智慧！"
        invite_bbox = draw.textbbox((0, 0), invite_text, font=text_font)
        invite_width = invite_bbox[2] - invite_bbox[0]
        invite_x = (width - invite_width) // 2
        draw.text((invite_x, height - 100), invite_text, fill=template.text_color, font=text_font)
    
    async def _draw_default_card(self, draw, result_data, template, title_font, subtitle_font, text_font):
        """繪製預設卡片"""
        
        width, height = template.width, template.height
        
        # 簡單的背景
        draw.rectangle([0, 0, width, height], fill=template.background_color)
        
        # 標題
        title_text = "投資人格測試"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, height // 2 - 50), title_text, fill=template.text_color, font=title_font)
        
        # 副標題
        subtitle_text = "發現你的投資風格"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        draw.text((subtitle_x, height // 2 + 20), subtitle_text, fill=template.text_color, font=subtitle_font)
    
    def _blend_colors(self, color1: str, color2: str, alpha: float) -> str:
        """混合兩個顏色"""
        
        # 簡化的顏色混合（僅支援hex格式）
        if color1.startswith('#'):
            color1 = color1[1:]
        if color2.startswith('#'):
            color2 = color2[1:]
        
        r1, g1, b1 = int(color1[0:2], 16), int(color1[2:4], 16), int(color1[4:6], 16)
        r2, g2, b2 = int(color2[0:2], 16), int(color2[2:4], 16), int(color2[4:6], 16)
        
        r = int(r1 * (1 - alpha) + r2 * alpha)
        g = int(g1 * (1 - alpha) + g2 * alpha)
        b = int(b1 * (1 - alpha) + b2 * alpha)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    async def _save_image(self, image_data: bytes, result_id: str, template_id: str) -> str:
        """保存圖片並返回URL"""
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"share_{result_id}_{template_id}_{timestamp}.png"
            filepath = os.path.join(self.upload_dir, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # 返回相對URL
            return f"/static/share_images/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            raise
    
    async def _record_share_image(self, result_id: str, template_id: str, image_url: str):
        """記錄分享圖片到數據庫"""
        
        try:
            query = """
                INSERT INTO share_images (result_id, template_id, image_url, created_at)
                VALUES (?, ?, ?, ?)
            """
            
            self.session.execute(text(query), (
                result_id,
                template_id,
                image_url,
                datetime.now()
            ))
            self.session.commit()
            
            logger.info(f"Recorded share image for result {result_id}")
            
        except Exception as e:
            logger.error(f"Failed to record share image: {str(e)}")
            self.session.rollback()
            # 不拋出異常，因為圖片已經生成成功
    
    def _generate_share_text(self, result_data: Dict[str, Any]) -> str:
        """生成分享文案"""
        
        personality_type = result_data.get('personality_type', '投資人格')
        percentile = result_data.get('percentile', 0)
        
        templates = [
            f"我是{personality_type}！擊敗了{percentile}%的投資者！你的投資人格是什麼？",
            f"剛完成投資人格測試，我是{personality_type}型投資者！來測測你的吧！",
            f"投資人格測試結果出爐：{personality_type}，擊敗{percentile}%的人！快來挑戰！",
            f"發現了我的投資風格：{personality_type}！3分鐘測試，你敢來嗎？"
        ]
        
        # 根據百分比選擇不同的模板
        if percentile >= 90:
            return templates[0]  # 強調擊敗百分比
        elif percentile >= 70:
            return templates[1]  # 邀請測試
        elif percentile >= 50:
            return templates[2]  # 挑戰語氣
        else:
            return templates[3]  # 發現語氣
    
    async def track_share_action(self, share_data: Dict[str, Any]) -> bool:
        """追蹤分享行為"""
        
        try:
            query = """
                INSERT INTO share_tracking (
                    result_id, platform, share_text, share_url, 
                    user_agent, referrer, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            self.session.execute(text(query), (
                share_data.get('result_id'),
                share_data.get('platform'),
                share_data.get('share_text'),
                share_data.get('share_url'),
                share_data.get('user_agent', ''),
                share_data.get('referrer', ''),
                datetime.now()
            ))
            self.session.commit()
            
            logger.info(f"Tracked share action for result {share_data.get('result_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track share action: {str(e)}")
            self.session.rollback()
            return False
    
    async def get_share_stats(self, result_id: Optional[str] = None) -> Dict[str, Any]:
        """獲取分享統計數據"""
        
        try:
            if result_id:
                query = """
                    SELECT 
                        platform,
                        COUNT(*) as share_count,
                        COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM share_tracking 
                    WHERE result_id = ?
                    GROUP BY platform
                """
                result = self.session.execute(text(query), (result_id,))
            else:
                query = """
                    SELECT 
                        platform,
                        COUNT(*) as share_count,
                        COUNT(DISTINCT result_id) as unique_results,
                        COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM share_tracking 
                    GROUP BY platform
                """
                result = self.session.execute(text(query))
            
            rows = result.fetchall()
            
            stats = {}
            total_shares = 0
            
            for row in rows:
                platform = row[0]
                share_count = row[1]
                total_shares += share_count
                
                stats[platform] = {
                    'share_count': share_count,
                    'active_days': row[2] if len(row) > 2 else row[2]
                }
                
                if not result_id and len(row) > 3:
                    stats[platform]['unique_results'] = row[2]
            
            stats['total_shares'] = total_shares
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get share stats: {str(e)}")
            return {}
    
    async def cleanup_old_images(self, days_old: int = 30) -> int:
        """清理舊的分享圖片"""
        
        try:
            # 獲取舊圖片記錄
            query = f"""
                SELECT image_url FROM share_images 
                WHERE created_at < datetime('now', '-{days_old} days')
            """
            
            result = self.session.execute(text(query))
            old_images = result.fetchall()
            
            cleaned_count = 0
            for row in old_images:
                image_url = row[0]
                if image_url.startswith('/static/share_images/'):
                    filename = image_url.split('/')[-1]
                    filepath = os.path.join(self.upload_dir, filename)
                    
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        cleaned_count += 1
            
            # 刪除數據庫記錄
            delete_query = f"""
                DELETE FROM share_images 
                WHERE created_at < datetime('now', '-{days_old} days')
            """
            
            self.session.execute(text(delete_query))
            self.session.commit()
            
            logger.info(f"Cleaned up {cleaned_count} old share images")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {str(e)}")
            self.session.rollback()
            return 0

# 全局服務實例
_share_service = None

def get_share_service() -> ShareService:
    """獲取分享服務實例"""
    global _share_service
    if _share_service is None:
        _share_service = ShareService()
    return _share_service
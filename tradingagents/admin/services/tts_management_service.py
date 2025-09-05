"""
TTS (Text-to-Speech) 管理服務
提供完整的語音合成管理功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid
import psycopg2
from fastapi import HTTPException, UploadFile
import json

logger = logging.getLogger(__name__)

class TTSManagementService:
    """TTS 語音管理服務"""
    
    def __init__(self):
        self.db_config = {
            'host': '35.194.205.200',
            'port': 5432,
            'database': 'tradingagents',
            'user': 'postgres',
            'password': 'secure_postgres_password_2024'
        }
    
    def get_connection(self):
        """獲取資料庫連接"""
        return psycopg2.connect(**self.db_config)
    
    async def get_tts_voices(self, language: Optional[str] = None, 
                           gender: Optional[str] = None, 
                           active_only: bool = False) -> List[Dict]:
        """獲取 TTS 語音列表"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            query = "SELECT * FROM tts_voice_models WHERE 1=1"
            params = []
            
            if language:
                query += " AND language = %s"
                params.append(language)
            
            if gender:
                query += " AND gender = %s"
                params.append(gender)
            
            if active_only:
                query += " AND is_active = TRUE"
            
            query += " ORDER BY language, name"
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            # 轉換為字典格式
            columns = [desc[0] for desc in cur.description]
            voices = [dict(zip(columns, row)) for row in results]
            
            cur.close()
            conn.close()
            
            return voices
            
        except Exception as e:
            logger.error(f"獲取 TTS 語音列表失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取語音列表失敗: {str(e)}")
    
    async def create_tts_voice(self, voice_data: Dict) -> Dict:
        """創建新的 TTS 語音"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 插入新語音模型
            cur.execute("""
                INSERT INTO tts_voice_models (
                    model_id, name, description, language, gender, voice_type,
                    provider, is_active, is_premium, cost_per_character, sample_rate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (
                voice_data.get('model_id'),
                voice_data.get('name'),
                voice_data.get('description'),
                voice_data.get('language'),
                voice_data.get('gender'),
                voice_data.get('voice_type', 'neural'),
                voice_data.get('provider'),
                voice_data.get('is_active', True),
                voice_data.get('is_premium', False),
                voice_data.get('cost_per_character', 0.0),
                voice_data.get('sample_rate', 22050)
            ))
            
            result = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
            voice = dict(zip(columns, result))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return voice
            
        except Exception as e:
            logger.error(f"創建 TTS 語音失敗: {e}")
            raise HTTPException(status_code=500, detail=f"創建語音失敗: {str(e)}")
    
    async def update_tts_voice(self, voice_id: str, voice_data: Dict) -> Dict:
        """更新 TTS 語音"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 更新語音模型
            cur.execute("""
                UPDATE tts_voice_models 
                SET name = %s, description = %s, is_active = %s, 
                    cost_per_character = %s, updated_at = NOW()
                WHERE model_id = %s
                RETURNING *
            """, (
                voice_data.get('name'),
                voice_data.get('description'),
                voice_data.get('is_active'),
                voice_data.get('cost_per_character'),
                voice_id
            ))
            
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="語音不存在")
                
            columns = [desc[0] for desc in cur.description]
            voice = dict(zip(columns, result))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return voice
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新 TTS 語音失敗: {e}")
            raise HTTPException(status_code=500, detail=f"更新語音失敗: {str(e)}")
    
    async def delete_tts_voice(self, voice_id: str):
        """刪除 TTS 語音"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 檢查是否有相關任務
            cur.execute("SELECT COUNT(*) FROM tts_jobs WHERE voice_model_id = (SELECT id FROM tts_voice_models WHERE model_id = %s)", (voice_id,))
            job_count = cur.fetchone()[0]
            
            if job_count > 0:
                raise HTTPException(status_code=400, detail=f"無法刪除語音，還有 {job_count} 個相關任務")
            
            # 刪除語音模型
            cur.execute("DELETE FROM tts_voice_models WHERE model_id = %s", (voice_id,))
            
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="語音不存在")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刪除 TTS 語音失敗: {e}")
            raise HTTPException(status_code=500, detail=f"刪除語音失敗: {str(e)}")
    
    async def get_tts_jobs(self, page: int = 1, limit: int = 20, 
                          status: Optional[str] = None,
                          user_id: Optional[str] = None,
                          voice_id: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict]:
        """獲取 TTS 任務列表"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            offset = (page - 1) * limit
            
            query = """
                SELECT j.*, vm.name as voice_name, u.email as user_email
                FROM tts_jobs j
                LEFT JOIN tts_voice_models vm ON j.voice_model_id = vm.id
                LEFT JOIN users u ON j.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND j.status = %s"
                params.append(status)
            
            if user_id:
                query += " AND j.user_id = %s"
                params.append(user_id)
            
            if voice_id:
                query += " AND vm.model_id = %s"
                params.append(voice_id)
            
            if start_date:
                query += " AND j.created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND j.created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            columns = [desc[0] for desc in cur.description]
            jobs = [dict(zip(columns, row)) for row in results]
            
            # 轉換時間格式
            for job in jobs:
                for key in ['created_at', 'started_at', 'completed_at']:
                    if job.get(key):
                        job[key] = job[key].isoformat()
            
            cur.close()
            conn.close()
            
            return jobs
            
        except Exception as e:
            logger.error(f"獲取 TTS 任務列表失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")
    
    async def get_tts_job(self, job_id: str) -> Optional[Dict]:
        """獲取特定 TTS 任務"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT j.*, vm.name as voice_name, u.email as user_email
                FROM tts_jobs j
                LEFT JOIN tts_voice_models vm ON j.voice_model_id = vm.id
                LEFT JOIN users u ON j.user_id = u.id
                WHERE j.job_id = %s
            """, (job_id,))
            
            result = cur.fetchone()
            
            if not result:
                return None
                
            columns = [desc[0] for desc in cur.description]
            job = dict(zip(columns, result))
            
            # 轉換時間格式
            for key in ['created_at', 'started_at', 'completed_at']:
                if job.get(key):
                    job[key] = job[key].isoformat()
            
            cur.close()
            conn.close()
            
            return job
            
        except Exception as e:
            logger.error(f"獲取 TTS 任務失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取任務失敗: {str(e)}")
    
    async def retry_tts_job(self, job_id: str) -> Dict:
        """重試 TTS 任務"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 更新任務狀態
            cur.execute("""
                UPDATE tts_jobs 
                SET status = 'pending', retry_count = retry_count + 1,
                    error_message = NULL, updated_at = NOW()
                WHERE job_id = %s AND status IN ('failed', 'cancelled')
                RETURNING *
            """, (job_id,))
            
            result = cur.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="任務不存在或狀態不允許重試")
            
            columns = [desc[0] for desc in cur.description]
            job = dict(zip(columns, result))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return {"message": "任務已重新排隊", "job": job}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"重試 TTS 任務失敗: {e}")
            raise HTTPException(status_code=500, detail=f"重試任務失敗: {str(e)}")
    
    async def cancel_tts_job(self, job_id: str):
        """取消 TTS 任務"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE tts_jobs 
                SET status = 'cancelled', updated_at = NOW()
                WHERE job_id = %s AND status IN ('pending', 'processing')
            """, (job_id,))
            
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="任務不存在或無法取消")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"取消 TTS 任務失敗: {e}")
            raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")
    
    async def get_tts_stats(self, period: str = "today") -> Dict:
        """獲取 TTS 統計數據"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 設置時間範圍
            if period == "today":
                date_filter = "DATE(created_at) = CURRENT_DATE"
            elif period == "week":
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '7 days'"
            elif period == "month":
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '30 days'"
            else:
                date_filter = "created_at >= CURRENT_DATE - INTERVAL '365 days'"
            
            # 獲取基礎統計
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
                    AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time END) as avg_processing_time,
                    SUM(character_count) as total_characters,
                    SUM(actual_duration) as total_duration
                FROM tts_jobs 
                WHERE {date_filter}
            """)
            
            stats = cur.fetchone()
            
            # 獲取語音統計
            cur.execute("SELECT COUNT(*) FROM tts_voice_models WHERE is_active = TRUE")
            active_voices = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM tts_voice_models")
            total_voices = cur.fetchone()[0]
            
            # 計算成功率
            total_jobs = stats[0]
            completed_jobs = stats[1]
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            result = {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "pending_jobs": stats[2],
                "failed_jobs": stats[3],
                "processing_jobs": stats[4],
                "success_rate": round(success_rate, 2),
                "avg_processing_time": round(float(stats[5]) if stats[5] else 0, 2),
                "total_characters": stats[6] or 0,
                "total_duration": stats[7] or 0,
                "total_voices": total_voices,
                "active_voices": active_voices,
                "period": period
            }
            
            cur.close()
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error(f"獲取 TTS 統計失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")
    
    async def get_tts_config(self) -> Dict:
        """獲取 TTS 配置"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("SELECT config_key, config_value, data_type, description FROM tts_configs ORDER BY config_key")
            results = cur.fetchall()
            
            config = {}
            for key, value, data_type, description in results:
                # 轉換數據類型
                if data_type == 'boolean':
                    config[key] = value.lower() == 'true'
                elif data_type == 'integer':
                    config[key] = int(value) if value else 0
                elif data_type == 'float':
                    config[key] = float(value) if value else 0.0
                elif data_type == 'json':
                    config[key] = json.loads(value) if value else {}
                else:
                    config[key] = value
                
                config[f"{key}_description"] = description
            
            cur.close()
            conn.close()
            
            return config
            
        except Exception as e:
            logger.error(f"獲取 TTS 配置失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")
    
    async def update_tts_config(self, config_data: Dict) -> Dict:
        """更新 TTS 配置"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            for key, value in config_data.items():
                if not key.endswith('_description'):
                    # 轉換為字符串存儲
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value)
                    elif isinstance(value, bool):
                        value_str = str(value).lower()
                    else:
                        value_str = str(value)
                    
                    cur.execute("""
                        UPDATE tts_configs 
                        SET config_value = %s, updated_at = NOW()
                        WHERE config_key = %s
                    """, (value_str, key))
            
            conn.commit()
            cur.close()
            conn.close()
            
            # 返回更新後的配置
            return await self.get_tts_config()
            
        except Exception as e:
            logger.error(f"更新 TTS 配置失敗: {e}")
            raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")
    
    async def get_voice_models(self) -> List[Dict]:
        """獲取語音模型列表"""
        return await self.get_tts_voices(active_only=False)
    
    async def upload_voice_model(self, file: UploadFile, name: str, description: Optional[str] = None) -> Dict:
        """上傳語音模型"""
        # 這裡應該實現文件上傳邏輯
        # 暫時返回模擬結果
        return {
            "message": "語音模型上傳功能正在開發中",
            "file_name": file.filename,
            "model_name": name,
            "description": description
        }
    
    async def delete_voice_model(self, model_id: str):
        """刪除語音模型"""
        await self.delete_tts_voice(model_id)
    
    async def get_audio_files(self, page: int = 1, limit: int = 20,
                             user_id: Optional[str] = None,
                             voice_id: Optional[str] = None) -> List[Dict]:
        """獲取音頻文件列表"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            offset = (page - 1) * limit
            
            query = """
                SELECT af.*, j.text_content, vm.name as voice_name, u.email as user_email
                FROM tts_audio_files af
                LEFT JOIN tts_jobs j ON af.job_id = j.id
                LEFT JOIN tts_voice_models vm ON af.voice_model_id = vm.id
                LEFT JOIN users u ON af.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND af.user_id = %s"
                params.append(user_id)
            
            if voice_id:
                query += " AND vm.model_id = %s"
                params.append(voice_id)
            
            query += " ORDER BY af.created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            columns = [desc[0] for desc in cur.description]
            files = [dict(zip(columns, row)) for row in results]
            
            # 轉換時間格式
            for file in files:
                for key in ['created_at', 'updated_at', 'last_accessed_at']:
                    if file.get(key):
                        file[key] = file[key].isoformat()
            
            cur.close()
            conn.close()
            
            return files
            
        except Exception as e:
            logger.error(f"獲取音頻文件列表失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取文件列表失敗: {str(e)}")
    
    async def delete_audio_file(self, file_id: str):
        """刪除音頻文件"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute("DELETE FROM tts_audio_files WHERE file_id = %s", (file_id,))
            
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="音頻文件不存在")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刪除音頻文件失敗: {e}")
            raise HTTPException(status_code=500, detail=f"刪除文件失敗: {str(e)}")
    
    async def get_tts_usage_report(self, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None,
                                  user_id: Optional[str] = None) -> Dict:
        """獲取 TTS 使用報告"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            query = "SELECT * FROM tts_usage_stats WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            query += " ORDER BY date DESC"
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            columns = [desc[0] for desc in cur.description]
            usage_data = [dict(zip(columns, row)) for row in results]
            
            # 計算總計
            total_jobs = sum(row['jobs_count'] for row in usage_data)
            total_characters = sum(row['characters_count'] for row in usage_data)
            total_cost = sum(float(row['total_cost']) for row in usage_data)
            
            cur.close()
            conn.close()
            
            return {
                "usage_data": usage_data,
                "summary": {
                    "total_jobs": total_jobs,
                    "total_characters": total_characters,
                    "total_cost": total_cost,
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"獲取 TTS 使用報告失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取使用報告失敗: {str(e)}")
    
    async def test_tts_synthesis(self, text: str, voice_id: str) -> Dict:
        """測試 TTS 語音合成"""
        # 這裡應該實現實際的語音合成邏輯
        # 暫時返回模擬結果
        return {
            "message": "TTS 語音合成測試功能正在開發中",
            "text": text,
            "voice_id": voice_id,
            "estimated_duration": len(text) * 0.1,  # 簡單估算
            "test_job_id": str(uuid.uuid4())
        }
    
    async def batch_cleanup_audio_files(self, days_old: int = 30) -> Dict:
        """批量清理舊音頻文件"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 查找需要清理的文件
            cur.execute("""
                SELECT COUNT(*) FROM tts_audio_files 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days_old,))
            
            file_count = cur.fetchone()[0]
            
            # 執行清理
            cur.execute("""
                DELETE FROM tts_audio_files 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """, (days_old,))
            
            deleted_count = cur.rowcount
            
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                "message": f"批量清理完成",
                "files_found": file_count,
                "files_deleted": deleted_count,
                "days_old": days_old
            }
            
        except Exception as e:
            logger.error(f"批量清理音頻文件失敗: {e}")
            raise HTTPException(status_code=500, detail=f"批量清理失敗: {str(e)}")
    
    async def get_tts_queue_status(self) -> Dict:
        """獲取 TTS 任務隊列狀態"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 獲取隊列統計
            cur.execute("""
                SELECT 
                    COUNT(*) as total_queued,
                    COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing,
                    AVG(attempts) as avg_attempts
                FROM tts_job_queue
            """)
            
            queue_stats = cur.fetchone()
            
            # 獲取正在處理的任務
            cur.execute("""
                SELECT j.job_id, j.text_content, vm.name as voice_name
                FROM tts_job_queue jq
                JOIN tts_jobs j ON jq.job_id = j.id
                LEFT JOIN tts_voice_models vm ON j.voice_model_id = vm.id
                WHERE jq.status = 'processing'
                LIMIT 5
            """)
            
            processing_jobs = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return {
                "queue_size": queue_stats[0] or 0,
                "queued_jobs": queue_stats[1] or 0,
                "processing_jobs": queue_stats[2] or 0,
                "avg_attempts": float(queue_stats[3]) if queue_stats[3] else 0,
                "is_processing": queue_stats[2] > 0,
                "system_load": min(100, (queue_stats[2] or 0) * 20),  # 簡單的負載計算
                "processing_job_samples": [
                    {
                        "job_id": job[0],
                        "text_preview": job[1][:50] + "..." if len(job[1]) > 50 else job[1],
                        "voice_name": job[2]
                    } for job in processing_jobs
                ]
            }
            
        except Exception as e:
            logger.error(f"獲取 TTS 隊列狀態失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取隊列狀態失敗: {str(e)}")
    
    async def clear_tts_queue(self) -> Dict:
        """清空 TTS 任務隊列"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # 計算要清除的任務數
            cur.execute("SELECT COUNT(*) FROM tts_job_queue WHERE status = 'queued'")
            queued_count = cur.fetchone()[0]
            
            # 清除排隊中的任務
            cur.execute("DELETE FROM tts_job_queue WHERE status = 'queued'")
            deleted_count = cur.rowcount
            
            # 更新相關任務狀態
            cur.execute("""
                UPDATE tts_jobs 
                SET status = 'cancelled', updated_at = NOW()
                WHERE status = 'pending'
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                "message": "TTS 任務隊列已清空",
                "queued_jobs_found": queued_count,
                "jobs_cancelled": deleted_count
            }
            
        except Exception as e:
            logger.error(f"清空 TTS 隊列失敗: {e}")
            raise HTTPException(status_code=500, detail=f"清空隊列失敗: {str(e)}")
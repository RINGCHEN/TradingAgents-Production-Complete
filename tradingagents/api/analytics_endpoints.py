"""
數據分析API端點
提供數據倉庫管理、ETL控制和品質監控的API接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import logging
import asyncio
import os

from ..core.deps import get_current_user, require_admin
from ...analytics.warehouse import DataWarehouseManager
from ...analytics.etl import ETLScheduler
from ...analytics.quality import DataQualityMonitor

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/analytics", tags=["數據分析"])

# 全局變量存儲管理器實例
_warehouse_manager = None
_etl_scheduler = None  
_quality_monitor = None

def get_warehouse_manager() -> DataWarehouseManager:
    """獲取數據倉庫管理器實例"""
    global _warehouse_manager
    if _warehouse_manager is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL環境變數未設置")
        _warehouse_manager = DataWarehouseManager(database_url)
    return _warehouse_manager

def get_etl_scheduler() -> ETLScheduler:
    """獲取ETL調度器實例"""
    global _etl_scheduler
    if _etl_scheduler is None:
        warehouse = get_warehouse_manager()
        _etl_scheduler = ETLScheduler(warehouse)
        # 非同步設置默認任務
        asyncio.create_task(_etl_scheduler.setup_default_jobs())
    return _etl_scheduler

def get_quality_monitor() -> DataQualityMonitor:
    """獲取品質監控器實例"""
    global _quality_monitor
    if _quality_monitor is None:
        warehouse = get_warehouse_manager()
        _quality_monitor = DataQualityMonitor(warehouse)
        _quality_monitor.register_quality_rules()
    return _quality_monitor

# 數據倉庫管理端點

@router.get("/warehouse/health")
async def get_warehouse_health():
    """獲取數據倉庫健康狀態"""
    try:
        warehouse = get_warehouse_manager()
        health_status = await warehouse.health_check()
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        logger.error(f"獲取數據倉庫健康狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {str(e)}")

@router.post("/warehouse/initialize", dependencies=[Depends(require_admin)])
async def initialize_warehouse(background_tasks: BackgroundTasks):
    """初始化數據倉庫（管理員權限）"""
    try:
        warehouse = get_warehouse_manager()
        
        # 在背景任務中執行初始化
        async def init_task():
            try:
                await warehouse.setup_data_warehouse()
                await warehouse.populate_ai_analysts_dimension()
                await warehouse.populate_products_dimension()
                logger.info("✅ 數據倉庫初始化完成")
            except Exception as e:
                logger.error(f"❌ 數據倉庫初始化失敗: {e}")
        
        background_tasks.add_task(init_task)
        
        return {
            "success": True,
            "message": "數據倉庫初始化任務已啟動，請稍後查看健康狀態"
        }
    except Exception as e:
        logger.error(f"啟動數據倉庫初始化失敗: {e}")
        raise HTTPException(status_code=500, detail=f"初始化失敗: {str(e)}")

@router.get("/warehouse/statistics")
async def get_warehouse_statistics():
    """獲取數據倉庫統計信息"""
    try:
        warehouse = get_warehouse_manager()
        stats = await warehouse.get_warehouse_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"獲取數據倉庫統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")

# ETL管理端點

@router.get("/etl/status")
async def get_etl_status(job_name: Optional[str] = None):
    """獲取ETL任務狀態"""
    try:
        etl_scheduler = get_etl_scheduler()
        status = etl_scheduler.get_job_status(job_name)
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"獲取ETL狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取ETL狀態失敗: {str(e)}")

@router.post("/etl/run", dependencies=[Depends(require_admin)])
async def run_etl_jobs(background_tasks: BackgroundTasks, job_name: Optional[str] = None):
    """執行ETL任務（管理員權限）"""
    try:
        etl_scheduler = get_etl_scheduler()
        
        async def etl_task():
            try:
                if job_name:
                    result = await etl_scheduler.run_etl_job(job_name)
                    logger.info(f"✅ ETL任務 {job_name} 執行完成: {result.status.value}")
                else:
                    results = await etl_scheduler.run_all_jobs()
                    completed = len([r for r in results if r.status.value == 'completed'])
                    logger.info(f"✅ ETL批量執行完成: {completed}/{len(results)} 成功")
            except Exception as e:
                logger.error(f"❌ ETL任務執行失敗: {e}")
        
        background_tasks.add_task(etl_task)
        
        return {
            "success": True,
            "message": f"ETL任務已啟動：{'所有任務' if not job_name else job_name}"
        }
    except Exception as e:
        logger.error(f"啟動ETL任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"ETL執行失敗: {str(e)}")

@router.get("/etl/history")
async def get_etl_history(limit: int = 50):
    """獲取ETL執行歷史"""
    try:
        etl_scheduler = get_etl_scheduler()
        
        # 返回最近的執行歷史
        history = etl_scheduler.job_history[-limit:] if etl_scheduler.job_history else []
        
        formatted_history = [
            {
                "job_name": h.job_name,
                "status": h.status.value,
                "start_time": h.start_time,
                "end_time": h.end_time,
                "execution_time_seconds": h.execution_time_seconds,
                "records_processed": h.records_processed,
                "records_inserted": h.records_inserted,
                "records_updated": h.records_updated,
                "error_message": h.error_message
            } for h in history
        ]
        
        return {
            "success": True,
            "data": {
                "history": formatted_history,
                "total_executions": len(etl_scheduler.job_history)
            }
        }
    except Exception as e:
        logger.error(f"獲取ETL歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取ETL歷史失敗: {str(e)}")

# 數據品質監控端點

@router.get("/quality/dashboard")
async def get_quality_dashboard():
    """獲取數據品質監控儀表板"""
    try:
        quality_monitor = get_quality_monitor()
        dashboard_data = await quality_monitor.generate_quality_dashboard_data()
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"獲取品質儀表板失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取品質儀表板失敗: {str(e)}")

@router.get("/quality/scan/{table_name}")
async def scan_table_quality(table_name: str):
    """掃描指定表的數據品質"""
    try:
        quality_monitor = get_quality_monitor()
        report = await quality_monitor.check_table_quality(table_name)
        
        return {
            "success": True,
            "data": {
                "table_name": report.table_name,
                "scan_time": report.scan_time,
                "total_records": report.total_records,
                "overall_score": report.overall_score,
                "passed_rules": report.passed_rules,
                "failed_rules": report.failed_rules,
                "issues": [
                    {
                        "rule_name": issue.rule_name,
                        "rule_type": issue.rule_type.value,
                        "severity": issue.severity.value,
                        "description": issue.issue_description,
                        "affected_records": issue.affected_records,
                        "issue_percentage": issue.issue_percentage,
                        "sample_values": issue.sample_values
                    } for issue in report.issues
                ]
            }
        }
    except Exception as e:
        logger.error(f"掃描表品質失敗: {e}")
        raise HTTPException(status_code=500, detail=f"品質掃描失敗: {str(e)}")

@router.post("/quality/scan-all", dependencies=[Depends(require_admin)])
async def scan_all_tables_quality(background_tasks: BackgroundTasks):
    """掃描所有表的數據品質（管理員權限）"""
    try:
        quality_monitor = get_quality_monitor()
        
        async def scan_task():
            try:
                reports = await quality_monitor.scan_all_tables()
                logger.info(f"✅ 品質掃描完成: {len(reports)} 個表")
            except Exception as e:
                logger.error(f"❌ 品質掃描失敗: {e}")
        
        background_tasks.add_task(scan_task)
        
        return {
            "success": True,
            "message": "數據品質全面掃描已啟動"
        }
    except Exception as e:
        logger.error(f"啟動品質掃描失敗: {e}")
        raise HTTPException(status_code=500, detail=f"品質掃描失敗: {str(e)}")

@router.get("/quality/alerts")
async def get_quality_alerts():
    """獲取數據品質告警"""
    try:
        quality_monitor = get_quality_monitor()
        alerts = await quality_monitor.get_quality_alerts()
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "alert_count": len(alerts),
                "critical_alerts": len([a for a in alerts if a['severity'] == 'critical']),
                "error_alerts": len([a for a in alerts if a['severity'] == 'error'])
            }
        }
    except Exception as e:
        logger.error(f"獲取品質告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取告警失敗: {str(e)}")

# 綜合分析端點

@router.get("/overview")
async def get_analytics_overview():
    """獲取數據分析平台總覽"""
    try:
        warehouse = get_warehouse_manager()
        etl_scheduler = get_etl_scheduler() 
        quality_monitor = get_quality_monitor()
        
        # 並行獲取各種狀態
        health_status, warehouse_stats, etl_status, quality_dashboard = await asyncio.gather(
            warehouse.health_check(),
            warehouse.get_warehouse_statistics(),
            asyncio.create_task(asyncio.coroutine(lambda: etl_scheduler.get_job_status())()),
            quality_monitor.generate_quality_dashboard_data()
        )
        
        return {
            "success": True,
            "data": {
                "warehouse_health": health_status,
                "warehouse_statistics": warehouse_stats,
                "etl_status": etl_status,
                "quality_overview": quality_dashboard['overview'],
                "last_updated": datetime.now(),
                "platform_status": "healthy" if health_status['status'] == 'healthy' else "warning"
            }
        }
    except Exception as e:
        logger.error(f"獲取分析平台總覽失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取總覽失敗: {str(e)}")

# 測試端點

@router.get("/test/connection")
async def test_analytics_connection():
    """測試數據分析平台連接"""
    try:
        warehouse = get_warehouse_manager()
        
        # 測試數據庫連接
        async with warehouse.async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
        
        return {
            "success": True,
            "message": "數據分析平台連接正常",
            "database_test": test_value == 1,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"連接測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"連接測試失敗: {str(e)}")

# 清理資源
@router.on_event("shutdown")
async def cleanup_analytics_resources():
    """應用關閉時清理資源"""
    global _warehouse_manager
    if _warehouse_manager:
        await _warehouse_manager.close()
        logger.info("數據分析平台資源已清理")
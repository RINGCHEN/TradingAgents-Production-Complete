#!/usr/bin/env python3
"""
不老傳說品牌部署監控系統
監控品牌更新部署的健康狀態並在異常時觸發回滾

功能：
1. 實時監控系統健康指標
2. 檢測品牌更新的影響
3. 自動觸發回滾機制
4. 生成監控報告
"""

import os
import json
import time
import requests
import logging
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class HealthMetrics:
    """健康指標數據類"""
    timestamp: datetime
    response_time: float
    error_rate: float
    availability: float
    brand_consistency: bool
    user_feedback_score: float

class BrandDeploymentMonitor:
    """品牌部署監控器"""
    
    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.metrics_history: List[HealthMetrics] = []
        self.alert_thresholds = self.config.get('alerts', {})
        self.rollback_triggers = self.config.get('rollback_triggers', {})
        
    def load_config(self, config_path: str) -> Dict:
        """載入監控配置"""
        default_config = {
            'alerts': {
                'error_rate_threshold': 0.05,
                'response_time_threshold': 2000,
                'availability_threshold': 0.99,
                'brand_consistency_required': True
            },
            'rollback_triggers': {
                'error_rate_exceeds': 0.1,
                'availability_below': 0.95,
                'response_time_exceeds': 5000,
                'brand_inconsistency_detected': True,
                'manual_trigger': True,
                'rollback_confirmation_required': True
            },
            'monitoring_endpoints': [
                'http://localhost:8000/api/health',
                'http://localhost:8000/api/brand/status',
                'http://localhost:8000/',
                'http://localhost:3000/'
            ],
            'monitoring_interval': 30,  # 秒
            'alert_cooldown': 300,     # 秒
            'rollback_confirmation_required': True
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def setup_logging(self):
        """設置日誌"""
        log_dir = 'deployment/logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = f"{log_dir}/brand_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def check_endpoint_health(self, endpoint: str) -> Dict:
        """檢查單一端點健康狀態"""
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            response_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            return {
                'endpoint': endpoint,
                'status_code': response.status_code,
                'response_time': response_time,
                'is_healthy': response.status_code == 200,
                'content': response.text[:500],  # 只保存前500字符用於分析
                'error': None
            }
            
        except requests.RequestException as e:
            return {
                'endpoint': endpoint,
                'status_code': None,
                'response_time': None,
                'is_healthy': False,
                'content': None,
                'error': str(e)
            }
    
    def check_brand_consistency(self, endpoint_results: List[Dict]) -> bool:
        """檢查品牌一致性"""
        brand_keywords = ['不老傳說', 'bulao-chuanshuo', '不老传说']
        old_brand_keywords = ['TradingAgents', 'tradingagents']
        
        for result in endpoint_results:
            if result['is_healthy'] and result['content']:
                content = result['content'].lower()
                
                # 檢查是否包含新品牌
                has_new_brand = any(keyword in result['content'] for keyword in brand_keywords)
                
                # 檢查是否還有舊品牌殘留
                has_old_brand = any(keyword.lower() in content for keyword in old_brand_keywords)
                
                if not has_new_brand or has_old_brand:
                    self.logger.warning(f"品牌不一致檢測: {result['endpoint']}")
                    return False
        
        return True
    
    def collect_metrics(self) -> HealthMetrics:
        """收集系統健康指標"""
        endpoints = self.config['monitoring_endpoints']
        endpoint_results = []
        
        # 檢查所有端點
        for endpoint in endpoints:
            result = self.check_endpoint_health(endpoint)
            endpoint_results.append(result)
        
        # 計算整體指標
        healthy_endpoints = [r for r in endpoint_results if r['is_healthy']]
        total_endpoints = len(endpoint_results)
        
        if not healthy_endpoints:
            availability = 0.0
            avg_response_time = float('inf')
            error_rate = 1.0
        else:
            availability = len(healthy_endpoints) / total_endpoints
            avg_response_time = sum(r['response_time'] for r in healthy_endpoints) / len(healthy_endpoints)
            error_rate = 1.0 - availability
        
        # 檢查品牌一致性
        brand_consistency = self.check_brand_consistency(endpoint_results)
        
        # 用戶反饋評分（模擬，實際應該從真實數據獲取）
        user_feedback_score = 4.5  # 暫時使用模擬數據
        
        metrics = HealthMetrics(
            timestamp=datetime.now(),
            response_time=avg_response_time,
            error_rate=error_rate,
            availability=availability,
            brand_consistency=brand_consistency,
            user_feedback_score=user_feedback_score
        )
        
        self.metrics_history.append(metrics)
        
        # 只保留最近24小時的數據
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        return metrics
    
    def should_trigger_alert(self, metrics: HealthMetrics) -> List[str]:
        """檢查是否應該觸發警報"""
        alerts = []
        
        if metrics.error_rate > self.alert_thresholds['error_rate_threshold']:
            alerts.append(f"錯誤率過高: {metrics.error_rate:.2%}")
        
        if metrics.response_time > self.alert_thresholds['response_time_threshold']:
            alerts.append(f"響應時間過長: {metrics.response_time:.0f}ms")
        
        if metrics.availability < self.alert_thresholds['availability_threshold']:
            alerts.append(f"可用性過低: {metrics.availability:.2%}")
        
        if not metrics.brand_consistency and self.alert_thresholds['brand_consistency_required']:
            alerts.append("品牌一致性檢查失敗")
        
        return alerts
    
    def should_trigger_rollback(self, metrics: HealthMetrics) -> bool:
        """檢查是否應該觸發回滾"""
        if metrics.error_rate > self.rollback_triggers['error_rate_exceeds']:
            self.logger.error(f"觸發回滾條件: 錯誤率 {metrics.error_rate:.2%}")
            return True
        
        if metrics.availability < self.rollback_triggers['availability_below']:
            self.logger.error(f"觸發回滾條件: 可用性 {metrics.availability:.2%}")
            return True
        
        if metrics.response_time > self.rollback_triggers.get('response_time_exceeds', float('inf')):
            self.logger.error(f"觸發回滾條件: 響應時間 {metrics.response_time:.0f}ms")
            return True
        
        if not metrics.brand_consistency and self.rollback_triggers['brand_inconsistency_detected']:
            self.logger.error("觸發回滾條件: 品牌不一致")
            return True
        
        return False
    
    def execute_rollback(self, reason: str):
        """執行自動回滾"""
        self.logger.critical(f"開始執行自動回滾: {reason}")
        
        if self.rollback_triggers['rollback_confirmation_required']:
            print(f"\n⚠️  ROLLBACK TRIGGER: {reason}")
            print("是否確認執行回滾？ (y/N): ", end='')
            confirmation = input().strip().lower()
            
            if confirmation != 'y':
                self.logger.info("用戶取消回滾操作")
                return False
        
        try:
            # 查找最新的備份
            backup_dirs = []
            if os.path.exists('deployment/backups'):
                for item in os.listdir('deployment/backups'):
                    if item.startswith('brand_update_'):
                        backup_dirs.append(item)
            
            if not backup_dirs:
                self.logger.error("找不到可用的備份目錄")
                return False
            
            # 使用最新的備份
            latest_backup = sorted(backup_dirs)[-1]
            backup_path = f"deployment/backups/{latest_backup}"
            
            self.logger.info(f"使用備份: {backup_path}")
            
            # 執行回滾腳本
            cmd = ['python', 'deployment/brand_deployment_script.py', 'rollback']
            env = os.environ.copy()
            env['BACKUP_DIR'] = backup_path
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                self.logger.info("回滾執行成功")
                return True
            else:
                self.logger.error(f"回滾執行失敗: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"回滾執行異常: {e}")
            return False
    
    def generate_report(self) -> Dict:
        """生成監控報告"""
        if not self.metrics_history:
            return {'error': '沒有可用的監控數據'}
        
        recent_metrics = self.metrics_history[-10:]  # 最近10次測量
        
        report = {
            'report_time': datetime.now().isoformat(),
            'monitoring_period': {
                'start': self.metrics_history[0].timestamp.isoformat(),
                'end': self.metrics_history[-1].timestamp.isoformat(),
                'total_measurements': len(self.metrics_history)
            },
            'current_status': {
                'response_time': recent_metrics[-1].response_time,
                'error_rate': recent_metrics[-1].error_rate,
                'availability': recent_metrics[-1].availability,
                'brand_consistency': recent_metrics[-1].brand_consistency,
                'user_feedback_score': recent_metrics[-1].user_feedback_score
            },
            'trends': {
                'avg_response_time': sum(m.response_time for m in recent_metrics) / len(recent_metrics),
                'avg_error_rate': sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
                'avg_availability': sum(m.availability for m in recent_metrics) / len(recent_metrics),
                'brand_consistency_rate': sum(1 for m in recent_metrics if m.brand_consistency) / len(recent_metrics)
            },
            'health_status': 'healthy' if recent_metrics[-1].availability > 0.95 and recent_metrics[-1].error_rate < 0.05 else 'unhealthy'
        }
        
        return report
    
    def start_monitoring(self, duration: Optional[int] = None):
        """開始監控"""
        self.logger.info("開始品牌部署監控...")
        self.logger.info(f"監控間隔: {self.config['monitoring_interval']}秒")
        
        start_time = time.time()
        last_alert_time = 0
        
        try:
            while True:
                # 收集指標
                metrics = self.collect_metrics()
                
                # 檢查警報
                alerts = self.should_trigger_alert(metrics)
                if alerts and (time.time() - last_alert_time) > self.config['alert_cooldown']:
                    for alert in alerts:
                        self.logger.warning(f"🚨 ALERT: {alert}")
                    last_alert_time = time.time()
                
                # 檢查回滾條件
                if self.should_trigger_rollback(metrics):
                    reason = f"健康檢查失敗 - 錯誤率: {metrics.error_rate:.2%}, 可用性: {metrics.availability:.2%}"
                    self.execute_rollback(reason)
                    break
                
                # 記錄當前狀態
                self.logger.info(
                    f"監控狀態 - 響應時間: {metrics.response_time:.0f}ms, "
                    f"錯誤率: {metrics.error_rate:.2%}, "
                    f"可用性: {metrics.availability:.2%}, "
                    f"品牌一致性: {'✓' if metrics.brand_consistency else '✗'}"
                )
                
                # 檢查是否達到監控時長
                if duration and (time.time() - start_time) > duration:
                    self.logger.info(f"監控時長 {duration} 秒已達到，停止監控")
                    break
                
                time.sleep(self.config['monitoring_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("監控被用戶中斷")
        
        # 生成最終報告
        report = self.generate_report()
        report_path = f"deployment/logs/brand_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"監控報告已生成: {report_path}")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='不老傳說品牌部署監控系統')
    parser.add_argument('--config', help='監控配置文件路徑')
    parser.add_argument('--duration', type=int, help='監控持續時間（秒）')
    parser.add_argument('--report-only', action='store_true', help='只生成報告不執行監控')
    
    args = parser.parse_args()
    
    monitor = BrandDeploymentMonitor(args.config)
    
    if args.report_only:
        report = monitor.generate_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        monitor.start_monitoring(args.duration)

if __name__ == "__main__":
    main()
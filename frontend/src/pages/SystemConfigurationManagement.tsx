import React, { useState, useEffect } from 'react';
import './SystemConfigurationManagement.css';
import { authService } from '../services/AuthService';

// 系統配置接口定義
interface SystemConfig {
  // 系統基本設定
  system: {
    app_name: string;
    app_version: string;
    debug_mode: boolean;
    maintenance_mode: boolean;
    max_concurrent_users: number;
    session_timeout: number;
  };
  
  // API設定
  api: {
    rate_limit_per_hour: number;
    max_request_size: number;
    timeout_seconds: number;
    cors_origins: string[];
    enable_swagger: boolean;
    log_requests: boolean;
  };
  
  // 安全設定
  security: {
    jwt_expire_minutes: number;
    password_min_length: number;
    max_login_attempts: number;
    require_2fa: boolean;
    allowed_file_types: string[];
    max_file_size: number;
  };
  
  // 資料庫設定
  database: {
    connection_pool_size: number;
    query_timeout: number;
    enable_logging: boolean;
    backup_enabled: boolean;
    backup_frequency: string;
    retention_days: number;
  };
  
  // 通知設定
  notifications: {
    email_enabled: boolean;
    smtp_host: string;
    smtp_port: number;
    smtp_use_tls: boolean;
    admin_emails: string[];
    slack_webhook_url: string;
  };
  
  // 監控設定
  monitoring: {
    metrics_enabled: boolean;
    log_level: string;
    error_tracking: boolean;
    performance_monitoring: boolean;
    alert_thresholds: {
      cpu_percent: number;
      memory_percent: number;
      disk_percent: number;
      response_time_ms: number;
    };
  };
}

interface ConfigSection {
  id: string;
  name: string;
  description: string;
  icon: string;
}

const SystemConfigurationManagement: React.FC = () => {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState('system');
  const [hasChanges, setHasChanges] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // 配置節定義
  const configSections: ConfigSection[] = [
    { id: 'system', name: '系統基本設定', description: '應用程式核心配置', icon: '⚙️' },
    { id: 'api', name: 'API設定', description: 'API服務和限制配置', icon: '🔌' },
    { id: 'security', name: '安全設定', description: '安全策略和權限配置', icon: '🔒' },
    { id: 'database', name: '資料庫設定', description: '資料庫連接和備份配置', icon: '💾' },
    { id: 'notifications', name: '通知設定', description: '郵件和通知服務配置', icon: '📧' },
    { id: 'monitoring', name: '監控設定', description: '系統監控和告警配置', icon: '📊' }
  ];

  // 載入配置
  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await authService.authenticatedRequest('/admin/system/config');
      
      if (response.ok) {
        const configData = await response.json();
        setConfig(configData);
        setHasChanges(false);
      } else {
        throw new Error('載入系統配置失敗');
      }
    } catch (error) {
      console.error('載入配置失敗:', error);
      setError('載入系統配置失敗');
    } finally {
      setLoading(false);
    }
  };

  // 儲存配置
  const saveConfig = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setValidationErrors({});

      // 驗證配置
      const errors = validateConfig(config);
      if (Object.keys(errors).length > 0) {
        setValidationErrors(errors);
        return;
      }

      const response = await authService.authenticatedRequest('/admin/system/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        setHasChanges(false);
        alert('✅ 系統配置已成功更新');
        
        // 如果是關鍵配置更改，提示重啟
        const criticalSections = ['system', 'database', 'security'];
        if (criticalSections.includes(activeSection)) {
          const restart = window.confirm(
            '⚠️ 部分配置更改需要重啟系統才能生效。是否現在重啟服務？'
          );
          if (restart) {
            restartSystem();
          }
        }
      } else {
        throw new Error('儲存配置失敗');
      }
    } catch (error) {
      console.error('儲存配置失敗:', error);
      alert('❌ 儲存系統配置失敗');
    } finally {
      setSaving(false);
    }
  };

  // 重啟系統
  const restartSystem = async () => {
    try {
      const response = await authService.authenticatedRequest('/admin/system/restart', {
        method: 'POST'
      });

      if (response.ok) {
        alert('🔄 系統正在重啟，請稍後重新登錄...');
        // 延遲後重新載入頁面
        setTimeout(() => {
          window.location.reload();
        }, 5000);
      } else {
        throw new Error('系統重啟失敗');
      }
    } catch (error) {
      console.error('系統重啟失敗:', error);
      alert('❌ 系統重啟失敗');
    }
  };

  // 重置配置
  const resetConfig = async () => {
    const confirmReset = window.confirm(
      '⚠️ 確定要重置所有配置為預設值嗎？這個操作不可撤銷。'
    );
    if (!confirmReset) return;

    try {
      const response = await authService.authenticatedRequest('/admin/system/config/reset', {
        method: 'POST'
      });

      if (response.ok) {
        const defaultConfig = await response.json();
        setConfig(defaultConfig);
        setHasChanges(true);
        alert('✅ 配置已重置為預設值');
      } else {
        throw new Error('重置配置失敗');
      }
    } catch (error) {
      console.error('重置配置失敗:', error);
      alert('❌ 重置配置失敗');
    }
  };

  // 驗證配置
  const validateConfig = (config: SystemConfig): Record<string, string> => {
    const errors: Record<string, string> = {};

    // 系統配置驗證
    if (config.system.max_concurrent_users < 1) {
      errors['system.max_concurrent_users'] = '最大併發用戶數必須大於0';
    }
    if (config.system.session_timeout < 300) {
      errors['system.session_timeout'] = '會話過期時間不能少於5分鐘';
    }

    // API配置驗證
    if (config.api.rate_limit_per_hour < 1) {
      errors['api.rate_limit_per_hour'] = '速率限制必須大於0';
    }
    if (config.api.timeout_seconds < 5) {
      errors['api.timeout_seconds'] = '超時時間不能少於5秒';
    }

    // 安全配置驗證
    if (config.security.password_min_length < 6) {
      errors['security.password_min_length'] = '密碼最小長度不能少於6個字符';
    }
    if (config.security.jwt_expire_minutes < 5) {
      errors['security.jwt_expire_minutes'] = 'JWT過期時間不能少於5分鐘';
    }

    // 監控配置驗證
    const thresholds = config.monitoring.alert_thresholds;
    if (thresholds.cpu_percent < 50 || thresholds.cpu_percent > 100) {
      errors['monitoring.alert_thresholds.cpu_percent'] = 'CPU告警閾值必須在50-100之間';
    }

    return errors;
  };

  // 更新配置值
  const updateConfig = (section: keyof SystemConfig, key: string, value: any) => {
    if (!config) return;

    setConfig(prev => {
      if (!prev) return null;

      const newConfig = { ...prev };
      const sectionConfig = { ...newConfig[section] };

      // 處理嵌套對象
      if (key.includes('.')) {
        const keys = key.split('.');
        let target = sectionConfig as any;
        for (let i = 0; i < keys.length - 1; i++) {
          target[keys[i]] = { ...target[keys[i]] };
          target = target[keys[i]];
        }
        target[keys[keys.length - 1]] = value;
      } else {
        (sectionConfig as any)[key] = value;
      }

      (newConfig[section] as any) = sectionConfig;
      return newConfig;
    });

    setHasChanges(true);
  };

  // 獲取配置值
  const getConfigValue = (section: keyof SystemConfig, key: string): any => {
    if (!config) return '';

    const sectionConfig = config[section] as any;
    if (key.includes('.')) {
      const keys = key.split('.');
      let value = sectionConfig;
      for (const k of keys) {
        value = value?.[k];
      }
      return value;
    }
    return sectionConfig[key];
  };

  // 初始化
  useEffect(() => {
    loadConfig();
  }, []);

  // 防止離開頁面時丟失未儲存的更改
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);

  if (loading) {
    return (
      <div className="config-management">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>載入系統配置...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="config-management">
        <div className="error-container">
          <h3>❌ 載入失敗</h3>
          <p>{error}</p>
          <button onClick={loadConfig}>重新載入</button>
        </div>
      </div>
    );
  }

  if (!config) return null;

  return (
    <div className="config-management">
      <div className="config-header">
        <div className="header-title">
          <h2>⚙️ 系統配置管理</h2>
          <p>管理系統核心配置、安全設定和服務參數</p>
        </div>
        <div className="header-actions">
          {hasChanges && (
            <span className="changes-indicator">● 有未儲存的更改</span>
          )}
          <button 
            className="reset-btn"
            onClick={resetConfig}
            disabled={saving}
          >
            🔄 重置預設
          </button>
          <button 
            className="save-btn"
            onClick={saveConfig}
            disabled={saving || !hasChanges}
          >
            {saving ? '⏳ 儲存中...' : '💾 儲存配置'}
          </button>
        </div>
      </div>

      <div className="config-content">
        {/* 配置節導航 */}
        <div className="config-navigation">
          {configSections.map(section => (
            <button
              key={section.id}
              className={`nav-item ${activeSection === section.id ? 'active' : ''}`}
              onClick={() => setActiveSection(section.id)}
            >
              <div className="nav-icon">{section.icon}</div>
              <div className="nav-text">
                <div className="nav-title">{section.name}</div>
                <div className="nav-description">{section.description}</div>
              </div>
            </button>
          ))}
        </div>

        {/* 配置表單 */}
        <div className="config-form-container">
          {/* 系統基本設定 */}
          {activeSection === 'system' && (
            <div className="config-section">
              <h3>⚙️ 系統基本設定</h3>
              
              <div className="form-group">
                <label>應用程式名稱</label>
                <input
                  type="text"
                  value={getConfigValue('system', 'app_name')}
                  onChange={(e: any) => updateConfig('system', 'app_name', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>應用程式版本</label>
                <input
                  type="text"
                  value={getConfigValue('system', 'app_version')}
                  onChange={(e: any) => updateConfig('system', 'app_version', e.target.value)}
                  readOnly
                />
                <small>版本號由系統自動管理</small>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('system', 'debug_mode')}
                    onChange={(e: any) => updateConfig('system', 'debug_mode', e.target.checked)}
                  />
                  啟用調試模式
                </label>
                <small>⚠️ 生產環境請關閉調試模式</small>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('system', 'maintenance_mode')}
                    onChange={(e: any) => updateConfig('system', 'maintenance_mode', e.target.checked)}
                  />
                  維護模式
                </label>
                <small>啟用後將阻止一般用戶訪問</small>
              </div>

              <div className="form-group">
                <label>最大併發用戶數</label>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={getConfigValue('system', 'max_concurrent_users')}
                  onChange={(e: any) => updateConfig('system', 'max_concurrent_users', parseInt(e.target.value))}
                />
                {validationErrors['system.max_concurrent_users'] && (
                  <span className="error-message">{validationErrors['system.max_concurrent_users']}</span>
                )}
              </div>

              <div className="form-group">
                <label>會話過期時間 (秒)</label>
                <input
                  type="number"
                  min="300"
                  max="86400"
                  value={getConfigValue('system', 'session_timeout')}
                  onChange={(e: any) => updateConfig('system', 'session_timeout', parseInt(e.target.value))}
                />
                {validationErrors['system.session_timeout'] && (
                  <span className="error-message">{validationErrors['system.session_timeout']}</span>
                )}
              </div>
            </div>
          )}

          {/* API設定 */}
          {activeSection === 'api' && (
            <div className="config-section">
              <h3>🔌 API設定</h3>
              
              <div className="form-group">
                <label>每小時請求限制</label>
                <input
                  type="number"
                  min="1"
                  max="100000"
                  value={getConfigValue('api', 'rate_limit_per_hour')}
                  onChange={(e: any) => updateConfig('api', 'rate_limit_per_hour', parseInt(e.target.value))}
                />
                {validationErrors['api.rate_limit_per_hour'] && (
                  <span className="error-message">{validationErrors['api.rate_limit_per_hour']}</span>
                )}
              </div>

              <div className="form-group">
                <label>最大請求大小 (MB)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={getConfigValue('api', 'max_request_size')}
                  onChange={(e: any) => updateConfig('api', 'max_request_size', parseInt(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label>請求超時時間 (秒)</label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={getConfigValue('api', 'timeout_seconds')}
                  onChange={(e: any) => updateConfig('api', 'timeout_seconds', parseInt(e.target.value))}
                />
                {validationErrors['api.timeout_seconds'] && (
                  <span className="error-message">{validationErrors['api.timeout_seconds']}</span>
                )}
              </div>

              <div className="form-group">
                <label>CORS允許來源 (每行一個)</label>
                <textarea
                  rows={4}
                  value={getConfigValue('api', 'cors_origins')?.join('\n') || ''}
                  onChange={(e: any) => updateConfig('api', 'cors_origins', e.target.value.split('\n').filter(Boolean))}
                  placeholder="https://example.com&#10;https://app.example.com"
                />
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('api', 'enable_swagger')}
                    onChange={(e: any) => updateConfig('api', 'enable_swagger', e.target.checked)}
                  />
                  啟用 Swagger UI
                </label>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('api', 'log_requests')}
                    onChange={(e: any) => updateConfig('api', 'log_requests', e.target.checked)}
                  />
                  記錄API請求日誌
                </label>
              </div>
            </div>
          )}

          {/* 安全設定 */}
          {activeSection === 'security' && (
            <div className="config-section">
              <h3>🔒 安全設定</h3>
              
              <div className="form-group">
                <label>JWT過期時間 (分鐘)</label>
                <input
                  type="number"
                  min="5"
                  max="1440"
                  value={getConfigValue('security', 'jwt_expire_minutes')}
                  onChange={(e: any) => updateConfig('security', 'jwt_expire_minutes', parseInt(e.target.value))}
                />
                {validationErrors['security.jwt_expire_minutes'] && (
                  <span className="error-message">{validationErrors['security.jwt_expire_minutes']}</span>
                )}
              </div>

              <div className="form-group">
                <label>密碼最小長度</label>
                <input
                  type="number"
                  min="6"
                  max="64"
                  value={getConfigValue('security', 'password_min_length')}
                  onChange={(e: any) => updateConfig('security', 'password_min_length', parseInt(e.target.value))}
                />
                {validationErrors['security.password_min_length'] && (
                  <span className="error-message">{validationErrors['security.password_min_length']}</span>
                )}
              </div>

              <div className="form-group">
                <label>最大登錄嘗試次數</label>
                <input
                  type="number"
                  min="3"
                  max="10"
                  value={getConfigValue('security', 'max_login_attempts')}
                  onChange={(e: any) => updateConfig('security', 'max_login_attempts', parseInt(e.target.value))}
                />
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('security', 'require_2fa')}
                    onChange={(e: any) => updateConfig('security', 'require_2fa', e.target.checked)}
                  />
                  強制雙因素驗證
                </label>
                <small>⚠️ 啟用後所有用戶需設定2FA才能登錄</small>
              </div>

              <div className="form-group">
                <label>允許的文件類型</label>
                <input
                  type="text"
                  value={getConfigValue('security', 'allowed_file_types')?.join(', ') || ''}
                  onChange={(e: any) => updateConfig('security', 'allowed_file_types', e.target.value.split(',').map(s => s.trim()))}
                  placeholder="pdf, jpg, png, xlsx"
                />
              </div>

              <div className="form-group">
                <label>最大文件大小 (MB)</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={getConfigValue('security', 'max_file_size')}
                  onChange={(e: any) => updateConfig('security', 'max_file_size', parseInt(e.target.value))}
                />
              </div>
            </div>
          )}

          {/* 監控設定 */}
          {activeSection === 'monitoring' && (
            <div className="config-section">
              <h3>📊 監控設定</h3>
              
              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('monitoring', 'metrics_enabled')}
                    onChange={(e: any) => updateConfig('monitoring', 'metrics_enabled', e.target.checked)}
                  />
                  啟用指標收集
                </label>
              </div>

              <div className="form-group">
                <label>日誌級別</label>
                <select
                  value={getConfigValue('monitoring', 'log_level')}
                  onChange={(e: any) => updateConfig('monitoring', 'log_level', e.target.value)}
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                  <option value="CRITICAL">CRITICAL</option>
                </select>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('monitoring', 'error_tracking')}
                    onChange={(e: any) => updateConfig('monitoring', 'error_tracking', e.target.checked)}
                  />
                  啟用錯誤追蹤
                </label>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={getConfigValue('monitoring', 'performance_monitoring')}
                    onChange={(e: any) => updateConfig('monitoring', 'performance_monitoring', e.target.checked)}
                  />
                  啟用性能監控
                </label>
              </div>

              <div className="form-subsection">
                <h4>告警閾值設定</h4>
                
                <div className="form-group">
                  <label>CPU使用率告警閾值 (%)</label>
                  <input
                    type="number"
                    min="50"
                    max="100"
                    value={getConfigValue('monitoring', 'alert_thresholds.cpu_percent')}
                    onChange={(e: any) => updateConfig('monitoring', 'alert_thresholds.cpu_percent', parseInt(e.target.value))}
                  />
                  {validationErrors['monitoring.alert_thresholds.cpu_percent'] && (
                    <span className="error-message">{validationErrors['monitoring.alert_thresholds.cpu_percent']}</span>
                  )}
                </div>

                <div className="form-group">
                  <label>記憶體使用率告警閾值 (%)</label>
                  <input
                    type="number"
                    min="50"
                    max="100"
                    value={getConfigValue('monitoring', 'alert_thresholds.memory_percent')}
                    onChange={(e: any) => updateConfig('monitoring', 'alert_thresholds.memory_percent', parseInt(e.target.value))}
                  />
                </div>

                <div className="form-group">
                  <label>磁碟使用率告警閾值 (%)</label>
                  <input
                    type="number"
                    min="70"
                    max="100"
                    value={getConfigValue('monitoring', 'alert_thresholds.disk_percent')}
                    onChange={(e: any) => updateConfig('monitoring', 'alert_thresholds.disk_percent', parseInt(e.target.value))}
                  />
                </div>

                <div className="form-group">
                  <label>響應時間告警閾值 (毫秒)</label>
                  <input
                    type="number"
                    min="100"
                    max="10000"
                    value={getConfigValue('monitoring', 'alert_thresholds.response_time_ms')}
                    onChange={(e: any) => updateConfig('monitoring', 'alert_thresholds.response_time_ms', parseInt(e.target.value))}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemConfigurationManagement;
# DigitalOcean App Platform 部署配置指南

**項目**: TradingAgents Complete Production  
**版本**: v2.0 (17系統完整版)  
**目標**: 企業級生產部署  

---

## 🚀 **快速部署步驟**

### 步驟 1: 訪問 DigitalOcean App Platform
1. 登入 [DigitalOcean](https://cloud.digitalocean.com/)
2. 進入 **Apps** 頁面
3. 點擊 **Create App**

### 步驟 2: 連接 GitHub 倉庫
1. 選擇 **GitHub** 作為代碼源
2. 選擇倉庫: `TradingAgents-Deploy`
3. 選擇分支: `main`
4. 設置自動部署: ✅ **Autodeploy code changes**

### 步驟 3: 應用配置
```yaml
# App 基本設置
Name: tradingagents-production
Region: Frankfurt (fra1) # 或選擇較近的區域

# Service 配置
Service Name: api
Service Type: Web Service
Branch: main
Source Directory: / (root)
```

### 步驟 4: 建構設置
```yaml
# 建構設置 (Build Settings)
Build Command: pip install -r requirements.txt
Run Command: python -m uvicorn tradingagents.app:app --host 0.0.0.0 --port 8080

# Docker 設置 (推薦)
Dockerfile Path: Dockerfile
HTTP Port: 8000
```

---

## ⚙️ **環境變數配置**

### 🔑 **必要環境變數 (32個)**

#### 基本配置
```bash
PORT=8000
ENVIRONMENT=production
PYTHONPATH=/app
```

#### 資料庫配置
```bash
DATABASE_URL=postgresql://doadmin:your_password@your_db_host:25060/tradingagents?sslmode=require
```

#### PayUni 支付系統 (商店代號 U03823060)
```bash
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_HASH_KEY=your_production_hash_key
PAYUNI_HASH_IV=your_production_hash_iv
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false
```

#### 安全認證
```bash
SECRET_KEY=your-super-secret-key-for-production-2024-with-minimum-32-chars
JWT_SECRET=your-jwt-secret-key-for-production-2024-with-minimum-32-chars
```

#### Google OAuth
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### CORS 配置
```bash
ALLOWED_ORIGINS=https://03king.com,https://admin.03king.com,https://tradingagents-production-xxxxx.ondigitalocean.app
```

#### FinMind API
```bash
FINMIND_TOKEN=your-finmind-api-token
```

#### 前端整合
```bash
VITE_API_URL=https://tradingagents-production-xxxxx.ondigitalocean.app
VITE_PAYUNI_MERCHANT_ID=U03823060
```

#### AI 訓練 (可選)
```bash
TRADING_AGENTS_DATA_DIR=/app/ai_training_data
TRADING_AGENTS_MODELS_DIR=/app/models
CUDA_VISIBLE_DEVICES=0
```

#### 監控系統 (可選)
```bash
GRAFANA_PASSWORD=admin123
PROMETHEUS_RETENTION=15d
LOG_LEVEL=INFO
```

---

## 🗄️ **資料庫配置**

### 選項 1: DigitalOcean Managed PostgreSQL (推薦)
1. 在 DigitalOcean 創建 **Database Cluster**
2. 選擇 **PostgreSQL 14**
3. 配置: **Basic** (1 vCPU, 1GB RAM, 10GB SSD) - $15/月
4. 獲取連接字符串並設置在 `DATABASE_URL`

### 選項 2: 外部資料庫
- 可使用現有的 PostgreSQL 資料庫
- 確保網路可達性和安全配置

---

## 🔧 **高級配置**

### HTTP Routes 設置
```yaml
# 主要 API 路由
Path: /
Internal Port: 8000

# 健康檢查
Health Check Path: /health
```

### 資源配置
```yaml
# 基本配置 (推薦開始)
CPU: 1 vCPU
RAM: 1GB
Instances: 1

# 生產配置 (流量增加後)
CPU: 2 vCPU  
RAM: 2GB
Instances: 2
```

### 自動擴展 (可選)
```yaml
Min Instances: 1
Max Instances: 3
CPU Threshold: 70%
Memory Threshold: 80%
```

---

## 🌐 **域名和 SSL 配置**

### 自定義域名設置
1. 在 App 設置中添加 **Custom Domain**
2. 配置 CNAME 記錄指向 DigitalOcean
3. SSL 證書自動配置

### DNS 配置示例
```dns
# 主 API
api.tradingagents.com CNAME tradingagents-production-xxxxx.ondigitalocean.app

# 或使用現有域名
your-domain.com CNAME tradingagents-production-xxxxx.ondigitalocean.app
```

---

## 📊 **監控和日誌**

### App Metrics
- DigitalOcean 提供內建監控
- CPU、記憶體、網路流量監控
- 應用日誌實時查看

### 外部監控 (可選)
- Grafana Dashboard
- Prometheus Metrics  
- AlertManager 告警

---

## 🔍 **部署驗證清單**

### ✅ **部署前檢查**
- [ ] GitHub 倉庫已創建並推送代碼
- [ ] 環境變數已正確配置 (32個)
- [ ] 資料庫已創建並可連接
- [ ] PayUni 測試通過

### ✅ **部署中檢查**
- [ ] 建構日誌無錯誤
- [ ] 容器啟動成功
- [ ] 健康檢查通過 (`/health`)
- [ ] API 文檔可訪問 (`/docs`)

### ✅ **部署後檢查**
- [ ] PayUni 支付系統測試
- [ ] 前端系統連接測試
- [ ] API 端點功能測試
- [ ] 性能基準測試

---

## 🚨 **故障排除**

### 常見問題
1. **建構失敗**
   - 檢查 `requirements.txt` 依賴
   - 確認 Python 版本相容性

2. **啟動失敗**
   - 檢查環境變數配置
   - 確認資料庫連接

3. **API 無回應**
   - 檢查端口配置 (8000)
   - 確認 CORS 設置

4. **支付系統錯誤**
   - 驗證 PayUni 環境變數
   - 檢查 SSL 證書配置

### 緊急回滾
```bash
# 如需回滾到前一版本
1. 在 DigitalOcean App 控制台選擇 "Deployments"
2. 選擇穩定的前一版本
3. 點擊 "Redeploy"
```

---

## 💰 **成本估算**

| 服務 | 配置 | 月費 (USD) |
|------|------|----------|
| App Platform | Basic (1 vCPU, 1GB) | $5 |
| PostgreSQL | Basic (1 vCPU, 1GB) | $15 |
| 網路流量 | 1TB included | $0 |
| **總計** | | **$20** |

**vs Google Cloud**: 節省 60-70% 成本

---

## 📞 **支援聯絡**

### 技術支援
- **DigitalOcean**: [支援文檔](https://docs.digitalocean.com/products/app-platform/)
- **項目文檔**: 參考 `DEPLOYMENT_MASTER_PLAN.md`

### 緊急聯絡
- **回滾程序**: 保留在 `EMERGENCY_ROLLBACK.md`
- **監控警報**: 配置在 `monitoring/alertmanager.yml`

---

**配置完成後，您的 TradingAgents 平台將在 DigitalOcean 上以企業級標準運行！** 🚀
# 🔑 TradingAgents Production Final - 完整生產環境變數

## DigitalOcean App: twshocks-app-79rsx.ondigitalocean.app

### **立即更新的環境變數**

```bash
# === 核心配置 ===
PORT=8000
ENVIRONMENT=production

# === 資料庫配置 (新創建的PostgreSQL) ===
DATABASE_URL=postgresql://tradingagents-complete-db:AVNS_yMapXU8UtQEbEzYBAht@app-f65ee22d-0465-4beb-9eef-7b1138793d6a-do-user-20425009-0.f.db.ondigitalocean.com:25060/tradingagents-complete-db?sslmode=require

# === PayUni支付系統 (您的真實配置) ===
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false
PAYUNI_HASH_KEY=[您已填入的真實值]
PAYUNI_HASH_IV=[您已填入的真實值]

# === 安全金鑰 ===
SECRET_KEY=twshocks-production-secret-key-2025-v2-complete-32-chars
JWT_SECRET=twshocks-jwt-secret-key-2025-v2-production-complete-32

# === CORS配置 (更新) ===
ALLOWED_ORIGINS=https://03king.com,https://admin.03king.com,https://twshocks-app-79rsx.ondigitalocean.app

# === 前端整合配置 (更新) ===
VITE_API_URL=https://twshocks-app-79rsx.ondigitalocean.app
VITE_PAYUNI_MERCHANT_ID=U03823060

# === 日誌配置 ===
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 📋 **DigitalOcean App 更新步驟**

### 1. 登入DigitalOcean控制台
- 進入 Apps → twshocks-app-79rsx

### 2. 更新環境變數
- Settings → Components → api → Environment Variables
- 更新以下關鍵變數：
  - `DATABASE_URL` (最重要！)
  - `ALLOWED_ORIGINS` 
  - `VITE_API_URL`
  - `SECRET_KEY`
  - `JWT_SECRET`

### 3. 保存並重新部署
- 點擊 "Save"
- 系統會自動觸發重新部署

## 🚀 **部署後驗證命令**

```bash
# 1. 基本健康檢查
curl https://twshocks-app-79rsx.ondigitalocean.app/health

# 2. 資料庫連接驗證
curl https://twshocks-app-79rsx.ondigitalocean.app/admin/health

# 3. PayUni系統檢查
curl https://twshocks-app-79rsx.ondigitalocean.app/api/v1/payuni/health

# 4. API文檔訪問
curl https://twshocks-app-79rsx.ondigitalocean.app/docs
```

## 🎯 **預期成功結果**

```json
// /health
{
  "status": "healthy",
  "timestamp": "2025-09-06T...",
  "version": "2.0.0",
  "services": {
    "api": "running",
    "database": "connected",
    "payuni": "healthy"
  },
  "environment": "production"
}

// /api/v1/payuni/health  
{
  "service": "payuni",
  "status": "healthy",
  "merchant_id": "U03823060",
  "is_sandbox": false
}
```

## ⚠️ **重要提醒**

1. **DATABASE_URL** 是最關鍵的更新，會立即解決系統響應緩慢問題
2. 更新後需要等待2-3分鐘重新部署完成
3. 資料庫首次連接可能需要運行初始化腳本

---

**配置完成後，TradingAgents系統將完全就緒！** 🎉
# 🔑 TradingAgents Production Complete - 真實環境變數配置

## DigitalOcean App Platform 環境變數設定

### **核心基礎配置**
```
PORT=8000
ENVIRONMENT=production
PYTHONPATH=/app
```

### **資料庫配置 (新的PostgreSQL)**
```
# ⚠️ 創建新DigitalOcean資料庫後更新此值
DATABASE_URL=postgresql://doadmin:新資料庫密碼@新資料庫主機:25060/defaultdb?sslmode=require
```

### **舊資料庫連接 (參考用)**
```
# 舊系統資料庫 (僅供參考，不在新App中使用)
OLD_DATABASE_URL=postgresql://tradingagents:AVNS_fOtfMRbIZWqZONv9uta@app-b55a4269-9a20-4527-8d8d-0b7a74b38922-do-user-20425009-0.k.db.ondigitalocean.com:25060/tradingagents?sslmode=require
```

### **PayUni支付系統 (商店代號: U03823060)**
```
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false
PAYUNI_HASH_KEY=[您已填入的真實值]
PAYUNI_HASH_IV=[您已填入的真實值]
```

### **安全金鑰 (建議使用)**
```
SECRET_KEY=tradingagents-production-secret-key-2025-v2-complete-32-chars
JWT_SECRET=tradingagents-jwt-secret-key-2025-v2-production-complete-32
```

### **CORS配置 (待更新)**
```
ALLOWED_ORIGINS=https://03king.com,https://admin.03king.com,https://[新App域名].ondigitalocean.app
```

### **前端整合配置 (待更新)**
```
VITE_API_URL=https://[新App域名].ondigitalocean.app
VITE_PAYUNI_MERCHANT_ID=U03823060
```

### **FinMind台股數據 (可選)**
```
FINMIND_TOKEN=your-finmind-token-if-needed
```

### **Google OAuth配置 (如需要)**
```
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### **日誌配置**
```
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### **AI訓練配置 (雲端路徑)**
```
TRADING_AGENTS_DATA_DIR=/app/ai_training_data
TRADING_AGENTS_MODELS_DIR=/app/models
```

## 📋 配置步驟

### 1. 創建DigitalOcean App
- App名稱: `tradingagents-production-complete`
- 倉庫: `RINGCHEN/TradingAgents-Production-Complete`
- 分支: `main`

### 2. 環境變數設定順序
1. 先設定基礎配置 (PORT, ENVIRONMENT, PYTHONPATH)
2. 設定資料庫 (DATABASE_URL)
3. 設定PayUni支付系統 (4個變數)
4. 設定安全金鑰 (SECRET_KEY, JWT_SECRET)
5. 其他配置項目

### 3. 部署後更新
App創建後會獲得新域名，需要更新：
- ALLOWED_ORIGINS (加入新App域名)
- VITE_API_URL (指向新App)
- 前端配置文件 (apiConfig.ts)

## ⚠️ 重要提醒

1. **DATABASE_URL** 已使用您現有的PostgreSQL資料庫
2. **PayUni配置** 使用您已填入的真實Hash Key/IV
3. **新App** 將與現有系統共享同一個資料庫
4. **SECRET_KEY** 建議使用新金鑰以區分新舊系統

## 🚀 驗證命令

部署完成後執行：
```bash
python verify_deployment.py --url https://[新App域名].ondigitalocean.app
```

預期結果：
- API健康: ✅
- 資料庫連接: ✅ 
- PayUni支付: ✅ (merchant_id: U03823060)
- 系統狀態: production

---
**配置完成後，新App將完全繼承現有系統的數據和支付功能！**
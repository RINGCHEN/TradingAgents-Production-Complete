# 🚀 TradingAgents Production - 最簡環境變數配置

## 核心必要環境變數 (僅12個)

```bash
# === 基礎配置 ===
PORT=8000
ENVIRONMENT=production

# === 資料庫 ===
DATABASE_URL=postgresql://doadmin:密碼@主機:25060/tradingagents?sslmode=require

# === PayUni支付系統 ===
PAYUNI_MERCHANT_ID=U03823060
PAYUNI_BASE_URL=https://api.payuni.com.tw
PAYUNI_SANDBOX_MODE=false
PAYUNI_HASH_KEY=您的真實值
PAYUNI_HASH_IV=您的真實值

# === 安全金鑰 ===
SECRET_KEY=tradingagents-production-secret-2025-32-chars
JWT_SECRET=tradingagents-jwt-secret-2025-32-chars

# === CORS ===
ALLOWED_ORIGINS=https://03king.com,https://admin.03king.com

# === API URL ===
VITE_API_URL=https://部署後更新.ondigitalocean.app
```

## DigitalOcean App配置

**Build Command**: 留空 (自動偵測)
**Run Command**: python -m uvicorn tradingagents.app:app --host 0.0.0.0 --port 8080

## 部署步驟

1. **移除所有可選環境變數** (CUDA, GRAFANA, PROMETHEUS等)
2. **只設置上面12個核心變數**
3. **不要設置自定義Build Command**
4. **讓DigitalOcean自動偵測建構流程**

這樣可以避免依賴衝突和環境變數問題！
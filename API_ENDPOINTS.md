# TradingAgents API 端點指南

## 🌐 **基本 URL**

**重要**: TradingAgents 系統部署在子路徑下，所有 API 請求必須使用以下基本 URL：

```
https://twshocks-app-79rsx.ondigitalocean.app/tradingagents-production-comple2
```

## 📋 **核心 API 端點**

### 系統端點
- **主頁**: `GET /`
- **健康檢查**: `GET /health`
- **API 文檔**: `GET /docs`
- **ReDoc 文檔**: `GET /redoc`

### PayUni 支付系統
- **健康檢查**: `GET /api/v1/payuni/health`
- **創建訪客支付**: `POST /api/v1/payuni/create-guest-payment`
- **查詢支付頁面**: `GET /api/v1/payuni/payment-page/{order_number}`

### 用戶 API
- **用戶資訊**: `GET /api/user/info`
- **用戶註冊**: `POST /api/user/register`
- **用戶登入**: `POST /api/user/login`

### 管理後台 API
- **系統配置**: `GET /admin/config`
- **用戶管理**: `GET /admin/user_management/users`
- **系統監控**: `GET /admin/system/health`

### AI 分析師 API
- **開始分析**: `POST /analysis/start`
- **查詢狀態**: `GET /analysis/{session_id}/status`
- **分析師資訊**: `GET /analysts/info`

## ✅ **測試端點範例**

```bash
# 系統健康檢查
curl https://twshocks-app-79rsx.ondigitalocean.app/tradingagents-production-comple2/health

# PayUni 支付系統
curl https://twshocks-app-79rsx.ondigitalocean.app/tradingagents-production-comple2/api/v1/payuni/health

# API 文檔
https://twshocks-app-79rsx.ondigitalocean.app/tradingagents-production-comple2/docs
```

## ⚠️ **常見錯誤**

### Method Not Allowed (405)
```json
{"detail":"Method Not Allowed"}
```

**原因**: 使用了錯誤的 HTTP 方法
- `/api/user/` 需要具體端點，如 `/api/user/info`
- `/admin/` 需要具體端點，如 `/admin/config`

### Not Found (404)
```json
{"detail":"Not Found"}
```

**原因**: 
1. 忘記了子路徑 `/tradingagents-production-comple2`
2. 端點路徑不正確

## 🔧 **前端配置更新**

更新前端配置檔案中的 API 基本 URL：

```javascript
// 正確配置
const API_BASE_URL = "https://twshocks-app-79rsx.ondigitalocean.app/tradingagents-production-comple2";

// API 調用範例
fetch(`${API_BASE_URL}/health`)
fetch(`${API_BASE_URL}/api/v1/payuni/health`)
```

---

**更新時間**: 2025-09-06  
**系統狀態**: ✅ 完全運行中
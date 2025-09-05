# 🚨 TradingAgents 緊急回滾指南

**緊急聯絡**: 系統管理員  
**最後更新**: 2025-09-05  
**適用版本**: v2.0 Complete Production  

---

## ⚡ **緊急情況識別**

### 🔴 **立即回滾情況**
- PayUni 支付系統完全無法使用
- API 全面無回應 (>5分鐘)
- 資料庫連接完全中斷
- 安全漏洞被發現並已被利用

### 🟡 **考慮回滾情況**
- 部分 API 端點異常
- 前端無法連接後端
- 監控系統異常
- 性能嚴重下降 (>50%)

---

## 🔄 **快速回滾步驟**

### 方案 A: DigitalOcean 版本回滾 (5分鐘)

#### 步驟 1: 訪問 DigitalOcean 控制台
```bash
1. 登入 https://cloud.digitalocean.com/
2. 進入 Apps > tradingagents-production
3. 點擊 "Deployments" 標籤
```

#### 步驟 2: 選擇穩定版本
```bash
1. 查看部署歷史列表
2. 選擇最後一個 "Successful" 部署
3. 點擊該版本的 "Actions" 按鈕
4. 選擇 "Redeploy"
```

#### 步驟 3: 確認回滾
```bash
1. 確認回滾操作
2. 等待部署完成 (約2-3分鐘)
3. 檢查 API 健康狀態: /health
4. 測試 PayUni 端點: /api/v1/payuni/health
```

### 方案 B: GitHub 代碼回滾 (10分鐘)

#### 步驟 1: 回滾 Git 代碼
```bash
# 在本地 TradingAgents-Production-Complete 目錄
git log --oneline  # 查看提交歷史
git revert HEAD    # 回滾最新提交
# 或
git reset --hard HEAD~1  # 強制回滾到前一版本

git push origin main --force  # 強制推送
```

#### 步驟 2: 觸發重新部署
```bash
# DigitalOcean 會自動檢測到 Git 變更並重新部署
# 或手動觸發：Apps > tradingagents-production > "Force Rebuild"
```

---

## 🏥 **服務狀態檢查**

### 快速健康檢查腳本
```bash
# 在部署目錄執行
python verify_deployment.py --url https://your-app-domain.ondigitalocean.app
```

### 關鍵端點檢查
```bash
# API 健康
curl https://your-app-domain.ondigitalocean.app/health

# PayUni 系統
curl https://your-app-domain.ondigitalocean.app/api/v1/payuni/health

# 資料庫連接
curl https://your-app-domain.ondigitalocean.app/admin/health
```

---

## 🔍 **故障診斷**

### DigitalOcean 日誌檢查
```bash
1. 進入 Apps > tradingagents-production
2. 點擊 "Runtime Logs" 標籤
3. 查看最近的錯誤消息
4. 檢查 "Build Logs" 是否有建構錯誤
```

### 常見錯誤模式
```bash
# 資料庫連接錯誤
ERROR: could not connect to server
SOLUTION: 檢查 DATABASE_URL 環境變數

# PayUni 配置錯誤  
ERROR: Invalid merchant configuration
SOLUTION: 檢查 PAYUNI_* 環境變數

# 依賴安裝錯誤
ERROR: Could not find a version that satisfies
SOLUTION: 檢查 requirements.txt 或使用 Docker

# 端口綁定錯誤
ERROR: Address already in use
SOLUTION: 確認 PORT 環境變數設為 8000
```

---

## 📞 **緊急聯絡程序**

### 1. 技術團隊通知
```bash
# 立即通知
Subject: [URGENT] TradingAgents Production Issue - Rollback Required
Body: 
- Issue: [描述問題]
- Impact: [影響範圍]
- Action Taken: [已採取的行動]
- ETA: [預估恢復時間]
```

### 2. 業務團隊通知
```bash
# PayUni 支付問題
Subject: [URGENT] Payment System Issue - Immediate Action Required
Body:
- Payment processing may be affected
- Customer transactions may be impacted
- Alternative payment methods: [如果有的話]
- ETA for resolution: [預估時間]
```

### 3. 用戶通知 (如需要)
```bash
# 如果影響用戶體驗
Subject: Temporary Service Disruption
Body:
- We are experiencing technical difficulties
- Our team is working to resolve the issue
- Expected resolution: [時間]
- We apologize for any inconvenience
```

---

## 📋 **回滾後驗證清單**

### ✅ **系統功能驗證**
- [ ] API 健康檢查通過
- [ ] PayUni 支付系統正常
- [ ] 資料庫連接正常
- [ ] 前端頁面可正常載入
- [ ] 用戶認證功能正常

### ✅ **業務功能驗證**
- [ ] 用戶註冊/登入正常
- [ ] 支付流程完整測試
- [ ] AI 分析功能可用
- [ ] 管理後台可訪問

### ✅ **監控恢復**
- [ ] 監控警報恢復正常
- [ ] 日誌系統正常記錄
- [ ] 性能指標回到正常範圍

---

## 🔒 **安全考慮**

### 數據完整性檢查
```bash
# 檢查關鍵數據表
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM payments; 
SELECT COUNT(*) FROM payment_transactions;

# 檢查最近的交易
SELECT * FROM payments ORDER BY created_at DESC LIMIT 10;
```

### 訪問日誌檢查
```bash
# 檢查是否有異常訪問
grep "ERROR" logs/tradingagents.log | tail -20
grep "Failed login" logs/tradingagents.log | tail -20
```

---

## 📈 **預防措施**

### 未來部署改進
1. **漸進式部署**: 考慮藍綠部署或金絲雀發布
2. **更多監控**: 設置更細粒度的監控警報
3. **自動回滾**: 配置自動故障檢測和回滾
4. **測試環境**: 建立與生產環境完全一致的測試環境

### 定期備份策略
```bash
# 資料庫備份 (每日)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 代碼備份 (Git tags)
git tag -a v2.0.1 -m "Production stable version"
git push origin v2.0.1
```

---

## 🔄 **恢復後步驟**

### 1. 問題分析
- 詳細記錄故障原因
- 分析影響範圍和持續時間
- 確定根本原因

### 2. 改進計劃
- 制定預防同類問題的措施
- 更新部署流程
- 加強監控和警報

### 3. 文檔更新
- 更新本回滾指南
- 更新故障排除文檔
- 分享經驗教訓

---

## 📞 **緊急聯絡資訊**

```bash
# 技術緊急聯絡
Tech Lead: [聯絡方式]
DevOps: [聯絡方式]
Database Admin: [聯絡方式]

# 業務緊急聯絡  
Product Manager: [聯絡方式]
Customer Support: [聯絡方式]

# 外部服務
DigitalOcean Support: https://cloud.digitalocean.com/support
PayUni Support: [聯絡方式]
```

---

**記住：在緊急情況下，用戶體驗和數據完整性是最高優先級！** 🚨
# GOOGLE清剿指令 - 部署說明
# 
# 依賴包營養補充完成後的部署步驟:
# 
# 1. 確認所有修復已提交到 Git:
git add requirements.txt requirements.lock.txt
git commit -m "fix: GOOGLE清剿指令 - 添加statsmodels依賴，完成營養補充

基於GOOGLE最終診斷分析:
- 添加 statsmodels==0.14.2 (深度行為學習系統)
- 生成完整依賴鎖定文件 requirements.lock.txt
- 驗證所有關鍵包可用性

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 2. 推送到 DigitalOcean 觸發自動部署:
git push origin main

# 3. 監控部署日誌，確認不再出現 'No module named statsmodels' 警告

# 4. 驗證系統健康:
curl https://twshocks-app-79rsx.ondigitalocean.app/health

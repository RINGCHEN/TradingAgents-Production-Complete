@echo off
echo 🚀 開始部署TTS管理前端到Firebase...

echo 📦 建構生產版本...
npm run build

echo 🔥 部署到Firebase Hosting...
firebase deploy --only hosting:twstock-admin-466914

echo ✅ 前端部署完成！
echo 🌐 管理後台URL: https://twstock-admin-466914.web.app/

echo 📋 接下來的步驟:
echo 1. 訪問管理後台
echo 2. 進入TTS語音管理模組
echo 3. 測試完整的CRUD功能

pause
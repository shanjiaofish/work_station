@echo off
echo 正在啟動 MaterialCorrectSystem NestJS 後端服務...
echo.

cd /d "C:\Users\Tim\Desktop\python\practice\MaterialCorrectSystem\backend"

echo 檢查依賴項...
if not exist "node_modules" (
    echo 安裝依賴項...
    npm install
)

echo.
echo 啟動開發服務器 (port 3000)...
echo 請保持此視窗開啟，服務將在背景運行
echo.
echo 按 Ctrl+C 可停止服務
echo.

npm run start:dev

pause

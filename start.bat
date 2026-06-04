@echo off
echo ========================================
echo   ShortLink - 构建前端并启动后端
echo ========================================
echo.

echo [1/3] 安装前端依赖...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [2/3] 构建前端...
call npm run build
if %errorlevel% neq 0 (
    echo 前端构建失败！
    pause
    exit /b 1
)

cd ..

echo.
echo [3/3] 启动后端服务...
echo.
echo ========================================
echo   服务已启动！
echo   访问地址: http://127.0.0.1:8000
echo   API 文档: http://127.0.0.1:8000/docs
echo ========================================
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

@echo off
chcp 65001 >nul
echo ========================================
echo   数字人直播系统 - 启动
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
if not exist ".venv" (
    echo [1/3] 创建虚拟环境...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [2/3] 安装依赖...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo [3/3] 启动系统...
echo.
python main.py -i %*
pause

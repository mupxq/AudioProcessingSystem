@echo off
chcp 65001 > nul
echo ==================================
echo Fun-ASR 语音识别批量处理系统
echo ==================================
echo.

REM 检查 Python 是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
python -c "import flask" > nul 2>&1
if errorlevel 1 (
    echo 依赖未安装，正在安装...
    pip install -r requirements.txt
)

REM 创建必要的目录
if not exist models mkdir models
if not exist outputs mkdir outputs

echo.
echo 启动服务器...
echo.

REM 启动应用
python backend\app.py

pause

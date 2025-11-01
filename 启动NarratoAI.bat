@echo off
chcp 65001 >nul
title NarratoAI 自动剪辑软件 - 启动中...

echo ============================================
echo    NarratoAI 自动剪辑软件 v0.7.4
echo ============================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python环境！
    echo 请先安装Python 3.12+ 并确保已添加到系统PATH
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist "venv" (
    echo [信息] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败！
        echo 请检查Python安装是否正确
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查依赖是否安装
if not exist "venv\Lib\site-packages\streamlit" (
    echo [信息] 首次运行，正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败！
        echo 请检查网络连接或手动安装依赖
        pause
        exit /b 1
    )
)

:: 检查配置文件
if not exist "config.toml" (
    echo [信息] 复制配置文件...
    copy config.example.toml config.toml >nul
)

echo [信息] 启动NarratoAI Web界面...
echo 应用启动后，请在浏览器中访问：http://localhost:8501
echo 按 Ctrl+C 可停止服务
echo.

:: 启动应用
echo [信息] 正在启动NarratoAI应用...
echo 访问地址: http://localhost:8501
echo.
streamlit run webui.py --server.maxUploadSize=2048

pause
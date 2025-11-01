@echo off
chcp 65001 >nul
title NarratoAI 环境检测

echo ============================================
echo    NarratoAI 环境检测工具
echo ============================================
echo.

:: 检查Python
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python环境
    echo   请安装Python 3.12+ 并添加到PATH
) else (
    python -c "import sys; print('✅ Python版本:', sys.version.split()[0])"
)

:: 检查FFmpeg
echo.
echo [2/4] 检查FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 未检测到FFmpeg（视频处理功能可能受限）
    echo   建议安装FFmpeg以获得更好的性能
) else (
    echo ✅ FFmpeg已安装
)

:: 检查虚拟环境
echo.
echo [3/4] 检查虚拟环境...
if exist "venv" (
    echo ✅ 虚拟环境已创建
) else (
    echo ⚠️ 虚拟环境未创建，首次运行时会自动创建
)

:: 检查依赖
echo.
echo [4/4] 检查依赖包...
if exist "venv\Lib\site-packages\streamlit" (
    echo ✅ 依赖包已安装
) else (
    echo ⚠️ 依赖包未安装，首次运行时会自动安装
)

echo.
echo ============================================
echo 检测完成！请运行"启动NarratoAI.bat"启动应用
echo ============================================
pause
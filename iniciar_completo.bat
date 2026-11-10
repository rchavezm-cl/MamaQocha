@echo off
title Mama Qocha - Ecosistema Completo (Streamlit + Terminal Cocina PWA)
color 0B

echo ===============================================================================
echo        MAMA QOCHA - ARQUITECTURA DE CONTINUIDAD OPERATIVA Y FEFO
echo         1. Micro-API y Terminal Cocina PWA  : http://localhost:8000/cocina/
echo         2. Panel Central de Administracion  : http://localhost:8501
echo ===============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    color 0C
    echo [ERROR] No se encontro el entorno virtual en la carpeta .venv
    pause
    exit /b 1
)

echo [1/3] Iniciando Micro-API y Terminal de Cocina PWA (Puerto 8000)...
start "Mama Qocha - Micro-API Sync (Puerto 8000)" /min cmd /c ".venv\Scripts\python.exe api_sync.py"

timeout /t 2 /nobreak >nul

echo [2/3] Verificando puertos...
echo  - Micro-API y PWA : http://localhost:8000/cocina/
echo  - Panel Central   : http://localhost:8501

echo.
echo [3/3] Iniciando Panel Administrativo Streamlit (Puerto 8501)...
.venv\Scripts\streamlit.exe run app.py --server.port=8501 --server.headless=false --browser.gatherUsageStats=false

pause

@echo off
title Mama Qocha - Sistema de Trazabilidad y Control FEFO
color 0B

echo ===============================================================================
echo              MAMA QOCHA - SISTEMA DE CONTROL DE INVENTARIO Y FEFO
echo                         Demostracion Academica INACAP
echo ===============================================================================
echo.

:: Cambiar al directorio donde se encuentra este archivo .bat
cd /d "%~dp0"

:: Verificar que el entorno virtual exista
if not exist ".venv\Scripts\activate.bat" (
    color 0C
    echo [ERROR] No se encontro el entorno virtual en la carpeta .venv
    echo Por favor asegurese de tener configurado el entorno con Python.
    echo.
    pause
    exit /b 1
)

echo [1/3] Activando entorno virtual (.venv)...
call .venv\Scripts\activate.bat

echo [2/3] Verificando conexion a PostgreSQL (localhost:5432)...
.venv\Scripts\python.exe -c "import db; db.test_connection()" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0E
    echo [ADVERTENCIA] No se pudo verificar la conexion con PostgreSQL.
    echo Asegurese de que el servicio de PostgreSQL este iniciado en el puerto 5432.
    echo Continuando con la apertura de Streamlit de todos modos...
    echo.
) else (
    echo [OK] Base de datos conectada correctamente.
)

echo [3/3] Iniciando servidor Streamlit...
echo.
echo ===============================================================================
echo  La aplicacion se abrira automaticamente en su navegador:
echo  URL Local: http://localhost:8501
echo  Para cerrar el servidor, presione Ctrl + C en esta ventana.
echo ===============================================================================
echo.

.venv\Scripts\streamlit.exe run app.py --server.port=8501 --server.headless=false --browser.gatherUsageStats=false

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [ERROR] Ocurrio un error al ejecutar la aplicacion.
    pause
)

@echo off
chcp 65001 > nul
echo ========================================================
echo   MAMA QOCHA - Recarga de Dataset Transaccional (1500)
echo ========================================================
echo.
echo Limpiando tablas operativas y cargando 1500 registros...
echo.

python generar_dataset_1500.py

echo.
echo ========================================================
echo Proceso finalizado. Presiona cualquier tecla para salir.
pause > nul

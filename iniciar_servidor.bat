@echo off
title Servidor Local RIS LLM
color 0A
echo ========================================================
echo   Iniciando Servidor Local RIS LLM para Google Chrome
echo   Escuchando peticiones en: http://127.0.0.1:5000
echo ========================================================
echo.

cd /d "%~dp0"
python server.py

echo.
echo Servidor detenido. Presiona cualquier tecla para salir...
pause > nul

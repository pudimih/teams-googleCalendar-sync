@echo off
chcp 65001 >nul
title Sincronizador Teams - Google Agenda
echo ============================================================
echo    Teams -> Google Agenda (Sincronizador Academico)
echo ============================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
) else (
    wsl.exe bash -c "cd \"$(wslpath '%~dp0')\" && .venv/bin/python main.py"
)

echo.
pause

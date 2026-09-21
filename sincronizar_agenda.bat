@echo off
chcp 65001 >nul
title Sincronizador Teams - Google Agenda
echo ============================================================
echo    Teams -^> Google Agenda (Sincronizador Academico)
echo ============================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" goto RUN_WINDOWS
goto RUN_WSL

:RUN_WINDOWS
echo [INFO] Executando no ambiente Windows...
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
goto END

:RUN_WSL
where wsl.exe >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRO] O comando wsl.exe nao foi encontrado no Windows.
    goto END
)

set "DIR_PATH=%~dp0"
set "DIR_PATH=%DIR_PATH:\=/%"
for /f "usebackq delims=" %%i in (`wsl.exe wslpath -u "%DIR_PATH%" 2^>nul`) do set "WSL_DIR=%%i"

if "%WSL_DIR%"=="" set "WSL_DIR=/home/millene/teams-google-calendar"

wsl.exe --cd "%WSL_DIR%" bash -c "if [ -f .venv/bin/python ]; then .venv/bin/python main.py; else python3 main.py; fi"
goto END

:END
echo.
pause


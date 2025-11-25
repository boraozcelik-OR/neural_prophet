@echo off
setlocal ENABLEDELAYEDEXPANSION

rem ============================================================================
rem Prophet Labs Windows menu runner
rem - Works from a fresh Windows checkout/extract (no prior setup required)
rem - Presents options to install deps, bootstrap .env, and start API/UI dev servers
rem - Gracefully handles missing tools (Python/PowerShell/npm) and logs actions
rem ============================================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%
set FRONTEND_DIR=%PROJECT_ROOT%frontend\prophet-labs-console
set INSTALL_PS=%PROJECT_ROOT%ops\shell\install_deps_windows.ps1
set BOOTSTRAP_MODULE=ops.bootstrap
set LOG_DIR=%PROJECT_ROOT%logs

set DEFAULT_ENV=dev
set DEFAULT_HOST=0.0.0.0
set DEFAULT_API_PORT=8000
set DEFAULT_UI_PORT=3000

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

call :find_powershell
call :find_python
call :find_npm

:menu
cls
set CHOICE=
echo =============================================================
echo      Prophet Labs - Windows Control Menu
echo =============================================================
echo  Detected tools:
echo    PowerShell: %POWERSHELL_EXE%
echo    Python    : %PYTHON_EXE%
echo    npm       : %NPM_EXE%
echo -------------------------------------------------------------
echo 1^) Install dependencies (PowerShell helper)
echo 2^) Bootstrap environment (.env)
echo 3^) Start API server (uvicorn)
echo 4^) Start UI dev server (npm)
echo 5^) Start API + UI
echo Q^) Quit
set /p CHOICE="Select option: "
if /I "%CHOICE%"=="1" goto install
if /I "%CHOICE%"=="2" goto bootstrap
if /I "%CHOICE%"=="3" goto start_api
if /I "%CHOICE%"=="4" goto start_ui
if /I "%CHOICE%"=="5" goto start_both
if /I "%CHOICE%"=="Q" goto end
if /I "%CHOICE%"=="" goto menu
echo Invalid choice. Try again.
timeout /t 1 >nul
goto menu

:install
echo.
if "%POWERSHELL_EXE%"=="" (
    echo [runner] PowerShell not found. Install PowerShell 5+ and retry.
    pause
    goto menu
)
if not exist "%INSTALL_PS%" (
    echo [runner] Installer script not found at %INSTALL_PS%
    pause
    goto menu
)
echo [runner] Running dependency installer ...
"%POWERSHELL_EXE%" -ExecutionPolicy Bypass -File "%INSTALL_PS%"
if errorlevel 1 (
    echo [runner] Install reported an error. Check logs for details.
) else (
    echo [runner] Install completed.
)
pause
goto menu

:bootstrap
echo.
if "%PYTHON_EXE%"=="" (
    echo [runner] Python not found. Install Python 3.9+ and retry.
    pause
    goto menu
)
set ENVIRONMENT=
set HOST=
set API_PORT=
set UI_PORT=
set /p ENVIRONMENT="Environment [default %DEFAULT_ENV%]: "
if "%ENVIRONMENT%"=="" set ENVIRONMENT=%DEFAULT_ENV%
set /p HOST="Bind host [default %DEFAULT_HOST%]: "
if "%HOST%"=="" set HOST=%DEFAULT_HOST%
set /p API_PORT="API port [default %DEFAULT_API_PORT%]: "
if "%API_PORT%"=="" set API_PORT=%DEFAULT_API_PORT%
set /p UI_PORT="UI port [default %DEFAULT_UI_PORT%]: "
if "%UI_PORT%"=="" set UI_PORT=%DEFAULT_UI_PORT%

echo [runner] Bootstrapping environment ...
"%PYTHON_EXE%" -m %BOOTSTRAP_MODULE% --yes --environment %ENVIRONMENT% --api-port %API_PORT% --frontend-port %UI_PORT% --host %HOST%
if errorlevel 1 (
    echo [runner] Bootstrap failed. Check logs for details.
) else (
    echo [runner] Bootstrap complete.
)
pause
goto menu

:start_api
echo.
if "%PYTHON_EXE%"=="" (
    echo [runner] Python not found. Install Python 3.9+ and retry.
    pause
    goto menu
)
set HOST=
set API_PORT=
set /p HOST="Bind host [default %DEFAULT_HOST%]: "
if "%HOST%"=="" set HOST=%DEFAULT_HOST%
set /p API_PORT="API port [default %DEFAULT_API_PORT%]: "
if "%API_PORT%"=="" set API_PORT=%DEFAULT_API_PORT%

echo [runner] Starting API server on %HOST%:%API_PORT% ...
start "ProphetLabs-API" "%PYTHON_EXE%" -m uvicorn prophet_labs.ui.api:app --host %HOST% --port %API_PORT%
echo [runner] API server launched. Press any key to return to menu.
pause
goto menu

:start_ui
echo.
if "%NPM_EXE%"=="" (
    echo [runner] npm not found. Install Node.js LTS to start the UI.
    pause
    goto menu
)
if not exist "%FRONTEND_DIR%" (
    echo [runner] Frontend directory not found at %FRONTEND_DIR%
    pause
    goto menu
)
set UI_PORT=
set /p UI_PORT="UI port [default %DEFAULT_UI_PORT%]: "
if "%UI_PORT%"=="" set UI_PORT=%DEFAULT_UI_PORT%

echo [runner] Starting UI dev server on 0.0.0.0:%UI_PORT% ...
start "ProphetLabs-UI" %NPM_EXE% --prefix "%FRONTEND_DIR%" run dev -- --host --port %UI_PORT%
echo [runner] UI server launched. Press any key to return to menu.
pause
goto menu

:start_both
echo.
if "%PYTHON_EXE%"=="" (
    echo [runner] Python not found. Install Python 3.9+ and retry.
    pause
    goto menu
)
if "%NPM_EXE%"=="" (
    echo [runner] npm not found. The API will start; UI will be skipped.
)
set HOST=
set API_PORT=
set UI_PORT=
set /p HOST="Bind host [default %DEFAULT_HOST%]: "
if "%HOST%"=="" set HOST=%DEFAULT_HOST%
set /p API_PORT="API port [default %DEFAULT_API_PORT%]: "
if "%API_PORT%"=="" set API_PORT=%DEFAULT_API_PORT%
set /p UI_PORT="UI port [default %DEFAULT_UI_PORT%]: "
if "%UI_PORT%"=="" set UI_PORT=%DEFAULT_UI_PORT%

echo [runner] Starting API server on %HOST%:%API_PORT% ...
start "ProphetLabs-API" "%PYTHON_EXE%" -m uvicorn prophet_labs.ui.api:app --host %HOST% --port %API_PORT%
if not "%NPM_EXE%"=="" if exist "%FRONTEND_DIR%" (
    echo [runner] Starting UI dev server on 0.0.0.0:%UI_PORT% ...
    start "ProphetLabs-UI" %NPM_EXE% --prefix "%FRONTEND_DIR%" run dev -- --host --port %UI_PORT%
) else (
    echo [runner] UI start skipped (npm or frontend missing).
)
echo [runner] Services launched. Press any key to return to menu.
pause
goto menu

:find_powershell
set POWERSHELL_EXE=
for %%P in (powershell pwsh) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set POWERSHELL_EXE=%%P
        goto :eof
    )
)
exit /b 0

:find_python
set PYTHON_EXE=
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe
    goto :eof
)
where py >nul 2>&1
if not errorlevel 1 (
    for /f "usebackq" %%p in (`py -3 -c "import sys; print(sys.executable)" 2^>NUL`) do set PYTHON_EXE=%%p
    if not "%PYTHON_EXE%"=="" goto :eof
)
for %%P in (python.exe python) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        for /f "usebackq" %%p in (`%%P -c "import sys; print(sys.executable)" 2^>NUL`) do set PYTHON_EXE=%%p
        if not "%PYTHON_EXE%"=="" goto :eof
    )
)
exit /b 0

:find_npm
set NPM_EXE=
for %%N in (npm.cmd npm.exe npm) do (
    where %%N >nul 2>&1
    if not errorlevel 1 (
        set NPM_EXE=%%N
        goto :eof
    )
)
exit /b 0

:end
endlocal
exit /b 0

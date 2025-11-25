@echo off
setlocal ENABLEDELAYEDEXPANSION

rem Windows runner for Prophet Labs (LAN-only). Installs deps (optional), renders .env, and can start dev servers.
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set INSTALL_PS=%PROJECT_ROOT%\ops\shell\install_deps_windows.ps1
set BOOTSTRAP_MODULE=ops.bootstrap
set DEFAULT_API_PORT=8000
set DEFAULT_FRONTEND_PORT=3000
set DEFAULT_ENV=dev

set SKIP_INSTALL=false
set SKIP_BOOTSTRAP=false
set START_DEV=false
set API_PORT=%DEFAULT_API_PORT%
set FRONTEND_PORT=%DEFAULT_FRONTEND_PORT%
set ENVIRONMENT=%DEFAULT_ENV%

:parse
if "%1"=="" goto done_parse
if "%1"=="--skip-install" set SKIP_INSTALL=true& shift & goto parse
if "%1"=="--skip-bootstrap" set SKIP_BOOTSTRAP=true& shift & goto parse
if "%1"=="--dev" set START_DEV=true& shift & goto parse
if "%1"=="--api-port" set API_PORT=%2& shift & shift & goto parse
if "%1"=="--frontend-port" set FRONTEND_PORT=%2& shift & shift & goto parse
if "%1"=="--environment" set ENVIRONMENT=%2& shift & shift & goto parse
if "%1"=="--help" goto usage
shift
goto parse

:done_parse

if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"

echo [windows-runner] project root: %PROJECT_ROOT%
echo [windows-runner] install=%SKIP_INSTALL% bootstrap=%SKIP_BOOTSTRAP% dev=%START_DEV% env=%ENVIRONMENT% api=%API_PORT% ui=%FRONTEND_PORT%

set PYTHON=py -3
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" set PYTHON="%PROJECT_ROOT%\.venv\Scripts\python.exe"

if "%SKIP_INSTALL%"=="false" (
    if exist "%INSTALL_PS%" (
        echo [windows-runner] installing dependencies via PowerShell ...
        powershell -ExecutionPolicy Bypass -File "%INSTALL_PS%" || goto :fail
    ) else (
        echo [windows-runner] installer not found at %INSTALL_PS%, skipping.
    )
) else (
    echo [windows-runner] skipping install as requested.
)

if "%SKIP_BOOTSTRAP%"=="false" (
    echo [windows-runner] rendering .env via bootstrap ...
    %PYTHON% -m %BOOTSTRAP_MODULE% --yes --environment %ENVIRONMENT% --api-port %API_PORT% --frontend-port %FRONTEND_PORT% || goto :fail
) else (
    echo [windows-runner] skipping bootstrap as requested.
)

if "%START_DEV%"=="true" (
    echo [windows-runner] starting API and UI (ports %API_PORT% / %FRONTEND_PORT%) ...
    start "ProphetLabs-API" %PYTHON% -m uvicorn prophet_labs.ui.api:app --host 0.0.0.0 --port %API_PORT%
    start "ProphetLabs-UI" npm --prefix "%PROJECT_ROOT%\frontend\prophet-labs-console" run dev -- --host --port %FRONTEND_PORT%
    echo [windows-runner] processes launched; check console windows for output.
) else (
    echo [windows-runner] dev servers not started. Run manually if needed.
)

echo [windows-runner] complete.
exit /b 0

:usage
echo Usage: run_windows.bat [--skip-install] [--skip-bootstrap] [--dev] [--api-port N] [--frontend-port N] [--environment dev^|stage^|prod]
exit /b 0

:fail
echo [windows-runner] failure occurred. Inspect logs directory for details.
exit /b 1

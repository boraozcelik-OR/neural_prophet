@echo off
setlocal ENABLEDELAYEDEXPANSION

rem ============================================================================
rem Prophet Labs Windows runner
rem - Optional dependency install via PowerShell helper
rem - Bootstrap .env settings
rem - Start API (uvicorn) and UI (npm dev server) for LAN-friendly dev
rem This script avoids external network calls except for configured package installs.
rem ============================================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
set INSTALL_PS=%PROJECT_ROOT%\ops\shell\install_deps_windows.ps1
set FRONTEND_DIR=%PROJECT_ROOT%\frontend\prophet-labs-console
set BOOTSTRAP_MODULE=ops.bootstrap

set DEFAULT_API_PORT=8000
set DEFAULT_FRONTEND_PORT=3000
set DEFAULT_ENV=dev
set DEFAULT_HOST=0.0.0.0

set SKIP_INSTALL=false
set SKIP_BOOTSTRAP=false
set START_DEV=false
set API_PORT=%DEFAULT_API_PORT%
set FRONTEND_PORT=%DEFAULT_FRONTEND_PORT%
set ENVIRONMENT=%DEFAULT_ENV%
set HOST=%DEFAULT_HOST%

:parse_args
if "%~1"=="" goto done_parse
if /I "%~1"=="--skip-install" set SKIP_INSTALL=true& shift & goto parse_args
if /I "%~1"=="--skip-bootstrap" set SKIP_BOOTSTRAP=true& shift & goto parse_args
if /I "%~1"=="--dev" set START_DEV=true& shift & goto parse_args
if /I "%~1"=="--api-port" set API_PORT=%~2& shift & shift & goto parse_args
if /I "%~1"=="--frontend-port" set FRONTEND_PORT=%~2& shift & shift & goto parse_args
if /I "%~1"=="--environment" set ENVIRONMENT=%~2& shift & shift & goto parse_args
if /I "%~1"=="--host" set HOST=%~2& shift & shift & goto parse_args
if /I "%~1"=="--help" goto usage
shift
goto parse_args

done_parse:

if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs" >nul 2>&1

call :find_powershell
call :find_python
call :find_npm

set FRONTEND_OK=true
if "%NPM_EXE%"=="" (
    set FRONTEND_OK=false
    echo [windows-runner] npm not found in PATH. Frontend will not start.
)

set API_OK=true
if "%PYTHON_EXE%"=="" (
    set API_OK=false
    echo [windows-runner] Python not found. Install Python 3.9+ and retry.
)

echo [windows-runner] project root: %PROJECT_ROOT%
echo [windows-runner] install=%SKIP_INSTALL% bootstrap=%SKIP_BOOTSTRAP% dev=%START_DEV% env=%ENVIRONMENT% api=%API_PORT% ui=%FRONTEND_PORT% host=%HOST%

after_install:
if "%SKIP_INSTALL%"=="false" (
    if exist "%INSTALL_PS%" (
        if "%POWERSHELL_EXE%"=="" (
            echo [windows-runner] PowerShell not available; cannot install dependencies.
            goto maybe_bootstrap
        )
        echo [windows-runner] running dependency installer ...
        "%POWERSHELL_EXE%" -ExecutionPolicy Bypass -File "%INSTALL_PS%"
        if errorlevel 1 goto fail
    ) else (
        echo [windows-runner] installer not found at %INSTALL_PS%; skipping install.
    )
) else (
    echo [windows-runner] skipping install as requested.
)

maybe_bootstrap:
if "%SKIP_BOOTSTRAP%"=="false" (
    if "%API_OK%"=="false" goto fail
    echo [windows-runner] rendering .env via bootstrap ...
    "%PYTHON_EXE%" -m %BOOTSTRAP_MODULE% --yes --environment %ENVIRONMENT% --api-port %API_PORT% --frontend-port %FRONTEND_PORT% --host %HOST%
    if errorlevel 1 goto fail
) else (
    echo [windows-runner] skipping bootstrap as requested.
)

if "%START_DEV%"=="true" (
    if "%API_OK%"=="false" goto fail
    echo [windows-runner] starting API on %HOST%:%API_PORT% ...
    start "ProphetLabs-API" "%PYTHON_EXE%" -m uvicorn prophet_labs.ui.api:app --host %HOST% --port %API_PORT%
    if "%FRONTEND_OK%"=="true" (
        echo [windows-runner] starting UI dev server on %HOST%:%FRONTEND_PORT% ...
        start "ProphetLabs-UI" %NPM_EXE% --prefix "%FRONTEND_DIR%" run dev -- --host --port %FRONTEND_PORT%
    ) else (
        echo [windows-runner] skipping UI start; npm missing.
    )
    echo [windows-runner] services launched; check spawned windows for output.
) else (
    echo [windows-runner] dev servers not started. Use --dev to launch.
)

echo [windows-runner] complete.
exit /b 0

:find_powershell
set POWERSHELL_EXE=
for %%P in (powershell pwsh) do (
    where %%P >nul 2>&1
    if not errorlevel 1 (
        set POWERSHELL_EXE=%%P
        goto :find_powershell_end
    )
)
:find_powershell_end
exit /b 0

:find_python
set PYTHON_EXE=
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe
    goto :find_python_end
)
where py >nul 2>&1
if not errorlevel 1 (
    for /f "usebackq" %%p in (`py -3 -c "import sys; print(sys.executable)" 2^>NUL`) do set PYTHON_EXE=%%p
    if not "%PYTHON_EXE%"=="" goto :find_python_end
)
where python >nul 2>&1
if not errorlevel 1 (
    for /f "usebackq" %%p in (`python -c "import sys; print(sys.executable)" 2^>NUL`) do set PYTHON_EXE=%%p
)
:find_python_end
exit /b 0

:find_npm
set NPM_EXE=
where npm >nul 2>&1
if not errorlevel 1 set NPM_EXE=npm
:find_npm_end
exit /b 0

:usage
echo Usage: run_windows.bat [--skip-install] [--skip-bootstrap] [--dev]^
      [--api-port N] [--frontend-port N] [--environment dev^|stage^|prod] [--host HOST]
echo The script will install deps (optional), bootstrap .env, and optionally start API/UI.
exit /b 0

:fail
echo [windows-runner] failure occurred. Inspect logs directory for details.
exit /b 1

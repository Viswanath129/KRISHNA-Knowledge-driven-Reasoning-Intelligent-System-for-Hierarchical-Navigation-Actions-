@echo off
echo ============================================
echo   KRISHNA AI Ethics Agent - Startup Script
echo   LLM Mode: Google Antigravity (agy CLI)
echo ============================================
echo.

REM Step 1: Verify agy CLI is present
echo [1/2] Verifying agy CLI integration...
set AGY_FOUND=0

if exist "%USERPROFILE%\AppData\Local\agy\bin\agy_core.exe" (
    echo [Antigravity] Found agy_core.exe at global AppData path.
    set AGY_FOUND=1
) else (
    where agy_core.exe >nul 2>nul
    if %ERRORLEVEL%==0 (
        echo [Antigravity] Found agy_core.exe in system PATH.
        set AGY_FOUND=1
    ) else (
        where agy >nul 2>nul
        if %ERRORLEVEL%==0 (
            echo [Antigravity] Found agy in system PATH.
            set AGY_FOUND=1
        )
    )
)

if "%AGY_FOUND%"=="0" (
    echo [WARNING] agy CLI was not found at standard paths or in system PATH.
    echo Make sure Google Antigravity is installed and accessible.
) else (
    echo [Antigravity] Integration verified. Using agy as LLM backend.
)
echo.

REM Step 2: Start KRISHNA agent web server
echo [2/2] Starting KRISHNA Ethics Agent on http://127.0.0.1:8000 ...
echo.
.venv\Scripts\python.exe api.py

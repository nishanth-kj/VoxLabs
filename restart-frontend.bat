@echo off
echo ========================================
echo   Stopping Port 3000 and Starting VoxLabs
echo ========================================
echo.

echo Finding process on port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    echo Found PID: %%a
    echo Attempting to stop...
    taskkill /F /PID %%a 2>nul
    if errorlevel 1 (
        echo Could not stop process %%a automatically
        echo Please stop it manually with Ctrl+C
    ) else (
        echo Process stopped successfully
    )
)

echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo.
echo Starting VoxLabs frontend on port 3000...
cd frontend
start cmd /k "npm run dev"

echo.
echo ========================================
echo   VoxLabs should start on port 3000
echo ========================================
echo.
pause

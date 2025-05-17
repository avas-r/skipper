@echo off
REM Windows Agent Communication Test Script
REM This batch file helps test agent-server communication on Windows

echo =========================================
echo Windows Agent Communication Test
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set test parameters
set SERVER_URL=http://localhost:8000
set TENANT_ID=test-tenant

echo Test Configuration:
echo - Server URL: %SERVER_URL%
echo - Tenant ID: %TENANT_ID%
echo.

REM Create menu
:MENU
echo Select test option:
echo 1. Start mock server
echo 2. Register Windows agent
echo 3. Run agent (normal mode)
echo 4. Run agent (headless mode)
echo 5. Test full communication cycle
echo 6. Exit
echo.
set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto START_SERVER
if "%choice%"=="2" goto REGISTER_AGENT
if "%choice%"=="3" goto RUN_AGENT
if "%choice%"=="4" goto RUN_HEADLESS
if "%choice%"=="5" goto FULL_TEST
if "%choice%"=="6" goto END

echo Invalid choice. Please try again.
goto MENU

:START_SERVER
echo.
echo Starting mock server...
start /b cmd /c "python simple_mock_server.py"
echo Mock server started in background
echo Check http://localhost:8000/docs for API documentation
echo.
pause
goto MENU

:REGISTER_AGENT
echo.
echo Registering Windows agent...
python windows_agent_fix.py %SERVER_URL% %TENANT_ID%
echo.
pause
goto MENU

:RUN_AGENT
echo.
echo Running agent in normal mode...
python run_agent.py --server %SERVER_URL% --tenant %TENANT_ID%
echo.
pause
goto MENU

:RUN_HEADLESS
echo.
echo Running agent in headless mode...
python run_agent.py --server %SERVER_URL% --tenant %TENANT_ID% --headless
echo.
pause
goto MENU

:FULL_TEST
echo.
echo Running full communication test...
echo.

REM Start mock server
echo Step 1: Starting mock server...
start /b cmd /c "python simple_mock_server.py"
timeout /t 3 /nobreak >nul

REM Register agent
echo Step 2: Registering agent...
python windows_agent_fix.py %SERVER_URL% %TENANT_ID%
timeout /t 2 /nobreak >nul

REM Run agent for 30 seconds
echo Step 3: Running agent for 30 seconds...
start /b cmd /c "python run_agent.py --server %SERVER_URL% --tenant %TENANT_ID% --headless"
timeout /t 30 /nobreak >nul

echo.
echo Test completed. Check agent.log for details.
echo.
pause
goto MENU

:END
echo.
echo Exiting test script...
taskkill /f /im python.exe >nul 2>&1
exit /b 0
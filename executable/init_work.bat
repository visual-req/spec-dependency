@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set WORK_DIR=work
mkdir "%WORK_DIR%\input" 2>nul
mkdir "%WORK_DIR%\input\req" 2>nul
mkdir "%WORK_DIR%\input\dependencies" 2>nul
mkdir "%WORK_DIR%\output" 2>nul
mkdir "%WORK_DIR%\logs" 2>nul
mkdir "%WORK_DIR%\uploads" 2>nul

echo Work directories are ready:
echo   %CD%\%WORK_DIR%\input
echo   %CD%\%WORK_DIR%\input\req
echo   %CD%\%WORK_DIR%\input\dependencies
echo   %CD%\%WORK_DIR%\output
echo   %CD%\%WORK_DIR%\logs
echo   %CD%\%WORK_DIR%\uploads
endlocal

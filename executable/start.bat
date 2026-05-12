@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if exist "%SCRIPT_DIR%spec_dep.exe" (
  "%SCRIPT_DIR%spec_dep.exe" %*
  exit /b %errorlevel%
)

echo [ERROR] spec_dep.exe not found under executable/. Please use the packaged binary distribution.
exit /b 1
endlocal

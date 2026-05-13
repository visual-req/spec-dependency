@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

rem Prefer native exe if present
if exist "%SCRIPT_DIR%spec_dep.exe" (
  "%SCRIPT_DIR%spec_dep.exe" %*
  exit /b %errorlevel%
)

rem Portable "jar-like" mode: embedded python + zipapp (.pyz)
if exist "%SCRIPT_DIR%python\python.exe" (
  if exist "%SCRIPT_DIR%spec_dep.pyz" (
    set SPEC_DEP_CONFIG=%SCRIPT_DIR%config.yaml
    set SPEC_DEP_WORK_DIR=%SCRIPT_DIR%work
    "%SCRIPT_DIR%python\python.exe" "%SCRIPT_DIR%spec_dep.pyz" %*
    exit /b %errorlevel%
  )
)

echo [ERROR] No runnable package found.
echo - expected one of:
echo   - %SCRIPT_DIR%spec_dep.exe
echo   - %SCRIPT_DIR%python\python.exe + %SCRIPT_DIR%spec_dep.pyz
exit /b 1
endlocal

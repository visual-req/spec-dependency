@echo off
setlocal enabledelayedexpansion

REM Usage:
REM   executable\package.bat windows-portable

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo usage: package.bat ^<target^>
  echo targets:
  echo   windows-portable
  exit /b 2
)

if /i not "%TARGET%"=="windows-portable" (
  echo unknown target: %TARGET%
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

if not exist "%ROOT_DIR%\backend\requirements.txt" (
  echo invalid repo layout: %ROOT_DIR%\backend\requirements.txt not found
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo python not found in PATH. Install Python on the packaging machine first.
  exit /b 1
)

REM Ensure frontend/dist exists (best-effort build if npm is available)
if not exist "%ROOT_DIR%\frontend\dist\index.html" (
  where npm >nul 2>nul
  if errorlevel 1 (
    echo frontend\dist not found and npm not available. Please build frontend first:
    echo   cd frontend ^&^& npm install ^&^& npm run build
    exit /b 1
  )
  pushd "%ROOT_DIR%\frontend"
  call npm install --no-audit --no-fund
  if errorlevel 1 (popd & exit /b 1)
  call npm run build
  if errorlevel 1 (popd & exit /b 1)
  popd
)

set "BUILD_VENV=%ROOT_DIR%\backend\.zipapp_venv"
set "BUILD_DIR=%ROOT_DIR%\backend\.zipapp_build"
set "EMBED_VER=%PY_EMBED_VERSION%"
set "EMBED_ARCH=%PY_EMBED_ARCH%"

if "%EMBED_VER%"=="" set "EMBED_VER=3.11.9"
if "%EMBED_ARCH%"=="" set "EMBED_ARCH=amd64"

if not exist "%BUILD_VENV%\Scripts\python.exe" (
  python -m venv "%BUILD_VENV%"
  if errorlevel 1 exit /b 1
)

set "BUILD_PY=%BUILD_VENV%\Scripts\python.exe"

REM Prepare build directory
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
if errorlevel 1 exit /b 1

REM Install deps into build dir (vendor)
"%BUILD_PY%" -m pip install -U pip >nul 2>nul
"%BUILD_PY%" -m pip install --no-cache-dir -r "%ROOT_DIR%\backend\requirements.txt" -t "%BUILD_DIR%"
if errorlevel 1 exit /b 1

REM Copy app code
if exist "%BUILD_DIR%\app" rmdir /s /q "%BUILD_DIR%\app"
xcopy /E /I /Y "%ROOT_DIR%\backend\app" "%BUILD_DIR%\app" >nul
if errorlevel 1 exit /b 1

REM Build pyz
if exist "%SCRIPT_DIR%spec_dep.pyz" del /f /q "%SCRIPT_DIR%spec_dep.pyz"
"%BUILD_PY%" -m zipapp "%BUILD_DIR%" -m "app.cli.main:main" -o "%SCRIPT_DIR%spec_dep.pyz"
if errorlevel 1 exit /b 1

REM Copy frontend dist into executable package
if exist "%SCRIPT_DIR%frontend" rmdir /s /q "%SCRIPT_DIR%frontend"
mkdir "%SCRIPT_DIR%frontend"
xcopy /E /I /Y "%ROOT_DIR%\frontend\dist" "%SCRIPT_DIR%frontend\dist" >nul
if errorlevel 1 exit /b 1

REM Download and extract embeddable python
set "EMBED_ZIP=%ROOT_DIR%\backend\.python-embed-%EMBED_VER%-%EMBED_ARCH%.zip"
set "EMBED_URL=https://www.python.org/ftp/python/%EMBED_VER%/python-%EMBED_VER%-embed-%EMBED_ARCH%.zip"

if not exist "%EMBED_ZIP%" (
  "%BUILD_PY%" -c "import urllib.request,zipfile,os,sys; url=r'%EMBED_URL%'; out=r'%EMBED_ZIP%'; urllib.request.urlretrieve(url,out); ok=zipfile.is_zipfile(out); (ok and sys.exit(0)) or (print('downloaded file is not a zip:',url) or os.remove(out) or sys.exit(1))"
  if errorlevel 1 exit /b 1
)

if exist "%SCRIPT_DIR%python" rmdir /s /q "%SCRIPT_DIR%python"
mkdir "%SCRIPT_DIR%python"

"%BUILD_PY%" -c "import zipfile; from pathlib import Path; z=Path(r'%EMBED_ZIP%'); out=Path(r'%SCRIPT_DIR%')/'python'; out.mkdir(parents=True, exist_ok=True); zipfile.ZipFile(z,'r').extractall(out)"
if errorlevel 1 exit /b 1

echo built: %SCRIPT_DIR%spec_dep.pyz
echo built: %SCRIPT_DIR%python\python.exe
echo built: %SCRIPT_DIR%frontend\dist
exit /b 0


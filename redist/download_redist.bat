@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Telechargement des redistribuables Windows
echo  (Python 3.12 + VC++ + LibreOffice)
echo.

where curl >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] curl introuvable. Utilisez Windows 10/11 a jour.
  pause
  exit /b 1
)

set "PY_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
set "PY_FILE=python-3.12.10-amd64.exe"

set "VC_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe"
set "VC_FILE=VC_redist.x64.exe"

set "LO_VER=26.2.4"
set "LO_FILE=LibreOffice_%LO_VER%_Win_x86-64.msi"
set "LO_URL=https://download.documentfoundation.org/libreoffice/stable/%LO_VER%/win/x86_64/%LO_FILE%"

call :download "%PY_URL%" "%PY_FILE%"
call :download "%VC_URL%" "%VC_FILE%"
call :download "%LO_URL%" "%LO_FILE%"

echo.
echo Termine. Contenu de redist\:
dir /b *.exe *.msi 2>nul
echo.
echo Ensuite lancez install_redist.bat sur le PC cible.
pause
exit /b 0

:download
set "URL=%~1"
set "OUT=%~2"
if exist "%OUT%" (
  echo [OK] Deja present: %OUT%
  exit /b 0
)
echo.
echo Telechargement: %OUT%
echo   %URL%
curl -L --retry 3 --retry-delay 2 -o "%OUT%.partial" "%URL%"
if errorlevel 1 (
  echo [ERREUR] Echec: %OUT%
  del /f /q "%OUT%.partial" 2>nul
  exit /b 1
)
move /y "%OUT%.partial" "%OUT%" >nul
echo [OK] %OUT%
exit /b 0

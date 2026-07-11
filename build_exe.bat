@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Build EXE - Generateur de certificats
echo.

REM Prefer a stable Python for PyInstaller: 3.12 then 3.11
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY_CMD=py -3.12"
  if not defined PY_CMD (
    py -3.11 -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3.11"
  )
)

if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)" >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
  )
)

if not defined PY_CMD (
  echo [ERREUR] Python 3.11 ou 3.12 introuvable.
  echo.
  echo Votre commande "python" pointe probablement vers 3.14, incompatible avec PyInstaller.
  echo.
  echo Solution:
  echo   1) Installez Python 3.12 depuis:
  echo      https://www.python.org/downloads/release/python-31210/
  echo   2) Pendant l'install, cochez:
  echo      - Add python.exe to PATH
  echo      - Install launcher for all users  (py.exe)
  echo   3) Ouvrez un NOUVEAU cmd et verifiez:
  echo      py -3.12 --version
  echo   4) Relancez build_exe.bat
  echo.
  echo Ou utilisez l'installateur deja present:
  echo   redist\python-3.12.10-amd64.exe
  echo   puis: redist\install_redist.bat /with-python
  echo.
  pause
  exit /b 1
)

echo Python utilise pour le build: %PY_CMD%
%PY_CMD% --version
echo.

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)" >nul 2>nul
  if errorlevel 1 (
    echo [INFO] Ancien .venv incompatible - recreation avec %PY_CMD% ...
    rmdir /s /q .venv
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de .venv ...
  %PY_CMD% -m venv .venv
  if errorlevel 1 (
    echo [ERREUR] Impossible de creer .venv
    pause
    exit /b 1
  )
)

echo Installation des dependances + PyInstaller...
".venv\Scripts\python.exe" -m pip install -q -U pip
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt "pyinstaller>=6.3,<7"
if errorlevel 1 (
  echo [ERREUR] pip a echoue.
  pause
  exit /b 1
)

echo Regeneration des modeles Excel...
".venv\Scripts\python.exe" -c "from certificate_generator import write_bulk_excel_templates; write_bulk_excel_templates()"

echo.
echo Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist GenerateurCertificats.spec del /f /q GenerateurCertificats.spec

echo.
echo Construction de l'executable (dossier dist\GenerateurCertificats)...
echo Cela peut prendre plusieurs minutes.
echo.

".venv\Scripts\pyinstaller.exe" --noconfirm --clean --name GenerateurCertificats --onedir --windowed --add-data "certificate_ui.py;." --add-data "certificate_generator.py;." --add-data "requirements.txt;." --add-data ".streamlit;.streamlit" --add-data "assets;assets" --add-data "fonts;fonts" --add-data "certificates templates;certificates templates" --add-data "bulk_templates;bulk_templates" --hidden-import streamlit --hidden-import streamlit.web.cli --hidden-import streamlit.web.bootstrap --hidden-import streamlit.runtime.scriptrunner.magic_funcs --hidden-import webview --hidden-import docx --hidden-import docxtpl --hidden-import openpyxl --hidden-import fitz --hidden-import arabic_reshaper --hidden-import bidi --collect-all streamlit --collect-all altair --collect-all webview --collect-all docxtpl --collect-all arabic_reshaper run_desktop.py

if errorlevel 1 (
  echo.
  echo [ERREUR] Build PyInstaller echoue.
  pause
  exit /b 1
)

if not exist "dist\GenerateurCertificats\GenerateurCertificats.exe" (
  echo [ERREUR] EXE introuvable dans dist\GenerateurCertificats\
  pause
  exit /b 1
)

echo.
echo ============================================================
echo  OK
echo.
echo  Lancez UNIQUEMENT celui-ci:
echo    dist\GenerateurCertificats\GenerateurCertificats.exe
echo.
echo  NE PAS utiliser le dossier build\ - cache interne.
echo.
echo  Livraison:
echo    1) dist\GenerateurCertificats\
echo    2) redist\
echo ============================================================
echo.

explorer "dist\GenerateurCertificats"
pause

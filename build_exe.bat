@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Build EXE - Generateur de certificats
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python introuvable dans le PATH.
  echo Installez Python 3.11 ou 3.12 depuis https://www.python.org/downloads/
  echo Cochez "Add python.exe to PATH".
  pause
  exit /b 1
)

echo Python detecte:
python --version
echo.

REM PyInstaller is unreliable with very new Python (3.13/3.14). Prefer 3.11/3.12.
python -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)"
if errorlevel 1 (
  echo [ERREUR] Ce build exige Python 3.11 ou 3.12.
  echo Vous utilisez actuellement:
  python --version
  echo.
  echo Desinstallez Python 3.13/3.14 pour ce projet, ou installez 3.12 a cote:
  echo   https://www.python.org/downloads/release/python-31210/
  echo Puis recreez le venv:
  echo   rmdir /s /q .venv
  echo   py -3.12 -m venv .venv
  echo   puis relancez build_exe.bat
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)"
  if errorlevel 1 (
    echo [INFO] Ancien .venv incompatible — recreation avec le Python actuel...
    rmdir /s /q .venv
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de .venv ...
  python -m venv .venv
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

".venv\Scripts\pyinstaller.exe" --noconfirm --clean ^
  --name GenerateurCertificats ^
  --onedir ^
  --windowed ^
  --add-data "certificate_ui.py;." ^
  --add-data "certificate_generator.py;." ^
  --add-data "requirements.txt;." ^
  --add-data ".streamlit;.streamlit" ^
  --add-data "assets;assets" ^
  --add-data "fonts;fonts" ^
  --add-data "certificates templates;certificates templates" ^
  --add-data "bulk_templates;bulk_templates" ^
  --hidden-import streamlit ^
  --hidden-import streamlit.web.cli ^
  --hidden-import streamlit.web.bootstrap ^
  --hidden-import streamlit.runtime.scriptrunner.magic_funcs ^
  --hidden-import webview ^
  --hidden-import docx ^
  --hidden-import docxtpl ^
  --hidden-import openpyxl ^
  --hidden-import fitz ^
  --hidden-import arabic_reshaper ^
  --hidden-import bidi ^
  --collect-all streamlit ^
  --collect-all altair ^
  --collect-all webview ^
  --collect-all docxtpl ^
  --collect-all arabic_reshaper ^
  run_desktop.py

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
echo  NE PAS utiliser le dossier "build\" — c'est un cache interne.
echo.
echo  Livraison:
echo    1) dist\GenerateurCertificats\   (l'app)
echo    2) redist\                      (VC++ / LibreOffice / Python)
echo       - download_redist.bat  pour telecharger les installateurs
echo       - install_redist.bat   sur le PC cible (une fois)
echo.
echo  Si "Failed to load Python DLL":
echo    - rebuild avec Python 3.12
echo    - ou lancez redist\install_redist.bat (installe VC++)
echo ============================================================
echo.

explorer "dist\GenerateurCertificats"
pause

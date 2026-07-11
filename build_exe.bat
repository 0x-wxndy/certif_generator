@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Build EXE - Generateur de certificats
echo  (progression visible ici - ne fermez pas la fenetre)
echo.

set "PYTHON_EXE="

where py >nul 2>nul
if not errorlevel 1 (
  for /f "delims=" %%E in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%E"
)
if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 (
    for /f "delims=" %%E in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%E"
  )
)
if not defined PYTHON_EXE (
  for %%P in (
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
  ) do (
    if exist %%~P (
      set "PYTHON_EXE=%%~P"
      goto have_python
    )
  )
)
if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)" 2>nul
    if not errorlevel 1 (
      for /f "delims=" %%E in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%E"
    )
  )
)

:have_python
if not defined PYTHON_EXE (
  echo [ERREUR] Python 3.11 ou 3.12 introuvable.
  echo.
  echo Installez: redist\python-3.12.10-amd64.exe
  echo ou: redist\install_redist.bat /with-python
  echo.
  echo Puis OUVREZ UN NOUVEAU cmd et verifiez:  py -3.12 --version
  echo.
  pause
  exit /b 1
)

echo Python pour le build:
"%PYTHON_EXE%" --version
echo Path: %PYTHON_EXE%
echo.

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)" 2>nul
  if errorlevel 1 (
    echo [INFO] Ancien .venv incompatible - recreation...
    rmdir /s /q .venv
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de .venv ...
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 (
    echo [ERREUR] Impossible de creer .venv
    pause
    exit /b 1
  )
)

echo.
echo [1/4] Installation / mise a jour des dependances...
echo       (peut prendre plusieurs minutes la premiere fois)
".venv\Scripts\python.exe" -m pip install -U pip
if errorlevel 1 (
  echo [ERREUR] pip upgrade a echoue
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6.3,<7"
if errorlevel 1 (
  echo [ERREUR] pip install a echoue
  pause
  exit /b 1
)

echo.
echo [2/4] Regeneration des modeles Excel...
".venv\Scripts\python.exe" -c "from certificate_generator import write_bulk_excel_templates; print(write_bulk_excel_templates())"
if errorlevel 1 (
  echo [ERREUR] regeneration Excel a echoue
  pause
  exit /b 1
)

echo.
echo [3/4] Nettoyage des anciens builds...
echo       Fermeture de l'app si elle tourne encore...
taskkill /F /IM GenerateurCertificats.exe /T >nul 2>nul
taskkill /F /IM soffice.exe /T >nul 2>nul
taskkill /F /IM soffice.bin /T >nul 2>nul
timeout /t 2 /nobreak >nul

if exist build rmdir /s /q build 2>nul
if exist GenerateurCertificats.spec del /f /q GenerateurCertificats.spec 2>nul

if exist dist (
  rmdir /s /q dist 2>nul
  if exist dist (
    echo.
    echo [ERREUR] Impossible de supprimer dist\ — fichiers verrouilles.
    echo.
    echo 1. Fermez GenerateurCertificats.exe ^(toutes fenetres^)
    echo 2. Fermez l'Explorateur s'il est ouvert dans dist\
    echo 3. Dans le Gestionnaire des taches, tuez GenerateurCertificats.exe
    echo 4. Relancez build_exe.bat
    echo.
    pause
    exit /b 1
  )
)

echo.
echo [4/4] Construction PyInstaller...
echo       (plusieurs minutes - laissez tourner)
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --name GenerateurCertificats --onedir --windowed --add-data "certificate_ui.py;." --add-data "certificate_generator.py;." --add-data "requirements.txt;." --add-data ".streamlit;.streamlit" --add-data "assets;assets" --add-data "fonts;fonts" --add-data "certificates templates;certificates templates" --add-data "bulk_templates;bulk_templates" --hidden-import streamlit --hidden-import streamlit.web.cli --hidden-import streamlit.web.bootstrap --hidden-import streamlit.runtime.scriptrunner.magic_funcs --hidden-import webview --hidden-import clr --hidden-import clr_loader --hidden-import pythonnet --hidden-import docx --hidden-import docxtpl --hidden-import openpyxl --hidden-import fitz --hidden-import arabic_reshaper --hidden-import bidi --collect-all streamlit --collect-all altair --collect-all webview --collect-all pythonnet --collect-all clr_loader --collect-all docxtpl --collect-all arabic_reshaper run_desktop.py
if errorlevel 1 (
  echo.
  echo [ERREUR] PyInstaller a echoue
  echo.
  echo Si vous voyez "Access is denied" / MSVCP140.dll :
  echo   - Fermez GenerateurCertificats.exe
  echo   - Fermez toute fenetre Explorateur dans dist\
  echo   - Relancez build_exe.bat
  echo.
  pause
  exit /b 1
)

REM Clear Mark-of-the-Web on the fresh build (helps target PCs after copy).
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Get-ChildItem -LiteralPath 'dist\GenerateurCertificats' -Recurse -Include *.dll,*.exe -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue" >nul 2>nul

if not exist "dist\GenerateurCertificats\GenerateurCertificats.exe" (
  echo [ERREUR] EXE introuvable dans dist\GenerateurCertificats\
  pause
  exit /b 1
)

copy /Y "debloquer_dll.bat" "dist\GenerateurCertificats\debloquer_dll.bat" >nul 2>nul
copy /Y "LIREMOI_WINDOWS.txt" "dist\GenerateurCertificats\LIREMOI_WINDOWS.txt" >nul 2>nul

echo.
echo ============================================================
echo  OK
echo  Lancez: dist\GenerateurCertificats\GenerateurCertificats.exe
echo.
echo  Mode par defaut: NAVIGATEUR (fiable sur tous les PC).
echo  Sur un autre PC apres copie/ZIP:
echo    1) redist\install_redist.bat
echo    2) debloquer_dll.bat
echo    3) GenerateurCertificats.exe
echo ============================================================
echo.
explorer "dist\GenerateurCertificats"
pause
exit /b 0

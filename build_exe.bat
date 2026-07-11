@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "LOG=%~dp0build_exe_log.txt"
echo. > "%LOG%"

call :body >> "%LOG%" 2>&1
set "ERR=%ERRORLEVEL%"

echo.
echo ========== LOG build_exe =========
type "%LOG%"
echo ==================================
echo.
if not "%ERR%"=="0" (
  echo [ECHEC] Code erreur: %ERR%
  echo Ouvrez aussi: build_exe_log.txt
) else (
  echo [OK] Build termine.
)
echo.
pause
exit /b %ERR%


:body
echo Build EXE - Generateur de certificats
echo Dossier: %CD%
echo.

set "PYTHON_EXE="

REM 1) Windows py launcher
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 -c "import sys; print(sys.executable)" > "%TEMP%\cert_py312.txt" 2>nul
  if not errorlevel 1 (
    set /p PYTHON_EXE=<"%TEMP%\cert_py312.txt"
  )
)
if defined PYTHON_EXE goto have_python

where py >nul 2>nul
if not errorlevel 1 (
  py -3.11 -c "import sys; print(sys.executable)" > "%TEMP%\cert_py312.txt" 2>nul
  if not errorlevel 1 (
    set /p PYTHON_EXE=<"%TEMP%\cert_py312.txt"
  )
)
if defined PYTHON_EXE goto have_python

REM 2) Common install paths for Python 3.12 / 3.11
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

REM 3) Default python only if it is 3.11/3.12
where python >nul 2>nul
if not errorlevel 1 (
  for /f "delims=" %%V in ('python -c "import sys; print(sys.version)" 2^>nul') do echo python --version: %%V
  python -c "import sys; v=sys.version_info; raise SystemExit(0 if (v.major,v.minor) in {(3,11),(3,12)} else 1)" 2>nul
  if not errorlevel 1 (
    for /f "delims=" %%E in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%E"
  )
)
if defined PYTHON_EXE goto have_python

echo [ERREUR] Python 3.11 ou 3.12 introuvable.
echo.
echo "python" seul pointe souvent vers 3.14 (incompatible).
echo.
echo Installez Python 3.12:
echo   redist\python-3.12.10-amd64.exe
echo ou:
echo   redist\install_redist.bat /with-python
echo.
echo Cochez: Add to PATH + py launcher
echo Puis OUVREZ UN NOUVEAU cmd et verifiez:
echo   py -3.12 --version
echo.
exit /b 1

:have_python
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
    exit /b 1
  )
)

echo Installation des dependances + PyInstaller...
".venv\Scripts\python.exe" -m pip install -q -U pip
if errorlevel 1 (
  echo [ERREUR] pip upgrade a echoue
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt "pyinstaller>=6.3,<7"
if errorlevel 1 (
  echo [ERREUR] pip install a echoue
  exit /b 1
)

echo Regeneration des modeles Excel...
".venv\Scripts\python.exe" -c "from certificate_generator import write_bulk_excel_templates; write_bulk_excel_templates()"
if errorlevel 1 (
  echo [ERREUR] regeneration Excel a echoue
  exit /b 1
)

echo Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist GenerateurCertificats.spec del /f /q GenerateurCertificats.spec

echo Construction PyInstaller...
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --name GenerateurCertificats --onedir --windowed --add-data "certificate_ui.py;." --add-data "certificate_generator.py;." --add-data "requirements.txt;." --add-data ".streamlit;.streamlit" --add-data "assets;assets" --add-data "fonts;fonts" --add-data "certificates templates;certificates templates" --add-data "bulk_templates;bulk_templates" --hidden-import streamlit --hidden-import streamlit.web.cli --hidden-import streamlit.web.bootstrap --hidden-import streamlit.runtime.scriptrunner.magic_funcs --hidden-import webview --hidden-import docx --hidden-import docxtpl --hidden-import openpyxl --hidden-import fitz --hidden-import arabic_reshaper --hidden-import bidi --collect-all streamlit --collect-all altair --collect-all webview --collect-all docxtpl --collect-all arabic_reshaper run_desktop.py
if errorlevel 1 (
  echo [ERREUR] PyInstaller a echoue
  exit /b 1
)

if not exist "dist\GenerateurCertificats\GenerateurCertificats.exe" (
  echo [ERREUR] EXE introuvable dans dist\GenerateurCertificats\
  exit /b 1
)

echo.
echo OK - EXE:
echo   dist\GenerateurCertificats\GenerateurCertificats.exe
explorer "dist\GenerateurCertificats"
exit /b 0

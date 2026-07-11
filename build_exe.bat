@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Build EXE - Generateur de certificats
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python introuvable dans le PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de .venv ...
  python -m venv .venv
)

echo Installation des dependances + PyInstaller...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt pyinstaller
if errorlevel 1 (
  echo [ERREUR] pip a echoue.
  pause
  exit /b 1
)

echo Regeneration des modeles Excel...
".venv\Scripts\python.exe" -c "from certificate_generator import write_bulk_excel_templates; write_bulk_excel_templates()"

echo.
echo Construction de l'executable (dossier dist\GenerateurCertificats)...
echo Cela peut prendre plusieurs minutes.
echo.

".venv\Scripts\pyinstaller.exe" --noconfirm --clean ^
  --name GenerateurCertificats ^
  --onedir ^
  --console ^
  --add-data "certificate_ui.py;." ^
  --add-data "certificate_generator.py;." ^
  --add-data "requirements.txt;." ^
  --add-data ".streamlit;.streamlit" ^
  --add-data "assets;assets" ^
  --add-data "fonts;fonts" ^
  --add-data "certificates templates;certificates templates" ^
  --add-data "bulk_templates;bulk_templates" ^
  --hidden-import streamlit ^
  --hidden-import docx ^
  --hidden-import docxtpl ^
  --hidden-import openpyxl ^
  --hidden-import fitz ^
  --hidden-import arabic_reshaper ^
  --hidden-import bidi ^
  --collect-all streamlit ^
  --collect-all docxtpl ^
  --collect-all arabic_reshaper ^
  run_desktop.py

if errorlevel 1 (
  echo.
  echo [ERREUR] Build PyInstaller echoue.
  pause
  exit /b 1
)

echo.
echo OK - Executable:
echo   dist\GenerateurCertificats\GenerateurCertificats.exe
echo.
echo Note: LibreOffice doit rester installe sur le PC pour l'apercu / PDF.
echo.
pause

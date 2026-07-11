@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Generateur de certificats - Ministere de la Justice
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
  echo Installez Python 3.12 depuis https://www.python.org/downloads/
  echo Cochez "Add python.exe to PATH" lors de l'installation.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement virtuel...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERREUR] Impossible de creer .venv
    pause
    exit /b 1
  )
)

echo Installation / mise a jour des dependances...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 (
  echo [ERREUR] Echec de l'installation des paquets.
  pause
  exit /b 1
)

echo.
echo  Ouvrez http://localhost:8501 dans votre navigateur
echo  (LibreOffice doit etre installe pour l'apercu PDF)
echo.

".venv\Scripts\streamlit.exe" run certificate_ui.py --server.headless true --browser.gatherUsageStats false --server.port 8501
pause

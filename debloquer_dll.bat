@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Debloquer les DLL (Mark-of-the-Web)
echo  A lancer UNE FOIS apres copie/ZIP sur un nouveau PC.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-ChildItem -LiteralPath '%cd%' -Recurse -Include *.dll,*.exe -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue"

if errorlevel 1 (
  echo [ERREUR] Impossible de debloquer. Clic droit sur le ZIP/dossier:
  echo   Proprietes -^> case Debloquer -^> OK
  pause
  exit /b 1
)

echo OK - relancez GenerateurCertificats.exe
pause
exit /b 0

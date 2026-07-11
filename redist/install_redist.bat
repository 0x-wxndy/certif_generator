@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  Installation des dependances Windows
echo  Generateur de certificats - Ministere de la Justice
echo.
echo  Ce script installe:
echo    1) Visual C++ Redistributable (requis pour l'EXE)
echo    2) LibreOffice (requis pour PDF / apercu)
echo    3) Python 3.12  [OPTIONNEL - seulement pour rebuild]
echo.

net session >nul 2>&1
if errorlevel 1 (
  echo [INFO] Droits admin recommandes. Relancez en tant qu'administrateur si une etape echoue.
  echo.
)

if exist "VC_redist.x64.exe" (
  echo [1/3] Installation VC++ Redistributable...
  "VC_redist.x64.exe" /install /quiet /norestart
  if errorlevel 1 (
    echo [WARN] Installation silencieuse VC++ echouee - ouverture interactive...
    start /wait "" "VC_redist.x64.exe"
  ) else (
    echo [OK] VC++ installe.
  )
) else (
  echo [MANQUANT] VC_redist.x64.exe - lancez d'abord download_redist.bat
)

echo.

set "LO_MSI="
for %%F in (LibreOffice_*_Win_x86-64.msi) do set "LO_MSI=%%F"
if defined LO_MSI (
  if exist "%LO_MSI%" (
    echo [2/3] Installation LibreOffice (%LO_MSI%)...
    echo       Cela peut prendre plusieurs minutes.
    msiexec /i "%LO_MSI%" /passive ALLUSERS=1 CREATEDESKTOPLINK=0 REGISTER_ALL_MSO_TYPES=0
    if errorlevel 1 (
      echo [WARN] Installation passive echouee - ouverture interactive...
      start /wait msiexec /i "%LO_MSI%"
    ) else (
      echo [OK] LibreOffice installe.
    )
  )
) else (
  echo [MANQUANT] LibreOffice_*.msi - lancez d'abord download_redist.bat
)

echo.

if /I "%~1"=="/with-python" goto install_python
echo [3/3] Python 3.12 ignore (pas besoin pour les utilisateurs finaux).
echo       Pour l'installer quand meme:  install_redist.bat /with-python
goto done

:install_python
if exist "python-3.12.10-amd64.exe" (
  echo [3/3] Installation Python 3.12...
  "python-3.12.10-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
  if errorlevel 1 (
    echo [WARN] Installation silencieuse Python echouee - ouverture interactive...
    start /wait "" "python-3.12.10-amd64.exe"
  ) else (
    echo [OK] Python 3.12 installe.
  )
) else (
  echo [MANQUANT] python-3.12.10-amd64.exe
)

:done
echo.
echo ============================================================
echo  Termine.
echo  Vous pouvez maintenant lancer GenerateurCertificats.exe
echo ============================================================
pause

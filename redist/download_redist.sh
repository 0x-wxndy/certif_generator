#!/usr/bin/env bash
# Download Windows redistributables into this folder (run from Linux or Git Bash).
set -euo pipefail
cd "$(dirname "$0")"

PY_URL="https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
PY_FILE="python-3.12.10-amd64.exe"
VC_URL="https://aka.ms/vs/17/release/vc_redist.x64.exe"
VC_FILE="VC_redist.x64.exe"
LO_VER="26.2.4"
LO_FILE="LibreOffice_${LO_VER}_Win_x86-64.msi"
LO_URL="https://download.documentfoundation.org/libreoffice/stable/${LO_VER}/win/x86_64/${LO_FILE}"

download() {
  local url="$1" out="$2"
  if [[ -f "$out" ]]; then
    echo "[OK] already present: $out"
    return 0
  fi
  echo "Downloading $out ..."
  curl -L --retry 3 --retry-delay 2 -o "${out}.partial" "$url"
  mv "${out}.partial" "$out"
  echo "[OK] $out ($(du -h "$out" | cut -f1))"
}

download "$PY_URL" "$PY_FILE"
download "$VC_URL" "$VC_FILE"
download "$LO_URL" "$LO_FILE"
echo "Done."
ls -lh *.exe *.msi 2>/dev/null || true

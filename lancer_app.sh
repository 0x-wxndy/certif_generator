#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -q -r requirements.txt

echo ""
echo "  Générateur de certificats"
echo "  Ouvrez http://localhost:8501 dans votre navigateur"
echo ""

.venv/bin/streamlit run certificate_ui.py --server.headless true --browser.gatherUsageStats false

#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  print -u2 "Missing .venv. Follow the installation steps in automation/README.md first."
  exit 2
fi

cd "${PROJECT_DIR}"
"${PYTHON}" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --specpath build \
  --name "Zaiko Lottery Assistant" \
  --hidden-import keyring.backends.macOS \
  automation/desktop_app.py

print "Built: ${PROJECT_DIR}/dist/Zaiko Lottery Assistant.app"

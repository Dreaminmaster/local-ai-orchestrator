#!/usr/bin/env sh
set -eu

python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp -n .env.example .env || true
python scripts/health_check.py

echo "\nSetup complete. Run:"
echo "  . venv/bin/activate"
echo "  python run.py"

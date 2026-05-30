#!/usr/bin/env python3
"""Prepare Python backend sidecar artifact plan.

Alpha: writes a manifest and documents the PyInstaller/uv target.
Does not build dmg/msi or enable Tauri bundle.
"""

from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/desktop/src-tauri/bin"
OUT.mkdir(parents=True, exist_ok=True)
manifest = {
    "created_at": datetime.now().isoformat(),
    "entrypoint": "run.py",
    "target_name": "local-ai-orchestrator-backend",
    "planned_commands": [
        "pyinstaller --onefile run.py -n local-ai-orchestrator-backend",
        "or use uv/standalone Python to package backend dependencies",
    ],
    "notes": "bundle.active remains false until sidecar binary is tested.",
}
(OUT / "SIDE_CAR_MANIFEST.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(OUT / "SIDE_CAR_MANIFEST.json")

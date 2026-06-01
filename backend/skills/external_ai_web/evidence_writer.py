from pathlib import Path
from datetime import datetime
import json
import re


class WebAIEvidenceWriter:
    def __init__(self, root: str = "runtime/evidence/web_ai"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_qa(
        self, provider: str, prompt: str, answer: str, metadata: dict | None = None
    ) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", provider.lower())
        provider_dir = self.root / safe
        provider_dir.mkdir(parents=True, exist_ok=True)
        path = provider_dir / f"{ts}.json"
        path.write_text(
            json.dumps(
                {
                    "provider": provider,
                    "prompt": prompt,
                    "answer": answer,
                    "metadata": metadata or {},
                    "created_at": datetime.now().isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(path)

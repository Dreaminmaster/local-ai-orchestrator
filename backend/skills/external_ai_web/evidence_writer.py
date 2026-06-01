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
        path = self.root / f"{safe}_{ts}.json"
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

    async def save_run(
        self,
        provider: str,
        prompt: str,
        answer: str,
        page=None,
        metadata: dict | None = None,
    ) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", provider.lower())
        path = self.root / safe / ts
        path.mkdir(parents=True, exist_ok=True)
        (path / "prompt.redacted.txt").write_text(prompt or "", encoding="utf-8")
        (path / "answer.txt").write_text(answer or "", encoding="utf-8")
        extract = (metadata or {}).get("extract", {}) if metadata else {}
        if extract.get("raw_body_fallback"):
            (path / "answer_raw_body_fallback.txt").write_text(
                extract.get("raw_body_fallback") or "",
                encoding="utf-8",
            )
        if extract.get("candidate_selectors"):
            (path / "candidate_selectors.json").write_text(
                json.dumps(
                    extract.get("candidate_selectors") or [],
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        if page is not None:
            try:
                await page.screenshot(path=str(path / "screenshot.png"), full_page=True)
            except Exception as exc:
                meta = metadata or {}
                meta["screenshot_error"] = str(exc)
                metadata = meta
        (path / "metadata.json").write_text(
            json.dumps(metadata or {}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(path)

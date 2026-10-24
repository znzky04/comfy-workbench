from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from .models import GenerationRequest
from .service import GenerationService


class InboxWatcher:
    def __init__(self, service: GenerationService, root: Path | None = None):
        self.service = service
        self.root = root or (service.settings.project_root / "inbox")
        for state in ("pending", "processing", "done", "failed"):
            (self.root / state).mkdir(parents=True, exist_ok=True)

    def process_one(self, source: Path) -> dict:
        processing = self.root / "processing" / source.name
        os.replace(source, processing)
        try:
            request = GenerationRequest.model_validate_json(processing.read_text(encoding="utf-8"))
            request.client = "inbox"
            manifest = self.service.submit(request, wait=True)
            destination = self.root / "done" / source.name
            os.replace(processing, destination)
            return {"ok": True, "job_id": manifest.job_id, "request": str(destination)}
        except Exception as exc:  # noqa: BLE001 - every failed request must be retained with evidence
            destination = self.root / "failed" / source.name
            os.replace(processing, destination)
            error_path = destination.with_suffix(destination.suffix + ".error.json")
            error_path.write_text(
                json.dumps(
                    {
                        "failed_at": datetime.now(UTC).isoformat(),
                        "error_category": type(exc).__name__,
                        "error": str(exc),
                        "request": str(destination.resolve()),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return {"ok": False, "error": str(exc), "request": str(destination)}

    def scan(self) -> list[dict]:
        return [self.process_one(path) for path in sorted((self.root / "pending").glob("*.json"))]

    def watch(self, interval_seconds: float = 2) -> None:
        while True:
            self.scan()
            time.sleep(interval_seconds)

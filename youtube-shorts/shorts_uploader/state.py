"""Память о уже залитых файлах, чтобы повторный запуск не создавал копии."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shorts_uploader.errors import ShortsError
from shorts_uploader.models import UploadRecord


class State:
    def __init__(self, path: Path, records: list[UploadRecord] | None = None) -> None:
        self.path = path
        self.records = list(records or [])

    def by_fingerprint(self, fingerprint: str) -> UploadRecord | None:
        for record in reversed(self.records):
            if record.fingerprint == fingerprint:
                return record
        return None

    def by_path(self, path: Path) -> UploadRecord | None:
        target = str(path.resolve())
        for record in reversed(self.records):
            if record.file == target:
                return record
        return None

    def upsert(self, record: UploadRecord) -> None:
        self.records = [item for item in self.records if item.fingerprint != record.fingerprint]
        self.records.append(record)

    def save(self) -> None:
        payload = {"version": 1, "uploads": [record.to_json() for record in self.records]}
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(self.path)


def load_state(path: Path) -> State:
    if not path.exists():
        return State(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ShortsError(f"файл состояния повреждён: {path}") from exc
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("uploads"), list):
        raise ShortsError(f"не понял файл состояния {path}. Ожидается version: 1")
    try:
        records = [UploadRecord.from_json(item) for item in data["uploads"]]
    except (TypeError, ValueError) as exc:
        raise ShortsError(f"файл состояния повреждён: {path}: {exc}") from exc
    return State(path, records)


def fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

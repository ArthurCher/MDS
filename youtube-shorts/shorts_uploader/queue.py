"""Чтение queue.yaml и соседних файлов с названием и описанием."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

from shorts_uploader.errors import QueueError
from shorts_uploader.models import DEFAULT_TIMEZONE, PRIVACY_VALUES, VIDEO_SUFFIXES, QueueFile, VideoSpec

_ROOT_KEYS = {"timezone", "defaults", "inbox", "videos"}
_DEFAULT_KEYS = {
    "privacy",
    "category_id",
    "made_for_kids",
    "append_shorts_hashtag",
    "playlist_id",
    "default_language",
    "synthetic_media",
    "allow_long_form",
    "embeddable",
    "tags",
    "description",
}
_VIDEO_KEYS = _DEFAULT_KEYS | {"file", "title", "publish_at", "thumbnail"}


def load_queue(path: Path) -> QueueFile:
    path = path.resolve()
    data = _read_mapping(path, f"очередь {path.name}")
    _reject_unknown(data, _ROOT_KEYS, f"очередь {path.name}")
    zone = _timezone(data.get("timezone", DEFAULT_TIMEZONE))
    defaults = _section(data.get("defaults") or {}, _DEFAULT_KEYS, "defaults")
    explicit = data.get("videos") or []
    if not isinstance(explicit, list):
        raise QueueError("поле videos должно быть списком")

    videos: list[VideoSpec] = []
    seen: set[Path] = set()
    for index, raw in enumerate(explicit, start=1):
        spec = _video(raw, defaults, zone, path.parent, where=f"videos[{index}]")
        if spec.file in seen:
            raise QueueError(f"файл указан дважды: {spec.file}")
        seen.add(spec.file)
        videos.append(spec)

    inbox = data.get("inbox")
    if inbox:
        inbox_dir = _resolve(inbox, path.parent, "inbox")
        if not inbox_dir.is_dir():
            raise QueueError(f"папка inbox не найдена: {inbox_dir}")
        for video_path in _iter_inbox(inbox_dir):
            resolved = video_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            videos.append(_from_inbox(resolved, defaults, zone))

    if not videos:
        raise QueueError("в очереди нет роликов. Добавьте videos или положите файлы в inbox")
    return QueueFile(path=path, timezone=zone, videos=videos)


def _from_inbox(path: Path, defaults: dict, zone: ZoneInfo) -> VideoSpec:
    sidecar = _sidecar(path)
    raw = dict(defaults)
    raw["file"] = str(path)
    if sidecar is not None:
        loaded = _read_mapping(sidecar, f"описание {sidecar.name}")
        _reject_unknown(loaded, _VIDEO_KEYS, f"описание {sidecar.name}")
        if "file" in loaded:
            raise QueueError(f"в {sidecar.name} поле file не нужно: ролик и так лежит рядом")
        raw.update(loaded)
    if "title" not in raw or not str(raw.get("title", "")).strip():
        raw["title"] = path.stem.replace("_", " ").strip()
    return _video(raw, defaults, zone, path.parent, where=path.name)


def _video(raw: object, defaults: dict, zone: ZoneInfo, base: Path, *, where: str) -> VideoSpec:
    if not isinstance(raw, dict):
        raise QueueError(f"{where} должен быть набором полей, а не {type(raw).__name__}")
    _reject_unknown(raw, _VIDEO_KEYS, where)
    merged = dict(defaults)
    merged.update(raw)
    if "file" not in merged:
        raise QueueError(f"в {where} не указан file")
    file_path = _resolve(merged["file"], base, f"{where}.file")
    title = _as_str(merged.get("title", ""), f"{where}.title")
    thumbnail = merged.get("thumbnail")
    return VideoSpec(
        file=file_path,
        title=title,
        description=_as_str(merged.get("description", ""), f"{where}.description"),
        tags=_tags(merged.get("tags", []), f"{where}.tags"),
        publish_at=_when(merged.get("publish_at"), zone, f"{where}.publish_at"),
        privacy=_privacy(merged.get("privacy", "private"), f"{where}.privacy"),
        thumbnail=None if not thumbnail else _resolve(thumbnail, base, f"{where}.thumbnail"),
        playlist_id=_optional_str(merged.get("playlist_id"), f"{where}.playlist_id"),
        category_id=_category(merged.get("category_id", "22"), f"{where}.category_id"),
        made_for_kids=_as_bool(merged.get("made_for_kids", False), f"{where}.made_for_kids"),
        append_shorts_hashtag=_as_bool(
            merged.get("append_shorts_hashtag", False), f"{where}.append_shorts_hashtag"
        ),
        synthetic_media=_as_bool(merged.get("synthetic_media", False), f"{where}.synthetic_media"),
        embeddable=_as_bool(merged.get("embeddable", True), f"{where}.embeddable"),
        default_language=_as_str(merged.get("default_language", "ru"), f"{where}.default_language") or "ru",
        allow_long_form=_as_bool(merged.get("allow_long_form", False), f"{where}.allow_long_form"),
        origin=where,
    )


def _section(raw: object, allowed: set[str], where: str) -> dict:
    if not isinstance(raw, dict):
        raise QueueError(f"{where} должен быть набором полей")
    _reject_unknown(raw, allowed, where)
    return raw


def _iter_inbox(directory: Path) -> list[Path]:
    found: list[Path] = []
    for path in directory.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if any(part.startswith(".") for part in path.relative_to(directory).parts):
            continue
        if path.suffix.lower() in VIDEO_SUFFIXES:
            found.append(path)
    return sorted(found, key=lambda item: item.as_posix().lower())


def _sidecar(video: Path) -> Path | None:
    for suffix in (".yaml", ".yml", ".json"):
        candidate = video.with_suffix(suffix)
        if candidate.is_file():
            return candidate
    return None


def _read_mapping(path: Path, where: str) -> dict:
    if not path.is_file():
        raise QueueError(f"не найден файл: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text or "{}")
        else:
            data = yaml.safe_load(text) or {}
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise QueueError(f"не удалось прочитать {where}: {exc}") from exc
    if not isinstance(data, dict):
        raise QueueError(f"{where} должен быть набором полей")
    return data


def _reject_unknown(data: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        names = ", ".join(unknown)
        known = ", ".join(sorted(allowed))
        raise QueueError(f"неизвестное поле в {where}: {names}. Допустимы: {known}")


def _timezone(value: object) -> ZoneInfo:
    name = _as_str(value, "timezone")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise QueueError(f"неизвестный часовой пояс: {name}") from exc


def _resolve(value: object, base: Path, where: str) -> Path:
    text = _as_str(value, where)
    if not text:
        raise QueueError(f"пустое поле {where}")
    path = Path(text)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _when(value: object, zone: ZoneInfo, where: str) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        moment = value
    else:
        text = _as_str(value, where)
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            moment = datetime.fromisoformat(text)
        except ValueError as exc:
            raise QueueError(
                f"не понял время в {where}: {value}. Пример: 2026-12-01 18:00"
            ) from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=zone)
    return moment.astimezone(timezone.utc)


def _privacy(value: object, where: str) -> str:
    text = _as_str(value, where).lower()
    if text not in PRIVACY_VALUES:
        allowed = ", ".join(sorted(PRIVACY_VALUES))
        raise QueueError(f"в {where} статус {value!r} не подходит. Допустимы: {allowed}")
    return text


def _category(value: object, where: str) -> str:
    text = _as_str(value, where)
    if not text.isdigit():
        raise QueueError(f"в {where} категория должна быть числом YouTube, например 22")
    return text


def _tags(value: object, where: str) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, list):
        parts = value
    else:
        raise QueueError(f"{where} должен быть списком или строкой через запятую")
    tags: list[str] = []
    seen: set[str] = set()
    for part in parts:
        tag = _as_str(part, where)
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def _optional_str(value: object, where: str) -> str | None:
    if value is None:
        return None
    text = _as_str(value, where)
    return text or None


def _as_str(value: object, where: str) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value).strip()
    raise QueueError(f"поле {where} должно быть строкой")


def _as_bool(value: object, where: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "да", "1"}:
            return True
        if lowered in {"false", "no", "нет", "0"}:
            return False
    raise QueueError(f"поле {where} должно быть true или false")

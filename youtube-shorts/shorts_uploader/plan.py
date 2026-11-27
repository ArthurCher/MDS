"""Решает по каждому файлу: залить, дописать обложку или пропустить."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from shorts_uploader.body import prepare_metadata
from shorts_uploader.errors import MediaProbeError
from shorts_uploader.media import assess_short
from shorts_uploader.models import (
    THUMBNAIL_LIMIT_BYTES,
    THUMBNAIL_SUFFIXES,
    VIDEO_SUFFIXES,
    Issue,
    MediaInfo,
    Planned,
    QueueFile,
    UploadRecord,
    VideoSpec,
)
from shorts_uploader.state import State, fingerprint_file

_UNCHECKED = MediaInfo(width=None, height=None, duration=None, checked=False)


def build_plan(
    queue: QueueFile,
    state: State,
    *,
    now: datetime | None = None,
    skip_media_check: bool = False,
    force: bool = False,
    probe=None,
) -> list[Planned]:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    reader = probe or _probe
    planned = [
        _one(
            spec,
            state,
            now=moment,
            skip_media_check=skip_media_check,
            force=force,
            probe=reader,
        )
        for spec in queue.videos
    ]
    return sorted(planned, key=_sort_key)


def _sort_key(item: Planned) -> tuple:
    stamp = item.spec.publish_at.timestamp() if item.spec.publish_at is not None else float("inf")
    return (stamp, item.spec.file.as_posix().lower())


def _one(
    spec: VideoSpec,
    state: State,
    *,
    now: datetime,
    skip_media_check: bool,
    force: bool,
    probe,
) -> Planned:
    prepared = prepare_metadata(spec, now=now)
    record, fingerprint, file_issues = _locate(spec, state, force=force)
    already = record is not None and not force

    if already and (_needs_thumbnail(spec, record) or _needs_playlist(spec, record)):
        action = "finish"
        issues = list(file_issues)
        issues.extend(_thumbnail_issues(spec))
        media = None
        if any(issue.level == "error" for issue in issues):
            action = "error"
    elif already:
        action = "skip"
        issues = []
        media = None
    else:
        action = "upload"
        issues = list(prepared.issues)
        issues.extend(file_issues)
        media = _read_media(spec, skip_media_check=skip_media_check, probe=probe, issues=issues)
        if media is not None:
            issues.extend(assess_short(media, allow_long_form=spec.allow_long_form))
        issues.extend(_thumbnail_issues(spec))
        if any(issue.level == "error" for issue in issues):
            action = "error"

    return Planned(
        spec=spec,
        action=action,
        issues=issues,
        title=prepared.title or spec.title or spec.file.name,
        description=prepared.description,
        privacy=prepared.privacy,
        body=prepared.body if action == "upload" else None,
        fingerprint=fingerprint,
        record=record,
        media=media,
    )


def _locate(
    spec: VideoSpec, state: State, *, force: bool
) -> tuple[UploadRecord | None, str | None, list[Issue]]:
    issues: list[Issue] = []
    if spec.file.suffix.lower() not in VIDEO_SUFFIXES:
        issues.append(
            Issue("error", f"ожидается видео ({', '.join(sorted(VIDEO_SUFFIXES))})")
        )
    if spec.file.is_file():
        if spec.file.stat().st_size == 0:
            issues.append(Issue("error", "файл пустой"))
            return None, None, issues
        fingerprint = fingerprint_file(spec.file)
        record = None if force else state.by_fingerprint(fingerprint)
        return record, fingerprint, issues
    if not spec.file.exists():
        record = None if force else state.by_path(spec.file)
        if record is None:
            issues.append(Issue("error", f"файл не найден: {spec.file}"))
            return None, None, issues
        return record, record.fingerprint, issues
    issues.append(Issue("error", f"это не файл: {spec.file}"))
    return None, None, issues


def _read_media(spec: VideoSpec, *, skip_media_check: bool, probe, issues: list[Issue]) -> MediaInfo | None:
    if not spec.file.is_file() or spec.file.stat().st_size == 0:
        return None
    if skip_media_check:
        return _UNCHECKED
    try:
        return probe(spec.file)
    except MediaProbeError as exc:
        issues.append(Issue("error", str(exc)))
        return None


def _needs_thumbnail(spec: VideoSpec, record: UploadRecord) -> bool:
    if spec.thumbnail is None:
        return False
    return (not record.thumbnail_set) or record.thumbnail != str(spec.thumbnail)


def _needs_playlist(spec: VideoSpec, record: UploadRecord) -> bool:
    if not spec.playlist_id:
        return False
    return (not record.playlist_added) or record.playlist_id != spec.playlist_id


def _thumbnail_issues(spec: VideoSpec) -> list[Issue]:
    if spec.thumbnail is None:
        return []
    issues: list[Issue] = []
    if spec.thumbnail.suffix.lower() not in THUMBNAIL_SUFFIXES:
        issues.append(Issue("error", "обложка должна быть JPEG, PNG, GIF или BMP"))
    if not spec.thumbnail.is_file():
        issues.append(Issue("error", f"обложка не найдена: {spec.thumbnail}"))
        return issues
    size = spec.thumbnail.stat().st_size
    if size == 0:
        issues.append(Issue("error", "обложка пустая"))
    elif size > THUMBNAIL_LIMIT_BYTES:
        issues.append(Issue("error", "обложка больше 2 МБ"))
    return issues


def _probe(path: Path) -> MediaInfo:
    from shorts_uploader.media import probe_file

    return probe_file(path)

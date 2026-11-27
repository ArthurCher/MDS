"""Отправляет на канал только то, что план пометил как новое."""

from __future__ import annotations

from datetime import datetime, timezone

from shorts_uploader.errors import YouTubeApiError
from shorts_uploader.models import STOP_REASONS, Planned, Summary, UploadRecord
from shorts_uploader.state import State
from shorts_uploader.text import video_url


def apply_limit(items: list[Planned], limit: int | None) -> None:
    """Оставляет в этом запуске не больше limit новых роликов. Обложки и плейлисты не считаются."""
    if limit is None:
        return
    queued = 0
    for item in items:
        if item.action != "upload":
            continue
        if queued >= limit:
            item.action = "deferred"
        else:
            queued += 1


def execute(
    items: list[Planned],
    *,
    state: State,
    client,
    dry_run: bool,
) -> Summary:
    summary = Summary()
    for item in items:
        if item.action == "error":
            summary.failed += 1
            continue
        if item.action == "skip":
            summary.skipped += 1
            continue
        if item.action == "deferred":
            summary.deferred += 1
            continue
        if dry_run:
            if item.action == "upload":
                summary.uploaded += 1
            else:
                summary.finished += 1
            continue
        try:
            if item.action == "upload":
                _upload(item, state=state, client=client)
                summary.uploaded += 1
            _extras_for(item, state=state, client=client)
            if item.action == "finish":
                summary.finished += 1
        except YouTubeApiError as exc:
            print()
            print(f"! {item.title}: {exc}")
            summary.failed += 1
            item.action = "error"
            item.issues.append(_issue(str(exc)))
            if exc.reason in STOP_REASONS or exc.status in {401}:
                print("Дальше в этом запуске ничего не отправляю.")
                _defer_rest(items, item, summary)
                break
    return summary


def _defer_rest(items: list[Planned], current: Planned, summary: Summary) -> None:
    seen = False
    for item in items:
        if item is current:
            seen = True
            continue
        if not seen:
            continue
        if item.action == "error":
            summary.failed += 1
        elif item.action == "skip":
            summary.skipped += 1
        elif item.action == "deferred":
            summary.deferred += 1
        elif item.action in {"upload", "finish"}:
            item.action = "deferred"
            summary.deferred += 1


def _upload(item: Planned, *, state: State, client) -> None:
    if item.body is None or item.fingerprint is None:
        raise YouTubeApiError("внутренняя ошибка: нечего отправлять")
    video_id = client.upload(item.spec.file, item.body, on_progress=_progress)
    print()
    print(f"  видео: {video_url(video_id)}")
    record = UploadRecord(
        fingerprint=item.fingerprint,
        video_id=video_id,
        file=str(item.spec.file),
        title=item.title,
        uploaded_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        thumbnail_set=item.spec.thumbnail is None,
        playlist_added=not item.spec.playlist_id,
        playlist_id=item.spec.playlist_id,
        thumbnail=str(item.spec.thumbnail) if item.spec.thumbnail else None,
    )
    state.upsert(record)
    state.save()
    item.record = record


def _extras_for(item: Planned, *, state: State, client) -> None:
    record = item.record
    if record is None:
        raise YouTubeApiError("внутренняя ошибка: нет id ролика")
    if item.action == "finish":
        print(f"  видео: {video_url(record.video_id)}")
    _extras(item, record, client=client, state=state)


def _extras(item: Planned, record: UploadRecord, *, client, state: State) -> None:
    if item.spec.thumbnail is not None and (
        not record.thumbnail_set or record.thumbnail != str(item.spec.thumbnail)
    ):
        client.wait_until_processed(record.video_id)
        client.set_thumbnail(record.video_id, item.spec.thumbnail)
        record.thumbnail_set = True
        record.thumbnail = str(item.spec.thumbnail)
        state.upsert(record)
        state.save()
        print("  обложка поставлена")
    if item.spec.playlist_id and (
        not record.playlist_added or record.playlist_id != item.spec.playlist_id
    ):
        client.add_to_playlist(record.video_id, item.spec.playlist_id)
        record.playlist_added = True
        record.playlist_id = item.spec.playlist_id
        state.upsert(record)
        state.save()
        print(f"  добавлено в плейлист {item.spec.playlist_id}")


def _progress(fraction: float) -> None:
    print(f"\r  заливка {fraction * 100:5.1f}%", end="", flush=True)


def _issue(text: str):
    from shorts_uploader.models import Issue

    return Issue("error", text)

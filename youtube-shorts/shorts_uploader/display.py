"""Текст плана для терминала."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from shorts_uploader.models import Planned, Summary
from shorts_uploader.text import format_duration, format_when, video_url

_MARK = {"upload": "+", "finish": "~", "skip": "—", "error": "!", "deferred": "…"}


def render_item(item: Planned, zone: ZoneInfo) -> str:
    mark = _MARK.get(item.action, "?")
    lines = [f"{mark} {item.title}", f"  файл: {item.spec.file}"]
    if item.action == "skip" and item.record is not None:
        lines.append(f"  уже на канале: {video_url(item.record.video_id)}")
    elif item.action == "finish" and item.record is not None:
        lines.append(f"  дописать уже залитый ролик: {video_url(item.record.video_id)}")
    elif item.action in {"upload", "deferred"}:
        if item.spec.publish_at is not None and item.privacy == "private":
            lines.append(f"  скрыт до {format_when(item.spec.publish_at, zone)}, затем станет public")
        else:
            lines.append(f"  сразу со статусом {item.privacy}")
    if item.media is not None and item.media.width and item.media.height and item.media.duration is not None:
        lines.append(
            f"  {item.media.width}×{item.media.height}, {format_duration(item.media.duration)}"
        )
    for issue in item.issues:
        prefix = "ошибка" if issue.level == "error" else "замечание"
        lines.append(f"  {prefix}: {issue.text}")
    return "\n".join(lines)


def render_plan(items: list[Planned], zone: ZoneInfo) -> str:
    if not items:
        return "Очередь пуста."
    return "\n\n".join(render_item(item, zone) for item in items)


def render_summary(summary: Summary, *, dry_run: bool) -> str:
    if dry_run:
        return (
            f"Пробный прогон, на YouTube ничего не отправлено. "
            f"К выкладке: {summary.uploaded}. Дописать: {summary.finished}. "
            f"Уже залито: {summary.skipped}. Ошибок: {summary.failed}. "
            f"Не влезает в --limit: {summary.deferred}."
        )
    return (
        f"Выложено: {summary.uploaded}. Дописано: {summary.finished}. "
        f"Пропущено: {summary.skipped}. Ошибок: {summary.failed}. "
        f"Отложено лимитом: {summary.deferred}."
    )

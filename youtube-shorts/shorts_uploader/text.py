"""Длины и подписи так, как их считает YouTube и как их удобно читать."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_MONTHS = (
    "янв",
    "фев",
    "мар",
    "апр",
    "мая",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
)


def youtube_len(text: str) -> int:
    """YouTube считает лимит заголовка в кодовых единицах UTF-16, эмодзи занимают две."""
    return sum(2 if ord(char) > 0xFFFF else 1 for char in text)


def tag_char_count(tags: list[str]) -> int:
    """Запятые между тегами входят в лимит. Пробел внутри тега добавляет кавычки."""
    total = 0
    for index, tag in enumerate(tags):
        length = youtube_len(tag)
        if any(char.isspace() for char in tag):
            length += 2
        total += length
        if index:
            total += 1
    return total


def to_rfc3339(moment: datetime) -> str:
    utc = moment.astimezone(timezone.utc).replace(microsecond=0)
    return utc.isoformat().replace("+00:00", "Z")


def format_when(moment: datetime, zone: ZoneInfo) -> str:
    local = moment.astimezone(zone)
    month = _MONTHS[local.month - 1]
    offset = local.strftime("%z")
    pretty_offset = f"{offset[:3]}:{offset[3:]}" if len(offset) == 5 else offset
    return (
        f"{local.day} {month} {local.year}, {local:%H:%M} "
        f"(UTC{pretty_offset}, {zone.key})"
    )


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} с"
    minutes = int(seconds // 60)
    rest = seconds - minutes * 60
    return f"{minutes} мин {rest:.0f} с"


def video_url(video_id: str) -> str:
    return f"https://www.youtube.com/shorts/{video_id}"

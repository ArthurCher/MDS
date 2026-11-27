"""Проверка, что файл действительно станет Shorts: вертикаль или квадрат и до 3 минут."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from shorts_uploader.errors import MediaProbeError
from shorts_uploader.models import SHORTS_MAX_SECONDS, Issue, MediaInfo


def display_size(width: int, height: int, rotation: int) -> tuple[int, int]:
    """Телефон часто пишет вертикаль как горизонтальный кадр с поворотом 90°."""
    if abs(int(rotation)) % 180 == 90:
        return height, width
    return width, height


def _rotation(stream: dict) -> int:
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            return int(round(float(side["rotation"])))
    tags = stream.get("tags") or {}
    if "rotate" in tags:
        return int(round(float(tags["rotate"])))
    return 0


def _duration(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            seconds = float(value)
        except (TypeError, ValueError):
            continue
        if seconds >= 0:
            return seconds
    return None


def parse_probe_payload(payload: dict) -> MediaInfo:
    streams = [
        stream
        for stream in payload.get("streams") or []
        if stream.get("codec_type", "video") == "video" and stream.get("width") and stream.get("height")
    ]
    format_duration = (payload.get("format") or {}).get("duration")
    if not streams:
        return MediaInfo(width=None, height=None, duration=_duration(format_duration), checked=True)
    stream = streams[0]
    width, height = display_size(int(stream["width"]), int(stream["height"]), _rotation(stream))
    return MediaInfo(
        width=width,
        height=height,
        duration=_duration(stream.get("duration"), format_duration),
        checked=True,
    )


def probe_file(path: Path) -> MediaInfo:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise MediaProbeError(
            "Не найден ffprobe. Установите ffmpeg, без него нельзя проверить, что ролик вертикальный и короче 3 минут."
        )
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired as exc:
        raise MediaProbeError(f"ffprobe слишком долго читал {path.name}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "неизвестная ошибка").strip()
        raise MediaProbeError(f"ffprobe не прочитал {path.name}: {detail}")
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise MediaProbeError(f"ffprobe вернул не JSON для {path.name}") from exc
    return parse_probe_payload(payload)


def assess_short(media: MediaInfo, *, allow_long_form: bool) -> list[Issue]:
    """Горизонталь и ролик длиннее 3 минут YouTube не кладёт в Shorts."""
    if not media.checked:
        return [Issue("warning", "размер и длительность не проверены (--skip-media-check)")]

    issues: list[Issue] = []
    level = "warning" if allow_long_form else "error"

    if media.width is None or media.height is None:
        issues.append(Issue(level, "в файле нет видеодорожки"))
    elif media.height < media.width:
        issues.append(
            Issue(
                level,
                f"кадр горизонтальный ({media.width}×{media.height}). "
                "Shorts получается только из вертикали или квадрата",
            )
        )
    elif media.height == media.width:
        issues.append(Issue("warning", f"квадрат {media.width}×{media.height}: Shorts примет, но на телефоне будут поля"))
    else:
        ratio = media.height / media.width
        if abs(ratio - (16 / 9)) > 0.08:
            issues.append(
                Issue(
                    "warning",
                    f"кадр {media.width}×{media.height} вертикальный, но не 9:16. "
                    "Надёжнее выгрузить 1080×1920",
                )
            )

    if media.width and media.height and (media.width > 1080 or media.height > 1920) and media.height >= media.width:
        issues.append(Issue("warning", "для Shorts YouTube рекомендует не выше 1080p (1080×1920)"))

    if media.duration is None:
        issues.append(Issue(level, "не удалось прочитать длительность"))
    elif media.duration > SHORTS_MAX_SECONDS + 0.05:
        issues.append(
            Issue(
                level,
                f"ролик {media.duration:.1f} с длиннее 3 минут и выйдет обычным видео, а не Shorts",
            )
        )
    elif media.duration > 60:
        issues.append(
            Issue(
                "warning",
                "Shorts длиннее минуты с любой претензией Content ID блокируется целиком. "
                "Чужую музыку безопаснее не класть",
            )
        )
    return issues

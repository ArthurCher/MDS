"""Данные очереди и уже выложенных роликов."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Makassar"
SHORTS_MAX_SECONDS = 180.0
TITLE_LIMIT = 100
DESCRIPTION_LIMIT = 5000
TAGS_LIMIT = 500
THUMBNAIL_LIMIT_BYTES = 2 * 1024 * 1024
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
THUMBNAIL_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
PRIVACY_VALUES = {"public", "private", "unlisted"}

# Сроки, на которых дальше слать ролики бессмысленно: кончилась квота или доступ.
STOP_REASONS = {
    "authError",
    "invalidCredentials",
    "insufficientPermissions",
    "quotaExceeded",
    "dailyLimitExceeded",
    "youtubeSignupRequired",
    "channelClosed",
    "channelSuspended",
}


@dataclass
class VideoSpec:
    """Один ролик после слияния defaults, строки очереди и соседнего yaml."""

    file: Path
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    publish_at: datetime | None = None
    privacy: str = "private"
    thumbnail: Path | None = None
    playlist_id: str | None = None
    category_id: str = "22"
    made_for_kids: bool = False
    append_shorts_hashtag: bool = False
    synthetic_media: bool = False
    embeddable: bool = True
    default_language: str = "ru"
    allow_long_form: bool = False
    origin: str = "queue"


@dataclass
class QueueFile:
    path: Path
    timezone: ZoneInfo
    videos: list[VideoSpec]


@dataclass
class MediaInfo:
    width: int | None
    height: int | None
    duration: float | None
    checked: bool


@dataclass
class Issue:
    level: str
    text: str


@dataclass
class PreparedMetadata:
    title: str
    description: str
    privacy: str
    publish_at: datetime | None
    issues: list[Issue]
    body: dict | None


@dataclass
class UploadRecord:
    fingerprint: str
    video_id: str
    file: str
    title: str
    uploaded_at: str
    thumbnail_set: bool
    playlist_added: bool
    playlist_id: str | None = None
    thumbnail: str | None = None

    def to_json(self) -> dict:
        return {
            "fingerprint": self.fingerprint,
            "video_id": self.video_id,
            "file": self.file,
            "title": self.title,
            "uploaded_at": self.uploaded_at,
            "thumbnail_set": self.thumbnail_set,
            "playlist_added": self.playlist_added,
            "playlist_id": self.playlist_id,
            "thumbnail": self.thumbnail,
        }

    @classmethod
    def from_json(cls, data: dict) -> UploadRecord:
        required = ("fingerprint", "video_id", "file", "title", "uploaded_at")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"в состоянии не хватает полей: {', '.join(missing)}")
        return cls(
            fingerprint=str(data["fingerprint"]),
            video_id=str(data["video_id"]),
            file=str(data["file"]),
            title=str(data["title"]),
            uploaded_at=str(data["uploaded_at"]),
            thumbnail_set=bool(data.get("thumbnail_set", False)),
            playlist_added=bool(data.get("playlist_added", False)),
            playlist_id=data.get("playlist_id") or None,
            thumbnail=data.get("thumbnail") or None,
        )


@dataclass
class Planned:
    spec: VideoSpec
    action: str
    issues: list[Issue]
    title: str
    description: str
    privacy: str
    body: dict | None
    fingerprint: str | None
    record: UploadRecord | None
    media: MediaInfo | None


@dataclass
class Summary:
    uploaded: int = 0
    finished: int = 0
    skipped: int = 0
    failed: int = 0
    deferred: int = 0

    @property
    def ok(self) -> bool:
        return self.failed == 0

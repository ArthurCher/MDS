"""Заливки, обложки и плейлисты через YouTube Data API v3."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from shorts_uploader.auth import load_credentials
from shorts_uploader.errors import YouTubeApiError

_RETRYABLE = {429, 500, 502, 503, 504}
_MIME = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


class YouTubeClient:
    def __init__(self, service, *, sleep=time.sleep, thumbnail_timeout: float = 600, thumbnail_poll: float = 15):
        self._service = service
        self._sleep = sleep
        self._thumbnail_timeout = thumbnail_timeout
        self._thumbnail_poll = thumbnail_poll

    def channel(self) -> tuple[str, str]:
        response = self._execute(self._service.channels().list(part="snippet", mine=True))
        items = response.get("items") or []
        if not items:
            raise YouTubeApiError(
                "У этого аккаунта нет канала YouTube. Создайте канал и снова выполните auth.",
                reason="youtubeSignupRequired",
            )
        snippet = items[0].get("snippet") or {}
        return items[0]["id"], snippet.get("title") or items[0]["id"]

    def upload(self, path: Path, body: dict, on_progress=None) -> str:
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            str(path),
            chunksize=8 * 1024 * 1024,
            resumable=True,
            mimetype=_MIME.get(path.suffix.lower(), "application/octet-stream"),
        )
        request = self._service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        retry = 0
        delay = 1.0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status is not None and on_progress is not None:
                    on_progress(min(status.progress(), 0.99))
                retry = 0
                delay = 1.0
            except HttpError as exc:
                status_code, reason, message = parse_http_error(exc)
                if status_code in _RETRYABLE and retry < 5:
                    retry += 1
                    self._sleep(delay + random.random())
                    delay *= 2
                    continue
                raise YouTubeApiError(message, status=status_code, reason=reason) from exc
            except (TimeoutError, ConnectionError, OSError) as exc:
                if retry < 5:
                    retry += 1
                    self._sleep(delay)
                    delay *= 2
                    continue
                raise YouTubeApiError(f"сеть оборвалась во время заливки: {exc}") from exc
        if on_progress is not None:
            on_progress(1.0)
        video_id = response.get("id")
        if not video_id:
            raise YouTubeApiError("YouTube принял ролик, но не вернул id")
        return video_id

    def wait_until_processed(self, video_id: str) -> None:
        deadline = time.monotonic() + self._thumbnail_timeout
        while True:
            response = self._execute(self._service.videos().list(part="processingDetails", id=video_id))
            items = response.get("items") or []
            details = (items[0].get("processingDetails") if items else None) or {}
            status = details.get("processingStatus")
            if status == "succeeded":
                return
            if status in {"failed", "terminated"}:
                raise YouTubeApiError(
                    f"YouTube не смог обработать ролик {video_id} (статус {status})",
                    reason=status or "",
                )
            if time.monotonic() >= deadline:
                raise YouTubeApiError(
                    f"YouTube не успел обработать ролик за {int(self._thumbnail_timeout)} с. "
                    "Запустите upload ещё раз: файл заново не зальётся, скрипт дождётся обработки и поставит обложку."
                )
            self._sleep(self._thumbnail_poll)

    def set_thumbnail(self, video_id: str, path: Path) -> None:
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(str(path), mimetype=_MIME.get(path.suffix.lower(), "image/jpeg"))
        self._execute(self._service.thumbnails().set(videoId=video_id, media_body=media))

    def add_to_playlist(self, video_id: str, playlist_id: str) -> None:
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
        try:
            self._execute(self._service.playlistItems().insert(part="snippet", body=body))
        except YouTubeApiError as exc:
            if exc.status == 409 or "already" in exc.reason.lower():
                return
            raise

    def _execute(self, request):
        from googleapiclient.errors import HttpError

        delay = 1.0
        for attempt in range(6):
            try:
                return request.execute()
            except HttpError as exc:
                status, reason, message = parse_http_error(exc)
                if status in _RETRYABLE and attempt < 5:
                    self._sleep(delay + random.random())
                    delay *= 2
                    continue
                raise YouTubeApiError(message, status=status, reason=reason) from exc
            except (TimeoutError, ConnectionError, OSError) as exc:
                if attempt < 5:
                    self._sleep(delay)
                    delay *= 2
                    continue
                raise YouTubeApiError(f"сеть оборвалась: {exc}") from exc
        raise YouTubeApiError("YouTube не ответил после нескольких попыток")


def connect(
    token_path: Path,
    client_secret: Path,
    *,
    interactive: bool,
    thumbnail_timeout: float = 600,
    thumbnail_poll: float = 15,
) -> YouTubeClient:
    from googleapiclient.discovery import build

    creds = load_credentials(token_path, client_secret, interactive=interactive)
    service = build("youtube", "v3", credentials=creds)
    return YouTubeClient(
        service,
        thumbnail_timeout=thumbnail_timeout,
        thumbnail_poll=thumbnail_poll,
    )


def parse_http_error(exc) -> tuple[int, str, str]:
    status = int(getattr(getattr(exc, "resp", None), "status", 0) or 0)
    reason = ""
    message = str(exc)
    content = getattr(exc, "content", b"") or b""
    if isinstance(content, bytes):
        try:
            payload = json.loads(content.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict):
            message = error.get("message") or message
            errors = error.get("errors") or []
            if errors and isinstance(errors[0], dict):
                reason = errors[0].get("reason") or ""
                message = errors[0].get("message") or message
    text = f"YouTube API {status}" if status else "YouTube API"
    if reason:
        text += f" ({reason})"
    text += f": {message}"
    return status, reason, text

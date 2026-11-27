"""Ошибки, которые CLI печатает текстом, без трассы."""


class ShortsError(Exception):
    """Ожидаемый сбой: неверная очередь, файл, сеть или ответ YouTube."""


class QueueError(ShortsError):
    """Очередь или соседний yaml с роликом написаны неверно."""


class MediaProbeError(ShortsError):
    """ffprobe не смог прочитать ролик."""


class AuthError(ShortsError):
    """Нет доступа к каналу или токен пора обновить."""


class YouTubeApiError(ShortsError):
    """YouTube отклонил запрос или не успел обработать ролик."""

    def __init__(self, message: str, *, status: int | None = None, reason: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason

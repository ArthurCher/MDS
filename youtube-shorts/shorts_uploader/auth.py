"""Доступ к каналу. Токен лежит локально и в git не попадает."""

from __future__ import annotations

from pathlib import Path

from shorts_uploader.errors import AuthError

# youtube.upload заливает ролик.
# youtube.force-ssl нужен, чтобы прочитать канал, дождаться обработки,
# поставить обложку и добавить ролик в плейлист. Более узкого набора нет.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def load_credentials(token_path: Path, client_secret: Path, *, interactive: bool):
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise AuthError(
                "Google не продлил доступ (для приложения в статусе Testing токен живёт 7 дней). "
                "Запустите ещё раз: python -m shorts_uploader auth"
            ) from exc
        _write_token(token_path, creds)
        return creds
    if not interactive:
        raise AuthError(
            "Нет сохранённого доступа к YouTube. Сначала выполните: python -m shorts_uploader auth"
        )
    if not client_secret.is_file():
        raise AuthError(
            f"Не найден {client_secret}. Скачайте JSON ключа OAuth (Desktop) из Google Cloud "
            "и положите его рядом с командой под именем client_secret.json."
        )
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        raise AuthError(
            "Google не выдал долгоживущий токен. Удалите доступ приложения в аккаунте Google "
            "и запустите auth ещё раз."
        )
    _write_token(token_path, creds)
    return creds


def _write_token(path: Path, creds) -> None:
    path.write_text(creds.to_json(), encoding="utf-8")
    path.chmod(0o600)

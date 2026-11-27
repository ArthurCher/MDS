"""Команды: auth, whoami, validate, upload, status."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from shorts_uploader import __version__
from shorts_uploader.display import render_plan, render_summary
from shorts_uploader.errors import ShortsError
from shorts_uploader.plan import build_plan
from shorts_uploader.queue import load_queue
from shorts_uploader.runner import apply_limit, execute
from shorts_uploader.state import load_state
from shorts_uploader.text import video_url


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except ShortsError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nОстановлено.", file=sys.stderr)
        return 130


def _main(argv: list[str] | None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "auth":
        return _auth(args, interactive=True)
    if args.command == "whoami":
        return _auth(args, interactive=False)
    if args.command == "status":
        return _status(args)
    if args.command == "validate":
        return _queue_command(args, upload=False)
    if args.command == "upload":
        return _queue_command(args, upload=True)
    parser.error(f"неизвестная команда {args.command}")
    return 2


def _queue_command(args, *, upload: bool) -> int:
    queue_path = Path(args.queue)
    queue = load_queue(queue_path)
    state_path = Path(args.state) if args.state else queue.path.parent / "state.json"
    state = load_state(state_path)
    items = build_plan(
        queue,
        state,
        skip_media_check=args.skip_media_check,
        force=args.force,
    )
    if upload:
        apply_limit(items, args.limit)
    print(f"Часовой пояс очереди: {queue.timezone.key}")
    print(render_plan(items, queue.timezone))
    print()
    dry_run = (not upload) or args.dry_run
    if dry_run:
        summary = execute(items, state=state, client=None, dry_run=True)
        print(render_summary(summary, dry_run=True))
        return 0 if summary.ok else 1

    from shorts_uploader.youtube_api import connect

    client = connect(
        Path(args.token),
        Path(args.client_secret),
        interactive=False,
        thumbnail_timeout=args.thumbnail_timeout,
        thumbnail_poll=args.thumbnail_poll,
    )
    channel_id, channel_title = client.channel()
    print(f"Канал: {channel_title} ({channel_id})")
    pending = [item for item in items if item.action in {"upload", "finish"}]
    if pending and sys.stdin.isatty() and not args.yes:
        new_count = sum(1 for item in pending if item.action == "upload")
        finish_count = len(pending) - new_count
        print(f"Новых роликов: {new_count}. Дописать обложки или плейлисты: {finish_count}.")
        try:
            answer = input("Введите «да», чтобы отправить на канал: ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in {"y", "yes", "д", "да"}:
            print("Отменено, на YouTube ничего не отправлено.")
            return 0
    summary = execute(items, state=state, client=client, dry_run=False)
    print()
    print(render_summary(summary, dry_run=False))
    return 0 if summary.ok else 1


def _auth(args, *, interactive: bool) -> int:
    from shorts_uploader.youtube_api import connect

    client = connect(Path(args.token), Path(args.client_secret), interactive=interactive)
    channel_id, channel_title = client.channel()
    if interactive:
        print(f"Доступ сохранён: {Path(args.token).resolve()}")
    print(f"Канал: {channel_title} ({channel_id})")
    print(f"https://www.youtube.com/channel/{channel_id}")
    return 0


def _status(args) -> int:
    state = load_state(Path(args.state))
    if not state.records:
        print("Пока ничего не выложено.")
        return 0
    for record in state.records:
        print(f"{record.uploaded_at}  {record.title}")
        print(f"  {video_url(record.video_id)}")
        notes = []
        if record.thumbnail and not record.thumbnail_set:
            notes.append("обложка ещё не поставлена")
        if record.playlist_id and not record.playlist_added:
            notes.append("в плейлист ещё не добавлен")
        if notes:
            print(f"  {'; '.join(notes)} — запустите upload ещё раз")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shorts-uploader",
        description="Выкладывает YouTube Shorts по очереди и открывает их в заданное время.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    secret = argparse.ArgumentParser(add_help=False)
    secret.add_argument(
        "--client-secret",
        default=os.environ.get("YOUTUBE_CLIENT_SECRET", "client_secret.json"),
        help="JSON ключа OAuth типа Desktop",
    )
    secret.add_argument(
        "--token",
        default=os.environ.get("YOUTUBE_TOKEN", "token.json"),
        help="куда сохранить доступ к каналу",
    )

    queue = argparse.ArgumentParser(add_help=False)
    queue.add_argument("queue", help="путь к queue.yaml")
    queue.add_argument("--state", help="память о заливках; по умолчанию state.json рядом с очередью")
    queue.add_argument(
        "--skip-media-check",
        action="store_true",
        help="не проверять, что ролик вертикальный и короче 3 минут",
    )
    queue.add_argument(
        "--force",
        action="store_true",
        help="залить копию даже если этот файл уже есть на канале",
    )

    commands.add_parser("auth", parents=[secret], help="один раз пустить скрипт на ваш канал")
    commands.add_parser("whoami", parents=[secret], help="показать, в какой канал уйдут ролики")
    commands.add_parser("validate", parents=[queue], help="проверить очередь и ничего не отправлять")

    upload = commands.add_parser("upload", parents=[queue, secret], help="залить то, чего ещё нет на канале")
    upload.add_argument("--dry-run", action="store_true", help="показать план и ничего не отправлять")
    upload.add_argument("--yes", action="store_true", help="не спрашивать подтверждение (так и нужен cron)")
    upload.add_argument("--limit", type=_non_negative, help="сколько новых роликов залить за этот запуск")
    upload.add_argument("--thumbnail-timeout", type=_positive, default=600.0, help="сколько секунд ждать обработку перед обложкой")
    upload.add_argument("--thumbnail-poll", type=_positive, default=15.0, help="пауза между проверками обработки, секунды")

    status = commands.add_parser("status", help="список уже залитых этим скриптом роликов")
    status.add_argument("--state", default="state.json")
    return parser


def _non_negative(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("нужно целое число") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("лимит не может быть отрицательным")
    return number


def _positive(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("нужно число секунд") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("нужно число больше нуля")
    return number

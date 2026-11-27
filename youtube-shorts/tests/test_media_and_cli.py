import json
import shutil
import subprocess
from pathlib import Path

import pytest

from shorts_uploader.cli import main
from shorts_uploader.media import parse_probe_payload, probe_file
from shorts_uploader.youtube_api import parse_http_error

ROOT = Path(__file__).resolve().parents[1]


def test_rotation_metadata_turns_a_landscape_frame_upright():
    info = parse_probe_payload(
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "15.5",
                    "side_data_list": [{"side_data_type": "Display Matrix", "rotation": -90}],
                }
            ]
        }
    )
    assert (info.width, info.height) == (1080, 1920)
    assert info.duration == 15.5

    tagged = parse_probe_payload(
        {"streams": [{"codec_type": "video", "width": 1280, "height": 720, "tags": {"rotate": "90"}}]}
    )
    assert (tagged.width, tagged.height) == (720, 1280)


def test_api_error_exposes_quota_reason():
    class Response:
        class resp:
            status = 403

        content = json.dumps(
            {"error": {"message": "quota", "errors": [{"reason": "quotaExceeded", "message": "quota"}]}}
        ).encode()

    status, reason, text = parse_http_error(Response())
    assert status == 403
    assert reason == "quotaExceeded"
    assert "quotaExceeded" in text


def test_validate_and_dry_run_do_not_need_google(tmp_path, capsys):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"not-a-real-video")
    queue = tmp_path / "queue.yaml"
    queue.write_text(
        f"""
        timezone: Asia/Makassar
        videos:
          - file: {clip.name}
            title: Проверка
        """,
        encoding="utf-8",
    )
    assert main(["validate", str(queue), "--skip-media-check"]) == 0
    printed = capsys.readouterr().out
    assert "Проверка" in printed
    assert "Пробный прогон" in printed
    assert main(["upload", str(queue), "--dry-run", "--skip-media-check", "--limit", "0"]) == 0
    limited = capsys.readouterr().out
    assert "Не влезает в --limit: 1" in limited

    missing = tmp_path / "missing.yaml"
    missing.write_text("videos:\n  - file: no.mp4\n    title: Нет\n", encoding="utf-8")
    assert main(["validate", str(missing)]) == 1


def test_status_mentions_an_unfinished_thumbnail(tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "version": 1,
                "uploads": [
                    {
                        "fingerprint": "abc",
                        "video_id": "xyz",
                        "file": "/tmp/a.mp4",
                        "title": "Уже залито",
                        "uploaded_at": "2026-11-27T06:00:00+00:00",
                        "thumbnail_set": False,
                        "playlist_added": True,
                        "thumbnail": "/tmp/a.jpg",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["status", "--state", str(state)]) == 0
    output = capsys.readouterr().out
    assert "https://www.youtube.com/shorts/xyz" in output
    assert "обложка ещё не поставлена" in output


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="нужен ffmpeg")
def test_ffprobe_accepts_a_real_vertical_clip_and_rejects_horizontal(tmp_path, capsys):
    vertical = tmp_path / "vertical.mp4"
    horizontal = tmp_path / "horizontal.mp4"
    _render(vertical, "320x568")
    _render(horizontal, "568x320")
    info = probe_file(vertical)
    assert info.height > info.width
    assert info.duration is not None and info.duration <= 3

    queue = tmp_path / "queue.yaml"
    queue.write_text(
        """
        videos:
          - file: vertical.mp4
            title: Вертикаль
          - file: horizontal.mp4
            title: Горизонталь
        """,
        encoding="utf-8",
    )
    assert main(["validate", str(queue)]) == 1
    output = capsys.readouterr().out
    assert "Вертикаль" in output
    assert "горизонтальный" in output


def _render(path: Path, size: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=red:s={size}:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-t",
            "1",
            str(path),
        ],
        check=True,
        capture_output=True,
    )

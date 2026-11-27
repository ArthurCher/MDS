from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from shorts_uploader.body import apply_shorts_hashtag, prepare_metadata
from shorts_uploader.errors import QueueError
from shorts_uploader.models import VideoSpec
from shorts_uploader.queue import load_queue
from shorts_uploader.text import tag_char_count, youtube_len

ROOT = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo("Asia/Makassar")
NOW = datetime(2026, 11, 27, 6, 0, tzinfo=timezone.utc)


def _queue(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "queue.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def _spec(**kwargs) -> VideoSpec:
    values = {
        "file": Path("clip.mp4"),
        "title": "Заголовок",
        "privacy": "private",
    }
    values.update(kwargs)
    return VideoSpec(**values)


def test_example_reads_makassar_evening_as_utc_morning():
    queue = load_queue(ROOT / "queue.example.yaml")
    assert queue.timezone == ZONE
    moment = queue.videos[0].publish_at
    assert moment is not None
    local = moment.astimezone(ZONE)
    assert (local.year, local.month, local.day, local.hour, local.minute) == (2027, 1, 15, 18, 0)
    assert moment.astimezone(timezone.utc).hour == 10


def test_unknown_field_is_rejected(tmp_path):
    path = _queue(tmp_path, "videos:\n  - file: a.mp4\n    title: A\n    publsh_at: '2027-01-01 10:00'\n")
    with pytest.raises(QueueError, match="publsh_at"):
        load_queue(path)


def test_relative_paths_and_default_tags(tmp_path):
    clip = tmp_path / "inbox" / "a.mp4"
    clip.parent.mkdir()
    clip.write_bytes(b"video")
    path = _queue(
        tmp_path,
        """
        timezone: Asia/Makassar
        defaults:
          tags: [общие]
          privacy: unlisted
        videos:
          - file: inbox/a.mp4
            title: "Первый"
            tags: [свой]
        """,
    )
    video = load_queue(path).videos[0]
    assert video.file == clip.resolve()
    assert video.tags == ["свой"]
    assert video.privacy == "unlisted"


def test_inbox_sidecar_and_explicit_entry_wins(tmp_path):
    inbox = tmp_path / "inbox" / "week"
    inbox.mkdir(parents=True)
    named = inbox / "my_clip.mp4"
    named.write_bytes(b"one")
    (inbox / "my_clip.yaml").write_text(
        "title: Из файла\npublish_at: '2027-02-01 09:30'\n",
        encoding="utf-8",
    )
    other = inbox / "second.mp4"
    other.write_bytes(b"two")
    path = _queue(
        tmp_path,
        f"""
        inbox: inbox
        videos:
          - file: {other}
            title: Из очереди
        """,
    )
    videos = {item.file: item for item in load_queue(path).videos}
    assert videos[other.resolve()].title == "Из очереди"
    sidecar = videos[named.resolve()]
    assert sidecar.title == "Из файла"
    assert sidecar.publish_at.astimezone(ZONE).hour == 9
    assert sidecar.publish_at.astimezone(ZONE).minute == 30


def test_duplicate_file_is_an_error(tmp_path):
    path = _queue(
        tmp_path,
        """
        videos:
          - file: a.mp4
            title: Раз
          - file: a.mp4
            title: Два
        """,
    )
    with pytest.raises(QueueError, match="дважды"):
        load_queue(path)


def test_hashtag_fits_in_title_or_moves_to_description():
    title, description = apply_shorts_hashtag("Коротко", "", True)
    assert title == "Коротко #Shorts"
    assert description == ""

    long_title = "Я" * 93
    title, description = apply_shorts_hashtag(long_title, "текст", True)
    assert title == long_title
    assert description.endswith("#Shorts")
    assert youtube_len("😀") == 2


def test_tag_limit_counts_commas_and_quotes():
    assert tag_char_count(["Foo-Baz"]) == 7
    assert tag_char_count(["Foo Baz"]) == 9
    assert tag_char_count(["foo", "bar"]) == 7


def test_schedule_becomes_private_and_past_time_is_rejected():
    future = NOW + timedelta(days=3)
    prepared = prepare_metadata(_spec(privacy="public", publish_at=future), now=NOW)
    assert prepared.privacy == "private"
    assert prepared.body["status"]["privacyStatus"] == "private"
    assert prepared.body["status"]["publishAt"].endswith("Z")
    assert prepared.body["status"]["containsSyntheticMedia"] is False
    assert "notifySubscribers" not in prepared.body["status"]
    assert "defaultAudioLanguage" not in prepared.body["snippet"]
    assert not any(issue.level == "warning" for issue in prepared.issues)

    soon = prepare_metadata(_spec(publish_at=NOW + timedelta(minutes=10)), now=NOW)
    assert any("30 минут" in issue.text for issue in soon.issues)

    past = prepare_metadata(_spec(publish_at=NOW - timedelta(hours=1)), now=NOW)
    assert past.body is None
    assert any("прошло" in issue.text for issue in past.issues)

    unlisted = prepare_metadata(_spec(privacy="unlisted", publish_at=future), now=NOW)
    assert unlisted.body is None
    assert any("unlisted" in issue.text for issue in unlisted.issues)


def test_naive_clock_gets_a_timezone_before_compare():
    prepared = prepare_metadata(_spec(), now=datetime(2026, 11, 27, 6, 0))
    assert prepared.body["status"]["privacyStatus"] == "private"
    assert "publishAt" not in prepared.body["status"]

from datetime import datetime, timedelta, timezone
from pathlib import Path

from shorts_uploader.errors import YouTubeApiError
from shorts_uploader.models import MediaInfo
from shorts_uploader.plan import build_plan
from shorts_uploader.queue import load_queue
from shorts_uploader.runner import apply_limit, execute
from shorts_uploader.state import State, load_state

NOW = datetime(2026, 11, 27, 6, 0, tzinfo=timezone.utc)


def vertical(_path):
    return MediaInfo(width=1080, height=1920, duration=20.0, checked=True)


def plan(tmp_path: Path, text: str, state: State | None = None, **kwargs):
    path = tmp_path / "queue.yaml"
    path.write_text(text, encoding="utf-8")
    queue = load_queue(path)
    return build_plan(queue, state or State(tmp_path / "state.json"), now=NOW, probe=kwargs.get("probe", vertical), **{k: v for k, v in kwargs.items() if k != "probe"})


class FakeClient:
    def __init__(self, *, fail_first=None, fail_thumbnail=False):
        self.uploads = []
        self.thumbs = []
        self.playlists = []
        self.fail_first = fail_first
        self.fail_thumbnail = fail_thumbnail
        self.calls = 0

    def upload(self, path, body, on_progress=None):
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise self.fail_first
        if on_progress:
            on_progress(1)
        video_id = f"id{self.calls}"
        self.uploads.append((Path(path).name, body, video_id))
        return video_id

    def wait_until_processed(self, video_id):
        if self.fail_thumbnail:
            raise YouTubeApiError("обработка не дождалась")

    def set_thumbnail(self, video_id, path):
        self.thumbs.append((video_id, Path(path).name))

    def add_to_playlist(self, video_id, playlist_id):
        self.playlists.append((video_id, playlist_id))


def test_horizontal_and_long_videos_do_not_upload(tmp_path):
    (tmp_path / "wide.mp4").write_bytes(b"wide")
    (tmp_path / "long.mp4").write_bytes(b"long")
    items = plan(
        tmp_path,
        """
        videos:
          - file: wide.mp4
            title: Широкий
          - file: long.mp4
            title: Длинный
        """,
        probe=lambda path: MediaInfo(
            1920 if path.name == "wide.mp4" else 1080,
            1080 if path.name == "wide.mp4" else 1920,
            10 if path.name == "wide.mp4" else 181,
            True,
        ),
    )
    assert {item.action for item in items} == {"error"}
    assert any("горизонтальный" in issue.text for item in items for issue in item.issues)
    assert any("3 минут" in issue.text for item in items for issue in item.issues)


def test_sooner_schedule_goes_first_and_limit_defers_the_rest(tmp_path):
    (tmp_path / "late.mp4").write_bytes(b"late")
    (tmp_path / "soon.mp4").write_bytes(b"soon")
    late = (NOW + timedelta(days=5)).isoformat()
    items = plan(
        tmp_path,
        f"""
        timezone: UTC
        videos:
          - file: late.mp4
            title: Позже
            publish_at: '{late}'
          - file: soon.mp4
            title: Раньше
            publish_at: '{(NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+00:00")}'
        """,
    )
    assert [item.title for item in items] == ["Раньше", "Позже"]
    apply_limit(items, 1)
    summary = execute(items, state=State(tmp_path / "state.json"), client=None, dry_run=True)
    assert summary.uploaded == 1
    assert summary.deferred == 1
    assert summary.ok


def test_second_run_skips_and_then_finishes_thumbnail(tmp_path, capsys):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"same-bytes")
    thumb = tmp_path / "cover.jpg"
    thumb.write_bytes(b"jpeg")
    text = """
    videos:
      - file: clip.mp4
        title: Ролик
        thumbnail: cover.jpg
        playlist_id: PLtest
    """
    state_path = tmp_path / "state.json"
    state = State(state_path)
    client = FakeClient(fail_thumbnail=True)
    items = plan(tmp_path, text, state)
    summary = execute(items, state=state, client=client, dry_run=False)
    assert summary.uploaded == 1
    assert summary.failed == 1
    assert client.thumbs == []
    saved = load_state(state_path)
    assert saved.records[0].video_id == "id1"
    assert saved.records[0].thumbnail_set is False

    client.fail_thumbnail = False
    again = plan(tmp_path, text, load_state(state_path))
    assert [item.action for item in again] == ["finish"]
    summary = execute(again, state=load_state(state_path), client=client, dry_run=False)
    assert summary.finished == 1
    assert summary.failed == 0
    assert client.thumbs == [("id1", "cover.jpg")]
    assert client.playlists == [("id1", "PLtest")]
    assert client.uploads == [(clip.name, items[0].body, "id1")]

    third = plan(tmp_path, text, load_state(state_path))
    assert [item.action for item in third] == ["skip"]
    capsys.readouterr()


def test_playlist_added_later_does_not_reupload(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(b"clip")
    state = State(tmp_path / "state.json")
    items = plan(tmp_path, "videos:\n  - file: clip.mp4\n    title: Ролик\n")
    execute(items, state=state, client=FakeClient(), dry_run=False)
    with_list = plan(
        tmp_path,
        "videos:\n  - file: clip.mp4\n    title: Ролик\n    playlist_id: PLnew\n",
        load_state(state.path),
    )
    assert with_list[0].action == "finish"
    client = FakeClient()
    execute(with_list, state=load_state(state.path), client=client, dry_run=False)
    assert client.uploads == []
    assert client.playlists == [("id1", "PLnew")]


def test_quota_stops_the_rest_of_the_queue(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"a")
    (tmp_path / "b.mp4").write_bytes(b"b")
    items = plan(
        tmp_path,
        """
        videos:
          - file: a.mp4
            title: Первый
          - file: b.mp4
            title: Второй
        """,
    )
    client = FakeClient(fail_first=YouTubeApiError("квота", status=403, reason="quotaExceeded"))
    summary = execute(items, state=State(tmp_path / "state.json"), client=client, dry_run=False)
    assert client.calls == 1
    assert summary.failed == 1
    assert summary.deferred == 1
    assert summary.uploaded == 0


def test_ordinary_failure_does_not_block_the_next_video(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"a")
    (tmp_path / "b.mp4").write_bytes(b"b")
    items = plan(
        tmp_path,
        """
        videos:
          - file: a.mp4
            title: Плохой
          - file: b.mp4
            title: Хороший
        """,
    )
    client = FakeClient(fail_first=YouTubeApiError("заголовок", status=400, reason="invalidTitle"))
    summary = execute(items, state=State(tmp_path / "state.json"), client=client, dry_run=False)
    assert summary.failed == 1
    assert summary.uploaded == 1
    assert [name for name, _body, _id in client.uploads] == ["b.mp4"]


def test_missing_file_is_skipped_when_state_remembers_the_path(tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"remember-me")
    state = State(tmp_path / "state.json")
    items = plan(tmp_path, "videos:\n  - file: clip.mp4\n    title: Был\n")
    execute(items, state=state, client=FakeClient(), dry_run=False)
    clip.unlink()
    again = plan(tmp_path, "videos:\n  - file: clip.mp4\n    title: Был\n", load_state(state.path))
    assert again[0].action == "skip"

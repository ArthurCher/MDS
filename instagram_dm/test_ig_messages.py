import json
import os
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timedelta, timezone

from ig_messages import (
    AutoResponder,
    GraphAPIError,
    InstagramClient,
    State,
    load_rules,
)

ME = {"user_id": "100", "username": "shop"}


def ts(hours_ago):
    t = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%S+0000")


def parse(url):
    parts = urllib.parse.urlsplit(url)
    return parts.netloc, parts.path.split("/", 2)[2], dict(urllib.parse.parse_qsl(parts.query))


class FakeGraph:
    """Minimal in-memory Graph API keyed by object id."""

    def __init__(self, objects, host="graph.instagram.com"):
        self.objects = objects
        self.host = host
        self.calls = []
        self.posts = []

    def __call__(self, method, url, body):
        self.calls.append((method, url))
        host, path, q = parse(url)
        assert host == self.host, host
        assert q["access_token"] == "TOKEN"
        if method == "POST":
            self.posts.append((path, body))
            return {"id": f"sent{len(self.posts)}"}
        if q.get("after"):
            path = f"{path}?after={q['after']}"
        if path not in self.objects:
            raise GraphAPIError(f"HTTP 400: unknown object {path}")
        obj = self.objects[path]
        if isinstance(obj, Exception):
            raise obj
        return obj


def inbox_objects(last_from_user_hours_ago=1, text="Сколько стоит?"):
    return {
        "me": ME,
        "me/conversations": {
            "data": [{"id": "c1", "updated_time": ts(last_from_user_hours_ago),
                      "participants": {"data": [{"username": "shop", "id": "100"},
                                                {"username": "alice", "id": "555"}]}}],
            "paging": {"next": "https://graph.instagram.com/v23.0/me/conversations?access_token=TOKEN&after=p2"},
        },
        "me/conversations?after=p2": {
            "data": [{"id": "c2", "updated_time": ts(48),
                      "participants": {"data": [{"username": "bob", "id": "777"}]}}],
        },
        "c1": {"id": "c1", "participants": {"data": [{"username": "shop", "id": "100"},
                                                       {"username": "alice", "id": "555"}]},
               "messages": {"data": [{"id": "m2"}, {"id": "m1"}]}},
        "c2": {"messages": {"data": [{"id": "m_old"}]}},
        "m2": {"id": "m2", "created_time": ts(last_from_user_hours_ago), "message": text,
               "from": {"username": "alice", "id": "555"}},
        "m1": {"id": "m1", "created_time": ts(30), "message": "hi",
               "from": {"username": "shop", "id": "100"}},
        "m_old": GraphAPIError("HTTP 400: too old"),
        "me/media": {"data": []},
    }


def comment_objects(comment_hours_ago=2, replied=False):
    replies = {"data": [{"id": "r1", "username": "shop", "text": "ok"}]} if replied else {"data": []}
    return {
        "me": ME,
        "me/conversations": {"data": []},
        "me/media": {"data": [{"id": "p1", "comments_count": 3}, {"id": "p2", "comments_count": 0}]},
        "p1/comments": {"data": [
            {"id": "k1", "text": "Какая цена?", "username": "carol", "timestamp": ts(comment_hours_ago),
             "replies": replies},
            {"id": "k2", "text": "Красиво!", "username": "dave", "timestamp": ts(1)},
            {"id": "k3", "text": "цена указана в профиле", "username": "shop", "timestamp": ts(1)},
        ]},
    }


RULES = {"rules": [{
    "name": "price",
    "keywords": ["цена", "сколько стоит"],
    "dm": "Прайс: link",
    "comment": "Отправили в Direct",
    "private_reply": "Прайс: link",
}]}


class ReadTests(unittest.TestCase):
    def test_export_follows_pagination_and_tolerates_old_messages(self):
        fake = FakeGraph(inbox_objects())
        data = InstagramClient("TOKEN", transport=fake).export_all()
        self.assertEqual([c["id"] for c in data], ["c1", "c2"])
        self.assertEqual([m["message"] for m in data[0]["messages"]], ["hi", "Сколько стоит?"])
        self.assertIn("error", data[1]["messages"][0])

    def test_facebook_mode_uses_page_and_linked_account(self):
        fake = FakeGraph({
            "123": {"instagram_business_account": {"id": "900", "username": "shop"}},
            "123/conversations": {"data": []},
            "900/media": {"data": [{"id": "p9"}]},
        }, host="graph.facebook.com")
        client = InstagramClient("TOKEN", auth_mode="facebook", page_id="123", transport=fake)
        self.assertEqual(list(client.conversations()), [])
        self.assertEqual(client.recent_media(), [{"id": "p9"}])
        client.private_reply_to_comment("k1", "hi")
        self.assertEqual(fake.posts, [("123/messages", {"recipient": {"comment_id": "k1"}, "message": {"text": "hi"}})])

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            InstagramClient.from_env({})
        with self.assertRaises(ValueError):
            InstagramClient.from_env({"IG_ACCESS_TOKEN": "t", "IG_AUTH_MODE": "facebook"})


class ReplyTests(unittest.TestCase):
    def test_reply_dm_sends_to_other_participant(self):
        fake = FakeGraph(inbox_objects())
        InstagramClient("TOKEN", transport=fake).reply_to_conversation("c1", "Добрый день")
        self.assertEqual(fake.posts, [("me/messages", {"recipient": {"id": "555"}, "message": {"text": "Добрый день"}})])

    def test_reply_dm_refuses_after_24h(self):
        fake = FakeGraph(inbox_objects(last_from_user_hours_ago=25))
        with self.assertRaisesRegex(GraphAPIError, "24-hour"):
            InstagramClient("TOKEN", transport=fake).reply_to_conversation("c1", "late")
        self.assertEqual(fake.posts, [])

    def test_reply_comment_public(self):
        fake = FakeGraph(comment_objects())
        InstagramClient("TOKEN", transport=fake).reply_to_comment("k1", "Спасибо")
        self.assertEqual(fake.posts, [("k1/replies", {"message": "Спасибо"})])


class AutoResponderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        rules_path = os.path.join(self.tmp.name, "rules.json")
        with open(rules_path, "w", encoding="utf-8") as fh:
            json.dump(RULES, fh, ensure_ascii=False)
        self.rules = load_rules(rules_path)
        self.state_path = os.path.join(self.tmp.name, "state.json")

    def tearDown(self):
        self.tmp.cleanup()

    def responder(self, fake, dry_run=False):
        return AutoResponder(InstagramClient("TOKEN", transport=fake), self.rules,
                             State(self.state_path), dry_run=dry_run, log=lambda _: None)

    def test_dm_template_sent_once(self):
        fake = FakeGraph(inbox_objects())
        self.assertEqual(self.responder(fake).run_once(), 1)
        self.assertEqual(fake.posts, [("me/messages", {"recipient": {"id": "555"}, "message": {"text": "Прайс: link"}})])
        self.assertEqual(self.responder(fake).run_once(), 0)
        self.assertEqual(len(fake.posts), 1)

    def test_dm_skipped_without_keyword_or_outside_window(self):
        for objects in (inbox_objects(text="Привет"), inbox_objects(last_from_user_hours_ago=25)):
            fake = FakeGraph(objects)
            self.assertEqual(self.responder(fake).run_once(), 0)
            self.assertEqual(fake.posts, [])

    def test_comment_gets_public_and_private_reply(self):
        fake = FakeGraph(comment_objects())
        self.assertEqual(self.responder(fake).run_once(), 1)
        self.assertEqual(fake.posts, [
            ("k1/replies", {"message": "Отправили в Direct"}),
            ("me/messages", {"recipient": {"comment_id": "k1"}, "message": {"text": "Прайс: link"}}),
        ])
        self.assertEqual(self.responder(fake).run_once(), 0)

    def test_comment_skipped_if_already_answered_or_old(self):
        for objects in (comment_objects(replied=True), comment_objects(comment_hours_ago=30)):
            fake = FakeGraph(objects)
            self.assertEqual(self.responder(fake).run_once(), 0)
            self.assertEqual(fake.posts, [])

    def test_dry_run_sends_nothing(self):
        fake = FakeGraph({**inbox_objects(), **{k: v for k, v in comment_objects().items()
                                                 if k not in ("me/conversations",)}})
        self.assertEqual(self.responder(fake, dry_run=True).run_once(), 2)
        self.assertEqual(fake.posts, [])
        self.assertFalse(os.path.exists(self.state_path))

    def test_rule_without_keywords_rejected(self):
        path = os.path.join(self.tmp.name, "bad.json")
        with open(path, "w") as fh:
            json.dump({"rules": [{"keywords": [], "dm": "spam"}]}, fh)
        with self.assertRaises(ValueError):
            load_rules(path)


if __name__ == "__main__":
    unittest.main()

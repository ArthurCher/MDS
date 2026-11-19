import unittest
import urllib.parse

from ig_messages import GraphAPIError, InstagramMessagesClient


def parse(url):
    parts = urllib.parse.urlsplit(url)
    return parts.netloc, parts.path, dict(urllib.parse.parse_qsl(parts.query))


class FakeGraph:
    def __init__(self):
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        host, path, q = parse(url)
        assert q["access_token"] == "TOKEN"
        if path.endswith("/conversations"):
            assert q["platform"] == "instagram"
            if q.get("after") == "p2":
                return {"data": [{"id": "c2", "updated_time": "2026-11-02"}]}
            return {
                "data": [{"id": "c1", "updated_time": "2026-11-01",
                          "participants": {"data": [{"username": "me"}, {"username": "alice"}]}}],
                "paging": {"next": f"https://{host}{path}?access_token=TOKEN&platform=instagram&after=p2"},
            }
        if path.endswith("/c1"):
            return {"messages": {"data": [{"id": "m2"}, {"id": "m1"}]}}
        if path.endswith("/c2"):
            return {"messages": {"data": [{"id": "m_old"}]}}
        if path.endswith("/m1"):
            return {"id": "m1", "created_time": "2026-11-01T10:00:00+0000", "message": "hi"}
        if path.endswith("/m2"):
            return {"id": "m2", "created_time": "2026-11-01T10:05:00+0000", "message": "hello"}
        if path.endswith("/m_old"):
            raise GraphAPIError("HTTP 400: too old")
        raise AssertionError(f"unexpected url {url}")


class ClientTests(unittest.TestCase):
    def test_instagram_login_export(self):
        fake = FakeGraph()
        client = InstagramMessagesClient("TOKEN", fetch=fake)
        data = client.export_all()

        self.assertEqual([c["id"] for c in data], ["c1", "c2"])
        self.assertEqual([m["message"] for m in data[0]["messages"]], ["hi", "hello"])
        self.assertIn("error", data[1]["messages"][0])
        host, path, _ = parse(fake.calls[0])
        self.assertEqual(host, "graph.instagram.com")
        self.assertEqual(path, "/v23.0/me/conversations")

    def test_facebook_login_uses_page(self):
        fake = FakeGraph()
        client = InstagramMessagesClient("TOKEN", auth_mode="facebook", page_id="123", fetch=fake)
        list(client.conversations())
        host, path, _ = parse(fake.calls[0])
        self.assertEqual(host, "graph.facebook.com")
        self.assertEqual(path, "/v23.0/123/conversations")

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            InstagramMessagesClient.from_env({})
        with self.assertRaises(ValueError):
            InstagramMessagesClient.from_env({"IG_ACCESS_TOKEN": "t", "IG_AUTH_MODE": "facebook"})


if __name__ == "__main__":
    unittest.main()

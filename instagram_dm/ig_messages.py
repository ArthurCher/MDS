"""Export Instagram Direct conversations through the official Graph API.

Works only for Instagram professional accounts (Business or Creator).

Two auth modes are supported:

* ``instagram`` (default) - "Instagram API with Instagram Login".
  Host ``graph.instagram.com``, Instagram user access token with the
  ``instagram_business_basic`` and ``instagram_business_manage_messages``
  permissions. No Facebook Page needed.
* ``facebook`` - "Instagram API with Facebook Login" (Messenger Platform).
  Host ``graph.facebook.com``, Page access token of the Facebook Page linked to
  the Instagram account, with ``instagram_basic``,
  ``instagram_manage_messages`` and ``pages_manage_metadata`` permissions.
  Requires ``IG_PAGE_ID``.

Configuration is read from environment variables (never pass tokens as
command-line arguments):

    IG_ACCESS_TOKEN   required
    IG_AUTH_MODE      instagram | facebook (default: instagram)
    IG_PAGE_ID        required for facebook mode
    IG_API_VERSION    default: v23.0

Usage:

    python ig_messages.py list
    python ig_messages.py export --out messages.json
    python ig_messages.py export --conversation <id> --out one.json

Meta only returns details for the 20 most recent messages of each
conversation; older history is available only via the account data download
in the Instagram app.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterator

DEFAULT_API_VERSION = "v23.0"
HOSTS = {
    "instagram": "https://graph.instagram.com",
    "facebook": "https://graph.facebook.com",
}
MESSAGE_FIELDS = "id,created_time,from,to,message,attachments"

Fetcher = Callable[[str], dict]


class GraphAPIError(RuntimeError):
    pass


def http_get_json(url: str, retries: int = 3) -> dict:
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            try:
                body = json.load(exc)
            except ValueError:
                body = {}
            err = body.get("error", {})
            transient = exc.code >= 500 or err.get("is_transient") or err.get("code") in (4, 17, 32, 613)
            if transient and attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise GraphAPIError(
                f"HTTP {exc.code}: {err.get('message', exc.reason)} "
                f"(code={err.get('code')}, subcode={err.get('error_subcode')}, "
                f"fbtrace_id={err.get('fbtrace_id')})"
            ) from None
        except urllib.error.URLError as exc:
            if attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise GraphAPIError(f"Network error: {exc.reason}") from None
    raise AssertionError("unreachable")


@dataclass
class InstagramMessagesClient:
    access_token: str
    auth_mode: str = "instagram"
    page_id: str | None = None
    api_version: str = DEFAULT_API_VERSION
    fetch: Fetcher = http_get_json

    def __post_init__(self) -> None:
        if self.auth_mode not in HOSTS:
            raise ValueError(f"auth_mode must be one of {sorted(HOSTS)}")
        if self.auth_mode == "facebook" and not self.page_id:
            raise ValueError("IG_PAGE_ID is required for facebook auth mode")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "InstagramMessagesClient":
        env = os.environ if env is None else env
        token = env.get("IG_ACCESS_TOKEN")
        if not token:
            raise ValueError("IG_ACCESS_TOKEN is not set")
        return cls(
            access_token=token,
            auth_mode=env.get("IG_AUTH_MODE", "instagram"),
            page_id=env.get("IG_PAGE_ID"),
            api_version=env.get("IG_API_VERSION", DEFAULT_API_VERSION),
        )

    def _url(self, path: str, **params: str) -> str:
        params["access_token"] = self.access_token
        base = f"{HOSTS[self.auth_mode]}/{self.api_version}/{path.lstrip('/')}"
        return f"{base}?{urllib.parse.urlencode(params)}"

    def _paginate(self, url: str) -> Iterator[dict]:
        while url:
            page = self.fetch(url)
            yield from page.get("data", [])
            url = page.get("paging", {}).get("next")

    def _owner(self) -> str:
        return "me" if self.auth_mode == "instagram" else str(self.page_id)

    def account(self) -> dict:
        if self.auth_mode == "instagram":
            return self.fetch(self._url("me", fields="user_id,username"))
        return self.fetch(self._url(str(self.page_id), fields="instagram_business_account{id,username}"))

    def conversations(self) -> Iterator[dict]:
        url = self._url(
            f"{self._owner()}/conversations",
            platform="instagram",
            fields="id,updated_time,participants",
        )
        yield from self._paginate(url)

    def message_ids(self, conversation_id: str) -> list[str]:
        data = self.fetch(self._url(conversation_id, fields="messages"))
        messages = data.get("messages", {})
        ids = [m["id"] for m in messages.get("data", [])]
        next_url = messages.get("paging", {}).get("next")
        if next_url:
            ids.extend(m["id"] for m in self._paginate(next_url))
        return ids

    def message(self, message_id: str) -> dict:
        return self.fetch(self._url(message_id, fields=MESSAGE_FIELDS))

    def export_conversation(self, conversation: dict) -> dict:
        messages = []
        for mid in self.message_ids(conversation["id"]):
            try:
                messages.append(self.message(mid))
            except GraphAPIError as exc:
                # Meta refuses details for messages beyond the most recent 20.
                messages.append({"id": mid, "error": str(exc)})
        messages.sort(key=lambda m: m.get("created_time", ""))
        return {**conversation, "messages": messages}

    def export_all(self, progress: Callable[[str], None] = lambda _: None) -> list[dict]:
        result = []
        for conv in self.conversations():
            progress(f"conversation {conv['id']}")
            result.append(self.export_conversation(conv))
        return result


def _participants(conv: dict) -> str:
    people = conv.get("participants", {}).get("data", [])
    return ", ".join(p.get("username") or p.get("id", "?") for p in people)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the connected account")
    sub.add_parser("list", help="list conversations")
    export = sub.add_parser("export", help="export conversations with messages to JSON")
    export.add_argument("--conversation", help="export only this conversation id")
    export.add_argument("--out", default="-", help="output file (default: stdout)")
    args = parser.parse_args(argv)

    try:
        client = InstagramMessagesClient.from_env()
        if args.command == "whoami":
            print(json.dumps(client.account(), ensure_ascii=False, indent=2))
        elif args.command == "list":
            for conv in client.conversations():
                print(f"{conv['id']}\t{conv.get('updated_time', '')}\t{_participants(conv)}")
        else:
            log = lambda msg: print(msg, file=sys.stderr)
            if args.conversation:
                data: Any = client.export_conversation({"id": args.conversation})
            else:
                data = client.export_all(progress=log)
            text = json.dumps(data, ensure_ascii=False, indent=2)
            if args.out == "-":
                print(text)
            else:
                with open(args.out, "w", encoding="utf-8") as fh:
                    fh.write(text)
                log(f"saved to {args.out}")
    except (ValueError, GraphAPIError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

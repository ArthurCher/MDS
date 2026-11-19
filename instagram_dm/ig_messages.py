"""Read and answer Instagram Direct messages and comments via the Graph API.

Works only for Instagram professional accounts (Business or Creator).

Two auth modes are supported:

* ``instagram`` (default) - "Instagram API with Instagram Login".
  Host ``graph.instagram.com``, Instagram user access token with the
  ``instagram_business_basic``, ``instagram_business_manage_messages`` and
  ``instagram_business_manage_comments`` permissions. No Facebook Page needed.
* ``facebook`` - "Instagram API with Facebook Login" (Messenger Platform).
  Host ``graph.facebook.com``, Page access token of the Facebook Page linked to
  the Instagram account, with ``instagram_basic``,
  ``instagram_manage_messages``, ``instagram_manage_comments`` and
  ``pages_manage_metadata`` permissions. Requires ``IG_PAGE_ID``.

Configuration is read from environment variables (never pass tokens as
command-line arguments):

    IG_ACCESS_TOKEN   required
    IG_AUTH_MODE      instagram | facebook (default: instagram)
    IG_PAGE_ID        required for facebook mode
    IG_API_VERSION    default: v23.0

Usage:

    python ig_messages.py whoami
    python ig_messages.py inbox
    python ig_messages.py reply-dm <conversation_id> "text"
    python ig_messages.py comments [--media-limit 10]
    python ig_messages.py reply-comment <comment_id> "text" [--private]
    python ig_messages.py auto --templates templates.json [--dry-run] [--watch 300]
    python ig_messages.py export --out messages.json

Meta limits that this tool enforces or works around:

* Direct replies are allowed only within 24 hours of the user's last message.
* A private (Direct) reply to a comment is allowed once, within 7 days.
* Message details are returned only for the 20 most recent messages of each
  conversation.
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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator

DEFAULT_API_VERSION = "v23.0"
HOSTS = {
    "instagram": "https://graph.instagram.com",
    "facebook": "https://graph.facebook.com",
}
MESSAGE_FIELDS = "id,created_time,from,to,message,attachments"
COMMENT_FIELDS = "id,text,timestamp,username,from,replies{id,text,timestamp,username}"
DM_WINDOW = timedelta(hours=24)
PRIVATE_REPLY_WINDOW = timedelta(days=7)
RATE_LIMIT_CODES = (4, 17, 32, 613)

# (method, url, json_body) -> parsed JSON response
Transport = Callable[[str, str, "dict | None"], dict]


class GraphAPIError(RuntimeError):
    pass


def http_request(method: str, url: str, body: dict | None = None, retries: int = 3) -> dict:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            try:
                err = json.load(exc).get("error", {})
            except ValueError:
                err = {}
            rate_limited = err.get("code") in RATE_LIMIT_CODES
            # Writes are retried only when Meta rejected them outright, so a
            # message is never sent twice.
            retryable = rate_limited or (method == "GET" and (exc.code >= 500 or err.get("is_transient")))
            if retryable and attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise GraphAPIError(
                f"HTTP {exc.code}: {err.get('message', exc.reason)} "
                f"(code={err.get('code')}, subcode={err.get('error_subcode')}, "
                f"fbtrace_id={err.get('fbtrace_id')})"
            ) from None
        except urllib.error.URLError as exc:
            if method == "GET" and attempt < retries:
                time.sleep(2 ** attempt * 2)
                continue
            raise GraphAPIError(f"Network error: {exc.reason}") from None
    raise AssertionError("unreachable")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class InstagramClient:
    access_token: str
    auth_mode: str = "instagram"
    page_id: str | None = None
    api_version: str = DEFAULT_API_VERSION
    transport: Transport = http_request
    _me: dict | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.auth_mode not in HOSTS:
            raise ValueError(f"auth_mode must be one of {sorted(HOSTS)}")
        if self.auth_mode == "facebook" and not self.page_id:
            raise ValueError("IG_PAGE_ID is required for facebook auth mode")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "InstagramClient":
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

    def _url(self, path: str, **params: Any) -> str:
        params["access_token"] = self.access_token
        base = f"{HOSTS[self.auth_mode]}/{self.api_version}/{path.lstrip('/')}"
        return f"{base}?{urllib.parse.urlencode(params)}"

    def _get(self, path: str, **params: Any) -> dict:
        return self.transport("GET", self._url(path, **params), None)

    def _post(self, path: str, body: dict) -> dict:
        return self.transport("POST", self._url(path), body)

    def _paginate(self, first_page: dict) -> Iterator[dict]:
        page = first_page
        while True:
            yield from page.get("data", [])
            next_url = page.get("paging", {}).get("next")
            if not next_url:
                return
            page = self.transport("GET", next_url, None)

    def _messaging_owner(self) -> str:
        return "me" if self.auth_mode == "instagram" else str(self.page_id)

    def me(self) -> dict:
        """The connected Instagram account as ``{"id": ..., "username": ...}``."""
        if self._me is None:
            if self.auth_mode == "instagram":
                data = self._get("me", fields="user_id,username")
                self._me = {"id": str(data.get("user_id") or data["id"]), "username": data.get("username")}
            else:
                data = self._get(str(self.page_id), fields="instagram_business_account{id,username}")
                account = data.get("instagram_business_account")
                if not account:
                    raise GraphAPIError("The Facebook Page has no linked Instagram professional account")
                self._me = {"id": str(account["id"]), "username": account.get("username")}
        return self._me

    def is_me(self, user: dict | None) -> bool:
        if not user:
            return False
        me = self.me()
        return user.get("username") == me["username"] or str(user.get("id")) == me["id"]

    # Direct messages

    def conversations(self) -> Iterator[dict]:
        first = self._get(
            f"{self._messaging_owner()}/conversations",
            platform="instagram",
            fields="id,updated_time,participants",
        )
        yield from self._paginate(first)

    def conversation(self, conversation_id: str) -> dict:
        return self._get(conversation_id, fields="id,updated_time,participants")

    def message_ids(self, conversation_id: str) -> list[str]:
        """Message ids of a conversation, newest first."""
        messages = self._get(conversation_id, fields="messages").get("messages", {})
        return [m["id"] for m in self._paginate(messages)]

    def message(self, message_id: str) -> dict:
        return self._get(message_id, fields=MESSAGE_FIELDS)

    def last_message(self, conversation_id: str) -> dict | None:
        messages = self._get(conversation_id, fields="messages").get("messages", {})
        ids = [m["id"] for m in messages.get("data", [])[:1]]
        return self.message(ids[0]) if ids else None

    def other_participant(self, conversation: dict) -> dict | None:
        people = conversation.get("participants", {}).get("data", [])
        return next((p for p in people if not self.is_me(p)), None)

    def send_dm(self, recipient_id: str, text: str) -> dict:
        return self._post(
            f"{self._messaging_owner()}/messages",
            {"recipient": {"id": recipient_id}, "message": {"text": text}},
        )

    def reply_to_conversation(self, conversation_id: str, text: str) -> dict:
        conversation = self.conversation(conversation_id)
        recipient = self.other_participant(conversation)
        if not recipient:
            raise GraphAPIError(f"No recipient found in conversation {conversation_id}")
        last = self.last_message(conversation_id)
        if last and not self.is_me(last.get("from")):
            sent_at = parse_time(last.get("created_time"))
            if sent_at and now_utc() - sent_at > DM_WINDOW:
                raise GraphAPIError(
                    "The 24-hour reply window for this conversation has closed "
                    f"(last message from the user at {last['created_time']})"
                )
        return self.send_dm(str(recipient["id"]), text)

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

    # Comments

    def recent_media(self, limit: int = 10) -> list[dict]:
        owner = "me" if self.auth_mode == "instagram" else self.me()["id"]
        data = self._get(
            f"{owner}/media",
            fields="id,caption,timestamp,permalink,comments_count",
            limit=limit,
        )
        return data.get("data", [])[:limit]

    def comments(self, media_id: str) -> Iterator[dict]:
        yield from self._paginate(self._get(f"{media_id}/comments", fields=COMMENT_FIELDS))

    def has_my_reply(self, comment: dict) -> bool:
        return any(self.is_me(r) for r in comment.get("replies", {}).get("data", []))

    def reply_to_comment(self, comment_id: str, text: str) -> dict:
        return self._post(f"{comment_id}/replies", {"message": text})

    def private_reply_to_comment(self, comment_id: str, text: str) -> dict:
        return self._post(
            f"{self._messaging_owner()}/messages",
            {"recipient": {"comment_id": comment_id}, "message": {"text": text}},
        )

@dataclass
class Rule:
    name: str
    keywords: list[str]
    dm: str | None = None
    comment: str | None = None
    private_reply: str | None = None

    def matches(self, text: str | None) -> bool:
        lowered = (text or "").lower()
        return any(k.lower() in lowered for k in self.keywords)


def load_rules(path: str) -> list[Rule]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rules = []
    for i, item in enumerate(raw.get("rules", [])):
        keywords = [k for k in item.get("keywords", []) if k.strip()]
        if not keywords:
            raise ValueError(f"rule #{i + 1} has no keywords")
        rules.append(Rule(
            name=item.get("name", f"rule{i + 1}"),
            keywords=keywords,
            dm=item.get("dm"),
            comment=item.get("comment"),
            private_reply=item.get("private_reply"),
        ))
    return rules


def find_rule(rules: list[Rule], text: str | None, channel: str) -> Rule | None:
    return next((r for r in rules if getattr(r, channel) and r.matches(text)), None)


class State:
    """Ids of messages and comments already answered, persisted between runs."""

    def __init__(self, path: str):
        self.path = path
        self.handled: set[str] = set()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.handled = set(json.load(fh).get("handled", []))

    def __contains__(self, item_id: str) -> bool:
        return item_id in self.handled

    def add(self, item_id: str) -> None:
        self.handled.add(item_id)
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"handled": sorted(self.handled)}, fh)
        os.replace(tmp, self.path)


@dataclass
class AutoResponder:
    client: InstagramClient
    rules: list[Rule]
    state: State
    dry_run: bool = False
    media_limit: int = 10
    comment_max_age: timedelta = timedelta(hours=24)
    log: Callable[[str], None] = print

    def run_once(self) -> int:
        return self.answer_dms() + self.answer_comments()

    def answer_dms(self) -> int:
        sent = 0
        now = now_utc()
        for conv in self.client.conversations():
            updated = parse_time(conv.get("updated_time"))
            if updated and now - updated > DM_WINDOW:
                continue
            last = self.client.last_message(conv["id"])
            if not last or last["id"] in self.state or self.client.is_me(last.get("from")):
                continue
            sent_at = parse_time(last.get("created_time"))
            if sent_at and now - sent_at > DM_WINDOW:
                continue
            rule = find_rule(self.rules, last.get("message"), "dm")
            if not rule:
                continue
            who = (last.get("from") or {}).get("username", "?")
            self.log(f"DM @{who}: {last.get('message')!r} -> rule '{rule.name}'")
            if not self.dry_run:
                self.client.send_dm(str(last["from"]["id"]), rule.dm)
                self.state.add(last["id"])
            sent += 1
        return sent

    def answer_comments(self) -> int:
        sent = 0
        now = now_utc()
        for media in self.client.recent_media(self.media_limit):
            if not media.get("comments_count"):
                continue
            for comment in self.client.comments(media["id"]):
                if comment["id"] in self.state or self.client.is_me(comment):
                    continue
                posted = parse_time(comment.get("timestamp"))
                if posted and now - posted > self.comment_max_age:
                    continue
                if self.client.has_my_reply(comment):
                    continue
                rule = find_rule(self.rules, comment.get("text"), "comment") or \
                    find_rule(self.rules, comment.get("text"), "private_reply")
                if not rule:
                    continue
                self.log(f"comment @{comment.get('username')}: {comment.get('text')!r} -> rule '{rule.name}'")
                if self.dry_run:
                    sent += 1
                    continue
                if rule.comment:
                    self.client.reply_to_comment(comment["id"], rule.comment)
                if rule.private_reply and (not posted or now - posted <= PRIVATE_REPLY_WINDOW):
                    try:
                        self.client.private_reply_to_comment(comment["id"], rule.private_reply)
                    except GraphAPIError as exc:
                        self.log(f"  private reply failed: {exc}")
                self.state.add(comment["id"])
                sent += 1
        return sent


def _short(text: str | None, width: int = 80) -> str:
    text = (text or "").replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def _message_text(message: dict) -> str:
    if message.get("message"):
        return message["message"]
    return "[attachment]" if message.get("attachments") else "[no text]"


def cmd_inbox(client: InstagramClient, limit: int) -> None:
    now = now_utc()
    for i, conv in enumerate(client.conversations()):
        if i >= limit:
            break
        other = client.other_participant(conv) or {}
        last = client.last_message(conv["id"])
        line = f"{conv['id']}  @{other.get('username', other.get('id', '?'))}"
        if last:
            mine = client.is_me(last.get("from"))
            status = "you" if mine else "them"
            sent_at = parse_time(last.get("created_time"))
            if not mine and sent_at:
                left = DM_WINDOW - (now - sent_at)
                status += f", AWAITING REPLY, {left.total_seconds() / 3600:.1f}h left" if left.total_seconds() > 0 \
                    else ", window closed"
            line += f"\n    [{last.get('created_time')}] ({status}) {_short(_message_text(last))}"
        print(line)


def cmd_comments(client: InstagramClient, media_limit: int, show_all: bool) -> None:
    for media in client.recent_media(media_limit):
        if not media.get("comments_count"):
            continue
        print(f"== {media.get('permalink', media['id'])}  {_short(media.get('caption'), 60)}")
        for comment in client.comments(media["id"]):
            if client.is_me(comment):
                continue
            answered = client.has_my_reply(comment)
            if answered and not show_all:
                continue
            mark = "answered" if answered else "UNANSWERED"
            print(f"  {comment['id']}  @{comment.get('username')} [{comment.get('timestamp')}] ({mark})")
            print(f"      {_short(comment.get('text'))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the connected account")

    inbox = sub.add_parser("inbox", help="conversations with their last message")
    inbox.add_argument("--limit", type=int, default=20)

    reply_dm = sub.add_parser("reply-dm", help="send a Direct message into a conversation")
    reply_dm.add_argument("conversation_id")
    reply_dm.add_argument("text")

    comments = sub.add_parser("comments", help="comments under recent posts (unanswered by default)")
    comments.add_argument("--media-limit", type=int, default=10)
    comments.add_argument("--all", action="store_true", help="include comments you already answered")

    reply_comment = sub.add_parser("reply-comment", help="reply to a comment")
    reply_comment.add_argument("comment_id")
    reply_comment.add_argument("text")
    reply_comment.add_argument("--private", action="store_true", help="reply in Direct instead of publicly")

    auto = sub.add_parser("auto", help="answer new messages and comments using keyword templates")
    auto.add_argument("--templates", required=True)
    auto.add_argument("--state", default=".ig_state.json")
    auto.add_argument("--dry-run", action="store_true", help="only print what would be sent")
    auto.add_argument("--watch", type=int, metavar="SECONDS", help="repeat every SECONDS instead of a single pass")
    auto.add_argument("--media-limit", type=int, default=10)
    auto.add_argument("--comment-max-age-hours", type=float, default=24)

    sub.add_parser("list", help="list conversations")
    export = sub.add_parser("export", help="export conversations with messages to JSON")
    export.add_argument("--conversation", help="export only this conversation id")
    export.add_argument("--out", default="-", help="output file (default: stdout)")
    args = parser.parse_args(argv)

    log = lambda msg: print(msg, file=sys.stderr)
    try:
        client = InstagramClient.from_env()
        if args.command == "whoami":
            print(json.dumps(client.me(), ensure_ascii=False, indent=2))
        elif args.command == "inbox":
            cmd_inbox(client, args.limit)
        elif args.command == "reply-dm":
            print(json.dumps(client.reply_to_conversation(args.conversation_id, args.text)))
        elif args.command == "comments":
            cmd_comments(client, args.media_limit, args.all)
        elif args.command == "reply-comment":
            if args.private:
                result = client.private_reply_to_comment(args.comment_id, args.text)
            else:
                result = client.reply_to_comment(args.comment_id, args.text)
            print(json.dumps(result))
        elif args.command == "auto":
            responder = AutoResponder(
                client=client,
                rules=load_rules(args.templates),
                state=State(args.state),
                dry_run=args.dry_run,
                media_limit=args.media_limit,
                comment_max_age=timedelta(hours=args.comment_max_age_hours),
                log=log,
            )
            while True:
                try:
                    log(f"answered: {responder.run_once()}")
                except GraphAPIError as exc:
                    if not args.watch:
                        raise
                    log(f"error: {exc}")
                if not args.watch:
                    break
                time.sleep(args.watch)
        elif args.command == "list":
            for conv in client.conversations():
                other = client.other_participant(conv) or {}
                print(f"{conv['id']}\t{conv.get('updated_time', '')}\t@{other.get('username', '?')}")
        else:
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
    except (ValueError, OSError, GraphAPIError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

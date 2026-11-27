"""Тело videos.insert: заголовок, расписание и объявление о синтетическом кадре."""

from __future__ import annotations

from datetime import datetime, timedelta

from shorts_uploader.models import (
    DESCRIPTION_LIMIT,
    TAGS_LIMIT,
    TITLE_LIMIT,
    Issue,
    PreparedMetadata,
    VideoSpec,
)
from shorts_uploader.text import tag_char_count, to_rfc3339, youtube_len

_LEAD = timedelta(minutes=30)


def apply_shorts_hashtag(title: str, description: str, enabled: bool) -> tuple[str, str]:
    if not enabled:
        return title, description
    blob = f"{title}\n{description}".lower()
    if "#shorts" in blob:
        return title, description
    with_title = f"{title} #Shorts"
    if youtube_len(with_title) <= TITLE_LIMIT:
        return with_title, description
    return title, f"{description}\n\n#Shorts".strip()


def prepare_metadata(spec: VideoSpec, *, now: datetime) -> PreparedMetadata:
    """Собирает запрос и список замечаний. body пустой, если метаданные нельзя отправлять."""
    issues: list[Issue] = []
    title, description = apply_shorts_hashtag(spec.title, spec.description, spec.append_shorts_hashtag)
    title = title.strip()
    description = description.strip()

    if not title:
        issues.append(Issue("error", "пустой заголовок"))
    elif youtube_len(title) > TITLE_LIMIT:
        issues.append(Issue("error", f"заголовок длиннее {TITLE_LIMIT} символов ({youtube_len(title)})"))

    if youtube_len(description) > DESCRIPTION_LIMIT:
        issues.append(Issue("error", f"описание длиннее {DESCRIPTION_LIMIT} символов"))

    tags = list(spec.tags)
    for tag in tags:
        if "," in tag or any(char in tag for char in "\r\n"):
            issues.append(Issue("error", f"тег «{tag}» содержит запятую или перенос. Разбейте его на отдельные теги"))
    counted = tag_char_count(tags)
    if counted > TAGS_LIMIT:
        issues.append(Issue("error", f"теги длиннее {TAGS_LIMIT} символов ({counted}), вместе с запятыми"))

    privacy = spec.privacy
    publish_at = spec.publish_at
    if publish_at is not None:
        if privacy == "unlisted":
            issues.append(
                Issue(
                    "error",
                    "отложенная публикация не умеет статус unlisted: в указанное время YouTube делает ролик public",
                )
            )
        if publish_at <= now:
            issues.append(
                Issue(
                    "error",
                    "время публикации уже прошло. YouTube в этом случае открывает ролик сразу — укажите будущее время",
                )
            )
        elif privacy != "unlisted":
            if privacy != "private":
                privacy = "private"
            if publish_at < now + _LEAD:
                issues.append(
                    Issue(
                        "warning",
                        "до публикации меньше 30 минут. Если обработка затянется, ролик откроется позже назначенного времени",
                    )
                )

    metadata_broken = any(issue.level == "error" for issue in issues)
    body = None if metadata_broken else _body(spec, title, description, tags, privacy, publish_at)
    return PreparedMetadata(
        title=title,
        description=description,
        privacy=privacy,
        publish_at=publish_at,
        issues=issues,
        body=body,
    )


def _body(
    spec: VideoSpec,
    title: str,
    description: str,
    tags: list[str],
    privacy: str,
    publish_at: datetime | None,
) -> dict:
    snippet: dict = {
        "title": title,
        "description": description,
        "categoryId": spec.category_id,
        "defaultLanguage": spec.default_language,
    }
    if tags:
        snippet["tags"] = tags
    status: dict = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": spec.made_for_kids,
        "embeddable": spec.embeddable,
        "containsSyntheticMedia": spec.synthetic_media,
    }
    if publish_at is not None and privacy == "private":
        status["publishAt"] = to_rfc3339(publish_at)
    return {"snippet": snippet, "status": status}

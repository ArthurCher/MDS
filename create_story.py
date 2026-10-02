#!/usr/bin/env python3
"""
Instagram Stories slide — all-caps modern sans (ref style),
3 tight zones, larger type, darker underlay.
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path

W, H = 1080, 1920
ASSETS = Path("/home/ubuntu/.cursor/projects/workspace/assets")
FONTS = Path("/workspace/story-assets/fonts")
OUT = Path("/workspace/output")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

CREAM = (245, 240, 230)
CREAM_DIM = (220, 214, 202)
GOLD = (222, 180, 88)
GOLD_SOFT = (198, 160, 78)
MUTED = (155, 148, 138)

# All-caps modern sans — Manrope (clean geometric, like ref templates)
font_hook = ImageFont.truetype(str(FONTS / "MR-700.ttf"), 42)
font_accent = ImageFont.truetype(str(FONTS / "MR-700.ttf"), 46)
font_body = ImageFont.truetype(str(FONTS / "MR-600.ttf"), 31)
font_close = ImageFont.truetype(str(FONTS / "MR-700.ttf"), 32)
font_close_em = ImageFont.truetype(str(FONTS / "MR-700.ttf"), 32)
font_label = ImageFont.truetype(str(FONTS / "MR-600.ttf"), 18)
font_handle = ImageFont.truetype(str(FONTS / "MR-600.ttf"), 18)


def cover_crop(img: Image.Image, tw: int, th: int, focus=(0.62, 0.30)) -> Image.Image:
    img = img.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int((nw - tw) * focus[0])
    top = int((nh - th) * focus[1])
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return img.crop((left, top, left + tw, top + th))


def make_underlay(photo: Image.Image, focus) -> Image.Image:
    base = cover_crop(photo, W, H, focus=focus)
    # Darker underlay — text pops harder
    base = ImageEnhance.Brightness(base).enhance(0.48)
    base = ImageEnhance.Color(base).enhance(0.48)
    base = ImageEnhance.Contrast(base).enhance(1.18)

    warm = Image.new("RGB", (W, H), (6, 4, 3))
    base = Image.blend(base, warm, 0.38)
    rgba = base.convert("RGBA")

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for x in range(W):
        t = x / W
        if t < 0.55:
            a = 215
        elif t < 0.75:
            a = int(215 - (t - 0.55) / 0.20 * 130)
        else:
            a = int(85 - (t - 0.75) / 0.25 * 30)
        pd.line([(x, 0), (x, H)], fill=(3, 2, 2, max(40, a)))

    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for y in range(0, 220):
        a = int(120 * (1 - y / 220) ** 1.0)
        vd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(1650, H):
        a = int(160 * ((y - 1650) / (H - 1650)) ** 0.85)
        vd.line([(0, y), (W, y)], fill=(0, 0, 0, min(200, a)))

    out = Image.alpha_composite(rgba, panel)
    out = Image.alpha_composite(out, vig)
    return out.convert("RGB")


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def shadow_text(draw, xy, text, font, fill, offset=2):
    x, y = xy
    draw.text((x + offset, y + offset), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def spaced(draw, text, font, xy, fill, tracking=3, offset=1):
    x, y = xy
    for ch in text:
        shadow_text(draw, (x, y), ch, font, fill, offset=offset)
        x += draw.textlength(ch, font=font) + tracking
    return x


def build(photo_path: Path, out_name: str, focus=(0.62, 0.30)):
    base = make_underlay(Image.open(photo_path), focus)
    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = 58
    content_w = 960
    y = 155

    # ── ZONE 1: header ──────────────────────────────────────────
    spaced(draw, "PERSONAL TRAINER", font_label, (margin, y), MUTED, tracking=5)
    y += 22
    draw.rectangle([margin, y, margin + 40, y + 2], fill=GOLD_SOFT)
    y += 26

    hook_lines = [
        "ЕСЛИ ВЫ УЗНАЁТЕ СЕБЯ",
        "ХОТЯ БЫ В ОДНОМ ПУНКТЕ —",
    ]
    for line in hook_lines:
        shadow_text(draw, (margin, y), line, font_hook, CREAM, offset=2)
        y += 50

    shadow_text(draw, (margin, y), "ВАМ СЮДА", font_accent, GOLD, offset=2)
    aw = draw.textlength("ВАМ СЮДА", font=font_accent)
    draw.rectangle([margin, y + 52, margin + aw, y + 55], fill=GOLD_SOFT)
    y += 72

    # ── ZONE 2: body list — air between lines, compact between items
    bullets = [
        "ХОТИТЕ ИЗМЕНИТЬ ТЕЛО, НО УЖЕ УСТАЛИ ОТ УНИВЕРСАЛЬНЫХ ПРОГРАММ",
        "ЕСТЬ ОГРАНИЧЕНИЯ: КОЛЕНИ, СПИНА, ГРЫЖИ, ВОССТАНОВЛЕНИЕ ПОСЛЕ ОПЕРАЦИЙ",
        "ЛИШНИЙ ВЕС, И ОТ ТИПОВЫХ ПРОГРАММ БОЛЬШЕ ТРЕВОГИ, ЧЕМ ПОЛЬЗЫ: НЕПОНЯТНО, КАК НАГРУЖАТЬСЯ БЕЗ РИСКА",
        "ПОСЛЕ ИЗМЕНЕНИЙ В ОРГАНИЗМЕ (В Т.Ч. ГОРМОНАЛЬНЫЕ ИЗМЕНЕНИЯ) ПРЕЖНИЕ СХЕМЫ ПЕРЕСТАЛИ РАБОТАТЬ",
        "ПРИНИМАЕТЕ ПОДДЕРЖКУ (В Т.Ч. ПЕПТИДЫ) И ХОТИТЕ, ЧТОБЫ НАГРУЗКА И ПИТАНИЕ ЭТО УЧИТЫВАЛИ",
        "НУЖЕН ЧЕЛОВЕК, КОТОРЫЙ ВИДИТ КАРТИНУ ЦЕЛИКОМ: ТРЕНИРОВКИ, ЕДА, АНАЛИЗЫ, САМОЧУВСТВИЕ, РЕЖИМ",
    ]

    line_h = 37   # air inside wrapped lines
    item_gap = 16  # air between points — no giant voids

    for item in bullets:
        lines = wrap_text(item, font_body, content_w - 30, draw)
        draw.rectangle([margin, y + 8, margin + 4, y + 26], fill=GOLD_SOFT)
        tx = margin + 22
        for line in lines:
            shadow_text(draw, (tx, y), line, font_body, CREAM_DIM, offset=1)
            y += line_h
        y += item_gap

    y += 2
    draw.rectangle([margin, y, margin + 40, y + 2], fill=GOLD_SOFT)
    y += 24
    shadow_text(draw, (margin, y), "НЕ «ДЛЯ ИДЕАЛЬНЫХ».", font_close, CREAM, offset=2)
    y += 40
    shadow_text(
        draw,
        (margin, y),
        "ДЛЯ РЕАЛЬНЫХ ЛЮДЕЙ С РЕАЛЬНОЙ ФИЗИОЛОГИЕЙ.",
        font_close_em,
        GOLD,
        offset=2,
    )

    # ── ZONE 3: footer ──────────────────────────────────────────
    handle = "@A.CHEREMISIN_FITNESS"
    total = sum(draw.textlength(ch, font=font_handle) + 3 for ch in handle) - 3
    spaced(
        draw,
        handle,
        font_handle,
        ((W - total) / 2, H - 100),
        MUTED,
        tracking=3,
    )

    final = canvas.convert("RGB")
    for dest in (OUT / out_name, ART / out_name):
        final.save(dest, "PNG")
        print("saved", dest)
    return OUT / out_name


if __name__ == "__main__":
    build(
        ASSETS / "fc132508-741c-4fd8-84fd-e0942788c9f4.jpg",
        "cheremisin_story_slide.png",
        focus=(0.62, 0.30),
    )
    build(
        ASSETS / "a84e4e80-0540-4281-af77-7a25b5ded17f.jpg",
        "cheremisin_story_slide_alt.png",
        focus=(0.58, 0.40),
    )

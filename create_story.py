#!/usr/bin/env python3
"""
Premium Instagram Stories slide.
Dark editorial underlay + Noto Serif Display (high-contrast Didone from refs).
Larger type, even density — air between lines/blocks, no huge empty gaps.
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

CREAM = (244, 236, 220)
CREAM_DIM = (218, 208, 192)
GOLD = (220, 178, 96)
GOLD_SOFT = (196, 158, 84)
MUTED = (138, 132, 122)

NOTO = Path("/usr/share/fonts/truetype/noto")
# Larger, more readable type
font_hook = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 62)
font_hook_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 64)
font_close = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 36)
font_close_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 38)
font_body = ImageFont.truetype(str(FONTS / "MR-500.ttf"), 30)
font_label = ImageFont.truetype(str(FONTS / "MR-600.ttf"), 18)
font_handle = ImageFont.truetype(str(FONTS / "MR-500.ttf"), 17)


def cover_crop(img: Image.Image, tw: int, th: int, focus=(0.65, 0.28)) -> Image.Image:
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

    # Slightly darker than previous pass
    base = ImageEnhance.Brightness(base).enhance(0.68)
    base = ImageEnhance.Color(base).enhance(0.60)
    base = ImageEnhance.Contrast(base).enhance(1.20)

    warm = Image.new("RGB", (W, H), (10, 8, 6))
    base = Image.blend(base, warm, 0.26)
    rgba = base.convert("RGBA")

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for x in range(W):
        t = x / W
        if t < 0.50:
            a = 215
        elif t < 0.72:
            a = int(215 - (t - 0.50) / 0.22 * 150)
        else:
            a = int(65 - (t - 0.72) / 0.28 * 30)
        pd.line([(x, 0), (x, H)], fill=(4, 3, 2, max(20, a)))

    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for y in range(0, 260):
        a = int(120 * (1 - y / 260) ** 1.05)
        vd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(1650, H):
        a = int(165 * ((y - 1650) / (H - 1650)) ** 0.85)
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


def spaced_label(draw, text, font, xy, fill, tracking=5):
    x, y = xy
    for ch in text:
        shadow_text(draw, (x, y), ch, font, fill, offset=1)
        x += draw.textlength(ch, font=font) + tracking
    return x


def build(photo_path: Path, out_name: str, focus=(0.65, 0.28)):
    base = make_underlay(Image.open(photo_path), focus)
    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = 64
    content_w = 720  # wider column → fewer wraps, larger readable lines
    y = 155  # start higher — less empty top

    spaced_label(draw, "PERSONAL TRAINER", font_label, (margin, y), MUTED, tracking=5)
    y += 24
    draw.rectangle([margin, y, margin + 40, y + 2], fill=GOLD_SOFT)
    y += 28

    # Headline — tighter leading, still airy
    for line in ("Если вы узнаёте себя", "хотя бы в одном пункте —"):
        shadow_text(draw, (margin, y), line, font_hook, CREAM, offset=2)
        y += 66

    shadow_text(draw, (margin, y), "вам сюда", font_hook_it, GOLD, offset=2)
    aw = draw.textlength("вам сюда", font=font_hook_it)
    draw.rectangle([margin, y + 68, margin + aw * 0.92, y + 70], fill=GOLD_SOFT)
    y += 84  # was 92 — less empty before list

    bullets = [
        "Хотите изменить тело, но уже устали от универсальных программ",
        "Есть ограничения: колени, спина, грыжи, восстановление после операций",
        "Лишний вес, и от типовых программ больше тревоги, чем пользы: непонятно, как нагружаться без риска",
        "После изменений в организме (в т.ч. гормональные изменения) прежние схемы перестали работать",
        "Принимаете поддержку (в т.ч. пептиды) и хотите, чтобы нагрузка и питание это учитывали",
        "Нужен человек, который видит картину целиком: тренировки, еда, анализы, самочувствие, режим",
    ]

    line_h = 38       # air inside wrapped lines
    block_gap = 14    # air between bullets — not huge

    for item in bullets:
        lines = wrap_text(item, font_body, content_w - 28, draw)
        draw.rectangle([margin, y + 9, margin + 4, y + 26], fill=GOLD_SOFT)
        tx = margin + 22
        for line in lines:
            shadow_text(draw, (tx, y), line, font_body, CREAM_DIM, offset=1)
            y += line_h
        y += block_gap

    y += 4
    draw.rectangle([margin, y, margin + 40, y + 2], fill=GOLD_SOFT)
    y += 22
    shadow_text(draw, (margin, y), "Не «для идеальных».", font_close, CREAM, offset=2)
    y += 44
    # Closing may wrap on one long line — keep as one if fits
    close = "Для реальных людей с реальной физиологией."
    close_lines = wrap_text(close, font_close_it, content_w, draw)
    for line in close_lines:
        shadow_text(draw, (margin, y), line, font_close_it, GOLD, offset=2)
        y += 42

    handle = "@A.CHEREMISIN_FITNESS"
    total = sum(draw.textlength(ch, font=font_handle) + 3 for ch in handle) - 3
    # Place handle closer to content (less empty bottom)
    handle_y = min(H - 96, y + 36)
    spaced_label(draw, handle, font_handle, ((W - total) / 2, handle_y), MUTED, tracking=3)

    final = canvas.convert("RGB")
    for dest in (OUT / out_name, ART / out_name):
        final.save(dest, "PNG")
        print("saved", dest, "content_end_y=", y)
    return OUT / out_name


if __name__ == "__main__":
    build(
        ASSETS / "fc132508-741c-4fd8-84fd-e0942788c9f4.jpg",
        "cheremisin_story_slide.png",
        focus=(0.62, 0.28),
    )
    build(
        ASSETS / "a84e4e80-0540-4281-af77-7a25b5ded17f.jpg",
        "cheremisin_story_slide_alt.png",
        focus=(0.58, 0.40),
    )

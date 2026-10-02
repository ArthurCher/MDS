#!/usr/bin/env python3
"""
Premium Instagram Stories slide.
Dark editorial underlay + Noto Serif Display (high-contrast Didone from refs).
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from pathlib import Path

W, H = 1080, 1920
ASSETS = Path("/home/ubuntu/.cursor/projects/workspace/assets")
FONTS = Path("/workspace/story-assets/fonts")
OUT = Path("/workspace/output")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

CREAM = (244, 236, 220)
CREAM_DIM = (210, 200, 184)
GOLD = (220, 178, 96)
GOLD_SOFT = (196, 158, 84)
MUTED = (138, 132, 122)

# High-contrast Didone display — fashion/editorial look from references
NOTO = Path("/usr/share/fonts/truetype/noto")
font_hook = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 56)
font_hook_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 58)
font_close = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 32)
font_close_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 34)
font_body = ImageFont.truetype(str(FONTS / "MR-500.ttf"), 26)
font_label = ImageFont.truetype(str(FONTS / "MR-600.ttf"), 17)
font_handle = ImageFont.truetype(str(FONTS / "MR-500.ttf"), 16)


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
    """
    Dark story underlay:
    - photo pushed to the right (subject visible)
    - left text column stays deep black
    - overall moody grade, not crushed black
    """
    base = cover_crop(photo, W, H, focus=focus)

    # Keep subject readable, then grade moody (not crushed)
    base = ImageEnhance.Brightness(base).enhance(0.82)
    base = ImageEnhance.Color(base).enhance(0.68)
    base = ImageEnhance.Contrast(base).enhance(1.22)

    # Warm dark blend (editorial) — light touch so photo stays present
    warm = Image.new("RGB", (W, H), (12, 9, 7))
    base = Image.blend(base, warm, 0.18)
    rgba = base.convert("RGBA")

    # Left text panel: deep dark for type; right stays open so YOU are visible
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    for x in range(W):
        t = x / W
        if t < 0.48:
            a = 200
        elif t < 0.68:
            a = int(200 - (t - 0.48) / 0.20 * 155)
        else:
            a = int(45 - (t - 0.68) / 0.32 * 25)
        pd.line([(x, 0), (x, H)], fill=(5, 4, 3, max(12, a)))

    # Soft top/bottom vignette only
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for y in range(0, 280):
        a = int(110 * (1 - y / 280) ** 1.1)
        vd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(1680, H):
        a = int(150 * ((y - 1680) / (H - 1680)) ** 0.9)
        vd.line([(0, y), (W, y)], fill=(0, 0, 0, min(190, a)))

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

    margin = 72
    content_w = 600  # left column — photo visible on right
    y = 195

    spaced_label(draw, "PERSONAL TRAINER", font_label, (margin, y), MUTED, tracking=6)
    y += 26
    draw.rectangle([margin, y, margin + 42, y + 2], fill=GOLD_SOFT)
    y += 40

    # Large Didone headline
    for line in ("Если вы узнаёте себя", "хотя бы в одном пункте —"):
        shadow_text(draw, (margin, y), line, font_hook, CREAM, offset=2)
        y += 62

    # Italic gold accent — magazine emphasis
    shadow_text(draw, (margin, y), "вам сюда", font_hook_it, GOLD, offset=2)
    aw = draw.textlength("вам сюда", font=font_hook_it)
    draw.rectangle([margin, y + 64, margin + aw * 0.92, y + 66], fill=GOLD_SOFT)
    y += 92

    bullets = [
        "Хотите изменить тело, но уже устали от универсальных программ",
        "Есть ограничения: колени, спина, грыжи, восстановление после операций",
        "Лишний вес, и от типовых программ больше тревоги, чем пользы: непонятно, как нагружаться без риска",
        "После изменений в организме (в т.ч. гормональные изменения) прежние схемы перестали работать",
        "Принимаете поддержку (в т.ч. пептиды) и хотите, чтобы нагрузка и питание это учитывали",
        "Нужен человек, который видит картину целиком: тренировки, еда, анализы, самочувствие, режим",
    ]

    for item in bullets:
        lines = wrap_text(item, font_body, content_w - 24, draw)
        draw.rectangle([margin, y + 8, margin + 3, y + 22], fill=GOLD_SOFT)
        tx = margin + 20
        for line in lines:
            shadow_text(draw, (tx, y), line, font_body, CREAM_DIM, offset=1)
            y += 33
        y += 16

    y += 6
    draw.rectangle([margin, y, margin + 42, y + 2], fill=GOLD_SOFT)
    y += 26
    shadow_text(draw, (margin, y), "Не «для идеальных».", font_close, CREAM, offset=2)
    y += 42
    shadow_text(
        draw,
        (margin, y),
        "Для реальных людей с реальной физиологией.",
        font_close_it,
        GOLD,
        offset=2,
    )

    handle = "@A.CHEREMISIN_FITNESS"
    total = sum(draw.textlength(ch, font=font_handle) + 3 for ch in handle) - 3
    spaced_label(draw, handle, font_handle, ((W - total) / 2, H - 108), MUTED, tracking=3)

    final = canvas.convert("RGB")
    for dest in (OUT / out_name, ART / out_name):
        final.save(dest, "PNG")
        print("saved", dest)
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

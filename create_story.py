#!/usr/bin/env python3
"""Instagram Stories slide — refined for a.cheremisin_fitness brand."""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path

W, H = 1080, 1920
ASSETS = Path("/home/ubuntu/.cursor/projects/workspace/assets")
FONTS = Path("/workspace/story-assets/fonts")
OUT = Path("/workspace/output")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

YELLOW = (255, 214, 0)
WHITE = (255, 255, 255)
CREAM = (248, 244, 236)
MUTED = (190, 190, 190)

font_hook = ImageFont.truetype(str(FONTS / "Cormorant-700.ttf"), 62)
font_accent = ImageFont.truetype(str(FONTS / "Cormorant-700.ttf"), 62)
font_body = ImageFont.truetype(str(FONTS / "Montserrat-500.ttf"), 29)
font_label = ImageFont.truetype(str(FONTS / "Montserrat-600.ttf"), 20)
font_close = ImageFont.truetype(str(FONTS / "Montserrat-600.ttf"), 29)
font_close_em = ImageFont.truetype(str(FONTS / "Montserrat-700.ttf"), 31)


def cover_crop(img: Image.Image, tw: int, th: int, focus=(0.55, 0.32)) -> Image.Image:
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


def prepare_bg(photo: Image.Image, focus) -> Image.Image:
    base = cover_crop(photo, W, H, focus=focus)
    # Keep subject a bit brighter
    base = ImageEnhance.Brightness(base).enhance(0.88)
    base = ImageEnhance.Contrast(base).enhance(1.1)
    base = base.convert("RGBA")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Left-weighted dark panel for text (keep right side of subject visible)
    for x in range(0, W):
        # stronger on left 70%, fade to right
        t = x / W
        if t < 0.58:
            side_a = 70
        else:
            side_a = int(70 * (1 - (t - 0.58) / 0.42) ** 1.3)
        d.line([(x, 0), (x, H)], fill=(5, 6, 8, max(0, side_a)))

    # Vertical readability bands
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(0, 520):
        a = int(130 * (1 - y / 520) ** 0.7)
        bd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(480, 1600):
        t = (y - 480) / 1120
        peak = 1 - abs(t - 0.4) * 0.9
        a = int(85 + 55 * max(0, peak))
        bd.line([(0, y), (W, y)], fill=(6, 7, 9, min(155, a)))
    for y in range(1520, H):
        a = int(180 * ((y - 1520) / (H - 1520)) ** 0.8)
        bd.line([(0, y), (W, y)], fill=(0, 0, 0, min(210, a)))

    out = Image.alpha_composite(base, overlay)
    out = Image.alpha_composite(out, band)
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


def build(photo_path: Path, out_name: str, focus=(0.58, 0.30)):
    base = prepare_bg(Image.open(photo_path), focus)
    canvas = base.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    margin = 70
    max_w = W - margin * 2 - 20
    y = 210

    label = "A.CHEREMISIN  ·  FITNESS"
    shadow_text(draw, (margin, y), label, font_label, MUTED, offset=1)
    bbox = draw.textbbox((margin, y), label, font=font_label)
    draw.rectangle([margin, bbox[3] + 6, margin + 108, bbox[3] + 9], fill=YELLOW)
    y = bbox[3] + 28

    for line in ("Если вы узнаёте себя", "хотя бы в одном пункте —"):
        shadow_text(draw, (margin, y), line, font_hook, WHITE, offset=2)
        y += 66

    shadow_text(draw, (margin, y), "вам сюда:", font_accent, YELLOW, offset=2)
    y += 72
    draw.rectangle([margin, y, margin + 56, y + 3], fill=YELLOW)
    y += 34

    bullets = [
        "Хотите изменить тело, но уже устали от универсальных программ",
        "Есть ограничения: колени, спина, грыжи, восстановление после операций",
        "Лишний вес, и от типовых программ больше тревоги, чем пользы: непонятно, как нагружаться без риска",
        "После изменений в организме (в т.ч. гормональные изменения) прежние схемы перестали работать",
        "Принимаете поддержку (в т.ч. пептиды) и хотите, чтобы нагрузка и питание это учитывали",
        "Нужен человек, который видит картину целиком: тренировки, еда, анализы, самочувствие, режим",
    ]

    for item in bullets:
        lines = wrap_text(item, font_body, max_w - 34, draw)
        by = y + 9
        draw.rectangle([margin, by, margin + 5, by + 18], fill=YELLOW)
        tx = margin + 26
        for line in lines:
            shadow_text(draw, (tx, y), line, font_body, CREAM, offset=1)
            y += 37
        y += 20

    y += 8
    draw.rectangle([margin, y, margin + 56, y + 3], fill=YELLOW)
    y += 26
    shadow_text(draw, (margin, y), "Не «для идеальных».", font_close_em, WHITE, offset=2)
    y += 42
    shadow_text(
        draw,
        (margin, y),
        "Для реальных людей с реальной физиологией.",
        font_close,
        YELLOW,
        offset=2,
    )

    handle = "@a.cheremisin_fitness"
    hw = draw.textlength(handle, font=font_label)
    shadow_text(draw, ((W - hw) / 2, H - 118), handle, font_label, MUTED, offset=1)

    final = canvas.convert("RGB")
    for dest in (OUT / out_name, ART / out_name):
        final.save(dest, "PNG")
        print("saved", dest)
    return OUT / out_name


if __name__ == "__main__":
    build(
        ASSETS / "fc132508-741c-4fd8-84fd-e0942788c9f4.jpg",
        "cheremisin_story_slide.png",
        focus=(0.58, 0.30),
    )
    # Bonus alt on beach — more lifestyle
    build(
        ASSETS / "4149701a-c32f-4dfe-91b5-3b1c2202743c.jpg",
        "cheremisin_story_slide_beach.png",
        focus=(0.52, 0.58),
    )

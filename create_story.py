#!/usr/bin/env python3
"""
Instagram Stories slide — filled page, ALL CAPS body, Artur cutout on dark.
"""

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from pathlib import Path

W, H = 1080, 1920
CUTOUTS = Path("/workspace/story-assets/cutouts")
FONTS = Path("/workspace/story-assets/fonts")
NOTO = Path("/usr/share/fonts/truetype/noto")
OUT = Path("/workspace/output")
ART = Path("/opt/cursor/artifacts")
OUT.mkdir(exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

CREAM = (244, 236, 220)
CREAM_DIM = (218, 208, 190)
GOLD = (222, 180, 98)
GOLD_SOFT = (196, 158, 84)
MUTED = (140, 134, 124)

# Headline — high-contrast Didone (premium)
font_hook = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 54)
font_hook_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 56)
font_close = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-Bold.ttf"), 34)
font_close_it = ImageFont.truetype(str(NOTO / "NotoSerifDisplay-BoldItalic.ttf"), 36)
# Body — modern sans ALL CAPS (как в тарифе «ПЛАН»)
font_body = ImageFont.truetype(str(FONTS / "Montserrat-700.ttf"), 33)
font_label = ImageFont.truetype(str(FONTS / "Montserrat-600.ttf"), 18)
font_handle = ImageFont.truetype(str(FONTS / "Montserrat-500.ttf"), 16)


def load_cutout(path: Path, max_h: int = 1500) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    im = im.crop(bbox)
    # scale to height
    ratio = max_h / im.height
    im = im.resize((int(im.width * ratio), max_h), Image.Resampling.LANCZOS)
    # Visible through dark veil — enough presence to fill lower page
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(0.52)
    rgb = ImageEnhance.Color(rgb).enhance(0.42)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.22)
    out = rgb.convert("RGBA")
    out.putalpha(im.split()[-1])
    # soft edge
    alpha = out.split()[-1].filter(ImageFilter.GaussianBlur(0.6))
    out.putalpha(alpha)
    return out


def place_cutout(canvas: Image.Image, cutout: Image.Image, anchor="bottom-center"):
    """Place Artur on the right/lower half so he shows beside/behind type."""
    cw, ch = cutout.size
    if anchor == "bottom-center":
        x = W - cw + 20
        y = H - ch + 60
    elif anchor == "bottom-right":
        x = W - cw + 40
        y = H - ch + 80
    else:
        x, y = 100, H - ch
    # soft glow behind figure
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = cutout.copy()
    # expand alpha for glow
    ga = g.split()[-1].filter(ImageFilter.GaussianBlur(28))
    glow_layer = Image.new("RGBA", g.size, (40, 32, 22, 0))
    glow_layer.putalpha(ga.point(lambda a: min(90, a // 3)))
    glow.paste(glow_layer, (x, y), glow_layer)
    canvas = Image.alpha_composite(canvas, glow)
    canvas.paste(cutout, (x, y), cutout)
    return canvas


def dark_veil(canvas: Image.Image) -> Image.Image:
    """Extra darken so Artur reads through darkness; text stays crisp."""
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(veil)
    # Darker overall; keep mid-lower a bit more open so Artur reads
    d.rectangle([0, 0, W, H], fill=(0, 0, 0, 125))
    for y in range(0, 900):
        a = int(60 * (1 - y / 900) ** 0.7)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    # lighter veil where figure sits (mid-lower)
    for y in range(1100, 1650):
        a = 35
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    for y in range(1650, H):
        a = int(90 * ((y - 1650) / (H - 1650)))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, min(140, a)))
    return Image.alpha_composite(canvas, veil)


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


def build(cutout_path: Path, out_name: str, max_h=1480, anchor="bottom-center"):
    # Near-black base
    canvas = Image.new("RGBA", (W, H), (6, 5, 4, 255))
    cut = load_cutout(cutout_path, max_h=max_h)
    canvas = place_cutout(canvas, cut, anchor=anchor)
    canvas = dark_veil(canvas)

    draw = ImageDraw.Draw(canvas)
    margin = 64
    content_w = W - margin * 2 - 10

    # Flow top → middle → bottom continuously (как разметка: 3 блока без дыр)
    y = 108
    spaced_label(draw, "—  PERSONAL TRAINER", font_label, (margin, y), MUTED, tracking=4)
    y += 28
    for line in ("Если вы узнаёте себя", "хотя бы в одном пункте —"):
        shadow_text(draw, (margin, y), line, font_hook, CREAM, offset=2)
        y += 58
    shadow_text(draw, (margin, y), "вам сюда", font_hook_it, GOLD, offset=2)
    aw = draw.textlength("вам сюда", font=font_hook_it)
    draw.rectangle([margin, y + 60, margin + aw * 0.95, y + 62], fill=GOLD_SOFT)
    y += 68

    bullets = [
        "Хотите изменить тело, но уже устали от универсальных программ",
        "Есть ограничения: колени, спина, грыжи, восстановление после операций",
        "Лишний вес, и от типовых программ больше тревоги, чем пользы: непонятно, как нагружаться без риска",
        "После изменений в организме (в т.ч. гормональные изменения) прежние схемы перестали работать",
        "Принимаете поддержку (в т.ч. пептиды) и хотите, чтобы нагрузка и питание это учитывали",
        "Нужен человек, который видит картину целиком: тренировки, еда, анализы, самочувствие, режим",
    ]

    # Larger type + wrap → taller middle block; comfortable air, no giant gaps
    # Slightly narrower column → more wraps → taller filled middle
    # Left column (~70%) so Artur reads on the right through the dark
    wrapped = [wrap_text(b.upper(), font_body, 720, draw) for b in bullets]
    total_lines = sum(len(w) for w in wrapped)
    # Pack into band ending ~1600 with air, no voids
    target = 1600
    avail = target - y
    n_gaps = len(bullets) - 1
    line_h = 40
    item_gap = max(14, min(22, (avail - total_lines * line_h) // n_gaps))
    # Prefer growing line_h a bit over huge gaps
    while total_lines * line_h + n_gaps * item_gap < avail - 30 and line_h < 44:
        line_h += 1
    item_gap = max(14, min(22, (avail - total_lines * line_h) // n_gaps))
    print(f"layout lines={total_lines} line_h={line_h} gap={item_gap} y0={y}")

    for lines in wrapped:
        draw.rectangle([margin, y + 10, margin + 4, y + 32], fill=GOLD_SOFT)
        tx = margin + 24
        for line in lines:
            shadow_text(draw, (tx, y), line, font_body, CREAM_DIM, offset=1)
            y += line_h
        y += item_gap

    # Closing directly under list (small air) — no empty band
    y += 10
    draw.rectangle([margin, y, margin + 48, y + 2], fill=GOLD_SOFT)
    y += 18
    shadow_text(draw, (margin, y), "Не «для идеальных».", font_close, CREAM, offset=2)
    y += 42
    close2 = "Для реальных людей с реальной физиологией."
    for line in wrap_text(close2, font_close_it, content_w - 40, draw):
        shadow_text(draw, (margin, y), line, font_close_it, GOLD, offset=2)
        y += 40

    print(f"content_end={y}")

    handle = "@A.CHEREMISIN_FITNESS"
    total = sum(draw.textlength(ch, font=font_handle) + 3 for ch in handle) - 3
    # Keep handle close under closing — no dead footer zone
    handle_y = min(H - 90, y + 36)
    spaced_label(draw, handle, font_handle, ((W - total) / 2, handle_y), MUTED, tracking=3)

    final = canvas.convert("RGB")
    for dest in (OUT / out_name, ART / out_name):
        final.save(dest, "PNG")
        print("saved", dest, "final_y", y)
    return OUT / out_name


if __name__ == "__main__":
    # Clean cutout — red beanie (no baked text)
    build(
        CUTOUTS / "cutout_fc132508-741c-4fd8-84fd-e0942788c9f4.png",
        "cheremisin_story_slide.png",
        max_h=1550,
        anchor="bottom-center",
    )
    build(
        CUTOUTS / "cutout_flex_upper.png",
        "cheremisin_story_slide_alt.png",
        max_h=1250,
        anchor="bottom-center",
    )

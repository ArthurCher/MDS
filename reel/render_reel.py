#!/usr/bin/env python3
"""Vertical reel in the reference style: a poster hook, readable subtitles,
and an app-like counter that highlights exercises, sets, and the workout.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
FONTS = ROOT / "fonts"
OUT = ROOT / "out" / "poyasnica-3-uprazhneniya.mp4"

W, H = 1080, 1920
FPS = 30
DUR = 21.0

IVORY = (243, 238, 230)
GOLD = (214, 164, 74)
INK = (10, 10, 10)

# Scene windows, seconds.
HOOK = (0.35, 5.45)
STAT = (5.45, 8.55)
EX = (8.55, 17.55)
END = (17.55, 21.0)
SETS = (
    (8.70, 11.55, "Встань боком к стулу"),
    (11.55, 14.45, "Рука на спинку, тянись в бок"),
    (14.45, 17.55, "Сними напряжение — десять выдохов"),
)


def ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def window(t: float, start: float, end: float, fin: float = 0.32, fout: float = 0.28) -> float:
    if t < start or t >= end:
        return 0.0
    a = 1.0
    if t < start + fin:
        a = ease((t - start) / fin)
    if t > end - fout:
        a = min(a, ease((end - t) / max(fout, 0.001)))
    return a


def appear(t: float, start: float, dur: float = 0.42) -> tuple[float, float]:
    if t < start:
        return 0.0, 22.0
    u = min(1.0, (t - start) / dur)
    e = ease(u)
    return e, 22.0 * (1 - e)


def rgba(rgb: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
    return (rgb[0], rgb[1], rgb[2], int(max(0.0, min(1.0, a)) * 255))


def load_font(name: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / name), size)
    font.set_variation_by_axes([weight])
    return font


def text_width(font: ImageFont.FreeTypeFont, text: str, tracking: float = 0) -> float:
    if tracking == 0 or len(text) < 2:
        return font.getlength(text)
    return sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: float,
    y: float,
    font: ImageFont.FreeTypeFont,
    fill,
    tracking: float = 0,
    align: str = "left",
) -> float:
    width = text_width(font, text, tracking)
    if align == "center":
        x -= width / 2
    elif align == "right":
        x -= width
    cursor = x
    for ch in text:
        draw.text((cursor, y), ch, font=font, fill=fill)
        cursor += font.getlength(ch) + tracking
    return width


def font_top(font: ImageFont.FreeTypeFont, text: str) -> int:
    return font.getbbox(text)[1]


def cover_base(image: Image.Image, zoom: float) -> Image.Image:
    scale = max(W / image.width, H / image.height) * zoom
    size = (max(W, int(image.width * scale)), max(H, int(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def frame_from_base(base: Image.Image, zoom: float, max_zoom: float, fx: float, fy: float) -> Image.Image:
    bw, bh = base.size
    cw = max(W, int(round(W * max_zoom / zoom)))
    ch = max(H, int(round(H * max_zoom / zoom)))
    cw = min(cw, bw)
    ch = min(ch, bh)
    x = int((bw - cw) * fx)
    y = int((bh - ch) * fy)
    x = max(0, min(bw - cw, x))
    y = max(0, min(bh - ch, y))
    crop = base.crop((x, y, x + cw, y + ch))
    if crop.size != (W, H):
        crop = crop.resize((W, H), Image.Resampling.LANCZOS)
    return crop


def paint_wall(image: Image.Image, box: tuple[int, int, int, int], color: tuple[int, int, int], feather: int = 16) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rectangle(box, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather))
    solid = Image.new("RGB", image.size, color)
    return Image.composite(solid, image, mask)


def clean_chair(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB").crop((0, 360, 1206, 2320))
    wall = (233, 236, 236)
    # Ghost captions from the reference screenshot: counter, title, "или".
    image = paint_wall(image, (860, 100, 1088, 205), wall, 14)
    image = paint_wall(image, (560, 175, 1120, 285), wall, 16)
    image = paint_wall(image, (900, 700, 1088, 830), wall, 14)
    image = ImageEnhance.Contrast(image).enhance(1.04)
    image = ImageEnhance.Color(image).enhance(0.94)
    return image


def feather_paste(image: Image.Image, box: tuple[int, int, int, int], patch: Image.Image) -> None:
    bw, bh = box[2] - box[0], box[3] - box[1]
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((10, 8, bw - 10, bh - 8), radius=10, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    region = image.crop(box).convert("RGBA")
    merged = Image.composite(patch.convert("RGBA"), region, mask)
    image.paste(merged.convert("RGB"), (box[0], box[1]))


def clean_portrait(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB").crop((0, 120, 1206, 2320))
    gray = image.convert("L")
    px = gray.load()
    w, h = image.size
    # Only the burned-in word on the shirt. The cap is white too, so the
    # window stays on the lower chest.
    pts = []
    for y in range(int(h * 0.64), int(h * 0.74)):
        for x in range(int(w * 0.58), int(w * 0.92)):
            if px[x, y] > 220:
                pts.append((x, y))
    if len(pts) > 40:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        box = (min(xs) - 14, min(ys) - 12, max(xs) + 16, max(ys) + 14)
        bw, bh = box[2] - box[0], box[3] - box[1]
        src = (box[0], box[1] - bh - 12, box[2], box[1] - 12)
        if src[1] > int(h * 0.45) and bh < 160:
            patch = image.crop(src).resize((bw, bh), Image.Resampling.BICUBIC)
            feather_paste(image, box, patch)
    # Small Instagram control in the corner, not the whole side of the frame.
    pts = []
    px = image.convert("L").load()
    for y in range(int(h * 0.90), h - 2, 2):
        for x in range(int(w * 0.84), w - 4, 2):
            if px[x, y] > 210:
                pts.append((x, y))
    if 8 < len(pts) < 1500:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        color = image.getpixel((max(0, min(xs) - 36), max(0, min(ys) - 8)))
        pad = 18
        ImageDraw.Draw(image).ellipse(
            (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad),
            fill=color,
        )
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Color(image).enhance(0.9)
    image = ImageEnhance.Brightness(image).enhance(0.92)
    return image


def vertical_gradient(strength: int = 150) -> Image.Image:
    column = Image.new("L", (1, H), 0)
    pix = column.load()
    for y in range(H):
        u = y / (H - 1)
        if u < 0.38:
            a = 0.0
        elif u < 0.74:
            a = (u - 0.38) / 0.36
        else:
            a = 1.0
        pix[0, y] = int((a ** 1.15) * strength)
    return column.resize((W, H))


def vignette_mask(amount: float = 0.45) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((-140, -100, W + 140, H + 180), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(100))
    return ImageChops.invert(mask).point(lambda p: int(p * amount))


def apply_shade(image: Image.Image, mask: Image.Image) -> Image.Image:
    black = Image.new("RGB", image.size, (6, 6, 6))
    return Image.composite(black, image, mask)


class Assets:
    def __init__(self) -> None:
        portrait = clean_portrait(SRC / "portrait.jpg")
        chair = clean_chair(SRC / "chair.jpg")
        self.portrait = cover_base(portrait, 1.12)
        self.chair = cover_base(chair, 1.10)
        self.shade = vertical_gradient(150)
        self.vignette = vignette_mask(0.42)
        self.vignette_soft = vignette_mask(0.22)
        blurred = portrait.filter(ImageFilter.GaussianBlur(26))
        blurred = ImageEnhance.Brightness(blurred).enhance(0.5)
        blurred = ImageEnhance.Color(blurred).enhance(0.75)
        self.end_base = cover_base(blurred, 1.08)

        self.hook_big = load_font("Oswald.ttf", 176, 700)
        self.hook_mid = load_font("Oswald.ttf", 78, 500)
        self.hook_found = load_font("Oswald.ttf", 112, 600)
        self.script = load_font("Caveat.ttf", 132, 700)
        self.stat_num = load_font("Oswald.ttf", 280, 600)
        self.stat_label = load_font("Oswald.ttf", 64, 500)
        self.ui_num = load_font("Oswald.ttf", 92, 600)
        self.ui_den = load_font("Oswald.ttf", 40, 500)
        self.set_num = load_font("Oswald.ttf", 148, 600)
        self.end_num = load_font("Oswald.ttf", 132, 600)
        self.sub = load_font("Manrope.ttf", 42, 650)
        self.sub_sm = load_font("Manrope.ttf", 36, 650)
        self.caption = load_font("Manrope.ttf", 34, 600)
        self.body = load_font("Manrope.ttf", 32, 600)
        self.small = load_font("Manrope.ttf", 22, 600)
        self.tiny = load_font("Manrope.ttf", 18, 700)
        self.chip = load_font("Manrope.ttf", 28, 650)


def background(assets: Assets, t: float) -> Image.Image:
    photo_a = ease(min(1.0, t / 0.45))
    if t < 8.35:
        u = t / 8.35
        frame = frame_from_base(assets.portrait, 1.12 - 0.07 * u, 1.12, 0.50, 0.42 + 0.06 * u)
        frame = apply_shade(frame, assets.shade)
    elif t < 8.95:
        u = (t - 8.35) / 0.60
        a = frame_from_base(assets.portrait, 1.05, 1.12, 0.50, 0.48)
        a = apply_shade(a, assets.shade)
        b = frame_from_base(assets.chair, 1.04, 1.10, 0.48, 0.42)
        frame = Image.blend(a, b, ease(u))
    elif t < 17.25:
        u = (t - 8.95) / (17.25 - 8.95)
        frame = frame_from_base(assets.chair, 1.04 + 0.05 * u, 1.10, 0.48, 0.40 + 0.04 * u)
    elif t < 17.85:
        u = ease((t - 17.25) / 0.60)
        a = frame_from_base(assets.chair, 1.09, 1.10, 0.48, 0.44)
        b = frame_from_base(assets.end_base, 1.04, 1.08, 0.50, 0.45)
        frame = Image.blend(a, b, u)
    else:
        u = (t - 17.85) / (DUR - 17.85)
        frame = frame_from_base(assets.end_base, 1.04 + 0.03 * u, 1.08, 0.50, 0.45)
    frame = apply_shade(frame, assets.vignette if t < 8.5 or t >= 17.2 else assets.vignette_soft)
    if photo_a < 1:
        frame = Image.blend(Image.new("RGB", (W, H), (8, 8, 8)), frame, photo_a)
    if t > DUR - 0.45:
        frame = Image.blend(frame, Image.new("RGB", (W, H), (8, 8, 8)), ease((t - (DUR - 0.45)) / 0.45))
    return frame


def pill(overlay: Image.Image, text: str, cx: float, cy: float, font: ImageFont.FreeTypeFont, alpha: float) -> None:
    if alpha <= 0.01:
        return
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 32, 18
    width, height = tw + pad_x * 2, th + pad_y * 2
    x, y = cx - width / 2, cy - height / 2
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((x, y, x + width, y + height), radius=height / 2, fill=rgba(INK, 0.72 * alpha))
    draw.text((x + pad_x - bbox[0], y + pad_y - bbox[1]), text, font=font, fill=rgba(IVORY, alpha))


def glow_text(
    overlay: Image.Image,
    text: str,
    x: float,
    y: float,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    alpha: float,
    blur: int = 18,
) -> None:
    if alpha <= 0.01:
        return
    bbox = font.getbbox(text)
    pad = blur * 3
    layer = Image.new("RGBA", (bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=rgba(fill, 1))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    r, g, b, a = layer.split()
    a = a.point(lambda p: int(p * 0.55 * alpha))
    layer = Image.merge("RGBA", (r, g, b, a))
    overlay.alpha_composite(layer, (int(x - pad), int(y - pad)))
    ImageDraw.Draw(overlay).text((x, y), text, font=font, fill=rgba(fill, alpha))


def draw_hook(overlay: Image.Image, assets: Assets, t: float) -> None:
    group = window(t, *HOOK, 0.28, 0.34)
    if group <= 0:
        return
    draw = ImageDraw.Draw(overlay)
    line1 = "7 ЛЕТ"
    # Match the second line to the width of the hero line so the stack is a block.
    hero_w = text_width(assets.hook_big, line1)
    phrase = "НАЗАД У МЕНЯ"
    raw = assets.hook_mid.getlength(phrase)
    tracking = max(0.0, min(16.0, (hero_w - raw) / (len(phrase) - 1)))

    top = 918  # below the lavalier, over the chest, face stays clear
    # Stagger.
    a1, y1 = appear(t, 0.55)
    a2, y2 = appear(t, 0.82)
    a3, y3 = appear(t, 1.05)
    a4, y4 = appear(t, 1.32)
    a5, _ = appear(t, 1.62, 0.36)

    cursor_y = top
    draw_tracked(draw, line1, W / 2, cursor_y + y1, assets.hook_big, rgba(IVORY, group * a1), align="center")
    cursor_y += 176 + 6
    draw_tracked(
        draw,
        phrase,
        W / 2,
        cursor_y + y2,
        assets.hook_mid,
        rgba(IVORY, group * a2),
        tracking=tracking,
        align="center",
    )
    cursor_y += 78 + 2
    draw_tracked(draw, "НАШЛИ", W / 2, cursor_y + y3, assets.hook_found, rgba(IVORY, group * a3), align="center")
    cursor_y += 108
    script = "3 грыжи"
    sw = assets.script.getlength(script)
    glow_text(overlay, script, (W - sw) / 2, cursor_y + y4 - 18, assets.script, GOLD, group * a4, blur=16)
    pill(overlay, "В пояснично-крестцовом отделе", W / 2, cursor_y + 176, assets.sub, group * a5)


def draw_stat(overlay: Image.Image, assets: Assets, t: float) -> None:
    group = window(t, *STAT, 0.30, 0.30)
    if group <= 0:
        return
    draw = ImageDraw.Draw(overlay)
    a1, y1 = appear(t, 5.60, 0.36)
    a2, y2 = appear(t, 5.78, 0.40)
    a3, y3 = appear(t, 6.05, 0.36)
    a4, _ = appear(t, 6.35, 0.36)

    draw_tracked(
        draw,
        "ПРОГРАММА",
        W / 2,
        690 + y1,
        assets.tiny,
        rgba(IVORY, 0.72 * group * a1),
        tracking=8,
        align="center",
    )
    num = "3"
    nw = assets.stat_num.getlength(num)
    glow_text(overlay, num, (W - nw) / 2, 760 + y2, assets.stat_num, GOLD, group * a2, blur=22)
    draw_tracked(
        draw,
        "УПРАЖНЕНИЯ",
        W / 2,
        1060 + y3,
        assets.stat_label,
        rgba(IVORY, group * a3),
        tracking=6,
        align="center",
    )
    meta = "3 подхода   ·   1 тренировка"
    # Draw with the digits in gold. Split around the words.
    parts = [("3", True), (" подхода    ·    ", False), ("1", True), (" тренировка", False)]
    widths = []
    font = assets.chip
    for text, _gold in parts:
        widths.append(font.getlength(text))
    total = sum(widths)
    x = (W - total) / 2
    y = 1188 + y3
    for (text, gold), width in zip(parts, widths):
        draw.text((x, y), text, font=font, fill=rgba(GOLD if gold else IVORY, group * a3 * (1 if gold else 0.78)))
        x += width
    pill(overlay, "Коротко. Каждый день.", W / 2, 1360, assets.sub, group * a4)


def elevation(overlay: Image.Image, box: tuple[float, float, float, float], radius: float, alpha: float) -> None:
    if alpha <= 0.01:
        return
    x0, y0, x1, y1 = box
    pad = 28
    width, height = int(x1 - x0 + pad * 2), int(y1 - y0 + pad * 2)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (pad, pad + 10, pad + (x1 - x0), pad + 10 + (y1 - y0)),
        radius=radius,
        fill=(0, 0, 0, int(150 * alpha)),
    )
    overlay.alpha_composite(layer.filter(ImageFilter.GaussianBlur(14)), (int(x0 - pad), int(y0 - pad)))


def glass(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], radius: float, alpha: float) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=rgba((16, 15, 13), 0.92 * alpha))


def draw_exercise(overlay: Image.Image, assets: Assets, t: float) -> None:
    group = window(t, *EX, 0.34, 0.32)
    if group <= 0:
        return
    draw = ImageDraw.Draw(overlay)
    a_head, y_head = appear(t, 8.75, 0.40)
    a_card, y_card = appear(t, 8.95, 0.42)
    ha = group * a_head
    ca = group * a_card

    # Which set is on screen.
    set_index = 1
    subtitle = SETS[0][2]
    set_t0 = SETS[0][0]
    for i, (t0, t1, line) in enumerate(SETS, start=1):
        if t0 <= t < t1:
            set_index = i
            subtitle = line
            set_t0 = t0
            break
    local = window(t, set_t0, set_t0 + 2.9, 0.18, 0.16)

    chip = (500, 188 + y_head, 1008, 470 + y_head)
    elevation(overlay, chip, 28, ha)
    glass(draw, chip, 28, ha)
    draw_tracked(draw, "УПРАЖНЕНИЕ", 536, 214 + y_head, assets.tiny, rgba(IVORY, 0.62 * ha), tracking=6)
    num_y = 248 + y_head
    glow_text(overlay, "01", 532, num_y, assets.ui_num, GOLD, ha, blur=12)
    den_x = 532 + assets.ui_num.getlength("01") + 14
    den_y = num_y + 40
    draw.text((den_x, den_y), "/  03", font=assets.ui_den, fill=rgba(IVORY, 0.78 * ha))
    draw.text((536, 392 + y_head), "Растяжка со стулом", font=assets.caption, fill=rgba(IVORY, ha))

    card_y = 1452 + y_card
    card = (64, card_y, 1016, card_y + 400)
    elevation(overlay, card, 32, ca)
    glass(draw, card, 32, ca)
    draw.rounded_rectangle((64, card_y + 36, 70, card_y + 364), radius=3, fill=rgba(GOLD, ca))
    draw_tracked(draw, "ПОДХОД", 108, card_y + 32, assets.tiny, rgba(IVORY, 0.62 * ca), tracking=6)

    pop = 1.0
    dt = t - set_t0
    if 0 <= dt < 0.36:
        u = dt / 0.36
        pop = 1 + 0.12 * (1 - u) * (1 - (2 * u - 1) ** 2)

    digit = str(set_index)
    bbox = assets.set_num.getbbox(digit)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    glyph = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
    ImageDraw.Draw(glyph).text((4 - bbox[0], 4 - bbox[1]), digit, font=assets.set_num, fill=rgba(GOLD, ca))
    if abs(pop - 1) > 0.01:
        glyph = glyph.resize((max(1, int(glyph.width * pop)), max(1, int(glyph.height * pop))), Image.Resampling.LANCZOS)
    gx = int(108 - (glyph.width - tw) / 2)
    gy = int(card_y + 78 - (glyph.height - th) / 2)
    overlay.alpha_composite(glyph, (gx, gy))

    of_y = card_y + 158
    draw.text((108 + tw + 22, of_y), "из", font=assets.body, fill=rgba(IVORY, 0.72 * ca))
    draw.text((108 + tw + 22 + assets.body.getlength("из "), of_y), "3", font=assets.body, fill=rgba(GOLD, ca))

    dots_x, dots_y = 108, card_y + 250
    for i in range(3):
        cx = dots_x + i * 28
        if i < set_index:
            draw.ellipse((cx, dots_y, cx + 12, dots_y + 12), fill=rgba(GOLD, ca))
        else:
            draw.ellipse((cx, dots_y, cx + 12, dots_y + 12), outline=rgba(IVORY, 0.4 * ca), width=2)

    draw.text((108, card_y + 286), subtitle, font=assets.sub, fill=rgba(IVORY, ca * local))


def draw_end(overlay: Image.Image, assets: Assets, t: float) -> None:
    group = window(t, *END, 0.32, 0.30)
    if group <= 0:
        return
    draw = ImageDraw.Draw(overlay)
    a0, y0 = appear(t, 17.70, 0.34)
    rows = (
        ("3", "упражнения", 17.82),
        ("9", "подходов", 18.00),
        ("1", "тренировка", 18.18),
    )
    draw_tracked(
        draw,
        "СЕГОДНЯ",
        W / 2,
        560 + y0,
        assets.tiny,
        rgba(IVORY, 0.7 * group * a0),
        tracking=8,
        align="center",
    )
    y = 660
    for digit, label, start in rows:
        a, dy = appear(t, start, 0.36)
        alpha = group * a
        nw = assets.end_num.getlength(digit)
        glow_text(overlay, digit, 250, y + dy, assets.end_num, GOLD, alpha, blur=16)
        draw.text((250 + nw + 28, y + dy + 48), label, font=assets.stat_label, fill=rgba(IVORY, alpha))
        y += 210
    pill(overlay, "Поясница. Каждый день.", W / 2, 1380, assets.sub, group * appear(t, 18.40, 0.3)[0])


def render_frame(assets: Assets, t: float) -> Image.Image:
    frame = background(assets, t).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hook(overlay, assets, t)
    draw_stat(overlay, assets, t)
    draw_exercise(overlay, assets, t)
    draw_end(overlay, assets, t)
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def main() -> None:
    assets = Assets()
    if "--stills" in sys.argv:
        out_dir = Path("/tmp/reel-stills")
        out_dir.mkdir(parents=True, exist_ok=True)
        times = [0.2, 2.4, 4.8, 6.8, 10.2, 12.4, 15.4, 19.0]
        for t in times:
            render_frame(assets, t).save(out_dir / f"t{t:.1f}.jpg", quality=86)
            print("still", t)
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "high",
        "-crf",
        "17",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        str(OUT),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(DUR * FPS)
    assert proc.stdin is not None
    try:
        for i in range(frames):
            frame = render_frame(assets, i / FPS)
            proc.stdin.write(frame.tobytes())
            if i % 30 == 0:
                print(f"{i}/{frames}", flush=True)
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise SystemExit(code)
    print("wrote", OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Instagram feed post slide — «Для кого это» for @a.cheremisin_fitness"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1350  # Instagram feed 4:5
YELLOW = (255, 229, 0)
WHITE = (255, 255, 255)
SOFT = (235, 235, 235)
MUTED = (170, 170, 170)

ROOT = Path("/workspace")
FONTS = ROOT / "fonts"
OUT = ROOT / "output"
ART = Path("/opt/cursor/artifacts/screenshots")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def cover_crop(img: Image.Image, size: tuple[int, int], focus=(0.5, 0.28)) -> Image.Image:
    tw, th = size
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int((nw - tw) * focus[0])
    top = int((nh - th) * focus[1])
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return img.crop((left, top, left + tw, top + th))


def draw_text_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill,
    shadow=(0, 0, 0),
    blur_offsets=((2, 2), (3, 4), (0, 3)),
):
    x, y = xy
    for ox, oy in blur_offsets:
        draw.text((x + ox, y + oy), text, font=font, fill=(*shadow, 180) if len(shadow) == 3 else shadow)
    draw.text(xy, text, font=font, fill=fill)


def wrap_lines(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)

    bg = Image.open(ROOT / "post/bg-volcano.jpg").convert("RGB")
    bg = cover_crop(bg, (W, H), focus=(0.55, 0.18))
    bg = ImageEnhance.Contrast(bg).enhance(1.1)
    bg = ImageEnhance.Color(bg).enhance(1.08)
    bg = ImageEnhance.Brightness(bg).enhance(1.06)

    # Dark overlays: keep face visible on the right, text-safe on left/bottom
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        t = y / H
        if t < 0.16:
            a = int(95 + 25 * (t / 0.16))
        elif t < 0.42:
            a = int(70 + 35 * ((t - 0.16) / 0.26))
        else:
            a = int(130 + 100 * ((t - 0.42) / 0.58))
        a = min(238, a)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    side = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(side)
    for x in range(W):
        t = x / W
        # stronger left, lighter over face (right-center)
        if t < 0.55:
            a = int(120 * (1 - t / 0.55))
        else:
            a = int(35 * ((t - 0.55) / 0.45))
        if a:
            sd.line([(x, 0), (x, H)], fill=(0, 0, 0, a))
    overlay = Image.alpha_composite(overlay, side)

    canvas = Image.alpha_composite(bg.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)

    font_eyebrow = load_font("Montserrat-Bold.ttf", 22)
    font_title_w = load_font("Montserrat-Black.ttf", 78)
    font_title_y = load_font("Montserrat-Black.ttf", 78)
    font_lead = load_font("Montserrat-SemiBold.ttf", 26)
    font_body = load_font("Montserrat-Medium.ttf", 25)
    font_close = load_font("Caveat.ttf", 42)
    font_meta = load_font("Montserrat-SemiBold.ttf", 18)

    # Eyebrow
    y = 48
    draw_text_shadow(draw, (52, y), "@A.CHEREMISIN_FITNESS", font_eyebrow, YELLOW)
    y += 42

    # Title
    draw_text_shadow(draw, (52, y), "ДЛЯ КОГО", font_title_w, WHITE)
    y += 74
    draw_text_shadow(draw, (52, y), "ЭТО", font_title_y, YELLOW)
    y += 84

    # Lead
    lead = "Если вы узнаёте себя хотя бы в одном пункте — вам сюда:"
    lead_lines = wrap_lines(lead, font_lead, W - 110, draw)
    for i, line in enumerate(lead_lines):
        # highlight "одном пункте"
        if "одном пункте" in line:
            before, _, after = line.partition("одном пункте")
            x = 52
            if before:
                draw_text_shadow(draw, (x, y), before, font_lead, SOFT)
                x += int(draw.textlength(before, font=font_lead))
            draw_text_shadow(draw, (x, y), "одном пункте", font_lead, YELLOW)
            x += int(draw.textlength("одном пункте", font=font_lead))
            if after:
                draw_text_shadow(draw, (x, y), after, font_lead, SOFT)
        else:
            draw_text_shadow(draw, (52, y), line, font_lead, SOFT)
        y += 34
    y += 18

    bullets = [
        "Хотите изменить тело, но уже устали от универсальных программ",
        "Есть ограничения: колени, спина, грыжи, восстановление после операций",
        "Лишний вес, и от типовых программ больше тревоги, чем пользы: непонятно, как нагружаться без риска",
        "После изменений в организме (в т.ч. гормональные изменения) прежние схемы перестали работать",
        "Принимаете поддержку (в т.ч. пептиды) и хотите, чтобы нагрузка и питание это учитывали",
        "Нужен человек, который видит картину целиком: тренировки, еда, анализы, самочувствие, режим",
    ]

    # Soft panel behind list for readability (subtle, not a heavy card)
    panel_top = y - 16
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    # estimate panel height later after measuring — draw after measuring
    # First measure content height
    measure_y = y
    line_gap = 6
    item_gap = 14
    max_text_w = W - 52 - 52 - 28
    measured_blocks = []
    for b in bullets:
        lines = wrap_lines(b, font_body, max_text_w, draw)
        measured_blocks.append(lines)
        measure_y += len(lines) * (27 + line_gap) - line_gap + item_gap
    measure_y += 14  # divider
    close1 = "Не «для идеальных»."
    close2 = "Для реальных людей с реальной физиологией."
    measure_y += 46 + 42 + 26
    panel_bottom = min(H - 36, measure_y + 10)

    pd.rounded_rectangle(
        (36, panel_top, W - 36, panel_bottom),
        radius=26,
        fill=(0, 0, 0, 95),
        outline=(255, 229, 0, 70),
        width=2,
    )
    canvas = Image.alpha_composite(canvas, panel)
    draw = ImageDraw.Draw(canvas)

    # Bullets
    for lines in measured_blocks:
        cy = y + 11
        draw.ellipse((52, cy - 5, 52 + 11, cy + 6), fill=YELLOW)
        tx = 52 + 26
        for j, line in enumerate(lines):
            draw_text_shadow(draw, (tx, y), line, font_body, WHITE, blur_offsets=((1, 1), (2, 2)))
            y += 27 + (line_gap if j < len(lines) - 1 else 0)
        y += item_gap

    # Divider + closing
    y += 2
    draw.line((52, y, W - 52, y), fill=(255, 229, 0), width=2)
    y += 16
    draw_text_shadow(draw, (52, y), close1, font_close, YELLOW)
    y += 44
    draw_text_shadow(draw, (52, y), close2, font_close, YELLOW)
    y += 48
    draw_text_shadow(draw, (52, y), "POST · SLIDE 02", font_meta, MUTED, blur_offsets=((1, 1),))

    final = canvas.convert("RGB")
    png_path = OUT / "post-slide-2-dlya-kogo.png"
    jpg_path = OUT / "post-slide-2-dlya-kogo.jpg"
    final.save(png_path, optimize=True)
    final.save(jpg_path, quality=94, optimize=True)
    final.save(ART / "post-slide-2-dlya-kogo.jpg", quality=94)

    # QA crops
    for name, box in [
        ("top", (0, 0, W, 450)),
        ("mid", (0, 450, W, 900)),
        ("bot", (0, 900, W, H)),
    ]:
        final.crop(box).save(ART / f"post-qa-{name}.jpg", quality=92)

    print(f"Saved {png_path} {final.size}")
    print(f"Saved {jpg_path}")


if __name__ == "__main__":
    main()

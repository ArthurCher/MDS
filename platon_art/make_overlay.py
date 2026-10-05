#!/usr/bin/env python3
"""Neon hand-drawn graphic overlay on Platon's photo (photo pixels untouched)."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "platon_source.jpg"
OUT = ROOT / "platon_neon_overlay.jpg"
OUT_PREVIEW = ROOT / "platon_neon_overlay_preview.jpg"
MASK_CACHE = ROOT / "silhouette_mask.png"
PTS_CACHE = ROOT / "landmarks.json"
SHIRT_CACHE = ROOT / "shirt_mask.png"

LIME = (180, 255, 40)  # RGB neon lime
ACCENT = LIME
TEXT = "THE BEST LOOKS ARE THE ONES YOU FEEL AMAZING"
BG_WORD = "Platon"
BG_COLOR = (236, 236, 234)  # light off-white like the reference
BG_TEXT_COLOR = (28, 28, 28)
# Previous stroke widths were 30 / 12 — doubled per request
OUTLINE_WIDTH = 60
OUTLINE_WIDTH_INNER = 24
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def load_font(size: int) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def segment_subject(bgr: np.ndarray) -> np.ndarray:
    if MASK_CACHE.exists():
        return cv2.imread(str(MASK_CACHE), cv2.IMREAD_GRAYSCALE)

    try:
        from rembg import remove
        from PIL import Image as PILImage

        rgba = np.array(
            remove(PILImage.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)))
        )
        mask = (rgba[:, :, 3] > 128).astype(np.uint8) * 255
    except Exception:
        border = np.concatenate(
            [
                bgr[0:20].reshape(-1, 3),
                bgr[-20:].reshape(-1, 3),
                bgr[:, 0:20].reshape(-1, 3),
                bgr[:, -20:].reshape(-1, 3),
            ]
        )
        bg = np.median(border, axis=0)
        diff = np.linalg.norm(bgr.astype(np.float32) - bg, axis=2)
        mask = (diff > 28).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8))
    if n > 1:
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        mask = ((labels == largest).astype(np.uint8)) * 255

    h, w = mask.shape
    flood = mask.copy()
    ff = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, ff, (0, 0), 255)
    mask = cv2.bitwise_or(mask, cv2.bitwise_not(flood))
    cv2.imwrite(str(MASK_CACHE), mask)
    return mask


def detect_landmarks(bgr: np.ndarray, mask: np.ndarray) -> dict:
    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    if not PTS_CACHE.exists():
        upper = np.zeros((h, w), np.uint8)
        upper[: int(h * 0.45)] = 255
        red = cv2.inRange(hsv, (0, 120, 100), (10, 255, 255)) | cv2.inRange(
            hsv, (170, 120, 100), (180, 255, 255)
        )
        red = cv2.bitwise_and(red, upper)
        red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(red)
        idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        band = (labels == idx).astype(np.uint8) * 255
        dens = band.sum(axis=1)
        rows = np.where(dens >= dens.max() * 0.35)[0]
        ys, xs = np.where(band > 0)
        bx0, bx1 = int(xs.min()), int(xs.max())
        by0, by1 = int(rows.min()), int(rows.max())

        eye_y0, eye_y1 = by1 + 40, by1 + 280
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        strip = gray[eye_y0:eye_y1, bx0:bx1].astype(np.float32)
        invb = cv2.GaussianBlur(255 - strip, (31, 15), 0)
        col = cv2.GaussianBlur(invb.max(axis=0).reshape(1, -1), (1, 51), 0).ravel()
        mid = len(col) // 2
        lx = int(np.argmax(col[:mid]))
        rx = mid + int(np.argmax(col[mid:]))
        left_eye = (bx0 + lx, eye_y0 + int(np.argmax(invb[:, lx])))
        right_eye = (bx0 + rx, eye_y0 + int(np.argmax(invb[:, rx])))

        ear_y = (by0 + by1) // 2 + 30
        cols = np.where(mask[ear_y] > 0)[0]
        cols = cols[(cols < bx1 + 100) & (cols > bx0 - 100)]
        pts = {
            "left_eye": [left_eye[0], left_eye[1], 110, 60],
            "right_eye": [right_eye[0], right_eye[1], 110, 60],
            "left_ear": [int(cols.min()) + 25, ear_y + 80],
            "right_ear": [int(cols.max()) - 25, ear_y + 50],
            "bandana": [bx0, by0, bx1, by1],
        }
        PTS_CACHE.write_text(json.dumps(pts, indent=2))
    else:
        pts = json.loads(PTS_CACHE.read_text())

    # Shirt / torso fill region for star pattern
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    by1 = pts["bandana"][3]
    shirt = (
        ((sat < 85) & (val > 130) & (mask > 0))
        | ((gray > 145) & (mask > 0) & (sat < 90))
    ).astype(np.uint8) * 255
    shirt[: by1 + 160] = 0
    shirt[int(h * 0.72) :] = 0
    mid_y = by1 + int((h - by1) * 0.25)
    cols = np.where(mask[mid_y] > 0)[0]
    if len(cols):
        lx, rx = int(cols.min()), int(cols.max())
        pad = int((rx - lx) * 0.12)
        shirt[:, : lx + pad] = 0
        shirt[:, rx - pad :] = 0
    # Keep stars off the lower face / hand-on-chin area
    le, re = pts["left_eye"], pts["right_eye"]
    shirt[: by1 + 280, le[0] - 80 : re[0] + 120] = 0
    shirt = cv2.morphologyEx(shirt, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    shirt = cv2.morphologyEx(shirt, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    cv2.imwrite(str(SHIRT_CACHE), shirt)
    return pts


def largest_contour(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(contours, key=cv2.contourArea)


def resample_contour(contour: np.ndarray, n: int = 1600) -> np.ndarray:
    pts = contour.reshape(-1, 2).astype(np.float64)
    d = np.sqrt(((np.roll(pts, -1, axis=0) - pts) ** 2).sum(axis=1))
    s = np.concatenate([[0], np.cumsum(d)])
    total = float(s[-1])
    samples = np.linspace(0, total, n, endpoint=False)
    x = np.interp(samples, s[:-1], pts[:, 0])
    y = np.interp(samples, s[:-1], pts[:, 1])
    k = 15
    x = np.convolve(np.pad(x, (k // 2, k // 2), mode="wrap"), np.ones(k) / k, mode="valid")
    y = np.convolve(np.pad(y, (k // 2, k // 2), mode="wrap"), np.ones(k) / k, mode="valid")
    return np.stack([x, y], axis=1)


def outward_normals(pts: np.ndarray) -> np.ndarray:
    tang = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
    normals = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-6
    center = pts.mean(axis=0)
    if np.mean(((center - pts) * normals).sum(axis=1)) > 0:
        normals = -normals
    return normals


def cumdist(pts: np.ndarray) -> tuple[np.ndarray, float]:
    d = np.sqrt(((np.roll(pts, -1, axis=0) - pts) ** 2).sum(axis=1))
    s = np.concatenate([[0], np.cumsum(d[:-1])])
    return s, float(s[-1] + d[-1])


def point_at(pts: np.ndarray, s: np.ndarray, dist: float) -> tuple[np.ndarray, np.ndarray]:
    total = float(s[-1] + np.linalg.norm(pts[0] - pts[-1]))
    dist = dist % total
    idx = int(np.searchsorted(s, dist) - 1)
    idx = max(0, min(idx, len(pts) - 2))
    seg = pts[idx + 1] - pts[idx]
    seg_len = np.linalg.norm(seg) + 1e-6
    t = (dist - s[idx]) / seg_len
    pos = pts[idx] * (1 - t) + pts[idx + 1] * t
    tang = seg / seg_len
    return pos, tang


def draw_thick_path(
    draw: ImageDraw.ImageDraw,
    pts: np.ndarray,
    color: tuple[int, int, int],
    width: int,
    skip: set[int] | None = None,
) -> None:
    """Draw polyline, optionally skipping index ranges (for text gaps)."""
    n = len(pts)
    run: list[tuple[float, float]] = []
    for i in range(n + 1):
        idx = i % n
        if skip and idx in skip:
            if len(run) > 1:
                draw.line(run, fill=color + (255,), width=width, joint="curve")
            run = []
            continue
        run.append((float(pts[idx, 0]), float(pts[idx, 1])))
    if len(run) > 1:
        draw.line(run, fill=color + (255,), width=width, joint="curve")


def draw_text_integrated(
    overlay: Image.Image,
    path: np.ndarray,
    text: str,
    color: tuple[int, int, int],
    font_size: int = 58,
) -> set[int]:
    """Place blocky caps on the silhouette path; return contour indices to skip for stroke."""
    draw = ImageDraw.Draw(overlay)
    font = load_font(font_size)
    s, total = cumdist(path)
    normals = outward_normals(path)

    # Start just left of the crown (top) and run clockwise down the left side then under —
    # reference wraps text around the upper silhouette.
    top = int(np.argmin(path[:, 1]))
    # Rotate so top is index 0
    path_r = np.vstack([path[top:], path[:top]])
    s, total = cumdist(path_r)
    normals_r = np.vstack([normals[top:], normals[:top]])

    # Use ~55% of perimeter starting slightly past the absolute top toward the left shoulder
    # Contour orientation: check whether index+ goes left or right from top
    if path_r[10, 0] > path_r[0, 0]:
        # increasing index goes right — reverse so text runs over left side first
        path_r = path_r[::-1]
        normals_r = -normals_r[::-1]
        s, total = cumdist(path_r)

    start_dist = total * 0.02
    chars = list(text)
    # Character advance
    advances = []
    for ch in chars:
        bbox = font.getbbox(ch if ch != " " else "i")
        advances.append(max(bbox[2] - bbox[0], font_size * 0.45) * (1.08 if ch != " " else 0.55))

    needed = sum(advances)
    max_len = total * 0.62
    while needed > max_len and len(chars) > 8:
        chars.pop()
        advances.pop()
        needed = sum(advances)

    skip_idx: set[int] = set()
    cursor = start_dist
    # Map rotated index back to original for skip — approximate via nearest point
    for ch, adv in zip(chars, advances):
        if ch != " ":
            pos, tang = point_at(path_r, s, cursor + adv * 0.45)
            ang = math.degrees(math.atan2(tang[1], tang[0]))
            # Keep letters sitting on the stroke (slight outward nudge)
            idx = int(np.searchsorted(s, cursor + adv * 0.45) - 1)
            idx = max(0, min(idx, len(path_r) - 1))
            nrm = normals_r[idx]
            pos = pos + nrm * 2

            glyph = Image.new("RGBA", (font_size * 3, font_size * 3), (0, 0, 0, 0))
            gdraw = ImageDraw.Draw(glyph)
            # slight hand-drawn size jitter
            local_font = load_font(int(font_size * random.uniform(0.92, 1.08)))
            gdraw.text(
                (font_size, font_size * 0.7),
                ch,
                font=local_font,
                fill=color + (255,),
            )
            rotated = glyph.rotate(-ang, resample=Image.BICUBIC, expand=True)
            overlay.alpha_composite(
                rotated,
                (int(pos[0] - rotated.width / 2), int(pos[1] - rotated.height / 2)),
            )

            # mark nearby original contour points to thin the stroke under letters
            # find nearest in original path
            d2 = ((path[:, 0] - pos[0]) ** 2 + (path[:, 1] - pos[1]) ** 2)
            nearest = int(np.argmin(d2))
            for k in range(-6, 7):
                skip_idx.add((nearest + k) % len(path))

        cursor += adv

    return skip_idx


def draw_eye_lashes(
    draw: ImageDraw.ImageDraw,
    eye: tuple[int, int],
    color: tuple[int, int, int],
    scale: float = 1.0,
) -> None:
    ex, ey = eye
    # Dramatic upward fan (reference "lashes")
    n = 8
    spread = math.radians(85)
    base = -math.pi / 2
    for i in range(n):
        a = base - spread / 2 + spread * i / (n - 1) + random.uniform(-0.04, 0.04)
        L = 110 * scale * random.uniform(0.8, 1.2)
        x1 = ex + math.cos(a) * 22 * scale
        y1 = ey - 8 * scale + math.sin(a) * 6
        x2 = ex + math.cos(a) * L
        y2 = ey + math.sin(a) * L
        draw.line([(x1, y1), (x2, y2)], fill=color + (255,), width=max(6, int(11 * scale)))
        r = int(9 * scale)
        draw.ellipse([x2 - r, y2 - r, x2 + r, y2 + r], fill=color + (255,))

    # Drop marks under eye
    for i, dx in enumerate((-22, -2, 20)):
        x = ex + dx * scale
        y0 = ey + 38 * scale
        drop = [
            (x, y0),
            (x + 8 * scale, y0 + 14 * scale),
            (x, y0 + 30 * scale),
            (x - 8 * scale, y0 + 14 * scale),
        ]
        draw.line(drop + [drop[0]], fill=color + (255,), width=5)


def draw_eye_bursts(
    draw: ImageDraw.ImageDraw,
    eye: tuple[int, int],
    color: tuple[int, int, int],
) -> None:
    ex, ey = eye
    for cx, cy, size in ((ex - 8, ey - 58, 40), (ex + 18, ey + 52, 30)):
        for i in range(6):
            a = i * math.pi / 3 + random.uniform(-0.08, 0.08)
            L = size * random.uniform(0.75, 1.15)
            draw.line(
                [(cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L)],
                fill=color + (255,),
                width=5,
            )
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color + (255,))


def draw_paisley(
    draw: ImageDraw.ImageDraw,
    anchor: tuple[int, int],
    color: tuple[int, int, int],
    scale: float = 1.2,
    flip: bool = False,
) -> None:
    ax, ay = anchor
    s = scale
    sign = -1 if flip else 1
    # Outer paisley
    outer = []
    for t in np.linspace(0, 2 * math.pi, 100):
        # teardrop leaning
        r = (62 + 34 * math.sin(t) ** 2 * (1.1 + 0.4 * math.cos(t))) * s
        x = sign * r * math.sin(t) * 0.72
        y = -r * math.cos(t) * 1.05 + 55 * s
        outer.append((ax + x, ay + y))
    draw.line(outer + [outer[0]], fill=color + (255,), width=int(9 * s), joint="curve")

    # Inner ornamental loops
    inner = []
    for t in np.linspace(0.15, 2 * math.pi - 0.15, 70):
        r = (34 + 16 * math.sin(t) ** 2) * s
        x = sign * r * math.sin(t) * 0.6
        y = -r * math.cos(t) * 0.95 + 55 * s
        inner.append((ax + x, ay + y))
    draw.line(inner, fill=color + (255,), width=int(5 * s), joint="curve")

    # Henna-like dots and curls
    for i in range(10):
        t = 0.5 + i * 0.22
        r = (14 + i * 2.2) * s
        px = ax + sign * math.sin(t) * r
        py = ay + 55 * s - math.cos(t) * r
        rad = max(3, int(4.5 * s))
        draw.ellipse([px - rad, py - rad, px + rad, py + rad], outline=color + (255,), width=3)

    # Decorative spiral
    spiral = []
    for i in range(40):
        ang = i * 0.35
        r = (4 + i * 0.9) * s
        spiral.append(
            (
                ax + sign * (18 * s + r * math.cos(ang)),
                ay + 70 * s + r * math.sin(ang),
            )
        )
    draw.line(spiral, fill=color + (255,), width=int(4 * s), joint="curve")

    # Ear hook
    draw.line(
        [
            (ax, ay - 10),
            (ax + sign * 6 * s, ay + 16 * s),
            (ax, ay + 40 * s),
        ],
        fill=color + (255,),
        width=int(7 * s),
        joint="curve",
    )


def draw_star(draw, cx, cy, r, color, width=5):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5 + random.uniform(-0.03, 0.03)
        rad = r if i % 2 == 0 else r * 0.4
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    draw.line(pts + [pts[0]], fill=color + (255,), width=width, joint="curve")


def draw_sparkle(draw, cx, cy, r, color):
    for a in (0, math.pi / 2, math.pi / 4, -math.pi / 4):
        L = r if abs(math.sin(2 * a)) < 0.1 else r * 0.65
        draw.line(
            [(cx - math.cos(a) * L, cy - math.sin(a) * L), (cx + math.cos(a) * L, cy + math.sin(a) * L)],
            fill=color + (255,),
            width=4 if L == r else 3,
        )


def fill_stars(draw, shirt_mask, color, seed=7):
    rng = random.Random(seed)
    ys, xs = np.where(shirt_mask > 0)
    if len(xs) < 50:
        return
    placed = []
    for _ in range(2500):
        if len(placed) >= 36:
            break
        i = rng.randrange(len(xs))
        x, y = float(xs[i]), float(ys[i])
        size = rng.choice([16, 20, 26, 32, 40, 48, 56])
        if any((x - px) ** 2 + (y - py) ** 2 < (max(size, gap) * 1.7) ** 2 for px, py, gap in placed):
            continue
        placed.append((x, y, size))
        if rng.random() < 0.62:
            draw_star(draw, x, y, size, color, width=5 if size > 28 else 4)
        else:
            draw_sparkle(draw, x, y, size * 0.6, color)


def inflate_path(pts: np.ndarray, px: float) -> np.ndarray:
    return pts + outward_normals(pts) * px


def make_platon_text_background(w: int, h: int, mask: np.ndarray) -> Image.Image:
    """Dense outlined 'Platon' fill behind the subject, like the reference."""
    del mask  # subject is composited on top; fill the full canvas
    bg = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(bg)

    base_size = max(48, int(w * 0.042))
    word = BG_WORD
    stroke = max(2, base_size // 16)
    rng = random.Random(19)

    # Measure nominal glyph box
    probe = load_font(base_size)
    bb0 = probe.getbbox(word)
    gap_x = int((bb0[2] - bb0[0]) * 0.10)
    gap_y = int((bb0[3] - bb0[1]) * 0.14)

    y = -int((bb0[3] - bb0[1]) * 0.25)
    row = 0
    while y < h + base_size:
        size = int(base_size * rng.uniform(0.94, 1.06))
        row_font = load_font(size)
        bb = row_font.getbbox(word)
        ww = max(bb[2] - bb[0], 1)
        wh = max(bb[3] - bb[1], 1)
        x = -int(ww * (0.4 if row % 2 else 0.05))
        while x < w + ww:
            # Hollow outlined letters: fill = background, dark stroke
            draw.text(
                (x + rng.uniform(-1.2, 1.2), y + rng.uniform(-0.8, 0.8)),
                word,
                font=row_font,
                fill=BG_COLOR,
                stroke_width=stroke,
                stroke_fill=BG_TEXT_COLOR,
            )
            x += ww + gap_x
        y += wh + gap_y
        row += 1

    return bg.convert("RGBA")


def cutout_subject(rgb: np.ndarray, mask: np.ndarray) -> Image.Image:
    """Subject pixels only; photo itself is not recolored."""
    # Slight feather so the cutout sits cleanly on the text background
    blur = cv2.GaussianBlur(mask, (5, 5), 0)
    rgba = np.dstack([rgb, blur])
    return Image.fromarray(rgba, mode="RGBA")


def build_overlay(bgr: np.ndarray, mask: np.ndarray, pts: dict) -> Image.Image:
    h, w = bgr.shape[:2]
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    contour = largest_contour(mask)
    path = resample_contour(contour, n=1800)
    # Outward offset for sticker halo — a bit more room for the thicker stroke
    path = inflate_path(path, 18)

    random.seed(12)
    skip = draw_text_integrated(overlay, path, TEXT, ACCENT, font_size=62)

    draw = ImageDraw.Draw(overlay)
    draw_thick_path(draw, path, ACCENT, width=OUTLINE_WIDTH, skip=skip)
    rng = np.random.default_rng(5)
    jitter = path + rng.normal(0, 2.2, path.shape)
    draw_thick_path(draw, jitter, ACCENT, width=OUTLINE_WIDTH_INNER, skip=skip)

    random.seed(21)
    le = (pts["left_eye"][0], pts["left_eye"][1])
    re = (pts["right_eye"][0], pts["right_eye"][1])
    draw = ImageDraw.Draw(overlay)
    draw_eye_lashes(draw, le, ACCENT, scale=1.25)
    draw_eye_bursts(draw, re, ACCENT)

    draw_paisley(draw, tuple(pts["left_ear"]), ACCENT, scale=1.35, flip=False)
    draw_paisley(draw, tuple(pts["right_ear"]), ACCENT, scale=0.95, flip=True)

    shirt = cv2.imread(str(SHIRT_CACHE), 0)
    if shirt is None:
        shirt = np.zeros(mask.shape, np.uint8)
    fill_stars(draw, shirt, ACCENT)

    return overlay


def main() -> None:
    bgr = cv2.imread(str(SRC))
    if bgr is None:
        raise SystemExit(f"Cannot read {SRC}")

    original_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    mask = segment_subject(bgr)
    pts = detect_landmarks(bgr, mask)

    h, w = mask.shape
    background = make_platon_text_background(w, h, mask)
    subject = cutout_subject(original_rgb, mask)
    overlay = build_overlay(bgr, mask, pts)

    # Background → original Platon cutout → lime graphics
    composed = Image.alpha_composite(background, subject)
    composed = Image.alpha_composite(composed, overlay).convert("RGB")

    composed.save(OUT, quality=95)
    preview = composed.copy()
    preview.thumbnail((900, 1400))
    preview.save(OUT_PREVIEW, quality=90)
    overlay.save(ROOT / "overlay_only.png")
    background.convert("RGB").save(ROOT / "background_platon.jpg", quality=90)

    # Subject interior (away from edges) must match the original photo
    ys, xs = np.where(cv2.erode(mask, np.ones((41, 41), np.uint8)) > 0)
    if len(xs):
        i = len(xs) // 2
        y, x = int(ys[i]), int(xs[i])
        assert np.array_equal(original_rgb[y, x], np.array(composed)[y, x]), (
            "Subject pixels were altered"
        )
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_PREVIEW}")
    print("Landmarks:", json.dumps(pts))


if __name__ == "__main__":
    main()


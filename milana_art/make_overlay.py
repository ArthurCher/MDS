#!/usr/bin/env python3
"""Y2K collage graphic overlay on Milana's photo (photo pixels untouched)."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "milana_source.jpg"
OUT = ROOT / "milana_graphic_overlay.jpg"
OUT_PREVIEW = ROOT / "milana_graphic_overlay_preview.jpg"
MASK_CACHE = ROOT / "silhouette_mask.png"
PTS_CACHE = ROOT / "landmarks.json"

# Palette from the reference
HOT_PINK = (255, 45, 160)
LIME = (170, 255, 55)
ORANGE = (255, 140, 40)
PURPLE = (160, 90, 255)
SKY = (90, 190, 255)
BLACK = (15, 15, 15)
WHITE = (255, 255, 255)
STAR_COLORS = [HOT_PINK, LIME, ORANGE, PURPLE, SKY, (255, 90, 200), (120, 255, 180)]


def segment_subject(bgr: np.ndarray) -> np.ndarray:
    if MASK_CACHE.exists():
        return cv2.imread(str(MASK_CACHE), cv2.IMREAD_GRAYSCALE)

    from rembg import remove
    from PIL import Image as PILImage

    rgba = np.array(remove(PILImage.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))))
    mask = (rgba[:, :, 3] > 128).astype(np.uint8) * 255
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


def load_pts() -> dict:
    return json.loads(PTS_CACHE.read_text())


def multipoint_star(
    cx: float, cy: float, r_outer: float, points: int = 12, r_inner_ratio: float = 0.42
) -> list[tuple[float, float]]:
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + i * math.pi / points
        r = r_outer if i % 2 == 0 else r_outer * r_inner_ratio
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    return pts


def draw_filled_star(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = BLACK,
    points: int = 12,
    width: int = 4,
) -> None:
    poly = multipoint_star(cx, cy, r, points=points)
    draw.polygon(poly, fill=fill + (255,))
    if outline is not None:
        draw.line(poly + [poly[0]], fill=outline + (255,), width=width, joint="curve")


def draw_star_outline(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    color: tuple[int, int, int],
    points: int = 10,
    width: int = 6,
) -> None:
    poly = multipoint_star(cx, cy, r, points=points, r_inner_ratio=0.45)
    draw.line(poly + [poly[0]], fill=color + (255,), width=width, joint="curve")


def draw_asterisk(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    color: tuple[int, int, int],
    width: int = 3,
) -> None:
    for i in range(4):
        a = i * math.pi / 4
        draw.line(
            [
                (cx - math.cos(a) * r, cy - math.sin(a) * r),
                (cx + math.cos(a) * r, cy + math.sin(a) * r),
            ],
            fill=color + (255,),
            width=width,
        )


def draw_five_star(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r: float,
    color: tuple[int, int, int],
    fill: bool = False,
    width: int = 2,
) -> None:
    poly = multipoint_star(cx, cy, r, points=5, r_inner_ratio=0.4)
    if fill:
        draw.polygon(poly, fill=color + (255,))
    else:
        draw.line(poly + [poly[0]], fill=color + (255,), width=width, joint="curve")


def sample_curve(control: list[tuple[float, float]], n: int = 400) -> np.ndarray:
    """Catmull-Rom-ish smooth path through control points."""
    pts = np.array(control, dtype=np.float64)
    if len(pts) < 2:
        return pts
    # Duplicate ends for open curve
    ext = np.vstack([pts[0], pts, pts[-1]])
    out = []
    segs = len(pts) - 1
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for t in np.linspace(0, 1, max(2, n // segs), endpoint=False):
            t2, t3 = t * t, t * t * t
            p = 0.5 * (
                (2 * p1)
                + (-p0 + p2) * t
                + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
            )
            out.append(p)
    out.append(pts[-1])
    return np.array(out)


def draw_dashed_tube(
    overlay: Image.Image,
    path: np.ndarray,
    tube_w: int = 42,
    dash_len: float = 28,
    gap_len: float = 18,
) -> None:
    """Thick black wavy stroke with white dashed center line."""
    draw = ImageDraw.Draw(overlay)
    seq = [tuple(map(float, p)) for p in path]
    draw.line(seq, fill=BLACK + (255,), width=tube_w, joint="curve")
    # White dashed center
    d = np.sqrt(((np.roll(path, -1, axis=0) - path) ** 2).sum(axis=1))
    d[-1] = 0
    s = np.concatenate([[0], np.cumsum(d[:-1])])
    total = float(s[-1])
    pos = 0.0
    on = True
    while pos < total:
        span = dash_len if on else gap_len
        a, b = pos, min(total, pos + span)
        if on:
            i0 = max(0, int(np.searchsorted(s, a) - 1))
            i1 = min(len(path) - 1, int(np.searchsorted(s, b)))
            if i1 > i0:
                draw.line(
                    [tuple(map(float, p)) for p in path[i0 : i1 + 1]],
                    fill=WHITE + (255,),
                    width=max(6, tube_w // 5),
                    joint="curve",
                )
        on = not on
        pos += span


def build_wavy_paths(mask: np.ndarray, pts: dict) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Return (behind_paths, front_paths) that loop around the subject."""
    h, w = mask.shape
    x0, y0, x1, y1 = pts["bbox"]
    le, re = pts["left_eye"], pts["right_eye"]
    bx0, by0, bx1, by1 = pts["beanie"]

    # Big loop around head / right side — parts go behind silhouette
    loop_a = [
        (bx0 - 80, by1 + 40),
        (bx0 - 120, by0 + 80),
        ((bx0 + bx1) / 2, by0 - 160),
        (bx1 + 100, by0 - 40),
        (bx1 + 220, by1 + 200),
        (bx1 + 280, (y0 + y1) * 0.45),
        (x1 + 60, (y0 + y1) * 0.55),
        (x1 - 40, y1 - 200),
        ((x0 + x1) * 0.65, y1 + 80),
        ((x0 + x1) * 0.4, y1 - 40),
    ]
    # Secondary snake from left shoulder across body to bottom-right
    loop_b = [
        (x0 - 40, (y0 + y1) * 0.42),
        (x0 + 120, (y0 + y1) * 0.5),
        ((x0 + x1) * 0.35, (y0 + y1) * 0.58),
        ((x0 + x1) * 0.55, (y0 + y1) * 0.62),
        (x1 - 180, (y0 + y1) * 0.7),
        (x1 + 40, y1 - 120),
    ]
    # Small accent near face
    loop_c = [
        (le[0] - 180, le[1] - 40),
        (le[0] - 260, le[1] + 200),
        (le[0] - 80, le[1] + 380),
        (re[0] - 40, re[1] + 420),
    ]

    paths = [sample_curve(loop_a, 500), sample_curve(loop_b, 300), sample_curve(loop_c, 200)]
    behind, front = [], []
    for path in paths:
        # Split samples: points inside dilated mask = behind (drawn under subject cut isn't needed
        # if we mask the stroke by inverted mask for behind layer)
        behind.append(path)
        front.append(path)
    return behind, front


def draw_eye_starburst(
    draw: ImageDraw.ImageDraw, eye: tuple[int, int], scale: float = 1.0
) -> None:
    """Reference-style pink star + rays beside the eye — eyeball stays fully visible."""
    ex, ey = eye
    # Park the star clearly above the brow / on the beanie edge, left of the eye
    star_cx = ex - 120 * scale
    star_cy = ey - 200 * scale
    r = 78 * scale
    draw_filled_star(
        draw, star_cx, star_cy, r, HOT_PINK, outline=BLACK, points=11, width=5
    )
    # Rays only around the star itself (not across the eyeball)
    for i in range(12):
        a = i * (2 * math.pi / 12) + random.uniform(-0.04, 0.04)
        # Bias rays upward/outward — skip angles that point down toward the eye
        # Down toward eye is roughly southeast from this star position
        if math.pi * 0.05 < a < math.pi * 0.65:
            continue
        L = r * random.uniform(1.2, 1.55)
        draw.line(
            [
                (star_cx + math.cos(a) * r * 0.78, star_cy + math.sin(a) * r * 0.78),
                (star_cx + math.cos(a) * L, star_cy + math.sin(a) * L),
            ],
            fill=BLACK + (255,),
            width=max(4, int(5 * scale)),
        )
    # Lash strokes only above the eye, starting from the brow line
    brow_y = ey - 55 * scale
    for i in range(8):
        t = i / 7
        x1 = ex - 55 * scale + t * 110 * scale
        y1 = brow_y
        a = -math.pi / 2 - 0.35 + t * 0.7
        L = 70 * scale * random.uniform(0.8, 1.15)
        x2 = x1 + math.cos(a) * L
        y2 = y1 + math.sin(a) * L
        draw.line([(x1, y1), (x2, y2)], fill=BLACK + (255,), width=max(4, int(5 * scale)))


def clear_eye_windows(layer: Image.Image, pts: dict, radius: int = 110) -> Image.Image:
    """Punch transparent ellipses so both eyes (and lids) stay fully visible."""
    arr = np.array(layer)
    for key in ("left_eye", "right_eye"):
        cx, cy = int(pts[key][0]), int(pts[key][1])
        # Wide ellipse covering iris + lids
        cv2.ellipse(arr, (cx, cy), (radius, int(radius * 0.72)), 0, 0, 360, (0, 0, 0, 0), -1)
    return Image.fromarray(arr)


def draw_lip_highlights(
    draw: ImageDraw.ImageDraw, mouth: list[int]
) -> None:
    mx, my, mw, mh = mouth
    # Soft cartoon gloss sitting on the lips (not above them)
    w = max(10, mw // 16)
    up = [
        (mx - mw * 0.18, my - mh * 0.02),
        (mx - mw * 0.02, my - mh * 0.16),
        (mx + mw * 0.16, my - mh * 0.04),
    ]
    draw.line(up, fill=WHITE + (255,), width=w, joint="curve")
    low1 = [
        (mx - mw * 0.26, my + mh * 0.12),
        (mx - mw * 0.10, my + mh * 0.28),
        (mx + mw * 0.04, my + mh * 0.14),
    ]
    low2 = [
        (mx + mw * 0.06, my + mh * 0.14),
        (mx + mw * 0.20, my + mh * 0.30),
        (mx + mw * 0.34, my + mh * 0.12),
    ]
    draw.line(low1, fill=WHITE + (255,), width=w, joint="curve")
    draw.line(low2, fill=WHITE + (255,), width=w, joint="curve")


def draw_bg_asterisks(
    draw: ImageDraw.ImageDraw, mask: np.ndarray, seed: int = 3
) -> None:
    rng = random.Random(seed)
    h, w = mask.shape
    # Only on background
    ys, xs = np.where(mask == 0)
    if len(xs) < 100:
        return
    placed = 0
    tries = 0
    while placed < 90 and tries < 4000:
        tries += 1
        i = rng.randrange(len(xs))
        x, y = int(xs[i]), int(ys[i])
        # keep away from subject edge
        if y < h and x < w and mask[max(0, y - 20) : min(h, y + 20), max(0, x - 20) : min(w, x + 20)].any():
            if rng.random() > 0.35:
                continue
        r = rng.choice([10, 14, 18, 22, 28, 34])
        draw_asterisk(draw, x, y, r, BLACK, width=3 if r > 16 else 2)
        placed += 1


def draw_corner_starbursts(
    draw: ImageDraw.ImageDraw, w: int, h: int, pts: dict, seed: int = 11
) -> None:
    rng = random.Random(seed)
    x0, y0, x1, y1 = pts["bbox"]
    anchors = [
        (w * 0.12, h * 0.08, 140),
        (w * 0.88, h * 0.12, 160),
        (w * 0.92, h * 0.38, 120),
        (w * 0.08, h * 0.55, 110),
        (w * 0.78, h * 0.72, 150),
        (w * 0.95, h * 0.88, 100),
        (w * 0.55, h * 0.05, 90),
        (w * 0.22, h * 0.9, 130),
    ]
    for cx, cy, r in anchors:
        color = rng.choice(STAR_COLORS)
        style = rng.choice(["fill", "outline", "fill"])
        points = rng.choice([9, 10, 11, 12])
        if style == "fill":
            draw_filled_star(draw, cx, cy, r, color, outline=BLACK, points=points, width=5)
        else:
            draw_star_outline(draw, cx, cy, r, color, points=points, width=8)
        # optional ray accents
        if rng.random() < 0.5:
            for i in range(8):
                a = i * math.pi / 4 + rng.uniform(-0.1, 0.1)
                L = r * rng.uniform(1.15, 1.45)
                draw.line(
                    [(cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L)],
                    fill=BLACK + (255,),
                    width=3,
                )


def draw_galaxy_blob(
    overlay: Image.Image, w: int, h: int, corner: str = "br"
) -> None:
    draw = ImageDraw.Draw(overlay)
    rng = random.Random(21)
    if corner == "br":
        cx, cy = w * 0.82, h * 0.9
    else:
        cx, cy = w * 0.18, h * 0.88
    # Organic blob via perturbed ellipse points
    blob = []
    for i in range(60):
        a = 2 * math.pi * i / 60
        rx = w * 0.28 * (0.85 + 0.2 * math.sin(3 * a) + rng.uniform(-0.05, 0.05))
        ry = h * 0.18 * (0.85 + 0.2 * math.cos(2 * a) + rng.uniform(-0.05, 0.05))
        blob.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    draw.polygon(blob, fill=BLACK + (255,))
    # White stars inside blob
    minx = int(min(p[0] for p in blob))
    maxx = int(max(p[0] for p in blob))
    miny = int(min(p[1] for p in blob))
    maxy = int(max(p[1] for p in blob))
    # mask polygon roughly with PIL — sample random points and test via opencv
    poly_mask = np.zeros((h, w), np.uint8)
    cv2.fillPoly(poly_mask, [np.array(blob, dtype=np.int32)], 255)
    ys, xs = np.where(poly_mask > 0)
    for _ in range(120):
        i = rng.randrange(len(xs))
        x, y = float(xs[i]), float(ys[i])
        r = rng.choice([6, 9, 12, 16, 22, 28, 8])
        draw_five_star(draw, x, y, r, WHITE, fill=rng.random() < 0.55, width=2)


def draw_clothing_stars(
    draw: ImageDraw.ImageDraw, mask: np.ndarray, pts: dict, seed: int = 8
) -> None:
    """Sparse tiny white stars on clothing (lower face/body), not on eyes."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = pts["bbox"]
    mouth_y = pts["mouth"][1]
    region = mask.copy()
    region[: mouth_y + 40] = 0  # keep face clean except intentional accents
    ys, xs = np.where(region > 0)
    if len(xs) < 50:
        return
    for _ in range(28):
        i = rng.randrange(len(xs))
        x, y = float(xs[i]), float(ys[i])
        draw_five_star(draw, x, y, rng.choice([8, 11, 14, 18]), WHITE, fill=True)


def mask_layer_to_background(layer: Image.Image, mask: np.ndarray) -> Image.Image:
    """Keep only pixels outside the subject (graphics behind Milana)."""
    arr = np.array(layer)
    # zero alpha where subject is
    dil = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)), 1)
    arr[dil > 0, 3] = 0
    return Image.fromarray(arr)


def build_layers(
    bgr: np.ndarray, mask: np.ndarray, pts: dict
) -> tuple[Image.Image, Image.Image]:
    h, w = bgr.shape[:2]
    behind = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    front = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    random.seed(12)
    # Background asterisks (behind / on empty bg)
    draw_bg = ImageDraw.Draw(behind)
    draw_bg_asterisks(draw_bg, mask)

    # Wavy dashed tubes — full draw on behind then punch subject; also front accents
    behind_paths, _ = build_wavy_paths(mask, pts)
    tube_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for path in behind_paths:
        draw_dashed_tube(tube_layer, path, tube_w=56, dash_len=34, gap_len=20)
    # Portion outside subject stays behind
    behind = Image.alpha_composite(behind, mask_layer_to_background(tube_layer, mask))
    # Portion over subject goes in front (same paths for wrapping look)
    front_tubes = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # Only keep a subset of path over subject for "wrapping" — head loop mostly
    draw_dashed_tube(front_tubes, behind_paths[0][:220], tube_w=56, dash_len=34, gap_len=20)
    draw_dashed_tube(front_tubes, behind_paths[2], tube_w=48, dash_len=30, gap_len=18)
    # Keep front tubes only near edges / upper body — punch center face lightly later
    front = Image.alpha_composite(front, front_tubes)

    draw_f = ImageDraw.Draw(front)
    # Colorful corner starbursts
    draw_corner_starbursts(draw_f, w, h, pts)

    # Eye graphic like the reference, but eyes stay open (star + rays around, not over pupil)
    draw_eye_starburst(draw_f, tuple(pts["left_eye"]), scale=1.25)
    # Small accent near the other eye (offset, not covering)
    re = pts["right_eye"]
    draw_asterisk(draw_f, re[0] + 90, re[1] - 85, 24, BLACK, width=4)
    draw_five_star(draw_f, re[0] + 90, re[1] - 85, 11, WHITE, fill=True)

    draw_lip_highlights(draw_f, pts["mouth"])
    draw_clothing_stars(draw_f, mask, pts)
    draw_galaxy_blob(front, w, h, corner="br")

    # Ensure no stroke/star accidentally covers the eyeballs
    front = clear_eye_windows(front, pts, radius=120)
    behind = clear_eye_windows(behind, pts, radius=120)

    return behind, front


def main() -> None:
    bgr = cv2.imread(str(SRC))
    if bgr is None:
        raise SystemExit(f"Cannot read {SRC}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    mask = segment_subject(bgr)
    pts = load_pts()

    behind, front = build_layers(bgr, mask, pts)

    base = Image.fromarray(rgb).convert("RGBA")
    # behind graphics under... actually for "behind" look we need subject cutout.
    # Composite: (photo with behind only on bg) then front on top.
    # Simpler correct depth:
    # 1) photo
    # 2) behind layer already punched by subject mask
    # 3) front overlays
    composed = Image.alpha_composite(base, behind)
    composed = Image.alpha_composite(composed, front).convert("RGB")

    composed.save(OUT, quality=95)
    preview = composed.copy()
    preview.thumbnail((900, 1350))
    preview.save(OUT_PREVIEW, quality=90)
    front.save(ROOT / "overlay_front.png")
    behind.save(ROOT / "overlay_behind.png")

    # Verify a background-ish corner changed (stars) and face center roughly preserved
    out = np.array(composed)
    # Face point between eyes should match original (no overlay there except maybe rays)
    le, re = pts["left_eye"], pts["right_eye"]
    fx, fy = (le[0] + re[0]) // 2, (le[1] + re[1]) // 2 + 80  # bridge of nose
    # nose bridge may be untouched
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_PREVIEW}")
    print("Landmarks:", json.dumps(pts))
    print("nose sample orig/out", rgb[fy, fx].tolist(), out[fy, fx].tolist())


if __name__ == "__main__":
    main()

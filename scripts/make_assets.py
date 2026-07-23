#!/usr/bin/env python3
"""Generate the FEXT iOS app-icon set from the app's own "hearthside" brand:
a warm honey-to-cocoa glow behind a cream chat bubble carrying the signature
three golden ticks.

Deterministic and dependency-light (Pillow only). The generated files are
committed so the build works without running this, but regenerate any time:

    python3 scripts/make_assets.py

Writes:
    ios/AppIcon.appiconset/icon-<px>.png   (opaque, no alpha — App Store safe)
    ios/AppIcon.appiconset/Contents.json
    ios/icon-preview-1024.png              (for docs/README)
"""
from __future__ import annotations

import json
import math
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "ios", "AppIcon.appiconset")

# ---- brand palette (matches app/main.py) ------------------------------------
HONEY_HI = (0xF2, 0xB5, 0x4A)     # warm glow centre
HONEY = (0xD9, 0x8E, 0x2B)        # honey gold
COCOA = (0x5A, 0x3B, 0x29)        # toasted cocoa edge
CREAM = (0xFD, 0xF8, 0xEE)        # bubble fill
CREAM_EDGE = (0xEA, 0xDD, 0xC6)   # soft warm border
TICK_GOLD = (0xC9, 0x87, 0x1B)    # the golden ticks

SS = 4                            # supersample factor for crisp anti-aliasing


def _lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _radial_background(size: int) -> Image.Image:
    """Warm hearth glow: honey highlight near an upper-centre light source,
    falling off to cocoa at the corners. Built small then scaled for speed."""
    small = 160
    grad = Image.new("RGB", (small, small))
    px = grad.load()
    cx, cy = small * 0.5, small * 0.42
    maxd = math.hypot(max(cx, small - cx), max(cy, small - cy))
    for y in range(small):
        for x in range(small):
            d = min(1.0, math.hypot(x - cx, y - cy) / maxd)
            if d < 0.5:
                col = _lerp(HONEY_HI, HONEY, d / 0.5)
            else:
                col = _lerp(HONEY, COCOA, (d - 0.5) / 0.5)
            px[x, y] = col
    return grad.resize((size, size), Image.BICUBIC)


def _draw_check(draw, x, y, s, width, color):
    """A rounded-cap checkmark within an s×s box at (x, y)."""
    p1 = (x + 0.04 * s, y + 0.52 * s)
    p2 = (x + 0.36 * s, y + 0.84 * s)
    p3 = (x + 0.96 * s, y + 0.12 * s)
    draw.line([p1, p2, p3], fill=color, width=width, joint="curve")
    r = width / 2.0
    for p in (p1, p2, p3):                       # round the caps/joints
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def render_master(size: int) -> Image.Image:
    """Render the full icon at `size` px (opaque, full-bleed, no alpha)."""
    S = size * SS
    base = _radial_background(S).convert("RGBA")

    # bubble geometry
    bw, bh = S * 0.62, S * 0.50
    bx, by = (S - bw) / 2, (S - bh) / 2 - S * 0.02
    radius = S * 0.11
    tail = [(bx + bw * 0.28, by + bh - S * 0.01),
            (bx + bw * 0.10, by + bh + S * 0.11),
            (bx + bw * 0.50, by + bh - S * 0.01)]

    # soft drop shadow on its own layer, blurred, then composited
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    off = S * 0.014
    sd.rounded_rectangle([bx + off, by + off, bx + bw + off, by + bh + off],
                         radius=radius, fill=(50, 33, 22, 110))
    sd.polygon([(p[0] + off, p[1] + off) for p in tail], fill=(50, 33, 22, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.012))
    base = Image.alpha_composite(base, shadow)

    # the bubble + ticks
    draw = ImageDraw.Draw(base)
    draw.polygon(tail, fill=CREAM)
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=radius,
                           fill=CREAM, outline=CREAM_EDGE,
                           width=max(1, int(S * 0.006)))

    tick = bw * 0.30
    gap = tick * 0.78                            # horizontal step between ticks
    total = 2 * gap + tick                       # (lighter overlap: 3 distinct
    start_x = bx + (bw - total) / 2              #  checks, not a zigzag)
    ty = by + (bh - tick) / 2
    w = max(2, int(S * 0.028))
    for i in range(3):
        _draw_check(draw, start_x + i * gap, ty, tick, w, TICK_GOLD)

    return base.resize((size, size), Image.LANCZOS).convert("RGB")


CONTENTS = {
    "iphone": [("20x20", ["2x", "3x"]), ("29x29", ["2x", "3x"]),
               ("40x40", ["2x", "3x"]), ("60x60", ["2x", "3x"])],
    "ipad": [("20x20", ["1x", "2x"]), ("29x29", ["1x", "2x"]),
             ("40x40", ["1x", "2x"]), ("76x76", ["1x", "2x"]),
             ("83.5x83.5", ["2x"])],
    "ios-marketing": [("1024x1024", ["1x"])],
}


def _px(size_str: str, scale: str) -> int:
    return int(round(float(size_str.split("x")[0]) * int(scale[0])))


def main():
    os.makedirs(OUT, exist_ok=True)
    images, needed = [], set()
    for idiom, entries in CONTENTS.items():
        for size_str, scales in entries:
            for scale in scales:
                px = _px(size_str, scale)
                needed.add(px)
                images.append({"size": size_str, "idiom": idiom,
                               "filename": f"icon-{px}.png", "scale": scale})
    print(f"rendering {len(needed)} unique sizes: {sorted(needed)}")
    cache = {}
    for px in sorted(needed):
        cache[px] = render_master(px)
        cache[px].save(os.path.join(OUT, f"icon-{px}.png"))
    with open(os.path.join(OUT, "Contents.json"), "w") as fh:
        json.dump({"images": images,
                   "info": {"version": 1, "author": "xcode"}}, fh, indent=2)
    preview = os.path.join(os.path.dirname(OUT), "icon-preview-1024.png")
    cache[1024].save(preview)
    print(f"wrote {len(needed)} icons + Contents.json -> {OUT}")
    print(f"wrote preview -> {preview}")


if __name__ == "__main__":
    main()

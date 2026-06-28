#!/usr/bin/env python3
"""Create distinct slider images (Pillow) — unique styles per section, separate from bright-* photos."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images"
OUTPUT.mkdir(parents=True, exist_ok=True)

W, H = 1536, 1024


def _font(size: int):
    for name in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        p = Path(name)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def _save(img: Image.Image, name: str) -> None:
    path = OUTPUT / name
    if name.endswith(".png"):
        img.save(path, "PNG", optimize=True)
    else:
        img.save(path, "WEBP", quality=88, method=6)
    print(f"  saved {path.name} ({path.stat().st_size // 1024}KB)")


def _gradient(w: int, h: int, c1: tuple, c2: tuple, vertical=True) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    span = h if vertical else w
    for i in range(span):
        t = i / span
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        if vertical:
            draw.line([(0, i), (w, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, h)], fill=(r, g, b))
    return img


def _soft_circle(cx, cy, r, fill, alpha=180) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill + (alpha,))
    return layer


def _silhouette_woman(draw, ox, oy, scale=1.0, color=(255, 255, 255, 200)):
    s = scale
    draw.ellipse((ox - 28 * s, oy - 90 * s, ox + 28 * s, oy - 34 * s), fill=color)
    draw.pieslice((ox - 36 * s, oy - 100 * s, ox + 36 * s, oy - 20 * s), 200, 340, fill=color)
    draw.polygon(
        [
            (ox - 22 * s, oy - 30 * s),
            (ox + 22 * s, oy - 30 * s),
            (ox + 38 * s, oy + 120 * s),
            (ox - 38 * s, oy + 120 * s),
        ],
        fill=color,
    )


def cinematic_hero(i: int) -> Image.Image:
    palettes = [
        ((220, 210, 245), (255, 248, 240), (180, 200, 230)),
        ((255, 230, 220), (248, 252, 255), (200, 220, 245)),
        ((210, 235, 225), (255, 250, 245), (190, 210, 250)),
        ((245, 225, 235), (250, 252, 255), (210, 225, 245)),
        ((230, 240, 255), (255, 245, 235), (200, 215, 240)),
    ]
    c1, c2, accent = palettes[i % 5]
    img = _gradient(W, H, c1, c2).convert("RGBA")
    random.seed(i + 11)
    for _ in range(12):
        layer = _soft_circle(
            random.randint(0, W),
            random.randint(0, H),
            random.randint(80, 220),
            accent,
            random.randint(30, 70),
        )
        img = Image.alpha_composite(img, layer)
    draw = ImageDraw.Draw(img)
    _silhouette_woman(draw, W * 0.62, H * 0.55, 2.2, (255, 255, 255, 210))
    draw.arc((W * 0.58, H * 0.42, W * 0.72, H * 0.58), 30, 200, fill=(120, 160, 200, 180), width=6)
    img = img.filter(ImageFilter.GaussianBlur(0.3))
    draw = ImageDraw.Draw(img)
    draw.text((80, H - 120), f"Healthcare · {i + 1}", fill=(60, 80, 120, 220), font=_font(42))
    return img.convert("RGB")


def gouache_hope(i: int) -> Image.Image:
    img = Image.new("RGB", (1024, 1024), (252, 250, 255))
    hues = [(255, 210, 220), (190, 225, 245), (210, 235, 220), (245, 225, 255), (255, 235, 210)]
    for j, col in enumerate(hues):
        layer = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        x = 120 + j * 160 + i * 20
        y = 200 + (j % 3) * 80
        ld.ellipse((x - 140, y - 100, x + 140, y + 180), fill=col + (140,))
        img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(img)
    _silhouette_woman(draw, 512, 520, 2.8, (255, 255, 255, 230))
    draw.ellipse((430, 380, 470, 420), fill=(255, 200, 200))
    return img.filter(ImageFilter.SMOOTH)


def panoramic_team(i: int) -> Image.Image:
    img = _gradient(W, H, (200, 220, 240), (235, 245, 255), vertical=False)
    draw = ImageDraw.Draw(img)
    for j in range(5):
        x = 180 + j * 260 + i * 15
        _silhouette_woman(draw, x, H * 0.52, 1.6, (255, 255, 255, 190 + j * 10))
    draw.rectangle((0, H - 8, W, H), fill=(140, 170, 210))
    return img


def isometric_guide(i: int) -> Image.Image:
    img = Image.new("RGB", (1024, 1024), (245, 248, 255))
    draw = ImageDraw.Draw(img)
    colors = [(186, 170, 255), (130, 210, 200), (255, 190, 210), (160, 200, 255), (200, 230, 180)]
    base = colors[i % 5]
    cx, cy = 512, 560
    for k in range(3):
        off = k * 40
        pts = [(cx - 200 + off, cy), (cx, cy - 120 + off), (cx + 200 - off, cy), (cx, cy + 120 - off)]
        shade = tuple(max(0, c - k * 25) for c in base)
        draw.polygon(pts, fill=shade, outline=(255, 255, 255))
    _silhouette_woman(draw, cx, cy - 80, 1.4, (80, 90, 120, 220))
    draw.rounded_rectangle((cx + 80, cy - 40, cx + 150, cy + 60), radius=12, fill=(60, 70, 100))
    draw.text((320, 120), f"Step {i + 1}", fill=(90, 100, 140), font=_font(56))
    return img


def lifestyle_recovery(i: int) -> Image.Image:
    w, h = (1024, 1536) if i % 2 == 0 else (W, H)
    img = _gradient(w, h, (255, 245, 230), (210, 235, 255))
    draw = ImageDraw.Draw(img)
    _silhouette_woman(draw, w * 0.5, h * 0.55, 2.5 if w > h else 2.0, (255, 255, 255, 200))
    draw.ellipse((w - 220, 80, w - 60, 240), fill=(255, 230, 180))
    draw.pieslice((int(w * 0.2), int(h * 0.7), int(w * 0.8), int(h * 1.1)), 180, 360, fill=(200, 220, 200))
    return img


def feature_style(section: str, i: int) -> Image.Image:
    if section == "feature-ai":
        return isometric_guide(i)
    if section == "feature-rag":
        return gouache_hope(i + 2)
    if section == "feature-reservation":
        return panoramic_team(i)
    if section == "feature-hospital":
        return cinematic_hero(i + 1)
    if section == "feature-health":
        return gouache_hope(i + 1)
    if section == "feature-subscription":
        return lifestyle_recovery(i)
    return cinematic_hero(i)


def main():
    print("Creating slider images...")
    specs: list[tuple[str, callable]] = []
    for n in range(1, 6):
        specs.append((f"slide-hero-{n:02d}.webp", lambda n=n: cinematic_hero(n - 1)))
        specs.append((f"slide-hope-{n:02d}.png", lambda n=n: gouache_hope(n - 1)))
        specs.append((f"slide-team-{n:02d}.webp", lambda n=n: panoramic_team(n - 1)))
        specs.append((f"slide-guide-{n:02d}.png", lambda n=n: isometric_guide(n - 1)))
        specs.append((f"slide-recovery-{n:02d}.webp", lambda n=n: lifestyle_recovery(n - 1)))
    for sec, ext in [
        ("feature-ai", "png"),
        ("feature-rag", "png"),
        ("feature-reservation", "webp"),
        ("feature-hospital", "webp"),
        ("feature-health", "png"),
        ("feature-subscription", "webp"),
    ]:
        for n in range(1, 6):
            specs.append(
                (f"slide-{sec}-{n:02d}.{ext}", lambda sec=sec, n=n: feature_style(sec, n - 1))
            )

    for fname, maker in specs:
        _save(maker(), fname)
    print(f"\nDone: {len(specs)} images")


if __name__ == "__main__":
    main()

"""Render the integration's own icon and logo (Pillow only, no cairo needed).

The drop outline is the same cubic path used in assets/icon.svg.

    python scripts/generate_brand.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parents[1]
BRAND = ROOT / "custom_components" / "bwt_aqa_perla" / "brand"
SS = 4  # supersampling factor

DEEP = (14, 76, 146)
MID = (24, 130, 200)
LIGHT = (31, 162, 224)
INK = (14, 59, 110)

# Drop outline on a 512 x 512 grid: start point plus cubic segments.
DROP_START = (256, 56)
DROP_SEGMENTS = (
    ((300, 120), (392, 220), (392, 320)),
    ((392, 395), (332, 456), (256, 456)),
    ((180, 456), (120, 395), (120, 320)),
    ((120, 220), (212, 120), (256, 56)),
)
PEARL = (256, 332, 62)  # cx, cy, r
HIGHLIGHT = (236, 310, 15)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def drop_points(scale: float, dx: float, dy: float, n: int = 80):
    pts = [DROP_START]
    cur = DROP_START
    for c1, c2, end in DROP_SEGMENTS:
        for i in range(1, n + 1):
            t = i / n
            u = 1 - t
            x = (
                u**3 * cur[0]
                + 3 * u**2 * t * c1[0]
                + 3 * u * t**2 * c2[0]
                + t**3 * end[0]
            )
            y = (
                u**3 * cur[1]
                + 3 * u**2 * t * c1[1]
                + 3 * u * t**2 * c2[1]
                + t**3 * end[1]
            )
            pts.append((x, y))
        cur = end
    return [(x * scale + dx, y * scale + dy) for x, y in pts]


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGBA", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, y / max(h - 1, 1)) + (255,))
    return img


def draw_pearl(img, scale, dx, dy, inner, outer):
    cx, cy, r = PEARL
    hx, hy, hr = HIGHLIGHT
    d = ImageDraw.Draw(img)
    # Radial shading: concentric discs drifting toward the highlight.
    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        rad = r * (1 - t * 0.92)
        ox = (hx - cx) * t * 0.55
        oy = (hy - cy) * t * 0.55
        x = (cx + ox) * scale + dx
        y = (cy + oy) * scale + dy
        d.ellipse(
            [x - rad * scale, y - rad * scale, x + rad * scale, y + rad * scale],
            fill=lerp(outer, inner, t) + (255,),
        )
    shine = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse(
        [
            (hx - hr) * scale + dx,
            (hy - hr * 0.8) * scale + dy,
            (hx + hr) * scale + dx,
            (hy + hr * 0.8) * scale + dy,
        ],
        fill=(255, 255, 255, 215),
    )
    img.alpha_composite(shine)


def render_icon(size: int) -> Image.Image:
    n = size * SS
    scale = n / 512
    bg = vertical_gradient((n, n), LIGHT, DEEP)
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, n - 1, n - 1], radius=112 * scale, fill=255
    )
    canvas = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    canvas.paste(bg, mask=mask)
    layer = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(layer).polygon(drop_points(scale, 0, 0), fill=(255, 255, 255, 255))
    canvas.alpha_composite(layer)
    draw_pearl(canvas, scale, 0, 0, (150, 215, 245), DEEP)
    return canvas.resize((size, size), Image.LANCZOS)


def find_font(size: int) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/Avenir Next.ttc"
    for index in range(20):
        try:
            font = ImageFont.truetype(path, size, index=index)
        except OSError:
            break
        if "Demi" in " ".join(font.getname()) or "Bold" in font.getname()[1]:
            return font
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def render_logo(height: int, text_color) -> Image.Image:
    h = height * SS
    pad = round(h * 0.06)
    mark_h = h - 2 * pad
    scale = mark_h / 400  # the drop spans y 56..456
    mark_w = round(272 * scale)
    font = find_font(round(h * 0.40))
    text = "AQA Perla"
    tw = round(font.getlength(text))
    gap = round(h * 0.10)
    w = pad + mark_w + gap + tw + pad
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    dx = pad - 120 * scale
    dy = pad - 56 * scale
    fill = vertical_gradient((w, h), LIGHT, DEEP)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(drop_points(scale, dx, dy), fill=255)
    canvas.paste(fill, mask=m)
    draw_pearl(canvas, scale, dx, dy, (255, 255, 255), (170, 222, 246))

    d = ImageDraw.Draw(canvas)
    bbox = font.getbbox(text)
    ty = (h - (bbox[3] - bbox[1])) / 2 - bbox[1]
    d.text((pad + mark_w + gap, ty), text, font=font, fill=text_color + (255,))
    return canvas.resize((w // SS, h // SS), Image.LANCZOS)


def main() -> None:
    BRAND.mkdir(parents=True, exist_ok=True)
    render_icon(256).save(BRAND / "icon.png")
    render_icon(512).save(BRAND / "icon@2x.png")
    for suffix, height in (("", 256), ("@2x", 512)):
        render_logo(height, INK).save(BRAND / f"logo{suffix}.png")
        render_logo(height, (235, 245, 252)).save(BRAND / f"dark_logo{suffix}.png")
    # README copies under a path GitHub's raw CDN has never cached.
    (ROOT / "assets").mkdir(exist_ok=True)
    render_logo(256, INK).save(ROOT / "assets" / "logo.png")
    render_logo(256, (235, 245, 252)).save(ROOT / "assets" / "logo_dark.png")
    print("written to", BRAND)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Launcher icon generator: one picture plus the shared version badge.

Same convention as the other com.vanipy.* apps: numbers-only version on a
full-width strip across the bottom of the icon, picture inside the
round-mask safe circle, one consistent corner radius.

Deterministic. Same version in, same PNGs out. Inputs are pinned: Pillow
PILLOW_PIN and DejaVu Sans Bold with sha256 FONT_SHA256. The script fails
instead of falling back to another font or Pillow version, because a
different rasterizer or font changes the pixels.
    pip install pillow==12.3.0   (fonts-dejavu-core provides the font)
"""
import hashlib
import math
import os
import re
import sys

import PIL
from PIL import Image, ImageChops, ImageDraw, ImageFont

PILLOW_PIN = "12.3.0"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SHA256 = "d1c3ff99f1e1ce1827a33efd4dad81f40babda06bff9e43bd7591c86662a287b"
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 768
STRIP_TOP = 0.76      # strip covers 76%..100% of the icon height
TEXT_SIZE = 0.115     # numeral size, fraction of icon size
SAFE_R = 0.485        # picture and text must stay inside this radius (fraction)

if PIL.__version__ != PILLOW_PIN:
    sys.exit("Pillow %s required, found %s" % (PILLOW_PIN, PIL.__version__))


def font(px):
    if not os.path.exists(FONT_PATH):
        sys.exit("missing font " + FONT_PATH)
    if hashlib.sha256(open(FONT_PATH, "rb").read()).hexdigest() != FONT_SHA256:
        sys.exit("unexpected font file " + FONT_PATH)
    return ImageFont.truetype(FONT_PATH, px)


def circle_mask(size, r=SAFE_R):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([size * (.5 - r), size * (.5 - r), size * (.5 + r), size * (.5 + r)], fill=255)
    return m


def assert_inside_circle(layer, what, size=S, r=SAFE_R):
    alpha = layer.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    outside = ImageChops.multiply(alpha, ImageChops.invert(circle_mask(size, r)))
    box = outside.getbbox()
    if box:
        sys.exit("%s leaves the round-mask safe circle at %s" % (what, box))


def new_layer(size=S):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def compose(bg, art, version, strip, text, rounded=None, size=S, circle_check=True):
    """Background, then the picture layer, then the badge strip."""
    if circle_check:
        assert_inside_circle(art, "picture", size)
    base = Image.new("RGBA", (size, size), bg) if bg else Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.alpha_composite(art)
    d = ImageDraw.Draw(base)
    y0 = int(size * STRIP_TOP)
    d.rectangle([0, y0, size, size], fill=strip)
    tl, td = new_layer(size)
    f = font(int(size * TEXT_SIZE))
    td.text((size / 2, (y0 + size) / 2), version, font=f, fill=text, anchor="mm")
    if circle_check:
        assert_inside_circle(tl, "version text", size)
    base.alpha_composite(tl)
    if rounded:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size, size], radius=rounded * size, fill=255)
        base.putalpha(ImageChops.multiply(base.getchannel("A"), m))
    return base


def parse_version(argv, fallback=None):
    v = argv[1] if len(argv) > 1 else fallback
    if not v or not re.fullmatch(r"\d+\.\d+\.\d+", v):
        sys.exit("version must be X.Y.Z")
    return v


def write_densities(img, res_dir, name="ic_launcher.png"):
    for dens, px in DENSITIES.items():
        out = os.path.join(res_dir, "mipmap-" + dens)
        os.makedirs(out, exist_ok=True)
        img.resize((px, px), Image.LANCZOS).save(os.path.join(out, name), optimize=True)


def tuju(version):
    """A route: start dot, curved path, destination pin (tuju = destination)."""
    BG = (26, 77, 122, 255)        # busway blue
    STRIP = (12, 38, 61, 255)
    WHITE = (255, 255, 255, 255)
    AMBER = (255, 199, 89, 255)    # destination pin
    art, d = new_layer()
    # route path: gentle S-curve from lower-left start to upper-right pin
    # smooth tube: stamp overlapping circles along the curve (no joint seams)
    w = S * .018
    steps = 220
    for i in range(steps + 1):
        t = i / steps
        x = (.30 + .40 * t) * S
        y = (.62 - .30 * t + .06 * math.sin(t * math.pi * 2)) * S
        d.ellipse([x - w, y - w, x + w, y + w], fill=WHITE)
    # start dot
    d.ellipse([S * .26, S * .63, S * .34, S * .71], fill=WHITE)
    # destination pin: circle head + pointed tail
    cx, cy, r = .70 * S, .30 * S, .085 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMBER)
    d.polygon([(cx - r * .72, cy + r * .55), (cx + r * .72, cy + r * .55), (cx, cy + r * 2.1)], fill=AMBER)
    d.ellipse([cx - r * .4, cy - r * .4, cx + r * .4, cy + r * .4], fill=BG)
    return compose(BG, art, version, STRIP, WHITE, rounded=.2)


def main():
    version = parse_version(sys.argv)
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    write_densities(tuju(version), os.path.join(root, "app", "src", "main", "res"))
    print("wrote icons for", version)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Genera logo-vector.svg y logo-vector-dark.svg: logo-icon-brain-gear.svg + texto original."""
import re
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
IMG = ROOT / 'static' / 'images'
ICON_SVG = IMG / 'logo-icon-brain-gear.svg'
ICON_PNG = IMG / 'logo-icon-brain-gear-512.png'
OUT_LIGHT = IMG / 'logo-vector.svg'
OUT_DARK = IMG / 'logo-vector-dark.svg'

ICON_TARGET_H = 680
ICON_X = 0
ICON_Y = 0
TEXT_X_MIN = 780
ICON_TEXT_GAP = 83


def icon_content_bbox() -> tuple[int, int, int, int]:
    img = Image.open(ICON_PNG).convert('RGBA')
    x0, y0, x1, y1 = img.getbbox() or (0, 0, 512, 512)
    return x0, y0, x1 - x0, y1 - y0


def original_logo_svg() -> str:
    return subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', 'HEAD:static/images/logo-vector.svg'],
        text=True,
    )


def load_brain_gear_image_tag() -> str:
    svg = ICON_SVG.read_text()
    m = re.search(r'<image\b[^>]*/>', svg, re.DOTALL)
    if not m:
        m = re.search(r'<image\b[^>]*>.*?</image>', svg, re.DOTALL)
    if not m:
        raise RuntimeError(f'No se encontró <image> en {ICON_SVG}')
    tag = m.group(0)
    if 'width=' not in tag:
        tag = tag.replace('<image', '<image width="512" height="512"', 1)
    return tag


def extract_text_paths(svg: str) -> list[str]:
    paths = re.findall(r'<path [^>]*/>', svg)
    text_paths = []
    for p in paths:
        m = re.search(r'translate\(([-\d.]+)', p)
        if m and float(m.group(1)) >= TEXT_X_MIN:
            text_paths.append(p)
    if len(text_paths) < 10:
        raise RuntimeError(f'Solo {len(text_paths)} paths de texto; se esperaban ≥10 del logo original')
    return text_paths


def path_y_extents(d: str) -> tuple[float, float]:
    nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', d)]
    ys = nums[1::2]
    return min(ys), max(ys)


def shift_text_paths(text_paths: list[str], dx: float, dy: float) -> list[str]:
    if abs(dx) < 0.01 and abs(dy) < 0.01:
        return text_paths
    out = []
    for p in text_paths:
        def repl(m):
            x = float(m.group(1)) + dx
            y = float(m.group(2)) + dy
            return f'translate({x},{y})'

        out.append(re.sub(r'translate\(([-\d.]+),([-\d.]+)\)', repl, p, count=1))
    return out


def text_vertical_bounds(text_paths: list[str]) -> tuple[float, float]:
    mins, maxs = [], []
    for p in text_paths:
        d_m = re.search(r'd="([^"]+)"', p)
        t_m = re.search(r'translate\(([-\d.]+),([-\d.]+)\)', p)
        if not d_m or not t_m:
            continue
        y0, y1 = path_y_extents(d_m.group(1))
        ty = float(t_m.group(2))
        mins.append(ty + y0)
        maxs.append(ty + y1)
    return min(mins), max(maxs)


def compose_svg(image_tag: str, text_paths: list[str]) -> str:
    bx, by, bw, bh = icon_content_bbox()
    scale = ICON_TARGET_H / bh
    icon_w = bw * scale

    # Alineación horizontal (sin margen izquierdo)
    min_text_x = min(
        float(re.search(r'translate\(([-\d.]+)', p).group(1)) for p in text_paths
    )
    text_dx = (ICON_X + icon_w + ICON_TEXT_GAP) - min_text_x
    text_paths = shift_text_paths(text_paths, text_dx, 0)

    # Recorte vertical: quitar márgenes arriba/abajo del lienzo original (784px)
    icon_top = ICON_Y
    icon_bottom = ICON_Y + ICON_TARGET_H
    text_top, text_bottom = text_vertical_bounds(text_paths)
    crop_top = min(icon_top, text_top)
    crop_bottom = max(icon_bottom, text_bottom)
    canvas_h = int(round(crop_bottom - crop_top))
    text_paths = shift_text_paths(text_paths, 0, -crop_top)

    icon_svg = (
        f'<svg width="{icon_w:.4f}" height="{ICON_TARGET_H}" '
        f'viewBox="{bx} {by} {bw} {bh}">\n{image_tag}\n</svg>'
    )
    icon_group = (
        f'<g transform="translate({ICON_X},{ICON_Y - crop_top})">\n'
        f'{icon_svg}\n</g>'
    )

    canvas_w = int(round(2504 + text_dx))
    body = icon_group + '\n' + '\n'.join(text_paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{canvas_w}" height="{canvas_h}">\n'
        f'{body}\n</svg>\n'
    )


def make_dark_svg(svg_text: str) -> str:
    def lighten_dark(m):
        hexcol = m.group(1)
        r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
        if max(r, g, b) < 150:
            return 'fill="#FFFFFF"'
        return m.group(0)

    return re.sub(r'fill="#([0-9A-Fa-f]{6})"', lighten_dark, svg_text)


def main() -> None:
    orig = original_logo_svg()
    text_paths = extract_text_paths(orig)
    image_tag = load_brain_gear_image_tag()
    svg = compose_svg(image_tag, text_paths)

    OUT_LIGHT.write_text(svg)
    OUT_DARK.write_text(make_dark_svg(svg))
    print(f'Logo claro: {OUT_LIGHT} (icono {ICON_SVG.name} + {len(text_paths)} paths texto)')
    print(f'Logo oscuro: {OUT_DARK}')


if __name__ == '__main__':
    main()

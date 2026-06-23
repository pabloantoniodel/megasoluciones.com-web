#!/usr/bin/env python3
"""Exporta logo partido: icono WebP + wordmark SVG (sin base64 embebido)."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMG = ROOT / 'static' / 'images'
FULL_LIGHT = IMG / 'logo-vector.svg'
FULL_DARK = IMG / 'logo-vector-dark.svg'
OUT_TEXT_LIGHT = IMG / 'logo-text.svg'
OUT_TEXT_DARK = IMG / 'logo-text-dark.svg'
ICON_PNG = IMG / 'logo-icon-brain-gear-512.png'
ICON_WEBP = IMG / 'logo-icon-brain-gear-256.webp'

# Debe coincidir con build_logo_vector_brain.py
ICON_NESTED_W = 633.3806
ICON_GAP = 83
CANVAS_H = 680
VIEWBOX_PAD = 8


def path_bounds(paths: list[str]) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for p in paths:
        t = re.search(r'translate\(([-\d.]+),([-\d.]+)\)', p)
        d = re.search(r'd="([^"]+)"', p)
        if not t or not d:
            continue
        tx, ty = float(t.group(1)), float(t.group(2))
        nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', d.group(1))]
        xs.extend(tx + nums[i] for i in range(0, len(nums), 2))
        ys.extend(ty + nums[i] for i in range(1, len(nums), 2))
    return min(xs), min(ys), max(xs), max(ys)


def extract_text_paths(svg: str) -> list[str]:
    return [p for p in re.findall(r'<path [^>]*/>', svg) if 'transform="translate(' in p]


def compose_text_svg(paths: list[str], canvas_w: float) -> str:
    x0, _, x1, _ = path_bounds(paths)
    text_x = max(0, int(x0 - VIEWBOX_PAD))
    text_w = int(round(canvas_w - text_x))
    body = '\n'.join(paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{text_x} 0 {text_w} {CANVAS_H}" '
        f'width="{text_w}" height="{CANVAS_H}">\n'
        f'{body}\n</svg>\n'
    )


def export_icon_webp() -> None:
    subprocess.run(
        [
            'convert', str(ICON_PNG),
            '-resize', '256x256',
            '-quality', '88',
            str(ICON_WEBP),
        ],
        check=True,
    )


def main() -> None:
    light_raw = FULL_LIGHT.read_text()
    dark_raw = FULL_DARK.read_text()
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', light_raw)
    canvas_w = float(m.group(1)) if m else 2403.0
    OUT_TEXT_LIGHT.write_text(compose_text_svg(extract_text_paths(light_raw), canvas_w))
    OUT_TEXT_DARK.write_text(compose_text_svg(extract_text_paths(dark_raw), canvas_w))
    export_icon_webp()
    total = OUT_TEXT_LIGHT.stat().st_size + ICON_WEBP.stat().st_size
    print(f'{OUT_TEXT_LIGHT.name}: {OUT_TEXT_LIGHT.stat().st_size} bytes')
    print(f'{OUT_TEXT_DARK.name}: {OUT_TEXT_DARK.stat().st_size} bytes')
    print(f'{ICON_WEBP.name}: {ICON_WEBP.stat().st_size} bytes')
    print(f'Total navbar (icono + texto claro): {total} bytes')


if __name__ == '__main__':
    main()

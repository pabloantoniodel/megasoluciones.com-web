#!/usr/bin/env python3
"""Exporta logo completo para navbar/footer: PNG + WebP transparentes (2x retina)."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMG = ROOT / 'static' / 'images'
DISPLAY_H = 56
RENDER_H = DISPLAY_H * 2


def export_pair(svg_name: str, png_name: str) -> None:
    svg = IMG / svg_name
    png = IMG / png_name
    webp = png.with_suffix('.webp')
    subprocess.run(['rsvg-convert', str(svg), '-h', str(RENDER_H), '-o', str(png)], check=True)
    subprocess.run(['convert', str(png), '-strip', str(png)], check=True)
    subprocess.run(['convert', str(png), '-quality', '92', str(webp)], check=True)
    print(f'{png.name}: {png.stat().st_size} bytes, {webp.name}: {webp.stat().st_size} bytes')


def main() -> None:
    export_pair('logo-vector.svg', 'logo-nav.png')
    export_pair('logo-vector-dark.svg', 'logo-nav-dark.png')
    print(f'Altura visible en web: {DISPLAY_H}px (render {RENDER_H}px)')


if __name__ == '__main__':
    main()

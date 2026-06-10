import re
import vtracer
from PIL import Image

SRC = '/home/administrator/megasoluciones/static/images/logo.png'
TMP = '/home/administrator/megasoluciones/static/images/logo_nobg.png'
OUT_LIGHT = '/home/administrator/megasoluciones/static/images/logo-vector.svg'
OUT_DARK = '/home/administrator/megasoluciones/static/images/logo-vector-dark.svg'

# 1. Make the white background transparent (color-to-alpha to kill AA halos)
import numpy as np

img = Image.open(SRC).convert('RGBA')
arr = np.asarray(img).astype(np.float32)
rgb = arr[:, :, :3]

# Whiteness-based alpha: a pure white pixel -> 0, saturated color -> 255
alpha = 255.0 - rgb.min(axis=2)
# Unpremultiply against white so edge pixels recover their true color
safe_alpha = np.maximum(alpha, 1.0)
unmixed = (rgb - (255.0 - alpha[:, :, None])) * (255.0 / safe_alpha[:, :, None])
unmixed = np.clip(unmixed, 0, 255)

# Binarize: keep pixels that are at least half-colored, drop the rest
mask = alpha >= 100
out = np.zeros_like(arr, dtype=np.uint8)
out[:, :, :3] = unmixed.astype(np.uint8)
out[:, :, 3] = np.where(mask, 255, 0).astype(np.uint8)
img = Image.fromarray(out, 'RGBA')

# Crop to content to remove the huge empty margins
bbox = img.getbbox()
img = img.crop(bbox)
img.save(TMP)
print(f'Transparent PNG saved, cropped to {img.size}')

# 2. Trace to SVG
vtracer.convert_image_to_svg_py(
    TMP,
    OUT_LIGHT,
    colormode='color',
    hierarchical='stacked',
    mode='spline',
    filter_speckle=14,
    color_precision=4,
    layer_difference=32,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=5,
)
print('Light SVG traced')

svg = open(OUT_LIGHT).read()

# 3a. Drop near-white artifact paths (leftover halos)
def drop_white_paths(svg_text):
    def repl(m):
        hexcol = m.group(1)
        r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
        if min(r, g, b) > 230:
            return ''
        return m.group(0)
    return re.sub(r'<path [^>]*fill="#([0-9A-Fa-f]{6})"[^>]*/>\n?', repl, svg_text)

svg = drop_white_paths(svg)
open(OUT_LIGHT, 'w').write(svg)

# 3b. Dark version: replace dark navy fills (text) with white
def lighten_dark(m):
    hexcol = m.group(1)
    r, g, b = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
    # Navy text is dark in ALL channels; icon blues/teals keep a bright channel
    if max(r, g, b) < 150:
        return 'fill="#FFFFFF"'
    return m.group(0)

svg_dark = re.sub(r'fill="#([0-9A-Fa-f]{6})"', lighten_dark, svg)
open(OUT_DARK, 'w').write(svg_dark)
print('Dark SVG written')

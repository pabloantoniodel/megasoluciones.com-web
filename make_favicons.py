import numpy as np
import vtracer
from PIL import Image

SRC = '/home/administrator/megasoluciones/static/images/logo.png'
IMG_DIR = '/home/administrator/megasoluciones/static/images'

# 1. White background -> transparent (color-to-alpha, same as the logo vectorization)
img = Image.open(SRC).convert('RGBA')
arr = np.asarray(img).astype(np.float32)
rgb = arr[:, :, :3]
alpha = 255.0 - rgb.min(axis=2)
safe_alpha = np.maximum(alpha, 1.0)
unmixed = np.clip((rgb - (255.0 - alpha[:, :, None])) * (255.0 / safe_alpha[:, :, None]), 0, 255)
mask = alpha >= 100
out = np.zeros_like(arr, dtype=np.uint8)
out[:, :, :3] = unmixed.astype(np.uint8)
out[:, :, 3] = np.where(mask, 255, 0).astype(np.uint8)
img = Image.fromarray(out, 'RGBA')

# 2. Crop just the icon: find the empty column gap between icon and text
bbox = img.getbbox()
img = img.crop(bbox)
a = np.asarray(img)[:, :, 3]
col_filled = (a > 0).sum(axis=0)
gap_x = None
for x in range(400, img.width):
    if col_filled[x] == 0:
        gap_x = x
        break
print(f'Gap found at x={gap_x}')
icon = img.crop((0, 0, gap_x, img.height))
ib = icon.getbbox()
icon = icon.crop(ib)
print(f'Icon size: {icon.size}')

# 3. Make it square with a small margin
w, h = icon.size
side = int(max(w, h) * 1.06)
square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
square.paste(icon, ((side - w) // 2, (side - h) // 2), icon)

# 4. Export PNG + WEBP sizes (same filenames already used by the site)
for size in [16, 32, 64, 128, 192, 256, 512]:
    resized = square.resize((size, size), Image.LANCZOS)
    resized.save(f'{IMG_DIR}/logo-icon-{size}.png')
    resized.save(f'{IMG_DIR}/logo-icon-{size}.webp')
    print(f'logo-icon-{size}.png/webp')

# 5. favicon.ico multi-size
square.resize((256, 256), Image.LANCZOS).save(
    '/home/administrator/megasoluciones/static/favicon.ico',
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
)
print('favicon.ico')

# 6. favicon.svg: vector trace of the icon
tmp = '/tmp/icon_square.png'
square.save(tmp)
vtracer.convert_image_to_svg_py(
    tmp,
    f'{IMG_DIR}/favicon.svg',
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
print('favicon.svg')

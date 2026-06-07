#!/bin/bash
# Convierte PNG/JPEG de static/images a WebP para Core Web Vitals
set -e
DIR="$(dirname "$0")/../static/images"
cd "$DIR"
for f in *.png *.jpg *.jpeg 2>/dev/null; do
  [ -f "$f" ] || continue
  base="${f%.*}"
  if command -v cwebp >/dev/null 2>&1; then
    cwebp -q 82 "$f" -o "${base}.webp" 2>/dev/null && echo "OK ${base}.webp"
  elif command -v convert >/dev/null 2>&1; then
    convert "$f" -quality 82 "${base}.webp" && echo "OK ${base}.webp"
  elif python3 -c "from PIL import Image" 2>/dev/null; then
    python3 - "$f" "${base}.webp" <<'PY'
import sys
from PIL import Image
img = Image.open(sys.argv[1])
img.save(sys.argv[2], 'WEBP', quality=82)
print('OK', sys.argv[2])
PY
  else
    echo "Instala cwebp, imagemagick o pillow para convertir imágenes"
    exit 1
  fi
done
# Hero JPEG con nombre distinto
if [ -f hero-megasoluciones.png ]; then
  :
elif [ -f hero-megasoluciones.png ] || [ -f hero-megasoluciones.jpg ]; then
  true
fi
for f in hero-megasoluciones.png hero-megasoluciones.jpg; do
  [ -f "$f" ] || continue
  base="${f%.*}"
  if command -v cwebp >/dev/null 2>&1; then
    cwebp -q 85 "$f" -o "${base}.webp"
  fi
done
echo "Hecho."

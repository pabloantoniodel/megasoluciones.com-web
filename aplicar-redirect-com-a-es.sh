#!/bin/bash
# Restaura routing megasolucion.com → Flask (301 a .es en la app)
set -euo pipefail
SRC=/home/administrator/megasoluciones/traefik-megasolucion-com.yml
DEST=/etc/dokploy/traefik/dynamic/megasolucion-com.yml

if [ -w "$DEST" ] 2>/dev/null || sudo -n true 2>/dev/null; then
  sudo cp "$SRC" "$DEST"
else
  docker run --rm \
    -v "$SRC:/src/f.yml:ro" \
    -v /etc/dokploy/traefik/dynamic:/dest \
    alpine cp /src/f.yml /dest/megasolucion-com.yml
fi

docker restart dokploy-traefik
sleep 5

echo "=== megasolucion.es (debe 200) ==="
curl -sI https://megasolucion.es/ | head -3
echo "=== megasolucion.com (debe 301) ==="
curl -sI https://megasolucion.com/ | grep -iE 'HTTP|location|server' | head -4

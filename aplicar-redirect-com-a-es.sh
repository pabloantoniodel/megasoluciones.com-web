#!/bin/bash
# Aplica redirect Traefik megasolucion.com → megasolucion.es (301 directo)
set -euo pipefail
SRC=/home/administrator/megasoluciones/traefik-megasolucion-com.yml
DEST=/etc/dokploy/traefik/dynamic/megasolucion-com.yml

docker run --rm \
  -v "$SRC:/src/f.yml:ro" \
  -v /etc/dokploy/traefik/dynamic:/dest \
  alpine cp /src/f.yml /dest/megasolucion-com.yml

docker restart dokploy-traefik
sleep 6

echo "=== http://megasolucion.com (debe 301 → .es en 1 salto) ==="
curl -sI http://megasolucion.com/ | grep -iE 'HTTP|location' | head -3
echo "=== https://megasolucion.com (debe 301 → .es) ==="
curl -sI https://megasolucion.com/ | grep -iE 'HTTP|location' | head -3
echo "=== https://megasolucion.es (debe 200) ==="
curl -sI https://megasolucion.es/ | head -2

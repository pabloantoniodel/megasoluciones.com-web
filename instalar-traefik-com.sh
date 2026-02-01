#!/bin/bash
# Instalar config Traefik para megasolucion.com
# Ejecutar: sudo bash instalar-traefik-com.sh

cp /home/administrator/megasoluciones/traefik-megasolucion-com.yml /etc/dokploy/traefik/dynamic/megasolucion-com.yml
echo "Config instalada. Traefik recargará automáticamente."

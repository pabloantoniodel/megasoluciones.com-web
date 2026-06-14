#!/bin/bash

# Despliega Megasoluciones como SERVICIO SWARM para que Traefik descubra megasolucion.es
# En Swarm, Traefik solo descubre servicios (no contenedores sueltos con docker compose).

set -e

cd "$(dirname "$0")"

echo "🔧 Megasoluciones - Deploy como Swarm Stack (dominio megasolucion.es)"
echo "=========================================================================="
echo ""

# 1. Detener contenedor compose si existe
echo "⏹️  Deteniendo contenedor docker-compose (si existe)..."
docker compose -f docker-compose.yml -f docker-compose.traefik.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true
echo ""

# 2. Construir imagen
echo "🔨 Construyendo imagen megasoluciones:latest..."
docker build -t megasoluciones:latest .
echo ""

# 3. Cargar variables .env
if [ -f .env ]; then
  echo "📂 Cargando variables desde .env"
  set -a
  source .env
  set +a
else
  echo "⚠️  No existe .env - las variables MAIL_* quedarán vacías"
  echo "   Crea .env con MAIL_USERNAME, MAIL_PASSWORD, etc."
fi
echo ""

# 4. Desplegar stack
echo "🚀 Desplegando stack megasoluciones (servicio Swarm)..."
docker stack deploy -c docker-compose.stack.yml megasoluciones
echo ""

echo "⏳ Esperando que el servicio arranque (15s)..."
sleep 15

echo ""
echo "📊 Estado del servicio:"
docker stack services megasoluciones

echo ""
echo "✅ Despliegue completado."
echo ""
echo "🌐 La web debería estar disponible en: https://megasolucion.es"
echo "   (Traefik descubre servicios Swarm; el dominio debería funcionar ahora)"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs:     docker service logs megasoluciones_megasoluciones -f"
echo "   Ver tareas:   docker stack ps megasoluciones"
echo "   Quitar stack: docker stack rm megasoluciones"
echo ""

#!/bin/bash

# Script de configuración Traefik para Megasoluciones
# Configura megasolucion.es (y alias .com → .es) con certificado SSL automático

echo "🚀 Configurando Megasoluciones con Traefik"
echo "=========================================="
echo ""

# Verificar que el DNS esté configurado
echo "📡 Verificando DNS..."
IP_SERVER=$(hostname -I | awk '{print $1}')
echo "IP del servidor: $IP_SERVER"
echo ""
echo "⚠️  IMPORTANTE: Asegúrate de que el DNS esté configurado:"
echo "   megasolucion.es → $IP_SERVER"
echo "   megasolucion.com → $IP_SERVER (alias 301 → .es)"
echo ""
echo "Puertos necesarios abiertos en firewall:"
echo "   - Puerto 80 (HTTP)"
echo "   - Puerto 443 (HTTPS)"
echo ""

read -p "¿DNS configurado correctamente? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Configura el DNS primero y vuelve a ejecutar este script"
    exit 1
fi

# Detener contenedor actual
echo ""
echo "⏹️  Deteniendo contenedor actual..."
docker-compose down

# Iniciar con Traefik
echo ""
echo "▶️  Iniciando con Traefik + SSL..."
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d

# Esperar inicio
echo ""
echo "⏳ Esperando que el servicio inicie..."
sleep 5

# Verificar estado
echo ""
echo "📊 Estado del servicio:"
docker-compose ps

echo ""
echo "✅ Configuración completada!"
echo ""
echo "🌐 Tu web estará disponible en:"
echo "   https://megasolucion.es"
echo "   https://www.megasolucion.es"
echo ""
echo "🔒 Certificado SSL:"
echo "   - Se generará automáticamente con Let's Encrypt"
echo "   - Primera solicitud puede tardar 1-2 minutos"
echo "   - Se renovará automáticamente cada 60 días"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs: docker-compose logs -f"
echo "   Detener: docker compose -f docker-compose.yml -f docker-compose.traefik.yml down"
echo "   Reiniciar: docker compose -f docker-compose.yml -f docker-compose.traefik.yml restart"
echo ""

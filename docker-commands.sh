#!/bin/bash

# Script de gestión Docker para Megasoluciones

echo "🚀 MEGASOLUCIONES - Docker Manager"
echo "===================================="
echo ""

case "$1" in
    start)
        echo "▶️  Iniciando Megasoluciones..."
        docker-compose up -d
        echo "✅ Aplicación iniciada en http://localhost:5000"
        ;;
    stop)
        echo "⏹️  Deteniendo Megasoluciones..."
        docker-compose down
        echo "✅ Aplicación detenida"
        ;;
    restart)
        echo "🔄 Reiniciando Megasoluciones..."
        docker-compose restart
        echo "✅ Aplicación reiniciada"
        ;;
    logs)
        echo "📋 Mostrando logs..."
        docker-compose logs -f
        ;;
    status)
        echo "📊 Estado del contenedor:"
        docker-compose ps
        ;;
    build)
        echo "🔨 Reconstruyendo imagen..."
        docker-compose up --build -d
        echo "✅ Imagen reconstruida y aplicación iniciada"
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|logs|status|build}"
        echo ""
        echo "Comandos disponibles:"
        echo "  start   - Iniciar la aplicación"
        echo "  stop    - Detener la aplicación"
        echo "  restart - Reiniciar la aplicación"
        echo "  logs    - Ver logs en tiempo real"
        echo "  status  - Ver estado del contenedor"
        echo "  build   - Reconstruir la imagen"
        exit 1
        ;;
esac

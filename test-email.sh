#!/bin/bash

# Script para probar envío de email desde Megasoluciones

echo "📧 Test de Email - Megasoluciones"
echo "=================================="
echo ""

# Verificar que .env existe
if [ ! -f ".env" ]; then
    echo "❌ Error: Archivo .env no encontrado"
    echo "   Crear .env con configuración SMTP"
    exit 1
fi

# Verificar variables SMTP
source .env

if [ -z "$MAIL_USERNAME" ] || [ -z "$MAIL_PASSWORD" ]; then
    echo "❌ Error: Variables SMTP no configuradas"
    echo "   Configurar MAIL_USERNAME y MAIL_PASSWORD en .env"
    exit 1
fi

echo "✅ Variables SMTP configuradas:"
echo "   Servidor: $MAIL_SERVER"
echo "   Puerto: $MAIL_PORT"
echo "   Usuario: $MAIL_USERNAME"
echo ""

echo "📋 Para probar el envío de emails:"
echo ""
echo "1. Ve a: https://megasolucion.es/contacto"
echo "2. Completa el formulario con:"
echo "   - Tu nombre"
echo "   - Tu email"
echo "   - Un mensaje de prueba"
echo "3. Click en 'Enviar Mensaje'"
echo "4. Revisa la bandeja de entrada de: info@megasolucion.net"
echo ""

echo "📊 Ver logs en tiempo real:"
echo "   docker-compose logs -f"
echo ""

echo "✅ Sistema listo para enviar emails!"

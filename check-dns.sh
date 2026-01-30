#!/bin/bash

# Script para verificar configuración DNS de megasolucion.com

echo "🔍 Verificando DNS para megasolucion.com"
echo "========================================"
echo ""

# IP del servidor
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "📍 IP del servidor: $SERVER_IP"
echo ""

# Verificar DNS principal
echo "🌐 Verificando megasolucion.com..."
DNS_IP=$(dig +short megasolucion.com @8.8.8.8 | tail -1)

if [ -z "$DNS_IP" ]; then
    echo "❌ megasolucion.com NO resuelve a ninguna IP"
    echo "   👉 Configura un registro A en tu proveedor DNS:"
    echo "      Tipo: A"
    echo "      Nombre: @"
    echo "      Valor: $SERVER_IP"
else
    echo "✅ megasolucion.com → $DNS_IP"
    if [ "$DNS_IP" = "$SERVER_IP" ]; then
        echo "   ✅ Apunta correctamente a este servidor"
    else
        echo "   ⚠️  NO apunta a este servidor ($SERVER_IP)"
        echo "   👉 Actualiza el registro A para apuntar a: $SERVER_IP"
    fi
fi

echo ""

# Verificar www
echo "🌐 Verificando www.megasolucion.com..."
WWW_IP=$(dig +short www.megasolucion.com @8.8.8.8 | tail -1)

if [ -z "$WWW_IP" ]; then
    echo "❌ www.megasolucion.com NO resuelve"
    echo "   👉 Configura un registro A (opcional):"
    echo "      Tipo: A"
    echo "      Nombre: www"
    echo "      Valor: $SERVER_IP"
else
    echo "✅ www.megasolucion.com → $WWW_IP"
    if [ "$WWW_IP" = "$SERVER_IP" ]; then
        echo "   ✅ Apunta correctamente a este servidor"
    else
        echo "   ⚠️  NO apunta a este servidor ($SERVER_IP)"
    fi
fi

echo ""
echo "=========================================="

# Verificar si el DNS está OK
if [ "$DNS_IP" = "$SERVER_IP" ]; then
    echo "✅ DNS configurado correctamente!"
    echo ""
    echo "🔒 El certificado SSL se generará automáticamente en:"
    echo "   https://megasolucion.com"
    echo ""
    echo "⏱️  Primera visita puede tardar 1-2 minutos mientras"
    echo "   Let's Encrypt valida el dominio y emite el certificado."
    echo ""
    echo "📋 Para ver el proceso:"
    echo "   docker-compose logs -f | grep -i certificate"
else
    echo "⚠️  DNS no está configurado correctamente"
    echo ""
    echo "📝 Pasos a seguir:"
    echo "1. Ve al panel de tu proveedor DNS (Namecheap, GoDaddy, etc.)"
    echo "2. Crea estos registros:"
    echo ""
    echo "   Tipo: A"
    echo "   Nombre: @"
    echo "   Valor: $SERVER_IP"
    echo "   TTL: 300"
    echo ""
    echo "   Tipo: A"
    echo "   Nombre: www"
    echo "   Valor: $SERVER_IP"
    echo "   TTL: 300"
    echo ""
    echo "3. Espera 5-10 minutos para propagación DNS"
    echo "4. Ejecuta este script de nuevo: ./check-dns.sh"
fi

echo ""

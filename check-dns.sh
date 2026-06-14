#!/bin/bash

# Script para verificar configuración DNS de megasolucion.es

echo "🔍 Verificando DNS para megasolucion.es"
echo "========================================"
echo ""

SERVER_IP=$(hostname -I | awk '{print $1}')
echo "📍 IP del servidor: $SERVER_IP"
echo ""

check_domain() {
    local label="$1"
    local domain="$2"
    echo "🌐 Verificando $domain..."
    local ip
    ip=$(dig +short "$domain" @8.8.8.8 | tail -1)
    if [ -z "$ip" ]; then
        echo "❌ $domain NO resuelve a ninguna IP"
        return 1
    fi
    echo "✅ $domain → $ip"
    if [ "$ip" = "$SERVER_IP" ]; then
        echo "   ✅ Apunta correctamente a este servidor"
        return 0
    fi
    echo "   ⚠️  NO apunta a este servidor ($SERVER_IP)"
    return 1
}

OK_ES=0
check_domain "principal" "megasolucion.es" && OK_ES=1
echo ""
check_domain "www" "www.megasolucion.es"
echo ""
echo "ℹ️  Alias megasolucion.com (301 → .es):"
check_domain "alias" "megasolucion.com" || true
echo ""

echo "=========================================="
if [ "$OK_ES" = 1 ]; then
    echo "✅ DNS de megasolucion.es configurado correctamente!"
    echo ""
    echo "🔒 Certificado SSL en: https://megasolucion.es"
else
    echo "⚠️  megasolucion.es no apunta a este servidor"
    echo ""
    echo "📝 Crea en tu DNS:"
    echo "   A  @   → $SERVER_IP"
    echo "   A  www → $SERVER_IP"
fi
echo ""

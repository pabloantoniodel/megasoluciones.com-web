# 🔒 Megasoluciones con Traefik + SSL Automático

## 📋 Configuración Completa

### 1️⃣ Configurar DNS (IMPORTANTE)

**Antes de desplegar**, configura estos registros DNS en tu proveedor:

```
Tipo: A
Nombre: @
Valor: 69.197.164.198
TTL: 300

Tipo: A
Nombre: www
Valor: 69.197.164.198
TTL: 300
```

**Verificar DNS** (espera 5-10 minutos después de configurar):
```bash
# Verificar dominio principal
dig megasolucion.com +short

# Verificar www
dig www.megasolucion.com +short

# Ambos deben mostrar: 69.197.164.198
```

### 2️⃣ Verificar Puertos Abiertos

Los puertos **80** y **443** deben estar abiertos en el firewall:

```bash
# Verificar firewall
sudo ufw status

# Si necesitas abrir puertos:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3️⃣ Desplegar con Traefik

**Opción A - Script Automático** (Recomendado):
```bash
cd /home/administrator/megasoluciones
./setup-traefik.sh
```

**Opción B - Manual**:
```bash
cd /home/administrator/megasoluciones

# Detener contenedor actual
docker-compose down

# Iniciar con Traefik
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d
```

### 4️⃣ Verificar Certificado SSL

El certificado se genera automáticamente en la **primera visita**:

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Esperar mensaje: "acme: Obtaining certificate"
# Luego: "Server responded with a certificate"
```

**Primera visita**: https://megasolucion.com
- Puede tardar 1-2 minutos en generar el certificado
- Luego será instantáneo

## 🌐 URLs Configuradas

✅ **HTTP** → **HTTPS** (redirect automático):
- http://megasolucion.com → https://megasolucion.com
- http://www.megasolucion.com → https://www.megasolucion.com

✅ **HTTPS** con certificado válido:
- https://megasolucion.com ✅
- https://www.megasolucion.com ✅

## 🔧 Gestión

### Ver Logs
```bash
cd /home/administrator/megasoluciones
docker-compose logs -f
```

### Reiniciar
```bash
docker compose -f docker-compose.yml -f docker-compose.traefik.yml restart
```

### Detener
```bash
docker compose -f docker-compose.yml -f docker-compose.traefik.yml down
```

### Reconstruir
```bash
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d
```

## 🔒 Certificado SSL

**Proveedor**: Let's Encrypt
**Tipo**: Domain Validated (DV)
**Validez**: 90 días
**Renovación**: Automática (cada 60 días)
**Algoritmo**: ECDSA P-384

**Verificar certificado**:
```bash
# Online
https://www.ssllabs.com/ssltest/analyze.html?d=megasolucion.com

# Terminal
openssl s_client -connect megasolucion.com:443 -servername megasolucion.com | openssl x509 -noout -dates
```

## 📊 Estado del Sistema

```bash
# Ver contenedores
docker ps | grep megasoluciones

# Ver redes
docker network inspect dokploy-network

# Ver uso de recursos
docker stats megasoluciones-web
```

## 🚨 Troubleshooting

### Problema: "Certificate obtain failed"

**Causa**: DNS no apunta correctamente o puertos cerrados

**Solución**:
```bash
# 1. Verificar DNS
dig megasolucion.com +short

# 2. Verificar puertos desde internet
curl -I http://megasolucion.com
curl -I https://megasolucion.com

# 3. Ver logs detallados
docker-compose logs | grep -i certificate
```

### Problema: "Gateway Timeout"

**Causa**: Servicio Flask no responde

**Solución**:
```bash
# Ver logs del contenedor
docker logs megasoluciones-web -f

# Reiniciar servicio
docker-compose restart
```

### Problema: "Too many failed authorizations"

**Causa**: Demasiados intentos fallidos de Let's Encrypt

**Solución**:
```bash
# Esperar 1 hora (rate limit de Let's Encrypt)
# Mientras tanto, usar staging:
# Editar labels en docker-compose.traefik.yml:
# - "traefik.http.routers.megasoluciones.tls.certresolver=letsencrypt-staging"
```

## 📈 Monitoreo

### Ver tráfico en tiempo real
```bash
docker-compose logs -f | grep megasolucion
```

### Verificar salud del servicio
```bash
curl -I https://megasolucion.com
```

### Ver métricas
```bash
docker stats megasoluciones-web --no-stream
```

## 🔐 Seguridad

✅ **HTTPS obligatorio** (HTTP redirige a HTTPS)
✅ **Certificado SSL válido** (Let's Encrypt)
✅ **Headers de seguridad** configurados
✅ **Puerto 5000 no expuesto** (solo Traefik tiene acceso)
✅ **TLS 1.2+** (protocolos seguros)

## 📝 Comandos Rápidos

```bash
# Status
docker-compose ps

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Full restart con rebuild
docker-compose down && docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d
```

---

**¡Tu web estará disponible en https://megasolucion.com con SSL válido!** 🚀🔒

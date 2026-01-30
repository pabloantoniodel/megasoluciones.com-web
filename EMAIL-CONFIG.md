# 📧 Configuración de Email para Formulario de Contacto

## ✅ Implementación Completa

El formulario de contacto ahora envía emails reales usando Flask-Mail.

---

## 🔧 CONFIGURACIÓN REQUERIDA

### 1. Crear archivo .env

```bash
cd /home/administrator/megasoluciones
cp .env.example .env
nano .env
```

### 2. Configurar Variables SMTP

Edita el archivo `.env` con tus credenciales:

```bash
# Variables básicas
SECRET_KEY=megasoluciones-secret-key-2026

# Configuración Email (REQUERIDO)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=info@megasolucion.net
MAIL_PASSWORD=tu-password-app-aqui
MAIL_DEFAULT_SENDER=info@megasolucion.net
```

---

## 📮 OPCIÓN 1: Gmail (Recomendado)

### Pasos para configurar Gmail:

#### 1. Habilitar verificación en 2 pasos
1. Ve a: https://myaccount.google.com/security
2. Activa "Verificación en 2 pasos"

#### 2. Generar App Password
1. Ve a: https://myaccount.google.com/apppasswords
2. Selecciona "Correo" y "Otro (nombre personalizado)"
3. Nombra: "Megasoluciones Web"
4. Click "Generar"
5. **Copia la contraseña de 16 caracteres**

#### 3. Configurar .env

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=info@megasolucion.net
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Tu App Password de 16 caracteres
MAIL_DEFAULT_SENDER=info@megasolucion.net
```

---

## 📮 OPCIÓN 2: Outlook/Hotmail

```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=info@megasolucion.net
MAIL_PASSWORD=tu-password-normal
MAIL_DEFAULT_SENDER=info@megasolucion.net
```

---

## 📮 OPCIÓN 3: SMTP Personalizado

Si tienes hosting con cPanel/Plesk:

```bash
MAIL_SERVER=mail.tudominio.com
MAIL_PORT=587  # O 465 para SSL
MAIL_USE_TLS=True  # O False si usas SSL
MAIL_USERNAME=info@megasolucion.net
MAIL_PASSWORD=tu-password-cpanel
MAIL_DEFAULT_SENDER=info@megasolucion.net
```

---

## 📮 OPCIÓN 4: SendGrid (Profesional)

Para producción con alto volumen:

```bash
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=tu-sendgrid-api-key
MAIL_DEFAULT_SENDER=info@megasolucion.net
```

Registro: https://sendgrid.com (100 emails/día gratis)

---

## 🚀 ACTIVAR EL ENVÍO DE EMAILS

### 1. Actualizar .env con credenciales reales

```bash
nano .env
# Completar MAIL_USERNAME y MAIL_PASSWORD
```

### 2. Reconstruir contenedor Docker

```bash
cd /home/administrator/megasoluciones

# Opción A: Con helper
./git-helper.sh deploy "feat: configurar envío de emails"

# Opción B: Manual
docker compose -f docker-compose.yml -f docker-compose.traefik.yml down
docker compose -f docker-compose.yml -f docker-compose.traefik.yml up --build -d
```

### 3. Actualizar docker-compose.traefik.yml

Asegúrate de que las variables de entorno se pasen al contenedor:

```yaml
services:
  megasoluciones:
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - MAIL_SERVER=${MAIL_SERVER}
      - MAIL_PORT=${MAIL_PORT}
      - MAIL_USE_TLS=${MAIL_USE_TLS}
      - MAIL_USERNAME=${MAIL_USERNAME}
      - MAIL_PASSWORD=${MAIL_PASSWORD}
      - MAIL_DEFAULT_SENDER=${MAIL_DEFAULT_SENDER}
```

---

## 🧪 PROBAR EL ENVÍO

### 1. Ir al formulario
```
https://megasolucion.com/contacto
```

### 2. Completar y enviar

### 3. Verificar logs
```bash
docker-compose logs -f | grep -i mail
```

### 4. Verificar bandeja de entrada
- Email llegará a: **info@megasolucion.net**
- Subject: "Nuevo contacto de [Nombre] - Megasoluciones"
- Incluye todos los datos del formulario

---

## 📊 FORMATO DEL EMAIL

### Email en HTML (bonito)
- ✅ Header con gradiente azul-verde
- ✅ Tabla con datos del contacto
- ✅ Mensaje en recuadro destacado
- ✅ Footer con fecha y hora

### Email en texto plano (fallback)
- ✅ Formato simple y legible
- ✅ Todos los datos incluidos

---

## 🔍 TROUBLESHOOTING

### Error: "SMTPAuthenticationError"

**Causa**: Credenciales incorrectas

**Solución**:
```bash
# Verificar .env
cat .env | grep MAIL_

# Para Gmail: usar App Password, no contraseña normal
# Regenerar App Password si es necesario
```

### Error: "Connection refused"

**Causa**: Puerto o servidor incorrecto

**Solución**:
```bash
# Verificar desde el servidor
telnet smtp.gmail.com 587

# Si falla, verificar firewall
sudo ufw allow out 587/tcp
```

### Error: "Must issue a STARTTLS command first"

**Causa**: TLS no configurado correctamente

**Solución**:
```bash
# En .env asegurar:
MAIL_USE_TLS=True
```

### Emails no llegan

**Verificar**:
1. ✅ .env tiene todas las variables
2. ✅ Contenedor reiniciado después de configurar
3. ✅ Revisar carpeta de SPAM
4. ✅ Ver logs: `docker-compose logs`

---

## 🔐 SEGURIDAD

### ⚠️ IMPORTANTE

1. ✅ **Nunca commits .env al git** (está en .gitignore)
2. ✅ **Usa App Passwords**, no contraseñas normales
3. ✅ **Habilita 2FA** en tu cuenta de email
4. ✅ **Limita permisos** del App Password solo a "Mail"

---

## 📝 FUNCIONAMIENTO

### Sin configuración SMTP
- ✅ Formulario funciona
- ✅ Muestra mensaje de éxito
- ❌ No envía email (solo muestra flash message)

### Con configuración SMTP
- ✅ Formulario funciona
- ✅ **Envía email real** a info@megasolucion.net
- ✅ Email con formato HTML profesional
- ✅ Incluye todos los datos del formulario
- ✅ Reply-to configurado al email del usuario

---

## 🎯 CARACTERÍSTICAS IMPLEMENTADAS

### Email al administrador
- ✅ Asunto: "Nuevo contacto de [Nombre] - Megasoluciones"
- ✅ Para: info@megasolucion.net
- ✅ Reply-To: email del usuario (puedes responder directo)
- ✅ HTML + texto plano
- ✅ Fecha y hora del envío

### Datos incluidos
- ✅ Nombre
- ✅ Email (con link mailto)
- ✅ Teléfono
- ✅ Empresa
- ✅ Mensaje completo
- ✅ Timestamp

---

## 🚀 PRÓXIMOS PASOS (Opcional)

### Email de confirmación al usuario
Añadir un segundo email para el usuario confirmando recepción.

### Guardar en base de datos
Almacenar contactos en SQLite/PostgreSQL para histórico.

### Notificaciones
- Webhook a Slack/Discord
- SMS via Twilio
- Telegram bot

---

## 📞 SOPORTE

Si tienes problemas:

1. Verificar logs: `docker-compose logs -f`
2. Probar SMTP: Ver section de troubleshooting
3. Contactar hosting si usas SMTP personalizado

---

**¡Emails configurados y listos!** 📧✅

# Consolidación técnica: megasolucion.es como dominio principal

> Marca: **Megasoluciones** · Dominio canónico: **https://megasolucion.es**  
> megasolucion.com redirige **301** a megasolucion.es (misma ruta)  
> Archivos listos para copiar en: `docs/dominio-es/`

---

## 1. Estado actual en producción (ya implementado)

| Elemento | Estado |
|----------|--------|
| 301 `.com` → `.es` (todas las rutas) | ✅ Flask + Traefik |
| 301 `www.megasolucion.es` → apex | ✅ Flask |
| Canonical siempre `.es` | ✅ `templates/base.html` |
| Sitemap solo URLs `.es` | ✅ `/sitemap.xml` dinámico |
| robots.txt diferenciado por host | ✅ `.es` permite / `.com` Disallow |

**No inventar URLs nuevas:** el sitemap incluye solo las 22 URLs que existen hoy en la web.

---

## 2. Mapa de redirecciones 301

| Origen | Destino |
|--------|---------|
| `http://megasolucion.com/` | `https://megasolucion.es/` |
| `https://megasolucion.com/` | `https://megasolucion.es/` |
| `https://www.megasolucion.com/` | `https://megasolucion.es/` |
| `https://megasolucion.com/contacto` | `https://megasolucion.es/contacto` |
| `https://megasolucion.com/recursos/slug` | `https://megasolucion.es/recursos/slug` |
| `https://www.megasolucion.es/cualquier-ruta` | `https://megasolucion.es/cualquier-ruta` |

Regla: **`$request_uri` se conserva** — la ruta y query string pasan al dominio `.es`.

---

## 3. Reglas por plataforma (copiar)

### NGINX
Archivo: `docs/dominio-es/nginx-megasoluciones.conf`

```nginx
# Resumen clave — .com → .es
return 301 https://megasolucion.es$request_uri;
```

### Apache
Archivo: `docs/dominio-es/apache-megasoluciones.htaccess`

```apache
RewriteCond %{HTTP_HOST} ^(www\.)?megasolucion\.com$ [NC]
RewriteRule ^(.*)$ https://megasolucion.es/$1 [R=301,L]
```

### Cloudflare
Archivo: `docs/dominio-es/cloudflare-megasoluciones.md`

```
Dynamic redirect: concat("https://megasolucion.es", http.request.uri.path)
Status: 301
```

### Traefik (tu servidor Dokploy)
Archivos en repo: `traefik-megasolucion-com.yml`, `traefik-megasolucion-es.yml`  
El 301 lo hace **Flask** (Traefik solo hace proxy). No activar `redirectRegex` en Traefik (devuelve 308 y falla GSC).

---

## 4. Canonical (todas las páginas)

Ya en `templates/base.html` — **no cambiar manualmente por página**:

```html
<link rel="canonical" href="{{ canonical_url }}">
<link rel="alternate" hreflang="es-ES" href="https://megasolucion.es/...">
<link rel="alternate" hreflang="x-default" href="https://megasolucion.es/...">
<meta property="og:url" content="{{ canonical_url }}">
```

`canonical_url()` en `app.py` **siempre** devuelve `https://megasolucion.es` + ruta actual.

**Ejemplos reales:**

```html
<!-- Home -->
<link rel="canonical" href="https://megasolucion.es/">

<!-- Contacto -->
<link rel="canonical" href="https://megasolucion.es/contacto">

<!-- Artículo -->
<link rel="canonical" href="https://megasolucion.es/recursos/seo-geo-inteligencia-artificial-2026">
```

**Nunca** debe aparecer `megasolucion.com` en canonical, og:url ni hreflang.

---

## 5. robots.txt

### megasolucion.es (dominio principal)

Archivo referencia: `docs/dominio-es/robots-megasolucion-es.txt`

```
User-agent: *
Allow: /
Disallow: /health

Sitemap: https://megasolucion.es/sitemap.xml
```

### megasolucion.com (bloquear indexación)

Archivo referencia: `docs/dominio-es/robots-megasolucion-com.txt`

```
User-agent: *
Disallow: /
```

**Nota técnica:** Un `robots.txt` en `.es` no puede bloquear otro dominio (`.com`). Por eso:
1. `.com` tiene su propio `robots.txt` con `Disallow: /`
2. Todas las páginas `.com` redirigen **301** a `.es`

---

## 6. sitemap.xml (megasolucion.es)

**URL en producción:** https://megasolucion.es/sitemap.xml (dinámico, se actualiza solo)

**Copia estática de referencia:** `docs/dominio-es/sitemap-megasolucion-es.xml`

### 22 URLs indexables (todas reales)

**Páginas principales (11)**
- https://megasolucion.es/
- https://megasolucion.es/desarrollo-software
- https://megasolucion.es/automatizaciones
- https://megasolucion.es/servicios
- https://megasolucion.es/sobre
- https://megasolucion.es/portfolio
- https://megasolucion.es/testimonios
- https://megasolucion.es/contacto
- https://megasolucion.es/recursos
- https://megasolucion.es/privacidad
- https://megasolucion.es/aviso-legal

**Artículos /recursos (7)**
- https://megasolucion.es/recursos/seo-geo-inteligencia-artificial-2026
- https://megasolucion.es/recursos/automatizar-procesos-pyme
- https://megasolucion.es/recursos/coste-desarrollo-software-2026
- https://megasolucion.es/recursos/rpa-vs-automatizacion-apis
- https://megasolucion.es/recursos/integrar-odoo-web-crm
- https://megasolucion.es/recursos/procesos-automatizar-empresa
- https://megasolucion.es/recursos/elegir-empresa-desarrollo-software

**Portfolio (4)**
- https://megasolucion.es/portfolio/plataforma-gestion-medida
- https://megasolucion.es/portfolio/automatizacion-erp-crm
- https://megasolucion.es/portfolio/portal-clientes-api-bancaria
- https://megasolucion.es/portfolio/rpa-documental-ocr

**No incluidas (correcto):** `/health`, anclas `#chatbots-ia`, URLs `.com`

---

## 7. Google Search Console — paso a paso

### Fase 1: Verificar ambas propiedades (ya hecho ✓)
- Propiedad **megasolucion.es** (prefijo o dominio)
- Propiedad **megasolucion.com**

### Fase 2: Cambio de dominio (migrar autoridad .com → .es)
1. Entra en la propiedad **megasolucion.com**
2. **Configuración** (engranaje) → **Cambio de dominio**
3. Selecciona destino: **megasolucion.es**
4. **Validar** — debe pasar:
   - ✅ Verificación de ambos sitios
   - ✅ Redirección **301** de página de inicio
   - ✅ (Recomendado) Redirecciones 301 de páginas de ejemplo
5. **Confirmar** el cambio

Google transferirá señales durante **semanas/meses**; no es instantáneo.

### Fase 3: Sitemap solo en .es
1. Propiedad **megasolucion.es** → **Sitemaps**
2. Añadir: `sitemap.xml` (o URL completa `https://megasolucion.es/sitemap.xml`)
3. Estado debe ser **Correcto**
4. En propiedad **megasolucion.com**: **no añadir sitemap** (o eliminar si existe)

### Fase 4: Forzar indexación de la home
1. Propiedad **megasolucion.es** → **Inspección de URLs**
2. Pega: `https://megasolucion.es/`
3. **Probar URL publicada** → debe mostrar canonical `megasolucion.es`
4. **Solicitar indexación**

Repite para URLs clave: `/servicios`, `/contacto`, `/desarrollo-software`, `/automatizaciones`

### Fase 5: Gestionar megasolucion.com sin perder autoridad
- **No elimines** la propiedad `.com` de inmediato
- Mantén el **301 activo mínimo 6–12 meses**
- Tras el cambio de dominio confirmado, Google dejará de indexar `.com` gradualmente
- Opcional (6+ meses después): eliminar propiedad `.com` en GSC cuando indexación `.com` ≈ 0

### Fase 6: Comprobar dominio canónico
En **Inspección de URLs** de `https://megasolucion.com/`:
- Debe decir: **Redirección** → URL final `https://megasolucion.es/`
- No debe indexar contenido duplicado en `.com`

---

## 8. Checklist de validación

### Redirecciones
```bash
curl -sI https://megasolucion.com/ | grep -iE 'HTTP|location'
# Esperado: HTTP/2 301 + location: https://megasolucion.es/

curl -sI https://megasolucion.com/contacto | grep -i location
# Esperado: location: https://megasolucion.es/contacto

curl -sI https://www.megasolucion.com/servicios | grep -i location
# Esperado: location: https://megasolucion.es/servicios

curl -sI https://www.megasolucion.es/ | grep -i location
# Esperado: location: https://megasolucion.es/
```

### Canonical
```bash
curl -sL https://megasolucion.es/ | grep canonical
# Esperado: href="https://megasolucion.es/"

curl -sL https://megasolucion.es/contacto | grep canonical
# Esperado: href="https://megasolucion.es/contacto"
```

### robots.txt
```bash
curl -sL https://megasolucion.es/robots.txt
# Esperado: Allow: / + Sitemap: https://megasolucion.es/sitemap.xml

curl -sL https://megasolucion.com/robots.txt
# Esperado: Disallow: /
```

### Sitemap
```bash
curl -sL https://megasolucion.es/sitemap.xml | grep -c '<loc>'
# Esperado: 22

curl -sL https://megasolucion.es/sitemap.xml | grep megasolucion.com
# Esperado: (vacío — ninguna URL .com)
```

### Sin contenido duplicado
- [ ] Ninguna página sirve **200** en `.com` (solo 301)
- [ ] Canonical nunca apunta a `.com`
- [ ] Sitemap solo contiene URLs `.es`
- [ ] hreflang `x-default` apunta a `.es`

### Google Search Console
- [ ] Cambio de dominio `.com` → `.es` validado
- [ ] Sitemap enviado en propiedad `.es`
- [ ] Home `.es` solicitada para indexación
- [ ] Inspección de `megasolucion.com` muestra redirección a `.es`

### Marca Megasoluciones
- [ ] `<title>` y schema usan **Megasoluciones** (con s)
- [ ] `og:site_name` / JSON-LD `name`: Megasoluciones
- [ ] Misma descripción en web, GSC y Google Business (si aplica)

---

## 9. Comandos de despliegue (Traefik + Flask)

```bash
# Actualizar Traefik (proxy sin redirectRegex 308)
sudo cp /home/administrator/megasoluciones/traefik-megasolucion-com.yml /etc/dokploy/traefik/dynamic/megasolucion-com.yml
sudo cp /home/administrator/megasoluciones/traefik-megasolucion-es.yml /etc/dokploy/traefik/dynamic/megasoluciones-web-megasoluciones-6gi9az.yml
docker restart dokploy-traefik

# Actualizar app Flask
cd /home/administrator/megasoluciones
docker build -t megasoluciones:latest .
docker service update --force megasoluciones_megasoluciones
```

---

## 10. Resumen ejecutivo

| Dominio | Rol | Indexación |
|---------|-----|------------|
| **megasolucion.es** | Principal, canonical, sitemap | ✅ Permitida |
| **www.megasolucion.es** | 301 → apex | ❌ No indexar |
| **megasolucion.com** | 301 → .es + robots Disallow | ❌ No indexar |
| **www.megasolucion.com** | 301 → .es | ❌ No indexar |

La autoridad de `.com` se conserva mediante **301 permanentes** + **Cambio de dominio en GSC**, no eliminando el dominio de golpe.

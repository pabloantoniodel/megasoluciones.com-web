# Cloudflare — Consolidación megasolucion.com → megasolucion.es

## Opción A: Redirect Rules (recomendado, panel Cloudflare)

### Regla 1 — .com → .es (todas las rutas)

1. **Rules** → **Redirect Rules** → **Create rule**
2. Nombre: `com to es 301`
3. **When incoming requests match:**
   - Field: `Hostname`
   - Operator: `equals`
   - Value: `megasolucion.com`
   - **OR** (añadir condición)
   - Field: `Hostname` → `equals` → `www.megasolucion.com`
4. **Then:**
   - Type: **Dynamic**
   - Expression: `concat("https://megasolucion.es", http.request.uri.path)`
   - Status code: **301**
5. **Deploy**

### Regla 2 — www.megasolucion.es → apex

1. Nombre: `www es to apex 301`
2. **When:** Hostname equals `www.megasolucion.es`
3. **Then:** Dynamic → `concat("https://megasolucion.es", http.request.uri.path)` → **301**

---

## Opción B: Bulk Redirects (lista estática)

**Bulk Redirects** → crear lista `com-to-es`:

| Source URL | Target URL | Status |
|------------|------------|--------|
| `https://megasolucion.com/*` | `https://megasolucion.es/${1}` | 301 |
| `https://www.megasolucion.com/*` | `https://megasolucion.es/${1}` | 301 |

---

## Opción C: Page Rules (legado, máx. 3 gratis)

```
URL: *megasolucion.com/*
Setting: Forwarding URL → 301 Permanent Redirect
Destination: https://megasolucion.es/$1
```

---

## DNS recomendado

| Registro | Nombre | Destino | Proxy |
|----------|--------|---------|-------|
| A / CNAME | `megasolucion.es` | IP/servidor | Proxied ☁️ |
| A / CNAME | `www` (.es) | igual | Proxied ☁️ |
| A / CNAME | `megasolucion.com` | igual (para que el 301 funcione) | Proxied ☁️ |
| A / CNAME | `www` (.com) | igual | Proxied ☁️ |

**Importante:** Si usas Redirect Rules en Cloudflare Y redirección en Traefik/Flask, evita doble redirect. Deja solo una capa activa.

---

## SSL/TLS

- Modo: **Full (strict)**
- **Edge Certificates** → activar **Always Use HTTPS**
- **HSTS** (opcional, solo cuando todo esté estable): max-age 31536000, includeSubDomains

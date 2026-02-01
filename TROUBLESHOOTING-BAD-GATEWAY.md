# 🔧 Bad Gateway (502) - Megasoluciones

## Causa real: Traefik en Swarm solo descubre SERVICIOS

**Tu Docker está en modo Swarm** (Dokploy). En Swarm, Traefik **solo descubre servicios** (creados con `docker stack deploy`), **no contenedores** creados con `docker compose up`.

- **localhost:5000 va bien** → la app está corriendo.
- **megasolucion.com da 502** → Traefik no tiene backend para ese dominio porque el contenedor no es un servicio Swarm.

### ✅ Solución: desplegar como Swarm Stack

Usa el script que despliega Megasoluciones como **servicio Swarm** para que Traefik lo descubra:

```bash
cd /home/administrator/megasoluciones
chmod +x deploy-stack.sh
./deploy-stack.sh
```

O manualmente:

```bash
cd /home/administrator/megasoluciones

# 1. Detener compose
docker compose -f docker-compose.yml -f docker-compose.traefik.yml down

# 2. Construir imagen
docker build -t megasoluciones:latest .

# 3. Cargar .env y desplegar stack
set -a && source .env && set +a
docker stack deploy -c docker-compose.stack.yml megasoluciones
```

Tras el despliegue, **https://megasolucion.com** debería responder correctamente.

### Alternativa (solo para pruebas): compose sin dominio

Si no usas el dominio y solo quieres probar en local:

```bash
docker compose -f docker-compose.yml up -d
# Acceso: http://localhost:5000
```

---

## Comprobar que está bien

### 1. Servicio Swarm activo

```bash
docker stack services megasoluciones
```

Debe mostrar 1/1 réplicas.

### 2. Tareas del stack

```bash
docker stack ps megasoluciones
```

Debe haber una tarea en estado "Running".

### 3. Logs del servicio

```bash
docker service logs megasoluciones_megasoluciones -f
```

### 4. Logs de Traefik (Dokploy)

Revisar los logs del servicio Traefik en Dokploy para ver si ya descubre el backend megasoluciones.

---

## Comandos útiles (Stack)

```bash
# Ver servicios del stack
docker stack services megasoluciones

# Ver logs
docker service logs megasoluciones_megasoluciones -f

# Actualizar (tras cambiar código)
./deploy-stack.sh

# Quitar stack
docker stack rm megasoluciones
```

---

## Resumen

| Método | Dominio megasolucion.com | localhost:5000 |
|--------|--------------------------|----------------|
| `docker compose up` | ❌ 502 (Traefik no lo descubre) | ✅ |
| `docker stack deploy` | ✅ | ❌ (puerto no publicado) |

**Para que el dominio funcione: desplegar con `./deploy-stack.sh` (Swarm Stack).**

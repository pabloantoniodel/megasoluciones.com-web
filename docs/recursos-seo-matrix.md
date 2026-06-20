# Matriz SEO — sección /recursos

Documento operativo para evitar canibalización y mantener coherencia editorial en megasolucion.es/recursos.

## Pilares por cluster

| Cluster | Slug pilar | Keyword principal |
|---------|------------|-------------------|
| IA | `seo-geo-inteligencia-artificial-2026` | seo geo inteligencia artificial |
| Desarrollo | `elegir-empresa-desarrollo-software` | elegir empresa desarrollo software |
| Automatizaciones | `automatizar-procesos-pyme` | automatizar procesos pyme |

## Artículos estáticos

| Slug | Cluster | Tipo | Intención | Keyword principal |
|------|---------|------|-----------|-------------------|
| seo-geo-inteligencia-artificial-2026 | ia | pilar | informacional | seo geo inteligencia artificial |
| agencia-ia-madrid-apuesta-comunidad-pymes | ia | soporte | comercial | agencia ia madrid pymes |
| desarrolladores-ia-gestion-automatizacion-empresas | ia | soporte | informacional | ia empresas produccion desarrolladores |
| elegir-empresa-desarrollo-software | desarrollo | pilar | comercial | elegir empresa desarrollo software |
| coste-desarrollo-software-2026 | desarrollo | soporte | comercial | coste desarrollo software a medida |
| integrar-odoo-web-crm | desarrollo | soporte | informacional | integrar odoo web crm |
| automatizar-procesos-pyme | automatizaciones | pilar | informacional | automatizar procesos pyme |
| rpa-vs-automatizacion-apis | automatizaciones | soporte | informacional | rpa vs automatizacion apis |
| procesos-automatizar-empresa | automatizaciones | soporte | informacional | procesos automatizar empresa |

## Posts de vídeo (noticia)

| Slug | Cluster | Keyword principal | Enlazar a pilar |
|------|---------|-------------------|-----------------|
| acceso-a-mitos-oportunidad-tardia-para-europa | ia | acceso modelos ia europa | seo-geo-inteligencia-artificial-2026 |
| el-impacto-de-la-ia-en-el-nhs-ahorro-de-tiempo-y-productividad | ia | ia sanidad publica productividad | seo-geo-inteligencia-artificial-2026 |
| la-ia-que-transformara-nuestra-comprension-del-conocimiento | ia | ia transformacion conocimiento | seo-geo-inteligencia-artificial-2026 |

## Reglas editoriales

1. **Una keyword principal por URL.** Si ya existe en la matriz, actualizar el artículo existente (y `fecha_modificacion`), no crear URL nueva.
2. **Tipo `noticia` para vídeos diarios.** No optimizar como pilar; enlazar siempre al pilar del cluster.
3. **Enlaces mínimos por artículo:** hub `/recursos` + pilar del cluster + 2 relacionados del mismo cluster.
4. **Canibalización:** misma keyword o título >80% similar → warning en admin; revisar título/H1 o fusionar con 301.
5. **Slug inmutable** tras indexación; si cambia, registrar redirect en `recursos_redirects`.
6. **Meta description ≤160 caracteres** (aviso si supera).
7. **Cluster obligatorio** al publicar vídeos: `ia`, `desarrollo` o `automatizaciones` (nunca `video`).

## Árbol de decisión ante conflicto

1. ¿Un artículo gana claramente en tráfico/conversión? → Fusionar en ganador + 301 del perdedor.
2. ¿Intenciones distintas mal diferenciadas? → Reescribir título/H1/meta sin cambiar slug.
3. ¿Noticia vs guía? → Mantener ambos; la noticia enlaza al pilar.
4. ¿Vídeos muy similares? → Menos URLs indexables o roundup semanal.

## Checklist pre-publicación

- [ ] Keyword principal única en esta matriz
- [ ] Tipo: pilar / soporte / noticia
- [ ] Cluster asignado
- [ ] Enlace a `/recursos`
- [ ] Enlace al pilar del cluster
- [ ] 2+ slugs en `relacionados`
- [ ] Meta description ≤160 caracteres
- [ ] Imagen OG (estáticos) o miniatura YouTube (vídeos)
- [ ] Slug validado (sin colisión RECURSOS + BD)
- [ ] `fecha_modificacion` solo en updates reales

## Hub /recursos

- Bloques fijos por cluster con enlace al pilar
- **Guías pilar:** solo los 3 pilares (SEO/GEO, elegir empresa, automatizar pyme)
- **Actualidad IA:** máximo 6 entradas en hub + `/recursos/actualidad` para el listado completo
- **Todas las guías:** evergreen sin repetir pilares ya mostrados arriba
- Schema `ItemList` solo con guías evergreen

## Grupo Mythos/Fable (consolidación)

URL canónica: `acceso-a-mitos-oportunidad-tardia-para-europa`

Redirects 301 activos hacia la canónica:
- `el-drama-de-mythos-la-regulacion-de-ia-en-ee-uu`
- `prohibicion-de-fable-y-mythos-un-precedente-en-ia`
- `mythos-fable-5-un-avance-revolucionario-en-ia`

**Regla admin:** no publicar nueva noticia si título/slug/keyword contiene mythos, mitos o fable y ya existe otra pieza del grupo (error bloqueante).

## Implementación técnica

- Validaciones: `recursos_seo.py` → `seo_check_recurso()`
- Redirects: tabla `recursos_redirects` + `RECURSOS_SLUG_REDIRECTS` en código
- Admin: campos SEO en `/admin/video/<id>` antes de publicar
- Sitemap: pilares priority 0.8, noticias 0.6, soporte 0.75; `lastmod` = `fecha_modificacion`

"""Utilidades SEO para la sección /recursos."""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher

CLUSTERS = ('ia', 'desarrollo', 'automatizaciones')

CLUSTER_PILARES: dict[str, str] = {
    'ia': 'seo-geo-inteligencia-artificial-2026',
    'desarrollo': 'elegir-empresa-desarrollo-software',
    'automatizaciones': 'automatizar-procesos-pyme',
}

RECURSOS_DESTACADOS = [
    'seo-geo-inteligencia-artificial-2026',
    'elegir-empresa-desarrollo-software',
    'automatizar-procesos-pyme',
]

FEED_ACTUALIDAD_LIMIT = 6
THIN_CONTENT_MIN_CHARS = 600

SUBTEMAS = (
    'regulacion-modelos',
    'producto-empresa',
    'sector-vertical',
    'conceptual',
    'estrategia-geo',
    'desarrollo-general',
    'automatizacion-general',
)

# Slug canónico del grupo Mythos/Fable (consolidación editorial)
MYTHOS_CANONICAL_SLUG = 'acceso-a-mitos-oportunidad-tardia-para-europa'
MYTHOS_TOPIC_RE = re.compile(r'\b(mythos|mitos|fable)\b', re.I)

META_CANONICAL_SLUG = 'meta-y-el-fiasco-de-su-chatbot-en-instagram'
META_TOPIC_RE = re.compile(r'\bmeta\b.*\b(chatbot|instagram|bot)\b|\b(chatbot|instagram)\b.*\bmeta\b', re.I)

# 301 de piezas Mythos/Fable redundantes hacia la URL canónica del grupo
RECURSOS_SLUG_REDIRECTS: dict[str, str] = {
    '/recursos/el-drama-de-mythos-la-regulacion-de-ia-en-ee-uu': f'/recursos/{MYTHOS_CANONICAL_SLUG}',
    '/recursos/prohibicion-de-fable-y-mythos-un-precedente-en-ia': f'/recursos/{MYTHOS_CANONICAL_SLUG}',
    '/recursos/mythos-fable-5-un-avance-revolucionario-en-ia': f'/recursos/{MYTHOS_CANONICAL_SLUG}',
}

CLUSTER_META: dict[str, dict] = {
    'ia': {
        'nombre': 'IA aplicada a empresas',
        'descripcion': 'Guías sobre inteligencia artificial, GEO y consultoría IA para pymes en España.',
        'ancla': 'cluster-ia',
    },
    'desarrollo': {
        'nombre': 'Desarrollo a medida',
        'descripcion': 'Cómo elegir proveedor, costes e integraciones de software a medida.',
        'ancla': 'cluster-desarrollo',
    },
    'automatizaciones': {
        'nombre': 'Automatización y RPA',
        'descripcion': 'Procesos, ROI y comparativas RPA vs APIs para empresas.',
        'ancla': 'cluster-automatizaciones',
    },
}

# Metadatos por defecto para posts de vídeo conocidos (migración / fallback)
VIDEO_POST_DEFAULTS: dict[str, dict] = {
    'acceso-a-mitos-oportunidad-tardia-para-europa': {
        'cluster': 'ia',
        'tipo': 'noticia',
        'intencion': 'noticia',
        'subtema': 'regulacion-modelos',
        'keyword_principal': 'acceso modelos ia europa',
        'indexable': True,
        'relacionados': [
            'seo-geo-inteligencia-artificial-2026',
            'agencia-ia-madrid-apuesta-comunidad-pymes',
            'desarrolladores-ia-gestion-automatizacion-empresas',
        ],
    },
    'el-impacto-de-la-ia-en-el-nhs-ahorro-de-tiempo-y-productividad': {
        'cluster': 'ia',
        'tipo': 'noticia',
        'intencion': 'noticia',
        'subtema': 'sector-vertical',
        'keyword_principal': 'ia sanidad publica productividad',
        'indexable': True,
        'relacionados': [
            'seo-geo-inteligencia-artificial-2026',
            'desarrolladores-ia-gestion-automatizacion-empresas',
        ],
    },
    'la-ia-que-transformara-nuestra-comprension-del-conocimiento': {
        'cluster': 'ia',
        'tipo': 'noticia',
        'intencion': 'noticia',
        'subtema': 'conceptual',
        'keyword_principal': 'ia transformacion conocimiento',
        'indexable': True,
        'relacionados': [
            'seo-geo-inteligencia-artificial-2026',
            'desarrolladores-ia-gestion-automatizacion-empresas',
        ],
    },
    'meta-y-el-fiasco-de-su-chatbot-en-instagram': {
        'cluster': 'ia',
        'tipo': 'noticia',
        'intencion': 'noticia',
        'subtema': 'producto-empresa',
        'keyword_principal': 'meta chatbot instagram empresas',
        'indexable': True,
        'relacionados': [
            'seo-geo-inteligencia-artificial-2026',
            'desarrolladores-ia-gestion-automatizacion-empresas',
        ],
    },
}

STATIC_SEO_DEFAULTS: dict[str, dict] = {
    'seo-geo-inteligencia-artificial-2026': {'subtema': 'estrategia-geo', 'indexable': True},
    'agencia-ia-madrid-apuesta-comunidad-pymes': {'subtema': 'estrategia-geo', 'indexable': True},
    'desarrolladores-ia-gestion-automatizacion-empresas': {'subtema': 'estrategia-geo', 'indexable': True},
    'elegir-empresa-desarrollo-software': {'subtema': 'desarrollo-general', 'indexable': True},
    'coste-desarrollo-software-2026': {'subtema': 'desarrollo-general', 'indexable': True},
    'integrar-odoo-web-crm': {'subtema': 'desarrollo-general', 'indexable': True},
    'automatizar-procesos-pyme': {'subtema': 'automatizacion-general', 'indexable': True},
    'rpa-vs-automatizacion-apis': {'subtema': 'automatizacion-general', 'indexable': True},
    'procesos-automatizar-empresa': {'subtema': 'automatizacion-general', 'indexable': True},
}

TIPOS_VALIDOS = ('pilar', 'soporte', 'noticia')
INTENCIONES_VALIDAS = ('informacional', 'comercial', 'noticia')


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _es_noticia(recurso: dict) -> bool:
    r = normalize_recurso(recurso)
    if r.get('video_id') and r.get('tipo') not in ('pilar', 'soporte'):
        return True
    return r.get('tipo') == 'noticia'


def _es_guia(recurso: dict) -> bool:
    return not _es_noticia(recurso) and normalize_recurso(recurso).get('tipo') in ('pilar', 'soporte')


def _texto_busqueda(articulo: dict) -> str:
    parts = [
        articulo.get('slug', ''),
        articulo.get('titulo', ''),
        articulo.get('keyword_principal', ''),
        articulo.get('resumen', ''),
    ]
    return ' '.join(parts)


def _es_tema_mythos(articulo: dict) -> bool:
    return bool(MYTHOS_TOPIC_RE.search(_texto_busqueda(articulo)))


def _es_tema_meta(articulo: dict) -> bool:
    return bool(META_TOPIC_RE.search(_texto_busqueda(articulo)))


def find_mythos_conflict(articulo: dict, todos: list[dict]) -> dict | None:
    slug = articulo.get('slug', '')
    if slug == MYTHOS_CANONICAL_SLUG or not _es_tema_mythos(articulo):
        return None
    for otro in todos:
        if otro.get('slug') != slug and _es_tema_mythos(otro):
            return normalize_recurso(otro)
    return None


def find_meta_conflict(articulo: dict, todos: list[dict]) -> dict | None:
    slug = articulo.get('slug', '')
    if slug == META_CANONICAL_SLUG or not _es_tema_meta(articulo):
        return None
    for otro in todos:
        if otro.get('slug') != slug and _es_tema_meta(otro):
            return normalize_recurso(otro)
    return None


def es_indexable(recurso: dict) -> bool:
    r = normalize_recurso(recurso)
    val = r.get('indexable')
    if val is None:
        return True
    if isinstance(val, str):
        return val.lower() not in ('0', 'false', 'no')
    return bool(val)


def find_subtema_conflict(articulo: dict, todos: list[dict]) -> dict | None:
    a = normalize_recurso(articulo)
    if a.get('tipo') != 'noticia' or not es_indexable(a) or not a.get('subtema'):
        return None
    for otro in todos:
        o = normalize_recurso(otro)
        if (
            o.get('slug') != a.get('slug')
            and o.get('tipo') == 'noticia'
            and es_indexable(o)
            and o.get('cluster') == a.get('cluster')
            and o.get('subtema') == a.get('subtema')
        ):
            return o
    return None


def normalize_recurso(recurso: dict) -> dict:
    """Completa campos SEO con valores por defecto razonables."""
    out = dict(recurso)
    slug = out.get('slug', '')
    defaults = {**STATIC_SEO_DEFAULTS.get(slug, {}), **VIDEO_POST_DEFAULTS.get(slug, {})}

    cluster = out.get('cluster') or defaults.get('cluster') or 'ia'
    if cluster == 'video':
        cluster = defaults.get('cluster', 'ia')
    out['cluster'] = cluster if cluster in CLUSTERS else 'ia'

    out.setdefault('tipo', defaults.get('tipo', 'noticia' if out.get('video_id') else 'soporte'))
    out.setdefault('intencion', defaults.get('intencion', 'informacional'))
    out.setdefault('keyword_principal', defaults.get('keyword_principal', ''))
    out.setdefault('fecha_modificacion', out.get('fecha_modificacion') or out.get('fecha', ''))

    relacionados = out.get('relacionados')
    if relacionados is None:
        relacionados = defaults.get('relacionados', [])
    if isinstance(relacionados, str):
        try:
            relacionados = json.loads(relacionados) if relacionados.startswith('[') else [
                s.strip() for s in relacionados.split(',') if s.strip()
            ]
        except json.JSONDecodeError:
            relacionados = [s.strip() for s in relacionados.split(',') if s.strip()]
    out['relacionados'] = [s for s in relacionados if s and s != slug]

    return out


def all_slugs(recursos_estaticos: list[dict], extra_slugs: list[str] | None = None) -> set[str]:
    slugs = {r['slug'] for r in recursos_estaticos}
    if extra_slugs:
        slugs.update(extra_slugs)
    return slugs


def slug_disponible(
    slug: str,
    recursos_estaticos: list[dict],
    db_slugs: list[str] | None = None,
    exclude_slug: str | None = None,
) -> bool:
    if not slug or not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        return False
    ocupados = all_slugs(recursos_estaticos, db_slugs)
    if exclude_slug:
        ocupados.discard(exclude_slug)
    return slug not in ocupados


def seo_check_recurso(articulo: dict, todos: list[dict]) -> list[dict]:
    """Devuelve avisos/errores {level: 'error'|'warning', message: str}."""
    issues: list[dict] = []
    a = normalize_recurso(articulo)
    slug = a.get('slug', '')

    if not a.get('keyword_principal'):
        issues.append({'level': 'error', 'message': 'Falta keyword_principal (obligatoria).'})

    if not a.get('titulo'):
        issues.append({'level': 'error', 'message': 'Falta título.'})

    if not a.get('resumen'):
        issues.append({'level': 'warning', 'message': 'Falta resumen (meta description).'})
    elif len(a['resumen']) > 160:
        issues.append({
            'level': 'warning',
            'message': f"Resumen de {len(a['resumen'])} caracteres (recomendado ≤160).",
        })

    if a.get('cluster') not in CLUSTERS:
        issues.append({'level': 'error', 'message': f"Cluster inválido: {a.get('cluster')}."})

    if a.get('tipo') not in TIPOS_VALIDOS:
        issues.append({'level': 'warning', 'message': f"Tipo no estándar: {a.get('tipo')}."})

    titulo = a.get('titulo', '')
    for otro in todos:
        if otro.get('slug') == slug:
            continue
        otro_t = otro.get('titulo', '')
        if otro_t and _similarity(titulo, otro_t) >= 0.8:
            issues.append({
                'level': 'warning',
                'message': f"Posible canibalización: título muy similar a «{otro_t[:60]}…».",
            })

    kw = (a.get('keyword_principal') or '').lower()
    cluster = a.get('cluster')
    intencion = a.get('intencion')
    for otro in todos:
        if otro.get('slug') == slug:
            continue
        okw = (otro.get('keyword_principal') or '').lower()
        if kw and okw and kw == okw:
            issues.append({
                'level': 'warning',
                'message': f"Misma keyword_principal que «{otro.get('titulo', otro.get('slug'))}».",
            })
        if (
            cluster
            and otro.get('cluster') == cluster
            and intencion
            and otro.get('intencion') == intencion
            and otro.get('tipo') == 'pilar'
            and a.get('tipo') != 'noticia'
            and slug != CLUSTER_PILARES.get(cluster, '')
        ):
            pilar_slug = CLUSTER_PILARES.get(cluster, '')
            if otro.get('slug') == pilar_slug or otro.get('tipo') == 'pilar':
                issues.append({
                    'level': 'warning',
                    'message': f"Considera actualizar el pilar del cluster ({pilar_slug}) en lugar de competir.",
                })
                break

    if not a.get('imagen') and not a.get('video_id'):
        issues.append({'level': 'warning', 'message': 'Sin imagen OG dedicada.'})

    for rel in a.get('relacionados', []):
        if rel == slug:
            issues.append({'level': 'warning', 'message': 'relacionados incluye el propio slug.'})
        elif not any(r.get('slug') == rel for r in todos):
            issues.append({'level': 'warning', 'message': f"relacionados referencia slug inexistente: {rel}."})

    mythos_conf = find_mythos_conflict(a, todos)
    if mythos_conf and a.get('tipo') == 'noticia':
        titulo_existente = mythos_conf.get('titulo', mythos_conf.get('slug', ''))
        if slug == MYTHOS_CANONICAL_SLUG:
            pass
        elif mythos_conf.get('slug') == MYTHOS_CANONICAL_SLUG:
            issues.append({
                'level': 'error',
                'message': (
                    f"Ya existe contenido Mythos/Fable indexado («{titulo_existente[:50]}…»). "
                    f"Actualiza /recursos/{MYTHOS_CANONICAL_SLUG} o usa otra keyword."
                ),
            })
        else:
            issues.append({
                'level': 'error',
                'message': (
                    f"Posible duplicado Mythos/Fable con «{titulo_existente[:50]}…». "
                    f"Consolida en /recursos/{MYTHOS_CANONICAL_SLUG}."
                ),
            })

    return issues


def get_articulos_relacionados(articulo: dict, todos: list[dict], limit: int = 4) -> list[dict]:
    """Resuelve slugs en relacionados + mismo cluster si faltan entradas."""
    a = normalize_recurso(articulo)
    by_slug = {normalize_recurso(r)['slug']: normalize_recurso(r) for r in todos}
    seen: set[str] = {a['slug']}
    result: list[dict] = []

    for slug in a.get('relacionados', []):
        if slug in by_slug and slug not in seen:
            result.append(by_slug[slug])
            seen.add(slug)
        if len(result) >= limit:
            return result

    pilar = CLUSTER_PILARES.get(a.get('cluster', ''))
    if pilar and pilar not in seen and pilar in by_slug and len(result) < limit:
        result.append(by_slug[pilar])
        seen.add(pilar)

    for r in sorted(todos, key=lambda x: x.get('fecha', ''), reverse=True):
        rs = normalize_recurso(r)
        if rs['slug'] in seen:
            continue
        if rs.get('cluster') == a.get('cluster') and rs.get('tipo') != 'noticia':
            result.append(rs)
            seen.add(rs['slug'])
        if len(result) >= limit:
            break

    return result[:limit]


def build_hub_context(todos: list[dict]) -> dict:
    """Contexto para recursos.html: clusters, destacados, guías evergreen, feed actualidad."""
    normalizados = [normalize_recurso(r) for r in todos]
    by_slug = {r['slug']: r for r in normalizados}

    clusters = []
    for key in CLUSTERS:
        meta = CLUSTER_META[key]
        pilar_slug = CLUSTER_PILARES[key]
        pilar = by_slug.get(pilar_slug)
        soporte = [
            r for r in normalizados
            if r.get('cluster') == key
            and r.get('slug') != pilar_slug
            and r.get('tipo') in ('pilar', 'soporte')
        ][:3]
        clusters.append({**meta, 'key': key, 'pilar': pilar, 'soporte': soporte})

    destacados = [by_slug[s] for s in RECURSOS_DESTACADOS if s in by_slug]
    destacados_slugs = {d['slug'] for d in destacados}

    guias = sorted(
        [r for r in normalizados if _es_guia(r)],
        key=lambda x: x.get('fecha', ''),
        reverse=True,
    )
    guias_sin_destacados = [g for g in guias if g['slug'] not in destacados_slugs]

    actualidad = sorted(
        [r for r in normalizados if _es_noticia(r)],
        key=lambda x: x.get('fecha', ''),
        reverse=True,
    )

    return {
        'clusters_hub': clusters,
        'destacados': destacados,
        'guias_evergreen': guias,
        'guias_todas': guias_sin_destacados,
        'feed_actualidad': actualidad[:FEED_ACTUALIDAD_LIMIT],
        'feed_actualidad_total': len(actualidad),
        'articulos': normalizados,
    }


def build_actualidad_context(todos: list[dict]) -> dict:
    normalizados = [normalize_recurso(r) for r in todos]
    actualidad = sorted(
        [r for r in normalizados if _es_noticia(r)],
        key=lambda x: x.get('fecha', ''),
        reverse=True,
    )
    return {'articulos': actualidad, 'total': len(actualidad)}


def sitemap_priority(recurso: dict) -> str:
    tipo = normalize_recurso(recurso).get('tipo', 'soporte')
    if tipo == 'pilar':
        return '0.8'
    if tipo == 'noticia' or recurso.get('video_id'):
        return '0.6'
    return '0.75'


def redirect_path_for_slug(slug: str, db_redirects: dict[str, str] | None = None) -> str | None:
    """Devuelve path destino /recursos/nuevo-slug si hay redirect."""
    path = f'/recursos/{slug}'
    if path in RECURSOS_SLUG_REDIRECTS:
        return RECURSOS_SLUG_REDIRECTS[path]
    if db_redirects and slug in db_redirects:
        return f"/recursos/{db_redirects[slug]}"
    legacy = f'/blog/{slug}'
    if legacy in RECURSOS_SLUG_REDIRECTS:
        return RECURSOS_SLUG_REDIRECTS[legacy]
    return None

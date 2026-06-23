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

META_CANONICAL_SLUG = 'meta-y-el-fiasco-de-su-chatbot-en-instagram'
META_TOPIC_RE = re.compile(r'\bmeta\b.*\b(chatbot|instagram|bot)\b|\b(chatbot|instagram)\b.*\bmeta\b', re.I)

# Redirects editoriales explícitos (slug inmutable tras indexación, etc.)
RECURSOS_SLUG_REDIRECTS: dict[str, str] = {}

_GENERIC_IA_TERMS = frozenset({
    'inteligencia', 'artificial', 'empresas', 'desarrollo', 'software',
    'automatizacion', 'procesos', 'modelos', 'tecnologia', 'digital',
    'consultoria', 'negocio', 'negocios', 'estrategia', 'soluciones',
    'regulacion', 'seguridad', 'nacional', 'oportunidad', 'productividad',
})

_SEARCH_STOPWORDS = frozenset({
    'para', 'con', 'los', 'las', 'del', 'de', 'una', 'uno', 'que', 'por',
    'sobre', 'como', 'más', 'mas', 'sus', 'este', 'esta', 'entre', 'desde',
    'hacia', 'todo', 'toda', 'todos', 'todas', 'son', 'ser', 'han', 'has',
    'the', 'and', 'for', 'with', 'from', 'noticia', 'recursos',
})


def _termino_distintivo(token: str) -> bool:
    return len(token) >= 4 and token not in _GENERIC_IA_TERMS and token not in _SEARCH_STOPWORDS

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
    'memoria-persistente-agentes-ia-desarrollo': {'subtema': 'automatizacion-general', 'indexable': True},
    'integrar-datos-ia-metodos-estrategias': {'subtema': 'desarrollo-general', 'indexable': True},
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
        articulo.get('slug') or '',
        articulo.get('titulo') or '',
        articulo.get('keyword_principal') or '',
        articulo.get('resumen') or '',
    ]
    return ' '.join(parts)


def _search_tokens(articulo: dict) -> set[str]:
    """Términos de búsqueda derivados de keyword, título y slug."""
    a = normalize_recurso(articulo)
    slug_text = (a.get('slug') or '').replace('-', ' ')
    text = ' '.join([
        a.get('keyword_principal') or '',
        a.get('titulo') or '',
        slug_text,
    ]).lower()
    return {
        w for w in re.findall(r'[a-záéíóúñ0-9]+', text)
        if len(w) >= 4 and w not in _SEARCH_STOPWORDS
    }


def _tokens_busqueda_solapados(ta: set[str], tb: set[str]) -> set[str]:
    overlap = set(ta & tb)
    for a in ta:
        for b in tb:
            if a != b and _similarity(a, b) >= 0.85:
                overlap.add(a)
    return overlap


def _tokens_extra_contenido(articulo: dict) -> set[str]:
    """Términos distintivos del resumen/cuerpo para proponer keywords."""
    a = normalize_recurso(articulo)
    cuerpo = (a.get('cuerpo') or '')[:800]
    text = ' '.join([a.get('resumen') or '', cuerpo])
    return {
        w for w in re.findall(r'[a-záéíóúñ0-9]+', text.lower())
        if _termino_distintivo(w)
    }


_SUBTEMA_ANGULOS: dict[str, str] = {
    'regulacion-modelos': 'regulación o restricción de modelos',
    'producto-empresa': 'producto o empresa concreta',
    'sector-vertical': 'sector vertical (sanidad, finanzas, sector público…)',
    'conceptual': 'tendencia o concepto de fondo',
    'estrategia-geo': 'estrategia GEO y visibilidad en buscadores IA',
    'desarrollo-general': 'desarrollo de software a medida',
    'automatizacion-general': 'automatización de procesos',
}


def sugerir_alternativas_canibalizacion(
    articulo: dict,
    otro: dict,
    terminos_solapados: set[str] | None = None,
    motivo: str = '',
) -> list[str]:
    """Acciones concretas para evitar competir por las mismas búsquedas."""
    a = normalize_recurso(articulo)
    o = normalize_recurso(otro)
    slug_otro = o.get('slug', '')
    titulo_otro = o.get('titulo', slug_otro)
    kw_otro = (o.get('keyword_principal') or '').strip()

    ta = _search_tokens(a) | _tokens_extra_contenido(a)
    tb = _search_tokens(o)
    overlap = terminos_solapados or _tokens_busqueda_solapados(ta, tb)
    unicos = sorted(t for t in (ta - tb) if _termino_distintivo(t))

    alternativas: list[str] = [
        f'Añade «{slug_otro}» en relacionados y enlázalo en el primer párrafo.',
    ]

    if a.get('tipo') == 'noticia':
        alternativas.append(
            f'Actualiza «{titulo_otro[:48]}…» con este contenido en vez de crear otra URL.'
        )

    if unicos:
        kw_alt = ' '.join(unicos[:3])
        conflictivos = ', '.join(sorted(overlap)[:3]) if overlap else 'términos repetidos'
        alternativas.append(f'Keyword alternativa: «{kw_alt}» (evita {conflictivos}).')

    if a.get('subtema') in _SUBTEMA_ANGULOS:
        angulo = _SUBTEMA_ANGULOS[a['subtema']]
        ref = f' (el existente usa «{kw_otro}»)' if kw_otro else ''
        alternativas.append(f'Diferencia el ángulo: {angulo}{ref}.')

    if motivo == 'misma keyword_principal' and unicos:
        alternativas.append(f'Sustituye la keyword actual por «{" ".join(unicos[:3])}».')

    if motivo == 'titulo_similar':
        alternativas.append(
            'Reformula el título con fecha, entidad o consecuencia concreta que no repita el existente.'
        )

    if motivo == 'mismo_subtema' and unicos:
        alternativas.append(
            f'Mismo subtema: prueba keyword «{" ".join(unicos[:2])} {a.get("cluster", "")}» '
            f'u otro subtema si el enfoque es distinto.'
        )

    return alternativas[:5]


def _issue_canibalizacion(message: str, alternativas: list[str]) -> dict:
    return {'level': 'warning', 'message': message, 'alternativas': alternativas}


def find_cannibalizacion_busqueda(
    articulo: dict, todos: list[dict],
) -> list[tuple[dict, str, set[str], str]]:
    """Artículos que podrían competir por las mismas búsquedas."""
    a = normalize_recurso(articulo)
    if not es_indexable(a):
        return []
    ta = _search_tokens(a)
    if not ta:
        return []
    conflictos: list[tuple[dict, str, set[str], str]] = []
    for otro in todos:
        o = normalize_recurso(otro)
        if o.get('slug') == a.get('slug') or not es_indexable(o):
            continue
        tb = _search_tokens(o)
        overlap = _tokens_busqueda_solapados(ta, tb)
        if not overlap:
            continue
        kw_a = (a.get('keyword_principal') or '').lower().strip()
        kw_b = (o.get('keyword_principal') or '').lower().strip()
        if kw_a and kw_b and kw_a == kw_b:
            motivo = 'misma keyword_principal'
            motivo_txt = f'misma keyword_principal («{kw_b}»)'
        elif len(overlap) >= 2:
            terminos = ', '.join(sorted(overlap)[:4])
            motivo = f'términos de búsqueda compartidos ({terminos})'
            motivo_txt = motivo
        elif any(_termino_distintivo(t) for t in overlap):
            terminos = ', '.join(sorted(t for t in overlap if _termino_distintivo(t))[:4])
            motivo = f'término de búsqueda distintivo compartido ({terminos})'
            motivo_txt = motivo
        else:
            continue
        conflictos.append((o, motivo_txt, overlap, motivo))
    return conflictos


def _es_tema_meta(articulo: dict) -> bool:
    return bool(META_TOPIC_RE.search(_texto_busqueda(articulo)))


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
            o = normalize_recurso(otro)
            issues.append(_issue_canibalizacion(
                f"Posible canibalización: título muy similar a «{otro_t[:60]}…».",
                sugerir_alternativas_canibalizacion(a, o, motivo='titulo_similar'),
            ))

    kw = (a.get('keyword_principal') or '').lower()
    cluster = a.get('cluster')
    intencion = a.get('intencion')
    for otro in todos:
        if otro.get('slug') == slug:
            continue
        okw = (otro.get('keyword_principal') or '').lower()
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

    subtema_conf = find_subtema_conflict(a, todos)
    if subtema_conf:
        titulo_existente = subtema_conf.get('titulo', subtema_conf.get('slug', ''))
        issues.append(_issue_canibalizacion(
            (
                f"Posible canibalización: mismo subtema «{a.get('subtema')}» que "
                f"«{titulo_existente[:50]}…»."
            ),
            sugerir_alternativas_canibalizacion(
                a, subtema_conf, motivo='mismo_subtema',
            ),
        ))

    for otro, motivo_txt, overlap, motivo_key in find_cannibalizacion_busqueda(a, todos):
        titulo_existente = otro.get('titulo', otro.get('slug', ''))
        slug_otro = otro.get('slug', '')
        issues.append(_issue_canibalizacion(
            (
                f"Posible canibalización por búsquedas ({motivo_txt}) con "
                f"«{titulo_existente[:50]}…» (/recursos/{slug_otro})."
            ),
            sugerir_alternativas_canibalizacion(
                a, otro, terminos_solapados=overlap, motivo=motivo_key,
            ),
        ))

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


def articulo_canonical_href(articulo: dict, base_url: str = 'https://megasolucion.es') -> str | None:
    """Canónica explícita solo si se define manualmente (sin reglas automáticas por tema)."""
    return None


def include_recurso_in_sitemap(recurso: dict, db_redirects: dict[str, str] | None = None) -> bool:
    """Excluye URLs que redirigen o declaran canónica a otra pieza."""
    slug = normalize_recurso(recurso).get('slug', '')
    if not slug:
        return False
    if redirect_path_for_slug(slug, db_redirects):
        return False
    if articulo_canonical_href(recurso):
        return False
    return True


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

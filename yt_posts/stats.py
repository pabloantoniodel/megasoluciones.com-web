"""Registro de visitas tipo WP Statistics: parseo de user-agent y tracking."""
import hashlib
import re
from urllib.parse import parse_qs, unquote_plus, urlparse

from . import db

BOT_PATTERN = re.compile(
    r'bot|crawl|spider|slurp|bingpreview|facebookexternalhit|whatsapp|telegram|'
    r'curl|wget|python-requests|httpx|go-http-client|java/|libwww|headless|'
    r'lighthouse|pingdom|uptimerobot|monitor|scrapy|semrush|ahrefs|mj12|dotbot|petalbot',
    re.IGNORECASE,
)

EXCLUDED_PATHS = ('/sitemap.xml', '/robots.txt', '/favicon.ico')

CLOUD_SCRAPER_IP_PREFIXES = ('34.', '35.', '104.197.', '104.155.')


def is_bot(user_agent: str) -> bool:
    return not user_agent or bool(BOT_PATTERN.search(user_agent))


def is_likely_cloud_scraper(ip: str, referrer: str, user_agent: str) -> bool:
    """Scrapers en Google Cloud: IP datacenter + Chrome/Edge sin referrer."""
    if not ip or not any(ip.startswith(p) for p in CLOUD_SCRAPER_IP_PREFIXES):
        return False
    if referrer and referrer.strip():
        return False
    ua_l = (user_agent or '').lower()
    return 'chrome' in ua_l or 'edge' in ua_l


def should_track(
    path: str,
    method: str,
    status_code: int,
    content_type: str,
    user_agent: str,
    ip: str = '',
    referrer: str = '',
) -> bool:
    if method != 'GET' or status_code != 200:
        return False
    if not content_type.startswith('text/html'):
        return False
    if path.startswith('/static/') or path.startswith('/admin') or path == '/health' or path in EXCLUDED_PATHS:
        return False
    if is_bot(user_agent):
        return False
    if is_likely_cloud_scraper(ip, referrer, user_agent):
        return False
    return True


def parse_user_agent(ua: str) -> tuple[str, str, str]:
    """Devuelve (navegador, so, dispositivo)."""
    ua_l = ua.lower()

    if 'edg/' in ua_l or 'edge/' in ua_l:
        navegador = 'Edge'
    elif 'opr/' in ua_l or 'opera' in ua_l:
        navegador = 'Opera'
    elif 'samsungbrowser' in ua_l:
        navegador = 'Samsung Internet'
    elif 'firefox/' in ua_l:
        navegador = 'Firefox'
    elif 'chrome/' in ua_l or 'crios/' in ua_l:
        navegador = 'Chrome'
    elif 'safari/' in ua_l:
        navegador = 'Safari'
    else:
        navegador = 'Otro'

    if 'android' in ua_l:
        so = 'Android'
    elif 'iphone' in ua_l or 'ipad' in ua_l or 'ios' in ua_l:
        so = 'iOS'
    elif 'windows' in ua_l:
        so = 'Windows'
    elif 'mac os' in ua_l or 'macintosh' in ua_l:
        so = 'macOS'
    elif 'linux' in ua_l:
        so = 'Linux'
    else:
        so = 'Otro'

    if 'ipad' in ua_l or 'tablet' in ua_l:
        dispositivo = 'tablet'
    elif 'mobile' in ua_l or 'android' in ua_l or 'iphone' in ua_l:
        dispositivo = 'móvil'
    else:
        dispositivo = 'escritorio'

    return navegador, so, dispositivo


# (hostname, parámetros de búsqueda en ese motor — probados en orden)
_SEARCH_ENGINE_PARAMS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r'google\.', re.I), ('q',)),
    (re.compile(r'bing\.', re.I), ('q',)),
    (re.compile(r'duckduckgo\.', re.I), ('q',)),
    (re.compile(r'ecosia\.', re.I), ('q',)),
    (re.compile(r'search\.yahoo\.', re.I), ('p', 'q')),
    (re.compile(r'yahoo\.', re.I), ('p', 'q')),
    (re.compile(r'yandex\.', re.I), ('text', 'q')),
    (re.compile(r'baidu\.', re.I), ('wd', 'word', 'q')),
    (re.compile(r'ask\.', re.I), ('q',)),
    (re.compile(r'qwant\.', re.I), ('q',)),
    (re.compile(r'startpage\.', re.I), ('query', 'q')),
    (re.compile(r'search\.brave\.', re.I), ('q',)),
    (re.compile(r'youtube\.|youtu\.be', re.I), ('search_query', 'q')),
    (re.compile(r'chatgpt\.|chat\.openai\.', re.I), ('q', 'query')),
    (re.compile(r'perplexity\.', re.I), ('q', 'query')),
)

# Parámetros genéricos en la URL de llegada (?q=, ?search_query=, etc.)
_LANDING_QUERY_PARAMS: tuple[str, ...] = (
    'q',
    'search_query',
    'query',
    'search',
    'keyword',
    'keywords',
    'p',
    'text',
    'wd',
    's',
    'k',
    'terms',
)


def _normalize_search_term(raw: str) -> str:
    text = unquote_plus((raw or '').strip())
    if len(text) < 2 or len(text) > 500:
        return ''
    if text.startswith(('http://', 'https://', '//')):
        return ''
    return text


def _query_dict_from_string(query_string: str) -> dict[str, list[str]]:
    if not query_string:
        return {}
    qs = query_string.lstrip('?')
    if not qs:
        return {}
    return parse_qs(qs, keep_blank_values=False)


def _extract_from_params(query_params: dict[str, list[str]], param_names: tuple[str, ...]) -> str:
    for param in param_names:
        for value in query_params.get(param, []):
            text = _normalize_search_term(value)
            if text:
                return text
    return ''


def extract_search_query_from_referrer(referrer: str) -> str:
    """Consulta de búsqueda embebida en la URL del header Referer."""
    if not referrer:
        return ''
    host = _referrer_host(referrer)
    if not host:
        return ''
    query_params = _query_dict_from_string(urlparse(referrer).query)
    for pattern, param_names in _SEARCH_ENGINE_PARAMS:
        if pattern.search(host):
            found = _extract_from_params(query_params, param_names)
            if found:
                return found
    return _extract_from_params(query_params, _LANDING_QUERY_PARAMS)


def extract_search_query_from_landing(query_string: str) -> str:
    """Consulta en la URL de entrada (?q=, ?search_query=, etc.)."""
    return _extract_from_params(_query_dict_from_string(query_string), _LANDING_QUERY_PARAMS)


def resolve_search_query(referrer: str, landing_query_string: str = '') -> str:
    """Prioridad: Referer del buscador, luego parámetros de la URL de llegada."""
    query, _source = resolve_search_query_with_source(referrer, landing_query_string)
    return query


def resolve_search_query_with_source(
    referrer: str, landing_query_string: str = '',
) -> tuple[str, str]:
    """Devuelve (consulta, origen) con origen «referer», «landing» o vacío."""
    from_referrer = extract_search_query_from_referrer(referrer)
    if from_referrer:
        return from_referrer, 'referer'
    from_landing = extract_search_query_from_landing(landing_query_string)
    if from_landing:
        return from_landing, 'landing'
    return '', ''


def extract_utm_source(landing_query_string: str) -> str:
    """utm_source de la URL de entrada (?utm_source=linkedin…)."""
    for value in _query_dict_from_string(landing_query_string).get('utm_source', []):
        text = unquote_plus((value or '').strip())
        if text:
            return text[:120]
    return ''


_UTM_SOURCE_CHANNELS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r'linkedin|lnkd', re.I), 'LinkedIn'),
    (re.compile(r'facebook|fb|meta', re.I), 'Facebook'),
    (re.compile(r'instagram', re.I), 'Instagram'),
    (re.compile(r'twitter|^x$|tweet', re.I), 'X (Twitter)'),
    (re.compile(r'google', re.I), 'Google'),
    (re.compile(r'bing', re.I), 'Bing'),
    (re.compile(r'whatsapp', re.I), 'WhatsApp'),
    (re.compile(r'youtube|youtu\.?be', re.I), 'YouTube'),
    (re.compile(r'tiktok', re.I), 'TikTok'),
    (re.compile(r'reddit', re.I), 'Reddit'),
    (re.compile(r'chatgpt|openai', re.I), 'ChatGPT'),
    (re.compile(r'claude|anthropic', re.I), 'Claude'),
    (re.compile(r'perplexity', re.I), 'Perplexity'),
)


def channel_from_utm(utm_source: str) -> str | None:
    if not utm_source:
        return None
    for pattern, channel in _UTM_SOURCE_CHANNELS:
        if pattern.search(utm_source):
            return channel
    return None


def extract_search_query(referrer: str) -> str:
    """Alias retrocompatible: solo Referer."""
    return extract_search_query_from_referrer(referrer)


def _referrer_host(referrer: str) -> str:
    if not referrer:
        return ''
    parsed = urlparse(referrer)
    if parsed.hostname:
        return parsed.hostname.lower().removeprefix('www.')
    m = re.match(r'https?://([^/]+)', referrer)
    return m.group(1).lower().removeprefix('www.') if m else ''


def clean_referrer(referrer: str, own_host: str) -> str:
    """Solo el dominio del referrer; vacío si es interno o no hay."""
    host = _referrer_host(referrer)
    if not host:
        return ''
    own = own_host.lower().removeprefix('www.').split(':')[0]
    if own and (host == own or host.endswith('.' + own)):
        return ''
    return host


# Clasificación de origen para estadísticas (cada visita → un solo canal)
_REFERRER_CHANNEL_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r'(^|\.)google\.', re.I), 'Google'),
    (re.compile(r'(^|\.)bing\.', re.I), 'Bing'),
    (re.compile(r'duckduckgo\.', re.I), 'DuckDuckGo'),
    (re.compile(r'yahoo\.|search\.yahoo', re.I), 'Yahoo'),
    (re.compile(r'ecosia\.', re.I), 'Ecosia'),
    (re.compile(r'chatgpt\.|chat\.openai\.', re.I), 'ChatGPT'),
    (re.compile(r'claude\.|anthropic\.', re.I), 'Claude'),
    (re.compile(r'perplexity\.', re.I), 'Perplexity'),
    (re.compile(r'gemini\.google\.', re.I), 'Gemini'),
    (re.compile(r'facebook\.|fb\.|l\.facebook\.|m\.facebook\.', re.I), 'Facebook'),
    (re.compile(r'instagram\.', re.I), 'Instagram'),
    (re.compile(r'(^|\.)t\.co$|twitter\.|x\.com', re.I), 'X (Twitter)'),
    (re.compile(r'linkedin\.|lnkd\.in', re.I), 'LinkedIn'),
    (re.compile(r'whatsapp\.|wa\.me', re.I), 'WhatsApp'),
    (re.compile(r'youtube\.|youtu\.be', re.I), 'YouTube'),
    (re.compile(r'reddit\.', re.I), 'Reddit'),
    (re.compile(r'pinterest\.', re.I), 'Pinterest'),
    (re.compile(r'tiktok\.', re.I), 'TikTok'),
    (re.compile(r't\.me|telegram\.', re.I), 'Telegram'),
    (re.compile(r'yandex\.|baidu\.|qwant\.|startpage\.|search\.brave\.|ask\.', re.I), 'Otros buscadores'),
)

REFERRER_KNOWN_CHANNELS = frozenset({channel for _p, channel in _REFERRER_CHANNEL_RULES})


def referrer_channel(referrer_host: str) -> str:
    """Agrupa un dominio referrer en un canal conocido o «Otros referentes» / «Tráfico directo»."""
    host = (referrer_host or '').strip().lower()
    if not host:
        return 'Tráfico directo'
    for pattern, channel in _REFERRER_CHANNEL_RULES:
        if pattern.search(host):
            return channel
    return 'Otros referentes'


def referrer_bucket(referrer_host: str) -> str:
    """Clave de agrupación: canal conocido, dominio concreto si es desconocido, o tráfico directo."""
    host = (referrer_host or '').strip().lower()
    if not host:
        return 'Tráfico directo'
    for pattern, channel in _REFERRER_CHANNEL_RULES:
        if pattern.search(host):
            return channel
    return host


def visit_origin_channel(referrer_host: str, utm_source: str = '') -> str:
    """Canal de origen: Referer, utm_source si no hay referrer, o tráfico directo."""
    ref = (referrer_host or '').strip()
    if ref:
        bucket = referrer_bucket(ref)
        if bucket != 'Tráfico directo':
            return bucket
    utm_channel = channel_from_utm(utm_source)
    if utm_channel:
        return utm_channel
    if ref:
        return referrer_bucket(ref)
    return 'Tráfico directo'


def visitor_id(ip: str, user_agent: str) -> str:
    """Identificador de visitante para contar únicos (hash de IP + user-agent)."""
    return hashlib.sha256(f'{ip}|{user_agent}'.encode()).hexdigest()[:20]


def track(
    path: str,
    referrer: str,
    ip: str,
    user_agent: str,
    own_host: str,
    landing_query_string: str = '',
) -> None:
    navegador, so, dispositivo = parse_user_agent(user_agent)
    query, query_source = resolve_search_query_with_source(referrer, landing_query_string)
    utm_source = extract_utm_source(landing_query_string)
    try:
        db.record_visit(
            path=path,
            referrer=clean_referrer(referrer, own_host),
            referrer_query=query,
            referrer_query_source=query_source,
            utm_source=utm_source,
            ip=ip,
            visitante=visitor_id(ip, user_agent),
            navegador=navegador,
            so=so,
            dispositivo=dispositivo,
        )
    except Exception as e:
        print(f'[stats] Error registrando visita: {e}')

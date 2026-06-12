"""Registro de visitas tipo WP Statistics: parseo de user-agent y tracking."""
import hashlib
import re

from . import db

BOT_PATTERN = re.compile(
    r'bot|crawl|spider|slurp|bingpreview|facebookexternalhit|whatsapp|telegram|'
    r'curl|wget|python-requests|httpx|go-http-client|java/|libwww|headless|'
    r'lighthouse|pingdom|uptimerobot|monitor|scrapy|semrush|ahrefs|mj12|dotbot|petalbot',
    re.IGNORECASE,
)

EXCLUDED_PATHS = ('/sitemap.xml', '/robots.txt', '/favicon.ico')


def is_bot(user_agent: str) -> bool:
    return not user_agent or bool(BOT_PATTERN.search(user_agent))


def should_track(path: str, method: str, status_code: int, content_type: str, user_agent: str) -> bool:
    if method != 'GET' or status_code != 200:
        return False
    if not content_type.startswith('text/html'):
        return False
    if path.startswith('/static/') or path.startswith('/admin') or path == '/health' or path in EXCLUDED_PATHS:
        return False
    if is_bot(user_agent):
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


def clean_referrer(referrer: str, own_host: str) -> str:
    """Solo el dominio del referrer; vacío si es interno o no hay."""
    if not referrer:
        return ''
    m = re.match(r'https?://([^/]+)', referrer)
    if not m:
        return ''
    host = m.group(1).lower().removeprefix('www.')
    if own_host.removeprefix('www.') in host:
        return ''
    return host


def visitor_id(ip: str, user_agent: str) -> str:
    """Identificador de visitante para contar únicos (hash de IP + user-agent)."""
    return hashlib.sha256(f'{ip}|{user_agent}'.encode()).hexdigest()[:20]


def track(path: str, referrer: str, ip: str, user_agent: str, own_host: str) -> None:
    navegador, so, dispositivo = parse_user_agent(user_agent)
    try:
        db.record_visit(
            path=path,
            referrer=clean_referrer(referrer, own_host),
            ip=ip,
            visitante=visitor_id(ip, user_agent),
            navegador=navegador,
            so=so,
            dispositivo=dispositivo,
        )
    except Exception as e:
        print(f'[stats] Error registrando visita: {e}')

"""Acceso a YouTube sin API key: feed RSS del canal y transcripciones."""
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

FEED_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id={cid}'
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'media': 'http://search.yahoo.com/mrss/',
}
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'es-ES,es;q=0.9'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8', errors='replace')


def resolve_channel(url_o_id: str) -> dict:
    """Acepta URL de canal (/channel/UC…, /@handle, /user/…) o un channel_id directo.

    Devuelve {'channel_id': …, 'nombre': …, 'url': …}. Lanza ValueError si no se resuelve.
    """
    texto = url_o_id.strip()
    m = re.search(r'(UC[0-9A-Za-z_-]{22})', texto)
    if m:
        channel_id = m.group(1)
    else:
        if not texto.startswith('http'):
            texto = f'https://www.youtube.com/@{texto.lstrip("@")}'
        html = _fetch(texto)
        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
        if not m:
            m = re.search(r'channel/(UC[0-9A-Za-z_-]{22})', html)
        if not m:
            raise ValueError('No se pudo extraer el channel_id de esa URL')
        channel_id = m.group(1)

    feed = fetch_feed(channel_id)
    return {
        'channel_id': channel_id,
        'nombre': feed['nombre'],
        'url': f'https://www.youtube.com/channel/{channel_id}',
    }


def fetch_feed(channel_id: str) -> dict:
    """Devuelve {'nombre': str, 'videos': [{'video_id', 'titulo', 'url', 'publicado'}]}."""
    xml_text = _fetch(FEED_URL.format(cid=channel_id))
    root = ET.fromstring(xml_text)
    nombre = root.findtext('atom:title', default='', namespaces=NS)
    videos = []
    for entry in root.findall('atom:entry', NS):
        vid = entry.findtext('yt:videoId', default='', namespaces=NS)
        if not vid:
            continue
        videos.append({
            'video_id': vid,
            'titulo': entry.findtext('atom:title', default='', namespaces=NS),
            'url': f'https://www.youtube.com/watch?v={vid}',
            'publicado': entry.findtext('atom:published', default='', namespaces=NS),
        })
    return {'nombre': nombre, 'videos': videos}


def _proxy_config():
    """Proxy para saltar el bloqueo de YouTube a IPs de datacenter.

    - WEBSHARE_PROXY_USERNAME / WEBSHARE_PROXY_PASSWORD: proxies residenciales
      rotatorios de Webshare (lo que recomienda la propia librería).
    - YT_PROXY: URL de un proxy genérico http/socks5 (p. ej. http://user:pass@host:puerto).
    """
    user = os.environ.get('WEBSHARE_PROXY_USERNAME', '').strip()
    pwd = os.environ.get('WEBSHARE_PROXY_PASSWORD', '').strip()
    if user and pwd:
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return WebshareProxyConfig(proxy_username=user, proxy_password=pwd)
    proxy = os.environ.get('YT_PROXY', '').strip()
    if proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(http_url=proxy, https_url=proxy)
    return None


def fetch_transcript(video_id: str, idiomas: tuple[str, ...] = ('es', 'es-ES', 'en')) -> str:
    """Transcripción del vídeo desde los subtítulos (incluidos los automáticos).

    Intenta primero la API de transcripciones (rápida). Si YouTube bloquea la IP,
    recurre a un navegador real headless que abre la página como una persona.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    try:
        api = YouTubeTranscriptApi(proxy_config=_proxy_config())
        transcript = api.fetch(video_id, languages=list(idiomas))
        textos = [snippet.text.strip() for snippet in transcript if snippet.text.strip()]
        return ' '.join(textos)
    except Exception as e:
        if not is_blocked_error(e):
            raise
        print(f'[youtube] API bloqueada para {video_id}; usando navegador headless…')
        from .browser_transcript import fetch_transcript_browser
        return fetch_transcript_browser(video_id)


def is_blocked_error(e: Exception) -> bool:
    """True si el fallo es por bloqueo de IP/rate-limit de YouTube (reintentable)."""
    texto = str(e).lower()
    return any(s in texto for s in (
        'blocking requests from your ip',
        'ipblocked', 'requestblocked',
        'too many requests', 'sign in to confirm',
    ))

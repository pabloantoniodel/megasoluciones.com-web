"""Geolocalización de IPs con caché en SQLite (solo para el panel de estadísticas)."""
import json
import urllib.request

from .db import get_db

UA = 'Megasoluciones-Stats/1.0'
# IPs privadas / locales
_PRIVATE_PREFIXES = ('10.', '127.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                     '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
                     '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '::1', 'fe80:')


def _ensure_geo_table() -> None:
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ip_geo (
                ip TEXT PRIMARY KEY,
                pais TEXT,
                pais_codigo TEXT,
                actualizado TEXT DEFAULT (datetime('now'))
            )
        """)


def _is_private(ip: str) -> bool:
    return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)


def lookup_country(ip: str) -> tuple[str, str]:
    """Devuelve (nombre_país, código_ISO). Vacío si no se puede resolver."""
    if not ip or _is_private(ip):
        return '—', ''

    _ensure_geo_table()
    with get_db() as conn:
        row = conn.execute(
            'SELECT pais, pais_codigo FROM ip_geo WHERE ip = ?', (ip,),
        ).fetchone()
        if row and row['pais']:
            return row['pais'], row['pais_codigo'] or ''

    pais, codigo = _fetch_country(ip)
    with get_db() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO ip_geo (ip, pais, pais_codigo) VALUES (?, ?, ?)',
            (ip, pais or '—', codigo or ''),
        )
    return pais or '—', codigo or ''


def _fetch_country(ip: str) -> tuple[str, str]:
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,country,countryCode'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        if data.get('status') == 'success':
            return data.get('country', ''), data.get('countryCode', '')
    except Exception as e:
        print(f'[geoip] Error resolviendo {ip}: {e}')
    return '', ''

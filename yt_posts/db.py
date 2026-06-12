"""Base de datos SQLite compartida: posts desde YouTube + estadísticas de visitas."""
import os
import re
import sqlite3
import unicodedata
from datetime import datetime

DATA_DIR = os.environ.get('DATA_DIR') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DB_PATH = os.path.join(DATA_DIR, 'megasoluciones.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS canales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE NOT NULL,
    nombre TEXT,
    url TEXT,
    activo INTEGER DEFAULT 1,
    creado TEXT DEFAULT (datetime('now')),
    ultimo_chequeo TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    canal_id INTEGER REFERENCES canales(id),
    titulo_video TEXT,
    url TEXT,
    publicado_video TEXT,
    transcripcion TEXT,
    post_titulo TEXT,
    post_slug TEXT UNIQUE,
    post_resumen TEXT,
    post_cuerpo TEXT,
    estado TEXT DEFAULT 'nuevo',
    error_motivo TEXT,
    intentos INTEGER DEFAULT 0,
    creado TEXT DEFAULT (datetime('now')),
    actualizado TEXT,
    publicado TEXT
);

CREATE TABLE IF NOT EXISTS visitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT DEFAULT (datetime('now')),
    fecha TEXT,
    path TEXT,
    referrer TEXT,
    ip TEXT,
    visitante TEXT,
    navegador TEXT,
    so TEXT,
    dispositivo TEXT
);

CREATE INDEX IF NOT EXISTS idx_visitas_fecha ON visitas(fecha);
CREATE INDEX IF NOT EXISTS idx_visitas_path ON visitas(path);
CREATE INDEX IF NOT EXISTS idx_videos_estado ON videos(estado);

CREATE TABLE IF NOT EXISTS ips_excluidas (
    ip TEXT PRIMARY KEY,
    motivo TEXT,
    es_robot INTEGER DEFAULT 0,
    excluido TEXT DEFAULT (datetime('now'))
);
"""

# Rutas internas + IPs excluidas provisionalmente en el panel
STATS_EXCLUDE_SQL = (
    "path NOT LIKE '/admin%' AND path NOT LIKE '/static/%' AND path != '/health' "
    "AND NOT EXISTS (SELECT 1 FROM ips_excluidas ex WHERE ex.ip = visitas.ip)"
)


def get_db() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=15000')
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(SCHEMA)
        # Migración para BDs creadas antes de añadir la columna
        try:
            conn.execute('ALTER TABLE videos ADD COLUMN intentos INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        # Eliminar visitas del panel / estáticos registradas antes del filtro
        conn.execute(
            "DELETE FROM visitas WHERE path LIKE '/admin%' OR path LIKE '/static/%' OR path = '/health'"
        )


def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return text[:80].rstrip('-') or 'post'


def unique_slug(conn: sqlite3.Connection, base: str, exclude_id: int | None = None) -> str:
    slug = base
    n = 2
    while True:
        row = conn.execute(
            'SELECT id FROM videos WHERE post_slug = ? AND (? IS NULL OR id != ?)',
            (slug, exclude_id, exclude_id),
        ).fetchone()
        if not row:
            return slug
        slug = f'{base}-{n}'
        n += 1


# ── Canales ──────────────────────────────────────────────────────────

def add_canal(channel_id: str, nombre: str, url: str) -> None:
    with get_db() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO canales (channel_id, nombre, url) VALUES (?, ?, ?)',
            (channel_id, nombre, url),
        )


def list_canales() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute('SELECT * FROM canales ORDER BY creado DESC').fetchall()


def set_canal_activo(canal_id: int, activo: bool) -> None:
    with get_db() as conn:
        conn.execute('UPDATE canales SET activo = ? WHERE id = ?', (1 if activo else 0, canal_id))


def delete_canal(canal_id: int) -> None:
    with get_db() as conn:
        conn.execute('DELETE FROM canales WHERE id = ?', (canal_id,))


def touch_canal(canal_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE canales SET ultimo_chequeo = datetime('now') WHERE id = ?", (canal_id,))


# ── Videos / posts ───────────────────────────────────────────────────

def add_video(video_id: str, canal_id: int, titulo: str, url: str, publicado: str) -> bool:
    """Devuelve True si el vídeo es nuevo."""
    with get_db() as conn:
        cur = conn.execute(
            'INSERT OR IGNORE INTO videos (video_id, canal_id, titulo_video, url, publicado_video) '
            'VALUES (?, ?, ?, ?, ?)',
            (video_id, canal_id, titulo, url, publicado),
        )
        return cur.rowcount > 0


def get_video(vid: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            'SELECT v.*, c.nombre AS canal_nombre, c.url AS canal_url FROM videos v '
            'LEFT JOIN canales c ON c.id = v.canal_id WHERE v.id = ?',
            (vid,),
        ).fetchone()


def list_videos(estado: str | None = None) -> list[sqlite3.Row]:
    with get_db() as conn:
        if estado:
            return conn.execute(
                'SELECT v.*, c.nombre AS canal_nombre FROM videos v '
                'LEFT JOIN canales c ON c.id = v.canal_id WHERE v.estado = ? ORDER BY v.creado DESC',
                (estado,),
            ).fetchall()
        return conn.execute(
            'SELECT v.*, c.nombre AS canal_nombre FROM videos v '
            'LEFT JOIN canales c ON c.id = v.canal_id ORDER BY v.creado DESC',
        ).fetchall()


def videos_pendientes_proceso() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT v.*, c.nombre AS canal_nombre, c.url AS canal_url FROM videos v "
            "LEFT JOIN canales c ON c.id = v.canal_id "
            "WHERE v.estado IN ('nuevo', 'transcrito') "
            "ORDER BY v.publicado_video DESC",
        ).fetchall()


def update_video(vid: int, **campos) -> None:
    if not campos:
        return
    sets = ', '.join(f'{k} = ?' for k in campos)
    valores = list(campos.values()) + [vid]
    with get_db() as conn:
        conn.execute(f"UPDATE videos SET {sets}, actualizado = datetime('now') WHERE id = ?", valores)


def posts_publicados() -> list[dict]:
    """Posts publicados con el mismo formato que la lista RECURSOS de app.py."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT v.*, c.nombre AS canal_nombre, c.url AS canal_url FROM videos v "
            "LEFT JOIN canales c ON c.id = v.canal_id "
            "WHERE v.estado = 'publicado' ORDER BY v.publicado DESC",
        ).fetchall()
    posts = []
    for r in rows:
        posts.append({
            'slug': r['post_slug'],
            'titulo': r['post_titulo'],
            'resumen': r['post_resumen'],
            'fecha': (r['publicado'] or r['creado'] or '')[:10],
            'cluster': 'video',
            'cta_servicio': 'consultoria-ia',
            'video_id': r['video_id'],
            'video_url': r['url'],
            'video_titulo': r['titulo_video'],
            'canal_nombre': r['canal_nombre'],
            'canal_url': r['canal_url'],
            'cuerpo': r['post_cuerpo'],
        })
    return posts


def get_post_publicado(slug: str) -> dict | None:
    return next((p for p in posts_publicados() if p['slug'] == slug), None)


# ── Estadísticas ─────────────────────────────────────────────────────

def record_visit(path: str, referrer: str, ip: str, visitante: str,
                 navegador: str, so: str, dispositivo: str) -> None:
    with get_db() as conn:
        conn.execute(
            'INSERT INTO visitas (fecha, path, referrer, ip, visitante, navegador, so, dispositivo) '
            "VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?)",
            (path, referrer, ip, visitante, navegador, so, dispositivo),
        )


def purge_old_visits(days: int = 90) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM visitas WHERE fecha < date('now', ?)",
            (f'-{days} days',),
        )
        return cur.rowcount


def stats_summary(desde: str, hasta: str) -> dict:
    """Resumen de visitas en un rango de fechas (inclusive)."""
    ex = STATS_EXCLUDE_SQL
    with get_db() as conn:
        def one(q, *args):
            return conn.execute(q, args).fetchone()[0] or 0
        return {
            'visitas': one(
                f'SELECT COUNT(*) FROM visitas WHERE fecha BETWEEN ? AND ? AND {ex}',
                desde, hasta,
            ),
            'unicos': one(
                f'SELECT COUNT(DISTINCT visitante) FROM visitas WHERE fecha BETWEEN ? AND ? AND {ex}',
                desde, hasta,
            ),
            'dias': one(
                f'SELECT COUNT(DISTINCT fecha) FROM visitas WHERE fecha BETWEEN ? AND ? AND {ex}',
                desde, hasta,
            ),
        }


def stats_overview() -> dict:
    """KPIs fijos: hoy, 7 días y 30 días (siempre visibles en el panel)."""
    ex = STATS_EXCLUDE_SQL
    with get_db() as conn:
        def one(q, *args):
            return conn.execute(q, args).fetchone()[0] or 0
        return {
            'hoy_visitas': one(f"SELECT COUNT(*) FROM visitas WHERE fecha = date('now') AND {ex}"),
            'hoy_unicos': one(f"SELECT COUNT(DISTINCT visitante) FROM visitas WHERE fecha = date('now') AND {ex}"),
            'semana_visitas': one(f"SELECT COUNT(*) FROM visitas WHERE fecha >= date('now', '-6 days') AND {ex}"),
            'semana_unicos': one(f"SELECT COUNT(DISTINCT visitante) FROM visitas WHERE fecha >= date('now', '-6 days') AND {ex}"),
            'mes_visitas': one(f"SELECT COUNT(*) FROM visitas WHERE fecha >= date('now', '-29 days') AND {ex}"),
            'mes_unicos': one(f"SELECT COUNT(DISTINCT visitante) FROM visitas WHERE fecha >= date('now', '-29 days') AND {ex}"),
        }


def stats_series_range(desde: str, hasta: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            f'SELECT fecha, COUNT(*) AS visitas, COUNT(DISTINCT visitante) AS unicos '
            f'FROM visitas WHERE fecha BETWEEN ? AND ? AND {STATS_EXCLUDE_SQL} GROUP BY fecha ORDER BY fecha',
            (desde, hasta),
        ).fetchall()
    return [dict(r) for r in rows]


def stats_series(days: int = 30) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT fecha, COUNT(*) AS visitas, COUNT(DISTINCT visitante) AS unicos "
            f"FROM visitas WHERE fecha >= date('now', ?) AND {STATS_EXCLUDE_SQL} GROUP BY fecha ORDER BY fecha",
            (f'-{days - 1} days',),
        ).fetchall()
    return [dict(r) for r in rows]


def stats_top_range(campo: str, desde: str, hasta: str, limit: int = 15) -> list[dict]:
    assert campo in ('path', 'referrer', 'navegador', 'so', 'dispositivo', 'ip')
    with get_db() as conn:
        rows = conn.execute(
            f'SELECT {campo} AS valor, COUNT(*) AS visitas FROM visitas '
            f"WHERE fecha BETWEEN ? AND ? AND {campo} != '' AND {STATS_EXCLUDE_SQL} "
            f'GROUP BY {campo} ORDER BY visitas DESC LIMIT ?',
            (desde, hasta, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def stats_top_pages_paginated(
    desde: str, hasta: str, page: int = 1, per_page: int = 15,
) -> dict:
    """Páginas más visitadas con visitantes únicos y paginación."""
    page = max(1, page)
    per_page = max(5, min(per_page, 50))
    offset = (page - 1) * per_page

    with get_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(DISTINCT path) FROM visitas "
            f"WHERE fecha BETWEEN ? AND ? AND path != '' AND {STATS_EXCLUDE_SQL}",
            (desde, hasta),
        ).fetchone()[0] or 0
        rows = conn.execute(
            f'SELECT path AS valor, COUNT(*) AS visitas, COUNT(DISTINCT visitante) AS unicos '
            f"FROM visitas WHERE fecha BETWEEN ? AND ? AND path != '' AND {STATS_EXCLUDE_SQL} "
            f'GROUP BY path ORDER BY visitas DESC LIMIT ? OFFSET ?',
            (desde, hasta, per_page, offset),
        ).fetchall()

    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page > total_pages:
        page = total_pages

    return {
        'filas': [dict(r) for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
    }


def stats_top(campo: str, days: int = 30, limit: int = 15) -> list[dict]:
    assert campo in ('path', 'referrer', 'navegador', 'so', 'dispositivo', 'ip')
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT {campo} AS valor, COUNT(*) AS visitas FROM visitas "
            f"WHERE fecha >= date('now', ?) AND {campo} != '' AND {STATS_EXCLUDE_SQL} "
            f'GROUP BY {campo} ORDER BY visitas DESC LIMIT ?',
            (f'-{days - 1} days', limit),
        ).fetchall()
    return [dict(r) for r in rows]


def _moda_dispositivo_ip(conn: sqlite3.Connection, ip: str, desde: str, hasta: str) -> str:
    row = conn.execute(
        f'SELECT dispositivo, COUNT(*) AS n FROM visitas '
        f"WHERE ip = ? AND fecha BETWEEN ? AND ? AND dispositivo != '' AND {STATS_EXCLUDE_SQL} "
        f'GROUP BY dispositivo ORDER BY n DESC LIMIT 1',
        (ip, desde, hasta),
    ).fetchone()
    return row['dispositivo'] if row else ''


DISPOSITIVO_ETIQUETAS = {
    'escritorio': 'Ordenador',
    'móvil': 'Móvil',
    'tablet': 'Tablet',
}

KNOWN_BOT_IP_PREFIXES: tuple[tuple[str, str], ...] = (
    ('66.249.', 'Googlebot'),
    ('66.102.', 'Google'),
    ('64.233.', 'Google'),
    ('72.14.', 'Google'),
    ('209.85.', 'Google'),
    ('216.239.', 'Google'),
    ('157.55.', 'Bingbot'),
    ('40.77.', 'Bing/Microsoft'),
    ('207.46.', 'Microsoft'),
    ('17.58.', 'Applebot'),
    ('17.56.', 'Applebot'),
    ('142.250.', 'Google'),
)

HUMAN_BROWSERS = ('Chrome', 'Firefox', 'Safari', 'Edge', 'Opera', 'Samsung Internet')


def _bot_label_for_ip(ip: str) -> str:
    for prefix, label in KNOWN_BOT_IP_PREFIXES:
        if ip.startswith(prefix):
            return label
    return ''


def _detect_robot_ip(conn: sqlite3.Connection, ip: str, desde: str, hasta: str) -> tuple[bool, str]:
    label = _bot_label_for_ip(ip)
    if label:
        return True, label
    placeholders = ','.join('?' * len(HUMAN_BROWSERS))
    row = conn.execute(
        f"""SELECT COUNT(*) AS total,
            SUM(CASE WHEN navegador IN ({placeholders}) THEN 0 ELSE 1 END) AS no_humano
            FROM visitas
            WHERE ip = ? AND fecha BETWEEN ? AND ?
            AND path NOT LIKE '/admin%' AND path NOT LIKE '/static/%' AND path != '/health'""",
        (*HUMAN_BROWSERS, ip, desde, hasta),
    ).fetchone()
    if row and row['total'] >= 3 and row['no_humano'] == row['total']:
        return True, 'Patrón automatizado'
    return False, ''


def excluir_ip(ip: str, motivo: str = 'manual', es_robot: bool = False) -> None:
    with get_db() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO ips_excluidas (ip, motivo, es_robot) VALUES (?, ?, ?)',
            (ip, motivo, 1 if es_robot else 0),
        )


def restaurar_ip(ip: str) -> bool:
    with get_db() as conn:
        cur = conn.execute('DELETE FROM ips_excluidas WHERE ip = ?', (ip,))
        return cur.rowcount > 0


def list_ips_excluidas() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT ip, motivo, es_robot, excluido FROM ips_excluidas ORDER BY excluido DESC',
        ).fetchall()
    return [dict(r) for r in rows]


def excluir_robots_en_rango(desde: str, hasta: str) -> int:
    """Excluye provisionalmente todas las IPs detectadas como robot en el rango."""
    with get_db() as conn:
        rows = conn.execute(
            f'SELECT ip, COUNT(*) AS visitas FROM visitas '
            f"WHERE fecha BETWEEN ? AND ? AND ip != '' AND {STATS_EXCLUDE_SQL} "
            f'GROUP BY ip',
            (desde, hasta),
        ).fetchall()
        count = 0
        for r in rows:
            es_robot, etiqueta = _detect_robot_ip(conn, r['ip'], desde, hasta)
            if es_robot:
                conn.execute(
                    'INSERT OR REPLACE INTO ips_excluidas (ip, motivo, es_robot) VALUES (?, ?, 1)',
                    (r['ip'], etiqueta or 'robot'),
                )
                count += 1
        return count


def _enriquecer_ip(conn: sqlite3.Connection, ip: str, visitas: int, desde: str, hasta: str) -> dict:
    from . import geoip

    dispositivo = _moda_dispositivo_ip(conn, ip, desde, hasta)
    pais, codigo = geoip.lookup_country(ip)
    es_robot, robot_etiqueta = _detect_robot_ip(conn, ip, desde, hasta)
    return {
        'ip': ip,
        'visitas': visitas,
        'dispositivo': dispositivo,
        'dispositivo_label': DISPOSITIVO_ETIQUETAS.get(dispositivo, dispositivo or '—'),
        'pais': pais,
        'pais_codigo': codigo,
        'es_robot': es_robot,
        'robot_etiqueta': robot_etiqueta,
        'tipo': 'robot' if es_robot else 'humano',
    }


def stats_ips_todas(desde: str, hasta: str) -> list[dict]:
    """Todas las IPs del rango con país y dispositivo (para tabla interactiva)."""
    with get_db() as conn:
        rows = conn.execute(
            f'SELECT ip, COUNT(*) AS visitas FROM visitas '
            f"WHERE fecha BETWEEN ? AND ? AND ip != '' AND {STATS_EXCLUDE_SQL} "
            f'GROUP BY ip ORDER BY visitas DESC',
            (desde, hasta),
        ).fetchall()
        return [_enriquecer_ip(conn, r['ip'], r['visitas'], desde, hasta) for r in rows]


def stats_ip_visitas(
    ip: str,
    desde: str,
    hasta: str,
    f_path: str = '',
    f_referrer: str = '',
    f_navegador: str = '',
    f_dispositivo: str = '',
) -> list[dict]:
    """Visitas individuales de una IP (subtabla desplegable)."""
    sql = (
        f'SELECT ts, fecha, path, referrer, navegador, so, dispositivo FROM visitas '
        f'WHERE ip = ? AND fecha BETWEEN ? AND ? AND {STATS_EXCLUDE_SQL}'
    )
    params: list = [ip, desde, hasta]
    if f_path:
        sql += ' AND path LIKE ?'
        params.append(f'%{f_path}%')
    if f_referrer:
        sql += ' AND referrer LIKE ?'
        params.append(f'%{f_referrer}%')
    if f_navegador:
        sql += ' AND navegador LIKE ?'
        params.append(f'%{f_navegador}%')
    if f_dispositivo:
        sql += ' AND dispositivo LIKE ?'
        params.append(f'%{f_dispositivo}%')
    sql += ' ORDER BY ts DESC LIMIT 500'
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {
            'ts': r['ts'],
            'fecha': r['fecha'],
            'path': r['path'],
            'referrer': r['referrer'] or '—',
            'navegador': r['navegador'] or '—',
            'so': r['so'] or '—',
            'dispositivo': DISPOSITIVO_ETIQUETAS.get(r['dispositivo'], r['dispositivo'] or '—'),
        }
        for r in rows
    ]


def stats_ips_paginated(desde: str, hasta: str, page: int = 1, per_page: int = 25) -> dict:
    """IPs agrupadas con visitas, dispositivo más frecuente y paginación."""
    todas = stats_ips_todas(desde, hasta)
    total = len(todas)
    page = max(1, page)
    per_page = max(10, min(per_page, 100))
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page
    return {
        'filas': todas[offset:offset + per_page],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
    }

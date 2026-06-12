"""Panel de control /admin: canales de YouTube, aprobación de posts y estadísticas."""
import os
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for,
)

from . import db, notify, pipeline, youtube

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def load_admin_password() -> str | None:
    for name in ('admin-password.txt', '.admin-password'):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), name)
        if os.path.isfile(path):
            pw = open(path, encoding='utf-8').read().strip()
            if pw and not pw.startswith('#'):
                return pw
    return os.environ.get('ADMIN_PASSWORD', '').strip() or None


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged'):
            return redirect(url_for('admin.login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = load_admin_password()
        if not password:
            flash('ADMIN_PASSWORD no está configurada en el servidor.', 'error')
        elif request.form.get('password') == password:
            session['admin_logged'] = True
            session.permanent = True
            return redirect(request.args.get('next') or url_for('admin.dashboard'))
        else:
            flash('Contraseña incorrecta.', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    estado = request.args.get('estado') or None
    videos = db.list_videos(estado)
    todos = db.list_videos()
    conteos = {}
    for v in todos:
        conteos[v['estado']] = conteos.get(v['estado'], 0) + 1
    return render_template(
        'admin/dashboard.html',
        videos=videos,
        canales=db.list_canales(),
        conteos=conteos,
        estado_activo=estado,
        total=len(todos),
    )


# ── Canales ──────────────────────────────────────────────────────────

@admin_bp.route('/canales/add', methods=['POST'])
@login_required
def canal_add():
    url = (request.form.get('url') or '').strip()
    if not url:
        flash('Indica la URL del canal.', 'error')
        return redirect(url_for('admin.dashboard'))
    try:
        info = youtube.resolve_channel(url)
        db.add_canal(info['channel_id'], info['nombre'], info['url'])
        flash(f"Canal añadido: {info['nombre']}", 'success')
    except Exception as e:
        flash(f'No se pudo añadir el canal: {e}', 'error')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/canales/<int:canal_id>/toggle', methods=['POST'])
@login_required
def canal_toggle(canal_id):
    canal = next((c for c in db.list_canales() if c['id'] == canal_id), None)
    if canal:
        db.set_canal_activo(canal_id, not canal['activo'])
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/canales/<int:canal_id>/delete', methods=['POST'])
@login_required
def canal_delete(canal_id):
    db.delete_canal(canal_id)
    flash('Canal eliminado.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/chequear', methods=['POST'])
@login_required
def chequear():
    try:
        resultado = pipeline.ciclo_completo()
        flash(
            f"Chequeo completado: {resultado['nuevos']} vídeos nuevos, "
            f"{resultado['borradores']} borradores generados.",
            'success',
        )
    except Exception as e:
        flash(f'Error en el chequeo: {e}', 'error')
    return redirect(url_for('admin.dashboard'))


# ── Revisión de posts ────────────────────────────────────────────────

@admin_bp.route('/video/<int:vid>')
@login_required
def video_detalle(vid):
    video = db.get_video(vid)
    if not video:
        abort(404)
    return render_template('admin/video.html', video=video)


@admin_bp.route('/video/<int:vid>/guardar', methods=['POST'])
@login_required
def video_guardar(vid):
    video = db.get_video(vid)
    if not video:
        abort(404)
    db.update_video(
        vid,
        post_titulo=request.form.get('post_titulo', '').strip(),
        post_resumen=request.form.get('post_resumen', '').strip(),
        post_cuerpo=request.form.get('post_cuerpo', '').strip(),
    )
    flash('Cambios guardados.', 'success')
    return redirect(url_for('admin.video_detalle', vid=vid))


@admin_bp.route('/video/<int:vid>/publicar', methods=['POST'])
@login_required
def video_publicar(vid):
    video = db.get_video(vid)
    if not video:
        abort(404)
    if not video['post_titulo'] or not video['post_cuerpo']:
        flash('El post no tiene título o cuerpo. Genera o edita el borrador antes de publicar.', 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))
    db.update_video(vid, estado='publicado', publicado=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    notify.notificar_publicado(video['post_titulo'], video['post_slug'])
    flash(f"Publicado: /recursos/{video['post_slug']}", 'success')
    return redirect(url_for('admin.video_detalle', vid=vid))


@admin_bp.route('/video/<int:vid>/rechazar', methods=['POST'])
@login_required
def video_rechazar(vid):
    db.update_video(vid, estado='rechazado')
    flash('Post rechazado (no se publicará).', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/video/<int:vid>/regenerar', methods=['POST'])
@login_required
def video_regenerar(vid):
    try:
        pipeline.regenerar(vid)
        flash('Post regenerado con IA.', 'success')
    except Exception as e:
        flash(f'Error regenerando: {e}', 'error')
    return redirect(url_for('admin.video_detalle', vid=vid))


# ── Estadísticas ─────────────────────────────────────────────────────

STATS_PRESETS = {
    'hoy': 0,
    '7': 6,
    '30': 29,
    '90': 89,
}


def _resolve_stats_range() -> tuple[str, str, str, str]:
    """Devuelve (desde, hasta, preset, etiqueta_rango). Por defecto: hoy."""
    hoy = date.today()
    preset = request.args.get('preset', 'hoy')
    desde_s = request.args.get('desde', '').strip()
    hasta_s = request.args.get('hasta', '').strip()

    if desde_s and hasta_s:
        try:
            d1 = date.fromisoformat(desde_s)
            d2 = date.fromisoformat(hasta_s)
            if d1 > d2:
                d1, d2 = d2, d1
            if d2 > hoy:
                d2 = hoy
            if d1 > hoy:
                d1 = hoy
            if d1 == d2 == hoy:
                return d1.isoformat(), d2.isoformat(), 'hoy', 'Hoy'
            if d1 == d2:
                return d1.isoformat(), d2.isoformat(), 'custom', d1.strftime('%d/%m/%Y')
            return (
                d1.isoformat(),
                d2.isoformat(),
                'custom',
                f"{d1.strftime('%d/%m/%Y')} – {d2.strftime('%d/%m/%Y')}",
            )
        except ValueError:
            pass

    if preset in STATS_PRESETS:
        back = STATS_PRESETS[preset]
        if preset == 'hoy':
            iso = hoy.isoformat()
            return iso, iso, 'hoy', 'Hoy'
        desde = (hoy - timedelta(days=back)).isoformat()
        return desde, hoy.isoformat(), preset, f'Últimos {back + 1} días'

    iso = hoy.isoformat()
    return iso, iso, 'hoy', 'Hoy'


@admin_bp.route('/api/stats/ips')
@login_required
def api_stats_ips():
    desde, hasta, _, _ = _resolve_stats_range()
    return jsonify({'filas': db.stats_ips_todas(desde, hasta), 'desde': desde, 'hasta': hasta})


@admin_bp.route('/api/stats/ip/<path:ip>/visitas')
@login_required
def api_stats_ip_visitas(ip):
    desde, hasta, _, _ = _resolve_stats_range()
    visitas = db.stats_ip_visitas(
        ip,
        desde,
        hasta,
        f_path=request.args.get('path', '').strip(),
        f_referrer=request.args.get('referrer', '').strip(),
        f_navegador=request.args.get('navegador', '').strip(),
        f_dispositivo=request.args.get('dispositivo', '').strip(),
    )
    return jsonify({'ip': ip, 'visitas': visitas, 'total': len(visitas)})


@admin_bp.route('/api/stats/ips/excluidas')
@login_required
def api_stats_ips_excluidas():
    return jsonify({'filas': db.list_ips_excluidas()})


@admin_bp.route('/api/stats/ip/<path:ip>/excluir', methods=['POST'])
@login_required
def api_stats_ip_excluir(ip):
    data = request.get_json(silent=True) or {}
    motivo = (data.get('motivo') or request.form.get('motivo') or 'manual').strip()
    es_robot = bool(data.get('es_robot') or request.form.get('es_robot'))
    db.excluir_ip(ip, motivo=motivo, es_robot=es_robot)
    return jsonify({'ok': True, 'ip': ip})


@admin_bp.route('/api/stats/ip/<path:ip>/restaurar', methods=['POST'])
@login_required
def api_stats_ip_restaurar(ip):
    ok = db.restaurar_ip(ip)
    return jsonify({'ok': ok, 'ip': ip})


@admin_bp.route('/api/stats/ips/excluir-robots', methods=['POST'])
@login_required
def api_stats_excluir_robots():
    desde, hasta, _, _ = _resolve_stats_range()
    count = db.excluir_robots_en_rango(desde, hasta)
    return jsonify({'ok': True, 'excluidas': count, 'desde': desde, 'hasta': hasta})


@admin_bp.route('/estadisticas')
@login_required
def estadisticas():
    desde, hasta, preset, rango_label = _resolve_stats_range()
    resumen = db.stats_summary(desde, hasta)
    try:
        pag_page = max(1, int(request.args.get('pag_page', 1)))
    except ValueError:
        pag_page = 1
    return render_template(
        'admin/estadisticas.html',
        desde=desde,
        hasta=hasta,
        preset=preset,
        rango_label=rango_label,
        resumen=resumen,
        overview=db.stats_overview(),
        series=db.stats_series_range(desde, hasta),
        top_paginas=db.stats_top_pages_paginated(desde, hasta, page=pag_page),
        top_referrers=db.stats_top_range('referrer', desde, hasta),
        top_navegadores=db.stats_top_range('navegador', desde, hasta, limit=8),
        top_dispositivos=db.stats_top_range('dispositivo', desde, hasta, limit=4),
        hoy_iso=date.today().isoformat(),
    )


# ── LinkedIn ───────────────────────────────────────────────────────

@admin_bp.route('/linkedin')
@login_required
def linkedin_panel():
    from . import linkedin_client, linkedin_queue

    cfg = linkedin_client.linkedin_config()
    masked = {
        'org_id': cfg['org_id'] or '—',
        'has_token': bool(cfg['access_token']),
        'has_refresh': bool(cfg['refresh_token']),
        'has_client': bool(cfg['client_id'] and cfg['client_secret']),
        'api_version': cfg['api_version'],
    }
    return render_template(
        'admin/linkedin.html',
        posts=linkedin_queue.load_queue(),
        configured=linkedin_client.is_configured(),
        config=masked,
    )


@admin_bp.route('/linkedin/test', methods=['POST'])
@login_required
def linkedin_test():
    from . import linkedin_client

    try:
        info = linkedin_client.test_connection()
        flash(f"Conexión OK — {info.get('name') or info.get('vanity_name') or info['org_urn']}", 'success')
    except Exception as e:
        flash(f'Error de conexión: {e}', 'error')
    return redirect(url_for('admin.linkedin_panel'))


@admin_bp.route('/linkedin/publish/<post_id>', methods=['POST'])
@login_required
def linkedin_publish_now(post_id):
    from . import linkedin_queue
    from .linkedin_worker import publish_one

    post = linkedin_queue.get_post(post_id)
    if not post:
        flash('Publicación no encontrada.', 'error')
    elif post.get('status') == 'published':
        flash('Esta publicación ya fue publicada.', 'error')
    elif publish_one(post):
        flash('Publicado en LinkedIn correctamente.', 'success')
    else:
        post = linkedin_queue.get_post(post_id)
        flash(f"Error al publicar: {post.get('error', 'desconocido')}", 'error')
    return redirect(url_for('admin.linkedin_panel'))


@admin_bp.route('/linkedin/schedule/<post_id>', methods=['POST'])
@login_required
def linkedin_schedule(post_id):
    from . import linkedin_queue

    scheduled_at = (request.form.get('scheduled_at') or '').strip()
    post = linkedin_queue.get_post(post_id)
    if not post:
        flash('Publicación no encontrada.', 'error')
    elif not scheduled_at:
        flash('Indica fecha y hora.', 'error')
    else:
        linkedin_queue.update_post(post_id, scheduled_at=scheduled_at, status='pending', error=None)
        flash(f'Programada para {scheduled_at}', 'success')
    return redirect(url_for('admin.linkedin_panel'))


@admin_bp.route('/linkedin/run-due', methods=['POST'])
@login_required
def linkedin_run_due():
    from .linkedin_worker import run_due

    result = run_due()
    if result.get('skipped'):
        flash('LinkedIn no está configurado (faltan claves).', 'error')
    else:
        flash(
            f"Ciclo completado: {result.get('published', 0)} publicadas, "
            f"{result.get('failed', 0)} fallidas de {result.get('due', 0)} pendientes.",
            'success' if not result.get('failed') else 'error',
        )
    return redirect(url_for('admin.linkedin_panel'))

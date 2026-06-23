"""Panel de control /admin: canales de YouTube, aprobación de posts y estadísticas."""
import json
import os
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for,
)

import recursos_seo
from recursos_seo import seo_check_recurso

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
    from . import social_queue

    estado = request.args.get('estado') or None
    videos = db.list_videos(estado)
    todos = db.list_videos()
    conteos = {}
    for v in todos:
        conteos[v['estado']] = conteos.get(v['estado'], 0) + 1
    social_by_video: dict[int, dict[str, dict]] = {}
    for p in social_queue.load_queue():
        vid = p.get('video_db_id')
        if vid is not None:
            social_by_video.setdefault(vid, {})[p['platform']] = p
    return render_template(
        'admin/dashboard.html',
        videos=videos,
        canales=db.list_canales(),
        conteos=conteos,
        estado_activo=estado,
        total=len(todos),
        social_by_video=social_by_video,
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
    from . import instagram_client, linkedin_client, social_queue, twitter_client
    video_d = dict(video)
    rel_raw = video_d.get('post_relacionados')
    if rel_raw:
        try:
            parsed = json.loads(rel_raw) if isinstance(rel_raw, str) else rel_raw
            if isinstance(parsed, list):
                video_d['post_relacionados'] = ', '.join(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    seo_issues = []
    try:
        from app import todos_los_recursos
        preview = {
            'slug': video_d.get('post_slug'),
            'titulo': video_d.get('post_titulo'),
            'resumen': video_d.get('post_resumen'),
            'cuerpo': video_d.get('post_cuerpo'),
            'cluster': video_d.get('post_cluster') or 'ia',
            'tipo': video_d.get('post_tipo') or 'noticia',
            'intencion': video_d.get('post_intencion') or 'noticia',
            'keyword_principal': video_d.get('post_keyword') or '',
            'video_id': video_d.get('video_id'),
        }
        seo_issues = seo_check_recurso(preview, todos_los_recursos())
    except Exception:
        pass
    social_posts = social_queue.get_posts_for_video(vid)
    return render_template(
        'admin/video.html',
        video=video_d,
        social_posts=social_posts,
        seo_issues=seo_issues,
        clusters=recursos_seo.CLUSTERS,
        twitter_configured=twitter_client.is_configured(),
        instagram_configured=instagram_client.is_configured(),
        linkedin_configured=linkedin_client.is_configured(),
    )


@admin_bp.route('/video/<int:vid>/guardar', methods=['POST'])
@login_required
def video_guardar(vid):
    video = db.get_video(vid)
    if not video:
        abort(404)
    old_slug = video['post_slug']
    new_slug = (request.form.get('post_slug') or old_slug or '').strip()
    cluster = (request.form.get('post_cluster') or 'ia').strip()
    if cluster not in recursos_seo.CLUSTERS:
        cluster = 'ia'

    from app import RECURSOS
    if new_slug and not recursos_seo.slug_disponible(
        new_slug, RECURSOS, db.list_video_slugs(exclude_id=vid), exclude_slug=old_slug,
    ):
        flash(f'Slug «{new_slug}» no disponible (duplicado en recursos estáticos o BD).', 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))

    if old_slug and new_slug and old_slug != new_slug and video['estado'] == 'publicado':
        if request.form.get('confirm_slug_change') != '1':
            flash('Cambio de slug en URL publicada: marca la confirmación y vuelve a guardar.', 'error')
            return redirect(url_for('admin.video_detalle', vid=vid))
        db.add_recursos_redirect(old_slug, new_slug)

    relacionados_raw = (request.form.get('post_relacionados') or '').strip()
    relacionados = [
        s.strip() for s in relacionados_raw.replace('\n', ',').split(',') if s.strip()
    ]

    db.update_video(
        vid,
        post_titulo=request.form.get('post_titulo', '').strip(),
        post_resumen=request.form.get('post_resumen', '').strip(),
        post_cuerpo=request.form.get('post_cuerpo', '').strip(),
        post_slug=new_slug or old_slug,
        post_cluster=cluster,
        post_tipo=(request.form.get('post_tipo') or 'noticia').strip(),
        post_intencion=(request.form.get('post_intencion') or 'noticia').strip(),
        post_keyword=(request.form.get('post_keyword') or '').strip(),
        post_relacionados=json.dumps(relacionados) if relacionados else None,
    )
    flash('Cambios guardados.', 'success')
    return redirect(url_for('admin.video_detalle', vid=vid))


@admin_bp.route('/video/<int:vid>/publicar', methods=['POST'])
@login_required
def video_publicar(vid):
    from app import RECURSOS, todos_los_recursos
    from . import social_content, social_queue, social_worker

    video = db.get_video(vid)
    if not video:
        abort(404)
    if not video['post_titulo'] or not video['post_cuerpo']:
        flash('El post no tiene título o cuerpo. Genera o edita el borrador antes de publicar.', 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))

    cluster = video['post_cluster'] if 'post_cluster' in video.keys() and video['post_cluster'] else None
    if not cluster or cluster == 'video':
        flash('Asigna un cluster (ia, desarrollo o automatizaciones) antes de publicar.', 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))

    articulo_check = {
        'slug': video['post_slug'],
        'titulo': video['post_titulo'],
        'resumen': video['post_resumen'],
        'cuerpo': video['post_cuerpo'],
        'cluster': cluster,
        'tipo': video['post_tipo'] if 'post_tipo' in video.keys() else 'noticia',
        'intencion': video['post_intencion'] if 'post_intencion' in video.keys() else 'noticia',
        'keyword_principal': video['post_keyword'] if 'post_keyword' in video.keys() else '',
        'video_id': video['video_id'],
    }
    issues = seo_check_recurso(articulo_check, todos_los_recursos())
    errors = [i for i in issues if i['level'] == 'error']
    if errors:
        flash('No se puede publicar: ' + errors[0]['message'], 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))
    for w in issues:
        if w['level'] == 'warning':
            msg = f"SEO: {w['message']}"
            if w.get('alternativas'):
                msg += ' Alternativas: ' + ' | '.join(w['alternativas'][:3])
            flash(msg, 'warning')

    publish_twitter = request.form.get('publish_twitter') == '1'
    publish_instagram = request.form.get('publish_instagram') == '1'
    publish_linkedin = request.form.get('publish_linkedin') == '1'

    db.update_video(vid, estado='publicado', publicado=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    notify.notificar_publicado(video['post_titulo'], video['post_slug'])

    video_d = dict(db.get_video(vid))
    social_msgs = []
    try:
        social_content.prepare_for_video(video_d)
        if publish_twitter:
            pid = social_queue.post_id(vid, 'twitter')
            if social_worker.publish_by_id(pid):
                social_msgs.append('Twitter publicado')
            else:
                p = social_queue.get_post(pid)
                social_msgs.append(f'Twitter: {p.get("error", "error") if p else "error"}')
        if publish_instagram:
            pid = social_queue.post_id(vid, 'instagram')
            if social_worker.publish_by_id(pid):
                social_msgs.append('Instagram publicado')
            else:
                p = social_queue.get_post(pid)
                social_msgs.append(f'Instagram: {p.get("error", "error") if p else "error"}')
        if publish_linkedin:
            pid = social_queue.post_id(vid, 'linkedin')
            if social_worker.publish_by_id(pid):
                social_msgs.append('LinkedIn publicado')
            else:
                p = social_queue.get_post(pid)
                social_msgs.append(f'LinkedIn: {p.get("error", "error") if p else "error"}')
    except Exception as e:
        social_msgs.append(f'Redes: {e}')

    msg = f"Publicado: /recursos/{video['post_slug']}"
    if social_msgs:
        msg += ' · ' + ' · '.join(social_msgs)
    flash(msg, 'success')
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


@admin_bp.route('/api/stats/ips/activas')
@login_required
def api_stats_ips_activas():
    desde, hasta, _, _ = _resolve_stats_range()
    limit = min(max(int(request.args.get('limit', 15)), 5), 50)
    return jsonify({
        'filas': db.stats_ips_mas_activas(desde, hasta, limit=limit),
        'desde': desde,
        'hasta': hasta,
    })


@admin_bp.route('/api/stats/ips/recientes')
@login_required
def api_stats_ips_recientes():
    desde, hasta, _, _ = _resolve_stats_range()
    limit = min(max(int(request.args.get('limit', 15)), 5), 50)
    return jsonify({
        'filas': db.stats_ips_recientes(desde, hasta, limit=limit),
        'desde': desde,
        'hasta': hasta,
    })


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
        f_busqueda=request.args.get('busqueda', '').strip(),
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
    include_google = request.args.get('include_google', '').lower() in ('1', 'true', 'yes')
    count = db.excluir_robots_en_rango(desde, hasta, include_google=include_google)
    return jsonify({
        'ok': True,
        'excluidas': count,
        'desde': desde,
        'hasta': hasta,
        'include_google': include_google,
    })


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
        exclusion_summary=db.stats_exclusion_summary(desde, hasta),
        series=db.stats_series_range_full(desde, hasta),
        top_paginas=db.stats_top_pages_paginated(desde, hasta, page=pag_page),
        referrer_breakdown=db.stats_referrer_breakdown(desde, hasta),
        origenes_excluidos=db.stats_origins_excluded_only(desde, hasta),
        top_busquedas=db.stats_top_search_queries(desde, hasta),
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


# ── Twitter / Instagram (posts de vídeo) ─────────────────────────────

@admin_bp.route('/social')
@login_required
def social_panel():
    from . import instagram_client, linkedin_client, social_queue, twitter_client

    posts = social_queue.load_queue()
    posts.sort(key=lambda p: (p.get('video_db_id') or 0, p.get('platform', '')))
    cfg_tw = twitter_client.twitter_config()
    cfg_ig = instagram_client.instagram_config()
    cfg_li = linkedin_client.linkedin_config()
    return render_template(
        'admin/social.html',
        posts=posts,
        twitter_configured=twitter_client.is_configured(),
        instagram_configured=instagram_client.is_configured(),
        linkedin_configured=linkedin_client.is_configured(),
        config={
            'twitter_has_token': bool(cfg_tw.get('access_token')),
            'instagram_has_token': bool(cfg_ig.get('access_token')),
            'instagram_user_id': cfg_ig.get('user_id') or '',
            'linkedin_org_id': cfg_li.get('org_id') or '',
            'linkedin_has_token': bool(cfg_li.get('access_token')),
        },
    )


@admin_bp.route('/social/bootstrap', methods=['POST'])
@login_required
def social_bootstrap():
    from . import social_content

    regenerate = request.form.get('regenerate') == '1'
    try:
        n = social_content.prepare_all_published(regenerate=regenerate)
        flash(f'Preparados textos e imágenes para {n} vídeos publicados.', 'success')
    except Exception as e:
        flash(f'Error preparando redes: {e}', 'error')
    return redirect(request.referrer or url_for('admin.social_panel'))


@admin_bp.route('/social/test/<platform>', methods=['POST'])
@login_required
def social_test(platform):
    try:
        if platform == 'twitter':
            from . import twitter_client
            info = twitter_client.test_connection()
            flash(f"Twitter OK: @{info.get('username', '?')}", 'success')
        elif platform == 'instagram':
            from . import instagram_client
            info = instagram_client.test_connection()
            flash(f"Instagram OK: @{info.get('username', '?')}", 'success')
        elif platform == 'linkedin':
            from . import linkedin_client
            info = linkedin_client.test_connection()
            flash(f"LinkedIn OK: {info.get('name', '?')}", 'success')
        else:
            flash('Plataforma desconocida.', 'error')
    except Exception as e:
        flash(f'Error de conexión: {e}', 'error')
    return redirect(url_for('admin.social_panel'))


@admin_bp.route('/social/publish/<post_id>', methods=['POST'])
@login_required
def social_publish_now(post_id):
    from . import social_queue
    from .social_worker import publish_one

    post = social_queue.get_post(post_id)
    if not post:
        flash('Publicación no encontrada.', 'error')
    elif post.get('status') == 'published':
        flash('Ya publicada en esta red.', 'error')
    elif publish_one(post):
        flash(f"Publicado en {post['platform']}.", 'success')
    else:
        post = social_queue.get_post(post_id)
        flash(f"Error: {post.get('error', 'desconocido')}", 'error')
    return redirect(request.referrer or url_for('admin.social_panel'))


@admin_bp.route('/social/save/<post_id>', methods=['POST'])
@login_required
def social_save(post_id):
    from . import social_content, social_queue

    post = social_queue.get_post(post_id)
    if not post:
        flash('Publicación no encontrada.', 'error')
        return redirect(request.referrer or url_for('admin.social_panel'))

    text = (request.form.get('text') or '').strip()
    if text:
        social_queue.update_post(post_id, text=text, error=None)

    uploaded = request.files.get('image')
    if uploaded and uploaded.filename:
        try:
            fname = social_content.save_uploaded_image(post_id, uploaded)
            flash(f'Texto e imagen guardados ({fname}).', 'success')
        except Exception as e:
            flash(f'Imagen: {e}', 'error')
    elif text:
        flash('Texto guardado.', 'success')
    elif not text:
        flash('Indica texto o sube una imagen.', 'error')

    return redirect(request.referrer or url_for('admin.social_panel'))


@admin_bp.route('/social/image/<post_id>/regenerate', methods=['POST'])
@login_required
def social_regenerate_image(post_id):
    from . import social_content

    try:
        fname = social_content.regenerate_post_image(post_id)
        flash(f'Imagen regenerada desde YouTube: {fname}', 'success')
    except Exception as e:
        flash(f'Error regenerando imagen: {e}', 'error')
    return redirect(request.referrer or url_for('admin.social_panel'))


@admin_bp.route('/video/<int:vid>/social/prepare', methods=['POST'])
@login_required
def video_social_prepare(vid):
    from . import social_content

    video = db.get_video(vid)
    if not video:
        abort(404)
    if video['estado'] != 'publicado':
        flash('Solo se preparan redes para posts ya publicados en la web.', 'error')
        return redirect(url_for('admin.video_detalle', vid=vid))
    try:
        regenerate = request.form.get('regenerate') == '1'
        social_content.prepare_for_video(dict(video), regenerate=regenerate)
        flash('Textos e imagen preparados para Twitter, Instagram y LinkedIn.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.video_detalle', vid=vid))

"""Pipeline: detectar vídeos nuevos, transcribir, redactar y dejar en borrador."""
import os
import time
from datetime import date, timedelta

from . import db, notify, youtube
from .generator import generar_post

# YouTube bloquea ráfagas de peticiones de transcripción: pocas por ciclo y espaciadas
MAX_TRANSCRIPCIONES_POR_CICLO = int(os.environ.get('YT_MAX_TRANSCRIPTS_PER_CYCLE', 3))
PAUSA_ENTRE_TRANSCRIPCIONES_S = int(os.environ.get('YT_TRANSCRIPT_PAUSE_S', 25))
MAX_INTENTOS = int(os.environ.get('YT_MAX_RETRIES', 10))
# Antigüedad máxima (en días) del último vídeo del canal para procesarlo
MAX_ANTIGUEDAD_DIAS = int(os.environ.get('YT_MAX_VIDEO_AGE_DAYS', 2))


def chequear_canales() -> int:
    """Registra SOLO el vídeo más reciente de cada canal activo, y únicamente
    si es de los últimos días (MAX_ANTIGUEDAD_DIAS). Los vídeos ya registrados
    se ignoran (video_id es único), así que nunca se reintenta uno que ya
    tengamos. Devuelve cuántos vídeos nuevos hay.
    """
    limite = (date.today() - timedelta(days=MAX_ANTIGUEDAD_DIAS)).isoformat()
    nuevos = 0
    for canal in db.list_canales():
        if not canal['activo']:
            continue
        try:
            feed = youtube.fetch_feed(canal['channel_id'])
        except Exception as e:
            print(f"[pipeline] Error leyendo feed de {canal['nombre']}: {e}")
            continue
        if feed['videos']:
            ultimo = max(feed['videos'], key=lambda v: v['publicado'])
            if ultimo['publicado'][:10] >= limite:
                if db.add_video(ultimo['video_id'], canal['id'], ultimo['titulo'], ultimo['url'], ultimo['publicado']):
                    nuevos += 1
                    print(f"[pipeline] Vídeo nuevo: {ultimo['titulo']}")
        db.touch_canal(canal['id'])
    return nuevos


def procesar_pendientes() -> int:
    """Transcribe y redacta los vídeos en estado nuevo/transcrito. Devuelve borradores creados."""
    borradores = 0
    transcripciones_hechas = 0
    for video in db.videos_pendientes_proceso():
        vid = video['id']
        transcripcion = video['transcripcion']

        if video['estado'] == 'nuevo':
            if transcripciones_hechas >= MAX_TRANSCRIPCIONES_POR_CICLO:
                continue
            if transcripciones_hechas > 0:
                time.sleep(PAUSA_ENTRE_TRANSCRIPCIONES_S)
            transcripciones_hechas += 1
            try:
                transcripcion = youtube.fetch_transcript(video['video_id'])
                if not transcripcion or len(transcripcion) < 200:
                    raise ValueError('Transcripción vacía o demasiado corta')
                db.update_video(vid, transcripcion=transcripcion, estado='transcrito', error_motivo=None)
                print(f"[pipeline] Transcrito: {video['titulo_video']} ({len(transcripcion)} chars)")
            except Exception as e:
                intentos = (video['intentos'] or 0) + 1
                if youtube.is_blocked_error(e) and intentos < MAX_INTENTOS:
                    # Bloqueo temporal de YouTube: se queda pendiente y se reintenta en el próximo ciclo
                    db.update_video(
                        vid, intentos=intentos,
                        error_motivo=f'YouTube bloqueó la petición; se reintentará (intento {intentos}/{MAX_INTENTOS})',
                    )
                    print(f"[pipeline] Bloqueado por YouTube (intento {intentos}): {video['titulo_video']}")
                    continue
                motivo = f'Sin transcripción disponible: {e}'
                db.update_video(vid, estado='error', error_motivo=motivo, intentos=intentos)
                notify.notificar_error(video['titulo_video'], motivo, vid)
                continue

        try:
            datos = generar_post(
                titulo=video['titulo_video'],
                canal=video['canal_nombre'] or 'YouTube',
                url=video['url'],
                transcripcion=transcripcion,
            )
        except Exception as e:
            texto_error = str(e).lower()
            if 'insufficient_quota' in texto_error or 'rate limit' in texto_error or '429' in texto_error:
                # Sin saldo o rate-limit de OpenAI: la transcripción ya está guardada,
                # se reintenta en el próximo ciclo sin avisar por email
                db.update_video(
                    vid,
                    error_motivo='OpenAI sin saldo o con rate-limit; se reintentará automáticamente',
                )
                print(f"[pipeline] OpenAI sin cuota, se reintentará: {video['titulo_video']}")
                continue
            motivo = f'Error generando el post: {e}'
            db.update_video(vid, estado='error', error_motivo=motivo)
            notify.notificar_error(video['titulo_video'], motivo, vid)
            continue

        try:
            with db.get_db() as conn:
                slug = db.unique_slug(conn, db.slugify(datos['titulo']))
            db.update_video(
                vid,
                post_titulo=datos['titulo'],
                post_slug=slug,
                post_resumen=datos['resumen'],
                post_cuerpo=datos['cuerpo_html'],
                post_cluster='ia',
                post_tipo='noticia',
                post_intencion='noticia',
                estado='borrador',
                error_motivo=None,
            )
            borradores += 1
            print(f"[pipeline] Borrador creado: {datos['titulo']}")
            notify.notificar_borrador(
                vid, datos['titulo'], datos['resumen'],
                video['titulo_video'], video['canal_nombre'] or 'YouTube',
            )
        except Exception as e:
            motivo = f'Error generando el post: {e}'
            db.update_video(vid, estado='error', error_motivo=motivo)
            notify.notificar_error(video['titulo_video'], motivo, vid)
    return borradores


def regenerar(video_db_id: int) -> dict:
    """Regenera el post de un vídeo concreto (desde el panel). Devuelve los datos nuevos."""
    video = db.get_video(video_db_id)
    if not video:
        raise ValueError('Vídeo no encontrado')
    transcripcion = video['transcripcion']
    if not transcripcion:
        transcripcion = youtube.fetch_transcript(video['video_id'])
        db.update_video(video_db_id, transcripcion=transcripcion)
    datos = generar_post(
        titulo=video['titulo_video'],
        canal=video['canal_nombre'] or 'YouTube',
        url=video['url'],
        transcripcion=transcripcion,
    )
    with db.get_db() as conn:
        slug = video['post_slug'] or db.unique_slug(conn, db.slugify(datos['titulo']))
    db.update_video(
        video_db_id,
        post_titulo=datos['titulo'],
        post_slug=slug,
        post_resumen=datos['resumen'],
        post_cuerpo=datos['cuerpo_html'],
        estado='borrador',
        error_motivo=None,
    )
    return datos


def ciclo_completo() -> dict:
    db.init_db()
    nuevos = chequear_canales()
    borradores = procesar_pendientes()
    purgados = db.purge_old_visits(90)
    return {'nuevos': nuevos, 'borradores': borradores, 'visitas_purgadas': purgados}

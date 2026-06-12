"""Notificaciones por email (smtplib directo, usable desde el worker sin Flask)."""
import os
import smtplib
from email.message import EmailMessage

DESTINATARIO = os.environ.get('NOTIFY_EMAIL', 'info@megasolucion.net')
BASE_URL = os.environ.get('CANONICAL_BASE_URL', 'https://megasolucion.es').rstrip('/')


def send_email(asunto: str, cuerpo: str) -> bool:
    servidor = os.environ.get('MAIL_SERVER', 'smtp.serviciodecorreo.es')
    puerto = int(os.environ.get('MAIL_PORT', 465))
    usuario = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    remitente = os.environ.get('MAIL_DEFAULT_SENDER', 'info@megasolucion.net')
    use_ssl = os.environ.get('MAIL_USE_SSL', 'True') == 'True'

    if not usuario or not password:
        print(f'[notify] MAIL_USERNAME no configurado; email no enviado: {asunto}')
        return False

    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = remitente
    msg['To'] = DESTINATARIO
    msg.set_content(cuerpo)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(servidor, puerto, timeout=30) as smtp:
                smtp.login(usuario, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(servidor, puerto, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(usuario, password)
                smtp.send_message(msg)
        print(f'[notify] Email enviado: {asunto}')
        return True
    except Exception as e:
        print(f'[notify] Error enviando email: {e}')
        return False


def notificar_borrador(video_db_id: int, post_titulo: str, resumen: str, video_titulo: str, canal: str) -> None:
    send_email(
        asunto=f'[Megasoluciones] Borrador listo para revisar: {post_titulo}',
        cuerpo=f"""Hay un nuevo post generado a partir de un vídeo de YouTube, pendiente de tu aprobación.

Vídeo: {video_titulo}
Canal: {canal}

Título propuesto: {post_titulo}
Resumen: {resumen}

Revísalo y publícalo (o recházalo) aquí:
{BASE_URL}/admin/video/{video_db_id}

— Sistema de posts automáticos de megasolucion.es""",
    )


def notificar_publicado(post_titulo: str, slug: str) -> None:
    send_email(
        asunto=f'[Megasoluciones] Post publicado: {post_titulo}',
        cuerpo=f"""El post se ha publicado correctamente.

Título: {post_titulo}
URL pública: {BASE_URL}/recursos/{slug}

— Sistema de posts automáticos de megasolucion.es""",
    )


def notificar_error(video_titulo: str, motivo: str, video_db_id: int) -> None:
    send_email(
        asunto=f'[Megasoluciones] Error procesando vídeo: {video_titulo}',
        cuerpo=f"""No se pudo generar el post para el vídeo "{video_titulo}".

Motivo: {motivo}

Puedes revisarlo en el panel:
{BASE_URL}/admin/video/{video_db_id}

— Sistema de posts automáticos de megasolucion.es""",
    )

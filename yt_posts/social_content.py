"""Generación de textos e imágenes para Twitter/X e Instagram a partir de posts de vídeo."""
from __future__ import annotations

import io
import json
import os
import textwrap
from pathlib import Path

import requests

from . import social_queue
from .generator import load_openai_key

STATIC_SOCIAL_DIR = Path(__file__).resolve().parent.parent / 'static' / 'images' / 'social'
LOGO_PATH = Path(__file__).resolve().parent.parent / 'static' / 'images' / 'logo-icon-brain-gear-256.png'

TWITTER_MAX = 280
SITE_BASE = social_queue.SITE_BASE


def article_url(slug: str) -> str:
    return f'{SITE_BASE}/recursos/{slug}'


def _youtube_thumb_urls(youtube_video_id: str) -> list[str]:
    vid = youtube_video_id.strip()
    return [
        f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg',
        f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg',
        f'https://i.ytimg.com/vi/{vid}/sddefault.jpg',
    ]


def _download_image(url: str, timeout: int = 20) -> bytes | None:
    try:
        resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'Megasoluciones/1.0'})
        if resp.status_code != 200:
            return None
        data = resp.content
        if len(data) < 8000:
            return None
        return data
    except requests.RequestException:
        return None


def _fetch_youtube_thumbnail(youtube_video_id: str) -> bytes | None:
    for url in _youtube_thumb_urls(youtube_video_id):
        data = _download_image(url)
        if data:
            return data
    return None


def _brand_image(image_bytes: bytes, title: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    target_w, target_h = 1200, 630
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    overlay = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bar_h = 88
    draw.rectangle((0, target_h - bar_h, target_w, target_h), fill=(15, 23, 42, 220))

    title_short = title[:72] + ('…' if len(title) > 72 else '')
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
        font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font

    draw.text((24, target_h - bar_h + 12), title_short, fill=(255, 255, 255), font=font)
    draw.text((24, target_h - bar_h + 48), 'megasolucion.es · IA y automatización', fill=(148, 163, 184), font=font_sm)

    if LOGO_PATH.is_file():
        logo = Image.open(LOGO_PATH).convert('RGBA')
        logo.thumbnail((64, 64), Image.Resampling.LANCZOS)
        overlay.paste(logo, (target_w - 88, target_h - bar_h + 12), logo)

    base = img.convert('RGBA')
    base = Image.alpha_composite(base, overlay)
    out = io.BytesIO()
    base.convert('RGB').save(out, format='JPEG', quality=88, optimize=True)
    return out.getvalue()


def _generate_card_image(title: str, subtitle: str = '') -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    w, h = 1200, 630
    img = Image.new('RGB', (w, h), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    for y in range(h):
        r = int(15 + (37 - 15) * y / h)
        g = int(23 + (99 - 23) * y / h)
        b = int(42 + (235 - 42) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    try:
        font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 42)
        font_sub = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 26)
        font_brand = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_brand = font_title

    if LOGO_PATH.is_file():
        logo = Image.open(LOGO_PATH).convert('RGBA')
        logo.thumbnail((120, 120), Image.Resampling.LANCZOS)
        img.paste(logo, (60, 60), logo)

    draw.text((60, 200), 'Nuevo en el blog', fill=(96, 165, 250), font=font_sub)

    lines = textwrap.wrap(title, width=32)[:3]
    y = 250
    for line in lines:
        draw.text((60, y), line, fill=(248, 250, 252), font=font_title)
        y += 52

    if subtitle:
        sub_lines = textwrap.wrap(subtitle, width=48)[:2]
        y += 8
        for line in sub_lines:
            draw.text((60, y), line, fill=(148, 163, 184), font=font_sub)
            y += 34

    draw.text((60, h - 56), 'megasolucion.es', fill=(59, 130, 246), font=font_brand)

    out = io.BytesIO()
    img.save(out, format='JPEG', quality=88, optimize=True)
    return out.getvalue()


def prepare_image(
    youtube_video_id: str,
    slug: str,
    title: str,
    resumen: str = '',
) -> tuple[str, str]:
    """Devuelve (filename, ruta_absoluta). Tarjeta de marca Megasoluciones (sin miniatura YouTube)."""
    filename = f'{slug}.jpg'
    os.makedirs(social_queue.SOCIAL_IMAGE_DIR, exist_ok=True)
    dest = Path(social_queue.SOCIAL_IMAGE_DIR) / filename

    image_bytes = _generate_card_image(title, resumen)
    dest.write_bytes(image_bytes)

    STATIC_SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    static_dest = STATIC_SOCIAL_DIR / filename
    static_dest.write_bytes(image_bytes)

    print(f'[social] Imagen {filename} (generated)')
    return filename, str(dest)


def _fallback_texts(titulo: str, resumen: str, url: str) -> dict[str, str]:
    hashtags_tw = '#IA #InteligenciaArtificial #Megasoluciones'
    link_line = f'\n\n👉 {url}'
    room = TWITTER_MAX - len(link_line) - len(hashtags_tw) - 2
    headline = titulo if len(titulo) <= room else titulo[: room - 1] + '…'
    twitter = f'{headline}{link_line}\n\n{hashtags_tw}'

    instagram = (
        f'{titulo}\n\n'
        f'{resumen}\n\n'
        f'Artículo completo en el blog 👇\n{url}\n\n'
        f'—\n'
        f'Megasoluciones · Desarrollo software, automatización e IA para empresas\n\n'
        f'#InteligenciaArtificial #IA #Automatización #DesarrolloSoftware '
        f'#Innovación #Tech #Megasoluciones #Empresas #España'
    )

    linkedin = (
        f'{titulo}\n\n'
        f'{resumen}\n\n'
        f'Hemos publicado un resumen en nuestro blog con las ideas clave del vídeo '
        f'y cómo aplicarlas en empresas reales.\n\n'
        f'👉 Lee el artículo completo: {url}\n\n'
        f'Megasoluciones · Agencia de IA, automatización y desarrollo software a medida '
        f'para empresas en España y LATAM.\n\n'
        f'#InteligenciaArtificial #Automatización #DesarrolloSoftware #Innovación #Megasoluciones'
    )
    return {'twitter': twitter.strip(), 'instagram': instagram.strip(), 'linkedin': linkedin.strip()}


def generar_textos_sociales(
    titulo: str,
    resumen: str,
    url: str,
    canal: str = '',
) -> dict[str, str]:
    api_key = load_openai_key()
    if not api_key:
        return _fallback_texts(titulo, resumen, url)

    from openai import OpenAI

    prompt = f"""Genera textos para promocionar este artículo del blog de Megasoluciones en redes sociales.

Título del artículo: {titulo}
Resumen: {resumen}
URL: {url}
Canal de origen (vídeo): {canal or 'YouTube'}

Devuelve JSON con:
- "twitter": tweet en español, máximo 270 caracteres incluyendo la URL {url}, tono profesional, 2-3 hashtags relevantes
- "instagram": caption en español, 400-900 caracteres, párrafos cortos, CTA al artículo con la URL, 8-12 hashtags al final
- "linkedin": post profesional en español, 500-1200 caracteres, tono B2B, párrafos cortos, CTA con la URL, 4-6 hashtags al final

No uses comillas tipográficas raras. La URL debe aparecer literalmente en los tres textos."""

    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
            response_format={'type': 'json_object'},
            temperature=0.5,
            messages=[
                {'role': 'system', 'content': 'Eres community manager de Megasoluciones (agencia IA España).'},
                {'role': 'user', 'content': prompt},
            ],
        )
        datos = json.loads(resp.choices[0].message.content)
        tw = (datos.get('twitter') or '').strip()
        ig = (datos.get('instagram') or '').strip()
        li = (datos.get('linkedin') or '').strip()
        if tw and ig and li:
            if len(tw) > TWITTER_MAX:
                tw = tw[: TWITTER_MAX - 1] + '…'
            return {'twitter': tw, 'instagram': ig, 'linkedin': li}
    except Exception as exc:
        print(f'[social] OpenAI textos: {exc}')

    return _fallback_texts(titulo, resumen, url)


def image_filename_for(slug: str, platform: str, *, custom: bool = False) -> str:
    if custom:
        return f'{slug}-{platform}.jpg'
    return f'{slug}.jpg'


def save_uploaded_image(post_id: str, file_storage) -> str:
    """Guarda imagen subida para un post concreto."""
    post = social_queue.get_post(post_id)
    if not post:
        raise ValueError('Publicación no encontrada')
    if not file_storage or not file_storage.filename:
        raise ValueError('No se recibió ningún archivo')

    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
        raise ValueError('Formato no válido. Usa JPG, PNG o WebP.')

    raw = file_storage.read()
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError('La imagen supera 8 MB.')

    from PIL import Image

    img = Image.open(io.BytesIO(raw))
    if img.mode != 'RGB':
        img = img.convert('RGB')

    slug = post.get('post_slug') or f'post-{post.get("video_db_id", 0)}'
    platform = post.get('platform') or 'social'
    filename = image_filename_for(slug, platform, custom=True)
    os.makedirs(social_queue.SOCIAL_IMAGE_DIR, exist_ok=True)
    dest = Path(social_queue.SOCIAL_IMAGE_DIR) / filename
    img.save(dest, format='JPEG', quality=88, optimize=True)

    STATIC_SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_SOCIAL_DIR / filename).write_bytes(dest.read_bytes())

    social_queue.set_post_image(post_id, filename, custom=True)
    return filename


def regenerate_post_image(post_id: str) -> str:
    """Regenera imagen de tarjeta Megasoluciones para un post."""
    from . import db as yt_db

    post = social_queue.get_post(post_id)
    if not post:
        raise ValueError('Publicación no encontrada')
    video = yt_db.get_video(int(post['video_db_id']))
    if not video:
        raise ValueError('Vídeo no encontrado')

    slug = post.get('post_slug') or video['post_slug']
    titulo = post.get('title') or video['post_titulo'] or video['titulo_video']
    resumen = video['post_resumen'] or ''
    platform = post.get('platform') or 'social'
    filename = image_filename_for(slug, platform, custom=True)

    image_bytes = _generate_card_image(titulo, resumen)

    os.makedirs(social_queue.SOCIAL_IMAGE_DIR, exist_ok=True)
    dest = Path(social_queue.SOCIAL_IMAGE_DIR) / filename
    dest.write_bytes(image_bytes)
    STATIC_SOCIAL_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_SOCIAL_DIR / filename).write_bytes(image_bytes)

    social_queue.set_post_image(post_id, filename, custom=False)
    return filename


def prepare_for_video(video: dict, *, regenerate: bool = False) -> list[dict]:
    """Crea o actualiza borradores Twitter, Instagram y LinkedIn para un vídeo publicado."""
    vid = int(video['id'])
    slug = video.get('post_slug') or ''
    titulo = video.get('post_titulo') or video.get('titulo_video') or 'Artículo'
    resumen = video.get('post_resumen') or ''
    yt_id = video.get('video_id') or ''
    canal = video.get('canal_nombre') or ''
    url = article_url(slug)

    textos = generar_textos_sociales(titulo, resumen, url, canal=canal)

    # Imagen compartida por defecto; no sobrescribir si algún post tiene imagen personalizada
    shared_filename = image_filename_for(slug, 'shared')
    existing_posts = social_queue.get_posts_for_video(vid)
    any_custom = any(p.get('custom_image') for p in existing_posts)
    if not any_custom or regenerate:
        shared_filename, _ = prepare_image(yt_id, slug, titulo, resumen=resumen)
    elif existing_posts:
        shared_filename = existing_posts[0].get('image') or shared_filename

    results = []
    for platform in social_queue.PLATFORMS:
        text = textos.get(platform, '')
        pid = social_queue.post_id(vid, platform)
        existing = social_queue.get_post(pid)
        if existing and existing.get('status') == 'published' and not regenerate:
            results.append(existing)
            continue
        preserve_status = 'draft'
        if existing and existing.get('status') in ('pending', 'failed') and not regenerate:
            preserve_status = existing['status']
        img_file = existing.get('image') if existing and existing.get('custom_image') else shared_filename
        entry = social_queue.new_entry(
            vid,
            platform,
            post_slug=slug,
            title=titulo,
            text=text,
            image_filename=img_file,
            status=preserve_status if existing else 'draft',
        )
        if existing:
            entry['custom_image'] = bool(existing.get('custom_image'))
            entry['scheduled_at'] = existing.get('scheduled_at') or ''
            entry['published_at'] = existing.get('published_at')
            entry['external_id'] = existing.get('external_id')
            entry['error'] = None if regenerate else existing.get('error')
        results.append(social_queue.upsert_post(entry))
    return results


def prepare_all_published(*, regenerate: bool = False) -> int:
    from . import db

    count = 0
    for row in db.list_videos('publicado'):
        video = dict(row)
        if not video.get('post_slug'):
            continue
        prepare_for_video(video, regenerate=regenerate)
        count += 1
    return count

"""Cliente Instagram Graph API — publicar fotos en cuenta Business."""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

GRAPH = 'https://graph.facebook.com/v21.0'


class InstagramError(Exception):
    pass


def _load_secret(name: str) -> str:
    root = Path(__file__).resolve().parent.parent
    key = name.lower().replace('_', '-')
    for fname in (f'instagram-{key}.txt', f'.instagram-{key}'):
        path = root / fname
        if path.is_file():
            val = path.read_text(encoding='utf-8').strip()
            if val and not val.startswith('#'):
                return val
    return os.environ.get(name, '').strip()


def instagram_config() -> dict:
    return {
        'access_token': _load_secret('INSTAGRAM_ACCESS_TOKEN'),
        'user_id': _load_secret('INSTAGRAM_USER_ID'),
    }


def is_configured() -> bool:
    cfg = instagram_config()
    return bool(cfg['access_token'] and cfg['user_id'])


def test_connection() -> dict:
    cfg = instagram_config()
    if not is_configured():
        raise InstagramError('INSTAGRAM_ACCESS_TOKEN o INSTAGRAM_USER_ID no configurados.')
    resp = requests.get(
        f'{GRAPH}/{cfg["user_id"]}',
        params={'fields': 'username,name,profile_picture_url', 'access_token': cfg['access_token']},
        timeout=30,
    )
    if resp.status_code != 200:
        raise InstagramError(f'Conexión fallida ({resp.status_code}): {resp.text[:400]}')
    data = resp.json()
    return {
        'ok': True,
        'username': data.get('username', ''),
        'name': data.get('name', ''),
        'id': data.get('id', cfg['user_id']),
    }


def publish_photo(caption: str, image_url: str) -> str:
    cfg = instagram_config()
    if not is_configured():
        raise InstagramError('Instagram no configurado.')
    if not image_url.startswith('https://'):
        raise InstagramError('Instagram requiere image_url pública HTTPS.')

    create = requests.post(
        f'{GRAPH}/{cfg["user_id"]}/media',
        data={
            'image_url': image_url,
            'caption': caption.strip(),
            'access_token': cfg['access_token'],
        },
        timeout=60,
    )
    if create.status_code != 200:
        raise InstagramError(f'Error creando media ({create.status_code}): {create.text[:500]}')
    creation_id = create.json().get('id')
    if not creation_id:
        raise InstagramError('Instagram no devolvió creation_id.')

    for _ in range(12):
        time.sleep(3)
        pub = requests.post(
            f'{GRAPH}/{cfg["user_id"]}/media_publish',
            data={'creation_id': creation_id, 'access_token': cfg['access_token']},
            timeout=60,
        )
        if pub.status_code == 200:
            media_id = pub.json().get('id', creation_id)
            return str(media_id)
        err = pub.json().get('error', {})
        if err.get('error_subcode') != 2207027:
            raise InstagramError(f'Error publicando ({pub.status_code}): {pub.text[:500]}')

    raise InstagramError('Instagram no terminó de procesar la imagen a tiempo.')


def publish_photo_file(caption: str, image_path: Path, public_url: str) -> str:
    """Publica usando URL pública (debe estar accesible en megasolucion.es)."""
    if not public_url:
        raise InstagramError('Falta URL pública de la imagen para Instagram.')
    return publish_photo(caption, public_url)

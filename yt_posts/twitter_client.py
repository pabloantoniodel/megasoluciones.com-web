"""Cliente Twitter/X API v2 — publicar tweets con imagen."""
from __future__ import annotations

import os
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

UPLOAD_URL = 'https://upload.twitter.com/1.1/media/upload.json'
TWEETS_URL = 'https://api.twitter.com/2/tweets'


class TwitterError(Exception):
    pass


def _load_secret(name: str) -> str:
    root = Path(__file__).resolve().parent.parent
    key = name.lower().replace('_', '-')
    for fname in (f'twitter-{key}.txt', f'x-{key}.txt', f'.twitter-{key}'):
        path = root / fname
        if path.is_file():
            val = path.read_text(encoding='utf-8').strip()
            if val and not val.startswith('#'):
                return val
    return os.environ.get(name, '').strip()


def twitter_config() -> dict:
    return {
        'api_key': _load_secret('TWITTER_API_KEY') or _load_secret('X_API_KEY'),
        'api_secret': _load_secret('TWITTER_API_SECRET') or _load_secret('X_API_SECRET'),
        'access_token': _load_secret('TWITTER_ACCESS_TOKEN') or _load_secret('X_ACCESS_TOKEN'),
        'access_token_secret': _load_secret('TWITTER_ACCESS_TOKEN_SECRET') or _load_secret('X_ACCESS_TOKEN_SECRET'),
    }


def is_configured() -> bool:
    cfg = twitter_config()
    return all(cfg.values())


def _oauth() -> OAuth1:
    cfg = twitter_config()
    if not is_configured():
        raise TwitterError('Faltan claves Twitter/X (API key, secret, access token y secret).')
    return OAuth1(
        cfg['api_key'],
        client_secret=cfg['api_secret'],
        resource_owner_key=cfg['access_token'],
        resource_owner_secret=cfg['access_token_secret'],
    )


def test_connection() -> dict:
    auth = _oauth()
    resp = requests.get(
        'https://api.twitter.com/2/users/me',
        auth=auth,
        params={'user.fields': 'username,name'},
        timeout=30,
    )
    if resp.status_code != 200:
        raise TwitterError(f'Conexión fallida ({resp.status_code}): {resp.text[:400]}')
    data = resp.json().get('data') or {}
    return {
        'ok': True,
        'username': data.get('username', ''),
        'name': data.get('name', ''),
        'id': data.get('id', ''),
    }


def upload_media(image_path: Path) -> str:
    auth = _oauth()
    with open(image_path, 'rb') as fh:
        resp = requests.post(
            UPLOAD_URL,
            auth=auth,
            files={'media': fh},
            timeout=120,
        )
    if resp.status_code != 200:
        raise TwitterError(f'Error subiendo imagen ({resp.status_code}): {resp.text[:400]}')
    media_id = resp.json().get('media_id_string')
    if not media_id:
        raise TwitterError('Twitter no devolvió media_id.')
    return str(media_id)


def publish_tweet(text: str, image_path: Path | None = None) -> str:
    auth = _oauth()
    payload: dict = {'text': text.strip()}
    if image_path and image_path.is_file():
        media_id = upload_media(image_path)
        payload['media'] = {'media_ids': [media_id]}

    resp = requests.post(TWEETS_URL, auth=auth, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise TwitterError(f'Error publicando tweet ({resp.status_code}): {resp.text[:500]}')
    tweet_id = (resp.json().get('data') or {}).get('id', '')
    return tweet_id or 'published'

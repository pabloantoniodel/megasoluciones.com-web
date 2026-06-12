"""Cliente LinkedIn Community Management API — publicar en página de empresa."""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

API_BASE = 'https://api.linkedin.com'
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'


class LinkedInError(Exception):
    pass


def _load_secret(name: str) -> str:
    root = Path(__file__).resolve().parent.parent
    for fname in (f'linkedin-{name.lower().replace("_", "-")}.txt', f'.linkedin-{name.lower()}'):
        path = root / fname
        if path.is_file():
            val = path.read_text(encoding='utf-8').strip()
            if val and not val.startswith('#'):
                return val
    return os.environ.get(name, '').strip()


def linkedin_config() -> dict:
    return {
        'client_id': _load_secret('LINKEDIN_CLIENT_ID'),
        'client_secret': _load_secret('LINKEDIN_CLIENT_SECRET'),
        'access_token': _load_secret('LINKEDIN_ACCESS_TOKEN'),
        'refresh_token': _load_secret('LINKEDIN_REFRESH_TOKEN'),
        'org_id': _load_secret('LINKEDIN_ORG_ID'),
        'api_version': os.environ.get('LINKEDIN_API_VERSION', '202501').strip() or '202501',
    }


def is_configured() -> bool:
    cfg = linkedin_config()
    return bool(cfg['access_token'] and cfg['org_id'])


def _headers(token: str, api_version: str) -> dict:
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Linkedin-Version': api_version,
        'X-Restli-Protocol-Version': '2.0.0',
    }


def refresh_access_token() -> str:
    cfg = linkedin_config()
    if not all([cfg['client_id'], cfg['client_secret'], cfg['refresh_token']]):
        raise LinkedInError('Faltan LINKEDIN_CLIENT_ID, CLIENT_SECRET o REFRESH_TOKEN para renovar el token.')
    resp = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': cfg['refresh_token'],
            'client_id': cfg['client_id'],
            'client_secret': cfg['client_secret'],
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise LinkedInError(f'Error renovando token ({resp.status_code}): {resp.text[:400]}')
    data = resp.json()
    token = data.get('access_token', '')
    if not token:
        raise LinkedInError('LinkedIn no devolvió access_token al renovar.')
    os.environ['LINKEDIN_ACCESS_TOKEN'] = token
    new_refresh = data.get('refresh_token')
    if new_refresh:
        os.environ['LINKEDIN_REFRESH_TOKEN'] = new_refresh
    return token


def _token() -> str:
    cfg = linkedin_config()
    if not cfg['access_token']:
        raise LinkedInError('LINKEDIN_ACCESS_TOKEN no configurado.')
    return cfg['access_token']


def org_urn(org_id: str | None = None) -> str:
    oid = (org_id or linkedin_config()['org_id']).strip()
    if not oid:
        raise LinkedInError('LINKEDIN_ORG_ID no configurado.')
    if oid.startswith('urn:li:organization:'):
        return oid
    return f'urn:li:organization:{oid}'


def test_connection() -> dict:
    cfg = linkedin_config()
    token = _token()
    urn = org_urn()
    resp = requests.get(
        f'{API_BASE}/rest/organizations/{cfg["org_id"]}',
        headers=_headers(token, cfg['api_version']),
        timeout=30,
    )
    if resp.status_code == 401 and cfg['refresh_token']:
        token = refresh_access_token()
        resp = requests.get(
            f'{API_BASE}/rest/organizations/{cfg["org_id"]}',
            headers=_headers(token, cfg['api_version']),
            timeout=30,
        )
    if resp.status_code != 200:
        raise LinkedInError(f'Conexión fallida ({resp.status_code}): {resp.text[:500]}')
    data = resp.json()
    return {
        'ok': True,
        'org_urn': urn,
        'name': data.get('localizedName') or data.get('name', ''),
        'vanity_name': data.get('vanityName', ''),
    }


def upload_image(image_path: Path, org_id: str | None = None) -> str:
    cfg = linkedin_config()
    token = _token()
    owner = org_urn(org_id)
    headers = _headers(token, cfg['api_version'])

    init_resp = requests.post(
        f'{API_BASE}/rest/images?action=initializeUpload',
        headers=headers,
        json={'initializeUploadRequest': {'owner': owner}},
        timeout=30,
    )
    if init_resp.status_code == 401 and cfg['refresh_token']:
        token = refresh_access_token()
        headers = _headers(token, cfg['api_version'])
        init_resp = requests.post(
            f'{API_BASE}/rest/images?action=initializeUpload',
            headers=headers,
            json={'initializeUploadRequest': {'owner': owner}},
            timeout=30,
        )
    if init_resp.status_code not in (200, 201):
        raise LinkedInError(f'Error subiendo imagen — init ({init_resp.status_code}): {init_resp.text[:400]}')

    value = init_resp.json().get('value') or {}
    upload_url = value.get('uploadUrl')
    image_urn = value.get('image')
    if not upload_url or not image_urn:
        raise LinkedInError('LinkedIn no devolvió uploadUrl o image URN.')

    binary = image_path.read_bytes()
    put_resp = requests.put(
        upload_url,
        data=binary,
        headers={'Content-Type': 'application/octet-stream'},
        timeout=120,
    )
    if put_resp.status_code not in (200, 201):
        raise LinkedInError(f'Error subiendo binario ({put_resp.status_code}): {put_resp.text[:300]}')

    # Breve espera para que LinkedIn procese la imagen
    time.sleep(2)
    return image_urn


def publish_post(text: str, image_path: Path | None = None, org_id: str | None = None) -> str:
    cfg = linkedin_config()
    token = _token()
    headers = _headers(token, cfg['api_version'])
    author = org_urn(org_id)

    payload: dict = {
        'author': author,
        'commentary': text.strip(),
        'visibility': 'PUBLIC',
        'distribution': {
            'feedDistribution': 'MAIN_FEED',
            'targetEntities': [],
            'thirdPartyDistributionChannels': [],
        },
        'lifecycleState': 'PUBLISHED',
    }

    if image_path and image_path.is_file():
        image_urn = upload_image(image_path, org_id=org_id)
        payload['content'] = {'media': {'id': image_urn}}

    resp = requests.post(f'{API_BASE}/rest/posts', headers=headers, json=payload, timeout=60)
    if resp.status_code == 401 and cfg['refresh_token']:
        token = refresh_access_token()
        headers = _headers(token, cfg['api_version'])
        resp = requests.post(f'{API_BASE}/rest/posts', headers=headers, json=payload, timeout=60)

    if resp.status_code not in (200, 201):
        raise LinkedInError(f'Error publicando ({resp.status_code}): {resp.text[:600]}')

    post_urn = resp.headers.get('x-restli-id') or resp.headers.get('X-RestLi-Id') or ''
    if not post_urn and resp.text:
        try:
            post_urn = resp.json().get('id', '')
        except Exception:
            post_urn = ''
    return post_urn or 'published'

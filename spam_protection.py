"""Protección anti-spam para el formulario de contacto (honeypot, Turnstile, Akismet, rate limit)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from time import time

MIN_FORM_SECONDS = 3
MAX_SUBMISSIONS_PER_HOUR = 5
HONEYPOT_FIELD = 'middle_name_hp'

_rate_limit: dict[str, list[float]] = defaultdict(list)


def _read_key_file(*names: str) -> str | None:
    base = os.path.dirname(__file__)
    for name in names:
        path = os.path.join(base, name)
        if os.path.isfile(path):
            value = open(path, encoding='utf-8').read().strip()
            if value and not value.startswith('#'):
                return value
    return None


def load_turnstile_site_key() -> str | None:
    return _read_key_file('turnstile-site-key.txt', '.turnstile-site-key') or os.environ.get(
        'TURNSTILE_SITE_KEY', ''
    ).strip() or None


def load_turnstile_secret_key() -> str | None:
    return _read_key_file('turnstile-secret-key.txt', '.turnstile-secret-key') or os.environ.get(
        'TURNSTILE_SECRET_KEY', ''
    ).strip() or None


def load_akismet_api_key() -> str | None:
    return _read_key_file('akismet-key.txt', '.akismet-key') or os.environ.get(
        'AKISMET_API_KEY', ''
    ).strip() or None


def get_client_ip(forwarded_for: str | None, remote_addr: str | None) -> str:
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return remote_addr or '0.0.0.0'


def honeypot_triggered(honeypot_value: str | None) -> bool:
    return bool(honeypot_value and honeypot_value.strip())


def form_submitted_too_fast(form_loaded_at: float | None) -> bool:
    if form_loaded_at is None:
        return False
    return (time() - form_loaded_at) < MIN_FORM_SECONDS


def spam_block_reason(
    honeypot_value: str | None,
    form_loaded_at: float | None,
    client_ip: str,
    *,
    akismet_spam: bool | None,
) -> str | None:
    if honeypot_triggered(honeypot_value):
        return 'honeypot'
    if form_submitted_too_fast(form_loaded_at):
        return 'too_fast'
    if is_rate_limited(client_ip):
        return 'rate_limit'
    if akismet_spam is True:
        return 'akismet'
    return None


def should_silently_drop(
    honeypot_value: str | None,
    form_loaded_at: float | None,
    client_ip: str,
    *,
    akismet_spam: bool | None,
) -> bool:
    return spam_block_reason(
        honeypot_value, form_loaded_at, client_ip, akismet_spam=akismet_spam
    ) is not None


def is_rate_limited(client_ip: str) -> bool:
    now = time()
    window_start = now - 3600
    hits = [t for t in _rate_limit[client_ip] if t > window_start]
    _rate_limit[client_ip] = hits
    return len(hits) >= MAX_SUBMISSIONS_PER_HOUR


def record_submission(client_ip: str) -> None:
    _rate_limit[client_ip].append(time())


def verify_turnstile(token: str | None, client_ip: str, secret_key: str | None) -> bool | None:
    """True si válido, False si inválido, None si Turnstile no está configurado."""
    if not secret_key:
        return None
    if not token:
        return False
    payload = urllib.parse.urlencode({
        'secret': secret_key,
        'response': token,
        'remoteip': client_ip,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data=payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return bool(data.get('success'))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False


def check_akismet_spam(
    api_key: str | None,
    *,
    blog_url: str,
    client_ip: str,
    user_agent: str,
    author: str,
    email: str,
    content: str,
) -> bool | None:
    """True si Akismet marca spam, False si ham, None si Akismet no configurado."""
    if not api_key:
        return None
    payload = urllib.parse.urlencode({
        'blog': blog_url,
        'user_ip': client_ip,
        'user_agent': user_agent or '',
        'comment_type': 'contact-form',
        'comment_author': author,
        'comment_author_email': email,
        'comment_content': content,
    }).encode('utf-8')
    url = f'https://{api_key}.rest.akismet.com/1.1/comment-check'
    req = urllib.request.Request(
        url,
        data=payload,
        method='POST',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Megasoluciones-ContactForm/1.0 | Akismet/3.0',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = resp.read().decode('utf-8').strip().lower()
            return result == 'true'
    except (urllib.error.URLError, TimeoutError):
        return False

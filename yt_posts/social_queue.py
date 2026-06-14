"""Cola de publicaciones en redes (Twitter/X e Instagram) ligadas a posts de vídeo."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
QUEUE_FILE = os.path.join(DATA_DIR, 'social_queue.json')
SOCIAL_IMAGE_DIR = os.path.join(DATA_DIR, 'social')
SITE_BASE = os.environ.get('SITE_BASE_URL', 'https://megasolucion.es').rstrip('/')

PLATFORMS = ('twitter', 'instagram', 'linkedin')


def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SOCIAL_IMAGE_DIR, exist_ok=True)


def _ensure_file() -> None:
    _ensure_dirs()
    if not os.path.isfile(QUEUE_FILE):
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_queue() -> list[dict]:
    _ensure_file()
    with open(QUEUE_FILE, encoding='utf-8') as f:
        return json.load(f)


def save_queue(items: list[dict]) -> None:
    _ensure_dirs()
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def post_id(video_db_id: int, platform: str) -> str:
    return f'v{video_db_id}-{platform}'


def get_post(item_id: str) -> dict | None:
    for item in load_queue():
        if item['id'] == item_id:
            return item
    return None


def get_posts_for_video(video_db_id: int) -> list[dict]:
    prefix = f'v{video_db_id}-'
    return [p for p in load_queue() if p['id'].startswith(prefix)]


def update_post(item_id: str, **fields) -> dict | None:
    items = load_queue()
    for item in items:
        if item['id'] == item_id:
            item.update(fields)
            save_queue(items)
            return item
    return None


def upsert_post(entry: dict) -> dict:
    items = load_queue()
    for i, item in enumerate(items):
        if item['id'] == entry['id']:
            merged = {**item, **entry}
            items[i] = merged
            save_queue(items)
            return merged
    items.append(entry)
    save_queue(items)
    return entry


def new_entry(
    video_db_id: int,
    platform: str,
    *,
    post_slug: str,
    title: str,
    text: str,
    image_filename: str = '',
    status: str = 'draft',
) -> dict:
    image_url = ''
    if image_filename:
        image_url = f'{SITE_BASE}/media/social/{image_filename}'
    return {
        'id': post_id(video_db_id, platform),
        'video_db_id': video_db_id,
        'post_slug': post_slug,
        'platform': platform,
        'title': title,
        'text': text,
        'image': image_filename,
        'image_url': image_url,
        'custom_image': False,
        'status': status,
        'scheduled_at': '',
        'published_at': None,
        'external_id': None,
        'error': None,
    }


def resolve_image_path(filename: str) -> Path | None:
    if not filename:
        return None
    name = os.path.basename(filename)
    static_dir = Path(__file__).resolve().parent.parent / 'static' / 'images' / 'social'
    for base in (Path(SOCIAL_IMAGE_DIR), static_dir):
        path = base / name
        if path.is_file():
            return path
    return None


def set_post_image(item_id: str, filename: str, *, custom: bool = True) -> dict | None:
    return update_post(
        item_id,
        image=os.path.basename(filename),
        image_url=public_image_url(filename),
        custom_image=custom,
        error=None,
    )


def public_image_url(filename: str) -> str:
    if not filename:
        return ''
    return f'{SITE_BASE}/media/social/{os.path.basename(filename)}'


def due_posts(now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    due = []
    for item in load_queue():
        if item.get('status') != 'pending':
            continue
        sched = (item.get('scheduled_at') or '').strip()
        if not sched:
            continue
        try:
            when = datetime.fromisoformat(sched.replace('Z', '+00:00'))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if when <= now:
            due.append(item)
    return due


def video_dict(row) -> dict:
    """Convierte sqlite3.Row de vídeo a dict."""
    return dict(row) if row is not None else {}

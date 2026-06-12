"""Worker LinkedIn: publica posts programados cuando llega scheduled_at."""
from __future__ import annotations

import os
import time
import traceback
from datetime import datetime, timezone

from . import linkedin_client, linkedin_queue

INTERVAL_MIN = int(os.environ.get('LINKEDIN_WORKER_INTERVAL_MIN', 15))


def publish_one(post: dict) -> bool:
    image_path = linkedin_queue.resolve_image_path(post.get('image') or '')
    try:
        urn = linkedin_client.publish_post(post['text'], image_path=image_path)
        linkedin_queue.update_post(
            post['id'],
            status='published',
            published_at=datetime.now(timezone.utc).isoformat(),
            linkedin_post_urn=urn,
            error=None,
        )
        print(f'[linkedin] Publicado: {post["id"]} → {urn}')
        return True
    except Exception as exc:
        linkedin_queue.update_post(post['id'], status='failed', error=str(exc)[:500])
        print(f'[linkedin] Error en {post["id"]}: {exc}')
        traceback.print_exc()
        return False


def run_due() -> dict:
    if not linkedin_client.is_configured():
        return {'skipped': True, 'reason': 'LinkedIn no configurado'}
    due = linkedin_queue.due_posts()
    ok = err = 0
    for post in due:
        if publish_one(post):
            ok += 1
        else:
            err += 1
    return {'due': len(due), 'published': ok, 'failed': err}


def main() -> None:
    print(f'[linkedin] Worker iniciado. Intervalo: {INTERVAL_MIN} min')
    while True:
        try:
            result = run_due()
            if not result.get('skipped'):
                print(f'[linkedin] Ciclo: {result}')
        except Exception:
            print('[linkedin] Error en ciclo:')
            traceback.print_exc()
        time.sleep(INTERVAL_MIN * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == '--test':
            info = linkedin_client.test_connection()
            print('OK:', info)
        elif cmd == '--run-due':
            print(run_due())
        elif cmd == '--publish' and len(sys.argv) > 2:
            post = linkedin_queue.get_post(sys.argv[2])
            if not post:
                print('Post no encontrado')
                sys.exit(1)
            ok = publish_one(post)
            sys.exit(0 if ok else 1)
        else:
            print('Uso: python -m yt_posts.linkedin_worker [--test|--run-due|--publish POST_ID]')
            sys.exit(1)
    else:
        main()

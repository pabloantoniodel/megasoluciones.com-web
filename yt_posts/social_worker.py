"""Worker y publicación de posts sociales (Twitter/X e Instagram)."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from . import instagram_client, linkedin_client, social_queue, twitter_client

INTERVAL_MIN = int(os.environ.get('SOCIAL_WORKER_INTERVAL_MIN', '15'))


def publish_one(post: dict) -> bool:
    platform = post.get('platform', '')
    image_path = social_queue.resolve_image_path(post.get('image') or '')
    image_url = post.get('image_url') or social_queue.public_image_url(post.get('image') or '')

    try:
        if platform == 'twitter':
            if not twitter_client.is_configured():
                raise RuntimeError('Twitter/X no configurado.')
            ext_id = twitter_client.publish_tweet(post['text'], image_path=image_path)
        elif platform == 'instagram':
            if not instagram_client.is_configured():
                raise RuntimeError('Instagram no configurado.')
            ext_id = instagram_client.publish_photo_file(
                post['text'], image_path or social_queue.resolve_image_path(''), image_url,
            )
        elif platform == 'linkedin':
            if not linkedin_client.is_configured():
                raise RuntimeError('LinkedIn no configurado.')
            ext_id = linkedin_client.publish_post(post['text'], image_path=image_path)
        else:
            raise RuntimeError(f'Plataforma desconocida: {platform}')

        social_queue.update_post(
            post['id'],
            status='published',
            published_at=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            external_id=ext_id,
            error=None,
        )
        print(f'[social] Publicado {post["id"]} → {ext_id}')
        return True
    except Exception as exc:
        social_queue.update_post(post['id'], status='failed', error=str(exc)[:500])
        print(f'[social] Error {post["id"]}: {exc}')
        return False


def run_due() -> dict:
    due = social_queue.due_posts()
    ok = fail = 0
    for post in due:
        if publish_one(post):
            ok += 1
        else:
            fail += 1
    return {'due': len(due), 'ok': ok, 'fail': fail}


def publish_by_id(post_id: str) -> bool:
    post = social_queue.get_post(post_id)
    if not post:
        return False
    return publish_one(post)


def run_loop() -> None:
    print(f'[social] Worker iniciado. Intervalo: {INTERVAL_MIN} min')
    while True:
        try:
            result = run_due()
            if result['due']:
                print(f'[social] Ciclo: {result}')
        except Exception:
            print('[social] Error en ciclo:')
            import traceback
            traceback.print_exc()
        time.sleep(max(INTERVAL_MIN, 1) * 60)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == '--test-twitter':
            print(twitter_client.test_connection())
        elif cmd == '--test-instagram':
            print(instagram_client.test_connection())
        elif cmd == '--test-linkedin':
            print(linkedin_client.test_connection())
        elif cmd == '--run-due':
            print(run_due())
        elif cmd == '--publish' and len(sys.argv) > 2:
            ok = publish_by_id(sys.argv[2])
            post = social_queue.get_post(sys.argv[2])
            print('OK' if ok else f'FAIL: {post.get("error") if post else "?"}')
        elif cmd == '--prepare-published':
            from . import social_content
            n = social_content.prepare_all_published(regenerate='--force' in sys.argv)
            print(f'Preparados {n} vídeos')
        else:
            print('Uso: python -m yt_posts.social_worker [--test-twitter|--test-instagram|--run-due|--publish ID|--prepare-published]')
    else:
        run_loop()

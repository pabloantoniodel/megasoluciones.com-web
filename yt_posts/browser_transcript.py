"""Transcripción vía navegador real (Playwright/Chromium headless).

YouTube bloquea las peticiones de la API de transcripciones desde IPs de
datacenter, pero la página web normal sí carga. Este módulo abre el vídeo
como lo haría una persona, pulsa «Mostrar transcripción» y lee el panel.
"""
import re

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')

# Markup nuevo (2025+) y antiguo del panel de transcripción
JS_EXTRAER_SEGMENTOS = """
() => {
    const out = [];
    const hosts = document.querySelectorAll('.ytwTranscriptSegmentViewModelHost');
    if (hosts.length) {
        for (const h of hosts) {
            const clone = h.cloneNode(true);
            clone.querySelectorAll('[class*="Timestamp"], [class*="A11y"]').forEach(e => e.remove());
            const t = clone.textContent.replace(/\\s+/g, ' ').trim();
            if (t) out.push(t);
        }
        return out;
    }
    for (const el of document.querySelectorAll('ytd-transcript-segment-renderer .segment-text')) {
        const t = el.textContent.replace(/\\s+/g, ' ').trim();
        if (t) out.push(t);
    }
    return out;
}
"""


def fetch_transcript_browser(video_id: str, timeout_s: int = 90) -> str:
    """Devuelve la transcripción del vídeo abriéndolo en un navegador headless."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            ctx = browser.new_context(
                user_agent=UA,
                locale='es-ES',
                viewport={'width': 1280, 'height': 900},
            )
            page = ctx.new_page()
            page.set_default_timeout(timeout_s * 1000)
            page.goto(
                f'https://www.youtube.com/watch?v={video_id}',
                wait_until='domcontentloaded',
                timeout=60000,
            )
            page.wait_for_timeout(5000)

            # Consentimiento de cookies (solo aparece en algunas regiones)
            for sel in ('button[aria-label*="Aceptar"]', 'button[aria-label*="Accept"]'):
                try:
                    page.click(sel, timeout=2000)
                    page.wait_for_timeout(2000)
                    break
                except Exception:
                    pass

            # Expandir la descripción para que aparezca «Mostrar transcripción»
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(1500)
            try:
                page.click('#description-inline-expander tp-yt-paper-button#expand', timeout=5000)
                page.wait_for_timeout(2000)
            except Exception:
                pass

            try:
                page.click('ytd-video-description-transcript-section-renderer button', timeout=8000)
            except Exception:
                raise RuntimeError('El vídeo no tiene botón de transcripción (sin subtítulos)')

            # Esperar a que el panel cargue los segmentos
            segmentos = []
            for _ in range(15):
                page.wait_for_timeout(2000)
                segmentos = page.evaluate(JS_EXTRAER_SEGMENTOS)
                if len(segmentos) > 3:
                    break
            if not segmentos:
                raise RuntimeError('El panel de transcripción no cargó ningún segmento')

            texto = ' '.join(segmentos)
            # Quitar cabeceras de capítulos repetidas tipo "Capítulo 1: ..."
            texto = re.sub(r'\s+', ' ', texto).strip()
            return texto
        finally:
            browser.close()

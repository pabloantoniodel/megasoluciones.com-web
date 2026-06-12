"""Worker de ingesta: ejecutar con `python -m yt_posts.worker`.

Bucle infinito que cada INTERVALO_MIN minutos:
1. Lee el RSS de los canales activos y registra vídeos nuevos.
2. Transcribe y redacta los pendientes (borrador + email de aviso).
3. Purga visitas de más de 90 días.
"""
import os
import time
import traceback

from .pipeline import ciclo_completo

INTERVALO_MIN = int(os.environ.get('YT_WORKER_INTERVAL_MIN', 30))


def main() -> None:
    print(f'[worker] Iniciado. Intervalo: {INTERVALO_MIN} min')
    while True:
        try:
            resultado = ciclo_completo()
            print(f'[worker] Ciclo completado: {resultado}')
        except Exception:
            print('[worker] Error en el ciclo:')
            traceback.print_exc()
        time.sleep(INTERVALO_MIN * 60)


if __name__ == '__main__':
    main()

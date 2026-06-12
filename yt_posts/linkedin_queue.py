"""Cola de publicaciones LinkedIn (JSON en DATA_DIR)."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
QUEUE_FILE = os.path.join(DATA_DIR, 'linkedin_queue.json')

DEFAULT_QUEUE = [
    {
        'id': 'post-01-presentacion',
        'title': 'Presentación — Agencia IA Madrid',
        'scheduled_at': '',
        'text': (
            '¿Tu empresa sigue perdiendo horas en tareas que una máquina podría hacer?\n\n'
            'En Megasoluciones ayudamos a empresas y pymes en España y LATAM a integrar '
            'inteligencia artificial de forma práctica: ingeniería que llega a producción.\n\n'
            '👉 Chatbots y asistentes con IA\n'
            '👉 Automatización de procesos (RPA)\n'
            '👉 Desarrollo de software a medida\n'
            '👉 Integraciones entre sistemas\n\n'
            'Primera consulta sin compromiso · Respuesta en menos de 24 h\n\n'
            'https://megasolucion.es\n\n'
            '#InteligenciaArtificial #Automatización #DesarrolloSoftware #Megasoluciones'
        ),
        'image': 'static/images/linkedin/post-01-presentacion.png',
        'status': 'pending',
        'published_at': None,
        'linkedin_post_urn': None,
        'error': None,
    },
    {
        'id': 'post-02-automatizacion',
        'title': 'Automatización de procesos',
        'scheduled_at': '',
        'text': (
            'Copiar datos entre Excel, CRM y ERP. Revisar facturas a mano. Enviar los mismos emails una y otra vez.\n\n'
            'Si esto suena familiar, no necesitas más personas: necesitas automatizar.\n\n'
            'En Megasoluciones diseñamos workflows y automatizaciones empresariales (RPA) que:\n\n'
            '✅ Eliminan tareas repetitivas\n'
            '✅ Reducen errores humanos\n'
            '✅ Conectan sistemas que no se hablan entre sí\n'
            '✅ Liberan a tu equipo para trabajo de valor\n\n'
            'Empezamos con un piloto pequeño, medimos resultados y escalamos solo si tiene sentido.\n\n'
            'https://megasolucion.es/automatizaciones\n\n'
            '#RPA #AutomatizaciónDeProcesos #IA #Megasoluciones'
        ),
        'image': 'static/images/linkedin/post-02-automatizacion.png',
        'status': 'pending',
        'published_at': None,
        'linkedin_post_urn': None,
        'error': None,
    },
    {
        'id': 'post-03-servicios',
        'title': 'Cómo trabajamos — 3 fases',
        'scheduled_at': '',
        'text': (
            'La IA no es magia. Es saber dónde aplicarla.\n\n'
            'Nuestro método en 3 fases:\n\n'
            '🔍 Diagnóstico — qué procesos merecen IA primero\n'
            '🚀 Implementación — chatbots, automatizaciones y software a medida\n'
            '🔄 Evolución — mantenimiento y mejoras continuas\n\n'
            'Desde 2015, más de 150 proyectos en España y Latinoamérica.\n\n'
            'Servicios: https://megasolucion.es/servicios\n'
            'Contacto: https://megasolucion.es/contacto\n\n'
            '#IAparaEmpresas #SoftwareAMedida #Megasoluciones'
        ),
        'image': 'static/images/linkedin/post-03-servicios.png',
        'status': 'pending',
        'published_at': None,
        'linkedin_post_urn': None,
        'error': None,
    },
]


def _ensure_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.isfile(QUEUE_FILE):
        save_queue(list(DEFAULT_QUEUE))


def load_queue() -> list[dict]:
    _ensure_file()
    with open(QUEUE_FILE, encoding='utf-8') as f:
        return json.load(f)


def save_queue(items: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def get_post(post_id: str) -> dict | None:
    for item in load_queue():
        if item['id'] == post_id:
            return item
    return None


def update_post(post_id: str, **fields) -> dict | None:
    items = load_queue()
    for item in items:
        if item['id'] == post_id:
            item.update(fields)
            save_queue(items)
            return item
    return None


def add_post(title: str, text: str, image: str = '', scheduled_at: str = '') -> dict:
    items = load_queue()
    post = {
        'id': str(uuid.uuid4())[:8],
        'title': title,
        'scheduled_at': scheduled_at,
        'text': text,
        'image': image,
        'status': 'pending',
        'published_at': None,
        'linkedin_post_urn': None,
        'error': None,
    }
    items.append(post)
    save_queue(items)
    return post


def resolve_image_path(rel_path: str) -> Path | None:
    if not rel_path:
        return None
    root = Path(__file__).resolve().parent.parent
    path = root / rel_path
    return path if path.is_file() else None


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

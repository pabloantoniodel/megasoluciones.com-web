"""Redacción del post a partir de la transcripción usando la API de OpenAI."""
import json
import os

OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
MAX_TRANSCRIPT_CHARS = 48000

PROMPT_SISTEMA = """Eres redactor profesional del blog de Megasoluciones (megasolucion.es), una agencia
española de inteligencia artificial, automatizaciones y desarrollo de software a medida.
Tono: profesional, claro, directo, orientado a negocio, sin humo ni claims falsos.
Escribes siempre en español de España."""

PROMPT_USUARIO = """A partir de la transcripción de este vídeo de YouTube, redacta un artículo para el blog.

Título del vídeo: {titulo}
Canal: {canal}
URL: {url}

TRANSCRIPCIÓN:
{transcripcion}

INSTRUCCIONES:
- Redacta un artículo original que resuma y desarrolle las ideas clave del vídeo (no una transcripción literal).
- Estructura: introducción breve, secciones con subtítulos <h2>/<h3>, y una conclusión.
- Usa listas <ul>/<li> donde aporten claridad.
- Menciona expresamente que el contenido procede del vídeo y cita el canal.
- Extensión: 600-1000 palabras.
- No inventes datos que no estén en la transcripción.

Devuelve SOLO un JSON válido con estas claves:
{{
  "titulo": "título SEO del artículo (máx 65 caracteres)",
  "resumen": "metadescripción de 140-160 caracteres",
  "cuerpo_html": "el artículo en HTML usando solo <h2>, <h3>, <p>, <ul>, <li>, <strong>"
}}"""


def load_openai_key() -> str | None:
    for name in ('openai-key.txt', '.openai-key'):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), name)
        if os.path.isfile(path):
            key = open(path, encoding='utf-8').read().strip()
            if key and not key.startswith('#'):
                return key
    return os.environ.get('OPENAI_API_KEY', '').strip() or None


def generar_post(titulo: str, canal: str, url: str, transcripcion: str) -> dict:
    """Devuelve {'titulo', 'resumen', 'cuerpo_html'}. Lanza excepción si falla."""
    from openai import OpenAI

    api_key = load_openai_key()
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY no configurada')

    client = OpenAI(api_key=api_key)
    respuesta = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={'type': 'json_object'},
        temperature=0.4,
        messages=[
            {'role': 'system', 'content': PROMPT_SISTEMA},
            {'role': 'user', 'content': PROMPT_USUARIO.format(
                titulo=titulo,
                canal=canal,
                url=url,
                transcripcion=transcripcion[:MAX_TRANSCRIPT_CHARS],
            )},
        ],
    )
    datos = json.loads(respuesta.choices[0].message.content)
    for clave in ('titulo', 'resumen', 'cuerpo_html'):
        if not datos.get(clave):
            raise ValueError(f'La respuesta de OpenAI no incluye "{clave}"')
    return datos

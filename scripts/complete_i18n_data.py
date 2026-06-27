"""Traduce estructuras de datos que aún no tienen campos _en en app.py y recursos_seo.py."""
from __future__ import annotations

import json
import os
import sys

import openai
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, '/home/administrator/megasoluciones')

client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))


def translate_json(data, instruction: str) -> dict | list:
    prompt = f"""{instruction}
Return ONLY valid JSON with the same structure, adding '_en' suffix fields for every user-visible Spanish string.
Keep Spanish fields unchanged. For lists of strings, add parallel list with key ending in _en (e.g. entregables + entregables_en).
For nested dicts in ejemplos, add label_en alongside label.
"""
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'user', 'content': prompt + '\n\n' + json.dumps(data, ensure_ascii=False, indent=2)},
        ],
        temperature=0,
        response_format={'type': 'json_object'},
    )
    raw = response.choices[0].message.content
    parsed = json.loads(raw)
    if isinstance(parsed, dict) and len(parsed) == 1:
        return next(iter(parsed.values()))
    return parsed


def main():
    from app import (
        AUTOMATIZACIONES_FAQS,
        CONTACTO_FAQS,
        DESARROLLO_FAQS,
        HOME_CASOS_USO,
        HOME_FAQS,
        HOME_SERVICIOS,
        PRIMERA_CONSULTA_PASOS_META,
        SERVICIO_CHOICES,
        TESTIMONIOS,
    )
    import recursos_seo

    out = {}

    print('Translating FAQs...')
    out['DESARROLLO_FAQS'] = translate_json(
        DESARROLLO_FAQS, 'Translate FAQ list (question, answer).'
    )
    out['AUTOMATIZACIONES_FAQS'] = translate_json(
        AUTOMATIZACIONES_FAQS, 'Translate FAQ list (question, answer).'
    )
    out['HOME_FAQS'] = translate_json(
        HOME_FAQS, 'Translate FAQ list (question, answer, link_text if present).'
    )
    out['CONTACTO_FAQS'] = translate_json(
        CONTACTO_FAQS, 'Translate FAQ list (question, answer).'
    )

    print('Translating HOME_SERVICIOS, HOME_CASOS_USO, TESTIMONIOS...')
    out['HOME_SERVICIOS'] = translate_json(
        HOME_SERVICIOS,
        'Translate service cards: titulo, descripcion, para_quien, caracteristicas (list), cta_text.',
    )
    out['HOME_CASOS_USO'] = translate_json(
        HOME_CASOS_USO, 'Translate use cases: sector, problema, solucion.'
    )
    out['TESTIMONIOS'] = translate_json(
        TESTIMONIOS, 'Translate testimonials: cargo, texto. Keep nombre as-is.'
    )

    print('Translating PRIMERA_CONSULTA_PASOS_META...')
    out['PRIMERA_CONSULTA_PASOS_META'] = translate_json(
        PRIMERA_CONSULTA_PASOS_META,
        'Translate roadmap steps: titulo, badge, desc, entregables list, pagina_label if any, ejemplos[].label.',
    )
    for paso in out['PRIMERA_CONSULTA_PASOS_META']:
        paso.setdefault('pagina_label', 'Ver metodología y entregables')
        paso.setdefault('pagina_label_en', 'View methodology and deliverables')

    print('Translating SERVICIO_CHOICES...')
    choices = [{'value': v, 'label': l} for v, l in SERVICIO_CHOICES]
    translated_choices = translate_json(choices, 'Translate label field only.')
    out['SERVICIO_CHOICES'] = translated_choices

    print('Translating CLUSTER_META...')
    out['CLUSTER_META'] = translate_json(
        recursos_seo.CLUSTER_META, 'Translate nombre and descripcion for each cluster key.'
    )

    path = '/home/administrator/megasoluciones/i18n_data_complete.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'Saved {path}')


if __name__ == '__main__':
    main()

"""Aplica i18n_data_complete.json a app.py y recursos_seo.py."""
from __future__ import annotations

import json
import pprint
import re

DATA_PATH = '/home/administrator/megasoluciones/i18n_data_complete.json'

with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)


def fmt(val):
    return pprint.pformat(val, width=120, sort_dicts=False)


def replace_var(name: str, content: str, new_val) -> str:
    pattern = re.compile(rf'^{name}\s*=\s*\[.*?^\]', re.MULTILINE | re.DOTALL)
    if not pattern.search(content):
        pattern = re.compile(rf'^{name}\s*=\s*\{{.*?^\}}', re.MULTILINE | re.DOTALL)
    return pattern.sub(f'{name} = {fmt(new_val)}', content, count=1)


with open('/home/administrator/megasoluciones/app.py', encoding='utf-8') as f:
    app_content = f.read()

# SERVICIO_CHOICES as tuples from translated list
choices_raw = data['SERVICIO_CHOICES']
if isinstance(choices_raw, list):
    choices = [(c['value'], c['label']) for c in choices_raw]
    choices_en = {c['value']: c.get('label_en', c['label']) for c in choices_raw}
else:
    choices = None
    choices_en = None

for key in (
    'DESARROLLO_FAQS',
    'AUTOMATIZACIONES_FAQS',
    'HOME_FAQS',
    'CONTACTO_FAQS',
    'HOME_SERVICIOS',
    'HOME_CASOS_USO',
    'TESTIMONIOS',
    'PRIMERA_CONSULTA_PASOS_META',
):
    app_content = replace_var(key, app_content, data[key])

if choices is not None:
    app_content = replace_var('SERVICIO_CHOICES', app_content, choices)
    if 'SERVICIO_CHOICES_EN' not in app_content:
        insert = f"\nSERVICIO_CHOICES_EN = {fmt(choices_en)}\n"
        app_content = app_content.replace(
            f'SERVICIO_CHOICES = {fmt(choices)}',
            f'SERVICIO_CHOICES = {fmt(choices)}{insert}',
            1,
        )
else:
    # Manual EN labels for contact form
    if 'SERVICIO_CHOICES_EN' not in app_content:
        manual_en = {
            '': 'Select a service',
            'desarrollo-software': 'Custom software development',
            'automatizaciones-rpa': 'Automations and RPA',
            'chatbots-ia': 'AI Chatbots',
            'consultoria-ia': 'AI Consulting',
            'machine-learning': 'Machine Learning',
            'otro': 'Other / Not sure',
        }
        app_content = app_content.replace(
            'class ContactForm(FlaskForm):',
            f'SERVICIO_CHOICES_EN = {fmt(manual_en)}\n\n\nclass ContactForm(FlaskForm):',
            1,
        )

with open('/home/administrator/megasoluciones/app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)

with open('/home/administrator/megasoluciones/recursos_seo.py', encoding='utf-8') as f:
    seo_content = f.read()

seo_content = replace_var('CLUSTER_META', seo_content, data['CLUSTER_META'])

with open('/home/administrator/megasoluciones/recursos_seo.py', 'w', encoding='utf-8') as f:
    f.write(seo_content)

print('Applied translations to app.py and recursos_seo.py')

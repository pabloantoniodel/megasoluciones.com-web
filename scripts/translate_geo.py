"""Genera traducciones EN para geo_pages.py."""
import json
import os
import sys
import openai
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, '/home/administrator/megasoluciones')
client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

from geo_pages import GEO_HUB, GEO_PAGES


def translate_obj(obj, hint):
    r = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role': 'user', 'content': f"""Translate this JSON from Spanish to English.
Add _en suffix fields for every user-visible string. Keep structure. {hint}
Return JSON only.

{json.dumps(obj, ensure_ascii=False)}"""}],
        temperature=0,
        response_format={'type': 'json_object'},
    )
    data = json.loads(r.choices[0].message.content)
    if isinstance(data, dict) and len(data) == 1:
        return next(iter(data.values()))
    return data


out = {'GEO_HUB': translate_obj(GEO_HUB, 'GEO hub metadata'), 'GEO_PAGES': {}}
for slug, page in GEO_PAGES.items():
    print(f'Translating geo/{slug}...')
    out['GEO_PAGES'][slug] = translate_obj(page, f'Local SEO page for {slug}')

path = '/home/administrator/megasoluciones/geo_i18n_en.json'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print('Saved', path)

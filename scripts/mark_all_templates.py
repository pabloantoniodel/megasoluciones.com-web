"""Marca todas las plantillas públicas con gettext _()."""
import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

templates_dir = '/home/administrator/megasoluciones/templates'
skip = ('admin/',)

prompt = """
You are an expert Jinja2 template editor. Wrap all user-visible Spanish text with {{ _('...') }}.
Rules:
1. Only visible text and alt/title/placeholder/meta content.
2. DO NOT wrap HTML tags, {% %}, or {{ }} that already call functions.
3. DO NOT double-wrap text already inside {{ _('...') }}.
4. Keep Spanish text, do not translate.
5. Return ONLY the template. No markdown fences.
"""

for root, _, files in os.walk(templates_dir):
    if any(s in root for s in skip):
        continue
    for file in files:
        if not file.endswith('.html'):
            continue
        path = os.path.join(root, file)
        with open(path, encoding='utf-8') as f:
            content = f.read()
        if "_('" in content or '_("' in content:
            # Still process if many untranslated strings - check ratio
            if content.count("{{ _('") > 5 and 'recursos-actualidad' not in path:
                continue
        print(f'Processing {path}...')
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': content},
            ],
            temperature=0,
        )
        new_content = response.choices[0].message.content.strip()
        for fence in ('```html', '```'):
            if new_content.startswith(fence):
                new_content = new_content[len(fence):]
        if new_content.endswith('```'):
            new_content = new_content[:-3]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content.strip() + '\n')
        print(f'Saved {file}')

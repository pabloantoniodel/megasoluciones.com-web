import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

templates_to_mark = [
    'base.html',
    'index.html',
    'servicios.html',
    'contacto.html',
    'sobre.html',
    'desarrollo-software.html',
    'automatizaciones.html',
    'portfolio.html',
    'recursos.html'
]

prompt = """
You are an expert Jinja2 template editor. I will provide you with a Jinja2 HTML template in Spanish.
Your task is to wrap all user-visible Spanish text strings with the Flask-Babel gettext function: `_('Text here')`.

Rules:
1. Only wrap actual text content that the user sees on the screen.
2. DO NOT wrap HTML tags, attributes (except `alt`, `title`, `placeholder`, `meta content`), or Jinja2 syntax (`{% ... %}`, `{{ ... }}`).
3. For attributes like `alt="Texto"`, change it to `alt="{{ _('Texto') }}"`.
4. For text inside tags like `<h1>Texto</h1>`, change it to `<h1>{{ _('Texto') }}</h1>`.
5. If the text contains Jinja variables like `<p>Hola {{ nombre }}</p>`, change it to `<p>{{ _('Hola %(nombre)s', nombre=nombre) }}</p>` if possible, or just leave the variable outside if it's simpler: `<p>{{ _('Hola') }} {{ nombre }}</p>`.
6. DO NOT translate the text to English. Keep it in Spanish. Just wrap it in `_()`.
7. Return ONLY the modified template code. No markdown formatting blocks (like ```html), no explanations.
"""

for tpl in templates_to_mark:
    path = f'/home/administrator/megasoluciones/templates/{tpl}'
    if not os.path.exists(path):
        continue
    print(f"Processing {tpl}...")
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        temperature=0
    )
    
    new_content = response.choices[0].message.content.strip()
    if new_content.startswith('```html'):
        new_content = new_content[7:]
    if new_content.startswith('```'):
        new_content = new_content[3:]
    if new_content.endswith('```'):
        new_content = new_content[:-3]
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content.strip() + '\n')
    print(f"Saved {tpl}")

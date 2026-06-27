"""Actualiza plantillas para usar get_field en datos dinámicos."""
import os
import re

replacements = [
    (r'\{\{\s*faq\.question\s*\}\}', "{{ get_field(faq, 'question') }}"),
    (r'\{\{\s*faq\.answer\s*\}\}', "{{ get_field(faq, 'answer') }}"),
    (r'\{\{\s*faq\.link_text\s*or\s*_\(', "{{ get_field(faq, 'link_text') or _("),
    (r'faq\.question\|tojson', "get_field(faq, 'question')|tojson"),
    (r'faq\.answer\|tojson', "get_field(faq, 'answer')|tojson"),
    (r'\{\{\s*testimonio\.texto\s*\}\}', "{{ get_field(testimonio, 'texto') }}"),
    (r'\{\{\s*testimonio\.cargo\s*\}\}', "{{ get_field(testimonio, 'cargo') }}"),
    (r'testimonio\.texto\|tojson', "get_field(testimonio, 'texto')|tojson"),
    (r'\{\{\s*cluster_meta\.nombre\s*\}\}', "{{ get_field(cluster_meta, 'nombre') }}"),
    (r'\{\{\s*cluster_meta\.descripcion\s*\}\}', "{{ get_field(cluster_meta, 'descripcion') }}"),
    (r'\{\{\s*servicio\.para_quien\s*\}\}', "{{ get_field(servicio, 'para_quien') }}"),
    (r'\{\{\s*servicio\.cta_text\s*\}\}', "{{ get_field(servicio, 'cta_text') }}"),
    (r'\{\{\s*caso\.sector\s*\}\}', "{{ get_field(caso, 'sector') }}"),
]

templates_dir = '/home/administrator/megasoluciones/templates'
for root, _, files in os.walk(templates_dir):
    for file in files:
        if not file.endswith('.html'):
            continue
        path = os.path.join(root, file)
        with open(path, encoding='utf-8') as f:
            content = f.read()
        new = content
        for pat, repl in replacements:
            new = re.sub(pat, repl, new)
        if new != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new)
            print('Updated', path)

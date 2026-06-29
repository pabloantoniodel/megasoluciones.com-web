import os
import re

templates_dir = '/home/administrator/megasoluciones/templates'

for root, _, files in os.walk(templates_dir):
    for file in files:
        if not file.endswith('.html'):
            continue
        path = os.path.join(root, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace item.titulo with get_field(item, 'titulo')
        # We need to be careful. Let's just use regex for known variables:
        # proyecto.titulo, proyecto.descripcion, proyecto.problema, proyecto.solucion, proyecto.resultados, proyecto.tecnologias, proyecto.testimonial
        # caso.titulo, caso.descripcion, caso.problema, caso.solucion, caso.resultados, caso.tecnologias, caso.testimonial
        # servicio.titulo, servicio.descripcion, servicio.caracteristicas
        # articulo.titulo, articulo.resumen
        
        replacements = [
            (r'proyecto\.titulo', r"get_field(proyecto, 'titulo')"),
            (r'proyecto\.descripcion', r"get_field(proyecto, 'descripcion')"),
            (r'proyecto\.tecnologias', r"get_field(proyecto, 'tecnologias')"),
            
            (r'caso\.titulo', r"get_field(caso, 'titulo')"),
            (r'caso\.descripcion', r"get_field(caso, 'descripcion')"),
            (r'caso\.problema', r"get_field(caso, 'problema')"),
            (r'caso\.solucion', r"get_field(caso, 'solucion')"),
            (r'caso\.resultados', r"get_field(caso, 'resultados')"),
            (r'caso\.tecnologias', r"get_field(caso, 'tecnologias')"),
            (r'caso\.testimonial', r"get_field(caso, 'testimonial')"),
            
            (r'servicio\.titulo', r"get_field(servicio, 'titulo')"),
            (r'servicio\.descripcion', r"get_field(servicio, 'descripcion')"),
            (r'servicio\.caracteristicas', r"get_field(servicio, 'caracteristicas')"),
            
            (r'articulo\.titulo', r"get_field(articulo, 'titulo')"),
            (r'articulo\.resumen', r"get_field(articulo, 'resumen')"),
        ]
        
        new_content = content
        for old, new in replacements:
            new_content = re.sub(old, new, new_content)
            
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {path}")

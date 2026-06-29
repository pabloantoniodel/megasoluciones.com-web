import os
import json
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

import sys
sys.path.append('/home/administrator/megasoluciones')
from app import RECURSOS, PORTFOLIO, SERVICIOS

def translate_dict_list(data_list, fields_to_translate):
    prompt = f"""
    Translate the following JSON array of objects from Spanish to English.
    Only translate the fields: {', '.join(fields_to_translate)}.
    Add the translated fields with the suffix '_en' (e.g., 'titulo_en').
    Keep the original Spanish fields intact.
    Return ONLY valid JSON.
    
    Data:
    {json.dumps(data_list, ensure_ascii=False, indent=2)}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={ "type": "json_object" }
    )
    
    return json.loads(response.choices[0].message.content)

print("Translating SERVICIOS...")
servicios_translated = translate_dict_list(SERVICIOS, ['titulo', 'descripcion', 'caracteristicas'])

print("Translating PORTFOLIO...")
portfolio_translated = translate_dict_list(PORTFOLIO, ['titulo', 'descripcion', 'problema', 'solucion', 'resultados', 'tecnologias', 'testimonial'])

print("Translating RECURSOS...")
recursos_translated = translate_dict_list(RECURSOS, ['titulo', 'resumen'])

with open('/home/administrator/megasoluciones/translated_data.json', 'w', encoding='utf-8') as f:
    json.dump({
        'SERVICIOS': servicios_translated,
        'PORTFOLIO': portfolio_translated,
        'RECURSOS': recursos_translated
    }, f, ensure_ascii=False, indent=2)
print("Done.")

import os
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def translate_html_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    prompt = """
    Translate the following HTML content from Spanish to English.
    Maintain all HTML tags, classes, IDs, and structure exactly as they are.
    Do not translate URLs inside href attributes, but you can translate the anchor text.
    Return ONLY the translated HTML content. No markdown formatting blocks (like ```html), no explanations.
    """
    
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
        
    return new_content.strip() + '\n'

dirs_to_translate = [
    '/home/administrator/megasoluciones/content/recursos',
    '/home/administrator/megasoluciones/content/portfolio'
]

for d in dirs_to_translate:
    for filename in os.listdir(d):
        if filename.endswith('.html') and not filename.endswith('-en.html'):
            path = os.path.join(d, filename)
            en_path = os.path.join(d, filename.replace('.html', '-en.html'))
            
            if os.path.exists(en_path):
                print(f"Skipping {filename}, English version already exists.")
                continue
                
            print(f"Translating {filename}...")
            try:
                en_content = translate_html_file(path)
                with open(en_path, 'w', encoding='utf-8') as f:
                    f.write(en_content)
                print(f"Saved {en_path}")
            except Exception as e:
                print(f"Error translating {filename}: {e}")

print("Done translating articles.")

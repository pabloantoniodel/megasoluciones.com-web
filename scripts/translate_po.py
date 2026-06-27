import os
import polib
import openai
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

po_path = '/home/administrator/megasoluciones/translations/en/LC_MESSAGES/messages.po'
po = polib.pofile(po_path)

untranslated = [entry for entry in po if not entry.translated() and entry.msgid]

batch_size = 10
for i in range(0, len(untranslated), batch_size):
    batch = untranslated[i:i+batch_size]
    print(f"Translating batch {i//batch_size + 1}/{len(untranslated)//batch_size + 1}...")
    
    texts_to_translate = [entry.msgid for entry in batch]
    
    prompt = f"""
    Translate the following Spanish texts to English. 
    Maintain any HTML tags, Jinja placeholders (like %(name)s), or formatting exactly as they are.
    Return the translations separated by '|||'.
    
    Texts:
    {'|||'.join(texts_to_translate)}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    translations = response.choices[0].message.content.strip().split('|||')
    
    for entry, translation in zip(batch, translations):
        entry.msgstr = translation.strip()

po.save()
print("Done translating .po file.")

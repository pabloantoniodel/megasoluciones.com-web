import json
import re

with open('/home/administrator/megasoluciones/translated_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_list(key):
    val = data[key]
    if isinstance(val, dict) and 'data' in val:
        return val['data']
    if isinstance(val, dict) and key in val:
        return val[key]
    return val

servicios = get_list('SERVICIOS')
portfolio = get_list('PORTFOLIO')
recursos = get_list('RECURSOS')

def format_list(lst):
    # format as python code
    import pprint
    return pprint.pformat(lst, indent=4, width=120, sort_dicts=False)

with open('/home/administrator/megasoluciones/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We can replace the assignments
def replace_var(var_name, new_val_str):
    global content
    pattern = re.compile(rf"^{var_name}\s*=\s*\[.*?^\]", re.MULTILINE | re.DOTALL)
    content = pattern.sub(f"{var_name} = {new_val_str}", content)

replace_var('SERVICIOS', format_list(servicios))
replace_var('PORTFOLIO', format_list(portfolio))
replace_var('RECURSOS', format_list(recursos))

with open('/home/administrator/megasoluciones/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app.py")

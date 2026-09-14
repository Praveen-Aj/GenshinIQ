import json
from pathlib import Path

with open('data/processed/game_data/weapon_curves.json', 'r', encoding='utf-8') as f:
    wcurves = json.load(f)

p = Path('data/processed/game_data/weapons.json')
with open(p, 'r', encoding='utf-8') as f:
    weps = json.load(f)

raw_dir = Path('data/raw/game_data/weapons')
updated = 0
for w in weps:
    wid = w['id']
    raw_file = raw_dir / f'{wid}.json'
    if not raw_file.exists():
        continue
    with open(raw_file, 'r', encoding='utf-8') as rf:
        raw_data = json.load(rf)['data']
    props = raw_data.get('upgrade', {}).get('prop', [])
    if len(props) > 1:
        sub_prop = props[1]
        p_type = sub_prop.get('propType')
        init_val = sub_prop.get('initValue', 0.0)
        c_name = sub_prop.get('type')
        c_val = wcurves.get(c_name, {}).get('90', 4.594)
        calculated = init_val * c_val
        
        if p_type == 'FIGHT_PROP_ELEMENT_MASTERY':
            correct_val = str(round(calculated))
            if w.get('sub_stat_val_lvl90') != correct_val:
                print(f"{w['name']}: {w.get('sub_stat_val_lvl90')} -> {correct_val} (calculated={calculated:.4f})")
                w['sub_stat_val_lvl90'] = correct_val
                updated += 1

with open(p, 'w', encoding='utf-8') as f:
    json.dump(weps, f, indent=2, ensure_ascii=False)

print(f'Done! Corrected {updated} weapons to exact canonical integer EM.')

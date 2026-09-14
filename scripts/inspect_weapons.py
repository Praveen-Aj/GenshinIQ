import json

with open('data/processed/game_data/weapons.json', 'r', encoding='utf-8') as f:
    weapons = {w['name']: w for w in json.load(f)}

targets = ['Freedom-Sworn', "Xiphos' Moonlight", 'Staff of Homa', 'Primordial Jade Cutter', 'Calamity Queller']
for t in targets:
    w = weapons.get(t)
    if w:
        print(f"{t} (ID: {w.get('id')}): Base ATK L1={w.get('base_atk_val')}, L90={w.get('base_atk_val_lvl90')}, Sub={w.get('sub_stat_type')}, Sub L1={w.get('sub_stat_val')}, Sub L90={w.get('sub_stat_val_lvl90')}")
    else:
        print(f"{t} NOT FOUND")

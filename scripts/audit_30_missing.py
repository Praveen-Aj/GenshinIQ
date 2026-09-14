import json
from pathlib import Path

with open('data/processed/game_data/characters.json', 'r', encoding='utf-8') as f:
    characters = json.load(f)

knowledge_docs = list(Path('data/knowledge').glob('*.json'))
k_by_char = {}
for p in knowledge_docs:
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    meta = d.get('metadata', {})
    char = meta.get('character')
    if char:
        k_by_char.setdefault(char, []).append((p.name, meta.get('game_version'), meta.get('source_id')))

wiki_files = list(Path('data/knowledge').glob('wiki_*.json'))
wiki_chars = set()
for wf in wiki_files:
    with open(wf, 'r', encoding='utf-8') as f:
        w = json.load(f)
    cname = w.get('metadata', {}).get('character') or wf.stem.replace('wiki_', '')
    wiki_chars.add(cname.lower().replace(' ', '').replace('_', '').replace('-', ''))

missing_from_wiki = []
missing_completely = []

for c in characters:
    cname = c['name']
    norm = cname.lower().replace(' ', '').replace('_', '').replace('-', '')
    docs = k_by_char.get(cname, [])
    has_wiki = norm in wiki_chars
    
    if not has_wiki:
        missing_from_wiki.append(c)
    if not docs:
        missing_completely.append(c)

print(f'Total canonical characters: {len(characters)}')
print(f'Missing from wiki (completeness gate): {len(missing_from_wiki)}')
print(f'Missing completely (no knowledge doc at all): {len(missing_completely)}')

print('\nDetailed Breakdown of the 30 Gate-Missing Characters:')
print(f'{"Character Name":22} | {"ID":10} | {"Rarity":6} | {"Element":8} | {"Weapon":8} | {"Ver":5} | {"Raw Avatar File?":17} | Docs in data/knowledge')
print('-' * 115)
for c in missing_from_wiki:
    docs = k_by_char.get(c['name'], [])
    doc_info = ', '.join(d[0] for d in docs) if docs else 'NONE'
    raw_avatar_exists = Path(f'data/raw/game_data/avatars/{c["id"]}.json').exists()
    rarity_str = str(c.get("rarity", "?")) + "-star"
    print(f'{c["name"]:22} | {c["id"]:<10} | {rarity_str:8} | {str(c.get("element", "?")):8} | {str(c.get("weapon_type", "?")):8} | {str(c.get("game_version_introduced", "?")):5} | {str(raw_avatar_exists):17} | {doc_info}')

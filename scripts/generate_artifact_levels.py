import json
from pathlib import Path

content_file = Path(r'C:\Users\Praveen\.gemini\antigravity-ide\brain\b3268147-3380-4376-a7d9-abddcd1f6d90\.system_generated\steps\3357\content.md')
with open(content_file, 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('[')
raw_data = json.loads(text[idx:])

prop_type_map = {
    "FIGHT_PROP_HP": "hp",
    "FIGHT_PROP_ATTACK": "atk",
    "FIGHT_PROP_HP_PERCENT": "hp_",
    "FIGHT_PROP_ATTACK_PERCENT": "atk_",
    "FIGHT_PROP_DEFENSE_PERCENT": "def_",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "enerRech_",
    "FIGHT_PROP_ELEMENT_MASTERY": "eleMas",
    "FIGHT_PROP_CRITICAL": "critRate_",
    "FIGHT_PROP_CRITICAL_HURT": "critDMG_",
    "FIGHT_PROP_HEAL_ADD": "heal_",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "physical_dmg_",
    "FIGHT_PROP_FIRE_ADD_HURT": "pyro_dmg_",
    "FIGHT_PROP_WATER_ADD_HURT": "hydro_dmg_",
    "FIGHT_PROP_ELEC_ADD_HURT": "electro_dmg_",
    "FIGHT_PROP_WIND_ADD_HURT": "anemo_dmg_",
    "FIGHT_PROP_ICE_ADD_HURT": "cryo_dmg_",
    "FIGHT_PROP_ROCK_ADD_HURT": "geo_dmg_",
    "FIGHT_PROP_GRASS_ADD_HURT": "dendro_dmg_",
}

# Structure: { "5": { "0": { "hp": 717.0, ... }, "20": { ... } }, "4": { ... } }
processed = {}
for entry in raw_data:
    rank = entry.get('rank')
    level = entry.get('level')
    if rank is None or level is None:
        continue
    rank_str = str(rank)
    enhancement_level = str(level - 1)  # internal level 1 is in-game +0
    
    if rank_str not in processed:
        processed[rank_str] = {}
        
    stats = {}
    for p in entry.get('addProps', []):
        pt = p.get('propType')
        val = p.get('value', 0.0)
        mapped = prop_type_map.get(pt)
        if mapped:
            stats[mapped] = val
            
    processed[rank_str][enhancement_level] = stats

out_path = Path('data/processed/game_data/artifact_levels.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(processed, f, indent=2)

print(f"Generated {out_path} with {len(processed)} rarity tiers.")
for r in sorted(processed.keys()):
    print(f"  Rarity {r}*: {len(processed[r])} levels (+0 to +{len(processed[r])-1})")

import json
from pathlib import Path

with open(r'C:\Users\Praveen\.gemini\antigravity-ide\brain\b3268147-3380-4376-a7d9-abddcd1f6d90\.system_generated\steps\3357\content.md', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find('[')
data = json.loads(text[idx:])

print("=== 5-STAR ARTIFACT MAIN STATS ACROSS BREAKPOINTS ===")
for d in data:
    rank = d.get('rank')
    level = d.get('level')
    if rank == 5 and level in [1, 5, 9, 13, 17, 21]:
        props = {p['propType']: p['value'] for p in d.get('addProps', [])}
        hp = props.get('FIGHT_PROP_HP')
        atk = props.get('FIGHT_PROP_ATTACK')
        atk_p = props.get('FIGHT_PROP_ATTACK_PERCENT')
        def_p = props.get('FIGHT_PROP_DEFENSE_PERCENT')
        hp_p = props.get('FIGHT_PROP_HP_PERCENT')
        er = props.get('FIGHT_PROP_CHARGE_EFFICIENCY')
        em = props.get('FIGHT_PROP_ELEMENT_MASTERY')
        cr = props.get('FIGHT_PROP_CRITICAL')
        cd = props.get('FIGHT_PROP_CRITICAL_HURT')
        elem = props.get('FIGHT_PROP_FIRE_ADD_HURT')
        phys = props.get('FIGHT_PROP_PHYSICAL_ADD_HURT')
        heal = props.get('FIGHT_PROP_HEAL_ADD')
        print(f"5* +{level-1:02d}: HP={round(hp):4d} | ATK={round(atk):3d} | ATK%={atk_p*100:4.1f}% | DEF%={def_p*100:4.1f}% | HP%={hp_p*100:4.1f}% | ER={er*100:4.1f}% | EM={round(em):3d} | CR={cr*100:4.1f}% | CD={cd*100:4.1f}% | Elem%={elem*100:4.1f}% | Phys%={phys*100:4.1f}% | Heal%={heal*100:4.1f}%")

print("\n=== 4-STAR ARTIFACT MAIN STATS ACROSS BREAKPOINTS ===")
for d in data:
    rank = d.get('rank')
    level = d.get('level')
    if rank == 4 and level in [1, 5, 9, 13, 17]:
        props = {p['propType']: p['value'] for p in d.get('addProps', [])}
        hp = props.get('FIGHT_PROP_HP')
        atk = props.get('FIGHT_PROP_ATTACK')
        atk_p = props.get('FIGHT_PROP_ATTACK_PERCENT')
        def_p = props.get('FIGHT_PROP_DEFENSE_PERCENT')
        hp_p = props.get('FIGHT_PROP_HP_PERCENT')
        er = props.get('FIGHT_PROP_CHARGE_EFFICIENCY')
        em = props.get('FIGHT_PROP_ELEMENT_MASTERY')
        cr = props.get('FIGHT_PROP_CRITICAL')
        cd = props.get('FIGHT_PROP_CRITICAL_HURT')
        elem = props.get('FIGHT_PROP_FIRE_ADD_HURT')
        phys = props.get('FIGHT_PROP_PHYSICAL_ADD_HURT')
        heal = props.get('FIGHT_PROP_HEAL_ADD')
        print(f"4* +{level-1:02d}: HP={round(hp):4d} | ATK={round(atk):3d} | ATK%={atk_p*100:4.1f}% | DEF%={def_p*100:4.1f}% | HP%={hp_p*100:4.1f}% | ER={er*100:4.1f}% | EM={round(em):3d} | CR={cr*100:4.1f}% | CD={cd*100:4.1f}% | Elem%={elem*100:4.1f}% | Phys%={phys*100:4.1f}% | Heal%={heal*100:4.1f}%")

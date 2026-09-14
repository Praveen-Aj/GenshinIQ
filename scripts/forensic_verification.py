import json
from pathlib import Path

def audit_characters():
    print("==================================================")
    print("1. CHARACTER DATA AUDIT")
    print("==================================================")
    with open('data/processed/game_data/avatar_curves.json', 'r', encoding='utf-8') as f:
        avatar_curves = json.load(f)

    char_ids = {
        'Kaedehara Kazuha': 10000047,
        'Hu Tao': 10000046,
        'Xiao': 10000026,
        'Arlecchino': 10000096
    }

    results = {}
    for name, cid in char_ids.items():
        p = Path(f'data/raw/game_data/avatars/{cid}.json')
        if not p.exists():
            print(f"Missing raw avatar file for {name} ({cid})")
            continue
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f).get('data', {})
        
        upgrade = d.get('upgrade', {})
        props = {pr['propType']: pr for pr in upgrade.get('prop', [])}
        promotes = upgrade.get('promote', [])
        
        init_hp = props.get('FIGHT_PROP_BASE_HP', {}).get('initValue', 0.0)
        hp_curve_name = props.get('FIGHT_PROP_BASE_HP', {}).get('type')
        init_atk = props.get('FIGHT_PROP_BASE_ATTACK', {}).get('initValue', 0.0)
        atk_curve_name = props.get('FIGHT_PROP_BASE_ATTACK', {}).get('type')
        init_def = props.get('FIGHT_PROP_BASE_DEFENSE', {}).get('initValue', 0.0)
        def_curve_name = props.get('FIGHT_PROP_BASE_DEFENSE', {}).get('type')

        breakpoints = [
            (1, 0), (20, 0), (20, 1), (40, 1), (40, 2), (50, 2), (50, 3),
            (60, 3), (60, 4), (70, 4), (70, 5), (80, 5), (80, 6), (90, 6)
        ]
        
        char_bp_res = []
        for lvl, asc in breakpoints:
            hp_mult = avatar_curves.get(hp_curve_name, {}).get(str(lvl), 1.0)
            atk_mult = avatar_curves.get(atk_curve_name, {}).get(str(lvl), 1.0)
            def_mult = avatar_curves.get(def_curve_name, {}).get(str(lvl), hp_mult)
            
            p_data = promotes[asc] if asc < len(promotes) else {}
            add_props = p_data.get('addProps', {})
            
            b_hp = add_props.get('FIGHT_PROP_BASE_HP', 0.0)
            b_atk = add_props.get('FIGHT_PROP_BASE_ATTACK', 0.0)
            b_def = add_props.get('FIGHT_PROP_BASE_DEFENSE', 0.0)
            
            calc_hp = round(init_hp * hp_mult + b_hp)
            calc_atk = round(init_atk * atk_mult + b_atk)
            calc_def = round(init_def * def_mult + b_def)
            
            special_stat = {}
            for pk, pv in add_props.items():
                if pk not in ['FIGHT_PROP_BASE_HP', 'FIGHT_PROP_BASE_ATTACK', 'FIGHT_PROP_BASE_DEFENSE']:
                    special_stat[pk] = pv
            
            char_bp_res.append({
                'level': lvl,
                'ascension': asc,
                'hp': calc_hp,
                'atk': calc_atk,
                'def': calc_def,
                'special': special_stat
            })
            
        results[name] = {
            'init': {'hp': init_hp, 'atk': init_atk, 'def': init_def},
            'breakpoints': char_bp_res
        }
        print(f"Verified {name}:")
        print(f"  Level 1 (Asc 0): HP={char_bp_res[0]['hp']}, ATK={char_bp_res[0]['atk']}, DEF={char_bp_res[0]['def']}")
        print(f"  Level 20 (Asc 0): HP={char_bp_res[1]['hp']}, ATK={char_bp_res[1]['atk']}, DEF={char_bp_res[1]['def']}")
        print(f"  Level 20+ (Asc 1): HP={char_bp_res[2]['hp']}, ATK={char_bp_res[2]['atk']}, DEF={char_bp_res[2]['def']}")
        print(f"  Level 40 (Asc 1): HP={char_bp_res[3]['hp']}, ATK={char_bp_res[3]['atk']}, DEF={char_bp_res[3]['def']}")
        print(f"  Level 40+ (Asc 2): HP={char_bp_res[4]['hp']}, ATK={char_bp_res[4]['atk']}, DEF={char_bp_res[4]['def']}")
        print(f"  Level 50 (Asc 2): HP={char_bp_res[5]['hp']}, ATK={char_bp_res[5]['atk']}, DEF={char_bp_res[5]['def']}")
        print(f"  Level 50+ (Asc 3): HP={char_bp_res[6]['hp']}, ATK={char_bp_res[6]['atk']}, DEF={char_bp_res[6]['def']}")
        print(f"  Level 60 (Asc 3): HP={char_bp_res[7]['hp']}, ATK={char_bp_res[7]['atk']}, DEF={char_bp_res[7]['def']}")
        print(f"  Level 60+ (Asc 4): HP={char_bp_res[8]['hp']}, ATK={char_bp_res[8]['atk']}, DEF={char_bp_res[8]['def']}")
        print(f"  Level 70 (Asc 4): HP={char_bp_res[9]['hp']}, ATK={char_bp_res[9]['atk']}, DEF={char_bp_res[9]['def']}")
        print(f"  Level 70+ (Asc 5): HP={char_bp_res[10]['hp']}, ATK={char_bp_res[10]['atk']}, DEF={char_bp_res[10]['def']}")
        print(f"  Level 80 (Asc 5): HP={char_bp_res[11]['hp']}, ATK={char_bp_res[11]['atk']}, DEF={char_bp_res[11]['def']}")
        print(f"  Level 80+ (Asc 6): HP={char_bp_res[12]['hp']}, ATK={char_bp_res[12]['atk']}, DEF={char_bp_res[12]['def']}")
        print(f"  Level 90 (Asc 6): HP={char_bp_res[13]['hp']}, ATK={char_bp_res[13]['atk']}, DEF={char_bp_res[13]['def']}, Special={char_bp_res[13]['special']}")

    return results

def audit_weapons():
    print("\n==================================================")
    print("2. WEAPON DATA AUDIT")
    print("==================================================")
    with open('data/processed/game_data/weapon_curves.json', 'r', encoding='utf-8') as f:
        weapon_curves = json.load(f)

    with open('data/processed/game_data/weapons.json', 'r', encoding='utf-8') as f:
        processed_weps = {w['name']: w for w in json.load(f)}

    target_weapons = [
        ('Freedom-Sworn', 11503),
        ("Xiphos' Moonlight", 11418),
        ('Staff of Homa', 13501),
        ('Primordial Jade Cutter', 11505),
        ('Calamity Queller', 13507)
    ]

    breakpoints = [
        (1, 0), (20, 0), (20, 1), (40, 1), (40, 2), (50, 2), (50, 3),
        (60, 3), (60, 4), (70, 4), (70, 5), (80, 5), (80, 6), (90, 6)
    ]

    prop_name_map = {
        'FIGHT_PROP_ELEMENT_MASTERY': 'Elemental Mastery',
        'FIGHT_PROP_CRITICAL_HURT': 'CRIT DMG',
        'FIGHT_PROP_CRITICAL': 'CRIT Rate',
        'FIGHT_PROP_CHARGE_EFFICIENCY': 'Energy Recharge',
        'FIGHT_PROP_ATTACK_PERCENT': 'ATK%',
        'FIGHT_PROP_HP_PERCENT': 'HP%',
        'FIGHT_PROP_DEFENSE_PERCENT': 'DEF%',
    }

    results = {}
    for name, wid in target_weapons:
        p = Path(f'data/raw/game_data/weapons/{wid}.json')
        if not p.exists():
            print(f"Missing raw weapon file for {name} ({wid})")
            continue
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f).get('data', {})
        
        upgrade = d.get('upgrade', {})
        props = upgrade.get('prop', [])
        promotes = upgrade.get('promote', [])
        
        atk_prop = props[0] if len(props) > 0 else {}
        sub_prop = props[1] if len(props) > 1 else {}
        
        init_atk = atk_prop.get('initValue', 0.0)
        atk_curve_type = atk_prop.get('type')
        
        init_sub = sub_prop.get('initValue', 0.0)
        sub_curve_type = sub_prop.get('type')
        sub_prop_key = sub_prop.get('propType')
        sub_name = prop_name_map.get(sub_prop_key, sub_prop_key)
        
        w_bp_res = []
        for lvl, asc in breakpoints:
            atk_mult = weapon_curves.get(atk_curve_type, {}).get(str(lvl), 1.0)
            sub_mult = weapon_curves.get(sub_curve_type, {}).get(str(lvl), 1.0)
            
            p_data = promotes[asc] if asc < len(promotes) else {}
            add_props = p_data.get('addProps', {})
            bonus_atk = add_props.get('FIGHT_PROP_BASE_ATTACK', 0.0)
            
            calc_atk = round(init_atk * atk_mult + bonus_atk)
            calc_sub_raw = init_sub * sub_mult
            
            if sub_name == 'Elemental Mastery':
                disp_sub = str(round(calc_sub_raw))
            elif calc_sub_raw <= 1.0:
                disp_sub = f"{round(calc_sub_raw * 100, 1)}%"
            else:
                disp_sub = str(round(calc_sub_raw, 1))
                
            w_bp_res.append({
                'level': lvl,
                'ascension': asc,
                'atk': calc_atk,
                'sub_stat_raw': calc_sub_raw,
                'sub_stat_disp': disp_sub
            })
            
        results[name] = w_bp_res
        print(f"\nVerified {name} (Substat: {sub_name}):")
        print(f"  Level 1 (Asc 0): Base ATK={w_bp_res[0]['atk']}, Sub={w_bp_res[0]['sub_stat_disp']}")
        print(f"  Level 20 (Asc 0): Base ATK={w_bp_res[1]['atk']}, Sub={w_bp_res[1]['sub_stat_disp']}")
        print(f"  Level 20+ (Asc 1): Base ATK={w_bp_res[2]['atk']}, Sub={w_bp_res[2]['sub_stat_disp']}")
        print(f"  Level 40 (Asc 1): Base ATK={w_bp_res[3]['atk']}, Sub={w_bp_res[3]['sub_stat_disp']}")
        print(f"  Level 40+ (Asc 2): Base ATK={w_bp_res[4]['atk']}, Sub={w_bp_res[4]['sub_stat_disp']}")
        print(f"  Level 50 (Asc 2): Base ATK={w_bp_res[5]['atk']}, Sub={w_bp_res[5]['sub_stat_disp']}")
        print(f"  Level 50+ (Asc 3): Base ATK={w_bp_res[6]['atk']}, Sub={w_bp_res[6]['sub_stat_disp']}")
        print(f"  Level 60 (Asc 3): Base ATK={w_bp_res[7]['atk']}, Sub={w_bp_res[7]['sub_stat_disp']}")
        print(f"  Level 60+ (Asc 4): Base ATK={w_bp_res[8]['atk']}, Sub={w_bp_res[8]['sub_stat_disp']}")
        print(f"  Level 70 (Asc 4): Base ATK={w_bp_res[9]['atk']}, Sub={w_bp_res[9]['sub_stat_disp']}")
        print(f"  Level 70+ (Asc 5): Base ATK={w_bp_res[10]['atk']}, Sub={w_bp_res[10]['sub_stat_disp']}")
        print(f"  Level 80 (Asc 5): Base ATK={w_bp_res[11]['atk']}, Sub={w_bp_res[11]['sub_stat_disp']}")
        print(f"  Level 80+ (Asc 6): Base ATK={w_bp_res[12]['atk']}, Sub={w_bp_res[12]['sub_stat_disp']}")
        print(f"  Level 90 (Asc 6): Base ATK={w_bp_res[13]['atk']}, Sub={w_bp_res[13]['sub_stat_disp']}")

    return results

if __name__ == '__main__':
    audit_characters()
    audit_weapons()

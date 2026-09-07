"""Deep verification and audit script for canonical GenshinIQ game data."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed" / "game_data"

def main():
    print("=== DEEP AUDIT OF CANONICAL DATASETS ===")

    with open(PROCESSED_DIR / "characters.json", "r", encoding="utf-8") as f:
        chars = json.load(f)
    with open(PROCESSED_DIR / "weapons.json", "r", encoding="utf-8") as f:
        weps = json.load(f)
    with open(PROCESSED_DIR / "artifacts.json", "r", encoding="utf-8") as f:
        arts = json.load(f)
    with open(PROCESSED_DIR / "materials.json", "r", encoding="utf-8") as f:
        mats = json.load(f)

    # 1. Characters Audit
    char_issues = []
    for c in chars:
        name = c["name"]
        hp, atk, df = c["base_hp_lvl90"], c["base_atk_lvl90"], c["base_def_lvl90"]
        if hp == 11000.0 and atk == 250.0:
            char_issues.append(f"{name}: placeholder stat detected (11000 HP / 250 ATK)")
        if hp <= 0 or atk <= 0 or df <= 0:
            char_issues.append(f"{name}: invalid base stat (HP={hp}, ATK={atk}, DEF={df})")
        if len(c["talents"]) < 3:
            char_issues.append(f"{name}: has fewer than 3 talents ({len(c['talents'])})")
        if name != "Aloy" and len(c["constellations"]) != 6:
            char_issues.append(f"{name}: constellation count is {len(c['constellations'])} (expected 6)")
        if not c["ascension_materials"]:
            char_issues.append(f"{name}: empty ascension materials")
        if not c["talent_materials"]:
            char_issues.append(f"{name}: empty talent materials")

    print(f"Characters Audit: {len(chars)} records | Issues: {len(char_issues)}")
    for iss in char_issues:
        print(f"  [!] {iss}")

    # 2. Weapons Audit
    wep_issues = []
    for w in weps:
        name = w["name"]
        atk1, atk90 = w["base_atk_lvl1"], w["base_atk_lvl90"]
        if atk90 <= 0 or atk1 <= 0:
            wep_issues.append(f"{name}: invalid base ATK (L1={atk1}, L90={atk90})")
        unrefinable_weapons = {"Sword of Descension", "Kagotsurube Isshin", "Predator"}
        if w["rarity"] in [4, 5] and w.get("passive_name") and name not in unrefinable_weapons:
            refs = w.get("refinements", [])
            if len(refs) < 5:
                wep_issues.append(f"{name} ({w['rarity']}*): has passive '{w.get('passive_name')}' but only {len(refs)} refinements")
        if not w["ascension_materials"]:
            wep_issues.append(f"{name}: empty ascension materials")

    print(f"Weapons Audit: {len(weps)} records | Issues: {len(wep_issues)}")
    for iss in wep_issues[:10]:
        print(f"  [!] {iss}")

    # 3. Artifacts Audit
    art_issues = []
    circlet_only = {"Prayers for Destiny", "Prayers for Illumination", "Prayers for Wisdom", "Prayers to Springtime"}
    for a in arts:
        name = a["name"]
        if not a.get("bonus_2pc"):
            art_issues.append(f"{name}: missing 2pc bonus")
        if name not in circlet_only and not a.get("bonus_4pc"):
            art_issues.append(f"{name}: missing 4pc bonus")
        pieces = a.get("pieces", {})
        if name not in circlet_only:
            for slot in ["flower", "plume", "sands", "goblet", "circlet"]:
                if slot not in pieces:
                    art_issues.append(f"{name}: missing slot '{slot}'")

    print(f"Artifacts Audit: {len(arts)} records | Issues: {len(art_issues)}")
    for iss in art_issues:
        print(f"  [!] {iss}")

    # 4. Materials Audit
    mat_issues = []
    for m in mats:
        if not m.get("name") or not m.get("type") or not m.get("sources"):
            mat_issues.append(f"ID {m.get('id')}: incomplete record")

    print(f"Materials Audit: {len(mats)} records | Issues: {len(mat_issues)}")
    for iss in mat_issues:
        print(f"  [!] {iss}")

    total_issues = len(char_issues) + len(wep_issues) + len(art_issues) + len(mat_issues)
    if total_issues == 0:
        print("\n[SUCCESS] 100% OF CANONICAL DATASETS VERIFIED CLEAN AND COMPLETE WITH ZERO PLACEHOLDERS!")
    else:
        print(f"\n[FAILURE] Total issues detected: {total_issues}")


if __name__ == "__main__":
    main()

"""Script to add canonical icon paths to local game data JSON files."""

import json
from pathlib import Path

CHARACTER_ICONS = {
    "Arlecchino": "UI_AvatarIcon_Arlecchino",
    "Furina": "UI_AvatarIcon_Furina",
    "Neuvillette": "UI_AvatarIcon_Neuvillette",
    "Raiden Shogun": "UI_AvatarIcon_Shogun",
    "Nahida": "UI_AvatarIcon_Nahida",
    "Kaedehara Kazuha": "UI_AvatarIcon_Kazuha",
    "Zhongli": "UI_AvatarIcon_Zhongli",
    "Bennett": "UI_AvatarIcon_Bennett",
    "Xiangling": "UI_AvatarIcon_Xiangling",
    "Xingqiu": "UI_AvatarIcon_Xingqiu",
    "Mavuika": "UI_AvatarIcon_Mavuika",
    "Skirk": "UI_AvatarIcon_Skirk",
    "Nefer": "UI_AvatarIcon_Nefer",
    "Zibai": "UI_AvatarIcon_Zibai",
}

WEAPON_ICONS = {
    13512: "UI_EquipIcon_Pole_Crimson",       # Crimson Moon's Semblance
    11512: "UI_EquipIcon_Sword_Magnum",        # Splendor of Tranquil Waters
    14512: "UI_EquipIcon_Catalyst_Iatros",     # Tome of the Eternal Flow
    13509: "UI_EquipIcon_Pole_Narukami",      # Engulfing Lightning
    13501: "UI_EquipIcon_Pole_Homa",          # Staff of Homa
    11509: "UI_EquipIcon_Sword_Narukami",     # Mistsplitter Reforged
    13415: "UI_EquipIcon_Pole_Miko",          # "The Catch"
    11401: "UI_EquipIcon_Sword_Zephyrus",     # Favonius Sword
    13407: "UI_EquipIcon_Pole_Zephyrus",       # Favonius Lance
    11418: "UI_EquipIcon_Sword_Pleroma",       # Xiphos' Moonlight
    12426: "UI_EquipIcon_Catalyst_Oath",       # Oathsworn Eye / Favonius Codex fallback
    12502: "UI_EquipIcon_Pole_Wolfmound",      # Footprint of the Rainbow
    14302: "UI_EquipIcon_Bow_Slingshot",       # Slingshot
}

ARTIFACT_ICONS = {
    15038: "UI_RelicIcon_15038_4",            # Scroll of Cinder City (Goblet)
    15037: "UI_RelicIcon_15037_4",            # Obsidian Codex (Goblet)
    15035: "UI_RelicIcon_15035_4",            # Fragment of Harmonic Whimsy (Goblet)
    15032: "UI_RelicIcon_15032_4",            # Golden Troupe (Goblet)
    15031: "UI_RelicIcon_15031_4",            # Marechaussee Hunter (Goblet)
    15020: "UI_RelicIcon_15020_4",            # Emblem of Severed Fate (Goblet)
    15002: "UI_RelicIcon_15002_4",            # Viridescent Venerer (Goblet)
    15007: "UI_RelicIcon_15007_4",            # Noblesse Oblige (Goblet)
    15034: "UI_RelicIcon_15034_4",            # Song of Days Past (Goblet)
}

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data" / "processed" / "game_data"

    # 1. Update Characters
    char_file = data_dir / "characters.json"
    if char_file.exists():
        with open(char_file, "r", encoding="utf-8") as f:
            chars = json.load(f)
        for c in chars:
            c["icon"] = CHARACTER_ICONS.get(c["name"], f"UI_AvatarIcon_{c['name']}")
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(chars, f, indent=2, ensure_ascii=False)
        print("Updated characters.json with icons.")

    # 2. Update Weapons
    weapon_file = data_dir / "weapons.json"
    if weapon_file.exists():
        with open(weapon_file, "r", encoding="utf-8") as f:
            weapons = json.load(f)
        for w in weapons:
            w["icon"] = WEAPON_ICONS.get(w["id"], f"UI_EquipIcon_Sword_Zephyrus")
        with open(weapon_file, "w", encoding="utf-8") as f:
            json.dump(weapons, f, indent=2, ensure_ascii=False)
        print("Updated weapons.json with icons.")

    # 3. Update Artifacts
    art_file = data_dir / "artifacts.json"
    if art_file.exists():
        with open(art_file, "r", encoding="utf-8") as f:
            artifacts = json.load(f)
        for a in artifacts:
            a["icon"] = ARTIFACT_ICONS.get(a["id"], f"UI_RelicIcon_{a['id']}_4")
        with open(art_file, "w", encoding="utf-8") as f:
            json.dump(artifacts, f, indent=2, ensure_ascii=False)
        print("Updated artifacts.json with icons.")

if __name__ == "__main__":
    main()

"""
Fetch comprehensive Genshin Impact knowledge from the genshin.jmp.blue community API.

Generates knowledge documents for:
- All playable characters (talents, constellations, passives, ascension materials)
- All artifact sets (2pc/4pc bonuses, piece names)

Each document is saved as a JSON file in data/knowledge/ matching the KnowledgeDocument schema.
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = "https://genshin.jmp.blue"
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge")


def fetch_json(url: str, retries: int = 3) -> dict | list | None:
    """Fetch JSON from URL with retry logic."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GenshinIQ/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            print(f"  [Attempt {attempt+1}/{retries}] Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(1.5)
    return None


def format_character_content(data: dict) -> str:
    """Convert raw API character data into rich Markdown knowledge content."""
    lines = []
    name = data.get("name", "Unknown")
    lines.append(f"# {name} — Complete Character Reference")
    lines.append("")

    # Overview
    lines.append("## Overview")
    lines.append(f"- **Name**: {name}")
    lines.append(f"- **Title**: {data.get('title', 'N/A')}")
    lines.append(f"- **Rarity**: {'★' * data.get('rarity', 4)}")
    lines.append(f"- **Element / Vision**: {data.get('vision', 'Unknown')}")
    lines.append(f"- **Weapon Type**: {data.get('weapon', 'Unknown')}")
    lines.append(f"- **Nation**: {data.get('nation', 'Unknown')}")
    lines.append(f"- **Affiliation**: {data.get('affiliation', 'N/A')}")
    lines.append(f"- **Constellation**: {data.get('constellation', 'N/A')}")
    lines.append(f"- **Birthday**: {data.get('birthday', 'N/A')}")
    lines.append(f"- **Special Dish**: {data.get('specialDish', 'None')}")
    desc = data.get("description", "")
    if desc:
        lines.append(f"\n> {desc}")
    lines.append("")

    # Skill Talents
    skill_talents = data.get("skillTalents", [])
    if skill_talents:
        lines.append("## Combat Talents")
        for talent in skill_talents:
            ttype = talent.get("type", "")
            label = {
                "NORMAL_ATTACK": "Normal Attack",
                "ELEMENTAL_SKILL": "Elemental Skill",
                "ELEMENTAL_BURST": "Elemental Burst",
            }.get(ttype, ttype)
            lines.append(f"\n### {label}: {talent.get('name', 'Unknown')}")
            desc = talent.get("description", "").replace("\\n", "\n")
            lines.append(desc)

            upgrades = talent.get("upgrades", [])
            if upgrades:
                lines.append("\n**Scaling Values (Lv. 1):**")
                for u in upgrades:
                    lines.append(f"- {u.get('name', '?')}: {u.get('value', '?')}")
        lines.append("")

    # Passive Talents
    passives = data.get("passiveTalents", [])
    if passives:
        lines.append("## Passive Talents")
        for p in passives:
            level = p.get("level")
            unlock = p.get("unlock", "")
            lines.append(f"\n### {p.get('name', 'Unknown')} ({unlock})")
            lines.append(p.get("description", "").replace("\\n", "\n"))
        lines.append("")

    # Constellations
    consts = data.get("constellations", [])
    if consts:
        lines.append("## Constellations")
        for c in consts:
            lvl = c.get("level", "?")
            lines.append(f"\n### C{lvl}: {c.get('name', 'Unknown')}")
            lines.append(c.get("description", "").replace("\\n", "\n"))
        lines.append("")

    # Ascension Materials
    asc_mats = data.get("ascension_materials", {})
    if asc_mats:
        lines.append("## Ascension Materials")
        for phase, mats in sorted(asc_mats.items()):
            mat_list = ", ".join([f"{m.get('name')} ×{m.get('value')}" for m in mats])
            lines.append(f"- **{phase.replace('_', ' ').title()}**: {mat_list}")
        lines.append("")

    return "\n".join(lines)


def format_artifact_content(data: dict) -> str:
    """Convert raw API artifact data into Markdown knowledge content."""
    lines = []
    name = data.get("name", "Unknown")
    lines.append(f"# {name} — Artifact Set Reference")
    lines.append("")
    lines.append(f"- **Max Rarity**: {'★' * data.get('max_rarity', 5)}")
    lines.append("")

    bonuses = data.get("bonuses", [])
    if bonuses:
        for i, b in enumerate(bonuses):
            pieces = b.get("pieces", 2 if i == 0 else 4)
            lines.append(f"## {pieces}-Piece Bonus")
            lines.append(b.get("description", "N/A"))
            lines.append("")

    # Individual pieces
    types_map = {
        "flower": "Flower of Life",
        "plume": "Plume of Death",
        "sands": "Sands of Eon",
        "goblet": "Goblet of Eonothem",
        "circlet": "Circlet of Logos",
    }
    availability = data.get("availability", {})
    for slot, label in types_map.items():
        piece = availability.get(slot) if isinstance(availability, dict) else None
        if piece:
            lines.append(f"### {label}")
            lines.append(f"**{piece.get('name', slot)}**: {piece.get('description', '')}")
            lines.append("")

    return "\n".join(lines)


def create_character_doc(char_id: str, data: dict) -> dict:
    """Create a KnowledgeDocument dict for a character."""
    name = data.get("name", char_id.replace("-", " ").title())
    vision = data.get("vision", "Unknown")
    weapon = data.get("weapon", "Unknown")
    rarity = data.get("rarity", 4)

    content = format_character_content(data)
    summary = (
        f"Complete reference for {name}: {rarity}-star {vision} {weapon} user. "
        f"Includes Normal Attack, Elemental Skill, Elemental Burst talent descriptions with scaling values, "
        f"passive talents, all 6 constellation effects, and ascension material requirements."
    )

    tags = [name, vision, weapon, data.get("nation", ""), "Character"]
    tags = [t for t in tags if t]

    return {
        "id": f"wiki_{char_id.replace('-', '_')}",
        "title": f"{name} — Complete Character Guide & Talent Reference",
        "metadata": {
            "source": "Genshin Impact Community Wiki (genshin.jmp.blue)",
            "source_url": f"https://genshin-impact.fandom.com/wiki/{name.replace(' ', '_')}",
            "source_type": "AUTHORITATIVE",
            "character": name,
            "topic": "Character Guide",
            "game_version": "5.4",
            "published_at": data.get("release", "2020-09-28") + "T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tags": tags,
        },
        "summary": summary,
        "content": content,
    }


def create_artifact_doc(art_id: str, data: dict) -> dict:
    """Create a KnowledgeDocument dict for an artifact set."""
    name = data.get("name", art_id.replace("-", " ").title())
    content = format_artifact_content(data)

    bonuses = data.get("bonuses", [])
    bonus_summaries = []
    for b in bonuses:
        pieces = b.get("pieces", "?")
        desc = b.get("description", "")[:100]
        bonus_summaries.append(f"{pieces}pc: {desc}")
    bonus_text = "; ".join(bonus_summaries) if bonus_summaries else "No set bonuses."

    summary = f"Artifact set reference for {name}. {bonus_text}"

    return {
        "id": f"artifact_{art_id.replace('-', '_')}",
        "title": f"{name} — Artifact Set Bonuses & Piece Details",
        "metadata": {
            "source": "Genshin Impact Community Wiki (genshin.jmp.blue)",
            "source_url": f"https://genshin-impact.fandom.com/wiki/{name.replace(' ', '_').replace(\"'\", '%27')}",
            "source_type": "AUTHORITATIVE",
            "character": None,
            "topic": "Artifact Set",
            "game_version": "5.4",
            "published_at": "2020-09-28T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tags": [name, "Artifact", "Set Bonus"],
        },
        "summary": summary,
        "content": content,
    }


def save_doc(doc: dict, filename: str):
    """Save a knowledge document as JSON."""
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)


def main():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

    # ── Fetch Characters ──
    print("Fetching character list...")
    char_ids = fetch_json(f"{BASE_URL}/characters")
    if not char_ids:
        print("ERROR: Failed to fetch character list.")
        return

    print(f"Found {len(char_ids)} characters. Fetching details...")
    char_count = 0
    for i, cid in enumerate(char_ids):
        print(f"  [{i+1}/{len(char_ids)}] {cid}...", end=" ")
        data = fetch_json(f"{BASE_URL}/characters/{cid}")
        if data:
            doc = create_character_doc(cid, data)
            save_doc(doc, f"wiki_{cid.replace('-', '_')}.json")
            char_count += 1
            print("OK")
        else:
            print("FAILED")
        time.sleep(0.3)  # Rate limit courtesy

    print(f"\nCharacters saved: {char_count}/{len(char_ids)}")

    # ── Fetch Artifacts ──
    print("\nFetching artifact set list...")
    art_ids = fetch_json(f"{BASE_URL}/artifacts")
    if not art_ids:
        print("ERROR: Failed to fetch artifact list.")
        return

    print(f"Found {len(art_ids)} artifact sets. Fetching details...")
    art_count = 0
    for i, aid in enumerate(art_ids):
        print(f"  [{i+1}/{len(art_ids)}] {aid}...", end=" ")
        data = fetch_json(f"{BASE_URL}/artifacts/{aid}")
        if data:
            doc = create_artifact_doc(aid, data)
            save_doc(doc, f"artifact_{aid.replace('-', '_')}.json")
            art_count += 1
            print("OK")
        else:
            print("FAILED")
        time.sleep(0.3)

    print(f"\nArtifact sets saved: {art_count}/{len(art_ids)}")
    print(f"\n{'='*50}")
    print(f"TOTAL: {char_count} characters + {art_count} artifact sets = {char_count + art_count} knowledge documents")
    print(f"Saved to: {KNOWLEDGE_DIR}")


if __name__ == "__main__":
    main()

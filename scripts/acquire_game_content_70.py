"""
GenshinIQ — Game Content Acquisition & Normalization Pipeline for Version 7.0
Authoritative source: Dimbreath / AnimeGameData / GenshinData (PRIMARY_ORIGINAL)
Acquires real raw game content tables and resolves combined TextMapEN + TextMap_MediumEN strings to produce:
- quests.json
- events.json
- domains.json
- enemies.json
- regions.json
- achievements.json
- recipes.json
"""

import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw" / "game_data" / "versions" / "7.0"
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "game_data" / "versions" / "7.0"
PROCESSED_ROOT = ROOT_DIR / "data" / "processed" / "game_data"

RAW_BASE_URL = "https://raw.githubusercontent.com/DimbreathBot/AnimeGameData/main/ExcelBinOutput/"
TEXTMAP_URL = "https://raw.githubusercontent.com/DimbreathBot/AnimeGameData/main/TextMap/TextMapEN.json"
TEXTMAP_MEDIUM_URL = "https://raw.githubusercontent.com/DimbreathBot/AnimeGameData/main/TextMap/TextMap_MediumEN.json"

RAW_TABLES = [
    "ChapterExcelConfigData.json",
    "MainQuestExcelConfigData.json",
    "DungeonExcelConfigData.json",
    "DailyDungeonConfigData.json",
    "MonsterDescribeExcelConfigData.json",
    "CityConfigData.json",
    "WorldAreaConfigData.json",
    "AchievementExcelConfigData.json",
    "CookRecipeExcelConfigData.json",
    "NewActivityExcelConfigData.json",
]

HEADERS = {"User-Agent": "GenshinIQ-CanonicalPipeline/1.0"}


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 0:
        print(f"File already exists: {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True
    
    for attempt in range(max_retries):
        try:
            print(f"Downloading {url} (attempt {attempt + 1})...")
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(data)
            print(f"Saved {dest_path.name} ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            time.sleep(2)
    return False


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download raw tables
    print("=== STEP 1: Acquiring raw ExcelBinOutput tables ===")
    for table_name in RAW_TABLES:
        url = RAW_BASE_URL + table_name
        dest = RAW_DIR / table_name
        ok = download_file(url, dest)
        if not ok:
            print(f"CRITICAL: Failed to download {table_name}")
            return

    # 2. Download and load TextMaps (TextMap_MediumEN + TextMapEN)
    print("=== STEP 2: Loading TextMaps ===")
    textmap_path = RAW_DIR / "TextMapEN.json"
    download_file(TEXTMAP_URL, textmap_path)

    textmap_med_path = RAW_DIR / "TextMap_MediumEN.json"
    download_file(TEXTMAP_MEDIUM_URL, textmap_med_path)

    print("Loading TextMap_MediumEN and TextMapEN into memory...")
    with open(textmap_med_path, "r", encoding="utf-8") as f:
        textmap: Dict[str, str] = json.load(f)
    print(f"Loaded TextMap_MediumEN with {len(textmap)} entries.")

    with open(textmap_path, "r", encoding="utf-8") as f:
        tm_en = json.load(f)
    print(f"Loaded TextMapEN with {len(tm_en)} entries.")
    
    # Merge: update with dialogue/quest strings
    textmap.update(tm_en)
    print(f"Combined TextMap has {len(textmap)} unique text hashes.")

    def get_text(h: Any, fallback: str = "") -> str:
        if h is None:
            return fallback
        h_str = str(h)
        val = textmap.get(h_str)
        if val is not None and val.strip():
            cleaned = val.replace("\\n", " ").replace("\n", " ").strip()
            return cleaned
        return fallback

    # 3. Process Quests (ChapterExcelConfigData + MainQuestExcelConfigData)
    print("=== STEP 3: Normalizing Quests ===")
    with open(RAW_DIR / "ChapterExcelConfigData.json", "r", encoding="utf-8") as f:
        chapters = json.load(f)
    with open(RAW_DIR / "MainQuestExcelConfigData.json", "r", encoding="utf-8") as f:
        main_quests = json.load(f)

    # Map chapter info
    chapter_map = {}
    for c in chapters:
        cid = c.get("id")
        title = get_text(c.get("chapterTitleTextMapHash"), "")
        num = get_text(c.get("chapterNumTextMapHash"), "")
        if cid and title:
            chapter_map[cid] = {"title": title, "num": num, "city_id": c.get("cityId")}

    processed_quests = []
    seen_quest_titles = set()
    for q in main_quests:
        qid = q.get("id")
        title = get_text(q.get("titleTextMapHash"), "")
        desc = get_text(q.get("descTextMapHash"), "")
        chapter_id = q.get("chapterId")
        chapter_info = chapter_map.get(chapter_id, {})
        
        if qid and title and title not in seen_quest_titles:
            seen_quest_titles.add(title)
            processed_quests.append({
                "id": qid,
                "title": title,
                "description": desc,
                "type": q.get("type", "AQ"),
                "chapter_id": chapter_id,
                "chapter_title": chapter_info.get("title", ""),
                "chapter_num": chapter_info.get("num", ""),
                "game_version_introduced": "7.0"
            })

    print(f"Normalized {len(processed_quests)} unique quests.")

    # 4. Process Events (NewActivityExcelConfigData)
    print("=== STEP 4: Normalizing Events ===")
    with open(RAW_DIR / "NewActivityExcelConfigData.json", "r", encoding="utf-8") as f:
        activities = json.load(f)
    
    processed_events = []
    seen_event_names = set()
    for act in activities:
        aid = act.get("activityId")
        name = get_text(act.get("nameTextMapHash"), "")
        atype = act.get("activityType", "")
        if aid and name and name not in seen_event_names:
            seen_event_names.add(name)
            processed_events.append({
                "id": aid,
                "name": name,
                "activity_type": atype,
                "cond_group_id": act.get("condGroupId"),
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_events)} unique events.")

    # 5. Process Domains (DungeonExcelConfigData + DailyDungeonConfigData)
    print("=== STEP 5: Normalizing Domains ===")
    with open(RAW_DIR / "DungeonExcelConfigData.json", "r", encoding="utf-8") as f:
        dungeons = json.load(f)
    with open(RAW_DIR / "DailyDungeonConfigData.json", "r", encoding="utf-8") as f:
        daily_dungeons = json.load(f)

    # Build daily dungeon set
    daily_dungeon_ids = {dd.get("dungeonId") for dd in daily_dungeons if dd.get("dungeonId")}

    processed_domains = []
    seen_domain_ids = set()
    for d in dungeons:
        did = d.get("id")
        name = get_text(d.get("displayNameTextMapHash"), "") or get_text(d.get("nameTextMapHash"), "")
        dtype = d.get("type", "")
        desc = get_text(d.get("descTextMapHash"), "")
        if did and name and did not in seen_domain_ids:
            seen_domain_ids.add(did)
            processed_domains.append({
                "id": did,
                "name": name,
                "type": dtype,
                "description": desc,
                "is_daily_rotation": did in daily_dungeon_ids,
                "recommend_level": d.get("showLevel") or d.get("recommendLevel", 0),
                "pass_cond": d.get("passCond", 0),
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_domains)} unique domains.")

    # 6. Process Enemies & Bosses (MonsterDescribeExcelConfigData)
    print("=== STEP 6: Normalizing Enemies ===")
    with open(RAW_DIR / "MonsterDescribeExcelConfigData.json", "r", encoding="utf-8") as f:
        monsters = json.load(f)

    processed_enemies = []
    seen_enemy_names = set()
    for m in monsters:
        mid = m.get("id")
        name = get_text(m.get("nameTextMapHash"), "")
        title = get_text(m.get("titleID"), "")
        special_name = get_text(m.get("specialNameLabID"), "")
        icon = m.get("icon", "")
        if mid and name and name not in seen_enemy_names:
            seen_enemy_names.add(name)
            processed_enemies.append({
                "id": mid,
                "name": name,
                "title": title or special_name,
                "icon": icon,
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_enemies)} unique enemies.")

    # 7. Process Regions & Areas (CityConfigData + WorldAreaConfigData)
    print("=== STEP 7: Normalizing Regions ===")
    with open(RAW_DIR / "CityConfigData.json", "r", encoding="utf-8") as f:
        cities = json.load(f)
    with open(RAW_DIR / "WorldAreaConfigData.json", "r", encoding="utf-8") as f:
        areas = json.load(f)

    area_map = {}
    for a in areas:
        aid = a.get("ID") or a.get("id")
        aname = get_text(a.get("AreaNameTextMapHash"), "")
        if aid and aname:
            area_map[aid] = aname

    processed_regions = []
    seen_region_names = set()
    for c in cities:
        cid = c.get("cityId")
        cname = get_text(c.get("cityNameTextMapHash"), "")
        area_ids = c.get("areaIdVec", [])
        area_names = [area_map[aid] for aid in area_ids if aid in area_map]
        if cid and cname and cname not in seen_region_names:
            seen_region_names.add(cname)
            processed_regions.append({
                "id": cid,
                "name": cname,
                "area_ids": area_ids,
                "area_names": area_names,
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_regions)} unique regions.")

    # 8. Process Achievements (AchievementExcelConfigData)
    print("=== STEP 8: Normalizing Achievements ===")
    with open(RAW_DIR / "AchievementExcelConfigData.json", "r", encoding="utf-8") as f:
        achievements = json.load(f)

    processed_achievements = []
    seen_achieve_ids = set()
    for ach in achievements:
        aid = ach.get("id")
        title = get_text(ach.get("titleTextMapHash"), "")
        desc = get_text(ach.get("descTextMapHash"), "")
        if aid and title and aid not in seen_achieve_ids:
            seen_achieve_ids.add(aid)
            processed_achievements.append({
                "id": aid,
                "title": title,
                "description": desc,
                "goal_id": ach.get("goalId"),
                "progress": ach.get("progress", 1),
                "finish_reward_id": ach.get("finishRewardId"),
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_achievements)} unique achievements.")

    # 9. Process Recipes & Crafting (CookRecipeExcelConfigData)
    print("=== STEP 9: Normalizing Recipes ===")
    with open(RAW_DIR / "CookRecipeExcelConfigData.json", "r", encoding="utf-8") as f:
        recipes = json.load(f)

    processed_recipes = []
    seen_recipe_ids = set()
    for r in recipes:
        rid = r.get("id")
        name = get_text(r.get("nameTextMapHash"), "")
        desc = get_text(r.get("descTextMapHash"), "")
        effect_list = r.get("effectDesc", [])
        effect_str = ", ".join(get_text(e) for e in effect_list if get_text(e)) if isinstance(effect_list, list) else get_text(effect_list)
        if rid and name and rid not in seen_recipe_ids:
            seen_recipe_ids.add(rid)
            processed_recipes.append({
                "id": rid,
                "name": name,
                "description": desc,
                "effect": effect_str,
                "food_type": r.get("foodType", ""),
                "rank_level": r.get("rankLevel", 1),
                "icon": r.get("icon", ""),
                "game_version_introduced": "7.0"
            })
    print(f"Normalized {len(processed_recipes)} unique recipes.")

    # Write processed files to version directory and processed root
    catalogs = {
        "quests.json": processed_quests,
        "events.json": processed_events,
        "domains.json": processed_domains,
        "enemies.json": processed_enemies,
        "regions.json": processed_regions,
        "achievements.json": processed_achievements,
        "recipes.json": processed_recipes,
    }

    for fname, data in catalogs.items():
        v_dest = PROCESSED_DIR / fname
        root_dest = PROCESSED_ROOT / fname
        with open(v_dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        with open(root_dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(data)} items to {fname}")

    # Update raw manifest
    raw_manifest_path = RAW_DIR / "raw_manifest.json"
    with open(raw_manifest_path, "r", encoding="utf-8") as f:
        raw_manifest = json.load(f)

    all_raw_files = RAW_TABLES + ["TextMapEN.json", "TextMap_MediumEN.json"]
    for tname in all_raw_files:
        p = RAW_DIR / tname
        if p.exists():
            with open(p, "rb") as f:
                content = f.read()
            raw_manifest["record_counts"][tname] = len(json.loads(content.decode("utf-8"))) if tname.endswith(".json") else 0
            raw_manifest["file_hashes"][tname] = hashlib.sha256(content).hexdigest()

    with open(raw_manifest_path, "w", encoding="utf-8") as f:
        json.dump(raw_manifest, f, indent=2)
    print("Updated raw_manifest.json")

    # Update version manifest
    v_manifest_path = PROCESSED_DIR / "version_manifest.json"
    with open(v_manifest_path, "r", encoding="utf-8") as f:
        v_manifest = json.load(f)

    for fname, data in catalogs.items():
        p = PROCESSED_DIR / fname
        with open(p, "rb") as f:
            content = f.read()
        v_manifest["record_counts"][fname] = len(data)
        v_manifest["file_hashes"][fname] = hashlib.sha256(content).hexdigest()

    with open(v_manifest_path, "w", encoding="utf-8") as f:
        json.dump(v_manifest, f, indent=2)
    print("Updated version_manifest.json")

    print("=== ACQUISITION & NORMALIZATION COMPLETE ===")


if __name__ == "__main__":
    main()

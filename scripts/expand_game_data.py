"""Expand game_data JSONs with comprehensive Genshin Impact entries matching Pydantic models."""
import json
import os

BASE = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "game_data"
)

# ── New Characters to ADD (These validated fine, but let's keep them correct) ──────────────────────────
NEW_CHARACTERS = [
    {
        "id": 10000052, "name": "Kaedehara Kazuha", "title": "Scarlet Leaves Pursue Wild Waves",
        "element": "Anemo", "weapon_type": "Sword", "rarity": 5, "region": "Inazuma",
        "affiliation": "Crux Fleet", "description": "A wandering samurai from Inazuma, now with the Crux Fleet.",
        "base_hp_lvl90": 13348.0, "base_atk_lvl90": 297.0, "base_def_lvl90": 807.0,
        "ascension_stat": "Elemental Mastery", "ascension_stat_val_lvl90": "115.2",
        "icon": "UI_AvatarIcon_Kazuha",
        "talents": [
            {"name": "Garyuu Bladework", "unlock": "Normal Attack", "type": "normal", "description": "Performs up to 5 rapid strikes."},
            {"name": "Chihayaburu", "unlock": "Elemental Skill", "type": "skill", "description": "Launches opponents in the area, pulling nearby objects."},
            {"name": "Kazuha Slash", "unlock": "Elemental Burst", "type": "burst", "description": "Fires an Autumn Whirlwind blade dealing AoE Anemo DMG."},
            {"name": "Soumon Swordsmanship", "unlock": "1st Ascension Passive", "type": "passive", "description": "Midair Plunging Attack after Chihayaburu."},
            {"name": "Poetics of Fuubutsu", "unlock": "4th Ascension Passive", "type": "passive", "description": "Swirl grants 0.04% Elemental DMG Bonus per EM point."}
        ],
        "constellations": [
            {"level": 1, "name": "Scarlet Hills", "description": "Chihayaburu CD reset on Elemental Reaction."},
            {"level": 2, "name": "Yamaarashi Tailwind", "description": "Autumn Whirlwind field grants 200 EM."},
            {"level": 3, "name": "Maple Monogatari", "description": "+3 Chihayaburu Level."},
            {"level": 4, "name": "Oozora Genpou", "description": "Energy gain when below 45 Energy."},
            {"level": 5, "name": "Wisdom of Bansei", "description": "+3 Kazuha Slash Level."},
            {"level": 6, "name": "Crimson Momiji", "description": "Anemo Infusion for 5s; EM increases ATK DMG by 0.2%."}
        ]
    },
    {
        "id": 10000051, "name": "Eula", "title": "Dance of the Shimmering Wave",
        "element": "Cryo", "weapon_type": "Claymore", "rarity": 5, "region": "Mondstadt",
        "affiliation": "Knights of Favonius", "description": "The Spindrift Knight, Captain of the Reconnaissance Company.",
        "base_hp_lvl90": 13226.0, "base_atk_lvl90": 342.0, "base_def_lvl90": 751.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Eula",
        "talents": [
            {"name": "Favonius Bladework - Edel", "unlock": "Normal Attack", "type": "normal", "description": "Up to 5 consecutive strikes."},
            {"name": "Icetide Vortex", "unlock": "Elemental Skill", "type": "skill", "description": "Gains Grimheart stacks; Hold consumes them for AoE Cryo DMG."},
            {"name": "Glacial Illumination", "unlock": "Elemental Burst", "type": "burst", "description": "Creates a Lightfall Sword that explodes for massive Physical DMG."},
            {"name": "Roiling Rime", "unlock": "1st Ascension Passive", "type": "passive", "description": "Shattered Lightfall Sword at 2 Grimheart stacks."},
            {"name": "Wellspring of War-Lust", "unlock": "4th Ascension Passive", "type": "passive", "description": "Burst resets Skill CD and grants Grimheart."}
        ],
        "constellations": [
            {"level": 1, "name": "Tidal Illusion", "description": "Grimheart grants 30% Physical DMG per stack."},
            {"level": 2, "name": "Lady of Seafoam", "description": "Hold CD matches Press CD."},
            {"level": 3, "name": "Lawrence Pedigree", "description": "+3 Glacial Illumination Level."},
            {"level": 4, "name": "The Obstinacy of One's Inferiors", "description": "+25% DMG vs <50% HP."},
            {"level": 5, "name": "Chivalric Quality", "description": "+3 Icetide Vortex Level."},
            {"level": 6, "name": "Noble Obligation", "description": "Start with 5 energy stacks; 50% chance for extra."}
        ]
    },
    {
        "id": 10000037, "name": "Ganyu", "title": "Plenilune Gaze",
        "element": "Cryo", "weapon_type": "Bow", "rarity": 5, "region": "Liyue",
        "affiliation": "Liyue Qixing", "description": "Secretary to the Liyue Qixing, a half-qilin adeptus.",
        "base_hp_lvl90": 9797.0, "base_atk_lvl90": 335.0, "base_def_lvl90": 630.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Ganyu",
        "talents": [
            {"name": "Liutian Archery", "unlock": "Normal Attack", "type": "normal", "description": "Up to 6 shots; Charged shots deal Cryo via Frostflake Arrows."},
            {"name": "Trail of the Qilin", "unlock": "Elemental Skill", "type": "skill", "description": "Ice Lotus taunts enemies and deals AoE Cryo DMG."},
            {"name": "Celestial Shower", "unlock": "Elemental Burst", "type": "burst", "description": "Sacred Cryo Pearl rains ice shards for continuous Cryo AoE DMG."},
            {"name": "Undivided Heart", "unlock": "1st Ascension Passive", "type": "passive", "description": "+20% CRIT Rate for Frostflake Arrows for 5s."},
            {"name": "Harmony between Heaven and Earth", "unlock": "4th Ascension Passive", "type": "passive", "description": "+20% Cryo DMG Bonus in burst AoE."}
        ],
        "constellations": [
            {"level": 1, "name": "Dew-Drinker", "description": "-15% Cryo RES; +2 Energy on hit."},
            {"level": 2, "name": "The Auspicious", "description": "+1 Skill charge."},
            {"level": 3, "name": "Cloud-Strider", "description": "+3 Celestial Shower Level."},
            {"level": 4, "name": "Westward Sojourn", "description": "+25% DMG in burst AoE over 3s."},
            {"level": 5, "name": "The Merciful", "description": "+3 Trail of the Qilin Level."},
            {"level": 6, "name": "The Clement", "description": "Instant Frostflake Arrow after Skill."}
        ]
    },
    {
        "id": 10000046, "name": "Hu Tao", "title": "Fragrance in Thaw",
        "element": "Pyro", "weapon_type": "Polearm", "rarity": 5, "region": "Liyue",
        "affiliation": "Wangsheng Funeral Parlor", "description": "The 77th Director of the Wangsheng Funeral Parlor.",
        "base_hp_lvl90": 15552.0, "base_atk_lvl90": 106.0, "base_def_lvl90": 876.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Hutao",
        "talents": [
            {"name": "Secret Spear of Wangsheng", "unlock": "Normal Attack", "type": "normal", "description": "Up to 6 spear strikes."},
            {"name": "Guide to Afterlife", "unlock": "Elemental Skill", "type": "skill", "description": "Enters Paramita Papilio, gaining Pyro infusion and Blood Blossom."},
            {"name": "Spirit Soother", "unlock": "Elemental Burst", "type": "burst", "description": "Massive AoE Pyro DMG, heals at low HP."},
            {"name": "Flutter By", "unlock": "1st Ascension Passive", "type": "passive", "description": "No Stamina cost for Charged Attacks in Paramita Papilio."},
            {"name": "Sanguine Rouge", "unlock": "4th Ascension Passive", "type": "passive", "description": "+33% Pyro DMG Bonus below 50% HP."}
        ],
        "constellations": [
            {"level": 1, "name": "Crimson Bouquet", "description": "No Stamina cost for Charged Attacks."},
            {"level": 2, "name": "Ominous Rainfall", "description": "Blood Blossom scales with Max HP; Burst applies it."},
            {"level": 3, "name": "Lingering Carmine", "description": "+3 Guide to Afterlife Level."},
            {"level": 4, "name": "Garden of Eternal Rest", "description": "+12% party CRIT Rate on kill."},
            {"level": 5, "name": "Floral Incense", "description": "+3 Spirit Soother Level."},
            {"level": 6, "name": "Butterfly's Embrace", "description": "Survive lethal blow once/60s with 200% CRIT Rate."}
        ]
    },
    {
        "id": 10000047, "name": "Kamisato Ayaka", "title": "Frostflake Heron",
        "element": "Cryo", "weapon_type": "Sword", "rarity": 5, "region": "Inazuma",
        "affiliation": "Kamisato Clan", "description": "Daughter of the Yashiro Commission's Kamisato Clan.",
        "base_hp_lvl90": 12858.0, "base_atk_lvl90": 342.0, "base_def_lvl90": 784.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Ayaka",
        "talents": [
            {"name": "Kamisato Art - Kabuki", "unlock": "Normal Attack", "type": "normal", "description": "Up to 5 rapid strikes."},
            {"name": "Kamisato Art - Hyouka", "unlock": "Elemental Skill", "type": "skill", "description": "AoE Cryo DMG ice bloom."},
            {"name": "Kamisato Art - Soumetsu", "unlock": "Elemental Burst", "type": "burst", "description": "Frostflake Seki no To deals multi-hit Cryo DMG."},
            {"name": "Amatsumi Kunitsumi Sanctification", "unlock": "1st Ascension Passive", "type": "passive", "description": "+30% Normal/Charged DMG after Skill for 6s."},
            {"name": "Kanten Senmyou Blessing", "unlock": "4th Ascension Passive", "type": "passive", "description": "+18% Cryo DMG Bonus from Sprint for 10s."}
        ],
        "constellations": [
            {"level": 1, "name": "Snowswept Sakura", "description": "50% chance to reduce Skill CD by 0.3s."},
            {"level": 2, "name": "Blizzard Blade Seki no To", "description": "Two smaller Seki no To at 20% DMG."},
            {"level": 3, "name": "Frostbloom Kamifubuki", "description": "+3 Soumetsu Level."},
            {"level": 4, "name": "Ebb and Flow", "description": "-30% DEF on Seki no To hit."},
            {"level": 5, "name": "Blossom Cloud Irutsuki", "description": "+3 Hyouka Level."},
            {"level": 6, "name": "Dance of Suigetsu", "description": "+298% Charged Attack DMG every 10s."}
        ]
    },
    {
        "id": 10000058, "name": "Yae Miko", "title": "Astute Amusement",
        "element": "Electro", "weapon_type": "Catalyst", "rarity": 5, "region": "Inazuma",
        "affiliation": "Grand Narukami Shrine", "description": "Lady Guuji of the Grand Narukami Shrine.",
        "base_hp_lvl90": 10372.0, "base_atk_lvl90": 340.0, "base_def_lvl90": 569.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Yae",
        "talents": [
            {"name": "Spiritfox Sin-Eater", "unlock": "Normal Attack", "type": "normal", "description": "Kitsune spirits for up to 3 Electro DMG attacks."},
            {"name": "Yakan Evocation: Sesshou Sakura", "unlock": "Elemental Skill", "type": "skill", "description": "Leaves Sesshou Sakura that periodically strike with Electro DMG."},
            {"name": "Great Secret Art: Tenko Kenshin", "unlock": "Elemental Burst", "type": "burst", "description": "Destroys all Sesshou Sakura for AoE Electro DMG."},
            {"name": "The Shrine's Sacred Shade", "unlock": "1st Ascension Passive", "type": "passive", "description": "Burst resets Sesshou Sakura CD."},
            {"name": "Enlightened Blessing", "unlock": "4th Ascension Passive", "type": "passive", "description": "EM increases Sesshou Sakura DMG by 0.15% per point."}
        ],
        "constellations": [
            {"level": 1, "name": "Yakan Offering", "description": "Burst restores 8 Energy."},
            {"level": 2, "name": "Fox's Mooncall", "description": "Sesshou Sakura start at Level 2."},
            {"level": 3, "name": "The Seven Glamours", "description": "+3 Sesshou Sakura Level."},
            {"level": 4, "name": "Sakura Channeling", "description": "+20% Electro DMG Bonus for 5s."},
            {"level": 5, "name": "Mischievous Teasing", "description": "+3 Tenko Kenshin Level."},
            {"level": 6, "name": "Forbidden Art: Daisesshou", "description": "Sesshou Sakura ignore 60% DEF."}
        ]
    },
    {
        "id": 10000060, "name": "Yelan", "title": "Valley Orchid",
        "element": "Hydro", "weapon_type": "Bow", "rarity": 5, "region": "Liyue",
        "affiliation": "Ministry of Civil Affairs", "description": "A mysterious intelligence officer of the Liyue Qixing.",
        "base_hp_lvl90": 14450.0, "base_atk_lvl90": 244.0, "base_def_lvl90": 548.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Yelan",
        "talents": [
            {"name": "Stealthy Bowshot", "unlock": "Normal Attack", "type": "normal", "description": "Up to 4 rapid shots."},
            {"name": "Lingering Lifeline", "unlock": "Elemental Skill", "type": "skill", "description": "Fires a Lifeline marking and dealing Hydro DMG."},
            {"name": "Depth-Clarion Dice", "unlock": "Elemental Burst", "type": "burst", "description": "AoE Hydro DMG; coordinates with Normal Attacks."},
            {"name": "Turn Control", "unlock": "1st Ascension Passive", "type": "passive", "description": "+6/12/18/30% Max HP based on party element types."},
            {"name": "Adapt With Ease", "unlock": "4th Ascension Passive", "type": "passive", "description": "Burst increases active character DMG by 1-50% over 14s."}
        ],
        "constellations": [
            {"level": 1, "name": "Enter the Plotters", "description": "+1 Skill charge."},
            {"level": 2, "name": "Taking All Comers", "description": "Extra water arrow at 14% Max HP."},
            {"level": 3, "name": "Beware the Trickster's Dice", "description": "+3 Burst Level."},
            {"level": 4, "name": "Bait-and-Switch", "description": "+10% Max HP per marked enemy, up to 40%."},
            {"level": 5, "name": "Dealer's Sleight", "description": "+3 Skill Level."},
            {"level": 6, "name": "Winner Takes All", "description": "Mastermind state with Breakthrough Barbs."}
        ]
    },
    {
        "id": 10000078, "name": "Alhaitham", "title": "Empyrean Reflection",
        "element": "Dendro", "weapon_type": "Sword", "rarity": 5, "region": "Sumeru",
        "affiliation": "Akademiya", "description": "The current Scribe of the Sumeru Akademiya.",
        "base_hp_lvl90": 13348.0, "base_atk_lvl90": 313.0, "base_def_lvl90": 782.0,
        "ascension_stat": "Dendro DMG Bonus", "ascension_stat_val_lvl90": "28.8%",
        "icon": "UI_AvatarIcon_Alhatham",
        "talents": [
            {"name": "Abductive Reasoning", "unlock": "Normal Attack", "type": "normal", "description": "Up to 5 rapid sword strikes."},
            {"name": "Universality: An Elaboration on Form", "unlock": "Elemental Skill", "type": "skill", "description": "Creates Chisel-Light Mirrors projecting Dendro DMG."},
            {"name": "Particular Field: Fetters of Phenomena", "unlock": "Elemental Burst", "type": "burst", "description": "Multi-hit AoE Dendro DMG generating Mirrors."},
            {"name": "Four-Causal Correction", "unlock": "1st Ascension Passive", "type": "passive", "description": "Charged/Plunging Attacks generate Mirrors (10s CD)."},
            {"name": "Mysteries Laid Bare", "unlock": "4th Ascension Passive", "type": "passive", "description": "EM increases Mirror DMG by 0.1% per point."}
        ],
        "constellations": [
            {"level": 1, "name": "Intuition", "description": "Mirror hits reduce Skill CD by 1.2s."},
            {"level": 2, "name": "Debate", "description": "+50 EM per Mirror, max 4 stacks."},
            {"level": 3, "name": "Negation", "description": "+3 Skill Level."},
            {"level": 4, "name": "Elucidation", "description": "+30 party EM per Mirror, up to +120."},
            {"level": 5, "name": "Sagacity", "description": "+3 Burst Level."},
            {"level": 6, "name": "Structuration", "description": "+10/20/30% CRIT Rate by Mirror count."}
        ]
    },
    {
        "id": 10000091, "name": "Navia", "title": "Helm of the Radiant Rose",
        "element": "Geo", "weapon_type": "Claymore", "rarity": 5, "region": "Fontaine",
        "affiliation": "Spina di Rosula", "description": "The head of Spina di Rosula, a passionate free-spirited leader.",
        "base_hp_lvl90": 12650.0, "base_atk_lvl90": 352.0, "base_def_lvl90": 793.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Navia",
        "talents": [
            {"name": "Blunt Refusal", "unlock": "Normal Attack", "type": "normal", "description": "Up to 4 rapid claymore strikes."},
            {"name": "Ceremonial Crystalshot", "unlock": "Elemental Skill", "type": "skill", "description": "Fires Rosula Shardshots dealing Geo DMG."},
            {"name": "As the Sunlit Sky's Singing Salute", "unlock": "Elemental Burst", "type": "burst", "description": "Fires an Artillery Shell for AoE Geo DMG."},
            {"name": "Undisclosed Distribution Channels", "unlock": "1st Ascension Passive", "type": "passive", "description": "Crystal Shell stacks increase Skill DMG."},
            {"name": "Mutual Assistance Network", "unlock": "4th Ascension Passive", "type": "passive", "description": "+20% Skill DMG per Pyro/Electro/Cryo/Hydro member, max +40%."}
        ],
        "constellations": [
            {"level": 1, "name": "A Lady's Rules for Keeping a Courteous Distance", "description": "+3 Energy per Crystal Shell consumed."},
            {"level": 2, "name": "The President's Pursuit of Victory", "description": "+20% ATK per hit, max 5 stacks."},
            {"level": 3, "name": "Businesswoman's Broad Vision", "description": "+3 Skill Level."},
            {"level": 4, "name": "The Oathsworn Never Capitulate", "description": "-20% Geo RES for 8s on Skill hit."},
            {"level": 5, "name": "Negotiator's Resolute Negotiations", "description": "+3 Burst Level."},
            {"level": 6, "name": "The Flexible Tenets of the Spina's President", "description": "+12% CRIT Rate, +28% CRIT DMG per extra Shell."}
        ]
    },
    {
        "id": 10000095, "name": "Clorinde", "title": "Candlebearer, Shadowhunter",
        "element": "Electro", "weapon_type": "Sword", "rarity": 5, "region": "Fontaine",
        "affiliation": "Maison Gardiennage", "description": "A Champions Duelist of the Court of Fontaine.",
        "base_hp_lvl90": 13289.0, "base_atk_lvl90": 337.0, "base_def_lvl90": 784.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Clorinde",
        "talents": [
            {"name": "Oath of Hunting Shadows", "unlock": "Normal Attack", "type": "normal", "description": "Up to 5 rapid strikes."},
            {"name": "Hunter's Vigil", "unlock": "Elemental Skill", "type": "skill", "description": "Night Vigil state with Electro gunblade strikes."},
            {"name": "Last Lightfall", "unlock": "Elemental Burst", "type": "burst", "description": "Devastating AoE Electro DMG."},
            {"name": "Dark-Shattering Flame", "unlock": "1st Ascension Passive", "type": "passive", "description": "Night Vigil gains bonus DMG at high Bond of Life."},
            {"name": "Lawful Remuneration", "unlock": "4th Ascension Passive", "type": "passive", "description": "Bond of Life increases Night Vigil attack DMG."}
        ],
        "constellations": [
            {"level": 1, "name": "From This Day, I Pass the Candle's Shadow-Loss", "description": "+30% Night Vigil DMG during Bond of Life."},
            {"level": 2, "name": "Now, as We Face the Perils of the Long Night", "description": "+15% CRIT Rate, +30% CRIT DMG vs <50% HP."},
            {"level": 3, "name": "I Pledge to Remember theErta of Days Past", "description": "+3 Skill Level."},
            {"level": 4, "name": "To Etch the Souls of the Blameless in Stone", "description": "+20% party ATK for 15s after Burst."},
            {"level": 5, "name": "Holding Dawn's Coming in My Hands", "description": "+3 Burst Level."},
            {"level": 6, "name": "And So Shall I Never Despair", "description": "+10% CRIT Rate, +100% CRIT DMG in Night Vigil."}
        ]
    },
    {
        "id": 10000086, "name": "Wriothesley", "title": "Emissary of Solitary Iniquity",
        "element": "Cryo", "weapon_type": "Catalyst", "rarity": 5, "region": "Fontaine",
        "affiliation": "Fortress of Meropide", "description": "The Duke of the Fortress of Meropide.",
        "base_hp_lvl90": 13593.0, "base_atk_lvl90": 228.0, "base_def_lvl90": 900.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Wriothesley",
        "talents": [
            {"name": "Forceful Fists of Frost", "unlock": "Normal Attack", "type": "normal", "description": "Frost boxing for up to 5 rapid strikes."},
            {"name": "Icefang Rush", "unlock": "Elemental Skill", "type": "skill", "description": "Chilling Penalty state with Cryo-infused combos."},
            {"name": "Darkgold Wolfbite", "unlock": "Elemental Burst", "type": "burst", "description": "Massive Cryo uppercut AoE DMG."},
            {"name": "There Shall Be a Plea for Justice", "unlock": "1st Ascension Passive", "type": "passive", "description": "Bonus DMG below 60% HP during Chilling Penalty."},
            {"name": "There Shall Be a Reckoning for Sin", "unlock": "4th Ascension Passive", "type": "passive", "description": "HP changes grant CRIT Rate."}
        ],
        "constellations": [
            {"level": 1, "name": "Terror for the Evildoers", "description": "Enhanced attacks heal Wriothesley."},
            {"level": 2, "name": "Shackles for the Arrogant", "description": "+40% Burst DMG per Prosecution Edict stack."},
            {"level": 3, "name": "Imprisonment for the Offenders", "description": "+3 Skill Level."},
            {"level": 4, "name": "Redemption for the Suffering", "description": "+8 Energy; +80% next Charged Attack DMG."},
            {"level": 5, "name": "Mercy for the Wronged", "description": "+3 Burst Level."},
            {"level": 6, "name": "Esteem for the Innocent", "description": "+10% CRIT Rate, +80% CRIT DMG during Chilling Penalty."}
        ]
    },
    {
        "id": 10000084, "name": "Lyney", "title": "Spectacle of Phantasmagoria",
        "element": "Pyro", "weapon_type": "Bow", "rarity": 5, "region": "Fontaine",
        "affiliation": "Hotel Bouffes d'ete", "description": "A famous magician in Fontaine.",
        "base_hp_lvl90": 10309.0, "base_atk_lvl90": 334.0, "base_def_lvl90": 542.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Lyney",
        "talents": [
            {"name": "Card Force Translocation", "unlock": "Normal Attack", "type": "normal", "description": "Up to 4 shots; Charged shots fire Prop Arrows."},
            {"name": "Bewildering Lights", "unlock": "Elemental Skill", "type": "skill", "description": "Grin-Malkin Cat dealing AoE Pyro DMG."},
            {"name": "Wondrous Trick: Miracle Parade", "unlock": "Elemental Burst", "type": "burst", "description": "Continuous Pyro DMG along path; increases Prop Surplus."},
            {"name": "Perilous Performance", "unlock": "1st Ascension Passive", "type": "passive", "description": "+20% Pyro DMG Bonus at <=60% HP."},
            {"name": "Conclusive Ovation", "unlock": "4th Ascension Passive", "type": "passive", "description": "+60/80/100% ATK per Pyro member using Prop Arrow."}
        ],
        "constellations": [
            {"level": 1, "name": "Whimsical Wonders", "description": "+1 extra Prop Arrow."},
            {"level": 2, "name": "Loquacious Precision", "description": "+20% CRIT DMG; +20% more on Pyro reaction."},
            {"level": 3, "name": "Prestidigitation", "description": "+3 Burst Level."},
            {"level": 4, "name": "Well-Versed, Well-Rehearsed", "description": "-20% Pyro RES for 6s."},
            {"level": 5, "name": "To Pierce Enigmas", "description": "+3 Skill Level."},
            {"level": 6, "name": "Guarded Smile", "description": "+1 extra Pyrotechnic Strike."}
        ]
    },
    {
        "id": 10000102, "name": "Mualani", "title": "Splish-Splash Wavechaser",
        "element": "Hydro", "weapon_type": "Catalyst", "rarity": 5, "region": "Natlan",
        "affiliation": "People of the Springs", "description": "A passionate waverider and guide from the People of the Springs.",
        "base_hp_lvl90": 13348.0, "base_atk_lvl90": 180.0, "base_def_lvl90": 632.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Mualani",
        "talents": [
            {"name": "Cooling Treatment", "unlock": "Normal Attack", "type": "normal", "description": "Hurls Hydro DMG projectiles."},
            {"name": "Surfshark Wavebreaker", "unlock": "Elemental Skill", "type": "skill", "description": "Rides sharksurfer with Nightsoul blessing, marking opponents."},
            {"name": "Boomsharka-laka", "unlock": "Elemental Burst", "type": "burst", "description": "Super Shark Missile deals AoE Hydro DMG."},
            {"name": "Heatproof Stars", "unlock": "1st Ascension Passive", "type": "passive", "description": "Wave Momentum marks grant bonus Hydro DMG."},
            {"name": "Natlan Tourism Champion", "unlock": "4th Ascension Passive", "type": "passive", "description": "Nightsoul Burst stacks increase Skill DMG."}
        ],
        "constellations": [
            {"level": 1, "name": "The Leisurely Meztli", "description": "+66% Sharky Missile DMG."},
            {"level": 2, "name": "Tepetlisaurus' Roar", "description": "+1 Wave Momentum on marked hit."},
            {"level": 3, "name": "Surfing Atop Joyous Seas", "description": "+3 Skill Level."},
            {"level": 4, "name": "Sharky Eats Puffies", "description": "+8 Energy on marked hit."},
            {"level": 5, "name": "Same Style of Surf", "description": "+3 Burst Level."},
            {"level": 6, "name": "Spirit of the Springs' People", "description": "+2 Wave Momentum stacks on activation."}
        ]
    },
    {
        "id": 10000103, "name": "Xilonen", "title": "Ardent Flames Forge the Soul",
        "element": "Geo", "weapon_type": "Sword", "rarity": 5, "region": "Natlan",
        "affiliation": "Children of Echoes", "description": "A masterful forgemaster and DJ from Natlan.",
        "base_hp_lvl90": 12405.0, "base_atk_lvl90": 275.0, "base_def_lvl90": 930.0,
        "ascension_stat": "DEF%", "ascension_stat_val_lvl90": "28.8%",
        "icon": "UI_AvatarIcon_Xilonen",
        "talents": [
            {"name": "Ehecatl's Roar", "unlock": "Normal Attack", "type": "normal", "description": "Up to 3 strikes; roller blade attacks in Nightsoul."},
            {"name": "Yohualcoatl's Ring of Buzzing", "unlock": "Elemental Skill", "type": "skill", "description": "Nightsoul Blessing with RES-shredding Samplers."},
            {"name": "Ocelotlicue Point!", "unlock": "Elemental Burst", "type": "burst", "description": "AoE Geo DMG and DEF-based healing."},
            {"name": "Netotiliztli Revolution", "unlock": "1st Ascension Passive", "type": "passive", "description": "Geo RES shred converts to party's dominant element."},
            {"name": "Portable Armored Sheath", "unlock": "4th Ascension Passive", "type": "passive", "description": "Enhanced RES shred in Nightsoul Blessing."}
        ],
        "constellations": [
            {"level": 1, "name": "Sabbatical Phrase", "description": "Extended Nightsoul Blessing duration."},
            {"level": 2, "name": "Chiucue Mix", "description": "+50 EM for nearby active characters."},
            {"level": 3, "name": "Tonalpohualli Routine", "description": "+3 Skill Level."},
            {"level": 4, "name": "Suchitl's Trance", "description": "+25% Geo DMG Bonus for 15s after Burst."},
            {"level": 5, "name": "Tlaltecuhtli's Crossfade", "description": "+3 Burst Level."},
            {"level": 6, "name": "Imperishable Night Carnival", "description": "+20% DMG Bonus for party element."}
        ]
    },
    {
        "id": 10000070, "name": "Cyno", "title": "Judicator of Secrets",
        "element": "Electro", "weapon_type": "Polearm", "rarity": 5, "region": "Sumeru",
        "affiliation": "Akademiya Matra", "description": "General Mahamatra of the Akademiya.",
        "base_hp_lvl90": 12491.0, "base_atk_lvl90": 318.0, "base_def_lvl90": 859.0,
        "ascension_stat": "CRIT DMG", "ascension_stat_val_lvl90": "38.4%",
        "icon": "UI_AvatarIcon_Cyno",
        "talents": [
            {"name": "Invoker's Spear", "unlock": "Normal Attack", "type": "normal", "description": "Up to 4 rapid polearm strikes."},
            {"name": "Secret Rite: Chasmic Soulfarer", "unlock": "Elemental Skill", "type": "skill", "description": "Rapid Electro DMG thrust."},
            {"name": "Sacred Rite: Wolf's Swiftness", "unlock": "Elemental Burst", "type": "burst", "description": "Pactsworn Pathclearer with Electro infusion and EM boost."},
            {"name": "Featherfall Judgment", "unlock": "1st Ascension Passive", "type": "passive", "description": "Duststalker Bolts during Pathclearer Skill use."},
            {"name": "Authority Over the Nine Bows", "unlock": "4th Ascension Passive", "type": "passive", "description": "Normal Attack DMG +150% of EM during Pathclearer."}
        ],
        "constellations": [
            {"level": 1, "name": "Ordinance: Unceasing Vigil", "description": "+20% ATK SPD for 10s."},
            {"level": 2, "name": "Ceremony: Homecoming of Spirits", "description": "+10% Electro DMG per hit, max 5 stacks."},
            {"level": 3, "name": "Precept: Lawful Enforcer", "description": "+3 Burst Level."},
            {"level": 4, "name": "Austerity: Forbidding Guard", "description": "+3 Energy on Electro reaction."},
            {"level": 5, "name": "Funerary Rite: The Passing of Starlight", "description": "+3 Skill Level."},
            {"level": 6, "name": "Raiment: Just Scales", "description": "2 Duststalker Bolts every 4 Normal Attacks."}
        ]
    },
    {
        "id": 10000071, "name": "Wanderer", "title": "Eons Adrift",
        "element": "Anemo", "weapon_type": "Catalyst", "rarity": 5, "region": "Sumeru",
        "affiliation": "None", "description": "A wandering puppet who walks his own path.",
        "base_hp_lvl90": 10164.0, "base_atk_lvl90": 328.0, "base_def_lvl90": 607.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Wanderer",
        "talents": [
            {"name": "Yuuban Meigen", "unlock": "Normal Attack", "type": "normal", "description": "Up to 3 wind-blade Anemo DMG attacks."},
            {"name": "Hanega: Song of the Wind", "unlock": "Elemental Skill", "type": "skill", "description": "Windfavored state hovering with enhanced attacks."},
            {"name": "Kyougen: Five Ceremonial Plays", "unlock": "Elemental Burst", "type": "burst", "description": "Vacuum AoE Anemo DMG."},
            {"name": "Jade-Claimed Flower", "unlock": "1st Ascension Passive", "type": "passive", "description": "+20% ATK/DMG/CRIT Rate on elemental contact."},
            {"name": "Gales of Reverie", "unlock": "4th Ascension Passive", "type": "passive", "description": "Anemo DMG arrows in Windfavored state."}
        ],
        "constellations": [
            {"level": 1, "name": "Shoban: Ostentatious Plumage", "description": "+10% ATK SPD in Windfavored."},
            {"level": 2, "name": "Niban: Moonlit Isle of Precedence", "description": "Burst field increases ATK DMG."},
            {"level": 3, "name": "Sanban: Moonflower Kusemai", "description": "+3 Skill Level."},
            {"level": 4, "name": "Yonban: Set Adrift into Spring", "description": "+25% Anemo DMG at 2+ elements."},
            {"level": 5, "name": "Matsuban: Ancient Illuminator From Abroad", "description": "+3 Burst Level."},
            {"level": 6, "name": "Shugen: The Curtains' Melancholic Sway", "description": "Wind arrows at 40% ATK as Anemo DMG."}
        ]
    },
    {
        "id": 10000054, "name": "Yoimiya", "title": "Frolicking Flames",
        "element": "Pyro", "weapon_type": "Bow", "rarity": 5, "region": "Inazuma",
        "affiliation": "Naganohara Fireworks", "description": "The Queen of the Summer Festival.",
        "base_hp_lvl90": 10164.0, "base_atk_lvl90": 323.0, "base_def_lvl90": 615.0,
        "ascension_stat": "CRIT Rate", "ascension_stat_val_lvl90": "19.2%",
        "icon": "UI_AvatarIcon_Yoimiya",
        "talents": [
            {"name": "Firework Flare-Up", "unlock": "Normal Attack", "type": "normal", "description": "Up to 5 rapid shots."},
            {"name": "Niwabi Fire-Dance", "unlock": "Elemental Skill", "type": "skill", "description": "Pyro-infused Normal Attacks with increased DMG."},
            {"name": "Ryuukin Saxifrage", "unlock": "Elemental Burst", "type": "burst", "description": "AoE Pyro DMG; marks opponent with Aurous Blaze."},
            {"name": "Tricks of the Trouble-Maker", "unlock": "1st Ascension Passive", "type": "passive", "description": "Stacking Pyro DMG Bonus for party."},
            {"name": "Summer Night's Dawn", "unlock": "4th Ascension Passive", "type": "passive", "description": "+10% party ATK for 15s after Burst."}
        ],
        "constellations": [
            {"level": 1, "name": "Agate Ryuukin", "description": "+4s Aurous Blaze; +20% ATK on kill."},
            {"level": 2, "name": "A Procession of Bonfires", "description": "+25% Pyro DMG Bonus for 6s."},
            {"level": 3, "name": "Trickster's Flare", "description": "+3 Skill Level."},
            {"level": 4, "name": "Pyrotechnic Professional", "description": "-1.2s Skill CD on Aurous Blaze trigger."},
            {"level": 5, "name": "A Summer Festival's Eve", "description": "+3 Burst Level."},
            {"level": 6, "name": "Naganohara Meteor Swarm", "description": "50% chance for extra kindling arrow."}
        ]
    },
]

# ── New Weapons to ADD (Matching WeaponData fields) ──────────────────────────────────────────
NEW_WEAPONS = [
    {
        "id": 11511, "name": "Primordial Jade Cutter", "weapon_type": "Sword", "rarity": 5,
        "base_atk_lvl1": 44.0, "base_atk_lvl90": 542.0, "sub_stat_type": "CRIT Rate", "sub_stat_val_lvl90": "44.1%",
        "passive_name": "Protector's Virtue", "passive_desc": "HP +20%. ATK Bonus based on 1.2% of Max HP.",
        "icon": "UI_EquipIcon_Sword_Primordial", "refinements": ["HP +20%", "HP +25%", "HP +30%", "HP +35%", "HP +40%"],
        "ascension_materials": ["Lead Oasis", "Shell", "Insignia"]
    },
    {
        "id": 12512, "name": "Wolf's Gravestone", "weapon_type": "Claymore", "rarity": 5,
        "base_atk_lvl1": 46.0, "base_atk_lvl90": 608.0, "sub_stat_type": "ATK%", "sub_stat_val_lvl90": "49.6%",
        "passive_name": "Wolfish Tracker", "passive_desc": "+20% ATK. Hits vs <30% HP grant +40% party ATK for 12s.",
        "icon": "UI_EquipIcon_Claymore_Wolfmound", "refinements": ["ATK +20%", "ATK +25%", "ATK +30%", "ATK +35%", "ATK +40%"],
        "ascension_materials": ["Boreal Wolf", "Dead Ley Line", "Insignia"]
    },
    {
        "id": 14512, "name": "Lost Prayer to the Sacred Winds", "weapon_type": "Catalyst", "rarity": 5,
        "base_atk_lvl1": 46.0, "base_atk_lvl90": 608.0, "sub_stat_type": "CRIT Rate", "sub_stat_val_lvl90": "33.1%",
        "passive_name": "Boundless Blessing", "passive_desc": "+10% Move SPD. +8% Elemental DMG every 4s, max 4 stacks.",
        "icon": "UI_EquipIcon_Catalyst_Fourwinds", "refinements": ["Move SPD +10%"],
        "ascension_materials": ["Dandelion Gladiator", "Chaos", "Insignia"]
    },
    {
        "id": 15511, "name": "Amos' Bow", "weapon_type": "Bow", "rarity": 5,
        "base_atk_lvl1": 46.0, "base_atk_lvl90": 608.0, "sub_stat_type": "ATK%", "sub_stat_val_lvl90": "49.6%",
        "passive_name": "Strong-Willed", "passive_desc": "+12% Normal/Charged DMG. +8% per 0.1s arrow airtime, max 5 stacks.",
        "icon": "UI_EquipIcon_Bow_Amos", "refinements": ["Normal/Charged DMG +12%"],
        "ascension_materials": ["Dandelion Gladiator", "Chaos", "Insignia"]
    },
    {
        "id": 11509, "name": "Freedom-Sworn", "weapon_type": "Sword", "rarity": 5,
        "base_atk_lvl1": 46.0, "base_atk_lvl90": 608.0, "sub_stat_type": "Elemental Mastery", "sub_stat_val_lvl90": "198",
        "passive_name": "Revolutionary Chorale", "passive_desc": "+10% DMG. Reactions grant Sigils; 2 Sigils = +20% ATK, +16% NA/CA/PA DMG.",
        "icon": "UI_EquipIcon_Sword_Narukami", "refinements": ["DMG +10%"],
        "ascension_materials": ["Decarabian", "Chaos", "Scroll"]
    },
    {
        "id": 15513, "name": "Aqua Simulacra", "weapon_type": "Bow", "rarity": 5,
        "base_atk_lvl1": 44.0, "base_atk_lvl90": 542.0, "sub_stat_type": "CRIT DMG", "sub_stat_val_lvl90": "88.2%",
        "passive_name": "The Cleansing Form", "passive_desc": "+16% HP. +20% DMG when near opponents.",
        "icon": "UI_EquipIcon_Bow_Kirin", "refinements": ["HP +16%"],
        "ascension_materials": ["Guyun", "Statue", "Shell"]
    },
    {
        "id": 12511, "name": "Redhorn Stonethresher", "weapon_type": "Claymore", "rarity": 5,
        "base_atk_lvl1": 44.0, "base_atk_lvl90": 542.0, "sub_stat_type": "CRIT DMG", "sub_stat_val_lvl90": "88.2%",
        "passive_name": "Gokadaiou Otogibanashi", "passive_desc": "+28% DEF. Normal/Charged DMG +40% of DEF.",
        "icon": "UI_EquipIcon_Claymore_Itadorimaru", "refinements": ["DEF +28%"],
        "ascension_materials": ["Narukami", "Claw", "Handguard"]
    },
    {
        "id": 14513, "name": "Kagura's Verity", "weapon_type": "Catalyst", "rarity": 5,
        "base_atk_lvl1": 46.0, "base_atk_lvl90": 608.0, "sub_stat_type": "CRIT DMG", "sub_stat_val_lvl90": "66.2%",
        "passive_name": "Kagura Dance of the Sacred Sakura", "passive_desc": "Skill use +12% Skill DMG for 16s. Max 3 stacks. At max: +12% All Elemental DMG.",
        "icon": "UI_EquipIcon_Catalyst_Narukami", "refinements": ["Skill DMG +12%"],
        "ascension_materials": ["Court Lantern", "Claw", "Husk"]
    },
    {
        "id": 11417, "name": "The Black Sword", "weapon_type": "Sword", "rarity": 4,
        "base_atk_lvl1": 42.0, "base_atk_lvl90": 510.0, "sub_stat_type": "CRIT Rate", "sub_stat_val_lvl90": "27.6%",
        "passive_name": "Justice", "passive_desc": "+20% Normal/Charged DMG. CRIT heals 60% ATK.",
        "icon": "UI_EquipIcon_Sword_Bloodstained", "refinements": ["Normal/Charged DMG +20%"],
        "ascension_materials": ["Guyun", "Dead Ley Line", "Insignia"]
    },
    {
        "id": 12416, "name": "Serpent Spine", "weapon_type": "Claymore", "rarity": 4,
        "base_atk_lvl1": 42.0, "base_atk_lvl90": 510.0, "sub_stat_type": "CRIT Rate", "sub_stat_val_lvl90": "27.6%",
        "passive_name": "Wavesplitter", "passive_desc": "+6% DMG every 4s on field, max 5. Taking DMG removes 1.",
        "icon": "UI_EquipIcon_Claymore_Kione", "refinements": ["DMG +6% per stack"],
        "ascension_materials": ["Aerosiderite", "Fragile Bone", "Nectar"]
    },
    {
        "id": 13416, "name": "Deathmatch", "weapon_type": "Polearm", "rarity": 4,
        "base_atk_lvl1": 41.0, "base_atk_lvl90": 454.0, "sub_stat_type": "CRIT Rate", "sub_stat_val_lvl90": "36.8%",
        "passive_name": "Gladiator", "passive_desc": "+16% ATK/DEF at 2+ opponents; +24% ATK at fewer.",
        "icon": "UI_EquipIcon_Pole_Gladiator", "refinements": ["ATK/DEF +16%"],
        "ascension_materials": ["Boreal Wolf", "Dead Ley Line", "Insignia"]
    },
    {
        "id": 13501, "name": "Calamity Queller", "weapon_type": "Polearm", "rarity": 5,
        "base_atk_lvl1": 49.0, "base_atk_lvl90": 741.0, "sub_stat_type": "ATK%", "sub_stat_val_lvl90": "16.5%",
        "passive_name": "Extinguishing Precept", "passive_desc": "+12% All Elemental DMG. Skill use grants stacking ATK (doubled off-field).",
        "icon": "UI_EquipIcon_Pole_Santika", "refinements": ["DMG +12%"],
        "ascension_materials": ["Mist Veiled Elixir", "Claw", "Handguard"]
    },
]

# ── New Artifact Sets to ADD (Matching ArtifactSetData fields) ──────────────────────────────────────
NEW_ARTIFACT_SETS = [
    {
        "id": 15001, "name": "Gladiator's Finale", "rarities": [4, 5],
        "bonus_2pc": "ATK +18%.",
        "bonus_4pc": "Sword/Claymore/Polearm Normal Attack DMG +35%.",
        "icon": "UI_RelicIcon_15001_4",
        "pieces": {"flower": "Gladiator's Nostalgia", "plume": "Gladiator's Destiny"}
    },
    {
        "id": 15003, "name": "Wanderer's Troupe", "rarities": [4, 5],
        "bonus_2pc": "Elemental Mastery +80.",
        "bonus_4pc": "Catalyst/Bow Charged Attack DMG +35%.",
        "icon": "UI_RelicIcon_15003_4",
        "pieces": {"flower": "Troupe's Dawnlight", "plume": "Bard's Arrow Feather"}
    },
    {
        "id": 15005, "name": "Thundering Fury", "rarities": [4, 5],
        "bonus_2pc": "Electro DMG Bonus +15%.",
        "bonus_4pc": "+40% Overloaded/Electro-Charged/Superconduct/Hyperbloom DMG. +20% Aggravate. Reactions reduce Skill CD by 1s.",
        "icon": "UI_RelicIcon_15005_4",
        "pieces": {"flower": "Thunderbird's Mercy", "plume": "Survivor of Catastrophe"}
    },
    {
        "id": 14001, "name": "Blizzard Strayer", "rarities": [4, 5],
        "bonus_2pc": "Cryo DMG Bonus +15%.",
        "bonus_4pc": "+20% CRIT Rate vs Cryo-affected. +20% more if Frozen.",
        "icon": "UI_RelicIcon_14001_4",
        "pieces": {"flower": "Snowswept Memory", "plume": "Icebreaker's Resolve"}
    },
    {
        "id": 15006, "name": "Crimson Witch of Flames", "rarities": [4, 5],
        "bonus_2pc": "Pyro DMG Bonus +15%.",
        "bonus_4pc": "+40% Overloaded/Burning/Burgeon DMG. +15% Vaporize/Melt. Skill boosts 2-piece by 50%, max 3 stacks.",
        "icon": "UI_RelicIcon_15006_4",
        "pieces": {"flower": "Witch's Flower of Blazes", "plume": "Witch's Ever-Burning Plume"}
    },
    {
        "id": 15016, "name": "Heart of Depth", "rarities": [4, 5],
        "bonus_2pc": "Hydro DMG Bonus +15%.",
        "bonus_4pc": "Skill grants +30% Normal/Charged DMG for 15s.",
        "icon": "UI_RelicIcon_15016_4",
        "pieces": {"flower": "Gilded Corsage", "plume": "Gust of Nostalgia"}
    },
    {
        "id": 15017, "name": "Tenacity of the Millelith", "rarities": [4, 5],
        "bonus_2pc": "HP +20%.",
        "bonus_4pc": "Skill hit grants +20% party ATK and +30% Shield Strength for 3s.",
        "icon": "UI_RelicIcon_15017_4",
        "pieces": {"flower": "Flower of Accolades", "plume": "Ceremonial War-Plume"}
    },
    {
        "id": 15018, "name": "Pale Flame", "rarities": [4, 5],
        "bonus_2pc": "Physical DMG Bonus +25%.",
        "bonus_4pc": "Skill hit +9% ATK for 7s, max 2 stacks. At 2: 2-piece doubled.",
        "icon": "UI_RelicIcon_15018_4",
        "pieces": {"flower": "Stainless Bloom", "plume": "Wise Doctor's Pinion"}
    },
    {
        "id": 15019, "name": "Shimenawa's Reminiscence", "rarities": [4, 5],
        "bonus_2pc": "ATK +18%.",
        "bonus_4pc": "Skill at 15+ Energy: -15 Energy, +50% Normal/Charged/Plunging DMG for 10s.",
        "icon": "UI_RelicIcon_15019_4",
        "pieces": {"flower": "Entangling Bloom", "plume": "Shaft of Remembrance"}
    },
    {
        "id": 15021, "name": "Husk of Opulent Dreams", "rarities": [4, 5],
        "bonus_2pc": "DEF +30%.",
        "bonus_4pc": "Geo hits and on-field time grant stacks. Each: +6% DEF and +6% Geo DMG. Max 4.",
        "icon": "UI_RelicIcon_15021_4",
        "pieces": {"flower": "Bloom Times", "plume": "Plume of Luxury"}
    },
    {
        "id": 15023, "name": "Gilded Dreams", "rarities": [4, 5],
        "bonus_2pc": "Elemental Mastery +80.",
        "bonus_4pc": "On reaction: same element = +14% ATK, different = +50 EM. Max 3 stacks.",
        "icon": "UI_RelicIcon_15023_4",
        "pieces": {"flower": "Dreaming Bud of a Summer Festival", "plume": "Feather of Judgment"}
    },
    {
        "id": 15024, "name": "Flower of Paradise Lost", "rarities": [4, 5],
        "bonus_2pc": "Elemental Mastery +80.",
        "bonus_4pc": "+40% Bloom/Hyperbloom/Burgeon DMG. EM further increases these by up to 25%.",
        "icon": "UI_RelicIcon_15024_4",
        "pieces": {"flower": "Ayus's Wondrous Flower", "plume": "Secret-Keeper's Magic Feather"}
    },
]


def main():
    # To prevent duplicates and garbage data, let's read the current contents,
    # filter out any entries that might be bad (i.e. missing required keys like weapon_type or bonus_2pc),
    # and then append our correct new entries.
    
    # 1. Characters
    char_path = os.path.join(BASE, "characters.json")
    if os.path.exists(char_path):
        with open(char_path, "r", encoding="utf-8") as f:
            chars = json.load(f)
    else:
        chars = []
    
    # Filter characters to keep only valid ones
    chars = [c for c in chars if "base_hp_lvl90" in c]
    existing_names = {c["name"] for c in chars}
    for c in NEW_CHARACTERS:
        if c["name"] not in existing_names:
            chars.append(c)
    with open(char_path, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chars)} characters.")

    # 2. Weapons
    wep_path = os.path.join(BASE, "weapons.json")
    if os.path.exists(wep_path):
        with open(wep_path, "r", encoding="utf-8") as f:
            weapons = json.load(f)
    else:
        weapons = []
        
    # Keep only valid original weapons
    weapons = [w for w in weapons if "weapon_type" in w]
    existing_wnames = {w["name"] for w in weapons}
    for w in NEW_WEAPONS:
        if w["name"] not in existing_wnames:
            weapons.append(w)
    with open(wep_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(weapons)} weapons.")

    # 3. Artifacts
    art_path = os.path.join(BASE, "artifacts.json")
    if os.path.exists(art_path):
        with open(art_path, "r", encoding="utf-8") as f:
            artifacts = json.load(f)
    else:
        artifacts = []
        
    # Keep only valid original artifacts
    artifacts = [a for a in artifacts if "bonus_2pc" in a]
    existing_anames = {a["name"] for a in artifacts}
    for a in NEW_ARTIFACT_SETS:
        if a["name"] not in existing_anames:
            artifacts.append(a)
    with open(art_path, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(artifacts)} artifacts.")


if __name__ == "__main__":
    main()

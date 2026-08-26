"""CLI utility to fetch and inspect a Genshin Impact player showcase."""

import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.account_service import account_service  # noqa: E402
from backend.config import settings  # noqa: E402


async def main():
    uid = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (settings.USER_UID or "817739968")
    )
    print(f"Fetching showcase for UID: {uid} (Bypassing cache)...")

    try:
        showcase = await account_service.get_showcase(
            uid=uid, force_refresh=True
        )
        prof = showcase.profile
        print("=" * 70)
        print(
            f"Player: {prof.nickname} (UID: {prof.uid}) | "
            f"AR {prof.level} | WL {prof.world_level}"
        )
        print(f"Signature: \"{prof.signature or 'None'}\"")
        abyss = (
            f"Floor {prof.spiral_abyss_floor}-"
            f"{prof.spiral_abyss_chamber}"
        )
        print(
            f"Achievements: {prof.achievement_count:,} | "
            f"Spiral Abyss: {abyss}"
        )
        print(f"Showcase Characters ({len(showcase.characters)}):")
        print("=" * 70)

        for i, char in enumerate(showcase.characters, 1):
            w = char.weapon
            w_str = (
                f"{w.name} (R{w.refinement}, Lv.{w.level})"
                if w else "No weapon"
            )
            arts_count = len(char.artifacts)
            print(
                f"{i:2d}. {char.name:<18} | {char.element:<7} | "
                f"Lv.{char.level}/90 C{char.constellation} | "
                f"Weapon: {w_str} | Artifacts: {arts_count}/5"
            )
            if char.stats:
                s = char.stats
                print(
                    f"    HP: {int(s.max_hp):,} | "
                    f"ATK: {int(s.atk):,} | "
                    f"DEF: {int(s.defense):,} | "
                    f"CR: {s.crit_rate*100:.1f}% | "
                    f"CD: {s.crit_dmg*100:.1f}% | "
                    f"ER: {s.energy_recharge*100:.1f}% | "
                    f"EM: {int(s.elemental_mastery)}"
                )

    except Exception as e:
        print(f"Error fetching showcase: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())

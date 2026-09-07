"""Account service coordinating showcase data retrieval, caching, and lookups."""

from difflib import get_close_matches
from typing import Optional, List
from backend.providers.enka_client import enka_client, EnkaClient
from backend.services.cache_service import cache_service, ShowcaseCacheService
from backend.models.account import EnkaShowcaseResponse, CharacterBuild


class AccountService:
    """High-level service for Genshin Impact player showcase management."""

    def __init__(self, client: Optional[EnkaClient] = None, cache: Optional[ShowcaseCacheService] = None):
        self.client = client or enka_client
        self.cache = cache or cache_service

    async def get_showcase(self, uid: str, force_refresh: bool = False) -> EnkaShowcaseResponse:
        """
        Get player showcase data by UID.
        Uses cached response if available and not forced to refresh.
        """
        clean_uid = str(uid).strip()

        # Check cache if not forcing refresh
        if not force_refresh:
            cached_raw = self.cache.get(clean_uid)
            if cached_raw:
                return self.client.normalize_showcase(cached_raw, clean_uid, cached=True)

        # Fetch fresh data from Enka API
        raw_data = await self.client.fetch_user_showcase(clean_uid)

        # Save to cache
        ttl = raw_data.get("ttl", 300)
        self.cache.set(clean_uid, raw_data, ttl_seconds=ttl)

        return self.client.normalize_showcase(raw_data, clean_uid, cached=False)

    async def get_character_build(self, uid: str, character_identifier: str) -> Optional[CharacterBuild]:
        """
        Retrieve a specific character build from a player's showcase by name or avatar ID.
        """
        showcase = await self.get_showcase(uid)
        ident_lower = character_identifier.lower().strip()

        for char in showcase.characters:
            if str(char.avatar_id) == character_identifier or char.name.lower() == ident_lower:
                return char

        if ident_lower and len(ident_lower) >= 3:
            names = [char.name.lower() for char in showcase.characters]
            match = get_close_matches(ident_lower, names, n=1, cutoff=0.78)
            if match:
                matched_name = match[0]
                for char in showcase.characters:
                    if char.name.lower() == matched_name:
                        return char

        return None


account_service = AccountService()

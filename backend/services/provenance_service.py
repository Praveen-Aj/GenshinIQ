"""Service that builds provenance metadata for local datasets."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from backend.config import settings
from backend.models.provenance import (
    DataProvenanceManifest,
    DatasetFileProvenance,
    GameDataProvenance,
    KnowledgeProvenance,
)
from backend.services.game_data_service import game_data_service
from backend.services.knowledge_service import knowledge_service


GAME_DATA_DIR = Path("data/processed/game_data")
KNOWLEDGE_DIR = Path("data/knowledge")
RUNTIME_CACHE_DIR = Path("data/runtime/showcases")


class ProvenanceService:
    """Builds a live provenance snapshot from local dataset files."""

    @staticmethod
    def _sha256_bytes(chunks: Iterable[bytes]) -> str:
        hasher = hashlib.sha256()
        for chunk in chunks:
            hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _sha256_file(path: Path) -> str:
        with open(path, "rb") as handle:
            return ProvenanceService._sha256_bytes(iter(lambda: handle.read(8192), b""))

    @staticmethod
    def _updated_at(path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

    @staticmethod
    def _posix_path(path: Path) -> str:
        return path.as_posix()

    @staticmethod
    def _record_count(payload: Any) -> int:
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            return len(payload)
        return 1

    def _build_game_data_provenance(self) -> GameDataProvenance:
        file_entries: list[DatasetFileProvenance] = []
        file_hashes: list[str] = []

        for file_path in sorted(GAME_DATA_DIR.glob("*.json")):
            with open(file_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)

            record_count = self._record_count(payload)
            file_hash = self._sha256_file(file_path)
            file_hashes.append(file_hash)
            sid = "src_project_amber" if file_path.name in ("characters.json", "weapons.json", "artifacts.json", "materials.json") else "src_animegamedata"
            surl = "https://api.ambr.top/v2/en/" if sid == "src_project_amber" else "https://github.com/Dimbreath/AnimeGameData/tree/master/ExcelBinOutput"
            inv_class = "CATEGORY_A_ENGINE_CONSTANT" if file_path.name in ("avatar_curves.json", "weapon_curves.json", "artifact_levels.json") else "CATEGORY_B_GAME_CONTENT_STATIC"
            file_entries.append(
                DatasetFileProvenance(
                    file_name=file_path.name,
                    record_count=record_count,
                    sha256=file_hash,
                    updated_at=self._updated_at(file_path),
                    source_id=sid,
                    source_url=surl,
                    source_version="5.4",
                    dataset_version="5.4",
                    project_target_version="7.0",
                    verification_state="VERIFIED_STRUCTURED",
                    verification_status="VERIFIED_STRUCTURED",
                    invariance_classification=inv_class,
                )
            )

        aggregate = self._sha256_bytes(f"{digest}\n".encode("utf-8") for digest in sorted(file_hashes))

        return GameDataProvenance(
            directory=self._posix_path(GAME_DATA_DIR),
            aggregate_sha256=aggregate,
            files=file_entries,
            characters=len(game_data_service.list_characters()),
            weapons=len(game_data_service.list_weapons()),
            artifact_sets=len(game_data_service.list_artifact_sets()),
            materials=len(game_data_service.list_materials()),
        )

    def _build_knowledge_provenance(self) -> KnowledgeProvenance:
        source_types = Counter()
        source_tiers = Counter()
        source_ids = Counter()
        sources = Counter()
        versions = Counter()
        file_hashes: list[str] = []

        for document in knowledge_service.documents.values():
            source_types[document.metadata.source_type.value] += 1
            source_tiers[f"Tier {document.metadata.authority_tier}"] += 1
            source_ids[document.metadata.source_id] += 1
            sources[document.metadata.source] += 1
            versions[document.metadata.game_version] += 1

        for file_path in sorted(KNOWLEDGE_DIR.glob("*.json")):
            file_hashes.append(self._sha256_file(file_path))

        aggregate = self._sha256_bytes(f"{digest}\n".encode("utf-8") for digest in sorted(file_hashes))

        return KnowledgeProvenance(
            directory=self._posix_path(KNOWLEDGE_DIR),
            aggregate_sha256=aggregate,
            total_documents=len(knowledge_service.documents),
            source_type_counts=dict(sorted(source_types.items())),
            source_tier_counts=dict(sorted(source_tiers.items())),
            source_id_counts=dict(sorted(source_ids.items())),
            source_counts=dict(sorted(sources.items())),
            game_version_counts=dict(sorted(versions.items())),
        )

    def build_manifest(self) -> DataProvenanceManifest:
        return DataProvenanceManifest(
            generated_at=datetime.now(timezone.utc).isoformat(),
            app_version=settings.APP_VERSION,
            runtime_cache_dir=self._posix_path(RUNTIME_CACHE_DIR),
            game_data=self._build_game_data_provenance(),
            knowledge_base=self._build_knowledge_provenance(),
        )


provenance_service = ProvenanceService()

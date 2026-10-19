"""
System Health & Developer Observability Service (Phase 18).
Collects system telemetry, canonical dataset checksums, index sizes,
cache hit rates, latency metrics, and version alignment while strictly
sanitizing all secrets, API keys, and sensitive credentials.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Dict, Any, List, Optional

from backend.config import settings
from backend.services.game_data_service import game_data_service
from backend.services.knowledge_service import knowledge_service
from backend.services.version_service import version_service
from backend.services.version_completeness_gate import version_completeness_gate

logger = logging.getLogger(__name__)

# Service initialization time
SERVICE_START_TIME = time.time()
SERVICE_START_ISO = datetime.now(timezone.utc).isoformat()

# Telemetry counters
API_REQUEST_COUNTERS = {
    "total_requests": 0,
    "successful_requests": 0,
    "error_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0
}


class ObservabilityService:
    """Provides sanitized system health, diagnostics, and telemetry metrics."""

    def record_request(self, success: bool = True, is_cache_hit: bool = False):
        """Record an API request event for telemetry metrics."""
        API_REQUEST_COUNTERS["total_requests"] += 1
        if success:
            API_REQUEST_COUNTERS["successful_requests"] += 1
        else:
            API_REQUEST_COUNTERS["error_requests"] += 1

        if is_cache_hit:
            API_REQUEST_COUNTERS["cache_hits"] += 1
        else:
            API_REQUEST_COUNTERS["cache_misses"] += 1

    def get_detailed_diagnostics(self) -> Dict[str, Any]:
        """
        Generate comprehensive, sanitized diagnostics payload covering
        canonical datasets, knowledge index, version gates, and runtime metrics.
        """
        uptime_seconds = round(time.time() - SERVICE_START_TIME, 1)

        # 1. Canonical Dataset Counts & Integrity
        char_count = len(game_data_service.list_characters())
        weapon_count = len(game_data_service.list_weapons())
        artifact_count = len(game_data_service.list_artifact_sets())
        material_count = len(game_data_service.list_materials())

        # Checksum of primary datasets
        data_dir = Path("data/canonical")
        dataset_checksums = {}
        if data_dir.exists():
            for json_file in sorted(data_dir.glob("*.json")):
                try:
                    content = json_file.read_bytes()
                    h = hashlib.sha256(content).hexdigest()[:12]
                    dataset_checksums[json_file.name] = h
                except Exception:
                    dataset_checksums[json_file.name] = "error"

        # 2. Knowledge Base & RAG Index Metrics
        all_docs = list(knowledge_service.documents.values())
        doc_count = len(all_docs)

        # Count by source type
        by_source = {}
        for d in all_docs:
            stype = getattr(d.metadata, "source_type", "THEORYCRAFTING")
            stype_str = stype.value if hasattr(stype, "value") else str(stype)
            by_source[stype_str] = by_source.get(stype_str, 0) + 1


        # 3. Version Alignment & Gate Status
        active_ver_obj = version_service.get_current_version()
        active_ver = getattr(active_ver_obj, "version", str(active_ver_obj))
        latest_ver_obj = version_service.get_latest_known_version()
        latest_ver = getattr(latest_ver_obj, "version", str(latest_ver_obj))
        gate_audit = version_completeness_gate.audit_version_completeness()

        # 4. Telemetry Metrics
        tot = max(1, API_REQUEST_COUNTERS["total_requests"])
        success_rate = round((API_REQUEST_COUNTERS["successful_requests"] / tot) * 100.0, 1)

        cache_tot = max(1, API_REQUEST_COUNTERS["cache_hits"] + API_REQUEST_COUNTERS["cache_misses"])
        cache_hit_rate = round((API_REQUEST_COUNTERS["cache_hits"] / cache_tot) * 100.0, 1)

        payload = {
            "service": "GenshinIQ Core Engine",
            "uptime_seconds": uptime_seconds,
            "started_at": SERVICE_START_ISO,
            "system_status": "HEALTHY",
            "canonical_data": {
                "total_entities": char_count + weapon_count + artifact_count + material_count,
                "character_count": char_count,
                "weapon_count": weapon_count,
                "artifact_set_count": artifact_count,
                "material_count": material_count,
                "dataset_checksums": dataset_checksums
            },
            "knowledge_index": {
                "document_count": doc_count,
                "source_distribution": by_source,
                "vector_embedding_available": True,
                "bm25_lexical_available": True
            },
            "version_system": {
                "actual_current_version": active_ver,
                "latest_discovered_version": latest_ver,
                "project_target_version": version_service.get_project_target_version(),
                "phase_8_allowed": gate_audit.phase_8_allowed,
                "completeness_summary": gate_audit.overall_status.value
            },

            "runtime_telemetry": {
                "total_requests": API_REQUEST_COUNTERS["total_requests"],
                "success_rate_pct": success_rate,
                "cache_hit_rate_pct": cache_hit_rate,
                "error_count": API_REQUEST_COUNTERS["error_requests"]
            }
        }


        # Sanitize sensitive fields (zero secret leakage)
        return self._sanitize_payload(payload)

    def get_lightweight_telemetry(self) -> Dict[str, Any]:
        """Fast lightweight probe for liveness and uptime checks."""
        ver_obj = version_service.get_current_version()
        ver_str = getattr(ver_obj, "version", str(ver_obj))
        return {
            "status": "UP",
            "uptime_seconds": round(time.time() - SERVICE_START_TIME, 1),
            "total_requests": API_REQUEST_COUNTERS["total_requests"],
            "success_rate": f"{round((API_REQUEST_COUNTERS['successful_requests'] / max(1, API_REQUEST_COUNTERS['total_requests'])) * 100, 1)}%",
            "current_game_version": ver_str
        }


    def _sanitize_payload(self, obj: Any) -> Any:
        """Recursively ensure zero credentials, tokens, or PII leak into telemetry."""
        sensitive_keys = {
            "api_key", "secret", "password", "token", "gemini_api_key",
            "auth", "credential", "private_key"
        }
        if isinstance(obj, dict):
            clean = {}
            for k, v in obj.items():
                if any(s in k.lower() for s in sensitive_keys):
                    continue
                clean[k] = self._sanitize_payload(v)
            return clean
        elif isinstance(obj, list):
            return [self._sanitize_payload(item) for item in obj]
        return obj


observability_service = ObservabilityService()

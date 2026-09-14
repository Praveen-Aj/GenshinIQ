"""Vector embedding and dense similarity index service for GenshinIQ.

Provides a pluggable, local-first embedding interface with deterministic subword
dense projection (local-subword-dense-v1), metadata tracking, and model-change invalidation.
"""

import json
import math
import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Protocol, Tuple

from backend.models.knowledge import SemanticChunk

INDEX_DIR = os.path.join(os.getcwd(), "data", "runtime", "index")
META_FILE = os.path.join(INDEX_DIR, "embedding_meta.json")
VECTORS_FILE = os.path.join(INDEX_DIR, "vectors.json")
CHUNKS_FILE = os.path.join(INDEX_DIR, "chunks.json")


class EmbeddingProvider(Protocol):
    """Abstract protocol for text embedding models."""
    model_name: str
    dimension: int

    def embed_text(self, text: str) -> List[float]:
        ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        ...


GENSHIN_DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    "em": ["elemental", "mastery"],
    "er": ["energy", "recharge"],
    "bol": ["bond", "life"],
    "cr": ["crit", "rate"],
    "cd": ["crit", "dmg", "damage"],
    "bis": ["best", "slot", "signature"],
    "battery": ["energy", "recharge", "funneling", "particles"],
    "funneling": ["energy", "recharge", "particles"],
    "pyronado": ["xiangling", "burst"],
    "fanfare": ["furina", "hp", "buff"],
}


class LocalSubwordEmbeddingProvider:
    """High-performance, deterministic subword dense projection embedding model (256-dim).

    Uses character n-grams, word tokens, and domain synonym expansions projected via
    deterministic sign-hashing with sublinear term weighting and L2 unit-normalization.
    Completely offline, zero-dependency, and deterministic.
    """

    model_name: str = "local-subword-dense-v1"
    dimension: int = 256

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def _hash_feature(self, feature: str) -> Tuple[int, float]:
        """Map feature string to (bucket_index, sign_multiplier)."""
        h = hashlib.md5(feature.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % self.dimension
        sign = 1.0 if (h[4] % 2 == 0) else -1.0
        return idx, sign

    def embed_text(self, text: str) -> List[float]:
        """Produce a normalized dense unit vector for input text."""
        vec = [0.0] * self.dimension
        clean_text = text.lower().strip()
        if not clean_text:
            return vec

        # 1. Word tokens and bigrams with domain synonym projection
        raw_words = re.findall(r"\b\w+\b", clean_text)
        words = list(raw_words)
        for w in raw_words:
            if w in GENSHIN_DOMAIN_SYNONYMS:
                words.extend(GENSHIN_DOMAIN_SYNONYMS[w])

        for i, w in enumerate(words):
            if len(w) < 2:
                continue
            idx, sign = self._hash_feature(f"w:{w}")
            vec[idx] += sign * 1.5

            if i < len(words) - 1:
                idx_bi, sign_bi = self._hash_feature(f"bi:{w}_{words[i+1]}")
                vec[idx_bi] += sign_bi * 2.0

        # 2. Subword character 3-grams and 4-grams (handles stems, affixes, names)
        padded = f"_{clean_text}_"
        for n in (3, 4):
            for i in range(len(padded) - n + 1):
                ngram = padded[i : i + n]
                idx, sign = self._hash_feature(f"ng:{ngram}")
                vec[idx] += sign * 0.5

        # 3. L2 Unit Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]

        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class EmbeddingService:
    """Manages embedding index storage, persistence, invalidation, and similarity searches."""

    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        self.provider = provider or LocalSubwordEmbeddingProvider()
        self.chunks: Dict[str, SemanticChunk] = {}
        self.vectors: Dict[str, List[float]] = {}
        self.meta: dict = {}
        self._load_or_initialize()

    def _ensure_index_dir(self):
        os.makedirs(INDEX_DIR, exist_ok=True)

    def _load_or_initialize(self):
        """Load persisted index or initialize empty if missing or invalidated."""
        self._ensure_index_dir()
        if not (os.path.exists(META_FILE) and os.path.exists(VECTORS_FILE) and os.path.exists(CHUNKS_FILE)):
            self._clear_index()
            return

        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # Invalidate if embedding model or dimension has changed
            if (
                meta.get("model_name") != self.provider.model_name
                or meta.get("dimension") != self.provider.dimension
            ):
                self._clear_index()
                return

            with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                raw_chunks = json.load(f)
                self.chunks = {cid: SemanticChunk(**data) for cid, data in raw_chunks.items()}

            with open(VECTORS_FILE, "r", encoding="utf-8") as f:
                self.vectors = json.load(f)

            self.meta = meta
        except Exception:
            self._clear_index()

    def _clear_index(self):
        """Reset in-memory index and empty metadata."""
        self.chunks = {}
        self.vectors = {}
        self.meta = {
            "model_name": self.provider.model_name,
            "dimension": self.provider.dimension,
            "indexed_at": None,
            "total_chunks": 0,
            "doc_hashes": {},
        }

    def save_index(self):
        """Persist in-memory index and metadata to disk."""
        self._ensure_index_dir()
        self.meta["total_chunks"] = len(self.chunks)
        self.meta["indexed_at"] = datetime.now(timezone.utc).isoformat()
        self.meta["model_name"] = self.provider.model_name
        self.meta["dimension"] = self.provider.dimension

        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

        with open(VECTORS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.vectors, f)

        with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
            raw_chunks = {cid: chunk.model_dump() for cid, chunk in self.chunks.items()}
            json.dump(raw_chunks, f, indent=2)

    def add_or_update_chunks(self, chunks: List[SemanticChunk], doc_id: str, doc_hash: str):
        """Add or update chunks for a document, recomputing embeddings for changed/new chunks."""
        # Remove any obsolete chunks for this document that are no longer present
        existing_doc_chunk_ids = [cid for cid, c in self.chunks.items() if c.document_id == doc_id]
        new_chunk_ids = {c.chunk_id for c in chunks}

        for cid in existing_doc_chunk_ids:
            if cid not in new_chunk_ids:
                self.chunks.pop(cid, None)
                self.vectors.pop(cid, None)

        # Embed and insert new/updated chunks
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            # Content embedded includes title, heading, and body
            embed_text = f"{chunk.title} {chunk.section_heading}\n{chunk.content}"
            self.vectors[chunk.chunk_id] = self.provider.embed_text(embed_text)

        if "doc_hashes" not in self.meta:
            self.meta["doc_hashes"] = {}
        self.meta["doc_hashes"][doc_id] = doc_hash

    def remove_document(self, doc_id: str):
        """Remove all chunks and vectors associated with a document ID."""
        chunk_ids_to_remove = [cid for cid, c in self.chunks.items() if c.document_id == doc_id]
        for cid in chunk_ids_to_remove:
            self.chunks.pop(cid, None)
            self.vectors.pop(cid, None)
        if "doc_hashes" in self.meta:
            self.meta["doc_hashes"].pop(doc_id, None)

    def search(
        self,
        query: str,
        top_k: int = 50,
        character_filter: Optional[str] = None,
        tier_filter: Optional[int] = None,
    ) -> List[Tuple[SemanticChunk, float]]:
        """Dense cosine similarity vector search over indexed semantic chunks."""
        if not self.vectors:
            return []

        q_vec = self.provider.embed_text(query)
        q_norm = math.sqrt(sum(x * x for x in q_vec))
        if q_norm < 1e-9:
            return []

        results: List[Tuple[SemanticChunk, float]] = []
        for chunk_id, vec in self.vectors.items():
            chunk = self.chunks.get(chunk_id)
            if not chunk:
                continue

            if character_filter:
                if not chunk.character or chunk.character.lower() != character_filter.lower():
                    continue

            if tier_filter and chunk.authority_tier > tier_filter:
                continue

            # Unit dot product equals cosine similarity
            sim = sum(q * v for q, v in zip(q_vec, vec))
            if sim > 0.0:
                results.append((chunk, float(sim)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


embedding_service = EmbeddingService()

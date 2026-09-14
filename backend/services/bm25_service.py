"""Lexical BM25 Okapi retrieval service for GenshinIQ semantic chunks.

Implements BM25 Okapi scoring with field-weighted term frequencies (headings,
characters, tags) and inverted index persistence for fast offline keyword matching.
"""

import json
import math
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from backend.models.knowledge import SemanticChunk


CHUNKS_FILE = os.path.join(os.getcwd(), "data", "runtime", "index", "chunks.json")


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


def tokenize(text: str, expand_synonyms: bool = False) -> List[str]:
    """Normalize and tokenize text into lowercase word tokens."""
    if not text:
        return []
    # Replace hyphens/underscores with space to capture split words as well as unified
    tokens = re.findall(r"\b[a-zA-Z0-9_']+\b", text.lower())
    clean_tokens = [t.strip("'") for t in tokens if len(t.strip("'")) > 1]
    if expand_synonyms:
        expanded = list(clean_tokens)
        for t in clean_tokens:
            if t in GENSHIN_DOMAIN_SYNONYMS:
                expanded.extend(GENSHIN_DOMAIN_SYNONYMS[t])
        return expanded
    return clean_tokens


class BM25Index:
    """BM25 Okapi inverted index with field boosting for semantic chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: Dict[str, SemanticChunk] = {}
        # term -> {chunk_id: weighted_tf}
        self.inverted_index: Dict[str, Dict[str, float]] = {}
        # chunk_id -> document length (total weighted tokens)
        self.doc_lens: Dict[str, float] = {}
        self.avg_doc_len: float = 0.0
        self._load_from_storage()

    def _load_from_storage(self):
        """Auto-populate inverted index from runtime chunks.json if available."""
        if os.path.exists(CHUNKS_FILE):
            try:
                with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for cid, raw in data.items():
                    chunk = SemanticChunk(**raw)
                    self._index_chunk(chunk)
                self._recompute_avgdl()
            except Exception:
                pass

    def clear(self):
        """Reset the index."""
        self.chunks.clear()
        self.inverted_index.clear()
        self.doc_lens.clear()
        self.avg_doc_len = 0.0

    def add_or_update_chunks(self, chunks: List[SemanticChunk], doc_id: str):
        """Add or update chunks for a document, updating inverted index and term statistics."""
        # First remove any chunks from this document
        self.remove_document(doc_id)

        for chunk in chunks:
            self._index_chunk(chunk)

        self._recompute_avgdl()

    def remove_document(self, doc_id: str):
        """Remove all chunks associated with a document ID."""
        cids_to_remove = [cid for cid, c in self.chunks.items() if c.document_id == doc_id]
        for cid in cids_to_remove:
            self.chunks.pop(cid, None)
            self.doc_lens.pop(cid, None)
            for term, postings in list(self.inverted_index.items()):
                postings.pop(cid, None)
                if not postings:
                    self.inverted_index.pop(term, None)

        self._recompute_avgdl()

    def _index_chunk(self, chunk: SemanticChunk):
        """Index a single semantic chunk with field-specific term weighting."""
        self.chunks[chunk.chunk_id] = chunk

        # Field tokenization with boosts
        title_tokens = tokenize(f"{chunk.title} {chunk.section_heading}")
        char_tokens = tokenize(chunk.character or "")
        topic_tokens = tokenize(chunk.topic)
        body_tokens = tokenize(chunk.content)

        weighted_tf: Dict[str, float] = {}

        # 1. Title & Heading tokens: 2.5x boost
        for t in title_tokens:
            weighted_tf[t] = weighted_tf.get(t, 0.0) + 2.5

        # 2. Character tokens: 2.0x boost
        for t in char_tokens:
            weighted_tf[t] = weighted_tf.get(t, 0.0) + 2.0

        # 3. Topic tokens: 1.5x boost
        for t in topic_tokens:
            weighted_tf[t] = weighted_tf.get(t, 0.0) + 1.5

        # 4. Body tokens: 1.0x
        for t in body_tokens:
            weighted_tf[t] = weighted_tf.get(t, 0.0) + 1.0

        total_tokens = sum(weighted_tf.values())
        self.doc_lens[chunk.chunk_id] = total_tokens

        for term, tf in weighted_tf.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
            self.inverted_index[term][chunk.chunk_id] = tf

    def _recompute_avgdl(self):
        """Update average document length."""
        if self.doc_lens:
            self.avg_doc_len = sum(self.doc_lens.values()) / len(self.doc_lens)
        else:
            self.avg_doc_len = 0.0

    def search(
        self,
        query: str,
        top_k: int = 50,
        character_filter: Optional[str] = None,
        tier_filter: Optional[int] = None,
    ) -> List[Tuple[SemanticChunk, float]]:
        """Compute BM25 Okapi scores for query against indexed chunks."""
        query_terms = tokenize(query, expand_synonyms=True)
        if not query_terms or not self.chunks or self.avg_doc_len == 0.0:
            return []

        num_docs = len(self.chunks)
        scores: Dict[str, float] = {}

        for term in set(query_terms):
            postings = self.inverted_index.get(term)
            if not postings:
                continue

            # IDF calculation with Robertson-Spärck Jones formula
            df = len(postings)
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            if idf <= 0.0:
                idf = 0.05  # Floor for very frequent terms

            for cid, tf in postings.items():
                chunk = self.chunks.get(cid)
                if not chunk:
                    continue

                if character_filter:
                    if not chunk.character or chunk.character.lower() != character_filter.lower():
                        continue

                if tier_filter and chunk.authority_tier > tier_filter:
                    continue

                doc_len = self.doc_lens.get(cid, self.avg_doc_len)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                term_score = idf * ((tf * (self.k1 + 1.0)) / denom)

                scores[cid] = scores.get(cid, 0.0) + term_score

        if not scores:
            return []

        ranked_results = [
            (self.chunks[cid], score)
            for cid, score in scores.items()
            if score > 0.0
        ]
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results[:top_k]


bm25_service = BM25Index()

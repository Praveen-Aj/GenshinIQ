"""Production indexing and rebuild script for GenshinIQ Phase 5 Retrieval.

Processes all curated knowledge documents from data/knowledge/, generates
context-preserving semantic chunks, builds the lexical BM25 index and dense
subword vector embeddings, and persists the index for fast sub-millisecond retrieval.

Usage:
    python scripts/rebuild_retrieval_index.py [--force] [--incremental]
"""

import argparse
import glob
import json
import os
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.models.knowledge import KnowledgeDocument
from backend.services.bm25_service import bm25_service
from backend.services.embedding_service import embedding_service
from backend.services.semantic_chunker import semantic_chunker

KNOWLEDGE_DIR = os.path.join(PROJECT_ROOT, "data", "knowledge")
INDEX_DIR = os.path.join(PROJECT_ROOT, "data", "runtime", "index")


def rebuild_index(force: bool = False):
    """Rebuild or incrementally update the retrieval index."""
    print("================================================================")
    print("  GenshinIQ Retrieval Layer — Index Builder (Phase 5)")
    print("================================================================")
    start_total = time.perf_counter()

    doc_files = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.json")))
    if not doc_files:
        print(f"ERROR: No knowledge documents found in {KNOWLEDGE_DIR}")
        sys.exit(1)

    print(f"Found {len(doc_files)} knowledge documents in data/knowledge/")
    print(f"Target index directory: {INDEX_DIR}")
    print(f"Embedding Model: {embedding_service.provider.model_name} ({embedding_service.provider.dimension}-dim)")

    if force:
        print("Mode: --force (Full index purge and rebuild)")
        embedding_service._clear_index()
        bm25_service.clear()
    else:
        print("Mode: Incremental update (skipping unchanged documents by content_hash)")

    indexed_docs = 0
    skipped_docs = 0
    total_chunks = 0
    current_doc_ids = set()

    # Load and process each document
    for file_path in doc_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc = KnowledgeDocument(**data)
        except Exception as e:
            print(f"WARNING: Skipping unparseable document {os.path.basename(file_path)}: {e}")
            continue

        current_doc_ids.add(doc.id)
        existing_hash = embedding_service.meta.get("doc_hashes", {}).get(doc.id)

        if not force and existing_hash == doc.metadata.content_hash:
            # Document unchanged
            skipped_docs += 1
            # Ensure chunks are loaded into BM25 if not present
            doc_chunks = [c for c in embedding_service.chunks.values() if c.document_id == doc.id]
            if not doc_chunks:
                # Chunks were not in memory, rechunk for BM25
                chunks = semantic_chunker.chunk_document(doc)
                bm25_service.add_or_update_chunks(chunks, doc.id)
            else:
                bm25_service.add_or_update_chunks(doc_chunks, doc.id)
            continue

        # Chunk document
        chunks = semantic_chunker.chunk_document(doc)
        total_chunks += len(chunks)

        # Update Vector Index
        embedding_service.add_or_update_chunks(chunks, doc.id, doc.metadata.content_hash)

        # Update BM25 Index
        bm25_service.add_or_update_chunks(chunks, doc.id)

        indexed_docs += 1

    # Detect deleted documents and prune
    indexed_doc_ids = set(embedding_service.meta.get("doc_hashes", {}).keys())
    pruned_docs = 0
    for stale_id in indexed_doc_ids - current_doc_ids:
        print(f"Pruning removed document: {stale_id}")
        embedding_service.remove_document(stale_id)
        bm25_service.remove_document(stale_id)
        pruned_docs += 1

    # Save to disk
    save_start = time.perf_counter()
    embedding_service.save_index()
    save_duration = (time.perf_counter() - save_start) * 1000

    total_duration = (time.perf_counter() - start_total)

    # Calculate index storage size
    index_bytes = 0
    for root, _, files in os.walk(INDEX_DIR):
        for file in files:
            index_bytes += os.path.getsize(os.path.join(root, file))

    print("\n----------------------------------------------------------------")
    print("  Index Summary:")
    print(f"  - Documents indexed/updated: {indexed_docs}")
    print(f"  - Documents skipped (unchanged): {skipped_docs}")
    print(f"  - Documents pruned: {pruned_docs}")
    print(f"  - Total semantic chunks in index: {len(embedding_service.chunks)}")
    print(f"  - Lexical terms in BM25 vocabulary: {len(bm25_service.inverted_index)}")
    print(f"  - Index file size on disk: {index_bytes / (1024 * 1024):.2f} MB")
    print(f"  - Disk save time: {save_duration:.1f}ms")
    print(f"  - Total execution time: {total_duration:.2f}s")
    print("================================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build GenshinIQ Retrieval Index")
    parser.add_argument("--force", action="store_true", help="Force complete rebuild from scratch")
    parser.add_argument("--incremental", action="store_true", help="Incremental build based on content hash")
    args = parser.parse_args()

    rebuild_index(force=args.force)

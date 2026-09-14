"""Semantic chunker for GenshinIQ knowledge documents.

Splits markdown documents into meaningful, context-preserving semantic chunks
along heading boundaries while preserving tables, formulas, lists, and full provenance.
"""

import re
from typing import List, Optional
from backend.models.knowledge import KnowledgeDocument, SemanticChunk


def slugify(text: str) -> str:
    """Generate a URL-safe lowercase slug from a heading string."""
    clean = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", clean).strip("-") or "section"


class SemanticChunker:
    """Segments knowledge documents into coherent, context-rich chunks."""

    def __init__(self, max_chunk_words: int = 500, min_chunk_words: int = 15):
        self.max_chunk_words = max_chunk_words
        self.min_chunk_words = min_chunk_words

    def chunk_document(self, doc: KnowledgeDocument) -> List[SemanticChunk]:
        """Split a KnowledgeDocument into semantic chunks preserving all metadata."""
        content = doc.content.strip()
        if not content:
            return []

        # Split into heading-based sections
        sections = self._split_by_headings(doc.title, content)

        # If splitting resulted in no sections or just one tiny section, wrap the document
        if not sections:
            sections = [(doc.title, content)]

        # Consolidate very small sections with subsequent/previous ones if appropriate,
        # or split very large sections at paragraph boundaries without breaking tables/formulas.
        normalized_sections = self._normalize_sections(doc.title, sections)

        chunks: List[SemanticChunk] = []
        slug_counts: dict = {}

        for idx, (heading, body) in enumerate(normalized_sections):
            base_slug = slugify(heading)
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                chunk_slug = f"{base_slug}-{slug_counts[base_slug]}"
            else:
                slug_counts[base_slug] = 1
                chunk_slug = base_slug

            chunk_id = f"{doc.id}#{chunk_slug}"
            word_count = len(body.split())

            # Format body with title and heading breadcrumb for standalone legibility
            formatted_content = f"### {doc.title} — {heading}\n\n{body.strip()}"

            chunk = SemanticChunk(
                chunk_id=chunk_id,
                document_id=doc.id,
                title=doc.title,
                section_heading=heading,
                content=formatted_content,
                character=doc.metadata.character,
                topic=doc.metadata.topic,
                game_version=doc.metadata.game_version,
                freshness_status=doc.metadata.freshness_status or "current",
                affected_systems=doc.metadata.affected_systems,
                source_id=doc.metadata.source_id,
                source=doc.metadata.source,
                source_url=doc.metadata.source_url,
                canonical_url=doc.metadata.canonical_url,
                authority_tier=doc.metadata.authority_tier,
                source_type=doc.metadata.source_type,
                content_hash=doc.metadata.content_hash,
                chunk_index=idx,
                token_count=word_count,
            )
            chunks.append(chunk)

        return chunks

    def _split_by_headings(self, doc_title: str, content: str) -> List[tuple]:
        """Parse markdown lines and group into (heading_breadcrumb, section_text)."""
        lines = content.split("\n")
        sections = []
        current_heading = doc_title
        current_lines = []
        h1_title = ""

        # Heading regex for #, ##, ###
        heading_re = re.compile(r"^(#{1,3})\s+(.+)$")

        for line in lines:
            match = heading_re.match(line.strip())
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()

                if level == 1:
                    # Top-level title
                    h1_title = heading_text
                    if current_lines:
                        body = "\n".join(current_lines).strip()
                        if body:
                            sections.append((current_heading, body))
                        current_lines = []
                    current_heading = heading_text
                else:
                    # Subheading (## or ###)
                    if current_lines:
                        body = "\n".join(current_lines).strip()
                        if body:
                            sections.append((current_heading, body))
                        current_lines = []
                    
                    if h1_title and heading_text != h1_title:
                        current_heading = heading_text
                    else:
                        current_heading = heading_text
            else:
                current_lines.append(line)

        if current_lines:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_heading, body))

        return sections

    def _normalize_sections(self, doc_title: str, sections: List[tuple]) -> List[tuple]:
        """Ensure sections are neither too small nor split across delicate structures."""
        result = []
        pending_body = []

        for heading, body in sections:
            words = len(body.split())

            # If section is tiny (< min_chunk_words) and not a table/formula, accumulate into subsequent section
            if words < self.min_chunk_words and not ("|" in body or "$$" in body):
                pending_body.append(body.strip())
                continue

            # If we had pending introductory content (e.g., banner image, short disclaimer), prepend it
            if pending_body:
                body = "\n\n".join(pending_body) + "\n\n" + body
                pending_body = []

            # If section is very large, split on paragraphs without breaking tables or formulas
            if words > self.max_chunk_words:
                sub_chunks = self._split_large_body(heading, body)
                result.extend(sub_chunks)
            else:
                result.append((heading, body))

        if pending_body:
            trailing_text = "\n\n".join(pending_body)
            if result:
                last_heading, last_body = result[-1]
                result[-1] = (last_heading, f"{last_body}\n\n{trailing_text}")
            else:
                result.append((doc_title, trailing_text))

        return result

    def _split_large_body(self, heading: str, body: str) -> List[tuple]:
        """Split a large section at paragraph boundaries while keeping tables & code blocks intact."""
        paragraphs = body.split("\n\n")
        chunks = []
        current_para_group = []
        current_words = 0
        in_code_or_table = False

        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue

            # Check if this paragraph is part of a table or code fence
            is_table_or_code = "|" in para_clean or "```" in para_clean or "$$" in para_clean
            p_words = len(para_clean.split())

            if (current_words + p_words > self.max_chunk_words) and current_para_group and not is_table_or_code:
                # Flush group
                part_idx = len(chunks) + 1
                sub_heading = f"{heading} (Part {part_idx})"
                chunks.append((sub_heading, "\n\n".join(current_para_group)))
                current_para_group = [para_clean]
                current_words = p_words
            else:
                current_para_group.append(para_clean)
                current_words += p_words

        if current_para_group:
            part_idx = len(chunks) + 1
            sub_heading = f"{heading} (Part {part_idx})" if chunks else heading
            chunks.append((sub_heading, "\n\n".join(current_para_group)))

        return chunks


semantic_chunker = SemanticChunker()

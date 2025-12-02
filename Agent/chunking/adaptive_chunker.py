from typing import List, Dict, Tuple
import re
from .base_chunker import BaseChunker


class AdaptiveChunker(BaseChunker):
    """Adaptive chunking based on document size with section-aware splitting"""

    def __init__(self):
        # Define size thresholds and corresponding chunk configs
        # Increased sizes for better context preservation
        self.size_configs = [
            {"max_chars": 5000, "chunk_size": 1200, "overlap": 250},      # Small docs
            {"max_chars": 20000, "chunk_size": 1800, "overlap": 350},     # Medium docs
            {"max_chars": 50000, "chunk_size": 2500, "overlap": 500},     # Large docs
            {"max_chars": float("inf"), "chunk_size": 3000, "overlap": 600},  # Very large docs
        ]

        # Section header patterns for policy documents
        self.section_patterns = [
            r"^Section\s+\d+\.?\d*\.?\d*",  # Section 1, Section 1.1, Section 1.1.1
            r"^\d+\.?\d*\.?\d*\s+[A-Z]",    # 1. Title, 1.1 Title, 1.1.1 Title
            r"^[A-Z][A-Z\s]+:$",            # ALL CAPS HEADER:
            r"^Chapter\s+\d+",              # Chapter 1
            r"^Article\s+\d+",              # Article 1
            r"^Part\s+[IVX]+",              # Part I, Part II
            r"^\d+\)\s+[A-Z]",              # 1) Title
        ]

    def _get_chunk_config(self, text_length: int) -> Dict:
        """Determine chunk size and overlap based on document size"""
        for config in self.size_configs:
            if text_length <= config["max_chars"]:
                return {"chunk_size": config["chunk_size"], "overlap": config["overlap"]}
        return {"chunk_size": 3000, "overlap": 600}

    def _detect_sections(self, text: str) -> List[Tuple[int, str]]:
        """
        Detect section headers in text

        Returns:
            List of (position, header_text) tuples
        """
        sections: List[Tuple[int, str]] = []
        lines = text.split("\n")
        current_pos = 0

        for line in lines:
            line_stripped = line.strip()
            if line_stripped:
                # Check if line matches any section pattern
                for pattern in self.section_patterns:
                    if re.match(pattern, line_stripped):
                        sections.append((current_pos, line_stripped))
                        break
            # +1 to account for the newline that was split
            current_pos += len(line) + 1

        return sections

    def _is_section_boundary(self, text: str, position: int, sections: List[Tuple[int, str]]) -> bool:
        """Check if position is near a section boundary"""
        for section_pos, _ in sections:
            # If we're within 100 chars of a section, it's a boundary
            if abs(position - section_pos) < 100:
                return True
        return False

    def _find_best_break_point(
        self,
        text: str,
        start: int,
        ideal_end: int,
        sections: List[Tuple[int, str]],
    ) -> int:
        """
        Find the best break point for chunking, preferring section boundaries

        Args:
            text: Full text
            start: Start position of chunk
            ideal_end: Ideal end position based on chunk_size
            sections: List of detected section positions

        Returns:
            Best break point position
        """
        chunk_text = text[start:ideal_end]

        # First, check if there's a section boundary within the chunk,
        # and it's at least 50% into the chunk
        for section_pos, _ in sections:
            if start < section_pos < ideal_end:
                if section_pos > start + len(chunk_text) * 0.5:
                    return section_pos

        # No section boundary, try a sentence or line boundary
        last_period = chunk_text.rfind(".")
        last_newline = chunk_text.rfind("\n")
        break_point = max(last_period, last_newline)

        # Only break if we're past 70% of the chunk
        if break_point > len(chunk_text) * 0.7:
            return start + break_point + 1

        # Default to ideal end
        return ideal_end

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]: # type: ignore
        """
        Chunk text adaptively based on document size with section-aware splitting

        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of dicts with 'text' and 'metadata' keys
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        text_length = len(text)

        # Base config (chunk_size & overlap)
        config = self._get_chunk_config(text_length)
        chunk_size = int(config["chunk_size"])
        overlap = int(config["overlap"])

        # Safety: never let overlap be >= chunk_size
        if overlap >= chunk_size:
            overlap = max(0, chunk_size // 2)

        # Detect sections in the document
        sections = self._detect_sections(text)

        chunks: List[Dict] = []
        start = 0
        chunk_index = 0

        while start < text_length:
            ideal_end = start + chunk_size

            # Find best break point (prefer section boundaries)
            if ideal_end < text_length:
                end = self._find_best_break_point(text, start, ideal_end, sections)
            else:
                end = text_length

            # Safety: ensure end moves forward
            if end <= start:
                end = min(text_length, start + chunk_size)
                if end <= start:
                    # Cannot make progress; break to avoid infinite loop
                    break

            raw_chunk_text = text[start:end]
            chunk_text = raw_chunk_text.strip()

            # Skip empty chunks but still force progress
            if not chunk_text:
                start = end
                continue

            # Detect if this chunk starts with a section header
            section_header = None
            for section_pos, header in sections:
                # Section header within first 200 chars of this chunk
                if start <= section_pos < start + 200:
                    section_header = header
                    break

            # Build metadata for this chunk
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update(
                {
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text),
                    "total_doc_size": text_length,
                    # This field is redundant with "text" but kept for your BM25 usage
                    "chunk_text": chunk_text,
                    "section_header": section_header,
                    "has_section": section_header is not None,
                    "start_char": start,
                    "end_char": end,
                }
            )

            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": chunk_metadata,
                }
            )

            # --- Compute next_start with overlap ---
            next_start = end - overlap

            # If there's a section boundary between end-overlap and end, start after it
            for section_pos, _ in sections:
                if next_start < section_pos <= end:
                    next_start = section_pos
                    break

            # Ensure valid index
            next_start = max(0, next_start)

            # ✅ Ensure progress; if overlap logic doesn't move us forward,
            # jump to end to avoid infinite loop.
            if next_start <= start:
                next_start = end

            # Last safety: if we still can't move, break
            if next_start <= start:
                break

            start = next_start
            chunk_index += 1

        return chunks

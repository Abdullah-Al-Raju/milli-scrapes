"""
Semantic Content Chunker for RAG and Vector Databases.
Splits dense Markdown content into semantically coherent, token-estimated chunks.
Preserves heading hierarchies, list structures, and sentence boundaries.
"""

import re
from typing import List, Dict, Any, Optional


class MilliChunker:
    """
    RAG-ready chunking engine supporting heading-based, sentence-based,
    and sliding-window chunking strategies.
    """

    @classmethod
    def chunk_markdown(
        cls,
        markdown: str,
        chunk_size: int = 500,
        overlap: int = 50,
        strategy: str = "heading"
    ) -> List[Dict[str, Any]]:
        """
        Chunks markdown content into structured segments.
        strategy options:
        - 'heading': Splices markdown cleanly at heading levels while preserving hierarchy breadcrumbs.
        - 'sentence': Splits on sentence terminations (., !, ?) without cutting thoughts in half.
        - 'sliding': Sliding word-window with overlap.
        """
        if not markdown or not markdown.strip():
            return []

        if strategy == "heading":
            return cls._chunk_by_headings(markdown, chunk_size)
        elif strategy == "sentence":
            return cls._chunk_by_sentences(markdown, chunk_size, overlap)
        else:
            return cls._chunk_sliding(markdown, chunk_size, overlap)

    @classmethod
    def _chunk_by_headings(cls, markdown: str, max_chunk_words: int) -> List[Dict[str, Any]]:
        """Splits markdown by headings and maintains active breadcrumbs."""
        lines = markdown.splitlines()
        chunks: List[Dict[str, Any]] = []

        current_headings: Dict[int, str] = {}
        current_lines: List[str] = []
        chunk_index = 0

        def _flush():
            nonlocal current_lines, chunk_index
            text = "\n".join(current_lines).strip()
            if text:
                breadcrumbs = [current_headings[k] for k in sorted(current_headings.keys())]
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": text,
                    "breadcrumbs": breadcrumbs,
                    "token_estimate": cls.estimate_tokens(text),
                    "char_count": len(text)
                })
                chunk_index += 1
            current_lines = []

        for line in lines:
            h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if h_match:
                level = len(h_match.group(1))
                title = h_match.group(2).strip()

                # Flush current accumulator if non-empty
                if current_lines:
                    _flush()

                # Update breadcrumb hierarchy
                current_headings = {k: v for k, v in current_headings.items() if k < level}
                current_headings[level] = title
                current_lines.append(line)
            else:
                current_lines.append(line)
                # If chunk exceeds max size, flush
                words = len(" ".join(current_lines).split())
                if words >= max_chunk_words:
                    _flush()

        if current_lines:
            _flush()

        return chunks

    @classmethod
    def _chunk_by_sentences(cls, markdown: str, chunk_size_words: int, overlap_words: int) -> List[Dict[str, Any]]:
        """Chunks on sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", markdown)
        chunks: List[Dict[str, Any]] = []
        current_sentences: List[str] = []
        current_words = 0
        chunk_index = 0

        for sentence in sentences:
            s_words = len(sentence.split())
            if current_words + s_words > chunk_size_words and current_sentences:
                text = " ".join(current_sentences).strip()
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": text,
                    "token_estimate": cls.estimate_tokens(text),
                    "char_count": len(text)
                })
                chunk_index += 1
                # Retain overlap
                if overlap_words > 0 and len(current_sentences) > 1:
                    current_sentences = current_sentences[-2:]
                    current_words = sum(len(s.split()) for s in current_sentences)
                else:
                    current_sentences = []
                    current_words = 0

            current_sentences.append(sentence)
            current_words += s_words

        if current_sentences:
            text = " ".join(current_sentences).strip()
            chunks.append({
                "chunk_index": chunk_index,
                "text": text,
                "token_estimate": cls.estimate_tokens(text),
                "char_count": len(text)
            })

        return chunks

    @classmethod
    def _chunk_sliding(cls, markdown: str, chunk_size_words: int, overlap_words: int) -> List[Dict[str, Any]]:
        """Standard sliding window over word tokens."""
        words = markdown.split()
        chunks: List[Dict[str, Any]] = []
        step = max(1, chunk_size_words - overlap_words)
        chunk_index = 0

        for i in range(0, len(words), step):
            slice_words = words[i: i + chunk_size_words]
            text = " ".join(slice_words).strip()
            chunks.append({
                "chunk_index": chunk_index,
                "text": text,
                "token_estimate": cls.estimate_tokens(text),
                "char_count": len(text)
            })
            chunk_index += 1

        return chunks

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Approximates LLM token count (~1.3 tokens per whitespace-separated word)."""
        words = len(text.split())
        return int(words * 1.3) + 1

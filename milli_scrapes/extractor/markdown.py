"""
Fast HTML to LLM-ready Markdown Extractor.
Optimized for token efficiency and high throughput.
Strips boilerplate (scripts, styles, navigation, ads, cookie notices) and formats structured markdown and tables.
"""

import re
from html import unescape
from typing import Dict, Any, Optional, Tuple, List


class HTMLToMarkdownExtractor:
    """
    Transforms arbitrary HTML strings into dense, clean, token-efficient Markdown.
    Includes support for GFM tables, metadata extraction, and aggressive boilerplate stripping.
    """

    # Elements to completely strip including their contents
    DISCARD_TAGS = [
        r"<head\b[^>]*>[\s\S]*?<\/head>",
        r"<script\b[^>]*>[\s\S]*?<\/script>",
        r"<style\b[^>]*>[\s\S]*?<\/style>",
        r"<noscript\b[^>]*>[\s\S]*?<\/noscript>",
        r"<svg\b[^>]*>[\s\S]*?<\/svg>",
        r"<iframe\b[^>]*>[\s\S]*?<\/iframe>",
        r"<!--[\s\S]*?-->"
    ]

    # Boilerplate patterns (cookie notices, banners, modals, tracking overlays)
    CLUTTER_PATTERNS = [
        r'<div\b[^>]*(?:cookie|consent|banner|onetrust|gdpr|advertisement|ad-container)[^>]*>[\s\S]*?<\/div>',
        r'<section\b[^>]*(?:cookie|consent|banner|advertisement)[^>]*>[\s\S]*?<\/section>',
        r'<aside\b[^>]*>[\s\S]*?<\/aside>'
    ]

    # Pre-compiled high-throughput regex engine
    _COMPILED_DISCARD = [re.compile(p, re.IGNORECASE) for p in DISCARD_TAGS]
    _COMPILED_CLUTTER = [re.compile(p, re.IGNORECASE) for p in CLUTTER_PATTERNS]
    _RE_NAV = re.compile(r"<nav\b[^>]*>[\s\S]*?<\/nav>", re.IGNORECASE)
    _RE_FOOTER = re.compile(r"<footer\b[^>]*>[\s\S]*?<\/footer>", re.IGNORECASE)
    _RE_TABLE = re.compile(r"<table\b[^>]*>[\s\S]*?<\/table>", re.IGNORECASE)
    _RE_HEADINGS = [(re.compile(rf"<h{i}\b[^>]*>(.*?)<\/h{i}>", re.IGNORECASE | re.DOTALL), f"\n\n{'#' * i} \\1\n\n") for i in range(6, 0, -1)]
    _RE_STRONG = re.compile(r"<(strong|b)\b[^>]*>(.*?)<\/\1>", re.IGNORECASE | re.DOTALL)
    _RE_EM = re.compile(r"<(em|i)\b[^>]*>(.*?)<\/\1>", re.IGNORECASE | re.DOTALL)
    _RE_PRE_CODE = re.compile(r"<pre\b[^>]*><code\b[^>]*>(.*?)<\/code><\/pre>", re.IGNORECASE | re.DOTALL)
    _RE_CODE = re.compile(r"<code\b[^>]*>(.*?)<\/code>", re.IGNORECASE | re.DOTALL)
    _RE_A = re.compile(r"<a\b([^>]*)>(.*?)<\/a>", re.IGNORECASE | re.DOTALL)
    _RE_HREF = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    _RE_LI = re.compile(r"<li\b[^>]*>(.*?)<\/li>", re.IGNORECASE | re.DOTALL)
    _RE_BR = re.compile(r"<br\s*\/?>", re.IGNORECASE)
    _RE_P = re.compile(r"<p\b[^>]*>(.*?)<\/p>", re.IGNORECASE | re.DOTALL)
    _RE_DIV = re.compile(r"<div\b[^>]*>(.*?)<\/div>", re.IGNORECASE | re.DOTALL)
    _RE_STRIP_TAGS = re.compile(r"<[^>]+>")

    def __init__(self, strip_nav_footer: bool = True, strip_clutter: bool = True):
        self.strip_nav_footer = strip_nav_footer
        self.strip_clutter = strip_clutter

    def extract(self, html: str) -> str:
        """Parses HTML and emits clean Markdown text."""
        md, _ = self.extract_with_metadata(html)
        return md

    def extract_with_metadata(self, html: str) -> Tuple[str, Dict[str, Any]]:
        """Parses HTML and returns both clean Markdown and extracted document metadata."""
        if not html:
            return "", {}

        # 0. Extract metadata before stripping tags
        metadata = self._extract_metadata(html)

        text = html

        # Strip unneeded blocks
        for pat in self._COMPILED_DISCARD:
            text = pat.sub("", text)

        if self.strip_clutter:
            for pat in self._COMPILED_CLUTTER:
                text = pat.sub("", text)

        if self.strip_nav_footer:
            text = self._RE_NAV.sub("", text)
            text = self._RE_FOOTER.sub("", text)

        # 1. Convert HTML Tables to GitHub-Flavored Markdown Tables
        text = self._RE_TABLE.sub(self._table_to_markdown, text)

        # 2. Headings
        for h_re, repl in self._RE_HEADINGS:
            text = h_re.sub(repl, text)

        # 3. Bold & Italic
        text = self._RE_STRONG.sub(r"**\2**", text)
        text = self._RE_EM.sub(r"*\2*", text)

        # 4. Code blocks and inline code
        text = self._RE_PRE_CODE.sub(r"\n```\n\1\n```\n", text)
        text = self._RE_CODE.sub(r"`\1`", text)

        # 5. Links
        def _link_sub(match):
            attrs = match.group(1)
            inner = match.group(2).strip()
            href_m = self._RE_HREF.search(attrs)
            if href_m and inner and not inner.startswith("<img"):
                href = href_m.group(1)
                return f"[{inner}]({href})"
            return inner

        text = self._RE_A.sub(_link_sub, text)

        # 6. List items
        text = self._RE_LI.sub(r"\n* \1", text)

        # 7. Paragraphs and line breaks
        text = self._RE_BR.sub("\n", text)
        text = self._RE_P.sub(r"\n\n\1\n\n", text)
        text = self._RE_DIV.sub(r"\n\1\n", text)

        # 8. Strip all remaining tags
        text = self._RE_STRIP_TAGS.sub("", text)

        # 9. Decode HTML entities
        text = unescape(text)

        # 10. Normalize whitespace and blank lines
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        consecutive_blank = 0
        for line in lines:
            if not line:
                consecutive_blank += 1
                if consecutive_blank <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_blank = 0
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip(), metadata

    _RE_TR = re.compile(r"<tr\b[^>]*>(.*?)<\/tr>", re.IGNORECASE | re.DOTALL)
    _RE_TH = re.compile(r"<th\b[^>]*>(.*?)<\/th>", re.IGNORECASE | re.DOTALL)
    _RE_TDH = re.compile(r"<t[dh]\b[^>]*>(.*?)<\/t[dh]>", re.IGNORECASE | re.DOTALL)
    _RE_TITLE = re.compile(r"<title\b[^>]*>(.*?)<\/title>", re.IGNORECASE | re.DOTALL)
    _RE_META = re.compile(r"<meta\b([^>]+)>", re.IGNORECASE)
    _RE_PROP = re.compile(r'(?:name|property)=["\']([^"\']+)["\']', re.IGNORECASE)
    _RE_CONTENT = re.compile(r'content=["\']([^"\']*)["\']', re.IGNORECASE)
    _RE_CANONICAL = re.compile(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.IGNORECASE)

    def _table_to_markdown(self, match: re.Match) -> str:
        """Converts an HTML <table> into a GitHub-Flavored Markdown table."""
        tbl_html = match.group(0)
        rows = self._RE_TR.findall(tbl_html)
        if not rows:
            return ""

        md_rows: List[str] = []
        headers: List[str] = []

        # Check first row for th headers
        first_th = self._RE_TH.findall(rows[0])
        if first_th:
            headers = [self._clean_cell(th) for th in first_th]
            md_rows.append("| " + " | ".join(headers) + " |")
            md_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
            rows = rows[1:]

        for r in rows:
            cells = self._RE_TDH.findall(r)
            clean_cells = [self._clean_cell(c).replace("|", "\\|") for c in cells]
            if clean_cells:
                if not headers:
                    headers = [f"Col {i+1}" for i in range(len(clean_cells))]
                    md_rows.append("| " + " | ".join(headers) + " |")
                    md_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")

                # Align row length with header length
                while len(clean_cells) < len(headers):
                    clean_cells.append("")
                clean_cells = clean_cells[:len(headers)]
                md_rows.append("| " + " | ".join(clean_cells) + " |")

        if not md_rows:
            return ""
        return "\n\n" + "\n".join(md_rows) + "\n\n"

    def _clean_cell(self, cell_html: str) -> str:
        """Cleans and extracts inner text from a table cell."""
        text = self._RE_STRIP_TAGS.sub("", cell_html)
        return unescape(text).strip()

    def _extract_metadata(self, html: str) -> Dict[str, Any]:
        """Extracts OpenGraph, Twitter, and standard HTML meta tags."""
        meta: Dict[str, Any] = {}

        # Title
        title_m = self._RE_TITLE.search(html)
        if title_m:
            meta["title"] = unescape(title_m.group(1).strip())

        # Meta tags
        meta_tags = self._RE_META.findall(html)
        for tag in meta_tags:
            prop_m = self._RE_PROP.search(tag)
            content_m = self._RE_CONTENT.search(tag)
            if prop_m and content_m:
                key = prop_m.group(1).strip().lower()
                val = unescape(content_m.group(1).strip())
                if key in ("description", "og:description", "twitter:description") and "description" not in meta:
                    meta["description"] = val
                elif key in ("og:title", "twitter:title") and "og_title" not in meta:
                    meta["og_title"] = val
                elif key in ("og:image", "twitter:image") and "image" not in meta:
                    meta["image"] = val
                elif key == "author" and "author" not in meta:
                    meta["author"] = val

        # Canonical URL
        canon_m = self._RE_CANONICAL.search(html)
        if canon_m:
            meta["canonical"] = canon_m.group(1).strip()

        return meta


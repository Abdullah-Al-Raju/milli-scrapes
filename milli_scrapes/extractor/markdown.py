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
        for pat in self.DISCARD_TAGS:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)

        if self.strip_clutter:
            for pat in self.CLUTTER_PATTERNS:
                text = re.sub(pat, "", text, flags=re.IGNORECASE)

        if self.strip_nav_footer:
            text = re.sub(r"<nav\b[^>]*>[\s\S]*?<\/nav>", "", text, flags=re.IGNORECASE)
            text = re.sub(r"<footer\b[^>]*>[\s\S]*?<\/footer>", "", text, flags=re.IGNORECASE)

        # 1. Convert HTML Tables to GitHub-Flavored Markdown Tables
        text = re.sub(r"<table\b[^>]*>[\s\S]*?<\/table>", self._table_to_markdown, text, flags=re.IGNORECASE)

        # 2. Headings
        for i in range(6, 0, -1):
            h_pat = rf"<h{i}\b[^>]*>(.*?)<\/h{i}>"
            prefix = "#" * i + " "
            text = re.sub(h_pat, rf"\n\n{prefix}\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)

        # 3. Bold & Italic
        text = re.sub(r"<(strong|b)\b[^>]*>(.*?)<\/\1>", r"**\2**", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<(em|i)\b[^>]*>(.*?)<\/\1>", r"*\2*", text, flags=re.IGNORECASE | re.DOTALL)

        # 4. Code blocks and inline code
        text = re.sub(r"<pre\b[^>]*><code\b[^>]*>(.*?)<\/code><\/pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<code\b[^>]*>(.*?)<\/code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)

        # 5. Links
        def _link_sub(match):
            attrs = match.group(1)
            inner = match.group(2).strip()
            href_m = re.search(r'href=["\']([^"\']+)["\']', attrs, flags=re.IGNORECASE)
            if href_m and inner and not inner.startswith("<img"):
                href = href_m.group(1)
                return f"[{inner}]({href})"
            return inner

        text = re.sub(r"<a\b([^>]*)>(.*?)<\/a>", _link_sub, text, flags=re.IGNORECASE | re.DOTALL)

        # 6. List items
        text = re.sub(r"<li\b[^>]*>(.*?)<\/li>", r"\n* \1", text, flags=re.IGNORECASE | re.DOTALL)

        # 7. Paragraphs and line breaks
        text = re.sub(r"<br\s*\/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<p\b[^>]*>(.*?)<\/p>", r"\n\n\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<div\b[^>]*>(.*?)<\/div>", r"\n\1\n", text, flags=re.IGNORECASE | re.DOTALL)

        # 8. Strip all remaining tags
        text = re.sub(r"<[^>]+>", "", text)

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

    def _table_to_markdown(self, match: re.Match) -> str:
        """Converts an HTML <table> into a GitHub-Flavored Markdown table."""
        tbl_html = match.group(0)
        rows = re.findall(r"<tr\b[^>]*>(.*?)<\/tr>", tbl_html, flags=re.IGNORECASE | re.DOTALL)
        if not rows:
            return ""

        md_rows: List[str] = []
        headers: List[str] = []

        # Check first row for th headers
        first_th = re.findall(r"<th\b[^>]*>(.*?)<\/th>", rows[0], flags=re.IGNORECASE | re.DOTALL)
        if first_th:
            headers = [self._clean_cell(th) for th in first_th]
            md_rows.append("| " + " | ".join(headers) + " |")
            md_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
            rows = rows[1:]

        for r in rows:
            cells = re.findall(r"<t[dh]\b[^>]*>(.*?)<\/t[dh]>", r, flags=re.IGNORECASE | re.DOTALL)
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
        text = re.sub(r"<[^>]+>", "", cell_html)
        return unescape(text).strip()

    def _extract_metadata(self, html: str) -> Dict[str, Any]:
        """Extracts OpenGraph, Twitter, and standard HTML meta tags."""
        meta: Dict[str, Any] = {}

        # Title
        title_m = re.search(r"<title\b[^>]*>(.*?)<\/title>", html, flags=re.IGNORECASE | re.DOTALL)
        if title_m:
            meta["title"] = unescape(title_m.group(1).strip())

        # Meta tags
        meta_tags = re.findall(r"<meta\b([^>]+)>", html, flags=re.IGNORECASE)
        for tag in meta_tags:
            prop_m = re.search(r'(?:name|property)=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
            content_m = re.search(r'content=["\']([^"\']*)["\']', tag, flags=re.IGNORECASE)
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
        canon_m = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
        if canon_m:
            meta["canonical"] = canon_m.group(1).strip()

        return meta


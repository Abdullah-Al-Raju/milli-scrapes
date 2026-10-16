"""
Fast HTML to LLM-ready Markdown Extractor.
Optimized for token efficiency and high throughput.
Strips boilerplate (scripts, styles, navigation, trackers) and formats structured markdown.
"""

import re
from html import unescape


class HTMLToMarkdownExtractor:
    """
    Transforms arbitrary HTML strings into dense, clean, token-efficient Markdown.
    """

    # Elements to completely strip including their contents
    DISCARD_TAGS = [
        r"<script\b[^>]*>[\s\S]*?<\/script>",
        r"<style\b[^>]*>[\s\S]*?<\/style>",
        r"<noscript\b[^>]*>[\s\S]*?<\/noscript>",
        r"<svg\b[^>]*>[\s\S]*?<\/svg>",
        r"<iframe\b[^>]*>[\s\S]*?<\/iframe>",
        r"<!--[\s\S]*?-->"
    ]

    def __init__(self, strip_nav_footer: bool = True):
        self.strip_nav_footer = strip_nav_footer

    def extract(self, html: str) -> str:
        """Parses HTML and emits clean Markdown text."""
        if not html:
            return ""

        text = html

        # Strip unneeded blocks
        for pat in self.DISCARD_TAGS:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)

        if self.strip_nav_footer:
            text = re.sub(r"<nav\b[^>]*>[\s\S]*?<\/nav>", "", text, flags=re.IGNORECASE)
            text = re.sub(r"<footer\b[^>]*>[\s\S]*?<\/footer>", "", text, flags=re.IGNORECASE)

        # Headings
        for i in range(6, 0, -1):
            h_pat = rf"<h{i}\b[^>]*>(.*?)<\/h{i}>"
            prefix = "#" * i + " "
            text = re.sub(h_pat, rf"\n\n{prefix}\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)

        # Bold & Italic
        text = re.sub(r"<(strong|b)\b[^>]*>(.*?)<\/\1>", r"**\2**", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<(em|i)\b[^>]*>(.*?)<\/\1>", r"*\2*", text, flags=re.IGNORECASE | re.DOTALL)

        # Code blocks and inline code
        text = re.sub(r"<pre\b[^>]*><code\b[^>]*>(.*?)<\/code><\/pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<code\b[^>]*>(.*?)<\/code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)

        # Links
        def _link_sub(match):
            attrs = match.group(1)
            inner = match.group(2).strip()
            href_m = re.search(r'href=["\']([^"\']+)["\']', attrs, flags=re.IGNORECASE)
            if href_m and inner and not inner.startswith("<img"):
                href = href_m.group(1)
                return f"[{inner}]({href})"
            return inner

        text = re.sub(r"<a\b([^>]*)>(.*?)<\/a>", _link_sub, text, flags=re.IGNORECASE | re.DOTALL)

        # List items
        text = re.sub(r"<li\b[^>]*>(.*?)<\/li>", r"\n* \1", text, flags=re.IGNORECASE | re.DOTALL)

        # Paragraphs and line breaks
        text = re.sub(r"<br\s*\/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<p\b[^>]*>(.*?)<\/p>", r"\n\n\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<div\b[^>]*>(.*?)<\/div>", r"\n\1\n", text, flags=re.IGNORECASE | re.DOTALL)

        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = unescape(text)

        # Normalize whitespace and blank lines
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

        return "\n".join(cleaned_lines).strip()

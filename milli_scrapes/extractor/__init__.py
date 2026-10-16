"""
Milli-Scrapes Data Extraction Subsystem.
Converts raw HTML into LLM-ready clean Markdown and structured JSON.
"""

from .markdown import HTMLToMarkdownExtractor
from .structured import StructuredDataExtractor

__all__ = ["HTMLToMarkdownExtractor", "StructuredDataExtractor"]

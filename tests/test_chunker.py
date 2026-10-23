"""
Unit tests for MilliChunker.
"""

import unittest
from milli_scrapes.extractor.chunker import MilliChunker


class TestMilliChunker(unittest.TestCase):

    def setUp(self):
        self.sample_markdown = """
# Getting Started

Welcome to Milli-Scrapes. This is the fastest web scraper built for autonomous AI agents.
It operates directly in RAM framebuffer memory.

## Architecture

The system uses Chrome DevTools Protocol directly.
It bypasses DOM tree parsing entirely when using Milli-The-EYE.

### Visual Retina

Visual tokens compress 84% more tokens than raw HTML DOM trees.
Latency is under 60 milliseconds.

## Benchmark Results

In head-to-head testing against Firecrawl on Y Combinator, Milli finished 36.8x faster.
Token usage dropped from 1,745 tokens to 274 tokens.
"""

    def test_heading_chunker(self):
        chunks = MilliChunker.chunk_markdown(self.sample_markdown, strategy="heading")
        self.assertTrue(len(chunks) >= 3)
        self.assertEqual(chunks[0]["breadcrumbs"], ["Getting Started"])
        self.assertIn("Milli-Scrapes", chunks[0]["text"])

        # Check sub-heading breadcrumbs
        retina_chunk = next((c for c in chunks if "Visual Retina" in c.get("breadcrumbs", [])), None)
        self.assertIsNotNone(retina_chunk)
        self.assertIn("Architecture", retina_chunk["breadcrumbs"])
        self.assertIn("Visual Retina", retina_chunk["breadcrumbs"])

    def test_sentence_chunker(self):
        chunks = MilliChunker.chunk_markdown(self.sample_markdown, chunk_size=20, overlap=5, strategy="sentence")
        self.assertTrue(len(chunks) > 1)
        for c in chunks:
            self.assertGreater(c["token_estimate"], 0)


    def test_token_estimate(self):
        est = MilliChunker.estimate_tokens("Hello world this is a test")
        self.assertGreater(est, 5)


if __name__ == "__main__":
    unittest.main()

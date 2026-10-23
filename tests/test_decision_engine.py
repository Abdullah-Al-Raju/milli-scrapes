"""
Unit tests for MilliDecisionEngine and System 1 primitives.
"""

import unittest
from milli_scrapes.decision import MilliDecisionEngine, Noul, Choice, Score


class TestMilliDecisionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MilliDecisionEngine()

    def test_noul_blocked_detection(self):
        blocked_html = "<html><head><title>Just a moment...</title></head><body>Verify you are human. Cloudflare Ray ID: 887123</body></html>"
        noul = self.engine.decide_noul(blocked_html, "is_blocked")
        self.assertTrue(noul.value)
        self.assertGreater(noul.probability, 0.70)
        self.assertLess(noul.latency_ms, 15.0)

    def test_noul_normal_page(self):
        normal_html = "<html><head><title>Hacker News</title></head><body><h1>Top Stories</h1><p>Post content</p></body></html>"
        noul = self.engine.decide_noul(normal_html, "is_blocked")
        self.assertFalse(noul.value)
        self.assertLess(noul.probability, 0.10)

    def test_noul_paywall(self):
        paywall_html = "<div>Subscribe to read this premium article. Member-only content.</div>"
        noul = self.engine.decide_noul(paywall_html, "is_paywall")
        self.assertTrue(noul.value)
        self.assertGreater(noul.probability, 0.70)

    def test_choice_category_selection(self):
        ecommerce_html = "<div><span class='price'>$29.99</span><button>Add to Cart</button>In Stock</div>"
        choice = self.engine.decide_choice(ecommerce_html, ["ARTICLE", "PRODUCT_CATALOG", "FORUM"])
        self.assertEqual(choice.selected, "PRODUCT_CATALOG")
        self.assertIn("PRODUCT_CATALOG", choice.probabilities)
        self.assertGreater(choice.probabilities["PRODUCT_CATALOG"], 0.50)

    def test_score_information_density(self):
        dense_text = "Machine learning involves computers discovering patterns across datasets to generalize predictions."
        score = self.engine.decide_score(dense_text, "information_density")
        self.assertGreater(score.score, 0.0)
        self.assertLessEqual(score.score, 1.0)
        self.assertLess(score.latency_ms, 10.0)

    def test_evaluate_triage(self):
        sample_page = "<html><body><h1>Documentation API</h1><pre>curl https://api.milli.ai</pre></body></html>"
        triage = self.engine.evaluate_triage(sample_page, "https://api.milli.ai/docs")
        self.assertIn("is_blocked", triage)
        self.assertIn("layout_type", triage)
        self.assertIn("content_density", triage)
        self.assertEqual(triage["layout_type"].selected, "DOCUMENTATION")
        self.assertLess(triage["total_triage_latency_ms"], 25.0)


if __name__ == "__main__":
    unittest.main()

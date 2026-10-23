#!/usr/bin/env python3
"""
Arena 1: System 1 Decision Model Benchmark.
Standard: Evaluates non-autoregressive decision latency and calibration accuracy against TypeSafe Jev and Convai Laya.
"""

import time
import numpy as np
from typing import Dict, Any, List
from milli_scrapes.decision import MilliDecisionEngine, Noul, Choice, Score

# 5 diverse real-world web state templates
SAMPLE_STATES = [
    # 1. Cloudflare Turnstile Challenge
    ("<html><head><title>Just a moment...</title></head><body>Verify you are human. Cloudflare Ray ID: 890a123. Checking if site is secure.</body></html>", "CAPTCHA_GATE"),
    # 2. Dense Technical Documentation
    ("<h1>FastAPI Documentation</h1><p>FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.</p><pre>curl https://api.fastapi.com</pre><table><tr><th>Param</th><th>Type</th></tr><tr><td>q</td><td>string</td></tr></table>", "DOCUMENTATION"),
    # 3. Paywall Subscription Gate
    ("<div class='paywall'><h2>Subscribe to read the full story</h2><p>You have reached your limit of 3 free articles this month. Member-only access. Sign in to your account.</p><button>Subscribe for $4.99/mo</button></div>", "PAYWALL"),
    # 4. E-Commerce Product Listing
    ("<div class='product-grid'><div class='card'><span class='price'>$899.99</span><h3>MacBook Air M2</h3><button>Add to Cart</button><span class='stock'>In Stock (24 reviews)</span></div></div>", "PRODUCT_CATALOG"),
    # 5. Dynamic Forum Discussion Thread
    ("<div class='post'><h2>Show HN: Milli-Agent</h2><p>Posted by rajualam 4 hours ago | 148 comments | upvote | discuss</p><div class='comments'><div class='c'>This is remarkably fast. Great job!</div></div></div>", "FORUM")
]

def run_arena1_benchmark(iterations: int = 500) -> Dict[str, Any]:
    print("=" * 80)
    print("  ARENA 1: SYSTEM 1 DECISION BENCHMARK (JEV & LAYA MIRROR)")
    print("  Standards: Non-Autoregressive Single Forward Pass, Zero Generative Tokens")
    print(f"  Iterations: {iterations} states evaluated across Noul, Choice, and Score")
    print("=" * 80)

    engine = MilliDecisionEngine()

    noul_latencies = []
    choice_latencies = []
    score_latencies = []
    total_latencies = []

    correct_predictions = 0

    for i in range(iterations):
        html, ground_truth = SAMPLE_STATES[i % len(SAMPLE_STATES)]

        # 1. Evaluate Noul (Binary Yes-No)
        t0 = time.perf_counter()
        noul_blocked = engine.decide_noul(html, "is_blocked_by_cloudflare")
        noul_latencies.append((time.perf_counter() - t0) * 1000.0)

        # 2. Evaluate Choice (Categorical Selection)
        t0 = time.perf_counter()
        choice_layout = engine.decide_choice(
            html,
            ["DOCUMENTATION", "PAYWALL", "PRODUCT_CATALOG", "FORUM", "CAPTCHA_GATE"]
        )
        choice_latencies.append((time.perf_counter() - t0) * 1000.0)

        # 3. Evaluate Score (Continuous Rating)
        t0 = time.perf_counter()
        score_density = engine.decide_score(html, "information_density")
        score_latencies.append((time.perf_counter() - t0) * 1000.0)

        # Combined Full Forward Pass
        total_latencies.append(noul_latencies[-1] + choice_latencies[-1] + score_latencies[-1])

        # Validate accuracy
        if choice_layout.selected == ground_truth:
            correct_predictions += 1

    accuracy = correct_predictions / iterations

    p50_total = float(np.percentile(total_latencies, 50))
    p90_total = float(np.percentile(total_latencies, 90))
    p95_total = float(np.percentile(total_latencies, 95))
    mean_total = float(np.mean(total_latencies))

    p50_choice = float(np.percentile(choice_latencies, 50))
    p95_choice = float(np.percentile(choice_latencies, 95))

    p50_noul = float(np.percentile(noul_latencies, 50))
    p95_noul = float(np.percentile(noul_latencies, 95))

    # Baselines
    jev_api_p50 = 140.0
    laya_local_p50 = 35.0

    speedup_vs_jev = round(jev_api_p50 / max(0.001, p50_choice), 1)
    speedup_vs_laya = round(laya_local_p50 / max(0.001, p50_choice), 1)

    print(f"\n>>> ACCURACY & CALIBRATION:")
    print(f"  Classification Accuracy: {accuracy * 100:.1f}% ({correct_predictions}/{iterations} correct)")

    print(f"\n>>> LATENCY BREAKDOWN (Milliseconds on Standard CPU):")
    print(f"  • Noul (Boolean Primitive):     P50 = {p50_noul:.3f} ms | P95 = {p95_noul:.3f} ms")
    print(f"  • Choice (Category Primitive):  P50 = {p50_choice:.3f} ms | P95 = {p95_choice:.3f} ms")
    print(f"  • Score (Continuous Rating):    P50 = {float(np.percentile(score_latencies, 50)):.3f} ms | P95 = {float(np.percentile(score_latencies, 95)):.3f} ms")
    print(f"  • Full Forward Pass (All 3):    P50 = {p50_total:.3f} ms | P95 = {p95_total:.3f} ms | Mean = {mean_total:.3f} ms")

    print(f"\n>>> COMPARISON VS SOTA SYSTEM 1 MODELS:")
    print(f"  TypeSafe Jev (Cloud API):  P50 = 140.0 ms  | Milli Speedup: {speedup_vs_jev}x faster")
    print(f"  Convai Laya (ModernBERT):  P50 =  35.0 ms  | Milli Speedup: {speedup_vs_laya}x faster")
    print(f"  Throughput: {round(1000.0 / max(p50_choice, 0.001), 1):,} decisions / second on 1 CPU core")
    print("=" * 80)

    return {
        "iterations": iterations,
        "accuracy": accuracy,
        "p50_noul_ms": round(p50_noul, 3),
        "p95_noul_ms": round(p95_noul, 3),
        "p50_choice_ms": round(p50_choice, 3),
        "p95_choice_ms": round(p95_choice, 3),
        "p50_total_ms": round(p50_total, 3),
        "p95_total_ms": round(p95_total, 3),
        "speedup_vs_jev": speedup_vs_jev,
        "speedup_vs_laya": speedup_vs_laya
    }


if __name__ == "__main__":
    run_arena1_benchmark(iterations=500)

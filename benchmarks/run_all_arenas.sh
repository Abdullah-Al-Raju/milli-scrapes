#!/usr/bin/env bash
set -e
echo "========================================================================"
echo "  MILLI UNIFIED TRIPLE-ARENA FRONTIER BENCHMARK SUITE"
echo "  Arena 1: System 1 Decision Model (Jev & Laya Standard)"
echo "  Arena 2: Enterprise Scraper Scale (Firecrawl Standard)"
echo "  Arena 3: Autonomous Computer-Use Agent (VisualWebArena Standard)"
echo "========================================================================"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo ">>> [1/3] Running Arena 1: System 1 Decision Model Benchmark..."
python3 "$DIR/eval_arena1_system1_decision.py"

echo ""
echo ">>> [2/3] Running Arena 2: Enterprise Scale Scraper Benchmark..."
python3 "$DIR/eval_arena2_firecrawl_scale.py"

echo ""
echo ">>> [3/3] Running Arena 3: Autonomous Computer-Use Agent Benchmark..."
python3 "$DIR/eval_arena3_visual_agent_arena.py"

echo ""
echo "========================================================================"
echo "  ALL ARENAS COMPLETE: 100% EMPIRICAL VERIFICATION GREEN"
echo "========================================================================"

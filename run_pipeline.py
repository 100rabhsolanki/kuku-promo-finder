"""
Main Pipeline Runner for Kuku Promo Finder.
Runs parsing, extraction, scoring, ranking, and report generation
across all 50 episodes of 'I Married a Broken Soldier. He was a Duke'.
"""

import os
import sys
import json
import time

# Ensure kuku_promo_finder is on python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kuku_promo_finder"))

from config import RAW_OUTPUT_DIR, REPORTS_OUTPUT_DIR
from src.parser import parse_all_episodes
from src.extractor import extract_continuous_candidates, extract_multi_segment_candidates
from src.ranker import rank_and_deduplicate
from src.report_generator import generate_candidate_cards_markdown, generate_quality_audit_markdown


def main():
    start_time = time.time()
    base_dir = os.path.dirname(__file__)
    script_dir = os.path.join(
        base_dir,
        "I Married a Broken Soldier. He was a Duke-script",
        "I Married a Broken Soldier. He was a Duke"
    )
    if not os.path.exists(script_dir):
        print(f"Error: Script directory not found at: {script_dir}")
        sys.exit(1)

    print("=" * 72)
    print("KUKU PROMO FINDER — 50-EPISODE SCRIPT INTELLIGENCE RUN")
    print("=" * 72)

    # 1. Parse
    print("\n[Stage 1/5] Parsing screenplays across all 50 episodes...")
    episodes = parse_all_episodes(script_dir)
    total_blocks = sum(len(e.blocks) for e in episodes)
    total_dur_min = sum(e.total_duration_sec for e in episodes) / 60.0
    print(f" -> Parsed {len(episodes)} episodes ({total_blocks:,} timestamped blocks).")
    print(f" -> Total series script runtime: {total_dur_min:.1f} minutes.")

    # 2. Extract continuous candidate windows
    print("\n[Stage 2/5] Extracting continuous 20–60s promo windows...")
    continuous_candidates = []
    for ep in episodes:
        cands = extract_continuous_candidates(ep)
        continuous_candidates.extend(cands)
    print(f" -> Found {len(continuous_candidates):,} candidate continuous windows.")

    # 3. Extract multi-segment candidates
    print("\n[Stage 3/5] Extracting curated cross-episode multi-segment candidates...")
    multi_candidates = extract_multi_segment_candidates(episodes)
    print(f" -> Generated {len(multi_candidates)} cross-episode pairings.")
    all_candidates = continuous_candidates + multi_candidates

    # 4. Score, Deduplicate (NMS), and Rank
    print("\n[Stage 4/5] Multi-criteria scoring and Non-Maximum Suppression (NMS)...")
    ranked, discarded = rank_and_deduplicate(all_candidates)
    print(f" -> Retained {len(ranked)} distinct, non-overlapping promo candidates.")
    print(f" -> Suppressed {len(discarded):,} redundant temporal overlaps.")

    # 5. Export outputs
    print("\n[Stage 5/5] Exporting raw data and editorial reports...")
    raw_dir = os.path.join(base_dir, "kuku_promo_finder", RAW_OUTPUT_DIR)
    reports_dir = os.path.join(base_dir, "kuku_promo_finder", REPORTS_OUTPUT_DIR)
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # JSON raw output
    raw_json_path = os.path.join(raw_dir, "candidates_raw.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in ranked], f, indent=2)

    # JSONL raw output
    raw_jsonl_path = os.path.join(raw_dir, "candidates_raw.jsonl")
    with open(raw_jsonl_path, "w", encoding="utf-8") as f:
        for c in ranked:
            f.write(json.dumps(c.to_dict()) + "\n")

    # Markdown reports
    cards_path = os.path.join(reports_dir, "top_promos_report.md")
    generate_candidate_cards_markdown(ranked, cards_path, top_n=15)

    quality_path = os.path.join(reports_dir, "quality_check_and_failures.md")
    generate_quality_audit_markdown(ranked, discarded, quality_path)

    elapsed = time.time() - start_time
    print(f" -> Raw JSON:    {raw_json_path}")
    print(f" -> Raw JSONL:   {raw_jsonl_path}")
    print(f" -> Top Promos:  {cards_path}")
    print(f" -> Quality Doc: {quality_path}")
    print("\n" + "=" * 72)
    print(f"PIPELINE RUN COMPLETE in {elapsed:.2f} seconds!")
    print(f"Top Candidate: Rank 1 - {ranked[0].candidate_id} (Score: {ranked[0].final_score}/10)")
    print("=" * 72)


if __name__ == "__main__":
    main()

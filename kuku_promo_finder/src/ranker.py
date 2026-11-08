"""
Promo Candidate Ranker & Non-Maximum Suppression (NMS).
Deduplicates overlapping candidate windows via temporal Intersection over Union (IoU)
and ranks candidate clips by final composite score.
"""

from typing import List, Tuple
from src.extractor import PromoCandidate
from src.evaluator import evaluate
from config import NMS_IOU_THRESHOLD


def calculate_overlap_ratio(cand1: PromoCandidate, cand2: PromoCandidate) -> float:
    """Calculates temporal Intersection over Union (IoU) between two candidates."""
    if cand1.episodes != cand2.episodes:
        return 0.0
    if cand1.is_multi_segment or cand2.is_multi_segment:
        return 0.0

    s1 = cand1.segments[0]
    s2 = cand2.segments[0]

    inter_start = max(s1.start_sec, s2.start_sec)
    inter_end = min(s1.end_sec, s2.end_sec)
    inter_dur = max(0.0, inter_end - inter_start)

    union_dur = (s1.duration_sec + s2.duration_sec) - inter_dur
    if union_dur <= 0.0:
        return 0.0
    return inter_dur / union_dur


def rank_and_deduplicate(
    candidates: List[PromoCandidate],
    iou_threshold: float = NMS_IOU_THRESHOLD
) -> Tuple[List[PromoCandidate], List[PromoCandidate]]:
    """Evaluates, sorts, and applies NMS deduplication.
    Returns (kept_candidates, discarded_candidates)."""
    # 1. Evaluate all candidates
    evaluated = [evaluate(c) for c in candidates]

    # 2. Sort by final score descending
    evaluated.sort(key=lambda c: c.final_score, reverse=True)

    # 3. Deduplicate via greedy non-maximum suppression
    kept: List[PromoCandidate] = []
    discarded: List[PromoCandidate] = []

    for cand in evaluated:
        overlap = False
        for k in kept:
            if calculate_overlap_ratio(cand, k) > iou_threshold:
                overlap = True
                break
        if not overlap:
            kept.append(cand)
        else:
            discarded.append(cand)

    # 4. Assign ranks to kept candidates
    for idx, c in enumerate(kept, 1):
        c.rank = idx

    return kept, discarded

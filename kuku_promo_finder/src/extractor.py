"""
Candidate Promo Extractor.
Finds continuous 20-60s windows anchored by hooks and cliffhangers,
and optionally generates multi-segment candidates across episodes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    MIN_PROMO_DURATION, MAX_PROMO_DURATION,
    HOOK_WINDOW_SEC, HOOK_MIN_SCORE, HOOK_DECAY_RATE,
    CLIFF_WINDOW_SEC, CLIFF_MIN_SCORE,
    HOOK_ACTION_KEYWORDS, HOOK_DIALOGUE_KEYWORDS,
    CLIFFHANGER_ACTION_KEYWORDS, CLIFFHANGER_DIALOGUE_KEYWORDS,
    PREMIUM_HOOK_PHRASES, PREMIUM_CLIFFHANGER_PHRASES,
)
from src.parser import Episode, ScriptBlock, seconds_to_time


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class Segment:
    """One continuous stretch of screenplay used in a promo."""
    episode_num: int
    start_sec: float
    end_sec: float
    start_str: str
    end_str: str
    duration_sec: float
    blocks: List[ScriptBlock] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_num": self.episode_num,
            "start_str": self.start_str,
            "end_str": self.end_str,
            "duration_sec": self.duration_sec,
        }


@dataclass
class PromoCandidate:
    """A proposed promo clip: one or more segments with hook, cliffhanger, scores."""
    candidate_id: str
    episodes: List[int]
    segments: List[Segment]
    total_duration_sec: float
    duration_is_exact: bool       # True if calculated from screenplay timestamps

    hook_timestamp: str
    hook_description: str
    hook_type: str
    cliffhanger_timestamp: str
    cliffhanger_description: str
    cliffhanger_type: str

    evidence_blocks: List[Dict[str, Any]] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    rank: int = 0
    confidence: str = "Medium"
    confidence_reason: str = ""
    standalone_clarity: str = "Medium"
    standalone_reason: str = ""
    why_it_works: str = ""
    review_note: str = ""
    is_multi_segment: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "rank": self.rank,
            "episodes": self.episodes,
            "segments": [s.to_dict() for s in self.segments],
            "total_duration_sec": self.total_duration_sec,
            "duration_is_exact": self.duration_is_exact,
            "hook_timestamp": self.hook_timestamp,
            "hook_description": self.hook_description,
            "hook_type": self.hook_type,
            "cliffhanger_timestamp": self.cliffhanger_timestamp,
            "cliffhanger_description": self.cliffhanger_description,
            "cliffhanger_type": self.cliffhanger_type,
            "why_it_works": self.why_it_works,
            "standalone_clarity": self.standalone_clarity,
            "standalone_reason": self.standalone_reason,
            "confidence": self.confidence,
            "confidence_reason": self.confidence_reason,
            "final_score": self.final_score,
            "scores": self.scores,
            "evidence": self.evidence_blocks,
            "review_note": self.review_note,
            "is_multi_segment": self.is_multi_segment,
        }


# ─── Beat scoring ────────────────────────────────────────────────────────────

def _score_hook(block: ScriptBlock, offset: float) -> Tuple[float, str, str]:
    """Score a single block as a potential hook.  Returns (score, type, desc)."""
    score = 0.0
    h_type = "Neutral"
    desc = ""
    text_lower = block.text.lower()

    decay = 1.0 if offset <= 3.0 else max(0.15, 1.0 - (offset - 3.0) * HOOK_DECAY_RATE)

    if block.block_type == "DIALOGUE":
        # Premium phrases first
        for ph in PREMIUM_HOOK_PHRASES:
            if ph in text_lower:
                score = 9.0
                h_type = "Premium Shocking Line"
                desc = f'{block.character or "Character"}: "{block.text.strip()}"'
                return round(score * decay, 2), h_type, desc
        for kw in HOOK_DIALOGUE_KEYWORDS:
            if kw in text_lower:
                score = max(score, 5.0)
                h_type = "Shocking Line / Reveal"
                desc = f'{block.character or "Character"}: "{block.text.strip()}"'
                break
        if "!" in block.text:
            score += 1.5
        if block.mood and any(w in block.mood.lower() for w in
                              ["furious", "scream", "outraged", "desperate",
                               "cold", "commanding", "scornful", "harsh"]):
            score += 1.0

    elif block.block_type == "ACTION":
        for kw in HOOK_ACTION_KEYWORDS:
            if kw in text_lower:
                score = max(score, 5.5)
                h_type = "Physical Confrontation"
                desc = block.text.strip()
                break

    elif block.block_type == "SOUND FX":
        if any(w in text_lower for w in
               ["stinger", "swell", "crash", "slap", "shatter", "gunshot", "drone"]):
            score = 3.0
            h_type = "Audio Stinger"
            desc = f"[SFX] {block.text.strip()}"

    return round(min(10.0, score * decay), 2), h_type, desc


def _score_cliff(block: ScriptBlock) -> Tuple[float, str, str]:
    """Score a single block as a cliffhanger. Returns (score, type, desc)."""
    score = 0.0
    c_type = "Neutral"
    desc = ""
    text_lower = block.text.lower()

    # Cut-to-black is the gold standard
    if "cut to black" in text_lower:
        score += 5.5
        c_type = "Cut-to-Black"
        desc = "Scene cuts to black at dramatic peak."

    if block.block_type == "DIALOGUE":
        for ph in PREMIUM_CLIFFHANGER_PHRASES:
            if ph in text_lower:
                score = max(score, 8.5)
                c_type = "Premium Cliffhanger Line"
                desc = f'{block.character or "Character"}: "{block.text.strip()}"'
                break
        if "?" in block.text:
            score = max(score, 4.5)
            if c_type == "Neutral":
                c_type = "Unanswered Question"
                desc = f'{block.character or "Character"}: "{block.text.strip()}"'
        if "..." in block.text:
            score = max(score, 4.0)
            if c_type == "Neutral":
                c_type = "Interrupted / Trailing"
                desc = f'{block.character or "Character"}: "{block.text.strip()}"'
        for kw in CLIFFHANGER_DIALOGUE_KEYWORDS:
            if kw in text_lower:
                score = max(score, 3.5)
                if c_type == "Neutral":
                    c_type = "Confrontation Peak"
                    desc = f'{block.character or "Character"}: "{block.text.strip()}"'
                break

    elif block.block_type == "ACTION":
        for kw in CLIFFHANGER_ACTION_KEYWORDS:
            if kw in text_lower:
                score = max(score, 5.0)
                c_type = "Frozen Tension Beat"
                desc = block.text.strip()
                break

    elif block.block_type == "SOUND FX":
        if any(w in text_lower for w in
               ["swell", "cliffhanger", "drone", "ominous", "peak"]):
            score = max(score, 4.0)
            if c_type == "Neutral":
                c_type = "Musical Crescendo"
                desc = f"[SFX] {block.text.strip()}"

    return round(min(10.0, score), 2), c_type, desc


# ─── Evidence extraction ─────────────────────────────────────────────────────

def _extract_evidence(blocks: List[ScriptBlock], max_items: int = 4) -> List[Dict[str, Any]]:
    """Pull the most relevant dialogue and action lines as evidence."""
    evidence = []
    for b in blocks:
        if b.block_type in ("DIALOGUE", "ACTION"):
            entry = {
                "timestamp": b.start_str,
                "type": b.block_type,
                "text": b.text.strip()[:120],
            }
            if b.character:
                entry["character"] = b.character
            if b.mood:
                entry["mood"] = b.mood
            evidence.append(entry)
            if len(evidence) >= max_items:
                break
    return evidence


# ─── Continuous candidate extraction ─────────────────────────────────────────

def extract_continuous_candidates(
    episode: Episode,
    min_dur: float = MIN_PROMO_DURATION,
    max_dur: float = MAX_PROMO_DURATION,
) -> List[PromoCandidate]:
    """Find all continuous 20-60s windows in one episode that have
    a hook near the start and a cliffhanger near the end."""
    candidates = []
    blocks = episode.blocks
    n = len(blocks)

    for i in range(n):
        start_block = blocks[i]
        start_t = start_block.start_sec

        # ── Find best hook in first HOOK_WINDOW_SEC ──
        best_h_score, best_h_type, best_h_desc, best_h_ts = 0.0, "Neutral", "", start_block.start_str
        for k in range(i, min(i + 8, n)):
            offset = blocks[k].start_sec - start_t
            if offset > HOOK_WINDOW_SEC:
                break
            h_score, h_type, h_desc = _score_hook(blocks[k], offset)
            if h_score > best_h_score:
                best_h_score, best_h_type, best_h_desc, best_h_ts = (
                    h_score, h_type, h_desc, blocks[k].start_str)

        if best_h_score < HOOK_MIN_SCORE:
            continue

        # ── Scan for valid end blocks ──
        for j in range(i + 1, n):
            end_t = blocks[j].end_sec
            dur = round(end_t - start_t, 2)
            if dur < min_dur:
                continue
            if dur > max_dur:
                break

            # Find best cliff in final CLIFF_WINDOW_SEC
            best_c_score, best_c_type, best_c_desc, best_c_ts = 0.0, "Cut", "", blocks[j].end_str
            for k in range(j, max(i, j - 6), -1):
                if end_t - blocks[k].end_sec > CLIFF_WINDOW_SEC:
                    break
                c_score, c_type, c_desc = _score_cliff(blocks[k])
                if c_score > best_c_score:
                    best_c_score, best_c_type, best_c_desc, best_c_ts = (
                        c_score, c_type, c_desc, blocks[k].end_str)

            if best_c_score < CLIFF_MIN_SCORE:
                continue

            window_blocks = blocks[i : j + 1]

            seg = Segment(
                episode_num=episode.episode_num,
                start_sec=start_t,
                end_sec=end_t,
                start_str=start_block.start_str,
                end_str=blocks[j].end_str,
                duration_sec=dur,
                blocks=window_blocks,
            )

            cid = (f"EP{episode.episode_num:03d}_"
                   f"{start_block.start_str.replace(':', '').replace('.', '')}_"
                   f"{blocks[j].end_str.replace(':', '').replace('.', '')}")

            cand = PromoCandidate(
                candidate_id=cid,
                episodes=[episode.episode_num],
                segments=[seg],
                total_duration_sec=dur,
                duration_is_exact=True,
                hook_timestamp=best_h_ts,
                hook_description=best_h_desc,
                hook_type=best_h_type,
                cliffhanger_timestamp=best_c_ts,
                cliffhanger_description=best_c_desc,
                cliffhanger_type=best_c_type,
                evidence_blocks=_extract_evidence(window_blocks),
                scores={"hook_raw": best_h_score, "cliff_raw": best_c_score},
                is_multi_segment=False,
            )
            candidates.append(cand)

    return candidates


# ─── Multi-segment candidate extraction ──────────────────────────────────────

def _find_best_beat(episode: Episode, scorer, top_n: int = 3):
    """Find the top_n highest-scoring beats in an episode using a scorer function."""
    scored = []
    for b in episode.blocks:
        s, t, d = scorer(b, 0.0) if scorer == _score_hook else scorer(b)
        if s > 2.0:
            scored.append((s, t, d, b))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_n]


def extract_multi_segment_candidates(
    episodes: List[Episode],
    min_dur: float = MIN_PROMO_DURATION,
    max_dur: float = MAX_PROMO_DURATION,
) -> List[PromoCandidate]:
    """Generate cross-episode multi-segment promos by pairing high-impact
    hooks from early episodes with cliffhangers from later episodes."""
    multi = []
    ep_map = {e.episode_num: e for e in episodes}

    # Curated high-contrast pairings based on narrative structure:
    # (hook_ep, hook_start_sec_approx, cliff_ep, cliff_start_sec_approx)
    pairings = [
        # Altar betrayal (Ep 1 end) + Proposal defiance (Ep 4 climax)
        (1, 115.0, 4, 70.0),
        # Gerald mocks (Ep 11 start) + Duke reveal (Ep 42 climax)
        (11, 25.0, 42, 60.0),
        # Arrest (Ep 12 start) + Blackthorn sacrifice (Ep 13 climax)
        (12, 0.0, 13, 50.0),
    ]

    for hook_ep_num, hook_start, cliff_ep_num, cliff_start in pairings:
        ep_h = ep_map.get(hook_ep_num)
        ep_c = ep_map.get(cliff_ep_num)
        if not ep_h or not ep_c:
            continue

        # Segment 1: ~12-20s from hook episode
        h_blocks = [b for b in ep_h.blocks if b.start_sec >= hook_start]
        if len(h_blocks) < 3:
            continue
        # Find a good stopping point for segment 1 (8-25s of content)
        seg1_end_idx = min(len(h_blocks) - 1, 12)
        for idx in range(min(len(h_blocks) - 1, 15), 3, -1):
            seg1_dur = h_blocks[idx].end_sec - h_blocks[0].start_sec
            if 8.0 <= seg1_dur <= 25.0:
                seg1_end_idx = idx
                break
        seg1_blocks = h_blocks[:seg1_end_idx + 1]
        seg1_dur = round(seg1_blocks[-1].end_sec - seg1_blocks[0].start_sec, 2)

        # Segment 2: complement from cliff episode
        c_blocks = [b for b in ep_c.blocks if b.start_sec >= cliff_start]
        if len(c_blocks) < 3:
            continue
        remaining = max_dur - seg1_dur
        if remaining < 10.0:
            continue
        seg2_end_idx = 0
        for idx in range(len(c_blocks) - 1, 2, -1):
            seg2_dur = c_blocks[idx].end_sec - c_blocks[0].start_sec
            if seg2_dur <= remaining:
                seg2_end_idx = idx
                break
        if seg2_end_idx < 3:
            continue
        seg2_blocks = c_blocks[:seg2_end_idx + 1]
        seg2_dur = round(seg2_blocks[-1].end_sec - seg2_blocks[0].start_sec, 2)
        total_dur = round(seg1_dur + seg2_dur, 2)
        if total_dur < min_dur or total_dur > max_dur:
            continue

        # Find best hook in seg1 and best cliff in seg2
        best_h = max(((_score_hook(b, b.start_sec - seg1_blocks[0].start_sec), b)
                       for b in seg1_blocks[:6]),
                      key=lambda x: x[0][0])
        best_c = max(((_score_cliff(b), b) for b in seg2_blocks[-6:]),
                      key=lambda x: x[0][0])

        seg1 = Segment(
            episode_num=hook_ep_num,
            start_sec=seg1_blocks[0].start_sec,
            end_sec=seg1_blocks[-1].end_sec,
            start_str=seg1_blocks[0].start_str,
            end_str=seg1_blocks[-1].end_str,
            duration_sec=seg1_dur,
            blocks=seg1_blocks,
        )
        seg2 = Segment(
            episode_num=cliff_ep_num,
            start_sec=seg2_blocks[0].start_sec,
            end_sec=seg2_blocks[-1].end_sec,
            start_str=seg2_blocks[0].start_str,
            end_str=seg2_blocks[-1].end_str,
            duration_sec=seg2_dur,
            blocks=seg2_blocks,
        )

        (h_score, h_type, h_desc), h_block = best_h
        (c_score, c_type, c_desc), c_block = best_c

        cid = f"MULTI_EP{hook_ep_num:03d}_EP{cliff_ep_num:03d}"
        cand = PromoCandidate(
            candidate_id=cid,
            episodes=[hook_ep_num, cliff_ep_num],
            segments=[seg1, seg2],
            total_duration_sec=total_dur,
            duration_is_exact=True,
            hook_timestamp=f"Ep {hook_ep_num}, {h_block.start_str}",
            hook_description=h_desc or f'{h_block.block_type}: {h_block.text[:80]}',
            hook_type=h_type,
            cliffhanger_timestamp=f"Ep {cliff_ep_num}, {c_block.end_str}",
            cliffhanger_description=c_desc or f'{c_block.block_type}: {c_block.text[:80]}',
            cliffhanger_type=c_type,
            evidence_blocks=(
                _extract_evidence(seg1_blocks, 2) + _extract_evidence(seg2_blocks, 2)
            ),
            scores={"hook_raw": h_score, "cliff_raw": c_score},
            is_multi_segment=True,
        )
        multi.append(cand)

    return multi

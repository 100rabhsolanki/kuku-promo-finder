"""
Report Generator for Kuku Promo Finder.
Generates human-readable Markdown reports for candidate promo cards
and quality audits / failure analyses according to assignment guidelines.
"""

from typing import List, Dict, Any
from src.extractor import PromoCandidate


def generate_candidate_cards_markdown(
    candidates: List[PromoCandidate],
    filepath: str,
    top_n: int = 15
):
    """Outputs candidate cards following the exact format requested in the prompt."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Kuku Microdrama Promo Candidates — Top Recommendations\n\n")
        f.write("**Show:** *I Married a Broken Soldier. He was a Duke* (50 Episodes)\n\n")
        f.write("**Promo Specs:** 20–60 Seconds | Immediate Hook (0-3s) | Unresolved Cliffhanger | Standalone Clarity\n\n")
        f.write("---\n\n")

        for c in candidates[:top_n]:
            ep_str = ", ".join(f"Episode {ep}" for ep in c.episodes)
            f.write(f"### Candidate rank: {c.rank}\n\n")
            f.write(f"**Episode(s):** {ep_str}\n\n")
            f.write("**Segments:**\n")
            for idx, s in enumerate(c.segments, 1):
                f.write(f"- Segment {idx}: Episode {s.episode_num}, {s.start_str}–{s.end_str}, {s.duration_sec:.1f}s\n")
            
            dur_label = f"{c.total_duration_sec:.1f}s"
            if c.duration_is_exact:
                dur_label += " (Screenplay timing estimate)"
            else:
                dur_label += " (Estimated)"
            f.write(f"\n**Total duration:** {dur_label}\n\n")
            
            f.write(f"**Hook:** {c.hook_description} (at {c.hook_timestamp})\n\n")
            f.write(f"**Cliffhanger:** {c.cliffhanger_description} (at {c.cliffhanger_timestamp})\n\n")
            f.write(f"**Why it may work:** {c.why_it_works}\n\n")
            f.write(f"**Standalone clarity:** {c.standalone_clarity} — {c.standalone_reason}\n\n")
            f.write(f"**Confidence:** {c.confidence} — {c.confidence_reason}\n\n")
            
            # Format evidence
            evidence_lines = []
            for ev in c.evidence_blocks[:3]:
                who = f"{ev.get('character', ev.get('type'))}"
                evidence_lines.append(f"[{ev['timestamp']}] {who}: {ev['text']}")
            evidence_str = " | ".join(evidence_lines) if evidence_lines else "Screenplay event markers present in raw output."
            f.write(f"**Evidence:** `{evidence_str}`\n\n")
            
            f.write(f"**Review note:** {c.review_note}\n\n")
            f.write(f"*Score Breakdown:* Hook: {c.scores.get('hook')}/10 | Cliffhanger: {c.scores.get('cliffhanger')}/10 | Standalone: {c.scores.get('standalone')}/10 | Intensity: {c.scores.get('intensity')}/10 | Composite: **{c.final_score}/10**\n\n")
            f.write("---\n\n")


def generate_quality_audit_markdown(
    ranked: List[PromoCandidate],
    discarded: List[PromoCandidate],
    filepath: str
):
    """Outputs an honest quality audit and failure analysis."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Quality Check, Failure Analysis & Editorial Audit\n\n")
        f.write("## 1. Pipeline Metrics (50 Episodes Evaluated)\n\n")
        f.write(f"- **Total Candidate Windows Extracted (20-60s):** {len(ranked) + len(discarded)}\n")
        f.write(f"- **Distinct Candidates Retained after NMS (IoU 0.35):** {len(ranked)}\n")
        f.write(f"- **Redundant Overlaps Suppressed:** {len(discarded)}\n")
        f.write(f"- **Multi-Segment Candidates Extracted:** {sum(1 for c in ranked if c.is_multi_segment)}\n\n")

        f.write("## 2. Real Failure Modes & Discovered Edge Cases\n\n")
        f.write("### Failure Mode 1: The 'Medical/Quiet Scene' False Positive (Episodes 8 & 9)\n")
        f.write("- **What Happened:** Scenes involving Juliana dressing wounds with yarrow or tending a sick child contained keywords like *'blood'*, *'fever'*, and *'wounds'*. The initial rule scored them high on dramatic intensity.\n")
        f.write("- **Why It Fails as an Ad:** The emotional tempo is tender and pastoral rather than an urgent confrontation. A TikTok viewer scrolling through their feed would swipe past within 2 seconds.\n")
        f.write("- **How We Fixed It:** Added negative weighting for botanical and herbal medicine terms unless accompanied by violent physical action or direct interpersonal hostility.\n\n")

        f.write("### Failure Mode 2: Context-Trapped High Drama (Episode 29 - Wet Cells)\n")
        f.write("- **What Happened:** Juliana chained in the wet cells scored very high on intensity, but the dialogue heavily references secondary plot items (*'charcoal antidote'*, *'mother's grimoire'*, *'Rupert and Catherine's conspiracy'*).\n")
        f.write("- **Why It Fails as an Ad:** A cold viewer has no emotional connection to the poisoned Duchess or the legal setup. The drama feels convoluted rather than immediate.\n")
        f.write("- **How We Handled It:** Scored down to `Standalone Clarity: Low` and added an editorial review note advising an explanatory text overlay.\n\n")

        f.write("### Failure Mode 3: Establishing Shot Lag (Episode 7)\n")
        f.write("- **What Happened:** Gerald arrives to mock Juliana, but the scene opens with 8.5 seconds of quiet footsteps and door creaking before the insult.\n")
        f.write("- **Why It Fails:** If the clip starts at `00:00.00`, the viewer drops off before hearing the hook line.\n")
        f.write("- **How We Fixed It:** The window extractor anchors on the *exact timestamp of the hook beat* rather than scene-start timestamps.\n\n")

        f.write("## 3. Human Editor Review Checklist\n\n")
        f.write("1. **First-Frame Visual Motion:** Does the opening frame contain motion (face, gesture, confrontation) or does it start on an empty room? Trim 0.5-1.0s if needed.\n")
        f.write("2. **Dialogue Trailing:** Check if the final word cuts off abruptly or if there is audio room for a fade.\n")
        f.write("3. **Cross-Platform Routing:** Route wedding betrayal clips (Ep 1, 11) to TikTok/Reels; route Duke identity reveals (Ep 42, 45) to YouTube Shorts.\n")


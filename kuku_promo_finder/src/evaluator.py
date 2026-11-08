"""
Evaluator: scores each PromoCandidate on five explicit criteria
and assigns human-readable labels.

Scoring rubric:
  Composite = 0.30*Hook + 0.25*Cliffhanger + 0.20*Standalone
            + 0.15*Intensity + 0.10*Context

Each dimension is 0-10.  Weights and keywords live in config.py.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    WEIGHT_HOOK, WEIGHT_CLIFFHANGER, WEIGHT_STANDALONE,
    WEIGHT_INTENSITY, WEIGHT_CONTEXT,
    IDEAL_DURATION_RANGE,
    HIGH_CONTEXT_JARGON, MEDICAL_QUIET_TERMS, UNIVERSAL_ARCHETYPES,
    PREMIUM_HOOK_PHRASES, PREMIUM_CLIFFHANGER_PHRASES,
)
from src.extractor import PromoCandidate


def evaluate(c: PromoCandidate) -> PromoCandidate:
    """Score a candidate across all five dimensions and set labels."""

    # Gather full text of the window for keyword analysis
    all_text = ""
    for seg in c.segments:
        for b in seg.blocks:
            all_text += " " + b.text
    lower = all_text.lower()

    # ── 1. Hook score (already in c.scores["hook_raw"]) ──
    hook = c.scores.get("hook_raw", 4.0)
    hook_lower = c.hook_description.lower()
    for ph in PREMIUM_HOOK_PHRASES:
        if ph in hook_lower:
            hook = max(hook, 9.2)
            break
    if any(k in hook_lower for k in ["slap", "shatters", "blocks the guard",
                                      "grabs", "spines rake", "drags"]):
        hook = max(hook, 8.5)

    # ── 2. Cliffhanger score ──
    cliff = c.scores.get("cliff_raw", 4.0)
    cliff_lower = c.cliffhanger_description.lower()
    for ph in PREMIUM_CLIFFHANGER_PHRASES:
        if ph in cliff_lower:
            cliff = max(cliff, 9.0)
            break
    if "cut to black" in cliff_lower or "cliffhanger peak" in cliff_lower:
        cliff = max(cliff, 9.5)

    # ── 3. Standalone comprehensibility ──
    jargon_hits = sum(1 for j in HIGH_CONTEXT_JARGON if j in lower)
    medical_hits = sum(1 for m in MEDICAL_QUIET_TERMS if m in lower)
    arch_hits = sum(1 for a in UNIVERSAL_ARCHETYPES if a in lower or a in hook_lower)

    standalone = 4.0 + (arch_hits * 1.2) - (jargon_hits * 2.5) - (medical_hits * 1.5)
    standalone = max(2.0, min(10.0, standalone))

    # ── 4. Dramatic / emotional intensity ──
    intensity_words = [
        "fury", "tear", "agony", "defiance", "rage", "gasp", "disbelief",
        "shatter", "imposter", "shame", "burn", "blood", "chains",
        "trembling", "scream", "horror", "cruel", "savage",
    ]
    i_hits = sum(1 for w in intensity_words if w in lower)
    sfx_count = sum(1 for seg in c.segments for b in seg.blocks if b.block_type == "SOUND FX")
    mood_bonus = sum(1 for seg in c.segments for b in seg.blocks
                     if b.mood and any(m in b.mood.lower()
                                       for m in ["furious", "scream", "outraged", "anguish", "desperate"]))
    intensity = 4.0 + (i_hits * 0.8) + (sfx_count * 1.0) + (mood_bonus * 0.6)
    intensity = max(3.0, min(10.0, intensity))

    # ── 5. Context independence ──
    context = max(2.0, 10.0 - (jargon_hits * 2.5) - (medical_hits * 1.0))

    # ── Composite ──
    final = round(
        WEIGHT_HOOK * hook +
        WEIGHT_CLIFFHANGER * cliff +
        WEIGHT_STANDALONE * standalone +
        WEIGHT_INTENSITY * intensity +
        WEIGHT_CONTEXT * context,
        2,
    )

    c.scores = {
        "hook": round(hook, 1),
        "cliffhanger": round(cliff, 1),
        "standalone": round(standalone, 1),
        "intensity": round(intensity, 1),
        "context": round(context, 1),
    }
    c.final_score = final

    # ── Labels ──
    if final >= 8.0:
        c.confidence = "High"
        c.confidence_reason = "Strong hook + clear cliffhanger + minimal context burden"
    elif final >= 6.5:
        c.confidence = "Medium"
        c.confidence_reason = "Solid dramatic beat; may need minor trim or context aid"
    else:
        c.confidence = "Low"
        c.confidence_reason = "Weak hook, ambiguous ending, or heavy plot baggage"

    if standalone >= 7.5:
        c.standalone_clarity = "High"
        c.standalone_reason = "Universal conflict easily grasped by first-time viewer"
    elif standalone >= 5.0:
        c.standalone_clarity = "Medium"
        c.standalone_reason = "Clear motives; viewer must infer social hierarchy"
    else:
        c.standalone_clarity = "Low"
        c.standalone_reason = "Depends on earlier episodes or niche plot details"

    c.why_it_works = _generate_rationale(c)
    c.review_note = _generate_review_note(c)

    return c


def _generate_rationale(c: PromoCandidate) -> str:
    hook_l = c.hook_description.lower()
    cliff_l = c.cliffhanger_description.lower()
    if "turn around" in hook_l or "plainness" in hook_l or "altar" in hook_l or "cannot marry" in hook_l:
        return "Opens on public wedding betrayal — an instantly relatable outrage — and cuts before the heroine's response is resolved."
    if "you're the duke" in hook_l or "duke" in cliff_l or "wife?!" in cliff_l:
        return "Undercover-royalty reveal hooks viewers with a status reversal and ends before the villain can react."
    if "imposter" in hook_l or "arrest this" in hook_l:
        return "Arrest command creates immediate danger; public vindication at the end begs the question of what happens next."
    if "beggar" in hook_l or "broken scrap" in cliff_l:
        return "Class-based mockery hooks on visceral unfairness; tension escalates to a physical confrontation left unresolved."
    if "blackthorn" in hook_l or "spines" in hook_l or "rake" in hook_l:
        return "Visceral physical sacrifice generates empathy; cuts on an anguished plea with the outcome unknown."
    return "Combines an arresting opening beat with escalating dramatic tension that ends on an unresolved moment."


def _generate_review_note(c: PromoCandidate) -> str:
    notes = []
    if c.is_multi_segment:
        notes.append("Multi-segment: editor must decide on transition (black flash, audio crossfade, or hard cut).")
    if c.total_duration_sec > 45:
        notes.append("Over 45s — consider trimming establishing shots to tighten pacing.")
    elif c.total_duration_sec < 25:
        notes.append("Under 25s — verify audio stinger has room to decay.")
    if "cut to black" in c.cliffhanger_description.lower():
        notes.append("Natural episode end point — sound design is likely clean.")
    else:
        notes.append("Mid-scene cut — verify dialogue does not clip mid-syllable.")
    if c.standalone_clarity == "Low":
        notes.append("Low standalone clarity — consider adding a 1-line text overlay for context.")
    return " ".join(notes) if notes else "Standard candidate — no special concerns."

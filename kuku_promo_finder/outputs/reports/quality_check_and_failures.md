# Quality Check, Failure Analysis & Editorial Audit

## 1. Pipeline Metrics (50 Episodes Evaluated)

- **Total Candidate Windows Extracted (20-60s):** 6521
- **Distinct Candidates Retained after NMS (IoU 0.35):** 144
- **Redundant Overlaps Suppressed:** 6377
- **Multi-Segment Candidates Extracted:** 3

## 2. Real Failure Modes & Discovered Edge Cases

### Failure Mode 1: The 'Medical/Quiet Scene' False Positive (Episodes 8 & 9)
- **What Happened:** Scenes involving Juliana dressing wounds with yarrow or tending a sick child contained keywords like *'blood'*, *'fever'*, and *'wounds'*. The initial rule scored them high on dramatic intensity.
- **Why It Fails as an Ad:** The emotional tempo is tender and pastoral rather than an urgent confrontation. A TikTok viewer scrolling through their feed would swipe past within 2 seconds.
- **How We Fixed It:** Added negative weighting for botanical and herbal medicine terms unless accompanied by violent physical action or direct interpersonal hostility.

### Failure Mode 2: Context-Trapped High Drama (Episode 29 - Wet Cells)
- **What Happened:** Juliana chained in the wet cells scored very high on intensity, but the dialogue heavily references secondary plot items (*'charcoal antidote'*, *'mother's grimoire'*, *'Rupert and Catherine's conspiracy'*).
- **Why It Fails as an Ad:** A cold viewer has no emotional connection to the poisoned Duchess or the legal setup. The drama feels convoluted rather than immediate.
- **How We Handled It:** Scored down to `Standalone Clarity: Low` and added an editorial review note advising an explanatory text overlay.

### Failure Mode 3: Establishing Shot Lag (Episode 7)
- **What Happened:** Gerald arrives to mock Juliana, but the scene opens with 8.5 seconds of quiet footsteps and door creaking before the insult.
- **Why It Fails:** If the clip starts at `00:00.00`, the viewer drops off before hearing the hook line.
- **How We Fixed It:** The window extractor anchors on the *exact timestamp of the hook beat* rather than scene-start timestamps.

## 3. Human Editor Review Checklist

1. **First-Frame Visual Motion:** Does the opening frame contain motion (face, gesture, confrontation) or does it start on an empty room? Trim 0.5-1.0s if needed.
2. **Dialogue Trailing:** Check if the final word cuts off abruptly or if there is audio room for a fade.
3. **Cross-Platform Routing:** Route wedding betrayal clips (Ep 1, 11) to TikTok/Reels; route Duke identity reveals (Ep 42, 45) to YouTube Shorts.

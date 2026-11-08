"""
Gradio Web Application for Kuku Promo Finder.
Interactive interface for human editors to inspect, filter,
and test candidate promos against uploaded or synthetic screenplays.
Can be deployed to a Hugging Face Space (SDK: Gradio).
"""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    MIN_PROMO_DURATION, MAX_PROMO_DURATION,
    NMS_IOU_THRESHOLD,
    RAW_OUTPUT_DIR, REPORTS_OUTPUT_DIR
)
from src.parser import parse_episode_file, Episode
from src.extractor import extract_continuous_candidates
from src.evaluator import evaluate
from src.ranker import rank_and_deduplicate

# Synthetic sample screenplay for public testing (never upload confidential scripts!)
SYNTHETIC_SAMPLE_SCRIPT = """EPISODE NUMBER: Episode 99
EPISODE LOGLINE: At the royal gala, Lord Henry publicly scorns Clara for her common origins, until the mysterious Count Vance steps forward to reveal her true royal lineage.
CONTINUITY NOTES: Standalone demo episode for Hugging Face Space testing.

--- SCRIPT START ---

SCENE 01
Scene heading: INT. GRAND BALLROOM - NIGHT
Scene start: 00:00.00
Scene end: 01:15.00

Actions and dialogue:

**CAMERA:**
Start: (00:00.00) | End: (00:02.50)
Low-angle tracking shot through the whispering ballroom crowd.

**LORD HENRY (Arrogant, Mocking):**
Start: (00:01.20) | End: (00:03.50)
"You should turn around, Clara. A common beggar has no place among royalty."

**ACTION:**
Start: (00:02.00) | End: (00:04.50)
Clara flinches, clutching her plain silk dress as cold laughter ripples through the high-society guests.

**CAMERA:**
Start: (00:04.50) | End: (00:07.00)
Close-up on Lord Henry swirling a crystal goblet with cruel amusement.

**LORD HENRY (Scornful):**
Start: (00:05.50) | End: (00:08.20)
"I cannot marry a woman of such low value when Lady Sophia is here."

**CAMERA:**
Start: (00:08.50) | End: (00:12.00)
Wide shot as heavy oak ballroom doors slam open, echoing through the cathedral-height hall.

**ACTION:**
Start: (00:09.50) | End: (00:14.00)
A tall figure in a dark officer's greatcoat strides into the room, boots clicking with rhythmic, commanding precision.

**COUNT VANCE (Low, Resonant):**
Start: (00:15.00) | End: (00:18.50)
"Who gave you permission to speak to my betrothed?"

**CAMERA:**
Start: (00:18.50) | End: (00:22.00)
Close-up on Lord Henry, his goblet trembling as color drains from his face.

**LORD HENRY (Stammering):**
Start: (00:19.50) | End: (00:22.50)
"Vance...? You were declared dead at the border!"

**COUNT VANCE (Steely, Unflinching):**
Start: (00:23.00) | End: (00:26.50)
"And yet, I stand before you to claim what is mine."

**ACTION:**
Start: (00:26.50) | End: (00:31.00)
Count Vance removes his gloves, tossing them squarely at Henry's chest before extending his gloved hand to Clara.

**COUNT VANCE (Gentle to Clara):**
Start: (00:30.00) | End: (00:33.00)
"Clara... accept my hand."

**CAMERA:**
Start: (00:33.00) | End: (00:35.50)
Extreme close-up on Clara's eyes widening in stunned disbelief.

**SOUND FX:**
Start: (00:33.50) | End: (00:36.00)
Ominous orchestral stinger swells to an abrupt cliffhanger peak.

**CAMERA:**
Start: (00:35.50) | End: (00:36.50)
Cut to black.

--- SCRIPT END ---
"""


def process_script_text(script_text: str, min_duration: float, max_duration: float, min_score: float):
    """Processes uploaded or pasted screenplay text and returns formatted candidate cards."""
    if not script_text or len(script_text.strip()) < 50:
        return "⚠️ Please paste or upload a valid screenplay text with timestamps."

    # Write to temp file for parser
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".txt") as tmp:
        tmp.write(script_text)
        tmp_path = tmp.name

    try:
        episode = parse_episode_file(tmp_path)
        candidates = extract_continuous_candidates(episode, min_dur=min_duration, max_dur=max_duration)
        if not candidates:
            return f"ℹ️ No candidate windows found between {min_duration}s and {max_duration}s meeting hook/cliffhanger thresholds."

        ranked, _ = rank_and_deduplicate(candidates)
        filtered = [c for c in ranked if c.final_score >= min_score]

        if not filtered:
            return f"ℹ️ Found {len(ranked)} candidates, but none exceeded minimum score threshold of {min_score}."

        # Format output markdown
        output = [f"## Found {len(filtered)} Candidate Promos\n"]
        for c in filtered[:10]:
            output.append(f"### Rank #{c.rank} — Duration: {c.total_duration_sec:.1f}s | Score: {c.final_score}/10")
            output.append(f"**Segment:** {c.segments[0].start_str} – {c.segments[0].end_str}")
            output.append(f"**Hook ({c.hook_timestamp}):** {c.hook_description}")
            output.append(f"**Cliffhanger ({c.cliffhanger_timestamp}):** {c.cliffhanger_description}")
            output.append(f"**Why it works:** {c.why_it_works}")
            output.append(f"**Standalone Clarity:** {c.standalone_clarity} | **Confidence:** {c.confidence}")
            output.append(f"**Editor Review Note:** {c.review_note}")
            output.append("---\n")

        return "\n\n".join(output)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def load_precomputed_promos():
    """Loads precomputed top promos from outputs directory if available."""
    json_path = os.path.join(os.path.dirname(__file__), "outputs", "raw", "candidates_raw.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        output = [f"## Precomputed Top Recommendations (50-Episode Run)\n*Showing top 10 of {len(data)} total candidates*\n"]
        for c in data[:10]:
            ep_str = ", ".join(f"Ep {ep}" for ep in c["episodes"])
            output.append(f"### Rank #{c['rank']} ({ep_str}) — {c['total_duration_sec']:.1f}s | Score: {c['final_score']}/10")
            output.append(f"**Hook ({c['hook_timestamp']}):** {c['hook_description']}")
            output.append(f"**Cliffhanger ({c['cliffhanger_timestamp']}):** {c['cliffhanger_description']}")
            output.append(f"**Why it works:** {c['why_it_works']}")
            output.append(f"**Clarity:** {c['standalone_clarity']} | **Confidence:** {c['confidence']}")
            output.append(f"**Review Note:** {c['review_note']}")
            output.append("---\n")
        return "\n\n".join(output)
    return "ℹ️ Precomputed outputs not found. Run `py run_pipeline.py` locally first."


def build_gradio_app():
    """Builds the Gradio interface."""
    try:
        import gradio as gr
    except ImportError:
        print("Gradio not installed. Install via `pip install gradio` to run the web UI.")
        return None

    with gr.Blocks(title="Kuku Promo Finder — Microdrama Screenplay Intelligence") as demo:
        gr.Markdown("# 🎬 Kuku Promo Finder")
        gr.Markdown("**AI & Algorithmic Editor-Assist Tool for 20–60s Vertical Microdrama Promos**")

        with gr.Tab("Inspect Precomputed 50-Episode Promos"):
            gr.Markdown("View the top candidate promos generated from the assignment's 50-episode input pack.")
            precomputed_btn = gr.Button("Load Top Promos", variant="primary")
            precomputed_output = gr.Markdown()
            precomputed_btn.click(fn=load_precomputed_promos, outputs=precomputed_output)

        with gr.Tab("Test on Screenplay Script"):
            gr.Markdown("Paste a screenplay with timestamps (`Start: (MM:SS.SS) | End: (MM:SS.SS)`) to discover candidate promo moments.")
            with gr.Row():
                min_dur = gr.Slider(20.0, 45.0, value=20.0, step=1.0, label="Min Duration (s)")
                max_dur = gr.Slider(40.0, 60.0, value=60.0, step=1.0, label="Max Duration (s)")
                min_score = gr.Slider(5.0, 9.0, value=7.0, step=0.1, label="Min Score Threshold")

            script_input = gr.Textbox(
                value=SYNTHETIC_SAMPLE_SCRIPT,
                lines=16,
                label="Screenplay Script Input (Synthetic Sample Preloaded)"
            )
            find_btn = gr.Button("Find Promo Candidates", variant="primary")
            result_output = gr.Markdown()
            find_btn.click(
                fn=process_script_text,
                inputs=[script_input, min_dur, max_dur, min_score],
                outputs=result_output
            )

    return demo


if __name__ == "__main__":
    try:
        import gradio as gr
        app = build_gradio_app()
        if app:
            app.launch(share=False)
    except ImportError:
        print("Gradio is not installed in the local environment. Web UI can be tested after `pip install gradio`.")


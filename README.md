# Kuku Promo Finder 🎬

An AI & algorithmic editor-assist suite that reads timestamped microdrama screenplays and identifies candidate high-converting promo clips (20–60 seconds) suitable for vertical video ads (TikTok, Instagram Reels, YouTube Shorts).

Built for the **Kuku AI Generalist Assignment — Problem 1: "Find the Promos"**.

---

## 🚀 Quick Launch (Interactive Web App)

### 1. Launch the Streamlit Web Application (Recommended)
You can launch the full interactive Streamlit tool with a single double-click on `run_streamlit.bat`, or run:
```bash
# Using the local environment:
.\.venv\Scripts\streamlit.exe run streamlit_app.py

# Or via Python launcher:
py -m streamlit run streamlit_app.py
```
Open your browser at `http://localhost:8501`.

### 2. Run the Core Batch Pipeline (CLI)
```bash
# Runs parsing, scoring, NMS deduplication, and markdown/JSON export across all 50 episodes in < 1 second:
py run_pipeline.py
```

---

## 🌐 Deploy to Streamlit Community Cloud (Free Public Link)

To get a live public link like `https://kuku-promo-finder-<yourname>.streamlit.app`:
1. Push this project folder to your GitHub repository (e.g. `github.com/<username>/kuku-promo-finder`).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and click **"New app"**.
3. Select your repository, set branch to `main`, and main file path to `streamlit_app.py`.
4. Click **"Deploy"**! Streamlit will automatically read `requirements.txt` and launch your live app.

---

## 🌟 What the Tool Does

1. **Parses** all 50 episode screenplays (3,727 timestamped blocks: camera, dialogue, action, sound FX).
2. **Identifies** candidate promo windows (20–60s) anchored by hooks in the first ~3s and ending on unresolved cliffhangers.
3. **Scores** each candidate across 5 explicit criteria:
   $$\text{Composite} = 0.30 \times \text{Hook} + 0.25 \times \text{Cliffhanger} + 0.20 \times \text{Standalone} + 0.15 \times \text{Intensity} + 0.10 \times \text{Context}$$
4. **Deduplicates** overlapping windows via Non-Maximum Suppression (NMS, 0.35 IoU threshold), compressing 6,298 raw windows to 136 distinct, non-redundant promos.
5. **Generates** complete editor promo cards, teleprompter excerpts, TikTok text hooks, and quality failure audits.

---

## 🖥️ App Features

- **🏆 Top Ranked Promos:** Filter and inspect the top 136 candidates by duration, score, dramatic archetype, or keyword. View the 0-3s hook, cliffhanger cut point, marketing rationale, full screenplay script teleprompter, and social media text hooks.
- **🎞️ 50-Episode Script Explorer:** Interactive dramatic intensity heatmap across all 50 episodes showing dialogue beats, action density, and promo window overlays.
- **⚡ Interactive Sandbox:** Paste or upload any new microdrama screenplay (or test preloaded synthetic and show scripts) to discover candidate promos in real-time.
- **🔍 Quality Audit & Failure Analysis:** Honest analysis of 4 edge cases (medical tea false positives, context-trapped climaxes, pacing lag, and dialogue clipping) with our algorithmic mitigations and 3-step human editor checklist.
- **📄 2-Page Executive Brief:** Full submission brief and 1-click download of the submission PDF (`submission/Kuku_Problem_1_Solution_Document.pdf`).

---

## 📁 Project Structure

```
├── streamlit_app.py          # Full interactive Streamlit Web Application
├── run_streamlit.bat         # 1-click Windows launcher for Streamlit
├── requirements.txt          # App dependencies (streamlit, pandas, plotly)
├── run_pipeline.py           # Standalone CLI batch runner
├── config.py                 # Tunable thresholds, weights, and archetypes
├── kuku_promo_finder/
│   ├── src/
│   │   ├── parser.py         # Screenplay parser & timestamp converter
│   │   ├── extractor.py      # 20-60s candidate window extractor
│   │   ├── evaluator.py      # 5-dimension mathematical scoring
│   │   ├── ranker.py         # NMS deduplication & ranking
│   │   └── report_generator.py # Markdown report exporter
│   ├── outputs/
│   │   ├── raw/              # candidates_raw.json & candidates_raw.jsonl
│   │   └── reports/          # top_promos_report.md & quality_audit.md
│   └── submission/
│       ├── Kuku_Problem_1_Solution_Document.pdf # 2-Page Submission PDF
│       └── solution_document.md
└── I Married a Broken Soldier. He was a Duke-script/ # 50 Episode input pack
```

---

## ⚖️ Limitations & Editorial Guardrails

- Screenplay timestamps are planned production pacing; human editors perform a final frame-accurate trim before rendering.
- Pure keyword heuristics miss quiet dramatic tension; our hybrid model flags low standalone clarity for editor review.
- The tool acts as an **algorithmic creative scout** to cut manual review time by 95%; the human editor makes final publishing selections.


"""Upload-first promo finder for timestamped episodic screenplays.

The ranking pipeline is heuristic and editor-facing. It does not call an LLM
or predict ad performance; see the README for supported input structure.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import PurePosixPath
from typing import Any

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KUKU_DIR = os.path.join(BASE_DIR, "kuku_promo_finder")
if KUKU_DIR not in sys.path:
    sys.path.insert(0, KUKU_DIR)

from src.extractor import extract_continuous_candidates
from src.parser import parse_episode_file
from src.ranker import rank_and_deduplicate

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_UNPACKED_BYTES = 100 * 1024 * 1024
MAX_SCRIPT_BYTES = 10 * 1024 * 1024
MAX_SCRIPTS = 100

st.set_page_config(
    page_title="Promo Finder",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1100px; padding-top: 2.2rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {background:#f7f8fa; border:1px solid #e6e8eb;
        padding:14px 16px; border-radius:10px;}
      div[data-testid="stFileUploader"] {border-radius:12px;}
      .eyebrow {color:#5d6673; text-transform:uppercase; letter-spacing:.09em;
        font-size:.76rem; font-weight:650; margin-bottom:.25rem;}
      .muted {color:#626b76; font-size:.95rem;}
      section[data-testid="stSidebar"] {background:#f7f8fa;}
    </style>
    """,
    unsafe_allow_html=True,
)


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", value)]


def collect_scripts(uploads: list[Any]) -> tuple[list[tuple[str, bytes]], list[str]]:
    """Read TXT and ZIP uploads without extracting archive paths to disk."""
    scripts: list[tuple[str, bytes]] = []
    warnings: list[str] = []
    unpacked_bytes = 0

    for upload in uploads:
        name = PurePosixPath(upload.name.replace("\\", "/")).name
        payload = upload.getvalue()
        if len(payload) > MAX_UPLOAD_BYTES:
            warnings.append(f"{name}: skipped because it exceeds the 50 MB upload limit.")
            continue
        if name.lower().endswith(".txt"):
            scripts.append((name, payload))
        elif name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    members = [m for m in archive.infolist()
                               if not m.is_dir() and m.filename.lower().endswith(".txt")]
                    for member in members:
                        unpacked_bytes += member.file_size
                        if member.file_size > MAX_SCRIPT_BYTES:
                            warnings.append(f"{PurePosixPath(member.filename).name}: skipped (over 10 MB).")
                            continue
                        if unpacked_bytes > MAX_ZIP_UNPACKED_BYTES:
                            warnings.append("Stopped reading this ZIP after reaching the 100 MB expanded-data limit.")
                            break
                        safe_name = PurePosixPath(member.filename.replace("\\", "/")).name
                        scripts.append((safe_name, archive.read(member)))
            except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
                warnings.append(f"{name}: could not read ZIP ({exc}).")
        else:
            warnings.append(f"{name}: skipped; upload .txt files or a .zip archive.")

    if len(scripts) > MAX_SCRIPTS:
        warnings.append(f"Only the first {MAX_SCRIPTS} text files were kept.")
        scripts = sorted(scripts, key=lambda item: natural_key(item[0]))[:MAX_SCRIPTS]
    return scripts, warnings


def analyze_scripts(
    scripts: list[tuple[str, bytes]], min_duration: float, max_duration: float
) -> tuple[list[Any], list[dict[str, Any]], list[str]]:
    all_candidates: list[Any] = []
    parsed: list[dict[str, Any]] = []
    warnings: list[str] = []

    # Keep short-lived files under the app folder so local and hosted runs do
    # not depend on the host's temp-directory permissions.
    with tempfile.TemporaryDirectory(prefix="promo_finder_", dir=BASE_DIR) as tmpdir:
        for index, (original_name, payload) in enumerate(sorted(scripts, key=lambda x: natural_key(x[0])), 1):
            if len(payload) > MAX_SCRIPT_BYTES:
                warnings.append(f"{original_name}: skipped because it exceeds the 10 MB per-script limit.")
                continue
            try:
                decoded = payload.decode("utf-8-sig")
            except UnicodeDecodeError:
                decoded = payload.decode("utf-8", errors="replace")
                warnings.append(f"{original_name}: some characters were not valid UTF-8 and may display incorrectly.")
            if not decoded.strip():
                warnings.append(f"{original_name}: empty file; skipped.")
                continue

            # Keep the source filename in the temporary path for parser metadata.
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original_name)[:100] or f"episode_{index}.txt"
            temp_path = os.path.join(tmpdir, f"{index:03d}_{safe_name}")
            with open(temp_path, "w", encoding="utf-8") as handle:
                handle.write(decoded)
            try:
                episode = parse_episode_file(temp_path)
            except (ValueError, OSError, IndexError) as exc:
                warnings.append(f"{original_name}: could not parse ({exc}).")
                continue

            if not episode.blocks:
                warnings.append(f"{original_name}: no timestamped screenplay blocks were recognized; check the input format.")
                continue
            if not episode.episode_num:
                episode.episode_num = index
            parsed.append({
                "file": original_name,
                "episode": episode.episode_num or index,
                "blocks": len(episode.blocks),
                "scenes": len(episode.scenes),
                "duration": episode.total_duration_sec,
            })
            for warning in episode.parse_warnings:
                warnings.append(f"{original_name}: {warning}")
            all_candidates.extend(
                extract_continuous_candidates(episode, min_dur=min_duration, max_dur=max_duration)
            )

    ranked, discarded = rank_and_deduplicate(all_candidates) if all_candidates else ([], [])
    return ranked, parsed, warnings + ([f"Removed {len(discarded)} overlapping candidate windows during deduplication."] if discarded else [])


def candidate_row(candidate: Any) -> dict[str, Any]:
    return {
        "rank": candidate.rank,
        "episodes": ", ".join(str(ep) for ep in candidate.episodes),
        "segments": " | ".join(
            f"Ep {segment.episode_num} {segment.start_str}-{segment.end_str}"
            for segment in candidate.segments
        ),
        "duration_seconds": round(candidate.total_duration_sec, 2),
        "score_out_of_10": round(candidate.final_score, 2),
        "hook_time": candidate.hook_timestamp,
        "hook": candidate.hook_description,
        "cliffhanger_time": candidate.cliffhanger_timestamp,
        "cliffhanger": candidate.cliffhanger_description,
        "why_candidate": candidate.why_it_works,
        "standalone_clarity": candidate.standalone_clarity,
        "confidence": candidate.confidence,
        "editor_review": candidate.review_note,
    }


def candidate_card(candidate: Any) -> None:
    episodes = ", ".join(f"Episode {ep}" for ep in candidate.episodes)
    with st.container(border=True):
        head = st.columns([3, 1, 1])
        head[0].markdown(f"### #{candidate.rank} · {episodes}")
        head[1].metric("Duration", f"{candidate.total_duration_sec:.1f}s")
        head[2].metric("Heuristic score", f"{candidate.final_score:.1f}/10")
        st.markdown(f"**Hook · {candidate.hook_timestamp}**  \n{candidate.hook_description or 'No clear hook found in the source text.'}")
        st.markdown(f"**Cliffhanger · {candidate.cliffhanger_timestamp}**  \n{candidate.cliffhanger_description or 'No clear unresolved ending identified.'}")
        st.markdown(f"**Why it is a candidate:** {candidate.why_it_works or 'The rule-based score found a possible dramatic moment.'}")
        segments = "; ".join(
            f"Episode {segment.episode_num}, {segment.start_str}–{segment.end_str} ({segment.duration_sec:.1f}s)"
            for segment in candidate.segments
        )
        st.caption(f"Suggested segment: {segments}")
        clarity = getattr(candidate, "standalone_reason", "")
        confidence = getattr(candidate, "confidence_reason", "")
        st.caption(
            f"Standalone clarity: {candidate.standalone_clarity}"
            + (f" — {clarity}" if clarity else "")
            + f" · Confidence: {candidate.confidence}"
            + (f" — {confidence}" if confidence else "")
        )
        if candidate.review_note:
            st.warning(f"Editor check: {candidate.review_note}")
        evidence_blocks = getattr(candidate, "evidence_blocks", getattr(candidate, "evidence", []))
        if evidence_blocks:
            with st.expander("Show screenplay evidence"):
                for block in evidence_blocks[:8]:
                    st.write(f"{block.get('timestamp', block.get('start_str', ''))} · {block.get('type', block.get('block_type', 'Block'))}: {block.get('text', '')}")


st.markdown('<div class="eyebrow">Editor assist · timestamped screenplays</div>', unsafe_allow_html=True)
st.title("Find promo moments in a screenplay")
st.markdown(
    '<p class="muted">Upload one episode or a ZIP of episodes. Get a ranked shortlist of 20–60 second moments for an editor to review.</p>',
    unsafe_allow_html=True,
)

with st.expander("What kind of screenplay can I upload?", expanded=False):
    st.write(
        "Use UTF-8 .txt files with timestamped blocks in this structure: "
        "`**CHARACTER / ACTION:**` followed by `Start: (00:12.00) | End: (00:15.00)` and the dialogue or action. "
        "ZIP files should contain one or more .txt episode files. The current parser is designed for this structured format; ordinary un-timestamped scripts are not supported."
    )
    st.info("The app analyzes screenplay text only. A timestamp in the script may not match the final edited video exactly.")

uploads = st.file_uploader(
    "Choose screenplay .txt files or a .zip of episodes",
    type=["txt", "zip"],
    accept_multiple_files=True,
    help="Maximums: 50 MB per upload, 10 MB per script, 100 MB expanded ZIP data, and 100 scripts.",
)

with st.expander("Or paste one timestamped episode", expanded=False):
    pasted_script = st.text_area("Paste screenplay text", height=180, placeholder="Paste a timestamped screenplay here…")

controls = st.columns([1, 1, 2])
with controls[0]:
    min_duration = st.number_input("Minimum clip (seconds)", min_value=20, max_value=59, value=20)
with controls[1]:
    max_duration = st.number_input("Maximum clip (seconds)", min_value=21, max_value=60, value=60)
with controls[2]:
    st.caption("Candidate score is a rule-based ranking aid, not a prediction of audience performance.")

run = st.button("Find candidate promos", type="primary", use_container_width=False)
if run:
    if min_duration >= max_duration:
        st.error("Maximum clip length must be greater than minimum clip length.")
    else:
        files, upload_warnings = collect_scripts(uploads or [])
        if pasted_script.strip():
            files.append(("pasted_episode.txt", pasted_script.encode("utf-8")))
        if not files:
            st.error("Upload at least one .txt file or a ZIP containing .txt screenplay files, or paste an episode above.")
        else:
            with st.spinner("Reading timestamps and ranking candidate moments…"):
                ranked, parsed, parse_warnings = analyze_scripts(files, min_duration, max_duration)
            st.session_state["promo_results"] = {
                "ranked": [candidate.to_dict() for candidate in ranked],
                "parsed": parsed,
                "warnings": upload_warnings + parse_warnings,
                "input_files": [name for name, _ in files],
            }

results = st.session_state.get("promo_results")
if results:
    st.divider()
    st.subheader("Run summary")
    metric_cols = st.columns(3)
    metric_cols[0].metric("Episodes read", len(results["parsed"]))
    metric_cols[1].metric("Timestamped blocks", sum(item["blocks"] for item in results["parsed"]))
    metric_cols[2].metric("Promo candidates", len(results["ranked"]))
    st.caption("Files: " + ", ".join(results["input_files"]))

    if results["warnings"]:
        with st.expander(f"Input and parsing notes ({len(results['warnings'])})"):
            for warning in results["warnings"]:
                st.write(f"- {warning}")
    if not results["ranked"]:
        st.warning("No candidate windows were found. Check that timestamps and blocks match the supported format, or try a different duration range.")
    else:
        min_score = st.slider("Hide candidates below this heuristic score", 0.0, 10.0, 0.0, 0.5)
        visible = [item for item in results["ranked"] if item["final_score"] >= min_score]
        st.caption(f"Showing {len(visible)} of {len(results['ranked'])} ranked candidates. Review the boundaries and story context before using a clip.")
        for item in visible[:50]:
            # Rehydrate the compact dictionary using the parsed pipeline's fields
            # needed by the card renderer; evidence and reasoning remain inspectable.
            from types import SimpleNamespace
            segments = [SimpleNamespace(**segment) for segment in item.get("segments", [])]
            card_data = dict(item)
            card_data["segments"] = segments
            candidate_card(SimpleNamespace(**card_data))

        rows = []
        for item in results["ranked"]:
            row_data = dict(item)
            row_data["segments"] = [SimpleNamespace(**segment) for segment in item.get("segments", [])]
            rows.append(candidate_row(SimpleNamespace(**row_data)))
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        download_cols = st.columns(2)
        download_cols[0].download_button(
            "Download candidates as CSV", csv_buffer.getvalue().encode("utf-8-sig"),
            file_name="promo_candidates.csv", mime="text/csv",
        )
        download_cols[1].download_button(
            "Download raw results as JSON",
            json.dumps(results, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="promo_results.json", mime="application/json",
        )

st.divider()
st.caption(
    "This prototype uses timestamp parsing and keyword-based heuristics. It does not call an AI model, "
    "understand the full plot reliably, or establish that a candidate will perform well. Human review is required."
)

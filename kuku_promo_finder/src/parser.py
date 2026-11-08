"""
Screenplay Parser for Microdrama Episodes.
Parses structured screenplay text files into typed Python dataclasses.
Every block (CAMERA, ACTION, DIALOGUE, SOUND FX) gets its own record
with start/end timestamps in both string and float-second forms.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re
import os
import glob


# ─── Timestamp helpers ───────────────────────────────────────────────────────

def time_to_seconds(ts_str: str) -> float:
    """Convert MM:SS.SS or HH:MM:SS.SS to float seconds."""
    ts_str = ts_str.strip().strip("()")
    parts = ts_str.split(":")
    if len(parts) == 2:
        return round(float(parts[0]) * 60 + float(parts[1]), 2)
    elif len(parts) == 3:
        return round(float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2]), 2)
    raise ValueError(f"Unrecognized timestamp format: {ts_str}")


def seconds_to_time(sec: float) -> str:
    """Convert float seconds to MM:SS.SS."""
    minutes = int(sec // 60)
    remainder = sec - (minutes * 60)
    return f"{minutes:02d}:{remainder:05.2f}"


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class ScriptBlock:
    """One timestamped block in the screenplay: a camera direction, action beat,
    dialogue line, or sound effect."""
    block_id: int
    raw_tag: str           # e.g. "LADY JULIANA (Confused, Breathless)"
    block_type: str        # CAMERA | ACTION | DIALOGUE | SOUND FX
    character: Optional[str]
    mood: Optional[str]
    start_sec: float
    end_sec: float
    start_str: str
    end_str: str
    duration_sec: float
    text: str
    scene_num: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "raw_tag": self.raw_tag,
            "block_type": self.block_type,
            "character": self.character,
            "mood": self.mood,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "start_str": self.start_str,
            "end_str": self.end_str,
            "duration_sec": self.duration_sec,
            "text": self.text,
            "scene_num": self.scene_num,
        }


@dataclass
class Scene:
    scene_num: int
    heading: str
    start_sec: float
    end_sec: float
    start_str: str
    end_str: str
    duration_sec: float
    blocks: List[ScriptBlock] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_num": self.scene_num,
            "heading": self.heading,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "duration_sec": self.duration_sec,
            "block_count": len(self.blocks),
        }


@dataclass
class Episode:
    episode_num: int
    episode_id: str        # e.g. "Episode 1671703"
    filename: str
    logline: str
    continuity_notes: str
    total_duration_sec: float
    scenes: List[Scene] = field(default_factory=list)
    blocks: List[ScriptBlock] = field(default_factory=list)
    parse_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_num": self.episode_num,
            "episode_id": self.episode_id,
            "filename": self.filename,
            "logline": self.logline,
            "continuity_notes": self.continuity_notes,
            "total_duration_sec": self.total_duration_sec,
            "scene_count": len(self.scenes),
            "block_count": len(self.blocks),
            "parse_warnings": self.parse_warnings,
            "scenes": [s.to_dict() for s in self.scenes],
        }


# ─── Main parsing ────────────────────────────────────────────────────────────

# Regex to capture each **TAG:** / Start: (...) | End: (...) / text block
_BLOCK_RE = re.compile(
    r"\*\*([^*]+?):\*\*\s*\n"                       # **TAG:**
    r"Start:\s*\(([0-9:.]+)\)\s*\|\s*End:\s*\(([0-9:.]+)\)\s*\n"  # timestamps
    r"(.*?)(?=\n\*\*|\n---|\Z)",                    # body text
    re.DOTALL,
)


def _classify_block(raw_tag: str):
    """Return (block_type, character_name, mood) from the raw tag string."""
    if raw_tag == "CAMERA":
        return "CAMERA", None, None
    if raw_tag == "ACTION":
        return "ACTION", None, None
    if "SOUND" in raw_tag.upper():
        return "SOUND FX", None, None
    # Dialogue: "LADY JULIANA (Confused, Breathless)" or "THE FORMER GROOM"
    m = re.match(r"^([^(]+?)(?:\s*\(([^)]+)\))?\s*$", raw_tag)
    if m:
        return "DIALOGUE", m.group(1).strip(), (m.group(2).strip() if m.group(2) else None)
    return "DIALOGUE", raw_tag.strip(), None


def parse_episode_file(filepath: str) -> Episode:
    """Parse a single episode screenplay file into an Episode dataclass."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    filename = os.path.basename(filepath)
    warnings: List[str] = []

    # ── Metadata ──
    m = re.search(r"EPISODE NUMBER:\s*(?:Episode\s*)?(\d+)", content, re.I)
    ep_num = int(m.group(1)) if m else 0
    if not m:
        warnings.append("Could not parse episode number")

    # Extract the full episode identifier from the filename
    ep_id_match = re.search(r"(Episode \d+)", filename)
    ep_id = ep_id_match.group(1) if ep_id_match else f"Episode {ep_num}"

    m = re.search(r"EPISODE LOGLINE:\s*(.+?)(?=\n[A-Z ]+:|\n---|\Z)", content, re.S)
    logline = m.group(1).strip() if m else ""

    m = re.search(r"CONTINUITY NOTES:\s*(.+?)(?=\n---|\Z)", content, re.S)
    continuity = m.group(1).strip() if m else ""

    # ── Scenes ──
    scene_chunks = re.split(r"(SCENE\s+\d+)", content)
    scenes: List[Scene] = []
    all_blocks: List[ScriptBlock] = []
    block_counter = 0

    for i in range(1, len(scene_chunks), 2):
        scene_header = scene_chunks[i]
        scene_body = scene_chunks[i + 1] if i + 1 < len(scene_chunks) else ""

        s_num_match = re.search(r"\d+", scene_header)
        s_num = int(s_num_match.group(0)) if s_num_match else len(scenes) + 1

        heading_m = re.search(r"Scene heading:\s*(.+)", scene_body)
        heading = heading_m.group(1).strip() if heading_m else "UNKNOWN"

        start_m = re.search(r"Scene start:\s*([0-9:.]+)", scene_body)
        end_m = re.search(r"Scene end:\s*([0-9:.]+)", scene_body)
        s_start_str = start_m.group(1) if start_m else "00:00.00"
        s_end_str = end_m.group(1) if end_m else "00:00.00"
        s_start = time_to_seconds(s_start_str)
        s_end = time_to_seconds(s_end_str)

        scene = Scene(
            scene_num=s_num,
            heading=heading,
            start_sec=s_start,
            end_sec=s_end,
            start_str=s_start_str,
            end_str=s_end_str,
            duration_sec=round(s_end - s_start, 2),
        )

        for bm in _BLOCK_RE.finditer(scene_body):
            raw_tag = bm.group(1).strip()
            b_start_str = bm.group(2).strip()
            b_end_str = bm.group(3).strip()
            text = bm.group(4).strip()

            b_start = time_to_seconds(b_start_str)
            b_end = time_to_seconds(b_end_str)
            dur = round(b_end - b_start, 2)

            if dur < 0:
                warnings.append(f"Negative duration in block at {b_start_str}: {dur}s")

            block_counter += 1
            b_type, character, mood = _classify_block(raw_tag)

            block = ScriptBlock(
                block_id=block_counter,
                raw_tag=raw_tag,
                block_type=b_type,
                character=character,
                mood=mood,
                start_sec=b_start,
                end_sec=b_end,
                start_str=b_start_str,
                end_str=b_end_str,
                duration_sec=dur,
                text=text,
                scene_num=s_num,
            )
            scene.blocks.append(block)
            all_blocks.append(block)

        scenes.append(scene)

    # Check: did we find any Start: timestamps that we didn't capture?
    expected = len(re.findall(r"Start:\s*\([0-9:.]+\)", content))
    if expected != len(all_blocks):
        warnings.append(
            f"Timestamp count mismatch: found {expected} Start: markers but parsed {len(all_blocks)} blocks"
        )

    total_dur = all_blocks[-1].end_sec if all_blocks else 0.0

    return Episode(
        episode_num=ep_num,
        episode_id=ep_id,
        filename=filename,
        logline=logline,
        continuity_notes=continuity,
        total_duration_sec=total_dur,
        scenes=scenes,
        blocks=all_blocks,
        parse_warnings=warnings,
    )


def parse_all_episodes(dirpath: str) -> List[Episode]:
    """Parse all episode .txt files in a directory, sorted by episode number."""
    files = sorted(glob.glob(os.path.join(dirpath, "*.txt")))
    if not files:
        raise FileNotFoundError(f"No .txt files found in {dirpath}")
    episodes = [parse_episode_file(f) for f in files]
    episodes.sort(key=lambda e: e.episode_num)
    return episodes


if __name__ == "__main__":
    import json
    test_dir = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "I Married a Broken Soldier. He was a Duke-script",
        "I Married a Broken Soldier. He was a Duke",
    )
    if not os.path.isdir(test_dir):
        test_dir = r".\I Married a Broken Soldier. He was a Duke-script\I Married a Broken Soldier. He was a Duke"
    eps = parse_all_episodes(test_dir)
    print(f"Parsed {len(eps)} episodes, {sum(len(e.blocks) for e in eps)} total blocks")
    for e in eps:
        if e.parse_warnings:
            print(f"  Ep {e.episode_num}: WARNINGS: {e.parse_warnings}")

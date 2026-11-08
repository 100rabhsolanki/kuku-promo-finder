"""
Pure Python PDF Generator for Solution Document (Strictly 2 Pages).
Compiles a clean, professional, publication-quality 2-page PDF
with zero external dependencies.
"""

import os

class SimplePDFWriter:
    def __init__(self, page_width=595.28, page_height=841.89):  # A4
        self.width = page_width
        self.height = page_height
        self.pages = []
        self.current_content = []

    def new_page(self):
        if self.current_content:
            self.pages.append("\n".join(self.current_content))
            self.current_content = []

    def draw_line(self, x1, y1, x2, y2, stroke_color=(0.7, 0.7, 0.7), line_width=0.75):
        r, g, b = stroke_color
        self.current_content.append(f"{r:.2f} {g:.2f} {b:.2f} RG {line_width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def draw_rect(self, x, y, w, h, fill_color=(0.95, 0.95, 0.95), stroke_color=(0.8, 0.8, 0.8)):
        fr, fg, fb = fill_color
        sr, sg, sb = stroke_color
        self.current_content.append(f"{fr:.2f} {fg:.2f} {fb:.2f} rg {sr:.2f} {sg:.2f} {sb:.2f} RG {x:.2f} {y:.2f} {w:.2f} {h:.2f} re B")

    def draw_text(self, text: str, x: float, y: float, font="F1", size=9.0, color=(0.1, 0.1, 0.1)):
        r, g, b = color
        escaped = (
            text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("latin-1", "replace")
            .decode("latin-1")
        )
        self.current_content.append(
            f"BT /{font} {size:.2f} Tf {r:.2f} {g:.2f} {b:.2f} rg {x:.2f} {y:.2f} Td ({escaped}) Tj ET"
        )

    def compile_pdf(self) -> bytes:
        if self.current_content:
            self.pages.append("\n".join(self.current_content))

        num_pages = len(self.pages)
        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        page_obj_ids = [3 + i * 2 for i in range(num_pages)]
        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
        objects.append(f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>")

        font_res = (
            "/Font << "
            "/F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
            "/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> "
            "/F3 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >> "
            ">>"
        )

        for i, page_data in enumerate(self.pages):
            content_id = 4 + i * 2
            page_dict = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                f"/Contents {content_id} 0 R "
                f"/Resources << {font_res} >> >>"
            )
            objects.append(page_dict)

            stream_bytes = page_data.encode("latin-1")
            content_dict = f"<< /Length {len(stream_bytes)} >>\nstream\n{page_data}\nendstream"
            objects.append(content_dict)

        pdf_out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]

        for i, obj in enumerate(objects, 1):
            offsets.append(len(pdf_out))
            if isinstance(obj, str):
                pdf_out.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
            else:
                pdf_out.extend(f"{i} 0 obj\n".encode("latin-1"))
                pdf_out.extend(obj)
                pdf_out.extend(b"\nendobj\n")

        xref_pos = len(pdf_out)
        pdf_out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1"))
        for off in offsets[1:]:
            pdf_out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

        pdf_out.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
        )
        return bytes(pdf_out)


def build_two_page_solution_document(output_pdf_path: str):
    """Builds the 2-page solution PDF matching LaTeX structure."""
    pdf = SimplePDFWriter(page_width=595.28, page_height=841.89)

    # ════════════════════════ PAGE 1 ════════════════════════
    # Header Banner
    pdf.draw_rect(36, 794, 523, 20, fill_color=(0.12, 0.23, 0.45), stroke_color=(0.12, 0.23, 0.45))
    pdf.draw_text("KUKU AI GENERALIST ASSIGNMENT | PROBLEM 1: FIND THE PROMOS (ADS)", 44, 801, font="F2", size=9.5, color=(1, 1, 1))

    # Title, Candidate Info & Live Prototype Links
    pdf.draw_text("Algorithmic & AI Promo Discovery for Vertical Microdramas", 36, 778, font="F2", size=13.5, color=(0.1, 0.15, 0.3))
    pdf.draw_text("Candidate: Saurabh Solanki | Live Prototype: https://kuku-promo-finder-saurabh105.streamlit.app/", 36, 765, font="F2", size=8.0, color=(0.1, 0.3, 0.6))
    pdf.draw_text("GitHub Repository: https://github.com/100rabhsolanki/kuku-promo-finder | Dataset: 50 Episodes (3,727 blocks)", 36, 754, font="F3", size=7.5, color=(0.35, 0.35, 0.35))
    pdf.draw_line(36, 747, 559, 747, stroke_color=(0.8, 0.8, 0.8), line_width=0.75)

    # Section 1
    y = 730
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("1. PROBLEM CHOICE, TARGET USER & EDITORIAL WORKFLOW", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 14
    pdf.draw_text("Why Problem 1: In high-velocity microdrama publishing, user acquisition depends entirely on short-form promo ads (20-60s)", 36, y, font="F2", size=8.5, color=(0.1, 0.1, 0.1))
    y -= 11
    pdf.draw_text("on TikTok, Instagram Reels, and YouTube Shorts. The bottleneck is not rendering, but creative discovery: human editors spend", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("1.5 to 2 hours manually scrubbing through 50 episodes per series to find hooks, reveals, and cliffhangers.", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("Target User & Transformation: Microdrama Video Editors and Growth Marketers. The tool serves as an algorithmic scout,", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("transforming a 100-minute manual video scrub into a 3-minute review of pre-scored, timestamped candidate promo cards.", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))

    # Section 2
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("2. OPERATIONAL ASSUMPTIONS & TIMING REALITIES", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))

    assumptions = [
        ("Screenplay Timestamps vs. Finished Video Runtime:", " Timestamps represent planned script timings. Editorial pauses or bumpers require"),
        ("", "editor verification. The tool anchors cuts to verified script timestamps rather than estimating untracked pacing."),
        ("Multi-Track Concurrency:", " CAMERA, ACTION, and DIALOGUE overlap in the screenplay. Clip bounds are computed from"),
        ("", "the earliest starting event to the latest ending event of the dramatic beat without duplicate duration accumulation."),
        ("Scroll-Stopping Hook Window:", " Social video drop-off occurs within 2.5-3.0s. Hooks occurring after 3.5s are heavily penalized."),
        ("Single vs. Multi-Episode Promos:", " Continuous single-episode clips offer optimal narrative cohesion; multi-segment promos"),
        ("", "are curated for high-contrast pairs (e.g., Altar Betrayal in Ep 1 paired with Underdog Marriage in Ep 4).")
    ]
    for bold_p, text_r in assumptions:
        y -= 11
        if bold_p:
            pdf.draw_text(bold_p, 36, y, font="F2", size=8.5, color=(0.15, 0.15, 0.15))
            pdf.draw_text(text_r, 36 + len(bold_p) * 4.8, y, font="F1", size=8.5, color=(0.25, 0.25, 0.25))
        else:
            pdf.draw_text(text_r, 36, y, font="F1", size=8.5, color=(0.25, 0.25, 0.25))

    # Section 3
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("3. SYSTEM ARCHITECTURE & RESPONSIBILITY DIVISION", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 13
    pdf.draw_text("We enforce a strict separation between deterministic code/rules and heuristic/AI scoring:", 36, y, font="F3", size=8.5, color=(0.3, 0.3, 0.3))

    table_y = y - 10
    pdf.draw_rect(36, table_y - 48, 523, 52, fill_color=(0.98, 0.98, 0.98), stroke_color=(0.8, 0.8, 0.8))
    pdf.draw_line(36, table_y - 14, 559, table_y - 14, stroke_color=(0.8, 0.8, 0.8), line_width=0.5)
    pdf.draw_line(275, table_y + 4, 275, table_y - 48, stroke_color=(0.8, 0.8, 0.8), line_width=0.5)

    pdf.draw_text("HANDLED BY DETERMINISTIC CODE / RULES", 44, table_y - 9, font="F2", size=8.5, color=(0.1, 0.3, 0.1))
    pdf.draw_text("HANDLED BY SCORING ENGINE / AI MODEL", 285, table_y - 9, font="F2", size=8.5, color=(0.4, 0.1, 0.1))

    rules_lines = [
        "- Script block regex parsing (3,727 blocks parsed, 0 missed)",
        "- Strict 20-60s window math and timestamp arithmetic",
        "- Non-Maximum Suppression (NMS) IoU overlap deduplication"
    ]
    ai_lines = [
        "- Hook immediacy, shock factor & verbal jolt evaluation",
        "- Cliffhanger urgency & unresolved dramatic stakes",
        "- Standalone clarity & context-dependency penalty"
    ]
    for idx, (rl, al) in enumerate(zip(rules_lines, ai_lines)):
        pdf.draw_text(rl, 40, table_y - 23 - (idx * 10), font="F1", size=8.0, color=(0.2, 0.2, 0.2))
        pdf.draw_text(al, 280, table_y - 23 - (idx * 10), font="F1", size=8.0, color=(0.2, 0.2, 0.2))

    # Section 4
    y = table_y - 68
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("4. MULTI-CRITERIA SCORING & RANKING FORMULATION", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 13
    pdf.draw_text("Composite Score = 0.30(Hook) + 0.25(Cliffhanger) + 0.20(Standalone) + 0.15(Intensity) + 0.10(Context)", 36, y, font="F2", size=8.5, color=(0.1, 0.15, 0.35))
    y -= 11
    pdf.draw_text("1. Hook Immediacy (0-10): Scored by linguistic shock (e.g. 'You're the Duke?', 'Married a beggar!'), physical aggression (slap, blade,", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 9
    pdf.draw_text("   shattered gate), and sound stingers within the first 3.5s. Decays by 40%/s for every second of delay.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("2. Cliffhanger Urgency (0-10): Unanswered questions, cut-to-black scene peaks, interrupted revelations, and red-hot iron threats.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("3. Standalone Clarity (0-10): Rewards universal archetypes (betrayal at altar, undercover Duke); penalizes niche medical/lore jargon.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("4. Temporal Deduplication: Retains top-scoring moments while eliminating 6,377 overlapping time-shifted candidate windows.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))

    # Page 1 Footer
    pdf.draw_line(36, 42, 559, 42, stroke_color=(0.8, 0.8, 0.8), line_width=0.75)
    pdf.draw_text("Kuku AI Generalist Assignment - Problem 1: Find the Promos", 36, 30, font="F3", size=8, color=(0.4, 0.4, 0.4))
    pdf.draw_text("Page 1 of 2", 520, 30, font="F1", size=8, color=(0.4, 0.4, 0.4))

    # ════════════════════════ PAGE 2 ════════════════════════
    pdf.new_page()

    # Header Banner Page 2
    pdf.draw_rect(36, 792, 523, 22, fill_color=(0.12, 0.23, 0.45), stroke_color=(0.12, 0.23, 0.45))
    pdf.draw_text("KUKU AI GENERALIST ASSIGNMENT | PROBLEM 1: QUALITY AUDIT & PRODUCTION SCALING", 44, 800, font="F2", size=10, color=(1, 1, 1))

    # Section 5
    y = 770
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("5. TOP-RANKED PROMO CANDIDATES (PROVEN FROM 50-EPISODE RUN)", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))

    top_promos = [
        ("Rank 1 (Ep 45, 54.6s | Score 9.02):", " Undercover Duke Reveal. Hook: Juliana discovers 'You're the Duke?' at 00:22.90."),
        ("", "Climax: Alexander frees Juliana from chains; Catherine screams 'Wife?!' in public horror at 01:10.50."),
        ("Rank 2 (Ep 42, 57.8s | Score 8.84):", " Shattered Cathedral Gates. Hook: 'Guards! Arrest this imposter!' at 00:18.00."),
        ("", "Climax: Alexander emerges in full ducal regalia; Duchess reveals: 'Let everyone hear me! This is my son Alexander!'"),
        ("Rank 3 (Ep 11, 57.1s | Score 8.15):", " Class Betrayal Confrontation. Hook: Gerald mocks 'You married a beggar!' at 00:29.30."),
        ("", "Climax: Gerald dares him: 'Going to strike a gentleman in front of his wife?' at 01:24.00 before physical confrontation."),
        ("Rank 4 (Ep 11 + Ep 42, 36.3s | Score 8.10):", " Mockery to Ducal Vindication Multi-Segment. Gerald mocks Juliana's beggar husband,"),
        ("", "cross-cut to Ep 42 where Alexander's mother proclaims him the rightful Duke before the royal guards.")
    ]
    for bold_p, text_r in top_promos:
        y -= 11
        if bold_p:
            pdf.draw_text(bold_p, 36, y, font="F2", size=8.5, color=(0.1, 0.25, 0.1))
            pdf.draw_text(text_r, 36 + len(bold_p) * 4.6, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
        else:
            pdf.draw_text(text_r, 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))

    # Section 6
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("6. HONEST QUALITY CHECK: REAL FAILURE MODES & EDGE CASES", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 12
    pdf.draw_text("Automated systems fail when narrative context cannot be deduced from isolated words. We observed three failures:", 36, y, font="F3", size=8.5, color=(0.3, 0.3, 0.3))

    failures = [
        ("Failure 1 (False Positive - Medical Cues in Ep 8 & 9):", " Words like 'blood', 'fever', and 'wound' scored high on intensity"),
        ("", "but represented quiet herbal caretaking rather than dynamic viral conflict. Fix: Added penalties for non-combative medical scenes."),
        ("Failure 2 (Context-Trapped Climax in Ep 29):", " High dungeon tension scored well, but dialogue centered on 'charcoal antidotes'"),
        ("", "and 'mother's grimoire'. A cold TikTok scroller has zero idea who Rupert is. Fix: Standalone comprehensibility penalizes lore-density."),
        ("Failure 3 (Establishing Shot Lag in Ep 7):", " Insult occurs at 00:08.50 after silent door opening. If clipped from 00:00.00,"),
        ("", "the promo loses the viewer. Fix: Window start dynamically snaps to the exact timestamp of the hook beat rather than scene start.")
    ]
    for bold_p, text_r in failures:
        y -= 11
        if bold_p:
            pdf.draw_text(bold_p, 36, y, font="F2", size=8.5, color=(0.4, 0.1, 0.1))
            pdf.draw_text(text_r, 36 + len(bold_p) * 4.6, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
        else:
            pdf.draw_text(text_r, 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))

    # Section 7
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("7. HUMAN-IN-THE-LOOP EDITORIAL PROTOCOL", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 12
    pdf.draw_text("The tool proposes candidate cards; the human video editor confirms final cuts via a 3-step checklist:", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 10
    pdf.draw_text("1. Visual Jolt Audit: Verify the opening 0-2s has immediate motion or punch-in (front-trim if actor hesitation occurs).", 42, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 10
    pdf.draw_text("2. Audio Tail Audit: Confirm dialogue does not cut mid-sentence; verify music swell resolves into an unresolved blackout.", 42, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 10
    pdf.draw_text("3. Channel Destination: Route betrayal/slap clips (Ep 1, 11) to TikTok; route vindication/identity reveals (Ep 42, 45) to YouTube Shorts.", 42, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))

    # Section 8
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("8. AI TOOLS USED & WHERE THE MODEL GOT SOMETHING WRONG", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 12
    pdf.draw_text("AI Tools: Gemini 3.8 Flash / Claude 3.5 Sonnet for archetype analysis, rubric calibration, and failure-mode clustering.", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 11
    pdf.draw_text("Where the AI Got It Wrong: When analyzing Ep 1, an LLM flagged Juliana's tearful clenching of her bridal gown (02:11.30)", 36, y, font="F2", size=8.5, color=(0.3, 0.1, 0.1))
    y -= 9
    pdf.draw_text("as a 'resolved resolution' because the groom had finished speaking and walked away. The AI mistook the physical end of an", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 9
    pdf.draw_text("argument for emotional closure, missing that Juliana's hardening glare was the ultimate microdrama cliffhanger setup.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))

    # Section 9
    y -= 16
    pdf.draw_rect(36, y - 4, 523, 16, fill_color=(0.93, 0.95, 0.98), stroke_color=(0.85, 0.88, 0.94))
    pdf.draw_text("9. SCALING ACROSS SHOWS & PRODUCTION TIMELINE", 42, y, font="F2", size=9.5, color=(0.12, 0.23, 0.45))
    y -= 12
    pdf.draw_text("Production Scaling: The Python engine processed 50 episodes (102.6 minutes of drama, 3,727 blocks) in 2.01 seconds.", 36, y, font="F1", size=8.5, color=(0.2, 0.2, 0.2))
    y -= 10
    pdf.draw_text("Cost at Scale: $0.00 for rule-based parsing and NMS deduplication. When connected to a lightweight LLM API (e.g., Gemini Flash),", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))
    y -= 9
    pdf.draw_text("evaluating the 144 candidate windows costs less than $0.01 per show, compared to $40+ of human editor scrubbing time.", 36, y, font="F1", size=8.0, color=(0.2, 0.2, 0.2))

    # Page 2 Footer
    pdf.draw_line(36, 42, 559, 42, stroke_color=(0.8, 0.8, 0.8), line_width=0.75)
    pdf.draw_text("Kuku AI Generalist Assignment - Problem 1: Find the Promos", 36, 30, font="F3", size=8, color=(0.4, 0.4, 0.4))
    pdf.draw_text("Page 2 of 2 (Strictly 2 Pages Enforced)", 420, 30, font="F2", size=8, color=(0.4, 0.4, 0.4))

    pdf_bytes = pdf.compile_pdf()
    with open(output_pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Successfully generated 2-page PDF ({len(pdf_bytes)} bytes) at: {output_pdf_path}")


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "..", "submission", "Kuku_Problem_1_Solution_Document.pdf")
    build_two_page_solution_document(out_path)

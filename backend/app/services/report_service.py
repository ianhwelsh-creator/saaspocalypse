"""Cohort PDF report generation service using fpdf2."""

import io
import logging
import math
import unicodedata

from fpdf import FPDF

logger = logging.getLogger(__name__)


def _safe_text(text: str) -> str:
    """Sanitize text to only contain characters supported by Helvetica (Latin-1)."""
    if not text:
        return ""
    replacements = {
        "\u2013": "-", "\u2014": "--", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
        "\u2032": "'", "\u2033": '"', "\u00a0": " ", "\u200b": "",
        "\u200e": "", "\u200f": "", "\ufeff": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    normalized = unicodedata.normalize("NFKD", text)
    try:
        return normalized.encode("latin-1", errors="replace").decode("latin-1")
    except Exception:
        return normalized.encode("ascii", errors="replace").decode("ascii")


def _logo_url(company_name: str) -> str:
    """Generate logo URL via Google Favicons (mirrors cohort_service._logo)."""
    from app.services.cohort_service import DOMAIN_OVERRIDES

    lower = company_name.lower().strip()
    if lower in DOMAIN_OVERRIDES:
        return f"https://www.google.com/s2/favicons?domain={DOMAIN_OVERRIDES[lower]}&sz=128"
    clean = lower.replace(" ", "").replace(",", "").replace("'", "")
    if clean.endswith(".com") or clean.endswith(".io") or clean.endswith(".ai"):
        domain = clean
    else:
        clean = clean.replace(".", "")
        domain = f"{clean}.com"
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def _score_color(val: int, max_val: int = 20) -> tuple[int, int, int]:
    """Return red->yellow->green gradient color based on score value."""
    ratio = val / max_val if max_val > 0 else 0
    ratio = max(0.0, min(1.0, ratio))
    if ratio < 0.5:
        # Red to Yellow
        t = ratio / 0.5
        r = 220
        g = int(60 + 160 * t)
        b = 50
    else:
        # Yellow to Green
        t = (ratio - 0.5) / 0.5
        r = int(220 - 180 * t)
        g = int(180 + 20 * t)
        b = int(50 + 30 * t)
    return (r, g, b)


def _score_color_100(val: int) -> tuple[int, int, int]:
    """Red->yellow->green for 0-100 scale."""
    return _score_color(val, 100)


# -- Constants ----------------------------------------------------------------

ZONE_COLORS = {
    "fortress": (26, 157, 63),
    "adaptation": (43, 127, 212),
    "compression": (212, 155, 26),
    "dead": (214, 57, 57),
}

ZONE_BG_COLORS = {
    "fortress": (232, 245, 236),
    "adaptation": (232, 240, 250),
    "compression": (250, 243, 224),
    "dead": (250, 232, 232),
}

ZONE_LABELS = {
    "fortress": "Fortress Zone",
    "adaptation": "Adaptation Zone",
    "compression": "Compression Zone",
    "dead": "Dead Zone",
}

ZONE_SHORT = {
    "fortress": "Fortress",
    "adaptation": "Adaptation",
    "compression": "Compression",
    "dead": "Dead Zone",
}

ZONE_DESCRIPTIONS = {
    "fortress": "AI-accelerated with strong defensibility (X>=60, Y>=60). Regulated verticals with institutional data moats become orchestration layers for AI agents.",
    "compression": "Seat-count revenue erosion risk (X<40, Y>60). Valuable data moat but simple workflows mean AI reduces required human seats and compresses pricing power.",
    "adaptation": "Workflow lock-in, must outpace AI natives (X>60, Y<40). Complex workflows provide runway, but weak data defensibility means AI erodes competitive position over time.",
    "dead": "High risk of AI obsolescence (X<40, Y<40). Simple tasks with no data defensibility that AI agents can fully automate.",
}

ZONE_ORDER = {"fortress": 0, "adaptation": 1, "compression": 2, "dead": 3}

X_FACTOR_LABELS = [
    ("regulatory_overlay", "Regulatory Overlay"),
    ("multi_stakeholder", "Multi-Stakeholder"),
    ("judgment_intensity", "Judgment Intensity"),
    ("process_depth", "Process Depth"),
    ("institutional_knowledge", "Institutional Knowledge"),
]

Y_FACTOR_LABELS = [
    ("regulatory_lock_in", "Regulatory Lock-in"),
    ("data_gravity", "Data Gravity"),
    ("network_effects", "Network Effects"),
    ("portability_resistance", "Portability Resistance"),
    ("proprietary_enrichment", "Proprietary Enrichment"),
]


# -- PDF Subclass -------------------------------------------------------------

class CohortReportPDF(FPDF):
    def __init__(self, cohort_name: str):
        super().__init__()
        self.cohort_name = cohort_name
        self._is_cover = True

    def header(self):
        if self._is_cover:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        half = (self.w - self.l_margin - self.r_margin) / 2
        self.cell(half, 8, self.cohort_name, align="L")
        self.cell(half, 8, "SaaSpocalypse Report", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, 16, self.w - self.r_margin, 16)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


# -- Report Service ------------------------------------------------------------

class ReportService:

    def generate_cohort_report(
        self,
        cohort_name: str,
        cohort_created_at: str | None,
        members: list[dict],
        evaluations: list[dict],
    ) -> bytes:
        safe_name = _safe_text(cohort_name)
        safe_members = self._sanitize_members(members)
        safe_evals = self._sanitize_evaluations(evaluations)

        pdf = CohortReportPDF(safe_name)
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=25)

        self._render_cover_page(pdf, safe_name, cohort_created_at, safe_members)
        pdf._is_cover = False
        self._render_summary_table(pdf, safe_members, safe_evals)
        self._render_matrix_chart(pdf, safe_members)
        self._render_company_details(pdf, safe_evals)

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    # -- Sanitizers ------------------------------------------------------------

    @staticmethod
    def _sanitize_members(members: list[dict]) -> list[dict]:
        return [{
            **m,
            "company_name": _safe_text(m.get("company_name", "")),
            "key_risk": _safe_text(m.get("key_risk", "")),
            "ai_summary": _safe_text(m.get("ai_summary", "")),
        } for m in members]

    @staticmethod
    def _sanitize_evaluations(evaluations: list[dict]) -> list[dict]:
        return [{
            **ev,
            "company_name": _safe_text(ev.get("company_name", "")),
            "overview": _safe_text(ev.get("overview", "")),
            "justification": _safe_text(ev.get("justification", "")),
            "diligence": [_safe_text(str(d)) for d in ev.get("diligence", [])],
        } for ev in evaluations]

    # -- Cover Page ------------------------------------------------------------

    def _render_cover_page(self, pdf: CohortReportPDF, cohort_name: str, created_at: str | None, members: list[dict]):
        pdf.add_page()

        pdf.ln(35)

        # Label
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 8, "SAASPOCALYPSE", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # Main title
        pdf.set_font("Helvetica", "B", 30)
        pdf.set_text_color(45, 43, 41)
        pdf.cell(0, 16, "Cohort Report", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Cohort name
        pdf.set_font("Helvetica", "", 18)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 10, cohort_name, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Date + company count
        date_str = ""
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                date_str = dt.strftime("%B %d, %Y")
            except Exception:
                date_str = created_at[:10] if len(created_at) >= 10 else created_at

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(130, 130, 130)
        info = f"{len(members)} companies analyzed"
        if date_str:
            info += f"  |  {date_str}"
        pdf.cell(0, 8, info, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)

        # -- Zone Legend: explain all four zones in a 2x2 grid --
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(0, 6, "AI DISRUPTION ZONES", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Count zones
        zone_counts: dict[str, int] = {}
        for m in members:
            z = m.get("zone", "unknown")
            zone_counts[z] = zone_counts.get(z, 0) + 1

        # 2x2 grid of zone cards — taller cards with bigger text
        card_w = 88
        card_h = 40
        gap = 4
        grid_x = (pdf.w - 2 * card_w - gap) / 2

        zones_grid = [
            ("fortress", "adaptation"),
            ("compression", "dead"),
        ]

        for row_idx, (z_left, z_right) in enumerate(zones_grid):
            y_pos = pdf.get_y()
            for col_idx, zone in enumerate((z_left, z_right)):
                x_pos = grid_x + col_idx * (card_w + gap)
                color = ZONE_COLORS.get(zone, (150, 150, 150))
                bg = ZONE_BG_COLORS.get(zone, (240, 240, 240))
                label = ZONE_LABELS.get(zone, zone.title())
                desc = ZONE_DESCRIPTIONS.get(zone, "")
                count = zone_counts.get(zone, 0)

                # Card background
                pdf.set_fill_color(*bg)
                pdf.rect(x_pos, y_pos, card_w, card_h, style="F")

                # Left color stripe
                pdf.set_fill_color(*color)
                pdf.rect(x_pos, y_pos, 2.5, card_h, style="F")

                # Zone name + count (always show count)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*color)
                pdf.set_xy(x_pos + 6, y_pos + 3)
                pdf.cell(card_w - 8, 5, f"{label} ({count})")

                # Description text — full text, larger font
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(80, 80, 80)
                pdf.set_xy(x_pos + 6, y_pos + 10)
                pdf.multi_cell(card_w - 9, 3.5, desc)

            pdf.set_y(y_pos + card_h + gap)

    # -- Executive Summary -----------------------------------------------------

    def _render_summary_table(self, pdf: CohortReportPDF, members: list[dict], evaluations: list[dict]):
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(45, 43, 41)
        pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        sorted_members = sorted(members, key=lambda m: ZONE_ORDER.get(m.get("zone", ""), 99))

        # Build evaluation lookup
        eval_map: dict[int, dict] = {}
        for ev in evaluations:
            eval_map[ev.get("id", 0)] = ev

        for m in sorted_members:
            zone = m.get("zone", "unknown")
            color = ZONE_COLORS.get(zone, (100, 100, 100))
            bg_color = ZONE_BG_COLORS.get(zone, (240, 240, 240))
            zone_label = ZONE_SHORT.get(zone, zone.title())
            name = m.get("company_name", "Unknown")
            x_score = int(m.get("x_score", 0))
            y_score = int(m.get("y_score", 0))
            key_risk = m.get("key_risk", "N/A")

            # Get the justification (reasoning) from the full evaluation
            ev = eval_map.get(m.get("evaluation_id", 0), {})
            justification = ev.get("justification", "")
            # First 3 sentences of justification as reasoning
            sentences = [s.strip() for s in justification.split(". ") if s.strip()]
            reasoning = ". ".join(sentences[:3])
            if reasoning and not reasoning.endswith("."):
                reasoning += "."

            # Check space
            if pdf.get_y() > pdf.h - 65:
                pdf.add_page()

            # Company name + zone badge
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(45, 43, 41)
            name_w = pdf.get_string_width(name) + 2
            pdf.cell(name_w, 7, name)
            pdf.cell(3, 7, "")

            pdf.set_font("Helvetica", "B", 8)
            badge_w = pdf.get_string_width(zone_label) + 6
            pdf.set_fill_color(*bg_color)
            pdf.set_text_color(*color)
            pdf.cell(badge_w, 7, zone_label, fill=True, new_x="LMARGIN", new_y="NEXT")

            # Scores row with color-coded values
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Complexity: {x_score}/100   |   Data Moat: {y_score}/100", new_x="LMARGIN", new_y="NEXT")

            # Reasoning text
            if reasoning:
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 4, reasoning)

            # Key risk
            if key_risk and key_risk != "N/A":
                pdf.ln(1)
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(180, 80, 80)
                prefix = "Key Risk: "
                prefix_w = pdf.get_string_width(prefix) + 1
                pdf.cell(prefix_w, 4, prefix)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(150, 80, 80)
                pdf.multi_cell(0, 4, key_risk)

            # Separator
            pdf.ln(3)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(4)

    # -- Matrix Chart ----------------------------------------------------------

    def _render_matrix_chart(self, pdf: CohortReportPDF, members: list[dict]):
        pdf.add_page("L")  # Landscape

        # CRITICAL: disable auto page break for chart rendering
        pdf.set_auto_page_break(auto=False)

        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(45, 43, 41)
        pdf.cell(0, 10, "AI Disruption Matrix", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Chart dimensions (landscape: 297 x 210 mm)
        chart_x = 45
        chart_y = 38
        chart_w = 210
        chart_h = 140

        # Helper: convert score 0-100 to chart pixel position
        def sx(score):
            return chart_x + (score / 100) * chart_w

        def sy(score):
            return chart_y + chart_h - (score / 100) * chart_h

        # Zone boundary position (clean 50/50 split)
        x50 = sx(50)
        y50 = sy(50)

        # -- Quadrant backgrounds (4 clean zones split at 50) --
        # Dead Zone: bottom-left (x<50, y<50)
        pdf.set_fill_color(*ZONE_BG_COLORS["dead"])
        pdf.rect(chart_x, y50, x50 - chart_x, chart_y + chart_h - y50, style="F")

        # Compression Zone: top-left (x<50, y>=50)
        pdf.set_fill_color(*ZONE_BG_COLORS["compression"])
        pdf.rect(chart_x, chart_y, x50 - chart_x, y50 - chart_y, style="F")

        # Adaptation Zone: bottom-right (x>=50, y<50)
        pdf.set_fill_color(*ZONE_BG_COLORS["adaptation"])
        pdf.rect(x50, y50, chart_x + chart_w - x50, chart_y + chart_h - y50, style="F")

        # Fortress Zone: top-right (x>=50, y>=50)
        pdf.set_fill_color(*ZONE_BG_COLORS["fortress"])
        pdf.rect(x50, chart_y, chart_x + chart_w - x50, y50 - chart_y, style="F")

        # -- Border --
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.3)
        pdf.rect(chart_x, chart_y, chart_w, chart_h)

        # -- Dashed zone boundary lines at 50 --
        pdf.set_draw_color(190, 190, 190)
        pdf.set_line_width(0.2)
        step = 3
        # Vertical line at x=50
        pos = chart_y
        while pos < chart_y + chart_h:
            end = min(pos + step * 0.5, chart_y + chart_h)
            pdf.line(x50, pos, x50, end)
            pos += step
        # Horizontal line at y=50
        pos = chart_x
        while pos < chart_x + chart_w:
            end = min(pos + step * 0.5, chart_x + chart_w)
            pdf.line(pos, y50, end, y50)
            pos += step

        # -- Quadrant labels (watermark style, centered in each quadrant) --
        pdf.set_font("Helvetica", "B", 12)

        # Dead Zone: center of bottom-left quadrant
        pdf.set_text_color(214, 57, 57)
        dead_cx = chart_x + (x50 - chart_x) / 2
        dead_cy = y50 + (chart_y + chart_h - y50) / 2
        pdf.set_xy(dead_cx - 25, dead_cy - 5)
        pdf.cell(50, 10, "DEAD ZONE", align="C")

        # Adaptation: center of bottom-right quadrant
        pdf.set_text_color(43, 127, 212)
        adapt_cx = x50 + (chart_x + chart_w - x50) / 2
        adapt_cy = dead_cy
        pdf.set_xy(adapt_cx - 25, adapt_cy - 5)
        pdf.cell(50, 10, "ADAPTATION", align="C")

        # Compression: center of top-left quadrant
        pdf.set_text_color(212, 155, 26)
        comp_cx = dead_cx
        comp_cy = chart_y + (y50 - chart_y) / 2
        pdf.set_xy(comp_cx - 30, comp_cy - 5)
        pdf.cell(60, 10, "COMPRESSION", align="C")

        # Fortress: center of top-right quadrant
        pdf.set_text_color(26, 157, 63)
        fort_cx = adapt_cx
        fort_cy = comp_cy
        pdf.set_xy(fort_cx - 25, fort_cy - 5)
        pdf.cell(50, 10, "FORTRESS", align="C")

        # -- Axis labels --
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(chart_x, chart_y + chart_h + 6)
        pdf.cell(chart_w, 6, "Workflow Complexity  -->", align="C")

        # Y-axis label (rotated)
        with pdf.rotation(90, chart_x - 15, chart_y + chart_h / 2):
            pdf.set_xy(chart_x - 15 - 30, chart_y + chart_h / 2 - 3)
            pdf.cell(60, 6, "Data Moat Depth  -->", align="C")

        # -- Axis ticks --
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(130, 130, 130)

        pdf.set_xy(chart_x, chart_y + chart_h + 1)
        pdf.cell(10, 4, "0")
        pdf.set_xy(x50 - 5, chart_y + chart_h + 1)
        pdf.cell(10, 4, "50", align="C")
        pdf.set_xy(chart_x + chart_w - 12, chart_y + chart_h + 1)
        pdf.cell(12, 4, "100", align="R")

        pdf.set_xy(chart_x - 12, chart_y + chart_h - 5)
        pdf.cell(10, 4, "0", align="R")
        pdf.set_xy(chart_x - 12, y50 - 2)
        pdf.cell(10, 4, "50", align="R")
        pdf.set_xy(chart_x - 12, chart_y - 1)
        pdf.cell(10, 4, "100", align="R")

        # -- Plot companies with logos --
        logo_size = 7  # mm
        positions = []
        for m in members:
            x_score = m.get("x_score", 50)
            y_score = m.get("y_score", 50)
            zone = m.get("zone", "dead")
            cx = chart_x + (x_score / 100) * chart_w
            cy = chart_y + chart_h - (y_score / 100) * chart_h
            positions.append({
                "cx": cx, "cy": cy, "zone": zone,
                "name": m.get("company_name", "?"),
            })

        # Sort for label collision avoidance
        positions.sort(key=lambda p: (p["cx"], p["cy"]))

        # Pre-compute label positions — place directly under each logo
        label_h = 4

        # First pass: compute logo positions and default label Y
        pdf.set_font("Helvetica", "B", 7)
        for pos in positions:
            logo_x = pos["cx"] - logo_size / 2
            logo_y = pos["cy"] - logo_size / 2
            logo_x = max(chart_x + 1, min(logo_x, chart_x + chart_w - logo_size - 1))
            logo_y = max(chart_y + 1, min(logo_y, chart_y + chart_h - logo_size - 1))
            pos["logo_x"] = logo_x
            pos["logo_y"] = logo_y
            pos["label_y"] = logo_y + logo_size + 1  # directly under logo

            # Pre-compute label width for collision checks
            name = pos["name"]
            if len(name) > 20:
                name = name[:18] + ".."
            pos["label_w"] = pdf.get_string_width(name) + 2
            pos["label_x"] = pos["cx"] - pos["label_w"] / 2

        # Second pass: resolve overlaps only for labels that truly collide
        for i, pos in enumerate(positions):
            for j in range(i):
                prev = positions[j]
                # Check actual bounding-box overlap
                h_overlap = not (pos["label_x"] + pos["label_w"] < prev["label_x"] or
                                 prev["label_x"] + prev["label_w"] < pos["label_x"])
                v_overlap = not (pos["label_y"] + label_h < prev["label_y"] or
                                 prev["label_y"] + label_h < pos["label_y"])
                if h_overlap and v_overlap:
                    # Push this label below the previous one
                    pos["label_y"] = max(pos["label_y"], prev["label_y"] + label_h + 1)

            pos["label_y"] = min(pos["label_y"], chart_y + chart_h - label_h)

        # Draw logos and labels
        for pos in positions:
            color = ZONE_COLORS.get(pos["zone"], (150, 150, 150))
            name = pos["name"]
            logo = _logo_url(name)

            try:
                pdf.image(logo, x=pos["logo_x"], y=pos["logo_y"], w=logo_size, h=logo_size)
            except Exception:
                # Fallback to colored circle if logo fetch fails
                r = logo_size / 2
                pdf.set_fill_color(*color)
                pdf.set_draw_color(*color)
                pdf.set_line_width(0.5)
                pdf.circle(pos["cx"] - r, pos["cy"] - r, r, style="FD")

            # Label centered under the logo
            if len(name) > 20:
                name = name[:18] + ".."
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(50, 50, 50)
            label_w = pdf.get_string_width(name) + 2
            label_x = pos["cx"] - label_w / 2
            label_x = max(chart_x + 1, min(label_x, chart_x + chart_w - label_w - 1))

            pdf.set_xy(label_x, pos["label_y"])
            pdf.cell(label_w, label_h, name, align="C")

        pdf.set_line_width(0.2)  # Reset

        # Re-enable auto page break for subsequent pages
        pdf.set_auto_page_break(auto=True, margin=25)

    # -- Company Detail Pages --------------------------------------------------

    def _render_company_details(self, pdf: CohortReportPDF, evaluations: list[dict]):
        sorted_evals = sorted(evaluations, key=lambda e: ZONE_ORDER.get(e.get("zone", ""), 99))

        for ev in sorted_evals:
            pdf.add_page("P")

            zone = ev.get("zone", "unknown")
            color = ZONE_COLORS.get(zone, (100, 100, 100))
            bg_color = ZONE_BG_COLORS.get(zone, (240, 240, 240))
            zone_label = ZONE_LABELS.get(zone, zone.title())

            # Company name
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_text_color(45, 43, 41)
            pdf.cell(0, 12, ev.get("company_name", "Unknown"), new_x="LMARGIN", new_y="NEXT")

            # Zone badge
            pdf.set_font("Helvetica", "B", 10)
            badge_w = pdf.get_string_width(zone_label) + 10
            pdf.set_fill_color(*bg_color)
            pdf.set_text_color(*color)
            pdf.cell(badge_w, 8, zone_label, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

            # -- Score cards side by side --
            x_score = int(ev.get("x_score", 0))
            y_score = int(ev.get("y_score", 0))
            card_w = 88
            card_h = 18
            bar_h = 4
            margin = pdf.l_margin

            # Pin Y position
            cards_y = pdf.get_y()

            for idx, (label, score) in enumerate([
                ("Workflow Complexity", x_score),
                ("Data Moat Depth", y_score),
            ]):
                card_x = margin + idx * (card_w + 6)
                bar_color = _score_color_100(score)

                # Card background
                pdf.set_fill_color(245, 243, 240)
                pdf.rect(card_x, cards_y, card_w, card_h, style="F")

                # Label
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(130, 130, 130)
                pdf.set_xy(card_x + 4, cards_y + 2)
                pdf.cell(50, 4, label)

                # Score
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(45, 43, 41)
                pdf.set_xy(card_x + 4, cards_y + 6)
                pdf.cell(20, 6, str(score))
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(130, 130, 130)
                pdf.cell(10, 6, "/100")

                # Bar with gradient color
                bar_x = card_x + 4
                bar_y_pos = cards_y + card_h - bar_h - 2
                bar_w = card_w - 8
                pdf.set_fill_color(230, 230, 230)
                pdf.rect(bar_x, bar_y_pos, bar_w, bar_h, style="F")
                pdf.set_fill_color(*bar_color)
                pdf.rect(bar_x, bar_y_pos, bar_w * (score / 100), bar_h, style="F")

            pdf.set_y(cards_y + card_h + 6)

            # -- Score factor breakdowns with spider charts --
            score_factors = ev.get("score_factors")
            if score_factors:
                self._render_factor_section(pdf, score_factors)
                pdf.ln(3)

            # -- Overview --
            overview = ev.get("overview", "")
            if overview:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(45, 43, 41)
                pdf.cell(0, 7, "Overview", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 4.5, overview)
                pdf.ln(3)

            # -- Justification --
            justification = ev.get("justification", "")
            if justification:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(45, 43, 41)
                pdf.cell(0, 7, "Justification", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 4.5, justification)
                pdf.ln(3)

            # -- Diligence --
            diligence = ev.get("diligence", [])
            if diligence:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(45, 43, 41)
                pdf.cell(0, 7, "Diligence Checklist", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                for i, item in enumerate(diligence, 1):
                    pdf.set_x(pdf.l_margin)
                    pdf.cell(8, 5, f"{i}.", align="R")
                    pdf.multi_cell(0, 5, str(item))
                    pdf.ln(0.5)

    # -- Factor Section (bars + spider charts side by side) --------------------

    def _render_factor_section(self, pdf: CohortReportPDF, score_factors: dict):
        """Render bar charts on the left, spider charts on the right for each axis."""
        x_factors = score_factors.get("x_factors", {})
        y_factors = score_factors.get("y_factors", {})

        bar_max_w = 50
        label_w = 38
        value_w = 12
        bar_h = 4
        row_h = 6

        # Spider chart dimensions
        spider_radius = 20
        spider_w = spider_radius * 2 + 50  # space for full labels

        # Total left section width (bars)
        bars_section_w = label_w + 3 + bar_max_w + 2 + value_w

        for section_label, factors, factor_labels in [
            ("COMPLEXITY BREAKDOWN", x_factors, X_FACTOR_LABELS),
            ("DATA MOAT BREAKDOWN", y_factors, Y_FACTOR_LABELS),
        ]:
            if not factors:
                continue

            section_y = pdf.get_y()

            # Section header
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(110, 110, 110)
            pdf.cell(0, 6, section_label, new_x="LMARGIN", new_y="NEXT")

            bars_start_y = pdf.get_y()

            # Draw bars on the left
            for i, (key, label) in enumerate(factor_labels):
                val = max(0, min(20, factors.get(key, 0)))
                bar_color = _score_color(val, 20)
                y = pdf.get_y()

                # Label
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(120, 120, 120)
                pdf.cell(label_w, row_h, label, align="R")
                pdf.cell(3, row_h, "")

                # Bar background
                bar_x = pdf.get_x()
                bar_y = y + (row_h - bar_h) / 2
                pdf.set_fill_color(230, 230, 230)
                pdf.rect(bar_x, bar_y, bar_max_w, bar_h, style="F")

                # Bar fill with gradient color (clamp to max width)
                fill_w = min(bar_max_w, bar_max_w * (val / 20))
                if fill_w > 0:
                    pdf.set_fill_color(*bar_color)
                    pdf.rect(bar_x, bar_y, fill_w, bar_h, style="F")

                # Value
                pdf.set_x(bar_x + bar_max_w + 2)
                pdf.set_font("Helvetica", "B", 7.5)
                pdf.set_text_color(*bar_color)
                pdf.cell(value_w, row_h, f"{int(val)}/20", align="L")

                pdf.ln()

            bars_end_y = pdf.get_y()

            # Draw spider chart on the right
            spider_cx = pdf.w - pdf.r_margin - spider_radius - 12
            spider_cy = bars_start_y + (bars_end_y - bars_start_y) / 2
            n = len(factor_labels)
            vals = [max(0, min(20, factors.get(k, 0))) for k, _ in factor_labels]
            spider_labels = [lbl for _, lbl in factor_labels]

            self._draw_spider(pdf, spider_cx, spider_cy, spider_radius, vals, 20, spider_labels)

            # Move Y to the end of whichever is taller
            pdf.set_y(max(bars_end_y, spider_cy + spider_radius + 10))
            pdf.ln(2)

    # -- Spider Chart Drawing --------------------------------------------------

    def _draw_spider(self, pdf: CohortReportPDF, cx: float, cy: float, radius: float,
                     values: list[int], max_val: int, labels: list[str]):
        """Draw a radar/spider chart centered at (cx, cy)."""
        n = len(values)
        if n < 3:
            return

        # Grid rings
        for ring_frac in [0.25, 0.5, 0.75, 1.0]:
            ring_pts = []
            for i in range(n):
                angle = (2 * math.pi * i / n) - math.pi / 2
                ring_pts.append((
                    cx + radius * ring_frac * math.cos(angle),
                    cy + radius * ring_frac * math.sin(angle),
                ))
            pdf.set_draw_color(215, 215, 215)
            pdf.set_line_width(0.1)
            pdf.polygon(ring_pts, style="D")

        # Axis lines
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.1)
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            pdf.line(cx, cy, cx + radius * math.cos(angle), cy + radius * math.sin(angle))

        # Value polygon (filled with light color)
        value_pts = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            v = min(values[i] / max_val, 1.0)
            value_pts.append((
                cx + radius * v * math.cos(angle),
                cy + radius * v * math.sin(angle),
            ))

        # Determine fill color based on average score
        avg_val = sum(values) / len(values) if values else 0
        fill_color = _score_color(int(avg_val), max_val)
        light_fill = (
            min(255, fill_color[0] + (255 - fill_color[0]) * 2 // 3),
            min(255, fill_color[1] + (255 - fill_color[1]) * 2 // 3),
            min(255, fill_color[2] + (255 - fill_color[2]) * 2 // 3),
        )

        pdf.set_fill_color(*light_fill)
        pdf.set_draw_color(*fill_color)
        pdf.set_line_width(0.6)
        pdf.polygon(value_pts, style="DF")

        # Dots on vertices
        for pt in value_pts:
            pdf.set_fill_color(*fill_color)
            pdf.circle(pt[0] - 1, pt[1] - 1, 1, style="F")

        # Axis labels — two-line labels for side vertices, centered for top/bottom
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(80, 80, 80)
        line_h = 3.2
        for i in range(n):
            angle = (2 * math.pi * i / n) - math.pi / 2
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            offset = radius + 4
            lx = cx + offset * cos_a
            ly = cy + offset * sin_a
            lbl = labels[i]

            # Split label into two lines for side vertices
            # Split on space first, then try hyphen for words like "Multi-Stakeholder"
            if " " in lbl:
                words = lbl.split(" ")
            elif "-" in lbl:
                parts = lbl.split("-")
                words = [parts[0] + "-", parts[1]]
            else:
                words = [lbl]
            if len(words) >= 2 and abs(cos_a) > 0.2:
                line1 = words[0]
                line2 = " ".join(words[1:])
            else:
                line1 = lbl
                line2 = ""

            lw1 = pdf.get_string_width(line1) + 1
            lw2 = pdf.get_string_width(line2) + 1 if line2 else 0
            max_lw = max(lw1, lw2)

            if cos_a > 0.2:
                # Right side — left-align from vertex point
                lbl_x = lx + 1
                lbl_y = ly - (line_h if line2 else line_h / 2)
                pdf.set_xy(lbl_x, lbl_y)
                pdf.cell(lw1, line_h, line1, align="L")
                if line2:
                    pdf.set_xy(lbl_x, lbl_y + line_h)
                    pdf.cell(lw2, line_h, line2, align="L")
            elif cos_a < -0.2:
                # Left side — right-align to vertex point
                lbl_x = lx - max_lw - 1
                lbl_y = ly - (line_h if line2 else line_h / 2)
                pdf.set_xy(lbl_x, lbl_y)
                pdf.cell(max_lw, line_h, line1, align="R")
                if line2:
                    pdf.set_xy(lbl_x, lbl_y + line_h)
                    pdf.cell(max_lw, line_h, line2, align="R")
            else:
                # Top or bottom — center horizontally
                lbl_x = lx - lw1 / 2
                if sin_a < 0:
                    lbl_y = ly - 0.5
                else:
                    lbl_y = ly + 2  # below
                pdf.set_xy(lbl_x, lbl_y)
                pdf.cell(lw1, line_h, line1, align="C")
                if line2:
                    pdf.set_xy(lx - lw2 / 2, lbl_y + line_h)
                    pdf.cell(lw2, line_h, line2, align="C")

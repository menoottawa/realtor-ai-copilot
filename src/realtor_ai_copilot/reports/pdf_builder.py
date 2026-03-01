"""Build a client-ready PDF report from scored and analysed match results."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Union

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from realtor_ai_copilot.models import BuyerProfile, MatchResult

# ── Brand colours ──────────────────────────────────────────────────────────────
_NAVY = colors.HexColor("#1B3A6B")
_GOLD = colors.HexColor("#C9A84C")
_LIGHT_GRAY = colors.HexColor("#F4F4F4")
_MID_GRAY = colors.HexColor("#888888")
_GREEN = colors.HexColor("#2E7D32")
_AMBER = colors.HexColor("#E65100")
_RED = colors.HexColor("#B71C1C")


def _score_colour(score: float) -> colors.Color:
    if score >= 75:
        return _GREEN
    if score >= 50:
        return _AMBER
    return _RED


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontSize=26,
        textColor=_NAVY,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontSize=13,
        textColor=_MID_GRAY,
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    styles["section_header"] = ParagraphStyle(
        "section_header",
        parent=base["Heading2"],
        fontSize=14,
        textColor=_NAVY,
        spaceBefore=14,
        spaceAfter=4,
    )
    styles["listing_title"] = ParagraphStyle(
        "listing_title",
        parent=base["Heading3"],
        fontSize=12,
        textColor=_NAVY,
        spaceAfter=2,
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        parent=base["Normal"],
        fontSize=9,
        leading=13,
        leftIndent=14,
        bulletIndent=0,
        bulletFontSize=9,
    )
    styles["caption"] = ParagraphStyle(
        "caption",
        parent=base["Normal"],
        fontSize=8,
        textColor=_MID_GRAY,
        alignment=TA_LEFT,
    )
    styles["score_big"] = ParagraphStyle(
        "score_big",
        parent=base["Normal"],
        fontSize=28,
        alignment=TA_CENTER,
    )
    return styles


def _cover_page(
    story: list,
    styles: dict[str, ParagraphStyle],
    profile: BuyerProfile,
    results: list[MatchResult],
) -> None:
    """Append cover-page elements to *story*."""
    story.append(Spacer(1, 1.0 * inch))
    story.append(Paragraph("Real Estate Research Packet", styles["title"]))
    story.append(Paragraph(f"Prepared for: <b>{profile.name}</b>", styles["subtitle"]))
    story.append(Paragraph(f"Date: {date.today().strftime('%B %d, %Y')}", styles["subtitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=2, color=_GOLD))
    story.append(Spacer(1, 0.3 * inch))

    # Summary stats
    top_score = results[0].score if results else 0.0
    data = [
        ["Listings Reviewed", "Top Match Score", "Budget"],
        [
            str(len(results)),
            f"{top_score:.0f}/100",
            f"${profile.max_price:,.0f}",
        ],
    ]
    tbl = Table(data, colWidths=[2.0 * inch, 2.0 * inch, 2.0 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_GRAY, colors.white]),
                ("FONTSIZE", (0, 1), (-1, -1), 14),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, _MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, _MID_GRAY),
            ]
        )
    )
    story.append(tbl)

    # Buyer criteria summary
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Buyer Search Criteria", styles["section_header"]))
    criteria = [
        ("Max Price", f"${profile.max_price:,.0f}"),
        ("Min Bedrooms", str(profile.min_bedrooms)),
        ("Min Bathrooms", str(profile.min_bathrooms)),
    ]
    if profile.min_sqft:
        criteria.append(("Min Sqft", f"{profile.min_sqft:,.0f}"))
    if profile.preferred_cities:
        criteria.append(("Preferred Cities", ", ".join(profile.preferred_cities)))
    if profile.preferred_property_types:
        criteria.append(("Property Types", ", ".join(profile.preferred_property_types)))
    if profile.notes:
        criteria.append(("Notes", profile.notes))

    crit_data = [["Criterion", "Value"]] + criteria
    crit_tbl = Table(crit_data, colWidths=[2.5 * inch, 4.0 * inch])
    crit_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_LIGHT_GRAY, colors.white]),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.5, _MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, _MID_GRAY),
            ]
        )
    )
    story.append(crit_tbl)
    story.append(PageBreak())


def _listing_page(
    story: list,
    styles: dict[str, ParagraphStyle],
    rank: int,
    result: MatchResult,
) -> None:
    """Append a listing detail page to *story*."""
    listing = result.listing
    score_col = _score_colour(result.score)

    story.append(
        Paragraph(
            f"#{rank} — {listing.full_address}",
            styles["section_header"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=_GOLD))
    story.append(Spacer(1, 0.15 * inch))

    # Key facts table
    facts = [
        ["MLS ID", listing.mls_id, "Price", f"${listing.price:,.0f}"],
        ["Bedrooms", str(listing.bedrooms), "Bathrooms", str(listing.bathrooms)],
        [
            "Sqft",
            f"{listing.sqft:,.0f}" if listing.sqft else "N/A",
            "Year Built",
            str(listing.year_built) if listing.year_built else "N/A",
        ],
        [
            "Type",
            listing.property_type,
            "$/sqft",
            f"${listing.price_per_sqft:,.0f}" if listing.price_per_sqft else "N/A",
        ],
    ]
    facts_tbl = Table(facts, colWidths=[1.2 * inch, 2.0 * inch, 1.2 * inch, 2.1 * inch])
    facts_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_LIGHT_GRAY, colors.white]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.5, _MID_GRAY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, _MID_GRAY),
            ]
        )
    )
    story.append(facts_tbl)
    story.append(Spacer(1, 0.15 * inch))

    # Match score badge
    score_para = Paragraph(
        f'<font color="{score_col.hexval()}" size="22"><b>{result.score:.0f}</b></font>'
        f'<font color="{_MID_GRAY.hexval()}" size="12">/100</font>  '
        f'<font color="{_MID_GRAY.hexval()}" size="10">Match Score</font>',
        styles["body"],
    )
    story.append(score_para)
    story.append(Spacer(1, 0.1 * inch))

    # Highlights
    if result.highlights:
        story.append(Paragraph("✓ Highlights", styles["listing_title"]))
        for h in result.highlights:
            story.append(Paragraph(f"• {h}", styles["bullet"]))
        story.append(Spacer(1, 0.1 * inch))

    # Concerns
    if result.concerns:
        story.append(Paragraph("⚠ Concerns", styles["listing_title"]))
        for c in result.concerns:
            story.append(Paragraph(f"• {c}", styles["bullet"]))
        story.append(Spacer(1, 0.1 * inch))

    # AI analysis
    if result.analysis:
        story.append(Paragraph("Agent Analysis", styles["listing_title"]))
        # Split into paragraphs on blank lines / newlines
        for para_text in result.analysis.split("\n\n"):
            para_text = para_text.strip()
            if para_text:
                story.append(Paragraph(para_text.replace("\n", " "), styles["body"]))
                story.append(Spacer(1, 0.08 * inch))

    # Optional listing URL
    if listing.listing_url:
        story.append(
            Paragraph(
                f'<link href="{listing.listing_url}">View on MLS →</link>',
                styles["caption"],
            )
        )

    story.append(PageBreak())


def build_report(
    results: list[MatchResult],
    profile: BuyerProfile,
    output_path: Union[str, Path],
) -> Path:
    """Render a client-ready PDF report.

    Parameters
    ----------
    results:
        Scored (and optionally analysed) match results, pre-sorted by score.
    profile:
        The buyer's profile used for the header and criteria summary.
    output_path:
        Where to write the PDF.

    Returns
    -------
    Path
        Absolute path to the written PDF file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"Real Estate Report — {profile.name}",
        author="Realtor AI Copilot",
    )

    styles = _build_styles()
    story: list = []

    _cover_page(story, styles, profile, results)

    for rank, result in enumerate(results, start=1):
        _listing_page(story, styles, rank, result)

    doc.build(story)
    return output_path.resolve()

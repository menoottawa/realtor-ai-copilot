"""Tests for the PDF report builder."""

from __future__ import annotations

from pathlib import Path

import pytest

from realtor_ai_copilot.models import BuyerProfile, Listing, MatchResult
from realtor_ai_copilot.reports.pdf_builder import build_report


def make_result(rank: int = 1, score: float = 85.0) -> MatchResult:
    listing = Listing(
        mls_id=f"PDF-{rank:02d}",
        address=f"{rank * 100} Test Street",
        city="Ottawa",
        state="ON",
        zip_code="K1A 0A1",
        price=525000,
        bedrooms=3,
        bathrooms=2,
        sqft=1800,
        year_built=2005,
        property_type="Single Family",
        description="A great home for the whole family.",
        listing_url=f"https://example.com/mls/{rank}",
    )
    return MatchResult(
        listing=listing,
        score=score,
        highlights=["Price fits budget", "3 bedrooms meets requirement"],
        concerns=["Only 2 bathrooms" if rank % 2 == 0 else ""],
        analysis=(
            "This is a strong match for the buyer's criteria.\n\n"
            "The location is excellent with good schools nearby.\n\n"
            "Recommendation: Schedule a showing soon."
        ),
    )


@pytest.fixture()
def sample_profile() -> BuyerProfile:
    return BuyerProfile(
        name="Alex & Jordan Chen",
        email="alex@example.com",
        max_price=600000,
        min_bedrooms=3,
        min_bathrooms=2,
        min_sqft=1600,
        preferred_cities=["Ottawa", "Kanata"],
        preferred_property_types=["Single Family"],
        notes="Two kids, need good schools.",
    )


class TestBuildReport:
    def test_creates_pdf_file(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        results = [make_result(i, score=90.0 - i * 5) for i in range(1, 4)]
        out = tmp_path / "report.pdf"
        written = build_report(results, sample_profile, out)
        assert written.exists()
        assert written.suffix == ".pdf"
        assert written.stat().st_size > 0

    def test_creates_parent_directories(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        results = [make_result()]
        out = tmp_path / "deep" / "nested" / "report.pdf"
        written = build_report(results, sample_profile, out)
        assert written.exists()

    def test_pdf_starts_with_pdf_header(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        results = [make_result()]
        out = tmp_path / "header_test.pdf"
        written = build_report(results, sample_profile, out)
        with written.open("rb") as fh:
            header = fh.read(4)
        assert header == b"%PDF"

    def test_returns_absolute_path(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        results = [make_result()]
        out = tmp_path / "abs_test.pdf"
        written = build_report(results, sample_profile, out)
        assert written.is_absolute()

    def test_empty_results_still_builds(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        """Report with no listings should still produce a valid (cover-only) PDF."""
        out = tmp_path / "empty.pdf"
        written = build_report([], sample_profile, out)
        assert written.exists()
        assert written.stat().st_size > 0

    def test_result_without_analysis(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        """Results without analysis text should render without errors."""
        result = make_result()
        result = result.model_copy(update={"analysis": None})
        out = tmp_path / "no_analysis.pdf"
        written = build_report([result], sample_profile, out)
        assert written.exists()

    def test_multiple_listings(self, tmp_path: Path, sample_profile: BuyerProfile) -> None:
        results = [make_result(i, score=float(100 - i * 3)) for i in range(1, 11)]
        out = tmp_path / "multi.pdf"
        written = build_report(results, sample_profile, out)
        assert written.exists()
        # Multi-listing PDF should be substantially larger
        assert written.stat().st_size > 5000

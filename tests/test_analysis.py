"""Tests for the AI analysis generator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from realtor_ai_copilot.analysis.generator import generate_analyses, generate_analysis
from realtor_ai_copilot.models import BuyerProfile, Listing, MatchResult


def make_result(score: float = 80.0, highlights=None, concerns=None) -> MatchResult:
    listing = Listing(
        mls_id="A1",
        address="1 Test St",
        city="Ottawa",
        state="ON",
        zip_code="K1A",
        price=500000,
        bedrooms=3,
        bathrooms=2,
        sqft=1800,
        property_type="Single Family",
        description="A lovely home.",
    )
    return MatchResult(
        listing=listing,
        score=score,
        highlights=highlights or ["Price fits budget"],
        concerns=concerns or [],
    )


def make_profile() -> BuyerProfile:
    return BuyerProfile(
        name="Test Buyer",
        max_price=600000,
        min_bedrooms=3,
        notes="Near schools please.",
    )


class TestFallbackAnalysis:
    """Ensure rule-based fallback works without an API key."""

    def test_returns_string(self) -> None:
        result = make_result()
        profile = make_profile()
        analysis = generate_analysis(result, profile, api_key="")
        assert isinstance(analysis, str)
        assert len(analysis) > 50

    def test_high_score_recommendation(self) -> None:
        result = make_result(score=85.0)
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "Strong match" in analysis or "recommend" in analysis.lower()

    def test_mid_score_recommendation(self) -> None:
        result = make_result(score=60.0)
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "Moderate" in analysis or "closer look" in analysis.lower()

    def test_low_score_recommendation(self) -> None:
        result = make_result(score=30.0)
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "Below threshold" in analysis or "deprioritising" in analysis.lower()

    def test_highlights_in_output(self) -> None:
        result = make_result(highlights=["Great location", "Good price"])
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "Great location" in analysis or "Strengths" in analysis

    def test_concerns_in_output(self) -> None:
        result = make_result(concerns=["Only 2 beds"])
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "Only 2 beds" in analysis or "concern" in analysis.lower()

    def test_price_per_sqft_in_output(self) -> None:
        result = make_result()  # listing has sqft=1800, price=500000
        analysis = generate_analysis(result, make_profile(), api_key="")
        assert "sqft" in analysis.lower() or "/" in analysis


class TestOpenAIPath:
    """Verify the OpenAI path is invoked and output returned."""

    def test_openai_called_when_key_provided(self) -> None:
        result = make_result()
        profile = make_profile()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "AI-generated analysis text."

        with patch("openai.OpenAI") as MockOpenAI:
            client = MagicMock()
            client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = client

            analysis = generate_analysis(result, profile, api_key="sk-test")

        assert analysis == "AI-generated analysis text."
        MockOpenAI.assert_called_once_with(api_key="sk-test")

    def test_falls_back_on_openai_exception(self) -> None:
        result = make_result()
        profile = make_profile()

        with patch("openai.OpenAI") as MockOpenAI:
            client = MagicMock()
            client.chat.completions.create.side_effect = Exception("API error")
            MockOpenAI.return_value = client

            analysis = generate_analysis(result, profile, api_key="sk-test")

        # Should have fallen back to rule-based
        assert "Recommendation:" in analysis


class TestGenerateAnalyses:
    def test_populates_all_results(self) -> None:
        results = [make_result(score=s) for s in [90.0, 70.0, 40.0]]
        profile = make_profile()
        generate_analyses(results, profile, api_key="")
        assert all(r.analysis is not None for r in results)
        assert all(len(r.analysis) > 0 for r in results)  # type: ignore[arg-type]

    def test_returns_same_list(self) -> None:
        results = [make_result()]
        profile = make_profile()
        returned = generate_analyses(results, profile, api_key="")
        assert returned is results

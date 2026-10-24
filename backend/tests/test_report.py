"""Tests for Part 3 (the reporter)."""
import pytest

from app.fetch import load_prefilled
from app.report import build_report
from app.schema import SiteData
from app.score import score


class TestReportContent:
    @pytest.mark.parametrize("name", ["forested", "suburban", "developed"])
    def test_builds_for_all_datasets(self, name):
        d = load_prefilled(name)
        md = build_report(d)
        assert isinstance(md, str) and len(md) > 500

    def test_contains_all_sections(self):
        md = build_report(load_prefilled("forested"))
        for heading in [
            "Environmental Impact Report",
            "Habitat Integrity",
            "Keystone Species Impact",
            "Connectivity",
            "Carbon & Climate",
            "Land Reuse",
            "Regulatory Risk",
            "Combining the Sub-scores",
            "Regulatory Hard Gate",
            "Data-Confidence Adjustment",
            "Recommended Mitigation",
            "Methodology & Limitations",
        ]:
            assert heading in md, f"missing section: {heading}"

    def test_shows_the_final_rating(self):
        d = load_prefilled("forested")
        r = score(d)
        md = build_report(d, r)
        # The computed final rating should appear verbatim in the report.
        assert f"{r.e_final:.1f}" in md
        assert r.grade in md

    def test_arithmetic_matches_computed_subscores(self):
        # Each sub-score value the scorer computed should appear in the report,
        # so the shown arithmetic is anchored to the real numbers.
        d = load_prefilled("suburban")
        r = score(d)
        md = build_report(d, r)
        for key, val in r.subscores.items():
            assert f"{val:.1f}" in md, f"{key}={val:.1f} not shown in report"

    def test_hard_gate_narrative_when_fired(self):
        # A protected-habitat hard trigger should produce the cap narrative.
        d = load_prefilled("forested")
        d.hard_triggers = {"protected_open_space": True}
        r = score(d)
        md = build_report(d, r)
        assert "capped at" in md
        assert "regulatory review likely" in md

    def test_no_gate_narrative_when_clear(self):
        d = load_prefilled("developed")  # no hard triggers
        md = build_report(d)
        assert "no cap was applied" in md

    def test_excluded_species_marked(self):
        # Developed site: beaver is implausible -> shown as excluded.
        md = build_report(load_prefilled("developed"))
        assert "no (excluded)" in md

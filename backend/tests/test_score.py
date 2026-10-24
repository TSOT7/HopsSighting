"""Tests for Part 2 (the scorer) and the schema round-trip."""
import math

import pytest

from app import config
from app.schema import SiteData, SpeciesRecord, validate
from app.score import (
    data_confidence,
    decay,
    geo,
    grade_for,
    lin,
    logis,
    s_habitat,
    s_keystone,
    s_landreuse,
    s_regulatory,
    score,
    species_risks,
)


# --- helpers --------------------------------------------------------------
class TestHelpers:
    def test_lin_bounds(self):
        assert lin(0, 0, 100) == 0
        assert lin(100, 0, 100) == 100
        assert lin(50, 0, 100) == 50

    def test_decay(self):
        assert decay(0, 800) == 100
        assert decay(800, 800) == pytest.approx(100 * math.exp(-1))

    def test_logis_midpoint(self):
        assert logis(0, 0, 1) == pytest.approx(50)

    def test_geo_floor(self):
        # A zero floors to 1, so the group stays > 0.
        assert geo([0, 80, 80]) > 0
        assert geo([0, 80, 80]) == pytest.approx((1 * 80 * 80) ** (1 / 3))


# --- schema ---------------------------------------------------------------
class TestSchema:
    def test_round_trip(self, tmp_path):
        d = SiteData(lat=42.0, lon=-71.0, frac_forest=0.5,
                     species=[SpeciesRecord("beaver", 3)])
        p = tmp_path / "s.json"
        d.save(p)
        back = SiteData.load(p)
        assert back.lat == 42.0
        assert back.frac_forest == 0.5
        assert back.species[0].name == "beaver"
        assert back.species[0].sightings_count == 3

    def test_validate_good(self):
        assert validate(SiteData(lat=42, lon=-71)) == []

    def test_validate_bad_lat(self):
        assert any("lat" in p for p in validate(SiteData(lat=999, lon=-71)))

    def test_validate_bad_fraction(self):
        assert any("frac_forest" in p for p in validate(SiteData(lat=42, lon=-71, frac_forest=5)))

    def test_validate_unknown_trigger(self):
        d = SiteData(lat=42, lon=-71, triggers={"nope": True})
        assert any("unknown trigger" in p for p in validate(d))


# --- sub-scores -----------------------------------------------------------
class TestSubScores:
    def test_habitat_empty_is_100(self):
        assert s_habitat(SiteData(lat=42, lon=-71)) == 100

    def test_habitat_full_wetland(self):
        s = s_habitat(SiteData(lat=42, lon=-71, frac_wetland=1.0))
        assert s == pytest.approx(100 * (1 - config.HABITAT_WEIGHTS["wetland"]))

    def test_regulatory_no_triggers(self):
        assert s_regulatory(SiteData(lat=42, lon=-71)) == 100

    def test_regulatory_protected_zeroes(self):
        d = SiteData(lat=42, lon=-71, triggers={"protected_open_space": True})
        assert s_regulatory(d) == 0

    def test_landreuse_brownfield(self):
        d = SiteData(lat=42, lon=-71, is_brownfield=True)
        assert s_landreuse(d) == pytest.approx(100 * config.LAND_REUSE_WEIGHTS["brownfield"])


# --- species --------------------------------------------------------------
class TestSpecies:
    def test_beaver_dry_not_applicable(self):
        d = SiteData(lat=42, lon=-71, stream_distance_m=9999, water_distance_m=9999)
        risks = {r.name: r for r in species_risks(d)}
        assert not risks["beaver"].applicable

    def test_higher_risk_lowers_sk(self):
        hi = SiteData(lat=42, lon=-71, frac_forest=0.7, frac_wetland=0.3,
                      stream_distance_m=20, water_distance_m=20, mean_slope_deg=2,
                      mature_canopy_frac=0.8, forest_patch_area_m2=1_000_000,
                      frac_open_land=0.5)
        lo = SiteData(lat=42, lon=-71, frac_forest=0.3, stream_distance_m=800,
                      mean_slope_deg=15, mature_canopy_frac=0.1,
                      forest_patch_area_m2=50_000, frac_open_land=0.05)
        assert s_keystone(species_risks(hi)) < s_keystone(species_risks(lo))


# --- confidence + grade ---------------------------------------------------
class TestConfidenceAndGrade:
    def test_full_confidence(self):
        d = SiteData(lat=42, lon=-71, n_all_records=config.N_REF_RECORDS,
                     nlcd_confidence=1.0, mean_location_uncertainty_m=0.0)
        assert data_confidence(d) == pytest.approx(100)

    def test_unavailable_layers_penalize(self):
        d = SiteData(lat=42, lon=-71, n_all_records=config.N_REF_RECORDS,
                     nlcd_confidence=1.0, mean_location_uncertainty_m=0.0,
                     layer_available={"a": True, "b": False})
        assert data_confidence(d) == pytest.approx(50)

    def test_grade_bands(self):
        assert grade_for(90)[0] == "A"
        assert grade_for(75)[0] == "B"
        assert grade_for(60)[0] == "C"
        assert grade_for(45)[0] == "D"
        assert grade_for(10)[0] == "F"


# --- full pipeline on the prefilled datasets -----------------------------
class TestPrefilledDatasets:
    @pytest.mark.parametrize("name", ["forested", "suburban", "developed"])
    def test_scores_in_range(self, name):
        from app.fetch import load_prefilled
        d = load_prefilled(name)
        r = score(d)
        assert 0 <= r.e_final <= 100
        assert r.grade in {"A", "B", "C", "D", "F"}

    def test_impact_ordering(self):
        from app.fetch import load_prefilled
        dev = score(load_prefilled("developed")).e_final
        sub = score(load_prefilled("suburban")).e_final
        forest = score(load_prefilled("forested")).e_final
        # Developed brownfield should rate better than clearing forest.
        assert dev > sub > forest

    def test_thin_data_pulls_toward_prior(self):
        d = SiteData(lat=42, lon=-71, frac_impervious=0.9, frac_developed=0.9,
                     n_all_records=3, nlcd_confidence=0.5,
                     mean_location_uncertainty_m=800)
        r = score(d)
        assert abs(r.e_final - config.CONSERVATIVE_PRIOR) < abs(
            r.e_gated - config.CONSERVATIVE_PRIOR)

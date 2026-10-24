"""Part 2: the scorer.

Reads a site-data JSON file (written by fetch.py), runs every formula
from docs/scoring-model.md, and prints / returns the rating, grade,
sub-scores, species breakdown, flags and mitigation.

Pure Python + stdlib only; no GIS libraries. Run it standalone:

    python -m app.score datasets/forested.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .schema import SiteData, SpeciesRecord, validate

# --------------------------------------------------------------------------
# Helper curves
# --------------------------------------------------------------------------
GEO_FLOOR = 1.0


def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def lin(x: float, a: float, b: float) -> float:
    if a == b:
        return 100.0 if x >= a else 0.0
    return 100.0 * clip((x - a) / (b - a), 0.0, 1.0)


def decay(d: float, d0: float) -> float:
    if d0 <= 0:
        raise ValueError("d0 must be positive")
    return 100.0 * math.exp(-d / d0)


def logis(x: float, x0: float, k: float) -> float:
    z = -k * (x - x0)
    if z > 700:
        return 0.0
    return 100.0 / (1.0 + math.exp(z))


def geo(values: list[float], weights: list[float] | None = None) -> float:
    if not values:
        raise ValueError("geo needs at least one value")
    n = len(values)
    if weights is None:
        weights = [1.0 / n] * n
    else:
        total = sum(weights)
        if total <= 0:
            raise ValueError("weights must sum to a positive number")
        weights = [w / total for w in weights]
    log_sum = sum(w * math.log(max(v, GEO_FLOOR)) for v, w in zip(values, weights))
    return math.exp(log_sum)


def _clamp(x: float) -> float:
    return clip(x, 0.0, 100.0)


# --------------------------------------------------------------------------
# Species risk (produces risk 0-1 per species, + applicability)
# --------------------------------------------------------------------------
@dataclass
class SpeciesRisk:
    name: str
    risk: float
    reason: str
    confidence: str
    applicable: bool = True


def _confidence(count: int) -> str:
    if count >= 10:
        return "high"
    if count >= 3:
        return "medium"
    return "low"


def _beaver_risk(d: SiteData, sightings: int) -> SpeciesRisk:
    water_near = min(d.stream_distance_m, d.water_distance_m) < 1000.0
    if not water_near and sightings == 0:
        return SpeciesRisk("beaver", 0.0,
                           "No stream or wetland nearby; beaver habitat implausible.",
                           "low", applicable=False)
    stream = decay(d.stream_distance_m, 150.0) / 100.0
    wetland = clip(d.frac_wetland * 2.0, 0.0, 1.0)
    slope = clip((20.0 - d.mean_slope_deg) / (20.0 - 5.0), 0.0, 1.0)
    trees = clip(d.frac_forest, 0.0, 1.0)
    risk = clip(0.40 * stream + 0.25 * wetland + 0.20 * slope + 0.15 * trees, 0.0, 1.0)
    bits = []
    if stream > 0.3:
        bits.append("low-gradient stream corridor")
    if wetland > 0.2:
        bits.append("adjacent wetland")
    if trees > 0.3:
        bits.append("nearby trees")
    reason = ("Site overlaps " + ", ".join(bits) + ".") if bits else "Limited beaver habitat."
    return SpeciesRisk("beaver", risk, reason, _confidence(sightings))


def _bats_risk(d: SiteData, sightings: int) -> SpeciesRisk:
    if d.frac_forest < 0.02 and sightings == 0:
        return SpeciesRisk("bats", 0.0,
                           "No forest cover; bat roosting habitat implausible.",
                           "low", applicable=False)
    canopy = clip(d.mature_canopy_frac, 0.0, 1.0)
    water = decay(d.water_distance_m, 400.0) / 100.0
    patch = clip(d.forest_patch_area_m2 / 500_000.0, 0.0, 1.0)
    risk = clip(0.50 * canopy + 0.25 * water + 0.25 * patch, 0.0, 1.0)
    bits = []
    if canopy > 0.3:
        bits.append("mature canopy")
    if patch > 0.3:
        bits.append("a large forest block")
    if water > 0.3:
        bits.append("water for foraging")
    reason = ("Site provides " + ", ".join(bits) + ".") if bits else "Marginal bat habitat."
    return SpeciesRisk("bats", risk, reason, _confidence(sightings))


def _pollinators_risk(d: SiteData, sightings: int) -> SpeciesRisk:
    open_land = clip(d.frac_open_land + d.frac_grassland, 0.0, 1.0)
    edge = clip(d.frac_forest * 0.5, 0.0, 1.0)
    risk = clip(0.75 * open_land + 0.25 * edge, 0.0, 1.0)
    if open_land > 0.3:
        reason = "Open meadow / grassland supports pollinators; clearing removes forage."
    elif risk > 0.1:
        reason = "Some edge habitat for pollinators; consider on-site planting."
    else:
        reason = "Little pollinator habitat; a planting opportunity rather than a loss."
    return SpeciesRisk("pollinators", risk, reason, _confidence(sightings))


_SPECIES_FUNCS = {
    "beaver": _beaver_risk,
    "bats": _bats_risk,
    "pollinators": _pollinators_risk,
}


def species_risks(d: SiteData) -> list[SpeciesRisk]:
    counts = {s.name: s.sightings_count for s in d.species}
    # Always evaluate the three known modules; a missing species record
    # just means a sighting count of 0.
    out = []
    for name, fn in _SPECIES_FUNCS.items():
        out.append(fn(d, counts.get(name, 0)))
    return out


# --------------------------------------------------------------------------
# The six sub-scores
# --------------------------------------------------------------------------
def s_habitat(d: SiteData) -> float:
    w = config.HABITAT_WEIGHTS
    loss = (w["wetland"] * d.frac_wetland
            + w["priority_habitat"] * d.frac_priority_habitat
            + w["forest"] * d.frac_forest
            + w["vernal_pool"] * d.frac_vernal_pool
            + w["grassland"] * d.frac_grassland)
    return _clamp(100.0 * (1.0 - loss))


def s_keystone(risks: list[SpeciesRisk]) -> float:
    applicable = [r for r in risks if r.applicable]
    if not applicable:
        return _clamp(config.S_K_NEUTRAL)
    raw = {r.name: config.SPECIES_IMPORTANCE.get(r.name, 0.0) for r in applicable}
    total = sum(raw.values())
    if total <= 0:
        norm = {r.name: 1.0 / len(applicable) for r in applicable}
    else:
        norm = {k: v / total for k, v in raw.items()}
    weighted = sum(norm[r.name] * r.risk for r in applicable)
    return _clamp(100.0 * (1.0 - weighted))


def s_connectivity(d: SiteData) -> float:
    return _clamp(100.0 * d.natural_frac_context)


def s_carbon(d: SiteData) -> float:
    co2_lost = d.canopy_area_m2 * config.CARBON_DENSITY_KG_PER_M2 * (44.0 / 12.0)
    carbon = 100.0 - lin(co2_lost, 0.0, config.CO2_MAX_KG)
    transit = decay(d.transit_distance_m, config.TRANSIT_DECAY_M)
    return _clamp(0.5 * carbon + 0.5 * transit)


def s_landreuse(d: SiteData) -> float:
    t = config.LAND_REUSE_WEIGHTS
    reuse = (t["impervious"] * d.frac_impervious
             + t["developed"] * d.frac_developed
             + t["brownfield"] * (1.0 if d.is_brownfield else 0.0)
             + t["agriculture"] * d.frac_agriculture)
    return _clamp(100.0 * reuse)


def s_regulatory(d: SiteData) -> float:
    penalty = sum(pen for name, pen in config.PENALTIES.items()
                  if d.triggers.get(name, False))
    return _clamp(100.0 - penalty)


# --------------------------------------------------------------------------
# Combine -> gate -> confidence -> grade
# --------------------------------------------------------------------------
_BANDS = [
    (85, "A", "Recommended"),
    (70, "B", "Low impact"),
    (55, "C", "Moderate: mitigation needed"),
    (40, "D", "High impact: consider alternatives"),
    (0, "F", "Not recommended"),
]


def grade_for(rating: float) -> tuple[str, str]:
    r = clip(rating, 0.0, 100.0)
    for low, grade, label in _BANDS:
        if r >= low:
            return grade, label
    return "F", "Not recommended"


def data_confidence(d: SiteData) -> float:
    survey = min(1.0, d.n_all_records / config.N_REF_RECORDS) if config.N_REF_RECORDS else 0.0
    nlcd = clip(d.nlcd_confidence, 0.0, 1.0)
    uncertainty = 1.0 - clip(d.mean_location_uncertainty_m / config.U_MAX_M, 0.0, 1.0)
    q = 100.0 * survey * nlcd * uncertainty
    if d.layer_available:
        total = len(d.layer_available)
        ok = sum(1 for v in d.layer_available.values() if v)
        if total:
            q *= ok / total
    return clip(q, 0.0, 100.0)


@dataclass
class ScoreResult:
    subscores: dict[str, float]
    categories: dict[str, float]
    species: list[SpeciesRisk]
    e_raw: float
    e_gated: float
    data_confidence: float
    e_final: float
    confidence_band: float
    grade: str
    label: str
    flags: list[str] = field(default_factory=list)
    mitigation: list[str] = field(default_factory=list)


def _mitigation(d: SiteData, risks: list[SpeciesRisk], flags: list[str]) -> list[str]:
    tips = []
    if d.frac_wetland > 0.05 or d.triggers.get("wetland_or_buffer"):
        tips.append("Keep a 30 m undisturbed buffer around wetlands and streams.")
    if any(r.name == "bats" and r.applicable and r.risk > 0.4 for r in risks):
        tips.append("Avoid clearing mature trees between April and September (bat season).")
    if any(r.name == "pollinators" and r.applicable for r in risks):
        tips.append("Plant native pollinator habitat on retained open land.")
    if d.frac_forest > 0.4:
        tips.append("Cluster the footprint to preserve the largest contiguous forest block.")
    if flags:
        tips.append("Engage a permitting consultant early; regulatory review is likely.")
    if not tips:
        tips.append("Low ecological sensitivity; standard erosion and stormwater controls apply.")
    return tips


def score(d: SiteData) -> ScoreResult:
    risks = species_risks(d)
    subs = {
        "S_H": s_habitat(d),
        "S_K": s_keystone(risks),
        "S_C": s_connectivity(d),
        "S_Cb": s_carbon(d),
        "S_L": s_landreuse(d),
        "S_G": s_regulatory(d),
    }

    e_eco = geo([subs["S_H"], subs["S_K"], subs["S_C"]])
    e_climate = subs["S_Cb"]
    e_site = (subs["S_L"] + subs["S_G"]) / 2.0
    gw = config.GROUP_WEIGHTS
    e_blended = gw["eco"] * e_eco + gw["climate"] * e_climate + gw["site"] * e_site
    # Stretch around the pivot to spread scores out of the mid-range cluster.
    e_spread = config.SPREAD_PIVOT + (e_blended - config.SPREAD_PIVOT) * config.SPREAD_GAIN
    e_raw = clip(e_spread, 0, 100)
    categories = {"E_eco": e_eco, "E_climate": e_climate, "E_site": e_site}

    flags: list[str] = []
    fired = any(d.hard_triggers.get(t, False)
                for t in ("protected_open_space", "federal_critical_habitat",
                          "regulated_wetland_fill"))
    e_gated = min(e_raw, config.HARD_GATE_CAP) if fired else e_raw
    if fired:
        flags.append(config.HARD_GATE_FLAG)

    q = data_confidence(d)
    e_final = clip((q / 100.0) * e_gated + (1 - q / 100.0) * config.CONSERVATIVE_PRIOR, 0, 100)
    margin = (100.0 - q) / 5.0
    grade, label = grade_for(e_final)

    return ScoreResult(
        subscores=subs,
        categories=categories,
        species=risks,
        e_raw=e_raw,
        e_gated=e_gated,
        data_confidence=q,
        e_final=e_final,
        confidence_band=margin,
        grade=grade,
        label=label,
        flags=flags,
        mitigation=_mitigation(d, risks, flags),
    )


def result_to_dict(d: SiteData, r: ScoreResult) -> dict:
    return {
        "location": {"lat": d.lat, "lon": d.lon},
        "label": d.label,
        "site_score": round(r.e_final),
        "e_final": round(r.e_final, 1),
        "grade": r.grade,
        "grade_label": r.label,
        "confidence_band": round(r.confidence_band, 1),
        "data_confidence": round(r.data_confidence, 1),
        "subscores": {k: round(v, 1) for k, v in r.subscores.items()},
        "categories": {k: round(v, 1) for k, v in r.categories.items()},
        "species": [
            {"species": s.name, "risk": round(s.risk, 3), "reason": s.reason,
             "confidence": s.confidence, "applicable": s.applicable}
            for s in r.species
        ],
        "flags": r.flags,
        "mitigation": r.mitigation,
        "coverage": d.coverage,
        "data_sources": d.data_sources,
        "is_live": d.is_live,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a site-data JSON file.")
    parser.add_argument("dataset", help="path to a site-data JSON file")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON")
    parser.add_argument("-o", "--out", help="write the result JSON to this path")
    args = parser.parse_args(argv)

    path = Path(args.dataset)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 1

    data = SiteData.load(path)
    problems = validate(data)
    if problems:
        print("error: invalid dataset:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    result = score(data)
    payload = result_to_dict(data, result)

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2))

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_summary(data, result)
    return 0


def _print_summary(d: SiteData, r: ScoreResult) -> None:
    title = d.label or f"({d.lat}, {d.lon})"
    print(f"\n{title}")
    print(f"  {'LIVE' if d.is_live else 'PREFILLED'} data | coverage: {d.coverage}")
    print(f"  Grade {r.grade} ({r.label})")
    print(f"  Rating {r.e_final:.1f} +/- {r.confidence_band:.1f}   "
          f"(confidence Q={r.data_confidence:.0f})")
    print("  Sub-scores: " + "  ".join(f"{k}={v:.0f}" for k, v in r.subscores.items()))
    print("  Categories: " + "  ".join(f"{k}={v:.0f}" for k, v in r.categories.items()))
    print("  Species:")
    for s in r.species:
        tag = "" if s.applicable else "  [N/A]"
        print(f"    {s.name:12} risk={s.risk:.2f} ({s.confidence}){tag}  {s.reason}")
    if r.flags:
        print("  Flags: " + ", ".join(r.flags))
    print("  Mitigation:")
    for tip in r.mitigation:
        print(f"    - {tip}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())

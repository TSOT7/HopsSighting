"""The site-data JSON schema: the handoff between the two backend parts.

Part 1 (fetch.py) writes one of these JSON files per location. Part 2
(score.py) reads it and runs the math. The file on disk is the ONLY
coupling between the two parts, so each can be built and run alone.

This module defines the schema as a dataclass with explicit field
documentation plus load/save helpers and a validator. Keeping it in one
place means both parts agree on the exact keys.

Every field maps to a variable in docs/scoring-model.md ("data inputs").
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA_VERSION = "1.0"

# Data layers whose availability affects data confidence (Q). If a layer
# failed to load, record it here as False so the scorer lowers Q rather
# than reading missing data as "no impact".
LAYER_KEYS: tuple[str, ...] = (
    "land_cover",       # NLCD land cover
    "tree_canopy",      # NLCD tree canopy
    "impervious",       # NLCD impervious surface
    "wetlands",         # USFWS NWI
    "streams",          # USGS NHD
    "flood",            # FEMA NFHL
    "protected",        # PAD-US
    "priority_habitat", # MA NHESP / BioMap
    "brownfield",       # MassDEP 21E / EPA
    "transit",          # MBTA GTFS
    "sightings",        # GBIF / iNaturalist
)

# Regulatory triggers the scorer knows about (match scoring-model.md).
TRIGGER_KEYS: tuple[str, ...] = (
    "protected_open_space",
    "federal_critical_habitat",
    "nhesp_priority_habitat",
    "wetland_or_buffer",
    "riverfront_area",
    "fema_flood_zone",
    "zoning_not_by_right",
)

# Hard-gate triggers (a hit caps the final rating).
HARD_TRIGGER_KEYS: tuple[str, ...] = (
    "protected_open_space",
    "federal_critical_habitat",
    "regulated_wetland_fill",
)


@dataclass
class SpeciesRecord:
    """Per-species observation data pulled by the fetcher.

    The scorer turns these into a risk; here we only carry the raw
    signals it needs (sighting count + habitat proxies specific to the
    species are read from the site-level habitat fields).
    """

    name: str                 # "beaver" | "bats" | "pollinators"
    sightings_count: int = 0  # records of this species in the buffer


@dataclass
class SiteData:
    """Everything the scorer needs for one location.

    Produced by the fetcher, consumed by the scorer. All fractions are
    0-1; distances in metres; booleans are 0/1 flags.
    """

    # --- identity / provenance ------------------------------------------
    lat: float
    lon: float
    schema_version: str = SCHEMA_VERSION
    label: str = ""
    coverage: str = "national"            # "national" | "national+MA" | "unknown"
    data_sources: list[str] = field(default_factory=list)
    fetched_at: str = ""                  # ISO 8601 UTC, when fetched
    is_live: bool = False                 # True if from live APIs, False if prefilled

    # --- habitat fractions (S_H) ----------------------------------------
    frac_wetland: float = 0.0
    frac_priority_habitat: float = 0.0
    frac_forest: float = 0.0
    frac_vernal_pool: float = 0.0
    frac_grassland: float = 0.0

    # --- connectivity (S_C) ---------------------------------------------
    natural_frac_context: float = 0.0

    # --- carbon / climate (S_Cb) ----------------------------------------
    canopy_area_m2: float = 0.0
    transit_distance_m: float = 5000.0

    # --- land reuse (S_L) -----------------------------------------------
    frac_impervious: float = 0.0
    frac_developed: float = 0.0
    frac_agriculture: float = 0.0
    is_brownfield: bool = False

    # --- species habitat proxies (S_K, shared across species) -----------
    mature_canopy_frac: float = 0.0
    frac_open_land: float = 0.0
    stream_distance_m: float = 1e9
    water_distance_m: float = 1e9
    mean_slope_deg: float = 10.0
    forest_patch_area_m2: float = 0.0
    species: list[SpeciesRecord] = field(default_factory=list)

    # --- regulatory (S_G + hard gate) -----------------------------------
    triggers: dict[str, bool] = field(default_factory=dict)
    hard_triggers: dict[str, bool] = field(default_factory=dict)

    # --- data confidence (Q) --------------------------------------------
    n_all_records: int = 0
    nlcd_confidence: float = 0.9
    mean_location_uncertainty_m: float = 150.0
    layer_available: dict[str, bool] = field(default_factory=dict)

    # -------------------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_dict(cls, data: dict) -> "SiteData":
        species = [SpeciesRecord(**s) for s in data.get("species", [])]
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known and k != "species"}
        return cls(species=species, **kwargs)

    @classmethod
    def load(cls, path: str | Path) -> "SiteData":
        return cls.from_dict(json.loads(Path(path).read_text()))


def validate(data: SiteData) -> list[str]:
    """Return a list of problems with a SiteData; empty means valid.

    Light validation — enough to catch a malformed hand-authored dataset
    before scoring, not a full schema enforcer.
    """
    problems: list[str] = []

    if not (-90 <= data.lat <= 90):
        problems.append(f"lat out of range: {data.lat}")
    if not (-180 <= data.lon <= 180):
        problems.append(f"lon out of range: {data.lon}")

    fractions = {
        "frac_wetland": data.frac_wetland,
        "frac_priority_habitat": data.frac_priority_habitat,
        "frac_forest": data.frac_forest,
        "frac_vernal_pool": data.frac_vernal_pool,
        "frac_grassland": data.frac_grassland,
        "natural_frac_context": data.natural_frac_context,
        "frac_impervious": data.frac_impervious,
        "frac_developed": data.frac_developed,
        "frac_agriculture": data.frac_agriculture,
        "mature_canopy_frac": data.mature_canopy_frac,
        "frac_open_land": data.frac_open_land,
        "nlcd_confidence": data.nlcd_confidence,
    }
    for name, value in fractions.items():
        if not (0.0 <= value <= 1.0):
            problems.append(f"{name} must be in [0,1], got {value}")

    for key in data.triggers:
        if key not in TRIGGER_KEYS:
            problems.append(f"unknown trigger: {key}")
    for key in data.hard_triggers:
        if key not in HARD_TRIGGER_KEYS:
            problems.append(f"unknown hard trigger: {key}")

    return problems

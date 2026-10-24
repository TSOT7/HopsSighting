"""Scoring parameters (from docs/scoring-model.md).

Every number here is a judgement call. Values tagged PLACEHOLDER are
first guesses to calibrate against known sites; the relative ordering is
already sensible, absolute grades are not yet trustworthy.
"""
from __future__ import annotations

# S_H habitat weights (sum to 1)
HABITAT_WEIGHTS = {
    "wetland": 0.30,            # PLACEHOLDER
    "priority_habitat": 0.25,   # PLACEHOLDER
    "forest": 0.20,             # PLACEHOLDER
    "vernal_pool": 0.15,        # PLACEHOLDER
    "grassland": 0.10,          # PLACEHOLDER
}

# S_K species importance (renormalized over applicable species)
SPECIES_IMPORTANCE = {
    "beaver": 0.40,       # PLACEHOLDER
    "bats": 0.35,         # PLACEHOLDER
    "pollinators": 0.25,  # PLACEHOLDER
}
S_K_NEUTRAL = 70.0        # PLACEHOLDER - S_K when no species apply

# S_Cb carbon / climate
CARBON_DENSITY_KG_PER_M2 = 12.0   # PLACEHOLDER - kg C / m^2 canopy
CO2_MAX_KG = 500_000.0            # PLACEHOLDER - c_max
TRANSIT_DECAY_M = 800.0           # PLACEHOLDER - d0

# S_L land-reuse weights (sum to 1)
LAND_REUSE_WEIGHTS = {
    "impervious": 0.35,   # PLACEHOLDER
    "developed": 0.30,    # PLACEHOLDER
    "brownfield": 0.20,   # PLACEHOLDER
    "agriculture": 0.15,  # PLACEHOLDER
}

# S_G regulatory penalties
PENALTIES = {
    "protected_open_space": 100.0,
    "federal_critical_habitat": 40.0,
    "nhesp_priority_habitat": 35.0,
    "wetland_or_buffer": 25.0,
    "riverfront_area": 20.0,
    "fema_flood_zone": 15.0,
    "zoning_not_by_right": 15.0,
}

# Option-D group weights (sum to 1)
GROUP_WEIGHTS = {"eco": 0.50, "climate": 0.30, "site": 0.20}

# Hard gate
HARD_GATE_CAP = 40.0              # PLACEHOLDER
HARD_GATE_FLAG = "regulatory review likely"

# Data confidence (Q) + prior
N_REF_RECORDS = 100              # PLACEHOLDER
U_MAX_M = 1_000.0                # PLACEHOLDER
CONSERVATIVE_PRIOR = 40.0        # E_0

# Recommender
E_MIN = 55.0                     # PLACEHOLDER

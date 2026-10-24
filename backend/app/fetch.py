"""Part 1: the fetcher.

Builds a site-data JSON file for a location. Two modes:

- live:      calls the public APIs (GBIF, iNaturalist) for sightings and
             survey effort, and records which data layers it could fill.
             GIS raster layers (NLCD / NWI / NHD) are heavy to fetch and
             are left marked unavailable here, which honestly lowers the
             data confidence the scorer computes.
- prefilled: copies one of the hand-authored demo datasets in datasets/.
             This is what the demo runs on.

Writes a JSON file that score.py reads. Run standalone:

    python -m app.fetch --prefilled forested -o datasets/forested.json
    python -m app.fetch --live --lat 42.38 --lon -71.06 -o out.json
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .schema import LAYER_KEYS, SiteData, SpeciesRecord

# Keystone species -> GBIF scientific name used for the sightings count.
SPECIES_TAXA = {
    "beaver": "Castor canadensis",
    "bats": "Chiroptera",
    "pollinators": "Apoidea",
}

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"
INAT_URL = "https://api.inaturalist.org/v1/observations"
USER_AGENT = "HopsSighting/1.0 (hackathon; contact: team@hopssighting.example)"
_TIMEOUT = 8.0

DATASETS_DIR = Path(__file__).resolve().parents[1] / "datasets"


# --------------------------------------------------------------------------
# Prefilled mode
# --------------------------------------------------------------------------
def load_prefilled(name: str) -> SiteData:
    """Load a hand-authored demo dataset by name (without .json)."""
    path = DATASETS_DIR / f"{name}.json"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in DATASETS_DIR.glob("*.json")))
        raise FileNotFoundError(
            f"no prefilled dataset '{name}'. Available: {available or '(none)'}"
        )
    return SiteData.load(path)


# --------------------------------------------------------------------------
# Live mode
# --------------------------------------------------------------------------
def _bbox_wkt(lat: float, lon: float, pad: float = 0.01) -> str:
    minx, miny, maxx, maxy = lon - pad, lat - pad, lon + pad, lat + pad
    return (f"POLYGON(({minx} {miny},{maxx} {miny},"
            f"{maxx} {maxy},{minx} {maxy},{minx} {miny}))")


def fetch_live(lat: float, lon: float) -> SiteData:
    """Fetch what the public sighting APIs can give for a location.

    GIS layers are left unavailable (not fetched here), so the scorer's
    confidence reflects that only sightings were loaded.
    """
    import requests  # imported lazily so the scorer never needs it

    headers = {"User-Agent": USER_AGENT}
    geometry = _bbox_wkt(lat, lon)
    sources: list[str] = []

    layer_available = {k: False for k in LAYER_KEYS}

    # Survey effort + per-species counts from GBIF.
    n_all = 0
    species_counts: dict[str, int] = {}
    try:
        total = requests.get(GBIF_URL, params={"geometry": geometry, "limit": 0},
                             headers=headers, timeout=_TIMEOUT)
        total.raise_for_status()
        n_all = int(total.json().get("count", 0))
        for name, taxon in SPECIES_TAXA.items():
            resp = requests.get(GBIF_URL,
                                params={"geometry": geometry, "limit": 0,
                                        "scientificName": taxon},
                                headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            species_counts[name] = int(resp.json().get("count", 0))
        layer_available["sightings"] = True
        sources.append("GBIF")
    except Exception as exc:  # noqa: BLE001
        print(f"warning: GBIF fetch failed: {exc}", file=sys.stderr)

    # Location uncertainty from iNaturalist.
    mean_unc = 150.0
    try:
        minx, miny, maxx, maxy = lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01
        inat = requests.get(INAT_URL,
                            params={"swlat": miny, "swlng": minx,
                                    "nelat": maxy, "nelng": maxx, "per_page": 50},
                            headers=headers, timeout=_TIMEOUT)
        inat.raise_for_status()
        accs = [o["positional_accuracy"] for o in inat.json().get("results", [])
                if o.get("positional_accuracy") is not None]
        if accs:
            mean_unc = sum(accs) / len(accs)
        sources.append("iNaturalist")
    except Exception as exc:  # noqa: BLE001
        print(f"warning: iNaturalist fetch failed: {exc}", file=sys.stderr)

    return SiteData(
        lat=lat,
        lon=lon,
        label=f"Live fetch ({lat:.4f}, {lon:.4f})",
        coverage="sightings-only",
        data_sources=sources,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        is_live=True,
        species=[SpeciesRecord(name=n, sightings_count=species_counts.get(n, 0))
                 for n in SPECIES_TAXA],
        n_all_records=n_all,
        nlcd_confidence=0.0,  # no land cover fetched live
        mean_location_uncertainty_m=mean_unc,
        layer_available=layer_available,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch site data into a JSON file.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prefilled", metavar="NAME",
                      help="use a demo dataset from datasets/ (e.g. forested)")
    mode.add_argument("--live", action="store_true", help="fetch from live APIs")
    parser.add_argument("--lat", type=float, help="latitude (live mode)")
    parser.add_argument("--lon", type=float, help="longitude (live mode)")
    parser.add_argument("-o", "--out", help="write the JSON here (default: stdout)")
    args = parser.parse_args(argv)

    if args.live:
        if args.lat is None or args.lon is None:
            print("error: --live requires --lat and --lon", file=sys.stderr)
            return 1
        data = fetch_live(args.lat, args.lon)
    else:
        try:
            data = load_prefilled(args.prefilled)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.out:
        data.save(args.out)
        print(f"wrote {args.out}")
    else:
        import json
        print(json.dumps(data.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Part 3: the reporter.

Produces a detailed, professional Markdown report explaining how a
site's final rating was computed: every sub-score with its plugged-in
arithmetic, the species-risk breakdown, the Option-D grouping, the hard
gate, and the data-confidence adjustment, each with a short factual
interpretation.

The UI turns this Markdown into a downloadable PDF. This module only
produces the Markdown.

The numbers shown are anchored to the same values score.py computes (via
the ScoreResult), and the arithmetic is rebuilt from the same config and
SiteData, so what is displayed matches what is calculated.

Run standalone:

    python -m app.report datasets/forested.json -o report.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config
from .schema import SiteData, validate
from .score import (
    ScoreResult,
    SpeciesRisk,
    decay,
    lin,
    score,
)


def _f(x: float, nd: int = 2) -> str:
    """Format a number without a trailing .0 clutter for whole numbers."""
    return f"{x:.{nd}f}"


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


# --------------------------------------------------------------------------
# Per-section builders
# --------------------------------------------------------------------------
def _header(d: SiteData, r: ScoreResult) -> list[str]:
    lines = [
        f"# Environmental Impact Report",
        "",
        f"**Site:** {d.label or 'Unnamed parcel'}  ",
        f"**Location:** {_f(d.lat, 4)}, {_f(d.lon, 4)} (WGS84)  ",
        f"**Data coverage:** {d.coverage}  ",
        f"**Data mode:** {'Live API fetch' if d.is_live else 'Prefilled dataset'}  ",
        f"**Data sources:** {', '.join(d.data_sources) if d.data_sources else 'none recorded'}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"**Final rating: {_f(r.e_final, 1)} / 100 \u00b1 {_f(r.confidence_band, 1)}** "
        f"&mdash; Grade **{r.grade}** ({r.label}).",
        "",
        f"The rating runs 0\u2013100, where a higher score indicates lower "
        f"environmental impact and greater suitability for development. "
        f"This site scored {_f(r.e_final, 1)}, placing it in the **{r.grade}** band.",
        "",
        f"The result carries a margin of \u00b1{_f(r.confidence_band, 1)} points, "
        f"reflecting a data-confidence index of {_f(r.data_confidence, 0)} out of 100 "
        f"(see Section 4).",
        "",
    ]
    if r.flags:
        lines += [
            "> **Regulatory flag:** " + "; ".join(r.flags) + ".",
            "",
        ]
    return lines


def _habitat_section(d: SiteData) -> list[str]:
    w = config.HABITAT_WEIGHTS
    terms = [
        ("Wetland", w["wetland"], d.frac_wetland),
        ("Priority / BioMap habitat", w["priority_habitat"], d.frac_priority_habitat),
        ("Mature forest", w["forest"], d.frac_forest),
        ("Vernal pool", w["vernal_pool"], d.frac_vernal_pool),
        ("Grassland / meadow", w["grassland"], d.frac_grassland),
    ]
    loss = sum(weight * frac for _, weight, frac in terms)
    value = max(0.0, min(100.0, 100.0 * (1.0 - loss)))

    rows = ["| Habitat | Weight | Site fraction | Contribution |",
            "|---|---|---|---|"]
    for name, weight, frac in terms:
        rows.append(f"| {name} | {_f(weight, 2)} | {_pct(frac)} | {_f(weight * frac, 4)} |")
    arith = " + ".join(f"{_f(weight, 2)}\u00b7{_f(frac, 2)}"
                        for _, weight, frac in terms)

    return [
        "### 1. Habitat Integrity (S_H)",
        "",
        "Measures how much natural habitat the footprint would destroy, as a "
        "weighted sum of the protected habitat types present on the site.",
        "",
        "**Formula:** S_H = 100 \u00d7 (1 \u2212 \u03a3 weight\u1d62 \u00d7 fraction\u1d62)",
        "",
        *rows,
        "",
        f"**Calculation:** weighted loss = {arith} = {_f(loss, 4)}  ",
        f"S_H = 100 \u00d7 (1 \u2212 {_f(loss, 4)}) = **{_f(value, 1)}**",
        "",
        f"*Interpretation:* " + _habitat_interpretation(value, d),
        "",
    ]


def _habitat_interpretation(value: float, d: SiteData) -> str:
    if value >= 80:
        return ("The footprint overlaps little protected habitat, so direct "
                "habitat loss is limited.")
    if value >= 50:
        return ("The site carries a moderate amount of protected habitat; "
                "development would cause meaningful but not severe habitat loss.")
    return ("A large share of the site is protected habitat, so development "
            "would destroy a significant amount of it.")


def _species_section(risks: list[SpeciesRisk], sk_value: float) -> list[str]:
    lines = [
        "### 2. Keystone Species Impact (S_K)",
        "",
        "Estimates impact on keystone species. Each species module returns a "
        "risk from 0 to 1 based on on-site habitat suitability. Species that are "
        "implausible for the area are excluded, and the remaining importance "
        "weights are renormalized.",
        "",
        "**Formula:** S_K = 100 \u00d7 (1 \u2212 \u03a3 importance\u2c7c \u00d7 risk\u2c7c), over applicable species",
        "",
        "**Per-species risk:**",
        "",
        "| Species | Risk (0\u20131) | Importance | Applicable | Basis |",
        "|---|---|---|---|---|",
    ]
    for s in risks:
        imp = config.SPECIES_IMPORTANCE.get(s.name, 0.0)
        applicable = "yes" if s.applicable else "no (excluded)"
        lines.append(
            f"| {s.name} | {_f(s.risk, 3)} | {_f(imp, 2)} | {applicable} | {s.reason} |"
        )
    lines.append("")

    applicable = [s for s in risks if s.applicable]
    if not applicable:
        lines += [
            f"No keystone species were applicable to this site, so S_K defaults "
            f"to the neutral value of **{_f(config.S_K_NEUTRAL, 1)}**.",
            "",
        ]
        return lines

    raw = {s.name: config.SPECIES_IMPORTANCE.get(s.name, 0.0) for s in applicable}
    total = sum(raw.values())
    norm = ({k: v / total for k, v in raw.items()} if total > 0
            else {s.name: 1.0 / len(applicable) for s in applicable})
    weighted = sum(norm[s.name] * s.risk for s in applicable)
    arith = " + ".join(f"{_f(norm[s.name], 3)}\u00b7{_f(s.risk, 3)}" for s in applicable)

    lines += [
        f"**Renormalized weights** (over applicable species): "
        + ", ".join(f"{name} = {_f(wt, 3)}" for name, wt in norm.items()) + ".",
        "",
        f"**Calculation:** weighted risk = {arith} = {_f(weighted, 4)}  ",
        f"S_K = 100 \u00d7 (1 \u2212 {_f(weighted, 4)}) = **{_f(sk_value, 1)}**",
        "",
        "*Interpretation:* " + _species_interpretation(sk_value),
        "",
    ]
    return lines


def _species_interpretation(value: float) -> str:
    if value >= 75:
        return "Keystone-species pressure is low; the site offers limited habitat for them."
    if value >= 45:
        return ("The site provides meaningful habitat for one or more keystone "
                "species; development would carry moderate species impact.")
    return ("The site is high-value habitat for keystone species; development "
            "would pose substantial risk to them.")


def _connectivity_section(d: SiteData, value: float) -> list[str]:
    return [
        "### 3. Connectivity / Fragmentation (S_C)",
        "",
        "Measures how embedded the site is within unbroken natural land. A site "
        "inside a large intact patch fragments more habitat when developed, which "
        "represents higher conservation value.",
        "",
        "**Formula:** S_C = 100 \u00d7 (natural fraction of the surrounding context area)",
        "",
        f"**Calculation:** natural context fraction = {_pct(d.natural_frac_context)}  ",
        f"S_C = 100 \u00d7 {_f(d.natural_frac_context, 2)} = **{_f(value, 1)}**",
        "",
        "*Interpretation:* " + (
            "The surrounding area is largely intact natural land, so building here "
            "would fragment a substantial contiguous habitat block."
            if value >= 60 else
            "The surrounding area is already fragmented or developed, so additional "
            "fragmentation from this site would be limited."
        ),
        "",
    ]


def _carbon_section(d: SiteData, value: float) -> list[str]:
    co2_lost = d.canopy_area_m2 * config.CARBON_DENSITY_KG_PER_M2 * (44.0 / 12.0)
    carbon_component = 100.0 - lin(co2_lost, 0.0, config.CO2_MAX_KG)
    transit_component = decay(d.transit_distance_m, config.TRANSIT_DECAY_M)
    return [
        "### 4. Carbon & Climate (S_Cb)",
        "",
        "Combines carbon lost by clearing tree canopy with proximity to transit "
        "(a proxy for avoided vehicle emissions). Each half contributes 50%.",
        "",
        "**Formula:** S_Cb = 0.5 \u00d7 (100 \u2212 lin(CO\u2082 lost; 0, c_max)) "
        "+ 0.5 \u00d7 decay(transit distance; d\u2080)",
        "",
        f"- Canopy area: {_f(d.canopy_area_m2, 0)} m\u00b2  ",
        f"- CO\u2082 lost = {_f(d.canopy_area_m2, 0)} \u00d7 "
        f"{_f(config.CARBON_DENSITY_KG_PER_M2, 1)} kg/m\u00b2 \u00d7 (44/12) = "
        f"**{_f(co2_lost, 0)} kg**  ",
        f"- Carbon component = 100 \u2212 lin({_f(co2_lost, 0)}; 0, "
        f"{_f(config.CO2_MAX_KG, 0)}) = {_f(carbon_component, 1)}  ",
        f"- Transit distance: {_f(d.transit_distance_m, 0)} m  ",
        f"- Transit component = decay({_f(d.transit_distance_m, 0)}; "
        f"{_f(config.TRANSIT_DECAY_M, 0)}) = {_f(transit_component, 1)}",
        "",
        f"**Calculation:** S_Cb = 0.5 \u00d7 {_f(carbon_component, 1)} + "
        f"0.5 \u00d7 {_f(transit_component, 1)} = **{_f(value, 1)}**",
        "",
        "*Interpretation:* " + _carbon_interpretation(value, co2_lost, d),
        "",
    ]


def _carbon_interpretation(value: float, co2_lost: float, d: SiteData) -> str:
    parts = []
    if co2_lost > 0.3 * config.CO2_MAX_KG:
        parts.append("clearing the canopy would release substantial stored carbon")
    else:
        parts.append("little canopy carbon is at stake")
    if d.transit_distance_m <= config.TRANSIT_DECAY_M:
        parts.append("the site is well served by transit")
    else:
        parts.append("the site is poorly served by transit")
    return parts[0].capitalize() + ", and " + parts[1] + "."


def _landreuse_section(d: SiteData, value: float) -> list[str]:
    t = config.LAND_REUSE_WEIGHTS
    terms = [
        ("Impervious surface", t["impervious"], d.frac_impervious),
        ("Already developed", t["developed"], d.frac_developed),
        ("Brownfield / landfill", t["brownfield"], 1.0 if d.is_brownfield else 0.0),
        ("Agriculture", t["agriculture"], d.frac_agriculture),
    ]
    reuse = sum(weight * frac for _, weight, frac in terms)
    rows = ["| Prior disturbance | Weight | Site value | Contribution |",
            "|---|---|---|---|"]
    for name, weight, frac in terms:
        shown = _pct(frac) if name != "Brownfield / landfill" else ("yes" if frac else "no")
        rows.append(f"| {name} | {_f(weight, 2)} | {shown} | {_f(weight * frac, 4)} |")
    arith = " + ".join(f"{_f(weight, 2)}\u00b7{_f(frac, 2)}" for _, weight, frac in terms)
    return [
        "### 5. Land Reuse (S_L)",
        "",
        "Rewards building on already-disturbed land (impervious, developed, "
        "brownfield, or agricultural) rather than greenfield.",
        "",
        "**Formula:** S_L = 100 \u00d7 \u03a3 weight\u1d62 \u00d7 disturbance\u1d62",
        "",
        *rows,
        "",
        f"**Calculation:** reuse = {arith} = {_f(reuse, 4)}  ",
        f"S_L = 100 \u00d7 {_f(reuse, 4)} = **{_f(value, 1)}**",
        "",
        "*Interpretation:* " + (
            "The site is largely previously disturbed, making it a strong reuse "
            "candidate with low greenfield impact."
            if value >= 50 else
            "The site is largely undisturbed, so development would consume "
            "greenfield land rather than reuse existing disturbance."
        ),
        "",
    ]


def _regulatory_section(d: SiteData, value: float) -> list[str]:
    fired = [(name, pen) for name, pen in config.PENALTIES.items()
             if d.triggers.get(name, False)]
    lines = [
        "### 6. Regulatory Risk (S_G)",
        "",
        "Begins at 100 and subtracts a penalty for each regulatory constraint the "
        "site triggers.",
        "",
        "**Formula:** S_G = max(0, 100 \u2212 \u03a3 penalty\u1d63 for each trigger hit)",
        "",
    ]
    if fired:
        lines += ["| Trigger | Penalty |", "|---|---|"]
        for name, pen in fired:
            lines.append(f"| {name.replace('_', ' ')} | \u2212{_f(pen, 0)} |")
        total = sum(pen for _, pen in fired)
        lines += [
            "",
            f"**Calculation:** S_G = max(0, 100 \u2212 {_f(total, 0)}) = **{_f(value, 1)}**",
            "",
        ]
    else:
        lines += [
            "No regulatory triggers were hit.",
            "",
            f"**Calculation:** S_G = 100 \u2212 0 = **{_f(value, 1)}**",
            "",
        ]
    lines += [
        "*Interpretation:* " + (
            "The site hits regulatory constraints that materially raise permitting "
            "risk." if value < 70 else
            "The site has low regulatory exposure under the datasets consulted."
        ),
        "",
    ]
    return lines


def _combine_section(r: ScoreResult) -> list[str]:
    gw = config.GROUP_WEIGHTS
    subs = r.subscores
    cats = r.categories
    lines = [
        "## 7. Combining the Sub-scores",
        "",
        "The six sub-scores are grouped into three headline categories, then "
        "blended into the overall rating (before gating and confidence).",
        "",
        "**Grouping (Option D):**",
        "",
        f"- Ecology = geometric mean of S_H, S_K, S_C "
        f"= geo({_f(subs['S_H'], 1)}, {_f(subs['S_K'], 1)}, {_f(subs['S_C'], 1)}) "
        f"= **{_f(cats['E_eco'], 1)}**  ",
        f"- Climate = S_Cb = **{_f(cats['E_climate'], 1)}**  ",
        f"- Site = mean(S_L, S_G) "
        f"= ({_f(subs['S_L'], 1)} + {_f(subs['S_G'], 1)}) / 2 "
        f"= **{_f(cats['E_site'], 1)}**",
        "",
        "The geometric mean is used for Ecology so that a single very low "
        "ecological sub-score cannot be masked by high ones.",
        "",
        "**Blend:**",
        "",
        f"E = {_f(gw['eco'], 2)}\u00b7Ecology + {_f(gw['climate'], 2)}\u00b7Climate "
        f"+ {_f(gw['site'], 2)}\u00b7Site",
        "",
        f"E = {_f(gw['eco'], 2)}\u00b7{_f(cats['E_eco'], 1)} + "
        f"{_f(gw['climate'], 2)}\u00b7{_f(cats['E_climate'], 1)} + "
        f"{_f(gw['site'], 2)}\u00b7{_f(cats['E_site'], 1)} = **{_f(r.e_raw, 1)}**",
        "",
    ]
    return lines


def _gate_section(r: ScoreResult) -> list[str]:
    gate_fired = config.HARD_GATE_FLAG in r.flags
    if gate_fired:
        if r.e_gated < r.e_raw:
            effect = (
                f"the rating is capped at {_f(config.HARD_GATE_CAP, 0)}."
            )
            calc = (
                f"E' = min({_f(r.e_raw, 1)}, {_f(config.HARD_GATE_CAP, 0)}) "
                f"= **{_f(r.e_gated, 1)}**"
            )
        else:
            # Trigger fired but the pre-gate rating was already at or below
            # the cap, so the cap did not lower it further.
            effect = (
                f"the rating is capped at {_f(config.HARD_GATE_CAP, 0)}; the "
                f"pre-gate rating was already at or below this cap, so no further "
                f"reduction was applied."
            )
            calc = (
                f"E' = min({_f(r.e_raw, 1)}, {_f(config.HARD_GATE_CAP, 0)}) "
                f"= **{_f(r.e_gated, 1)}** (unchanged)"
            )
        return [
            "## 8. Regulatory Hard Gate",
            "",
            f"A hard regulatory trigger fired, so {effect}",
            "",
            calc,
            "",
            f"Flag raised: *{'; '.join(r.flags)}*.",
            "",
        ]
    return [
        "## 8. Regulatory Hard Gate",
        "",
        "No hard regulatory trigger (protected open space, federal critical "
        "habitat, or regulated wetland fill) fired, so no cap was applied.",
        "",
        f"E' = {_f(r.e_gated, 1)} (unchanged)",
        "",
    ]


def _confidence_section(d: SiteData, r: ScoreResult) -> list[str]:
    survey = min(1.0, d.n_all_records / config.N_REF_RECORDS) if config.N_REF_RECORDS else 0.0
    nlcd = max(0.0, min(1.0, d.nlcd_confidence))
    uncertainty = 1.0 - max(0.0, min(1.0, d.mean_location_uncertainty_m / config.U_MAX_M))
    layer_factor = 1.0
    layer_note = ""
    if d.layer_available:
        total = len(d.layer_available)
        ok = sum(1 for v in d.layer_available.values() if v)
        if total:
            layer_factor = ok / total
            layer_note = f" \u00d7 {ok}/{total} layers available"

    return [
        "## 9. Data-Confidence Adjustment",
        "",
        "The rating is shrunk toward a conservative prior of "
        f"{_f(config.CONSERVATIVE_PRIOR, 0)} when data is thin, so that missing or "
        "uncertain data never produces a falsely favourable score.",
        "",
        "**Confidence index (Q):**",
        "",
        f"- Survey effort = min(1, {d.n_all_records} / {config.N_REF_RECORDS}) "
        f"= {_f(survey, 3)}  ",
        f"- Land-cover classification confidence = {_f(nlcd, 3)}  ",
        f"- Location certainty = 1 \u2212 ({_f(d.mean_location_uncertainty_m, 0)} / "
        f"{_f(config.U_MAX_M, 0)}) = {_f(uncertainty, 3)}  ",
        f"- Q = 100 \u00d7 {_f(survey, 3)} \u00d7 {_f(nlcd, 3)} \u00d7 "
        f"{_f(uncertainty, 3)}{layer_note} = **{_f(r.data_confidence, 1)}**",
        "",
        "**Shrinkage toward the prior:**",
        "",
        f"E_final = (Q/100)\u00b7E' + (1 \u2212 Q/100)\u00b7{_f(config.CONSERVATIVE_PRIOR, 0)}  ",
        f"E_final = ({_f(r.data_confidence / 100, 3)})\u00b7{_f(r.e_gated, 1)} + "
        f"({_f(1 - r.data_confidence / 100, 3)})\u00b7{_f(config.CONSERVATIVE_PRIOR, 0)} "
        f"= **{_f(r.e_final, 1)}**",
        "",
        f"The displayed margin of \u00b1{_f(r.confidence_band, 1)} is "
        f"(100 \u2212 Q) / 5.",
        "",
        "*Interpretation:* " + (
            "Data confidence is high, so the rating closely reflects the computed "
            "sub-scores."
            if r.data_confidence >= 70 else
            "Data confidence is limited, so the rating has been pulled toward the "
            "conservative prior and should be read with its margin in mind."
        ),
        "",
    ]


def _mitigation_section(r: ScoreResult) -> list[str]:
    lines = ["## 10. Recommended Mitigation", ""]
    for tip in r.mitigation:
        lines.append(f"- {tip}")
    lines.append("")
    return lines


def _footer() -> list[str]:
    return [
        "---",
        "",
        "## Methodology & Limitations",
        "",
        "This report is a screening assessment, not a permit or a substitute for "
        "professional ecological or legal review. Sub-score weights, penalties, and "
        "thresholds are configurable parameters; the current values are provisional "
        "and pending calibration against reference sites. Species presence is "
        "estimated from habitat suitability and sighting records, not direct survey. "
        "The full model is documented in the project's scoring-model reference.",
        "",
    ]


# --------------------------------------------------------------------------
# Top-level builder
# --------------------------------------------------------------------------
def build_report(d: SiteData, r: ScoreResult | None = None) -> str:
    """Return the full Markdown report for a site."""
    if r is None:
        r = score(d)

    sections: list[str] = []
    sections += _header(d, r)
    sections += ["## Detailed Factor Calculations", ""]
    sections += _habitat_section(d)
    sections += _species_section(r.species, r.subscores["S_K"])
    sections += _connectivity_section(d, r.subscores["S_C"])
    sections += _carbon_section(d, r.subscores["S_Cb"])
    sections += _landreuse_section(d, r.subscores["S_L"])
    sections += _regulatory_section(d, r.subscores["S_G"])
    sections += _combine_section(r)
    sections += _gate_section(r)
    sections += _confidence_section(d, r)
    sections += _mitigation_section(r)
    sections += _footer()
    return "\n".join(sections)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a detailed Markdown report for a site-data JSON file."
    )
    parser.add_argument("dataset", help="path to a site-data JSON file")
    parser.add_argument("-o", "--out", help="write the report here (default: stdout)")
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

    report = build_report(data)
    if args.out:
        Path(args.out).write_text(report)
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

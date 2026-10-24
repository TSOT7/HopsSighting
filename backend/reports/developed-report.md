# Environmental Impact Report

**Site:** Developed brownfield (Boston metro)  
**Location:** 42.3760, -71.0600 (WGS84)  
**Data coverage:** national+MA  
**Data mode:** Prefilled dataset  
**Data sources:** NLCD, MBTA, MassDEP-21E, GBIF, iNaturalist

---

## Summary

**Final rating: 64.5 / 100 ± 2.3** &mdash; Grade **C** (Moderate: mitigation needed).

The rating runs 0–100, where a higher score indicates lower environmental impact and greater suitability for development. This site scored 64.5, placing it in the **C** band.

The result carries a margin of ±2.3 points, reflecting a data-confidence index of 88 out of 100 (see Section 4).

## Detailed Factor Calculations

### 1. Habitat Integrity (S_H)

Measures how much natural habitat the footprint would destroy, as a weighted sum of the protected habitat types present on the site.

**Formula:** S_H = 100 × (1 − Σ weightᵢ × fractionᵢ)

| Habitat | Weight | Site fraction | Contribution |
|---|---|---|---|
| Wetland | 0.30 | 0% | 0.0000 |
| Priority / BioMap habitat | 0.25 | 0% | 0.0000 |
| Mature forest | 0.20 | 2% | 0.0040 |
| Vernal pool | 0.15 | 0% | 0.0000 |
| Grassland / meadow | 0.10 | 0% | 0.0000 |

**Calculation:** weighted loss = 0.30·0.00 + 0.25·0.00 + 0.20·0.02 + 0.15·0.00 + 0.10·0.00 = 0.0040  
S_H = 100 × (1 − 0.0040) = **99.6**

*Interpretation:* The footprint overlaps little protected habitat, so direct habitat loss is limited.

### 2. Keystone Species Impact (S_K)

Estimates impact on keystone species. Each species module returns a risk from 0 to 1 based on on-site habitat suitability. Species that are implausible for the area are excluded, and the remaining importance weights are renormalized.

**Formula:** S_K = 100 × (1 − Σ importanceⱼ × riskⱼ), over applicable species

**Per-species risk:**

| Species | Risk (0–1) | Importance | Applicable | Basis |
|---|---|---|---|---|
| beaver | 0.000 | 0.40 | no (excluded) | No stream or wetland nearby; beaver habitat implausible. |
| bats | 0.000 | 0.35 | yes | Marginal bat habitat. |
| pollinators | 0.025 | 0.25 | yes | Little pollinator habitat; a planting opportunity rather than a loss. |

**Renormalized weights** (over applicable species): bats = 0.583, pollinators = 0.417.

**Calculation:** weighted risk = 0.583·0.000 + 0.417·0.025 = 0.0104  
S_K = 100 × (1 − 0.0104) = **99.0**

*Interpretation:* Keystone-species pressure is low; the site offers limited habitat for them.

### 3. Connectivity / Fragmentation (S_C)

Measures how embedded the site is within unbroken natural land. A site inside a large intact patch fragments more habitat when developed, which represents higher conservation value.

**Formula:** S_C = 100 × (natural fraction of the surrounding context area)

**Calculation:** natural context fraction = 12%  
S_C = 100 × 0.12 = **12.0**

*Interpretation:* The surrounding area is already fragmented or developed, so additional fragmentation from this site would be limited.

### 4. Carbon & Climate (S_Cb)

Combines carbon lost by clearing tree canopy with proximity to transit (a proxy for avoided vehicle emissions). Each half contributes 50%.

**Formula:** S_Cb = 0.5 × (100 − lin(CO₂ lost; 0, c_max)) + 0.5 × decay(transit distance; d₀)

- Canopy area: 300 m²  
- CO₂ lost = 300 × 12.0 kg/m² × (44/12) = **13200 kg**  
- Carbon component = 100 − lin(13200; 0, 500000) = 97.4  
- Transit distance: 250 m  
- Transit component = decay(250; 800) = 73.2

**Calculation:** S_Cb = 0.5 × 97.4 + 0.5 × 73.2 = **85.3**

*Interpretation:* Little canopy carbon is at stake, and the site is well served by transit.

### 5. Land Reuse (S_L)

Rewards building on already-disturbed land (impervious, developed, brownfield, or agricultural) rather than greenfield.

**Formula:** S_L = 100 × Σ weightᵢ × disturbanceᵢ

| Prior disturbance | Weight | Site value | Contribution |
|---|---|---|---|
| Impervious surface | 0.35 | 80% | 0.2800 |
| Already developed | 0.30 | 95% | 0.2850 |
| Brownfield / landfill | 0.20 | yes | 0.2000 |
| Agriculture | 0.15 | 0% | 0.0000 |

**Calculation:** reuse = 0.35·0.80 + 0.30·0.95 + 0.20·1.00 + 0.15·0.00 = 0.7650  
S_L = 100 × 0.7650 = **76.5**

*Interpretation:* The site is largely previously disturbed, making it a strong reuse candidate with low greenfield impact.

### 6. Regulatory Risk (S_G)

Begins at 100 and subtracts a penalty for each regulatory constraint the site triggers.

**Formula:** S_G = max(0, 100 − Σ penaltyᵣ for each trigger hit)

No regulatory triggers were hit.

**Calculation:** S_G = 100 − 0 = **100.0**

*Interpretation:* The site has low regulatory exposure under the datasets consulted.

## 7. Combining the Sub-scores

The six sub-scores are grouped into three headline categories, then blended into the overall rating (before gating and confidence).

**Grouping (Option D):**

- Ecology = geometric mean of S_H, S_K, S_C = geo(99.6, 99.0, 12.0) = **49.1**  
- Climate = S_Cb = **85.3**  
- Site = mean(S_L, S_G) = (76.5 + 100.0) / 2 = **88.2**

The geometric mean is used for Ecology so that a single very low ecological sub-score cannot be masked by high ones.

**Blend:**

E = 0.50·Ecology + 0.30·Climate + 0.20·Site

E = 0.50·49.1 + 0.30·85.3 + 0.20·88.2 = **67.8**

## 8. Regulatory Hard Gate

No hard regulatory trigger (protected open space, federal critical habitat, or regulated wetland fill) fired, so no cap was applied.

E' = 67.8 (unchanged)

## 9. Data-Confidence Adjustment

The rating is shrunk toward a conservative prior of 40 when data is thin, so that missing or uncertain data never produces a falsely favourable score.

**Confidence index (Q):**

- Survey effort = min(1, 140 / 100) = 1.000  
- Land-cover classification confidence = 0.950  
- Location certainty = 1 − (70 / 1000) = 0.930  
- Q = 100 × 1.000 × 0.950 × 0.930 × 11/11 layers available = **88.3**

**Shrinkage toward the prior:**

E_final = (Q/100)·E' + (1 − Q/100)·40  
E_final = (0.883)·67.8 + (0.117)·40 = **64.5**

The displayed margin of ±2.3 is (100 − Q) / 5.

*Interpretation:* Data confidence is high, so the rating closely reflects the computed sub-scores.

## 10. Recommended Mitigation

- Plant native pollinator habitat on retained open land.

---

## Methodology & Limitations

This report is a screening assessment, not a permit or a substitute for professional ecological or legal review. Sub-score weights, penalties, and thresholds are configurable parameters; the current values are provisional and pending calibration against reference sites. Species presence is estimated from habitat suitability and sighting records, not direct survey. The full model is documented in the project's scoring-model reference.

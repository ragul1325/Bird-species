# Bird Species Observation Analysis — Forest vs. Grassland Ecosystems

**National Capital Region Parks | 2018 Breeding Season Survey**

---

## 1. Project Overview

This analysis consolidates bird monitoring data collected across 11 National Park
Service administrative units in the Washington, D.C. region, comparing species
distribution and diversity between **forest** and **grassland** habitats. The goal
is to surface patterns useful for habitat conservation, land management, and
biodiversity monitoring.

**Data source:** `Bird_Monitoring_Data_FOREST.XLSX` and
`Bird_Monitoring_Data_GRASSLAND.XLSX`, each containing 11 sheets (one per
administrative unit).

**Survey window in the data:** May 7, 2018 – July 19, 2018 (spring/summer
breeding season). The brief references multi-year analysis, but the supplied
files contain a single season; the pipeline is written to handle additional
years automatically if later data is added.

---

## 2. Data Cleaning & Preprocessing

| Step | Detail |
|---|---|
| Consolidation | All 11 sheets per workbook combined; Forest and Grassland combined into one table with a `Location_Type` flag |
| Schema reconciliation | Forest's `NPSTaxonCode` and Grassland's `TaxonCode` merged into one `Taxon_Code` field; `Site_Name` (Forest-only) and `Previously_Obs` (Grassland-only) preserved as nulls where structurally absent |
| Duplicates | **1,705 fully duplicate rows removed** (all from the Grassland workbook) |
| Missing `Sex` | Recoded to explicit `"Not Recorded"` category rather than dropped (8,290 of 15,372 records had no sex recorded — common in audio-ID'd songbirds) |
| Missing `Distance` | Recoded to `"Not Recorded"` (689 records) |
| `Sub_Unit_Code` | Left null — structurally absent for nearly all records, not a data quality issue |
| Date/time fields | Parsed into proper datetime/time objects; derived `Month`, `Month_Name`, `Season`, and `Observation_Duration_Min` |
| Outlier check | Temperature and humidity values all fell within plausible physical ranges — **zero outliers flagged** |

**Result:** 17,077 raw rows → **15,372 cleaned, analysis-ready rows** (29 → 36
columns after derived fields), loaded into both a CSV and a SQLite database
(`bird_observations.db`, table `bird_observations`) for SQL-driven analysis.

---

## 3. Key Findings

### 3.1 Overall diversity is comparable, but habitats favor different species

| Metric | Forest | Grassland |
|---|---|---|
| Total observations | 8,546 | 6,826 |
| Unique species | 108 | 107 |
| Admin units surveyed | 11 | 4 |
| Avg. temperature at observation | 21.9°C | 23.3°C |
| Avg. humidity | 77.8% | 69.7% |

Species *richness* is nearly identical, but *composition* differs sharply.
Forests are dominated by canopy/understory specialists — **Red-eyed Vireo**,
**Carolina Wren**, **Eastern Tufted Titmouse**, **Acadian Flycatcher** — while
grasslands are dominated by open-field and edge species — **Indigo Bunting**,
**Field Sparrow**, **Grasshopper Sparrow**, **Red-winged Blackbird**. Northern
Cardinal and Carolina Wren are the only species that rank in the top 10 for
both habitats, confirming each ecosystem supports a largely distinct bird
community.

![Top species by habitat](outputs/charts/02_top_species.png)

### 3.2 Spatial hotspots

Grassland surveys are concentrated in just 4 units, but **Antietam National
Battlefield (ANTI)** alone accounts for 3,130 grassland observations and 78
species — the single richest site in the dataset. **Monocacy National
Battlefield (MONO)** stands out with 93 species in its grassland plots, the
highest species count of any site/habitat combination. Among forest sites,
**Chesapeake & Ohio Canal NHP (CHOH)** and **Prince William Forest Park
(PRWI)** are the clear hotspots, together contributing over half of all forest
observations.

![Admin unit hotspots](outputs/charts/04_admin_unit_hotspots.png)

### 3.3 Seasonal pattern

The data only spans spring and summer 2018, but within that window activity is
heavily weighted toward summer in forests (6,156 vs. 2,390 spring
observations) — consistent with denser canopy foliage concealing birds early
in spring, and peak breeding-season vocalization by early summer. Grassland
observations are more evenly split between spring (2,474) and summer (4,352).

![Seasonal trends](outputs/charts/03_seasonal_trends.png)

### 3.4 How birds are detected differs by habitat

**Singing** is the dominant identification method in both habitats (Forest
63.5%, Grassland 61.4%), but **visual identification is 3x more common in
grasslands** (20.1% vs. 5.1% in forest) — unsurprising given open sightlines
versus dense forest canopy. Forest birds are correspondingly identified by ear
("Calling") more often.

![ID method by habitat](outputs/charts/05_id_method.png)

### 3.5 Disturbance and detectability

Forest surveys recorded **"no effect" disturbance** more often (56.8% vs.
39.1% in grassland), while grasslands saw a higher share of "slight effect"
disturbance (46.1% vs. 31.5%). This may reflect more variable wind/weather
exposure in open grassland plots affecting observer conditions.

![Disturbance effect](outputs/charts/07_disturbance_effect.png)

### 3.6 Conservation priorities

The **Wood Thrush** (*Hylocichla mustelina*) is by far the most-observed
PIF Watchlist species — 290 sightings in forest plots and 19 in grassland —
making it the top conservation priority to track given its forest dependency.
Grassland-associated **Grasshopper Sparrow** and **Prairie Warbler** are also
notable, as grassland-breeding birds are disproportionately declining
nationally and warrant habitat protection focus at sites like ANTI and MONO.

![Watchlist species](outputs/charts/08_watchlist_species.png)

### 3.7 Observer consistency

Three observers (Elizabeth Oswald, Kimberly Serno, Brian Swimelar) conducted
all surveys across both habitats. Elizabeth Oswald logged the most
observations and the broadest species list in both forest (102 species) and
grassland (98 species), suggesting experience/skill level affects detection
rate — a useful caveat when comparing site-level diversity, since site
differences may partly reflect which observer was assigned there.

---

## 4. Business Use Case Takeaways

- **Wildlife Conservation:** Prioritize Wood Thrush habitat protection in
  forest units (especially CHOH, PRWI) and grassland-breeding sparrow habitat
  at ANTI and MONO.
- **Land Management:** Grassland species composition is concentrated in just
  4 of 11 units — expanding grassland habitat monitoring/restoration to more
  units could reveal additional biodiversity value.
- **Eco-Tourism:** ANTI and MONO (grassland) and CHOH/PRWI (forest) are the
  strongest candidates for birding-tourism promotion given species counts.
- **Policy Support:** Wood Thrush, Grasshopper Sparrow, and Prairie Warbler
  are the clearest data-backed candidates for targeted regional conservation
  policy.

---

## 5. Deliverables

| File | Description |
|---|---|
| `data/bird_observations_clean.csv` | Cleaned, consolidated dataset |
| `data/bird_observations.db` | SQLite database (table: `bird_observations`) |
| `data/cleaning_report.txt` | Cleaning step log |
| `scripts/01_clean_data.py` | Cleaning & consolidation pipeline |
| `scripts/02_eda_sql.py` | SQL-based EDA (14 analysis queries) |
| `scripts/03_visualizations.py` | Static chart generation |
| `outputs/eda_query_results.xlsx` | All SQL query outputs, one sheet each |
| `outputs/charts/*.png` | 10 EDA chart images |
| `dashboard/app.py` | Interactive Streamlit + Plotly dashboard |

### Running the dashboard
```bash
pip install streamlit plotly pandas
cd dashboard
streamlit run app.py
```

---

## 6. Limitations

- Data covers only one breeding season (spring/summer 2018) — no multi-year
  trend analysis is possible with the data provided.
- Grassland surveys cover only 4 of 11 admin units, limiting direct
  habitat-vs-habitat comparison at sites without grassland data.
- Observer identity is confounded with site assignment, which may bias
  apparent differences in per-site species richness.

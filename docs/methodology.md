# Florida Voter Registration, Real Income, and Housing Affordability — Methodology

## Project goal

Quantify how local economic conditions — real income and housing affordability — relate to voter registration patterns, party affiliation, and residential movement across Florida communities (March–May 2026).

## Data sources

| Source | Vintage | Geography | Purpose |
|---|---|---|---|
| Florida Division of Elections voter detail extract | 20260310, 20260414, 20260512 | Voter (67 county files/month) | Registration, party, status, ZIP, age, movement |
| IRS SOI Statistics of Income | Tax years 2020, 2021, 2022 | 5-digit ZIP | Mean AGI per return → income proxy |
| Zillow ZHVI (smoothed, seasonally adjusted) | Monthly back to 2000-01 | 5-digit ZIP | Typical home value, growth rates |
| BLS CPI-U All Items (US City Average) | Monthly 2019-01 to 2026-04 | National | Inflation adjustment for real income |

The Census ACS B19013 median household income table was originally considered, but the Census API requires a registered key. IRS SOI mean AGI per return is used instead as a ZIP-level taxable-income proxy. AGI is not interchangeable with household income, but it provides a consistent public measure for comparing ZIP-level economic context.

HUD ZIP/ZCTA crosswalk was skipped (also requires an API key). All joins use 5-digit residence ZIP, which is consistent across voter records, Zillow, and IRS SOI. Limitations of this choice are documented below.

## Pipeline

```
raw_zips/external/  ──┐
extracted/*/detail/   │
                      ▼
                 DuckDB (Python venv)
                      │
        ┌─────────────┼──────────────────────┐
        ▼             ▼                      ▼
voter_month_snapshot  cpi_monthly      zip_home_values
voter_changes         zip_income       zip_affordability
                      │
                      ▼
              powerbi/*.csv  ──► aggregate dashboard exports
```

All transformation lives in `scripts/`:

| Script | What it does |
|---|---|
| `load_one_county.py` | Loads one detail file as a sanity check. |
| `load_all_months.py` | Loads all 3 months × 67 counties into `voter_month_snapshot` (~48M rows). |
| `build_voter_changes.py` | Pivots per-voter across months; derives presence, new/departure, and mutation flags; adds age band and registration age. |
| `build_external_tables.py` | Loads CPI, IRS SOI, Zillow ZHVI; builds `zip_income`, `zip_home_values`, `zip_affordability`. |
| `export_for_powerbi.py` | Writes privacy-safe aggregated CSVs and a data dictionary to `powerbi/`. |

## Derived measures

**Real income (deflated to May 2026 dollars):**
`real_mean_agi_2026 = nominal_agi × (base_cpi / cpi_year_dec)` where `base_cpi` is the CPI-U for the most recent published month (April 2026 = 333.020 as of this build).

**Home-value-to-income ratio:**
`home_value_to_income_ratio = typical_home_value_latest / mean_agi_per_return`
Higher = local homes cost more per dollar of local income.

**Affordability pressure score (z-score across FL ZIPs):**
`affordability_pressure_score = (ratio - mean(ratio)) / sd(ratio)`
Standardized within Florida so cuts are interpretable against the state, not the nation.

**Affordability bands:**
- 1 low pressure: z < −0.75
- 2 below average: −0.75 ≤ z < −0.25
- 3 average: −0.25 ≤ z < 0.25
- 4 above average: 0.25 ≤ z < 0.75
- 5 high pressure: z ≥ 0.75

**Age band** (as of 2026-05-01): 18-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75+.

**Movement flags** are computed per voter_id across the three monthly snapshots:
- `new_in_april`, `new_in_may`, `new_in_may_only` (presence transitions)
- `missing_after_march`, `missing_after_april` (departures)
- `*_changed_mar_apr`, `*_changed_apr_may` for county, zip, party, status (mutations)

## Privacy approach

The DuckDB database in `duckdb/voter.duckdb` contains row-level voter data and never leaves the local machine.

Only the files in `powerbi/` are intended for external review or dashboarding. They are:
- Aggregated to county, ZIP, party, age band, or affordability band — never to individual voter.
- Suppressed where any cell would describe fewer than 10 underlying voters (in `zip_month_summary`, `zip_party_by_affordability`, `party_by_income_band`).
- Stripped of all PII fields (name, address, birth date, registration date, phone, email).

## Known limitations

1. **ZIP, not ZCTA.** Voter data uses USPS ZIP. Zillow and IRS SOI also use USPS ZIP. The Census ACS uses ZCTAs (slightly different geometry, especially for ZIPs that are PO-box-only or serve a single recipient). For Florida this affects a small minority of ZIPs, and we accept the consistency benefit of joining all three datasets on the same key.
2. **AGI ≠ household income.** IRS AGI excludes some non-taxable income (Social Security portion, some retirement income, certain transfers). It's a strong relative proxy across ZIPs but not directly comparable to ACS B19013 medians.
3. **AGI is per-return, not per-household.** Joint returns count once; some households file multiple returns. The relative ordering across ZIPs is preserved.
4. **Income data is TY 2022.** The most recent SOI vintage. There's a ~3.5 year lag relative to the May 2026 voter snapshot. For tracking real income *trends*, the 2020 vs 2022 comparison is provided (`real_income_growth_2020_2022`).
5. **3 monthly snapshots is a short window.** Movement signals are real but the absolute volume of churn is modest. Findings are most reliable for *patterns* (e.g., which counties churn more, who moves to/from where) rather than projecting annual rates.
6. **April extract anomaly.** April has an extra `20260414_VoterDetail/` nesting layer and 5 voter_id duplicates (likely voters appearing under both old and new county in a mid-extract move). The loader handles both with explicit globs and `ANY_VALUE` deduplication.
7. **Pre-registered voters and address-confidentiality program participants are excluded from the extract by statute.** Our universe is the public extract only.

## Dashboard Export Mapping

The aggregate CSVs in `powerbi/` are organized around the following analytical pages:

| Report page | Primary CSV(s) |
|---|---|
| Executive Summary | `state_executive_summary.csv`, `county_month_summary.csv` |
| Voter Movement | `voter_movement_summary.csv`, `movement_by_age_band.csv` |
| Party Affiliation Patterns | `county_party_age_summary.csv`, `county_month_summary.csv` |
| Income and Registration | `party_by_income_band.csv`, `zip_affordability_export.csv` |
| Housing Affordability | `zip_affordability_export.csv`, `movement_by_affordability.csv`, `zip_party_by_affordability.csv` |
| Methodology | this document, `data_dictionary.csv` |

# Page 6 — Data Quality and Methodology

**Purpose:** document the data sources, field definitions, transformations, privacy choices, duplicate handling, and limitations behind the analysis.

---

## TL;DR

This project transforms ~48M raw voter registration records and ~70M voting history records across 3 monthly extracts into 24 privacy-safe aggregated CSV tables suitable for dashboarding and independent review. Source data is the Florida Division of Elections official voter extract (public records, requested via the standard extract process). All transformation logic is reproducible from `scripts/` against `extracted/`. Individual voter rows live only in the local DuckDB database; no identifiable records are exported. Below is the provenance, transformation, and limitations documentation that supports every other page of this report.

---

## 1. Data Sources

| Source | Vintage | Records | Granularity | Authority |
|---|---|---:|---|---|
| FL voter registration extract (March 2026) | 2026-03-10 | 16,077,003 | Voter row | FL Division of Elections, official monthly extract |
| FL voter registration extract (April 2026) | 2026-04-14 | 16,096,219 | Voter row | FL Division of Elections |
| FL voter registration extract (May 2026) | 2026-05-12 | 16,115,656 | Voter row | FL Division of Elections |
| FL voting history extract (May 2026) | 2026-05-12 | 69,931,186 | Vote event | FL Division of Elections |
| IRS Statistics of Income — ZIP-level | TY 2020, 2021, 2022 | ~2,800 FL rows × 3 years | ZIP × income bracket | IRS, public free download |
| Zillow Home Value Index (ZHVI), ZIP-level | Monthly 2000-01 to 2026-04 | ~280K FL rows | ZIP × month | Zillow Research, free download |
| BLS CPI-U All Items, US City Average | Monthly 2019-01 to 2026-04 | 87 records | National × month | BLS Public Data API |

All sources documented in [`docs/methodology.md`](../methodology.md). Voter extract layout described in [`docs/FINAL Voter Extract Disk File Layout rev 20260504.pdf`](../FINAL%20Voter%20Extract%20Disk%20File%20Layout%20rev%2020260504.pdf).

---

## 2. Field Definitions (Voter Registration Extract)

38 tab-delimited fields per record, no header row. Full definitions follow the May 2026 Florida layout PDF (page 2-3); summarized:

| # | Field | Type | Notes |
|---:|---|---|---|
| 1 | County Code | 3-char | DAD=Miami-Dade, MRN=Marion, etc. |
| 2 | Voter ID | 10-digit | Stable across moves and party changes |
| 3-6 | Name | Strings | Suppressed for public-records-exempt voters |
| 7 | Public Records Exemption | Y/N | If Y, protected fields (3-6, 8-19, 22, 25-28, 30-38) are blank |
| 8-12 | Residence Address | Strings | Used for ZIP-based joins |
| 13-19 | Mailing Address | Strings | Often blank; used only when different from residence |
| 20 | Gender | F/M/U | Self-reported at registration |
| 21 | Race | Single digit code | See the official Florida voter extract layout PDF in `docs/`. |
| 22 | Birth Date | MM/DD/YYYY | "*" or blank for protected/exempt voters |
| 23 | Registration Date | MM/DD/YYYY | First registered in FL |
| 24 | Party Affiliation | 3-char | DEM, REP, NPA, IND, AMF, etc. |
| 25-28 | Precinct | Strings | Local geographic identifier |
| 29 | Voter Status | ACT/INA | Active or Inactive |
| 30-34 | Districts | Numeric | Congressional, House, Senate, Co Commission, School Board |
| 35-37 | Phone | Numeric | Often blank |
| 38 | Email | String | Often blank |

**Voting History Extract** (5 fields):
1. County Code (3)
2. Voter ID (10)
3. Election Date (MM/DD/YYYY)
4. Election Type (PPP, PRI, RUN, GEN, OTH)
5. History Code (A/B/E/L/N/P/Y — see Page 5 for definitions)

---

## 3. Transformations

The pipeline runs entirely in Python + DuckDB via the scripts in [`scripts/`](../../scripts/):

```
scripts/load_one_county.py            sanity-load one file
scripts/load_all_months.py            48.3M-row voter_month_snapshot
scripts/load_voting_history.py        70M-row voter_history
scripts/build_voter_changes.py        16.2M-row voter_changes panel
scripts/build_external_tables.py      CPI + IRS SOI + Zillow → income/value/affordability
scripts/analyze_movers.py             224K-event movers analysis
scripts/analyze_historical_pressure.py per-ZIP historical metrics + voter joins
scripts/build_voting_history_exports.py  Page-5 aggregates
scripts/export_for_powerbi.py         10 base aggregated CSVs to powerbi/
```

Run order:
```
1. load_all_months.py        (10 min)
2. load_voting_history.py    (15 min)
3. build_voter_changes.py    (5 min)
4. build_external_tables.py  (3 min, requires downloads in raw_zips/external/)
5. analyze_movers.py         (5 min)
6. analyze_historical_pressure.py (3 min)
7. build_voting_history_exports.py (10 min)
8. export_for_powerbi.py     (3 min)
```

Total wall-clock: ~50 minutes on an M-series Mac Mini. The DuckDB database file is ~6 GB.

**No row-level intermediate files are written.** All transformation happens inside `duckdb/voter.duckdb`. Only the privacy-safe aggregates in `powerbi/` ever leave that database.

---

## 4. Duplicate Handling

| Place | Issue observed | Resolution |
|---|---|---|
| April voter detail extract | 5 voter_ids appear twice (out of 16.1M) | `ANY_VALUE(...)` deduplication when building per-voter per-month view |
| All extracts | Trailing whitespace in fields | Implicit during VARCHAR storage; explicit `TRIM()` only when comparing |
| Voting history | 0.1-0.5% of voters have >5 GEN history rows for 2016-2024 (legacy IDs) | Acknowledged in Page 5 methodology section; not corrected |
| ZIP code field | Some 9-digit ZIP+4 entries | Truncated to 5 digits during loading where needed |
| Multiple race-or-party-code synonyms | None observed; codes are strictly enumerated | Validated via `SELECT DISTINCT race FROM voter_month_snapshot;` |
| Date parsing | Public-records-exempt voters have `*` instead of dates | `TRY_STRPTIME()` returns NULL, age computation handles NULL gracefully |

---

## 5. Privacy Choices

The single most important architectural decision in this project: **row-level voter data never leaves the local DuckDB database.**

Rules applied:
1. **No individual voter rows in any CSV in `powerbi/`.** Every export is aggregated to at least (county × party × status) granularity.
2. **No PII in any export.** Names, addresses, birth dates, registration dates, phone numbers, and email addresses are not selected into export queries.
3. **Small-cell suppression** at the ZIP level: any aggregate cell with fewer than 10 underlying voters is dropped from the export (applied to `zip_month_summary`, `zip_party_by_affordability`, `party_by_income_band`, and all `movers_*` exports).
4. **Coarse age bands instead of birth date or exact age.** Buckets are 18-24, 25-34, 35-44, 45-54, 55-64, 65-74, 75+. No exact ages or birth years appear in exports.
5. **County-level rollups for any sensitive demographic intersection.** Race × Party shown at state level, not ZIP level.
6. **Dashboard publication check:** confirm that only aggregate `powerbi/` CSVs are loaded into any external dashboard and that no row-level source is connected.

These choices follow standard practice for any analysis derived from public voter files: the *data is public*, but **the assemblage and presentation matter**. A reasonable bystander can re-derive any number on the dashboard from the public Florida extract — but the dashboard itself never expresses anything individual.

---

## 6. Joins and Matching Assumptions

| Join | Key | Assumption |
|---|---|---|
| `voter_month_snapshot` across months | `voter_id` | Stable identifier across moves, party changes, status flips |
| `voter_changes` ← `voter_month_snapshot` | `voter_id` | Same as above |
| `voter_history` → `voter_changes` | `voter_id` | History rows reflect current county; we attach current party/age/race |
| `voter_*` → `zip_income` / `zip_home_values` | `residence_zipcode` (5-digit) | ZIP from voter file ≈ ZIP in Zillow / IRS SOI. Mismatches occur for: PO Box-only ZIPs (no Zillow data), unique-recipient ZIPs (no IRS data), ZIP+4 issues. ~10% of voter ZIPs do not match into both external datasets and appear as "unknown" income/affordability band. |
| `zip_income` (real terms) → `cpi_monthly` | December CPI of the tax year | Standard practice for annual income deflation |
| CPI deflation base | April 2026 = 333.020 | Most recent published month at time of build |

---

## 7. Limitations Matrix

| Category | Limitation | Severity | Mitigation |
|---|---|---|---|
| **Temporal coverage** | Only 3 monthly snapshots (Mar/Apr/May 2026) | High | Use for cross-sectional + short-window dynamic analysis only; do not project annual trends |
| **No individual income** | Voter file lacks income; we use ZIP-level mean AGI as proxy | High | Document clearly; any "wealth" finding is area-level, not individual |
| **Race coding** | Self-reported, single-digit codes; "Hispanic" conflated with race | Medium | Display race exactly as reported; document scheme |
| **ZIP vs ZCTA** | We use 5-digit residence ZIP throughout; some ZIPs have no ZCTA equivalent | Low | Most FL ZIPs map cleanly; PO Box ZIPs are minority |
| **History survivorship** | Voting history reflects only voters currently in FL; movers-in/out create bias | Medium | Caveat all cross-cycle comparisons; do not present as "what FL voters did" |
| **Census API requires key** | Originally planned ACS B19013 unavailable without registration | Low | Substituted IRS SOI mean AGI per return as a ZIP-level taxable-income proxy; documented in methodology |
| **HUD ZIP/ZCTA crosswalk requires key** | Crosswalk skipped | Low | Joined on 5-digit ZIP throughout; loss is minor |
| **April detail nesting quirk** | `20260414_VoterDetail/` subfolder + `VerificationFiles/` exclusion | Low | Handled explicitly in `load_all_months.py` |
| **April voter_id duplicates** | 5 duplicate voter_ids in April (out of 16.1M) | Negligible | `ANY_VALUE(...)` dedup in pipeline |
| **Active/Inactive churn timing** | 109K Active→Inactive in 8 weeks likely reflects NVRA cycle | Low | Explained on Page 1; treated as administrative artifact |
| **Hardee County −16.4% loss** | Anomalous; almost certainly a list-maintenance purge | Low | Footnoted on Page 1 and Page 2; not removed from data |
| **3-month party-change rate (~0.48%)** | Annualizes to ~2-3% — too short to study annual partisan churn | Medium | Use for movement rate comparisons across subgroups, not for absolute prediction |
| **Public-records-exempt voters** | ~5-10% of voters have blank names, addresses, birth dates | Low | Treated as "unknown" in derived bands; party/county still visible |
| **Florida-only universe** | Cannot compare to other states | N/A by design | Documented as scope |

---

## 8. Reproducibility

The analysis can be rebuilt from scratch as follows:

1. **Acquire data:**
   - Voter extracts for 20260310, 20260414, 20260512 from the FL Division of Elections extract program (annual fee or per-extract; standard process).
   - Run `scripts/build_external_tables.py` after downloading the external data files listed in its docstring.
2. **Install:** `python3 -m venv .venv && .venv/bin/pip install duckdb pandas pyarrow`.
3. **Run pipeline:** `for s in scripts/load_*.py scripts/build_*.py scripts/analyze_*.py scripts/export_*.py; do .venv/bin/python $s; done`.
4. **Inspect:** open `duckdb/voter.duckdb` in any DuckDB client; or open the CSVs in `powerbi/`.
5. **Refresh dashboard exports:** reload the updated aggregate CSVs from `powerbi/`.

End-to-end wall time: ~50 minutes on M-series Mac with 16 GB RAM.

---

## 9. What's Out of Scope (and what would be needed to extend it)

| Out of scope | Would require |
|---|---|
| Individual longitudinal income/wealth trajectories | Linked tax + voter data (would require special data use agreement; politically and legally sensitive) |
| Multi-year partisan trend lines | 5-10 years of monthly extracts (each costs money + storage) |
| Causal identification of "did house value affect party choice" | Quasi-experimental design (panel methods + natural experiment) |
| Turnout prediction for next election | Modeling layer (e.g., regression on history + demographics) — out of scope for descriptive dashboard |
| Cross-state comparisons | Acquire equivalent extracts from other states; varies dramatically by state |
| Election outcome predictions | Voter registration ≠ vote choice; would need polling + outcome data |

---

## 10. Acknowledgments and References

- **Florida Division of Elections** — for publishing the official extract under public-records statutes (Ch. 119, Florida Statutes). Layout documentation: `docs/FINAL Voter Extract Disk File Layout rev 20260504.pdf`.
- **IRS Statistics of Income** — ZIP-level tax-return summaries, free public download (https://www.irs.gov/statistics/soi-tax-stats-individual-income-tax-statistics-zip-code-data-soi).
- **Zillow Research** — Home Value Index, ZIP-level monthly series (https://www.zillow.com/research/data/).
- **U.S. Bureau of Labor Statistics** — CPI-U All Items series CUUR0000SA0 (https://api.bls.gov).
- **DuckDB** — the analytical database engine that makes 100M-row joins fast enough to do on a Mac Mini.

---

*This page is intentionally detailed because the source, privacy, and limitation choices determine how the descriptive findings should be interpreted.*

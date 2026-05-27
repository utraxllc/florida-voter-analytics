# Florida Voter Registration, Real Income, and Housing Affordability Analytics

This repository contains a reproducible descriptive analysis of Florida voter-registration patterns, ZIP-level income proxies, home-value change, and housing-affordability pressure. It processes approximately 48 million voter-registration records and 70 million voting-history events across the March, April, and May 2026 Florida voter extracts, then joins those records to public IRS SOI, Zillow ZHVI, and BLS CPI data.

The public repository contains code, methodology, and aggregated outputs only. Row-level voter records, source extracts, local DuckDB files, and other raw data are excluded.

## Research Questions

- How did Florida's registered-voter base change between March and May 2026?
- Which counties and party groups account for short-window registration growth, departures, and party-affiliation changes?
- How are ZIP-level taxable-income proxies, home values, and affordability pressure associated with party affiliation?
- How does long-run home-value appreciation relate to current party-registration composition?
- How did vote-method patterns shift around the 2020 election cycle?
- What privacy boundaries are needed when public voter records are joined with public economic data?

## Project Workflow

1. Load 67 county files across three monthly voter-detail extracts into a local DuckDB analytical database.
2. Clean known extract anomalies, including April directory nesting, five duplicate voter IDs, and masked values for public-records-exempt voters.
3. Pivot monthly snapshots into a per-voter panel with presence, movement, status-change, ZIP-change, and party-change flags.
4. Join residence ZIPs to IRS SOI mean AGI per return, Zillow ZHVI, and BLS CPI to derive real-income proxies, home-value-to-income ratios, and affordability-pressure bands.
5. Aggregate to county, ZIP, age-band, party, voting-history, income, and affordability tables.
6. Export privacy-safe CSVs under `powerbi/` for dashboarding and independent review.

## Tech Stack

| Layer | Tool | Role |
|---|---|---|
| Storage / analytical engine | DuckDB | Local columnar database for large joins and aggregations |
| Pipeline | Python | Reproducible extraction, loading, transformation, and export scripts |
| Data manipulation | SQL, pandas, pyarrow | Structured transformations and CSV/Parquet handling |
| Dashboard outputs | Aggregate CSVs | Privacy-safe reporting layer |

## Repository Structure

```text
Voter/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── scripts/
│   ├── load_one_county.py
│   ├── load_all_months.py
│   ├── load_voting_history.py
│   ├── build_voter_changes.py
│   ├── build_external_tables.py
│   ├── analyze_movers.py
│   ├── analyze_historical_pressure.py
│   ├── build_voting_history_exports.py
│   └── export_for_powerbi.py
├── docs/
│   ├── methodology.md
│   ├── findings_preview.md
│   ├── report_pages/
│   │   ├── page1_executive_overview.md
│   │   ├── page2_party_and_county_trends.md
│   │   ├── page3_voter_lifecycle.md
│   │   ├── page4_demographic_segments.md
│   │   ├── page5_voting_history.md
│   │   └── page6_data_quality_methodology.md
│   └── FINAL Voter Extract Disk File Layout rev 20260504.pdf
├── powerbi/
├── duckdb/       # local analytical database, not committed
├── raw_zips/     # source archives, not committed
└── extracted/    # unzipped voter extracts, not committed
```

## Local Rebuild

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/load_all_months.py
.venv/bin/python scripts/load_voting_history.py
.venv/bin/python scripts/build_voter_changes.py
.venv/bin/python scripts/build_external_tables.py
.venv/bin/python scripts/analyze_movers.py
.venv/bin/python scripts/analyze_historical_pressure.py
.venv/bin/python scripts/build_voting_history_exports.py
.venv/bin/python scripts/export_for_powerbi.py
```

Rebuilding requires separately obtained Florida Division of Elections voter extracts and the public external data described in [docs/methodology.md](docs/methodology.md). The source extracts and local database are intentionally ignored by Git.

## Privacy Boundary

Florida voter extracts are public records, but joined and reshaped public data still carries re-identification risk. This repository uses a strict publication boundary:

- No individual voter rows are committed.
- No names, addresses, exact birth dates, phone numbers, or email addresses are exported.
- ZIP-level aggregate files apply small-cell suppression where relevant.
- Exact ages are converted to broad age bands.
- Row-level detail remains local in `duckdb/voter.duckdb`, which is ignored by Git.

## Current Findings

See [docs/findings_preview.md](docs/findings_preview.md) for tables and supporting detail. Current descriptive findings include:

- Florida had 16.12 million registered voters in the May 2026 extract, with REP at 38.6%, DEM at 31.0%, NPA at 27.0%, and other parties at 3.4%.
- The March-to-May window shows 99,158 new registrations, 60,505 departures, 224,834 ZIP-change events, and 77,025 party-affiliation changes.
- Move direction by ZIP-level income proxy is weakly associated with party composition among movers.
- Race, age, and county context show stronger descriptive associations with party registration than short-window move direction.
- Long-run ZIP home-value appreciation is strongly associated with current party-registration composition.
- High-appreciation ZIPs show lower short-window movement and party-change rates than lower-appreciation ZIPs.

These findings are descriptive. They should not be read as causal estimates of individual income, wealth, or vote choice.

## Documentation

- [docs/methodology.md](docs/methodology.md) — data sources, pipeline, derived measures, privacy rules, and limitations.
- [docs/findings_preview.md](docs/findings_preview.md) — current descriptive findings and aggregate tables.
- [docs/report_pages/](docs/report_pages/) — page-level analysis notes for dashboard review.

## License

This project is released under the [MIT License](LICENSE).

The voter extract data itself is public under Florida law but is not redistributed in this repository. Reproduction requires obtaining source extracts directly from the Florida Division of Elections.

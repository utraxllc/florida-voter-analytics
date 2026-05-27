"""Export privacy-safe aggregated tables for dashboarding.

All outputs go to powerbi/ and contain NO individual-voter rows. The lowest
cardinality bucket is (county, party, status) or (zip, party). Any aggregate
with fewer than `MIN_CELL` underlying voters is suppressed to limit re-identification
risk for very small ZIPs.

Outputs:

  county_month_summary.csv         voters by county x month x party x status
  county_party_age_summary.csv     voters by county x party x age_band (last-known)
  zip_month_summary.csv            voters by zip x month x party (suppressed if <MIN_CELL)
  voter_movement_summary.csv       movement flag counts by county x party
  movement_by_age_band.csv         movement flag counts by age band
  movement_by_affordability.csv    movement flag counts by affordability band
  zip_affordability_export.csv     zip-level affordability, income, home values
  zip_party_by_affordability.csv   party share by affordability band x age_band
  party_by_income_band.csv         party share by income band
  state_executive_summary.csv      headline KPIs for the cover page
  data_dictionary.csv              one row per exported file/column with description
"""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"
OUT_DIR = PROJECT_ROOT / "powerbi"

MIN_CELL = 10  # suppress aggregates with fewer than this many underlying voters


def export(con: duckdb.DuckDBPyConnection, name: str, sql: str) -> int:
    """Run sql and write the result to powerbi/<name>.csv. Returns row count."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{name}.csv"
    # Use COPY to write CSV with header.
    con.execute(f"COPY ({sql}) TO '{out_path}' (HEADER, DELIMITER ',')")
    (rows,) = con.execute(f"SELECT COUNT(*) FROM ({sql}) sub").fetchone()
    print(f"  wrote {out_path.name}: {rows:,} rows")
    return rows


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== county_month_summary ===")
    export(
        con,
        "county_month_summary",
        """
        SELECT
            extract_month,
            county_code,
            party_affiliation,
            voter_status,
            COUNT(*) AS voter_count
        FROM voter_month_snapshot
        GROUP BY 1,2,3,4
        ORDER BY 1,2,3,4
        """,
    )

    print("=== county_party_age_summary (last-known per voter) ===")
    export(
        con,
        "county_party_age_summary",
        """
        SELECT
            county_last_known AS county_code,
            party_last_known  AS party_affiliation,
            age_band,
            COUNT(*) AS voter_count
        FROM voter_changes
        WHERE county_last_known IS NOT NULL
        GROUP BY 1,2,3
        ORDER BY 1,2,3
        """,
    )

    print("=== zip_month_summary (suppress small cells) ===")
    export(
        con,
        "zip_month_summary",
        f"""
        SELECT
            extract_month,
            residence_zipcode AS zip_code,
            party_affiliation,
            COUNT(*) AS voter_count
        FROM voter_month_snapshot
        WHERE residence_zipcode IS NOT NULL
          AND LENGTH(residence_zipcode) >= 5
        GROUP BY 1,2,3
        HAVING COUNT(*) >= {MIN_CELL}
        ORDER BY 1,2,3
        """,
    )

    print("=== voter_movement_summary (county x party) ===")
    export(
        con,
        "voter_movement_summary",
        """
        SELECT
            county_last_known AS county_code,
            party_last_known  AS party_affiliation,
            COUNT(*) AS voters,
            SUM(CAST(new_in_april AS INT))           AS new_in_april,
            SUM(CAST(new_in_may AS INT))             AS new_in_may,
            SUM(CAST(missing_after_march AS INT))    AS missing_after_march,
            SUM(CAST(missing_after_april AS INT))    AS missing_after_april,
            SUM(CAST(zip_changed_mar_apr AS INT))    AS zip_changed_mar_apr,
            SUM(CAST(zip_changed_apr_may AS INT))    AS zip_changed_apr_may,
            SUM(CAST(county_changed_mar_apr AS INT)) AS county_changed_mar_apr,
            SUM(CAST(county_changed_apr_may AS INT)) AS county_changed_apr_may,
            SUM(CAST(party_changed_mar_apr AS INT))  AS party_changed_mar_apr,
            SUM(CAST(party_changed_apr_may AS INT))  AS party_changed_apr_may,
            SUM(CAST(status_changed_mar_apr AS INT)) AS status_changed_mar_apr,
            SUM(CAST(status_changed_apr_may AS INT)) AS status_changed_apr_may
        FROM voter_changes
        WHERE county_last_known IS NOT NULL
        GROUP BY 1,2
        ORDER BY 1,2
        """,
    )

    print("=== movement_by_age_band ===")
    export(
        con,
        "movement_by_age_band",
        """
        SELECT
            age_band,
            party_last_known AS party_affiliation,
            COUNT(*) AS voters,
            SUM(CAST(new_in_april AS INT) + CAST(new_in_may AS INT))         AS new_registrations,
            SUM(CAST(missing_after_march AS INT) + CAST(missing_after_april AS INT)) AS departures,
            SUM(CAST(zip_changed_mar_apr AS INT) + CAST(zip_changed_apr_may AS INT)) AS zip_changes,
            SUM(CAST(county_changed_mar_apr AS INT) + CAST(county_changed_apr_may AS INT)) AS county_changes,
            SUM(CAST(party_changed_mar_apr AS INT) + CAST(party_changed_apr_may AS INT)) AS party_changes,
            SUM(CAST(status_changed_mar_apr AS INT) + CAST(status_changed_apr_may AS INT)) AS status_changes
        FROM voter_changes
        GROUP BY 1,2
        ORDER BY 1,2
        """,
    )

    print("=== movement_by_affordability ===")
    export(
        con,
        "movement_by_affordability",
        """
        SELECT
            COALESCE(a.affordability_band, 'unknown') AS affordability_band,
            COALESCE(v.party_last_known, 'unknown')   AS party_affiliation,
            COUNT(*) AS voters,
            SUM(CAST(v.new_in_april AS INT) + CAST(v.new_in_may AS INT))         AS new_registrations,
            SUM(CAST(v.missing_after_march AS INT) + CAST(v.missing_after_april AS INT)) AS departures,
            SUM(CAST(v.zip_changed_mar_apr AS INT) + CAST(v.zip_changed_apr_may AS INT)) AS zip_changes,
            SUM(CAST(v.county_changed_mar_apr AS INT) + CAST(v.county_changed_apr_may AS INT)) AS county_changes,
            SUM(CAST(v.party_changed_mar_apr AS INT) + CAST(v.party_changed_apr_may AS INT)) AS party_changes
        FROM voter_changes v
        LEFT JOIN zip_affordability a
          ON v.zip_last_known = a.zip_code
        GROUP BY 1,2
        ORDER BY 1,2
        """,
    )

    print("=== zip_affordability_export ===")
    export(
        con,
        "zip_affordability_export",
        """
        SELECT
            a.zip_code,
            h.city,
            h.county,
            h.metro,
            a.mean_agi_per_return,
            a.real_mean_agi_2026,
            a.income_band,
            a.typical_home_value_latest,
            a.home_value_yoy_change,
            a.home_value_5yr_change,
            a.real_income_growth_2020_2022,
            a.home_value_to_income_ratio,
            a.affordability_pressure_score,
            a.affordability_band
        FROM zip_affordability a
        LEFT JOIN (
            SELECT DISTINCT zip_code, city, county, metro
            FROM zip_home_values
        ) h USING (zip_code)
        ORDER BY a.zip_code
        """,
    )

    print("=== zip_party_by_affordability_age ===")
    export(
        con,
        "zip_party_by_affordability",
        f"""
        SELECT
            COALESCE(a.affordability_band, 'unknown') AS affordability_band,
            v.age_band,
            v.party_last_known AS party_affiliation,
            COUNT(*) AS voters
        FROM voter_changes v
        LEFT JOIN zip_affordability a
          ON v.zip_last_known = a.zip_code
        WHERE v.party_last_known IS NOT NULL
        GROUP BY 1,2,3
        HAVING COUNT(*) >= {MIN_CELL}
        ORDER BY 1,2,3
        """,
    )

    print("=== party_by_income_band ===")
    export(
        con,
        "party_by_income_band",
        f"""
        SELECT
            COALESCE(i.income_band, 'unknown') AS income_band,
            v.party_last_known AS party_affiliation,
            COUNT(*) AS voters
        FROM voter_changes v
        LEFT JOIN zip_income i
          ON v.zip_last_known = i.zip_code AND i.tax_year = 2022
        WHERE v.party_last_known IS NOT NULL
        GROUP BY 1,2
        HAVING COUNT(*) >= {MIN_CELL}
        ORDER BY 1,2
        """,
    )

    print("=== state_executive_summary (headline KPIs) ===")
    export(
        con,
        "state_executive_summary",
        """
        WITH per_month AS (
            SELECT extract_month, COUNT(*) AS voters,
                   SUM(CASE WHEN voter_status = 'ACT' THEN 1 ELSE 0 END) AS active_voters,
                   SUM(CASE WHEN party_affiliation = 'DEM' THEN 1 ELSE 0 END) AS dem,
                   SUM(CASE WHEN party_affiliation = 'REP' THEN 1 ELSE 0 END) AS rep,
                   SUM(CASE WHEN party_affiliation = 'NPA' THEN 1 ELSE 0 END) AS npa,
                   SUM(CASE WHEN party_affiliation NOT IN ('DEM','REP','NPA') THEN 1 ELSE 0 END) AS other
            FROM voter_month_snapshot
            GROUP BY extract_month
        ),
        moves AS (
            SELECT
                SUM(CAST(new_in_april AS INT))           AS new_in_april,
                SUM(CAST(new_in_may AS INT))             AS new_in_may,
                SUM(CAST(missing_after_march AS INT))    AS missing_after_march,
                SUM(CAST(missing_after_april AS INT))    AS missing_after_april,
                SUM(CAST(zip_changed_mar_apr AS INT))    AS zip_changes_mar_apr,
                SUM(CAST(zip_changed_apr_may AS INT))    AS zip_changes_apr_may,
                SUM(CAST(county_changed_mar_apr AS INT)) AS county_changes_mar_apr,
                SUM(CAST(county_changed_apr_may AS INT)) AS county_changes_apr_may,
                SUM(CAST(party_changed_mar_apr AS INT))  AS party_changes_mar_apr,
                SUM(CAST(party_changed_apr_may AS INT))  AS party_changes_apr_may
            FROM voter_changes
        )
        SELECT
            (SELECT voters FROM per_month WHERE extract_month = '2026-03') AS voters_march,
            (SELECT voters FROM per_month WHERE extract_month = '2026-04') AS voters_april,
            (SELECT voters FROM per_month WHERE extract_month = '2026-05') AS voters_may,
            (SELECT active_voters FROM per_month WHERE extract_month = '2026-05') AS active_voters_may,
            (SELECT dem FROM per_month WHERE extract_month = '2026-05') AS dem_may,
            (SELECT rep FROM per_month WHERE extract_month = '2026-05') AS rep_may,
            (SELECT npa FROM per_month WHERE extract_month = '2026-05') AS npa_may,
            (SELECT other FROM per_month WHERE extract_month = '2026-05') AS other_party_may,
            m.*
        FROM moves m
        """,
    )

    print("=== writing data_dictionary.csv ===")
    dictionary = [
        ("county_month_summary.csv", "extract_month, county_code, party_affiliation, voter_status, voter_count",
         "Voter counts by county x month x party x status. Lowest-grain aggregate, no suppression needed."),
        ("county_party_age_summary.csv", "county_code, party_affiliation, age_band, voter_count",
         "Voters by county x party x age band using the voter's last-known affiliation/county."),
        ("zip_month_summary.csv", "extract_month, zip_code, party_affiliation, voter_count",
         f"Voters by ZIP x month x party. Cells with <{MIN_CELL} voters are suppressed."),
        ("voter_movement_summary.csv", "county_code, party_affiliation, voters, new_in_*, missing_after_*, zip_changed_*, county_changed_*, party_changed_*, status_changed_*",
         "Movement flag counts aggregated by county and party. Use for movement maps and county-level churn metrics."),
        ("movement_by_age_band.csv", "age_band, party_affiliation, voters, new_registrations, departures, zip_changes, county_changes, party_changes, status_changes",
         "Total movement events by age band and party — used for cohort comparisons."),
        ("movement_by_affordability.csv", "affordability_band, party_affiliation, voters, new_registrations, departures, zip_changes, county_changes, party_changes",
         "Movement events by ZIP-level affordability pressure band — answers the housing pressure question."),
        ("zip_affordability_export.csv", "zip_code, city, county, metro, mean_agi_per_return, real_mean_agi_2026, income_band, typical_home_value_latest, home_value_yoy_change, home_value_5yr_change, real_income_growth_2020_2022, home_value_to_income_ratio, affordability_pressure_score, affordability_band",
         "One row per Florida ZIP with income (IRS SOI TY 2022), home values (Zillow ZHVI latest), and derived affordability metrics."),
        ("zip_party_by_affordability.csv", "affordability_band, age_band, party_affiliation, voters",
         f"Party share by affordability x age band. Cells <{MIN_CELL} suppressed."),
        ("party_by_income_band.csv", "income_band, party_affiliation, voters",
         f"Party share by ZIP-level mean-AGI income band. Cells <{MIN_CELL} suppressed."),
        ("state_executive_summary.csv", "voters_*, active_voters_may, dem_may, rep_may, npa_may, other_party_may, new_in_*, missing_after_*, *_changes_*",
         "Single-row KPI strip for the report cover page."),
    ]
    with (OUT_DIR / "data_dictionary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "columns", "description"])
        for r in dictionary:
            w.writerow(r)
    print(f"  wrote data_dictionary.csv: {len(dictionary)} rows")

    print("\nfiles in powerbi/:")
    for p in sorted(OUT_DIR.glob("*.csv")):
        size_kb = p.stat().st_size / 1024
        print(f"  {p.name:<42}  {size_kb:>10,.1f} KB")


if __name__ == "__main__":
    main()

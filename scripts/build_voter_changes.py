"""Derive the voter_changes table from voter_month_snapshot.

One row per voter_id with flags describing:
  - presence per month (appeared_in_*)
  - new arrivals (new_in_april, new_in_may)
  - departures (missing_after_march, missing_after_april)
  - mutation flags (zip_changed, county_changed, party_changed, status_changed)

Also derives an age_band from birth_date and a registration_age (years between
registration_date and 2026-05-01) for downstream joins.

Handles the small number of duplicate (voter_id, extract_month) pairs in the
April extract by picking the lexically-first source_file deterministically.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    print("creating dedup'd per-month voter snapshot view ...")
    con.execute(
        """
        CREATE OR REPLACE TEMPORARY VIEW v_dedup AS
        SELECT
            extract_month,
            voter_id,
            ANY_VALUE(county_code)        AS county_code,
            ANY_VALUE(residence_zipcode)  AS residence_zipcode,
            ANY_VALUE(party_affiliation)  AS party_affiliation,
            ANY_VALUE(voter_status)       AS voter_status,
            ANY_VALUE(birth_date)         AS birth_date,
            ANY_VALUE(registration_date)  AS registration_date,
            ANY_VALUE(gender)             AS gender,
            ANY_VALUE(race)               AS race
        FROM voter_month_snapshot
        GROUP BY extract_month, voter_id
        """
    )

    print("pivoting per voter ...")
    con.execute("DROP TABLE IF EXISTS voter_changes")
    con.execute(
        """
        CREATE TABLE voter_changes AS
        WITH per_voter AS (
            SELECT
                voter_id,
                MAX(CASE WHEN extract_month = '2026-03' THEN county_code END) AS county_mar,
                MAX(CASE WHEN extract_month = '2026-04' THEN county_code END) AS county_apr,
                MAX(CASE WHEN extract_month = '2026-05' THEN county_code END) AS county_may,
                MAX(CASE WHEN extract_month = '2026-03' THEN residence_zipcode END) AS zip_mar,
                MAX(CASE WHEN extract_month = '2026-04' THEN residence_zipcode END) AS zip_apr,
                MAX(CASE WHEN extract_month = '2026-05' THEN residence_zipcode END) AS zip_may,
                MAX(CASE WHEN extract_month = '2026-03' THEN party_affiliation END) AS party_mar,
                MAX(CASE WHEN extract_month = '2026-04' THEN party_affiliation END) AS party_apr,
                MAX(CASE WHEN extract_month = '2026-05' THEN party_affiliation END) AS party_may,
                MAX(CASE WHEN extract_month = '2026-03' THEN voter_status END) AS status_mar,
                MAX(CASE WHEN extract_month = '2026-04' THEN voter_status END) AS status_apr,
                MAX(CASE WHEN extract_month = '2026-05' THEN voter_status END) AS status_may,
                MAX(birth_date)        AS birth_date,
                MAX(registration_date) AS registration_date,
                MAX(gender)            AS gender,
                MAX(race)              AS race
            FROM v_dedup
            GROUP BY voter_id
        )
        SELECT
            voter_id,
            -- presence flags
            county_mar IS NOT NULL AS appeared_in_march,
            county_apr IS NOT NULL AS appeared_in_april,
            county_may IS NOT NULL AS appeared_in_may,
            -- new arrivals
            (county_mar IS NULL AND county_apr IS NOT NULL) AS new_in_april,
            (county_apr IS NULL AND county_may IS NOT NULL) AS new_in_may,
            (county_mar IS NULL AND county_apr IS NULL AND county_may IS NOT NULL) AS new_in_may_only,
            -- departures
            (county_mar IS NOT NULL AND county_apr IS NULL) AS missing_after_march,
            (county_apr IS NOT NULL AND county_may IS NULL) AS missing_after_april,
            -- mutations across consecutive months (only when present in both)
            (county_mar IS DISTINCT FROM county_apr AND county_mar IS NOT NULL AND county_apr IS NOT NULL) AS county_changed_mar_apr,
            (county_apr IS DISTINCT FROM county_may AND county_apr IS NOT NULL AND county_may IS NOT NULL) AS county_changed_apr_may,
            (zip_mar IS DISTINCT FROM zip_apr AND zip_mar IS NOT NULL AND zip_apr IS NOT NULL) AS zip_changed_mar_apr,
            (zip_apr IS DISTINCT FROM zip_may AND zip_apr IS NOT NULL AND zip_may IS NOT NULL) AS zip_changed_apr_may,
            (party_mar IS DISTINCT FROM party_apr AND party_mar IS NOT NULL AND party_apr IS NOT NULL) AS party_changed_mar_apr,
            (party_apr IS DISTINCT FROM party_may AND party_apr IS NOT NULL AND party_may IS NOT NULL) AS party_changed_apr_may,
            (status_mar IS DISTINCT FROM status_apr AND status_mar IS NOT NULL AND status_apr IS NOT NULL) AS status_changed_mar_apr,
            (status_apr IS DISTINCT FROM status_may AND status_apr IS NOT NULL AND status_may IS NOT NULL) AS status_changed_apr_may,
            -- carry per-month values for slicing
            county_mar, county_apr, county_may,
            zip_mar, zip_apr, zip_may,
            party_mar, party_apr, party_may,
            status_mar, status_apr, status_may,
            -- derived
            CAST(TRY_STRPTIME(birth_date, '%m/%d/%Y') AS DATE) AS birth_date_parsed,
            CAST(TRY_STRPTIME(registration_date, '%m/%d/%Y') AS DATE) AS registration_date_parsed,
            gender, race,
            COALESCE(party_may, party_apr, party_mar) AS party_last_known,
            COALESCE(county_may, county_apr, county_mar) AS county_last_known,
            COALESCE(zip_may, zip_apr, zip_mar) AS zip_last_known
        FROM per_voter
        """
    )

    print("adding age_band and registration_age columns ...")
    con.execute(
        """
        ALTER TABLE voter_changes ADD COLUMN age_at_may_2026 INTEGER
        """
    )
    con.execute(
        """
        ALTER TABLE voter_changes ADD COLUMN age_band VARCHAR
        """
    )
    con.execute(
        """
        ALTER TABLE voter_changes ADD COLUMN registration_age_years INTEGER
        """
    )
    con.execute(
        """
        UPDATE voter_changes
        SET age_at_may_2026 = CAST(DATE_DIFF('year', birth_date_parsed, DATE '2026-05-01') AS INTEGER)
        WHERE birth_date_parsed IS NOT NULL
        """
    )
    con.execute(
        """
        UPDATE voter_changes
        SET age_band = CASE
            WHEN age_at_may_2026 IS NULL THEN 'unknown'
            WHEN age_at_may_2026 < 25 THEN '18-24'
            WHEN age_at_may_2026 < 35 THEN '25-34'
            WHEN age_at_may_2026 < 45 THEN '35-44'
            WHEN age_at_may_2026 < 55 THEN '45-54'
            WHEN age_at_may_2026 < 65 THEN '55-64'
            WHEN age_at_may_2026 < 75 THEN '65-74'
            WHEN age_at_may_2026 < 120 THEN '75+'
            ELSE 'unknown'
        END
        """
    )
    con.execute(
        """
        UPDATE voter_changes
        SET registration_age_years = CAST(DATE_DIFF('year', registration_date_parsed, DATE '2026-05-01') AS INTEGER)
        WHERE registration_date_parsed IS NOT NULL
        """
    )

    print("\nvoter_changes row count:")
    (total,) = con.execute("SELECT COUNT(*) FROM voter_changes").fetchone()
    print(f"  {total:,} distinct voters across the three months")

    print("\npresence patterns (mar/apr/may):")
    for row in con.execute(
        """
        SELECT appeared_in_march, appeared_in_april, appeared_in_may,
               COUNT(*) AS voters
        FROM voter_changes
        GROUP BY 1,2,3
        ORDER BY voters DESC
        """
    ).fetchall():
        print(f"  {row}")

    print("\nmovement counts:")
    for row in con.execute(
        """
        SELECT
            SUM(CAST(new_in_april AS INT))            AS new_in_april,
            SUM(CAST(new_in_may AS INT))              AS new_in_may,
            SUM(CAST(missing_after_march AS INT))     AS missing_after_march,
            SUM(CAST(missing_after_april AS INT))     AS missing_after_april,
            SUM(CAST(county_changed_mar_apr AS INT))  AS county_changed_mar_apr,
            SUM(CAST(county_changed_apr_may AS INT))  AS county_changed_apr_may,
            SUM(CAST(zip_changed_mar_apr AS INT))     AS zip_changed_mar_apr,
            SUM(CAST(zip_changed_apr_may AS INT))     AS zip_changed_apr_may,
            SUM(CAST(party_changed_mar_apr AS INT))   AS party_changed_mar_apr,
            SUM(CAST(party_changed_apr_may AS INT))   AS party_changed_apr_may,
            SUM(CAST(status_changed_mar_apr AS INT))  AS status_changed_mar_apr,
            SUM(CAST(status_changed_apr_may AS INT))  AS status_changed_apr_may
        FROM voter_changes
        """
    ).fetchall():
        print(f"  {row}")

    print("\nage band distribution:")
    for row in con.execute(
        """
        SELECT age_band, COUNT(*) AS voters
        FROM voter_changes
        GROUP BY age_band
        ORDER BY age_band
        """
    ).fetchall():
        print(f"  {row}")

    print("done.")


if __name__ == "__main__":
    main()

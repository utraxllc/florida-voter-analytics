"""Individual-level movers analysis.

For every voter who appears in two consecutive monthly snapshots with a *different*
residence ZIP, classify the move by:
  - source vs destination income band (IRS SOI mean AGI, TY 2022)
  - source vs destination affordability band (z-scored home_value_to_income_ratio)
  - race (per voter file race code)
  - party before move, party after move, party_changed boolean

IMPORTANT LIMITATION: we have NO individual income. The "wealth direction" of a
move is inferred from the *area* income of the source vs destination ZIP. A
person moving from a low-mean-AGI ZIP to a high-mean-AGI ZIP is treated as
"moving up the income ladder" — but this is an area-level proxy, not personal
wealth acquisition.

Outputs to powerbi/:
  movers_long.parquet               row-per-move detail (still aggregable, no PII)
  movers_income_direction.csv       counts by (move_direction_income, race, party_after)
  movers_affordability_direction.csv counts by (move_direction_afford, race, party_after)
  movers_band_to_band.csv           source_band → destination_band heatmap by race
  movers_party_change.csv           did the voter ALSO change party? by move direction × race
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"
OUT_DIR = PROJECT_ROOT / "powerbi"

RACE_LABEL = """
    CASE race
        WHEN '1' THEN '1 American Indian / Alaskan'
        WHEN '2' THEN '2 Asian / Pacific Islander'
        WHEN '3' THEN '3 Black, Not Hispanic'
        WHEN '4' THEN '4 Hispanic'
        WHEN '5' THEN '5 White, Not Hispanic'
        WHEN '6' THEN '6 Other'
        WHEN '7' THEN '7 Multi-racial'
        ELSE         '9 Unknown'
    END
"""

MIN_CELL = 10


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    print("building movers_long ...")
    con.execute("DROP TABLE IF EXISTS movers_long")
    con.execute(
        f"""
        CREATE TABLE movers_long AS
        WITH zi AS (
            SELECT zip_code,
                   mean_agi_per_return,
                   income_band
            FROM zip_income
            WHERE tax_year = 2022
        ),
        zaf AS (
            SELECT zip_code,
                   affordability_band,
                   affordability_pressure_score,
                   home_value_to_income_ratio,
                   typical_home_value_latest
            FROM zip_affordability
        ),
        moves AS (
            -- Mar -> Apr moves
            SELECT
                voter_id,
                '2026-03 -> 2026-04' AS window,
                zip_mar AS src_zip, zip_apr AS dst_zip,
                party_mar AS src_party, party_apr AS dst_party,
                county_mar AS src_county, county_apr AS dst_county,
                race
            FROM voter_changes
            WHERE zip_changed_mar_apr
            UNION ALL
            -- Apr -> May moves
            SELECT
                voter_id,
                '2026-04 -> 2026-05' AS window,
                zip_apr AS src_zip, zip_may AS dst_zip,
                party_apr AS src_party, party_may AS dst_party,
                county_apr AS src_county, county_may AS dst_county,
                race
            FROM voter_changes
            WHERE zip_changed_apr_may
        )
        SELECT
            m.voter_id,
            m.window,
            m.src_zip, m.dst_zip,
            m.src_county, m.dst_county,
            (m.src_county <> m.dst_county) AS crossed_county,
            m.src_party, m.dst_party,
            (m.src_party <> m.dst_party) AS party_changed,
            {RACE_LABEL} AS race_label,
            zi_src.mean_agi_per_return AS src_mean_agi,
            zi_dst.mean_agi_per_return AS dst_mean_agi,
            zi_src.income_band         AS src_income_band,
            zi_dst.income_band         AS dst_income_band,
            zaf_src.affordability_band AS src_affordability_band,
            zaf_dst.affordability_band AS dst_affordability_band,
            zaf_src.home_value_to_income_ratio AS src_hv_to_income,
            zaf_dst.home_value_to_income_ratio AS dst_hv_to_income,
            -- Income direction: up if destination ZIP avg AGI >= 1.15x source; down if <= 0.85x; lateral otherwise.
            CASE
                WHEN zi_src.mean_agi_per_return IS NULL OR zi_dst.mean_agi_per_return IS NULL THEN 'unknown'
                WHEN zi_dst.mean_agi_per_return >= 1.15 * zi_src.mean_agi_per_return THEN 'up (>=+15%)'
                WHEN zi_dst.mean_agi_per_return <= 0.85 * zi_src.mean_agi_per_return THEN 'down (<=-15%)'
                ELSE 'lateral (+/-15%)'
            END AS income_direction,
            -- Affordability direction: "to less affordable" if dst HV/income ratio >= src + 1.0; "to more affordable" if <= -1.0
            CASE
                WHEN zaf_src.home_value_to_income_ratio IS NULL OR zaf_dst.home_value_to_income_ratio IS NULL THEN 'unknown'
                WHEN zaf_dst.home_value_to_income_ratio - zaf_src.home_value_to_income_ratio >= 1.0 THEN 'to less affordable (+1.0+ ratio)'
                WHEN zaf_dst.home_value_to_income_ratio - zaf_src.home_value_to_income_ratio <= -1.0 THEN 'to more affordable (-1.0+ ratio)'
                ELSE 'similar pressure'
            END AS affordability_direction
        FROM moves m
        LEFT JOIN zi  zi_src  ON m.src_zip = zi_src.zip_code
        LEFT JOIN zi  zi_dst  ON m.dst_zip = zi_dst.zip_code
        LEFT JOIN zaf zaf_src ON m.src_zip = zaf_src.zip_code
        LEFT JOIN zaf zaf_dst ON m.dst_zip = zaf_dst.zip_code
        """
    )
    (rows,) = con.execute("SELECT COUNT(*) FROM movers_long").fetchone()
    print(f"  {rows:,} mover-events total")

    print("\nmove direction (income) by race — party_after distribution:")
    for r in con.execute(
        """
        SELECT income_direction, race_label, dst_party,
               COUNT(*) AS movers
        FROM movers_long
        WHERE dst_party IN ('DEM','REP','NPA')
        GROUP BY 1,2,3
        HAVING COUNT(*) >= 10
        ORDER BY 1,2, movers DESC
        LIMIT 30
        """
    ).fetchall():
        print(f"  {r}")

    # Export aggregates ------------------------------------------------------
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nexporting movers_income_direction.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT income_direction,
                   race_label,
                   dst_party AS party_after,
                   COUNT(*) AS movers,
                   SUM(CAST(party_changed AS INT)) AS movers_who_also_changed_party,
                   SUM(CAST(crossed_county AS INT)) AS crossed_county
            FROM movers_long
            WHERE dst_party IS NOT NULL
            GROUP BY 1,2,3
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2,3
        ) TO '{OUT_DIR / "movers_income_direction.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting movers_affordability_direction.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT affordability_direction,
                   race_label,
                   dst_party AS party_after,
                   COUNT(*) AS movers,
                   SUM(CAST(party_changed AS INT)) AS movers_who_also_changed_party
            FROM movers_long
            WHERE dst_party IS NOT NULL
            GROUP BY 1,2,3
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2,3
        ) TO '{OUT_DIR / "movers_affordability_direction.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting movers_band_to_band.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT src_income_band, dst_income_band, race_label,
                   dst_party AS party_after,
                   COUNT(*) AS movers
            FROM movers_long
            WHERE src_income_band IS NOT NULL
              AND dst_income_band IS NOT NULL
              AND dst_party IN ('DEM','REP','NPA')
            GROUP BY 1,2,3,4
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2,3,4
        ) TO '{OUT_DIR / "movers_band_to_band.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting movers_party_change.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT income_direction,
                   race_label,
                   src_party,
                   dst_party,
                   COUNT(*) AS movers
            FROM movers_long
            WHERE party_changed
              AND src_party IS NOT NULL AND dst_party IS NOT NULL
            GROUP BY 1,2,3,4
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2,3,4
        ) TO '{OUT_DIR / "movers_party_change.csv"}' (HEADER, DELIMITER ',')
        """
    )

    # --- headline rollups printed to screen for the user ---
    print("\n" + "=" * 70)
    print("HEADLINE: party share AFTER the move, by income direction of the move")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT income_direction, dst_party, COUNT(*) AS n
            FROM movers_long
            WHERE income_direction <> 'unknown'
              AND dst_party IN ('DEM','REP','NPA')
            GROUP BY 1,2
        ),
        tot AS (SELECT income_direction, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.income_direction, t.dst_party,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS movers
        FROM t JOIN tot USING (income_direction)
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: among voters who MOVED UP (income), party share after, by race")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT race_label, dst_party, COUNT(*) AS n
            FROM movers_long
            WHERE income_direction = 'up (>=+15%)'
              AND dst_party IN ('DEM','REP','NPA')
            GROUP BY 1,2
        ),
        tot AS (SELECT race_label, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.race_label, t.dst_party,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS movers
        FROM t JOIN tot USING (race_label)
        WHERE tot.total >= 100
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: among voters who MOVED DOWN (income), party share after, by race")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT race_label, dst_party, COUNT(*) AS n
            FROM movers_long
            WHERE income_direction = 'down (<=-15%)'
              AND dst_party IN ('DEM','REP','NPA')
            GROUP BY 1,2
        ),
        tot AS (SELECT race_label, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.race_label, t.dst_party,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS movers
        FROM t JOIN tot USING (race_label)
        WHERE tot.total >= 100
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: did movers ALSO change party? party_change rate by move direction")
    print("(comparison vs non-movers' party_change rate ~0.48%)")
    print("=" * 70)
    for r in con.execute(
        """
        SELECT income_direction,
               COUNT(*) AS movers,
               SUM(CAST(party_changed AS INT)) AS movers_who_changed_party,
               ROUND(100.0 * SUM(CAST(party_changed AS INT)) / COUNT(*), 2) AS pct_changed_party
        FROM movers_long
        GROUP BY income_direction
        ORDER BY income_direction
        """
    ).fetchall():
        print(f"  {r}")

    print("\ndone.")


if __name__ == "__main__":
    main()

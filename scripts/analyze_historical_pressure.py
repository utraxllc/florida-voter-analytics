"""Historical ZIP pressure analysis.

For each FL ZIP, compute long-run home value growth (Zillow back to 2000) and
short-run real income growth (IRS SOI 2020 -> 2022, deflated by CPI), then look
at how those historical metrics correlate with:
  - May 2026 party share
  - Party-change rate Mar -> May 2026
  - Movement rate Mar -> May 2026
  - Net active-status change

LIMITATION: ZIP-level economic measures, not individual longitudinal histories.
We're asking "do voters living in ZIPs that saw heavier appreciation behave
differently in 2026 from voters in ZIPs that saw lighter appreciation?" — not
"did individual X get richer over 25 years and then switch parties."

Outputs to powerbi/:
  zip_pressure_metrics.csv          per-ZIP metrics + bands
  party_by_25yr_appreciation.csv    party share by long-run home value growth band
  party_by_real_income_change.csv   party share by recent real income change band
  movement_by_25yr_appreciation.csv movement rate by long-run growth band
  partychange_by_25yr_appreciation.csv party-change rate by long-run growth band
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"
OUT_DIR = PROJECT_ROOT / "powerbi"

MIN_CELL = 10


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    # Anchor home values to two reference months: 2000-01 (or earliest available)
    # and the most recent month in Zillow.
    print("computing per-ZIP historical metrics ...")
    con.execute("DROP TABLE IF EXISTS zip_pressure_metrics")
    con.execute(
        """
        CREATE TABLE zip_pressure_metrics AS
        WITH hv_min AS (
            SELECT zip_code, MIN(year_month) AS first_month, MIN(month_date) AS first_date
            FROM zip_home_values
            WHERE typical_home_value IS NOT NULL
            GROUP BY zip_code
        ),
        hv_max AS (
            SELECT zip_code, MAX(year_month) AS last_month, MAX(month_date) AS last_date
            FROM zip_home_values
            WHERE typical_home_value IS NOT NULL
            GROUP BY zip_code
        ),
        first_v AS (
            SELECT v.zip_code, v.typical_home_value AS hv_first, v.year_month AS first_month
            FROM zip_home_values v
            JOIN hv_min m USING (zip_code)
            WHERE v.year_month = m.first_month
        ),
        last_v AS (
            SELECT v.zip_code, v.typical_home_value AS hv_last, v.year_month AS last_month
            FROM zip_home_values v
            JOIN hv_max m USING (zip_code)
            WHERE v.year_month = m.last_month
        ),
        five_yr_v AS (
            SELECT v.zip_code, v.typical_home_value AS hv_5y_ago
            FROM zip_home_values v
            WHERE v.year_month = '2021-04'
        ),
        inc_20 AS (
            SELECT zip_code, real_mean_agi_2026 AS real_agi_2020
            FROM zip_income WHERE tax_year = 2020
        ),
        inc_22 AS (
            SELECT zip_code, real_mean_agi_2026 AS real_agi_2022,
                   mean_agi_per_return, income_band
            FROM zip_income WHERE tax_year = 2022
        ),
        joined AS (
            SELECT
                COALESCE(i22.zip_code, lv.zip_code) AS zip_code,
                fv.first_month,
                lv.last_month,
                fv.hv_first,
                lv.hv_last,
                fyv.hv_5y_ago,
                LN(NULLIF(lv.hv_last,0) / NULLIF(fv.hv_first,0)) /
                    NULLIF(DATE_DIFF('year', CAST(fv.first_month || '-01' AS DATE), CAST(lv.last_month || '-01' AS DATE)),0)
                    AS log_growth_cagr,
                (lv.hv_last / NULLIF(fv.hv_first,0)) - 1            AS hv_growth_since_2000,
                (lv.hv_last / NULLIF(fyv.hv_5y_ago,0)) - 1          AS hv_growth_5yr,
                i22.real_agi_2022,
                i20.real_agi_2020,
                (i22.real_agi_2022 / NULLIF(i20.real_agi_2020,0)) - 1 AS real_income_change_20_22,
                i22.mean_agi_per_return AS mean_agi_2022,
                i22.income_band
            FROM last_v lv
            LEFT JOIN first_v fv USING (zip_code)
            LEFT JOIN five_yr_v fyv USING (zip_code)
            LEFT JOIN inc_22 i22 USING (zip_code)
            LEFT JOIN inc_20 i20 USING (zip_code)
        )
        SELECT
            *,
            CASE
                WHEN hv_growth_since_2000 IS NULL THEN 'unknown'
                WHEN hv_growth_since_2000 < 1.50 THEN '1 <150% (low)'
                WHEN hv_growth_since_2000 < 2.50 THEN '2 150-250%'
                WHEN hv_growth_since_2000 < 3.50 THEN '3 250-350%'
                WHEN hv_growth_since_2000 < 4.50 THEN '4 350-450%'
                ELSE                                    '5 >=450% (high)'
            END AS hv_growth_25yr_band,
            CASE
                WHEN hv_growth_5yr IS NULL THEN 'unknown'
                WHEN hv_growth_5yr < 0.20 THEN '1 <20% (cool)'
                WHEN hv_growth_5yr < 0.40 THEN '2 20-40%'
                WHEN hv_growth_5yr < 0.60 THEN '3 40-60%'
                WHEN hv_growth_5yr < 0.80 THEN '4 60-80%'
                ELSE                            '5 >=80% (hot)'
            END AS hv_growth_5yr_band,
            CASE
                WHEN real_income_change_20_22 IS NULL THEN 'unknown'
                WHEN real_income_change_20_22 < -0.05 THEN '1 declined >5%'
                WHEN real_income_change_20_22 < 0.00  THEN '2 declined 0-5%'
                WHEN real_income_change_20_22 < 0.05  THEN '3 grew 0-5%'
                WHEN real_income_change_20_22 < 0.10  THEN '4 grew 5-10%'
                ELSE                                       '5 grew >=10%'
            END AS real_income_change_band
        FROM joined
        """
    )

    (zips, hv_zips, inc_zips) = con.execute(
        """
        SELECT COUNT(*), COUNT(hv_growth_since_2000), COUNT(real_income_change_20_22)
        FROM zip_pressure_metrics
        """
    ).fetchone()
    print(f"  {zips} ZIPs in pressure_metrics; {hv_zips} have 25-yr appreciation; {inc_zips} have real income change")

    # Per-voter join: map each voter to their last_known ZIP's pressure metrics
    print("joining voters to ZIP pressure ...")
    con.execute("DROP TABLE IF EXISTS voter_pressure_long")
    con.execute(
        """
        CREATE TABLE voter_pressure_long AS
        SELECT
            v.voter_id,
            v.zip_last_known,
            v.party_last_known,
            v.county_last_known,
            v.age_band,
            v.race,
            v.appeared_in_march, v.appeared_in_april, v.appeared_in_may,
            v.new_in_april, v.new_in_may, v.new_in_may_only,
            v.missing_after_march, v.missing_after_april,
            v.party_changed_mar_apr, v.party_changed_apr_may,
            v.zip_changed_mar_apr,   v.zip_changed_apr_may,
            v.county_changed_mar_apr, v.county_changed_apr_may,
            v.status_changed_mar_apr, v.status_changed_apr_may,
            p.hv_growth_since_2000,
            p.hv_growth_5yr,
            p.real_income_change_20_22,
            p.hv_growth_25yr_band,
            p.hv_growth_5yr_band,
            p.real_income_change_band
        FROM voter_changes v
        LEFT JOIN zip_pressure_metrics p
          ON v.zip_last_known = p.zip_code
        """
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("exporting zip_pressure_metrics.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT zip_code, first_month, last_month,
                   hv_first, hv_last, hv_growth_since_2000, hv_growth_5yr, hv_growth_25yr_band, hv_growth_5yr_band,
                   mean_agi_2022, income_band, real_agi_2020, real_agi_2022,
                   real_income_change_20_22, real_income_change_band
            FROM zip_pressure_metrics
            ORDER BY zip_code
        ) TO '{OUT_DIR / "zip_pressure_metrics.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting party_by_25yr_appreciation.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT hv_growth_25yr_band,
                   party_last_known AS party_affiliation,
                   COUNT(*) AS voters
            FROM voter_pressure_long
            WHERE party_last_known IN ('DEM','REP','NPA')
            GROUP BY 1,2
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2
        ) TO '{OUT_DIR / "party_by_25yr_appreciation.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting party_by_real_income_change.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT real_income_change_band,
                   party_last_known AS party_affiliation,
                   COUNT(*) AS voters
            FROM voter_pressure_long
            WHERE party_last_known IN ('DEM','REP','NPA')
            GROUP BY 1,2
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2
        ) TO '{OUT_DIR / "party_by_real_income_change.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting movement_by_25yr_appreciation.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT hv_growth_25yr_band,
                   COUNT(*) AS voters,
                   SUM(CAST(zip_changed_mar_apr AS INT) + CAST(zip_changed_apr_may AS INT)) AS zip_changes,
                   SUM(CAST(county_changed_mar_apr AS INT) + CAST(county_changed_apr_may AS INT)) AS county_changes,
                   SUM(CAST(new_in_april AS INT) + CAST(new_in_may AS INT)) AS new_registrations,
                   SUM(CAST(missing_after_march AS INT) + CAST(missing_after_april AS INT)) AS departures,
                   ROUND(100.0 * SUM(CAST(zip_changed_mar_apr AS INT) + CAST(zip_changed_apr_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_zip_changes,
                   ROUND(100.0 * SUM(CAST(new_in_april AS INT) + CAST(new_in_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_new_registrations,
                   ROUND(100.0 * SUM(CAST(missing_after_march AS INT) + CAST(missing_after_april AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_departures
            FROM voter_pressure_long
            GROUP BY hv_growth_25yr_band
            ORDER BY hv_growth_25yr_band
        ) TO '{OUT_DIR / "movement_by_25yr_appreciation.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("exporting partychange_by_25yr_appreciation.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT hv_growth_25yr_band,
                   COUNT(*) AS voters,
                   SUM(CAST(party_changed_mar_apr AS INT) + CAST(party_changed_apr_may AS INT)) AS party_changes,
                   ROUND(100.0 * SUM(CAST(party_changed_mar_apr AS INT) + CAST(party_changed_apr_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_party_changes
            FROM voter_pressure_long
            GROUP BY hv_growth_25yr_band
            ORDER BY hv_growth_25yr_band
        ) TO '{OUT_DIR / "partychange_by_25yr_appreciation.csv"}' (HEADER, DELIMITER ',')
        """
    )

    # --- headline rollups printed to screen ---
    print("\n" + "=" * 70)
    print("HEADLINE: party share by ZIP's 25-yr home value growth band")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT hv_growth_25yr_band, party_last_known AS p, COUNT(*) AS n
            FROM voter_pressure_long
            WHERE party_last_known IN ('DEM','REP','NPA')
              AND hv_growth_25yr_band <> 'unknown'
            GROUP BY 1,2
        ),
        tot AS (SELECT hv_growth_25yr_band, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.hv_growth_25yr_band, t.p,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS voters
        FROM t JOIN tot USING (hv_growth_25yr_band)
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: party share by ZIP's 2020->2022 REAL income change band")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT real_income_change_band, party_last_known AS p, COUNT(*) AS n
            FROM voter_pressure_long
            WHERE party_last_known IN ('DEM','REP','NPA')
              AND real_income_change_band <> 'unknown'
            GROUP BY 1,2
        ),
        tot AS (SELECT real_income_change_band, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.real_income_change_band, t.p,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS voters
        FROM t JOIN tot USING (real_income_change_band)
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: 2026 movement rates by ZIP's 25-yr home value growth band")
    print("=" * 70)
    for r in con.execute(
        """
        SELECT hv_growth_25yr_band,
               COUNT(*) AS voters,
               ROUND(100.0 * SUM(CAST(zip_changed_mar_apr AS INT) + CAST(zip_changed_apr_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_zip_change,
               ROUND(100.0 * SUM(CAST(new_in_april AS INT) + CAST(new_in_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_new,
               ROUND(100.0 * SUM(CAST(missing_after_march AS INT) + CAST(missing_after_april AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_left,
               ROUND(100.0 * SUM(CAST(party_changed_mar_apr AS INT) + CAST(party_changed_apr_may AS INT)) / NULLIF(COUNT(*),0), 3) AS pct_party_change
        FROM voter_pressure_long
        GROUP BY hv_growth_25yr_band
        ORDER BY hv_growth_25yr_band
        """
    ).fetchall():
        print(f"  {r}")

    print("\n" + "=" * 70)
    print("HEADLINE: party share by 5-yr (2021-2026) home value growth band")
    print("=" * 70)
    for r in con.execute(
        """
        WITH t AS (
            SELECT hv_growth_5yr_band, party_last_known AS p, COUNT(*) AS n
            FROM voter_pressure_long
            WHERE party_last_known IN ('DEM','REP','NPA')
              AND hv_growth_5yr_band <> 'unknown'
            GROUP BY 1,2
        ),
        tot AS (SELECT hv_growth_5yr_band, SUM(n) AS total FROM t GROUP BY 1)
        SELECT t.hv_growth_5yr_band, t.p,
               ROUND(100.0 * t.n / tot.total, 1) AS pct,
               t.n AS voters
        FROM t JOIN tot USING (hv_growth_5yr_band)
        ORDER BY 1, 2
        """
    ).fetchall():
        print(f"  {r}")

    print("\ndone.")


if __name__ == "__main__":
    main()

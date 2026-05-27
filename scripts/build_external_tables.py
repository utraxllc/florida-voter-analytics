"""Build ZIP-level income, home value, and affordability tables in DuckDB.

Inputs (in raw_zips/external/):
  - irs_soi_zip_22.csv   IRS Statistics of Income, ZIP-level, TY 2022 (and TY 21, 20)
  - zillow_zhvi_zip.csv  Zillow Home Value Index, ZIP-level, monthly back to 2000
  - bls_cpi.json         BLS CPI-U All Items, monthly, 2019-2026

Outputs (DuckDB tables in duckdb/voter.duckdb):
  - cpi_monthly                year_month, cpi_value, real_factor_to_may_2026
  - zip_income                 zip_code, tax_year, total_returns, total_agi_dollars,
                               mean_agi_per_return, real_mean_agi_2026
  - zip_home_values            zip_code, year_month, typical_home_value,
                               home_value_yoy_change, home_value_5yr_change
  - zip_affordability          zip_code, tax_year, mean_agi_per_return,
                               typical_home_value_may_2026, home_value_to_income_ratio,
                               affordability_pressure_score, affordability_band

Notes:
  * Joining everything on 5-digit ZIP (voter, Zillow, IRS all use ZIP). HUD ZIP/ZCTA
    crosswalk was skipped because it requires an API key; ZIP-only joins lose a small
    number of PO-box-only ZIPs and unique-recipient ZIPs but are otherwise consistent.
  * "Real" income is computed by deflating nominal IRS AGI by CPI-U to May 2026 dollars.
  * Affordability pressure is z-scored across Florida ZIPs to make the band cuts
    interpretable relative to the state, not the nation.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = PROJECT_ROOT / "raw_zips" / "external"
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"


def load_cpi(con: duckdb.DuckDBPyConnection) -> float:
    """Load CPI into DuckDB, return the May-2026 CPI value used as the deflation base."""
    payload = json.loads((EXTERNAL_DIR / "bls_cpi.json").read_text())
    rows = []
    for rec in payload["Results"]["series"][0]["data"]:
        if not rec["period"].startswith("M"):
            continue  # skip M13 (annual average) and any non-monthly periods
        try:
            value = float(rec["value"])
        except ValueError:
            continue  # skip unpublished or placeholder values
        month = int(rec["period"][1:])
        if month > 12:
            continue
        ym = f"{rec['year']}-{month:02d}"
        rows.append((ym, value))

    con.execute("DROP TABLE IF EXISTS cpi_monthly")
    con.execute(
        "CREATE TABLE cpi_monthly (year_month VARCHAR, cpi_value DOUBLE, real_factor_to_may_2026 DOUBLE)"
    )

    # Pick the most recent month we have as the deflation base; fall back to a
    # known anchor if May 2026 isn't yet published.
    rows_sorted = sorted(rows)
    base_month_target = "2026-05"
    base_cpi = next((c for ym, c in rows_sorted if ym == base_month_target), rows_sorted[-1][1])

    for ym, cpi in rows_sorted:
        factor = base_cpi / cpi
        con.execute(
            "INSERT INTO cpi_monthly VALUES (?, ?, ?)",
            [ym, cpi, factor],
        )

    print(f"  loaded {len(rows_sorted)} CPI rows; deflation base = {base_cpi:.3f} (May 2026 target)")
    return base_cpi


def load_irs_soi(con: duckdb.DuckDBPyConnection, base_cpi: float) -> None:
    """Load IRS SOI ZIP-level files, derive zip_income table with real AGI per return."""
    # SOI files: one row per (ZIP, agi_stub bracket). We aggregate to per-ZIP totals.
    # N1   = number of returns
    # A00100 = AGI (in $1000s)
    # Skip rows with zipcode = '00000' (state totals).

    soi_files = {
        2020: EXTERNAL_DIR / "irs_soi_zip_20.csv",
        2021: EXTERNAL_DIR / "irs_soi_zip_21.csv",
        2022: EXTERNAL_DIR / "irs_soi_zip_22.csv",
    }

    # CPI year-over-year deflation: use the December value of each tax year as the
    # representative price level for that year's nominal income.
    year_cpi = {}
    for year in soi_files:
        (cpi,) = con.execute(
            "SELECT cpi_value FROM cpi_monthly WHERE year_month = ?",
            [f"{year}-12"],
        ).fetchone()
        year_cpi[year] = cpi

    con.execute("DROP TABLE IF EXISTS zip_income")
    con.execute(
        """
        CREATE TABLE zip_income (
            zip_code           VARCHAR,
            tax_year           INTEGER,
            total_returns      DOUBLE,
            total_agi_dollars  DOUBLE,
            mean_agi_per_return DOUBLE,
            real_mean_agi_2026 DOUBLE,
            income_band        VARCHAR
        )
        """
    )

    for year, path in soi_files.items():
        cpi = year_cpi[year]
        deflator = base_cpi / cpi
        con.execute(
            f"""
            INSERT INTO zip_income (zip_code, tax_year, total_returns, total_agi_dollars,
                                    mean_agi_per_return, real_mean_agi_2026, income_band)
            WITH agg AS (
                SELECT
                    LPAD(CAST(zipcode AS VARCHAR), 5, '0') AS zip_code,
                    {year} AS tax_year,
                    SUM(N1)                  AS total_returns,
                    SUM(A00100) * 1000.0     AS total_agi_dollars
                FROM read_csv('{path}', header=true, ignore_errors=true)
                WHERE STATE = 'FL'
                  AND zipcode IS NOT NULL
                  AND CAST(zipcode AS VARCHAR) <> '0'
                  AND CAST(zipcode AS VARCHAR) <> '00000'
                GROUP BY zipcode
                HAVING SUM(N1) > 0
            )
            SELECT
                zip_code,
                tax_year,
                total_returns,
                total_agi_dollars,
                total_agi_dollars / NULLIF(total_returns, 0) AS mean_agi_per_return,
                (total_agi_dollars / NULLIF(total_returns, 0)) * {deflator} AS real_mean_agi_2026,
                CASE
                    WHEN total_agi_dollars / NULLIF(total_returns, 0) < 35000 THEN '1: under $35K'
                    WHEN total_agi_dollars / NULLIF(total_returns, 0) < 55000 THEN '2: $35-55K'
                    WHEN total_agi_dollars / NULLIF(total_returns, 0) < 80000 THEN '3: $55-80K'
                    WHEN total_agi_dollars / NULLIF(total_returns, 0) < 120000 THEN '4: $80-120K'
                    WHEN total_agi_dollars / NULLIF(total_returns, 0) < 200000 THEN '5: $120-200K'
                    ELSE '6: $200K+'
                END AS income_band
            FROM agg
            """
        )

    (rows,) = con.execute("SELECT COUNT(*) FROM zip_income").fetchone()
    print(f"  built zip_income with {rows:,} rows (FL ZIPs x tax years)")


def load_zillow(con: duckdb.DuckDBPyConnection) -> None:
    """Load Zillow ZHVI ZIP-level and pivot to long form for FL only."""
    csv_path = EXTERNAL_DIR / "zillow_zhvi_zip.csv"

    # First, get the column list to find all the date columns dynamically.
    col_rows = con.execute(
        f"DESCRIBE SELECT * FROM read_csv('{csv_path}', header=true, sample_size=10) LIMIT 0"
    ).fetchall()
    date_cols = [r[0] for r in col_rows if r[0].startswith(("19", "20")) and "-" in r[0]]

    # UNPIVOT all the date columns into one long table.
    unpivot_list = ", ".join(f'"{c}"' for c in date_cols)

    con.execute("DROP TABLE IF EXISTS zip_home_values")
    con.execute(
        f"""
        CREATE TABLE zip_home_values AS
        WITH src AS (
            SELECT * FROM read_csv('{csv_path}', header=true, sample_size=10)
            WHERE State = 'FL'
        ),
        long AS (
            UNPIVOT src
            ON {unpivot_list}
            INTO NAME date_str VALUE typical_home_value
        ),
        with_keys AS (
            SELECT
                LPAD(CAST(RegionName AS VARCHAR), 5, '0') AS zip_code,
                CAST(City AS VARCHAR)        AS city,
                CAST(CountyName AS VARCHAR)  AS county,
                CAST(Metro AS VARCHAR)       AS metro,
                STRFTIME(CAST(date_str AS DATE), '%Y-%m') AS year_month,
                CAST(date_str AS DATE)       AS month_date,
                typical_home_value
            FROM long
            WHERE typical_home_value IS NOT NULL
        )
        SELECT
            zip_code, city, county, metro, year_month, month_date,
            typical_home_value,
            LAG(typical_home_value, 12) OVER (PARTITION BY zip_code ORDER BY month_date) AS hv_1y_ago,
            LAG(typical_home_value, 60) OVER (PARTITION BY zip_code ORDER BY month_date) AS hv_5y_ago,
            (typical_home_value / NULLIF(LAG(typical_home_value, 12) OVER (PARTITION BY zip_code ORDER BY month_date), 0)) - 1 AS home_value_yoy_change,
            (typical_home_value / NULLIF(LAG(typical_home_value, 60) OVER (PARTITION BY zip_code ORDER BY month_date), 0)) - 1 AS home_value_5yr_change
        FROM with_keys
        """
    )

    (rows, zips, months) = con.execute(
        """
        SELECT COUNT(*), COUNT(DISTINCT zip_code),
               COUNT(DISTINCT year_month)
        FROM zip_home_values
        """
    ).fetchone()
    print(f"  built zip_home_values with {rows:,} rows, {zips} FL ZIPs, {months} months")


def build_affordability(con: duckdb.DuckDBPyConnection) -> None:
    """Combine income (TY 2022) and home values (May 2026) into per-ZIP affordability."""
    con.execute("DROP TABLE IF EXISTS zip_affordability")
    con.execute(
        """
        CREATE TABLE zip_affordability AS
        WITH inc AS (
            SELECT zip_code, mean_agi_per_return, real_mean_agi_2026, income_band
            FROM zip_income
            WHERE tax_year = 2022
        ),
        hv AS (
            SELECT zip_code, typical_home_value, home_value_yoy_change, home_value_5yr_change
            FROM zip_home_values
            WHERE year_month = (SELECT MAX(year_month) FROM zip_home_values)
        ),
        inc_growth AS (
            SELECT
                a.zip_code,
                (a.real_mean_agi_2026 / NULLIF(b.real_mean_agi_2026, 0)) - 1 AS real_income_growth_2020_2022
            FROM zip_income a
            LEFT JOIN zip_income b
              ON a.zip_code = b.zip_code AND b.tax_year = 2020
            WHERE a.tax_year = 2022
        ),
        combined AS (
            SELECT
                inc.zip_code,
                inc.mean_agi_per_return,
                inc.real_mean_agi_2026,
                inc.income_band,
                hv.typical_home_value AS typical_home_value_latest,
                hv.home_value_yoy_change,
                hv.home_value_5yr_change,
                inc_growth.real_income_growth_2020_2022,
                hv.typical_home_value / NULLIF(inc.mean_agi_per_return, 0) AS home_value_to_income_ratio
            FROM inc
            INNER JOIN hv USING (zip_code)
            LEFT JOIN inc_growth USING (zip_code)
        ),
        stats AS (
            SELECT
                AVG(home_value_to_income_ratio) AS mean_ratio,
                STDDEV_SAMP(home_value_to_income_ratio) AS sd_ratio
            FROM combined
            WHERE home_value_to_income_ratio IS NOT NULL
        )
        SELECT
            combined.*,
            (home_value_to_income_ratio - stats.mean_ratio) / NULLIF(stats.sd_ratio, 0) AS affordability_pressure_score,
            CASE
                WHEN home_value_to_income_ratio IS NULL THEN 'unknown'
                WHEN (home_value_to_income_ratio - stats.mean_ratio) / NULLIF(stats.sd_ratio, 0) < -0.75 THEN '1: low pressure'
                WHEN (home_value_to_income_ratio - stats.mean_ratio) / NULLIF(stats.sd_ratio, 0) < -0.25 THEN '2: below average'
                WHEN (home_value_to_income_ratio - stats.mean_ratio) / NULLIF(stats.sd_ratio, 0) <  0.25 THEN '3: average'
                WHEN (home_value_to_income_ratio - stats.mean_ratio) / NULLIF(stats.sd_ratio, 0) <  0.75 THEN '4: above average'
                ELSE '5: high pressure'
            END AS affordability_band
        FROM combined CROSS JOIN stats
        """
    )

    (rows,) = con.execute("SELECT COUNT(*) FROM zip_affordability").fetchone()
    print(f"  built zip_affordability with {rows:,} rows")

    print("\n  affordability band distribution:")
    for row in con.execute(
        """
        SELECT affordability_band,
               COUNT(*) AS zips,
               ROUND(AVG(home_value_to_income_ratio), 2) AS mean_ratio,
               ROUND(AVG(typical_home_value_latest), 0) AS mean_home_value,
               ROUND(AVG(mean_agi_per_return), 0) AS mean_agi
        FROM zip_affordability
        GROUP BY affordability_band
        ORDER BY affordability_band
        """
    ).fetchall():
        print(f"    {row}")


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    print("loading CPI ...")
    base_cpi = load_cpi(con)
    print("loading IRS SOI income ...")
    load_irs_soi(con, base_cpi)
    print("loading Zillow ZHVI ...")
    load_zillow(con)
    print("building zip_affordability ...")
    build_affordability(con)
    print("done.")


if __name__ == "__main__":
    main()

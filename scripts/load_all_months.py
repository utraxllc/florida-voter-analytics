"""Load all Florida voter detail files (March, April, May 2026) into DuckDB.

Builds the canonical `voter_month_snapshot` table with one row per voter per
extract month, plus an `extract_month` column derived from the source path.

Handles the April nesting quirk: April detail files live in
`extracted/20260414/detail/20260414_VoterDetail/` and that folder also contains
a `VerificationFiles/` subdirectory which must be excluded.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"

# Glob patterns per extract date. Notice April's extra nesting layer.
MONTH_GLOBS = {
    "2026-03": str(PROJECT_ROOT / "extracted" / "20260310" / "detail" / "*.txt"),
    "2026-04": str(
        PROJECT_ROOT
        / "extracted"
        / "20260414"
        / "detail"
        / "20260414_VoterDetail"
        / "*.txt"
    ),
    "2026-05": str(PROJECT_ROOT / "extracted" / "20260512" / "detail" / "*.txt"),
}

COLUMN_DEFS = [
    ("county_code", "VARCHAR"),
    ("voter_id", "VARCHAR"),
    ("name_last", "VARCHAR"),
    ("name_suffix", "VARCHAR"),
    ("name_first", "VARCHAR"),
    ("name_middle", "VARCHAR"),
    ("public_records_exemption", "VARCHAR"),
    ("residence_address_1", "VARCHAR"),
    ("residence_address_2", "VARCHAR"),
    ("residence_city", "VARCHAR"),
    ("residence_state", "VARCHAR"),
    ("residence_zipcode", "VARCHAR"),
    ("mailing_address_1", "VARCHAR"),
    ("mailing_address_2", "VARCHAR"),
    ("mailing_address_3", "VARCHAR"),
    ("mailing_city", "VARCHAR"),
    ("mailing_state", "VARCHAR"),
    ("mailing_zipcode", "VARCHAR"),
    ("mailing_country", "VARCHAR"),
    ("gender", "VARCHAR"),
    ("race", "VARCHAR"),
    ("birth_date", "VARCHAR"),
    ("registration_date", "VARCHAR"),
    ("party_affiliation", "VARCHAR"),
    ("precinct", "VARCHAR"),
    ("precinct_group", "VARCHAR"),
    ("precinct_split", "VARCHAR"),
    ("precinct_suffix", "VARCHAR"),
    ("voter_status", "VARCHAR"),
    ("congressional_district", "VARCHAR"),
    ("house_district", "VARCHAR"),
    ("senate_district", "VARCHAR"),
    ("county_commission_district", "VARCHAR"),
    ("school_board_district", "VARCHAR"),
    ("daytime_area_code", "VARCHAR"),
    ("daytime_phone_number", "VARCHAR"),
    ("daytime_phone_extension", "VARCHAR"),
    ("email_address", "VARCHAR"),
]


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    columns_struct = ", ".join(f"'{n}': '{t}'" for n, t in COLUMN_DEFS)
    column_list = ", ".join(n for n, _ in COLUMN_DEFS)

    con.execute("DROP TABLE IF EXISTS voter_month_snapshot")
    con.execute(
        f"""
        CREATE TABLE voter_month_snapshot (
            extract_month VARCHAR,
            source_file VARCHAR,
            {", ".join(f"{n} {t}" for n, t in COLUMN_DEFS)}
        )
        """
    )

    for extract_month, glob in MONTH_GLOBS.items():
        print(f"loading {extract_month} from {glob} ...")
        con.execute(
            f"""
            INSERT INTO voter_month_snapshot
            SELECT
                '{extract_month}' AS extract_month,
                filename AS source_file,
                {column_list}
            FROM read_csv(
                '{glob}',
                delim = '\t',
                header = false,
                quote = '',
                escape = '',
                strict_mode = false,
                ignore_errors = true,
                filename = true,
                columns = {{{columns_struct}}}
            )
            """
        )
        (rows, files) = con.execute(
            "SELECT COUNT(*), COUNT(DISTINCT source_file) FROM voter_month_snapshot WHERE extract_month = ?",
            [extract_month],
        ).fetchone()
        print(f"  -> {rows:,} rows, {files} distinct source files")

    print("\nper-month summary:")
    for row in con.execute(
        """
        SELECT extract_month,
               COUNT(*) AS rows,
               COUNT(DISTINCT source_file) AS files,
               COUNT(DISTINCT county_code) AS counties,
               COUNT(DISTINCT voter_id) AS distinct_voter_ids
        FROM voter_month_snapshot
        GROUP BY extract_month
        ORDER BY extract_month
        """
    ).fetchall():
        print(f"  {row}")

    print("\nindexing voter_id + extract_month for fast joins...")
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_voter_month ON voter_month_snapshot(voter_id, extract_month)"
    )
    print("done.")


if __name__ == "__main__":
    main()

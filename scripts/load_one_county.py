"""Load a single Florida voter detail file into DuckDB as a sanity check.

Default: Alachua County, March 2026 extract.
The 38 columns follow `docs/FINAL Voter Extract Disk File Layout rev 20260504.pdf`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = PROJECT_ROOT / "extracted" / "20260310" / "detail" / "ALA_20260310.txt"
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"

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

# Dates parsed at the query layer later; keep everything VARCHAR on load to
# avoid choking on blank or malformed values.


def main(target: str | None = None) -> None:
    file_path = Path(target) if target else DEFAULT_FILE
    if not file_path.exists():
        sys.exit(f"file not found: {file_path}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    column_sql = ", ".join(f"{name} {dtype}" for name, dtype in COLUMN_DEFS)
    columns_struct = ", ".join(f"'{name}': '{dtype}'" for name, dtype in COLUMN_DEFS)

    con.execute(f"CREATE OR REPLACE TABLE voter_detail_sample ({column_sql})")
    con.execute(
        f"""
        INSERT INTO voter_detail_sample
        SELECT * FROM read_csv(
            '{file_path}',
            delim = '\t',
            header = false,
            quote = '',
            escape = '',
            strict_mode = false,
            ignore_errors = true,
            columns = {{{columns_struct}}}
        )
        """
    )

    (row_count,) = con.execute("SELECT COUNT(*) FROM voter_detail_sample").fetchone()
    print(f"loaded {row_count:,} rows from {file_path.name}")

    print("\ncounty / status / party sanity check:")
    for row in con.execute(
        """
        SELECT county_code, voter_status, party_affiliation, COUNT(*) AS n
        FROM voter_detail_sample
        GROUP BY 1, 2, 3
        ORDER BY n DESC
        LIMIT 10
        """
    ).fetchall():
        print(f"  {row}")

    print("\nfirst 3 non-identifying rows (county, zip, party, status):")
    for row in con.execute(
        """
        SELECT county_code,
               residence_zipcode,
               party_affiliation,
               voter_status
        FROM voter_detail_sample
        LIMIT 3
        """
    ).fetchall():
        print(f"  {row}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

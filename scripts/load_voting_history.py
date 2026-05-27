"""Load May 2026 voting history into DuckDB.

We use the May extract only because (per the layout PDF) all voting history for
each voter is stored in the county file where they're *currently* registered.
The most recent extract is the most complete; older extracts add no information
beyond what's already in May.

Schema (5 fields, tab-delimited, no header):
  1 County Code (3)
  2 Voter ID (10)
  3 Election Date (10) MM/DD/YYYY
  4 Election Type (3) - PPP, PRI, RUN, GEN, OTH
  5 History Code (1)  - A (mail), B (mail rejected), E (early), L (late mail),
                        N (didn't vote), P (provisional rejected), Y (at polls)
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"

GLOB = str(PROJECT_ROOT / "extracted" / "20260512" / "history" / "*.txt")


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    print("creating voter_history table ...")
    con.execute("DROP TABLE IF EXISTS voter_history")
    con.execute(
        f"""
        CREATE TABLE voter_history AS
        SELECT
            county_code,
            voter_id,
            election_date_str,
            CAST(TRY_STRPTIME(election_date_str, '%m/%d/%Y') AS DATE) AS election_date,
            election_type,
            history_code
        FROM read_csv(
            '{GLOB}',
            delim = '\t',
            header = false,
            quote = '',
            escape = '',
            strict_mode = false,
            ignore_errors = true,
            columns = {{
                'county_code': 'VARCHAR',
                'voter_id': 'VARCHAR',
                'election_date_str': 'VARCHAR',
                'election_type': 'VARCHAR',
                'history_code': 'VARCHAR'
            }}
        )
        """
    )

    print("indexing ...")
    con.execute("CREATE INDEX IF NOT EXISTS idx_vh_voter ON voter_history(voter_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_vh_election ON voter_history(election_date, election_type)")

    (total, voters, elections) = con.execute(
        """
        SELECT COUNT(*),
               COUNT(DISTINCT voter_id),
               COUNT(DISTINCT (election_date, election_type))
        FROM voter_history
        """
    ).fetchone()
    print(f"  loaded {total:,} history rows / {voters:,} distinct voters / {elections} elections")

    print("\nhistory code distribution:")
    for r in con.execute(
        """
        SELECT history_code, COUNT(*) AS rows,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM voter_history
        GROUP BY history_code
        ORDER BY rows DESC
        """
    ).fetchall():
        print(f"  {r}")

    print("\nelection type distribution:")
    for r in con.execute(
        """
        SELECT election_type, COUNT(*) AS rows
        FROM voter_history
        GROUP BY election_type
        ORDER BY rows DESC
        """
    ).fetchall():
        print(f"  {r}")

    print("\nyear range:")
    for r in con.execute(
        """
        SELECT MIN(election_date), MAX(election_date), COUNT(DISTINCT EXTRACT(YEAR FROM election_date)) AS years
        FROM voter_history
        WHERE election_date IS NOT NULL
        """
    ).fetchall():
        print(f"  {r}")


if __name__ == "__main__":
    main()

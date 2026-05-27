"""Build Page-5 (Voting History) aggregates and Power BI exports.

Approach: join voter_history (70M rows) to voter_changes (16M voters) so each
history row carries the voter's current party, age band, race, county, and
zip-affordability band.

Outputs to powerbi/:
  vh_method_by_party.csv           method (mail/early/at polls) x party x year
  vh_method_by_age_band.csv        method x age band x party
  vh_election_participation.csv    election-level totals (by party, county)
  vh_voter_consistency.csv         per-voter cohort: how often they vote, by party/race/age
  vh_method_shift_pre_post_2020.csv method share before vs after Nov 2020
  vh_dropoff_general_to_midterm.csv cycle drop-off (2024 GEN vs 2022 GEN vs 2020 GEN)
  vh_method_by_county.csv          method share by county (for the map)
"""

from __future__ import annotations

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "duckdb" / "voter.duckdb"
OUT_DIR = PROJECT_ROOT / "powerbi"

# Group history codes into analytical buckets.
METHOD_LABEL_SQL = """
    CASE history_code
        WHEN 'A' THEN '1 Mail (counted)'
        WHEN 'B' THEN '5 Mail (rejected)'
        WHEN 'E' THEN '2 Early in person'
        WHEN 'L' THEN '6 Mail (late, rejected)'
        WHEN 'N' THEN '7 Did not vote'
        WHEN 'P' THEN '8 Provisional (rejected)'
        WHEN 'Y' THEN '3 Polls (election day)'
        ELSE         '9 Unknown'
    END
"""

ELECTION_LABEL_SQL = """
    CASE election_type
        WHEN 'GEN' THEN '1 General'
        WHEN 'PRI' THEN '2 Primary'
        WHEN 'PPP' THEN '3 Presidential Preference Primary'
        WHEN 'RUN' THEN '4 Runoff'
        WHEN 'OTH' THEN '5 Other / Special / Local'
        ELSE             '9 Unknown'
    END
"""

RACE_LABEL_SQL = """
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

    print("creating enriched voter_history_enriched view ...")
    con.execute(
        f"""
        CREATE OR REPLACE VIEW voter_history_enriched AS
        SELECT
            h.county_code,
            h.voter_id,
            h.election_date,
            EXTRACT(YEAR FROM h.election_date) AS election_year,
            h.election_type,
            {ELECTION_LABEL_SQL.replace("election_type", "h.election_type")} AS election_type_label,
            h.history_code,
            {METHOD_LABEL_SQL.replace("history_code", "h.history_code")} AS method_label,
            CASE WHEN h.history_code IN ('A','E','Y') THEN 1 ELSE 0 END AS counted_vote,
            CASE WHEN h.history_code IN ('A','L','B') THEN 'mail'
                 WHEN h.history_code = 'E' THEN 'early'
                 WHEN h.history_code = 'Y' THEN 'polls'
                 ELSE 'other' END AS method_bucket,
            v.party_last_known,
            v.age_band,
            {RACE_LABEL_SQL.replace("race", "v.race")} AS race_label,
            v.county_last_known
        FROM voter_history h
        LEFT JOIN voter_changes v ON h.voter_id = v.voter_id
        WHERE h.election_date IS NOT NULL
        """
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("vh_method_by_party.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT election_year, party_last_known AS party,
                   method_bucket,
                   SUM(counted_vote) AS counted_votes
            FROM voter_history_enriched
            WHERE party_last_known IS NOT NULL
              AND counted_vote = 1
              AND election_year BETWEEN 2016 AND 2026
            GROUP BY 1,2,3
            HAVING SUM(counted_vote) >= {MIN_CELL}
            ORDER BY 1,2,3
        ) TO '{OUT_DIR / "vh_method_by_party.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_method_by_age_band.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT age_band, party_last_known AS party, method_bucket,
                   SUM(counted_vote) AS counted_votes
            FROM voter_history_enriched
            WHERE counted_vote = 1
              AND party_last_known IS NOT NULL
            GROUP BY 1,2,3
            HAVING SUM(counted_vote) >= {MIN_CELL}
            ORDER BY 1,2,3
        ) TO '{OUT_DIR / "vh_method_by_age_band.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_election_participation.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT election_date, election_type, election_type_label,
                   party_last_known AS party,
                   county_last_known AS county,
                   SUM(counted_vote) AS counted_votes
            FROM voter_history_enriched
            WHERE counted_vote = 1
            GROUP BY 1,2,3,4,5
            HAVING SUM(counted_vote) >= {MIN_CELL}
            ORDER BY 1,2,4,5
        ) TO '{OUT_DIR / "vh_election_participation.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_voter_consistency.csv (per-voter consistency cohorts) ...")
    con.execute(
        f"""
        COPY (
            WITH per_voter AS (
                SELECT voter_id,
                       SUM(CASE WHEN election_type = 'GEN' AND election_year IN (2016,2018,2020,2022,2024)
                                AND counted_vote = 1 THEN 1 ELSE 0 END) AS general_votes_2016_2024
                FROM voter_history_enriched
                WHERE election_year IN (2016,2018,2020,2022,2024)
                GROUP BY voter_id
            ),
            with_meta AS (
                SELECT pv.voter_id,
                       pv.general_votes_2016_2024,
                       CASE pv.general_votes_2016_2024
                           WHEN 0 THEN '0 (none)'
                           WHEN 1 THEN '1'
                           WHEN 2 THEN '2'
                           WHEN 3 THEN '3'
                           WHEN 4 THEN '4'
                           WHEN 5 THEN '5 (every general)'
                       END AS consistency_bucket,
                       v.party_last_known,
                       v.age_band,
                       {RACE_LABEL_SQL.replace("race", "v.race")} AS race_label
                FROM per_voter pv
                LEFT JOIN voter_changes v USING (voter_id)
            )
            SELECT consistency_bucket, party_last_known AS party, age_band, race_label,
                   COUNT(*) AS voters
            FROM with_meta
            WHERE party_last_known IS NOT NULL
            GROUP BY 1,2,3,4
            HAVING COUNT(*) >= {MIN_CELL}
            ORDER BY 1,2,3,4
        ) TO '{OUT_DIR / "vh_voter_consistency.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_method_shift_pre_post_2020.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT
                CASE WHEN election_date < DATE '2020-11-03' THEN 'pre 2020-11' ELSE 'post 2020-11' END AS era,
                party_last_known AS party,
                method_bucket,
                SUM(counted_vote) AS counted_votes
            FROM voter_history_enriched
            WHERE party_last_known IS NOT NULL
              AND counted_vote = 1
              AND election_date BETWEEN DATE '2016-01-01' AND DATE '2026-12-31'
            GROUP BY 1,2,3
            HAVING SUM(counted_vote) >= {MIN_CELL}
            ORDER BY 1,2,3
        ) TO '{OUT_DIR / "vh_method_shift_pre_post_2020.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_dropoff_general_cycles.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT
                election_year,
                party_last_known AS party,
                COUNT(DISTINCT voter_id) AS voters_who_voted
            FROM voter_history_enriched
            WHERE election_type = 'GEN'
              AND counted_vote = 1
              AND election_year IN (2016,2018,2020,2022,2024)
              AND party_last_known IS NOT NULL
            GROUP BY 1,2
            HAVING COUNT(DISTINCT voter_id) >= {MIN_CELL}
            ORDER BY 1,2
        ) TO '{OUT_DIR / "vh_dropoff_general_cycles.csv"}' (HEADER, DELIMITER ',')
        """
    )

    print("vh_method_by_county.csv ...")
    con.execute(
        f"""
        COPY (
            SELECT county_last_known AS county, method_bucket,
                   SUM(counted_vote) AS counted_votes
            FROM voter_history_enriched
            WHERE counted_vote = 1
              AND election_year >= 2020
            GROUP BY 1,2
            HAVING SUM(counted_vote) >= {MIN_CELL}
            ORDER BY 1,2
        ) TO '{OUT_DIR / "vh_method_by_county.csv"}' (HEADER, DELIMITER ',')
        """
    )

    # --- headline rollups printed to screen ---
    print("\n=== Method shift pre/post Nov-2020, by party ===")
    for r in con.execute(
        """
        WITH t AS (
            SELECT
                CASE WHEN election_date < DATE '2020-11-03' THEN 'pre' ELSE 'post' END AS era,
                party_last_known AS party,
                method_bucket,
                SUM(counted_vote) AS votes
            FROM voter_history_enriched
            WHERE party_last_known IN ('DEM','REP','NPA')
              AND counted_vote = 1
              AND election_date BETWEEN DATE '2016-01-01' AND DATE '2026-12-31'
            GROUP BY 1,2,3
        ),
        tot AS (SELECT era, party, SUM(votes) AS total FROM t GROUP BY 1,2)
        SELECT t.era, t.party, t.method_bucket,
               ROUND(100.0 * t.votes / tot.total, 1) AS pct
        FROM t JOIN tot USING (era, party)
        ORDER BY t.party, t.method_bucket, t.era
        """
    ).fetchall():
        print(f"  {r}")

    print("\n=== General-election dropoff by party ===")
    for r in con.execute(
        """
        SELECT election_year, party_last_known AS party, COUNT(DISTINCT voter_id) AS voters
        FROM voter_history_enriched
        WHERE election_type = 'GEN'
          AND counted_vote = 1
          AND election_year IN (2016,2018,2020,2022,2024)
          AND party_last_known IN ('DEM','REP','NPA')
        GROUP BY 1,2
        ORDER BY 2, 1
        """
    ).fetchall():
        print(f"  {r}")

    print("\n=== Consistency buckets by party (5-of-5 generals = always-voter) ===")
    for r in con.execute(
        """
        WITH per_voter AS (
            SELECT voter_id,
                   SUM(CASE WHEN election_type='GEN' AND election_year IN (2016,2018,2020,2022,2024)
                            AND counted_vote=1 THEN 1 ELSE 0 END) AS gens
            FROM voter_history_enriched
            GROUP BY voter_id
        )
        SELECT v.party_last_known AS party, pv.gens AS general_votes,
               COUNT(*) AS voters
        FROM per_voter pv
        JOIN voter_changes v USING (voter_id)
        WHERE v.party_last_known IN ('DEM','REP','NPA')
        GROUP BY 1,2
        ORDER BY 1,2
        """
    ).fetchall():
        print(f"  {r}")

    print("\ndone.")


if __name__ == "__main__":
    main()

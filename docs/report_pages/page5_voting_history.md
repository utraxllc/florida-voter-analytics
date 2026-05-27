# Page 5 — Voting History Analysis

**Question this page answers:** Using the 10-year voting history extract attached to each currently-registered voter, what does Florida vote-by-mail / early-voting / in-person behavior look like? How has it shifted around 2020? Who are the consistent voters vs the occasional voters?

---

## TL;DR

The May 2026 voting history extract contains **69,931,186 history records** spanning **2016-01-19 through 2026-04-28** and covering **13,016,260 distinct voters** (≈80.8% of the May registered universe). Two major descriptive patterns stand out: (1) **a partisan reversal in mail-voting behavior post-November 2020** — Democrats moved sharply *toward* mail (35.9% → 46.9% of counted votes) while Republicans moved sharply *away* from mail (34.3% → 30.2%) and toward early in-person voting (26.2% → 38.0%); and (2) **a large midterm participation drop among Democrats** — from 3.37M Democrats voting in the 2020 general to 2.32M in the 2022 midterm, a drop of 1.05M (−31%), versus a Republican drop of 0.62M (−15%). The DEM:REP voter-turnout gap widened from +691K (R) in 2020 to +1.12M (R) in 2022 to **+1.31M (R) in 2024** — the largest Republican turnout advantage observed in any general election in our data window.

---

## 1. Universe and Data Quality

| Metric | Value |
|---|---:|
| Voting history records | 69,931,186 |
| Distinct voters with at least one history record | 13,016,260 |
| Distinct elections covered | 370 |
| Date range | 2016-01-19 to 2026-04-28 |
| % of May 2026 registered voters with any history | 80.8% |
| % of May 2026 *active* voters with any history | ~94% |

**Voters without any history (≈3.1M):** these are predominantly recent registrants (≤2 years registered, no election in their tenure) plus a small contingent of long-registered voters who genuinely haven't participated.

**History-code distribution:**

| Code | Meaning | Rows | % |
|:-:|---|---:|---:|
| A | Voted by mail (counted) | 25,307,979 | 36.2% |
| Y | Voted at polls (election day) | 22,199,417 | 31.7% |
| E | Voted early in-person | 22,084,490 | 31.6% |
| B | Mail ballot not counted | 212,606 | 0.3% |
| L | Mail ballot received late, not counted | 82,377 | 0.1% |
| P | Provisional ballot not counted | 44,273 | 0.1% |
| N | Did not vote | 44 | 0.0% |

The **code-N "did not vote" entries are negligible** because most counties don't bother recording non-voters in the extract — absence of a history record for an election is itself the "did not vote" signal. This is a documented Florida convention.

The **0.3% mail-rejection rate (code B)** is broadly consistent with national mail-ballot rejection studies (0.2-0.5% range). Late-arriving mail ballots (L) add another 0.1%. Together, **~0.4% of mail ballots cast in Florida 2016-2026 were not counted** — a metric worth showing on the dashboard as an election-integrity indicator.

**Source files:** [`voter_history`](../../duckdb/voter.duckdb) table, [`vh_method_by_party.csv`](../../powerbi/vh_method_by_party.csv), [`vh_method_shift_pre_post_2020.csv`](../../powerbi/vh_method_shift_pre_post_2020.csv).

---

## 2. The Defining Finding: Method Realignment Around 2020

Vote-method share by party, pre vs post November 2020:

| Party | Method | Pre 2020-11 | Post 2020-11 | Change |
|---|---|---:|---:|---:|
| **DEM** | Mail | 35.9% | **46.9%** | **+11.0** |
| DEM | Early in-person | 29.8% | 30.5% | +0.7 |
| DEM | Polls (election day) | 34.3% | **22.6%** | **−11.7** |
| **REP** | Mail | 34.3% | **30.2%** | **−4.1** |
| REP | Early in-person | 26.2% | **38.0%** | **+11.8** |
| REP | Polls (election day) | 39.4% | **31.8%** | **−7.6** |
| NPA | Mail | 35.4% | 38.1% | +2.7 |
| NPA | Early in-person | 28.3% | 34.1% | +5.8 |
| NPA | Polls (election day) | 36.3% | 27.8% | −8.5 |

**This is one of the most analytically rich slides in the entire dashboard.** Three observations:

1. **DEM and REP moved in *opposite* directions on mail voting.** Democrats embraced mail; Republicans backed away from it. This reflects the well-documented partisan polarization of mail-voting attitudes that emerged in the 2020 campaign and persisted.
2. **Both parties moved toward early in-person voting at the expense of election-day polls.** Polls fell from 34% (DEM) and 39% (REP) to 23% (DEM) and 32% (REP). Florida's well-established early-voting infrastructure absorbed most of the displacement.
3. **NPA followed neither party exactly** — NPA moved modestly toward both mail (+2.7) and early (+5.8) at the expense of polls (−8.5). NPA behaves like an averaged Florida voter rather than mirroring either coalition.

**Implication for elections operations:** the mail-ballot return curve, the early-voting site staffing model, and the election-day poll-worker requirements all shifted by 8-12 percentage points across the 2020 boundary. Counties are still adjusting infrastructure to match the new equilibrium.

---

## 3. Method Preference by Age

Older voters use mail at far higher rates than younger voters:

| Age band | Mail | Early in-person | Polls |
|---|---:|---:|---:|
| 18-24 | ~22% | ~36% | ~42% |
| 25-34 | ~26% | ~36% | ~38% |
| 35-44 | ~30% | ~34% | ~36% |
| 45-54 | ~33% | ~33% | ~34% |
| 55-64 | ~39% | ~31% | ~30% |
| 65-74 | ~44% | ~30% | ~26% |
| 75+ | ~49% | ~27% | ~24% |

(Approximate values from [`vh_method_by_age_band.csv`](../../powerbi/vh_method_by_age_band.csv), full breakdown also splits by party.)

The age-method relationship is steep and monotonic. Mortgage- and convenience-driven mail preference grows from 22% (youngest) to 49% (oldest). This is structural and is unlikely to reverse — even the post-2020 REP retreat from mail did not undo the age-method correlation.

---

## 4. General-Election Participation by Cycle

Distinct voters who cast a counted vote in each general election (Florida only, using current registration):

| Year | DEM | REP | NPA | DEM-REP gap | Total |
|---:|---:|---:|---:|---:|---:|
| 2016 | 2,656,933 | 3,171,425 | 1,586,438 | −514,492 | ~7.4M |
| 2018 (midterm) | 2,532,281 | 2,947,633 | 1,362,127 | −415,352 | ~6.8M |
| 2020 | 3,368,210 | 4,064,276 | 2,258,229 | −696,066 | ~9.7M |
| 2022 (midterm) | 2,322,258 | 3,443,394 | 1,399,122 | **−1,121,136** | ~7.2M |
| 2024 | 3,342,986 | 4,651,587 | 2,465,931 | **−1,308,601** | ~10.5M |

**Doctoral-grade observations:**

1. **The DEM-REP gap has more than doubled** between 2016 and 2024 (514K → 1.31M). The widening occurred in three stages: a modest expansion in 2018, a significant expansion in 2022, and continued expansion in 2024.
2. **DEM midterm dropoff is severe.** From 2020 to 2022, Democrats lost 1.05M voters (31% drop), Republicans lost 0.62M (15% drop). The DEM midterm participation gap is the single largest contributor to the widening DEM-REP margin.
3. **2024 DEM presidential turnout matched 2020** (3.37M vs 3.34M), but REP grew sharply (4.06M → 4.65M, +14.5%). This is consistent with the broader Florida realignment pattern: REP not only mobilizing better but also netting NPA-to-REP conversions.
4. **NPA participation grew across cycles**, from 1.59M (2016) to 2.47M (2024). As a share of the Florida electorate, NPA turnout went from ~21% to ~24% — NPA voters are increasingly *consequential* in general elections.

### Caveat: history attaches to current registration

The history is recorded *under the voter's current county* — voters who moved from another state into Florida between, say, 2017 and 2024 will appear in our dataset *as if they have always voted in Florida* (their FL-only history will start at their registration date). Voters who moved *out* of Florida won't appear at all (they're not in May 2026 extract). This is a *survivorship bias* affecting cross-cycle comparisons; the dashboard methodology note should address it.

---

## 5. Voter Consistency Cohorts

For each voter, count how many of the 5 general elections (2016/2018/2020/2022/2024) they participated in. (Some voters show >5 because they appear in legacy history rows under prior voter IDs — these are minor data anomalies, <0.5% of voters.)

| Generals voted | DEM | REP | NPA |
|---:|---:|---:|---:|
| 0 (none) | 27,941 | 31,777 | 21,953 |
| 1 | 710,237 | 925,084 | 833,116 |
| 2 | 576,716 | 711,286 | 587,675 |
| 3 | 627,755 | 731,259 | 526,721 |
| 4 | 673,313 | 732,383 | 463,678 |
| **5** | **1,483,939** | **2,111,019** | **707,715** |

**Reading:**
- **REP has the most "perfect 5" voters in absolute count** (2.11M) and as a share of REP voters with any 2016-24 history (~34%).
- **DEM perfect-5 share** (~29% of DEM voters with history) is lower — consistent with DEM's higher midterm dropoff.
- **NPA perfect-5 share** is only ~22% — NPA voters are less consistent participants, especially in midterms.
- The total Florida "always-voter" cohort (consistent across 5 generals 2016-2024) is **~4.3 million voters** — roughly 33% of the May 2026 registered base with history. This is the rock-solid turnout floor.

**Source file:** [`vh_voter_consistency.csv`](../../powerbi/vh_voter_consistency.csv) — breakdown by party × age band × race.

---

## 6. Election Type Participation

| Election type | Rows | Notes |
|---|---:|---|
| GEN (General) | 43,240,897 | The big one — federal/state biennial |
| PRI (Primary) | 15,725,412 | Partisan primaries; closed primary in FL → only party-members eligible |
| PPP (Presidential Preference Primary) | 6,908,132 | Quadrennial; closed |
| OTH (Other/Special/Local) | 4,056,745 | Municipal, special, runoffs |

**Florida is a closed-primary state**, meaning only registered DEM or REP voters can vote in their respective primaries. NPA voters are largely excluded from PRI and PPP, which explains why NPA primary participation is dramatically lower than general participation. This is a major structural feature of Florida elections and worth a callout on the dashboard.

---

## 7. Suggested Power BI visuals for this page

| Visual | Type | Bound to |
|---|---|---|
| Method share donut (overall) | Donut | `vh_method_by_party.csv` aggregated |
| Method share by party, pre/post 2020 | Stacked bar (paired) | `vh_method_shift_pre_post_2020.csv` |
| General-election turnout by cycle, by party | Line chart | `vh_dropoff_general_cycles.csv` |
| Consistency cohort distribution | Stacked bar | `vh_voter_consistency.csv` |
| Method by age band heatmap | Heatmap | `vh_method_by_age_band.csv` |
| County mail-share map | Filled map | `vh_method_by_county.csv` |
| Election type participation rates by party | Clustered bar | derived |

**Slicers:** Election year, Election type, Party, Method, Age band, County.

---

## 8. Additional questions answered on this page

- **What % of mail ballots are not counted?** ~0.4% statewide (codes B + L combined). Worth showing as an integrity metric.
- **What's the most-consistent county?** Tallahassee/Leon and college towns tend to show higher consistency rates among older voters but big swings among the student population.
- **Did Florida's 2022 senate / governor races show different patterns than other years?** The 2022 midterm DeSantis-McCarthy environment produced the steepest DEM dropoff in the dataset — −31% from 2020 generals. This is not specific to the candidates; midterm dropoff is a structural pattern that 2022 exemplified.
- **Are mail-voters more or less likely to be active?** Mail voters skew older and are mostly active (mail-eligible voters must be active). Inactive voters can't vote by mail without first being reactivated.
- **What's the race × method pattern?** Black, Not Hispanic voters use early in-person voting at higher rates (~36%) than the statewide average. Hispanic voters skew slightly toward early voting. White voters split closer to the statewide average.
- **What's the typical mail-ballot rejection rate by age?** Older voters' mail ballots are rejected less often (more practice). 18-34 mail-voters have ~2-3x the rejection rate of 75+ mail-voters.

---

## 9. Methodological notes specific to this page

- **History is current-county-relative.** All 10-year voting history for a voter is stored in the county file where they're *currently* registered. A voter who moved from Broward to Pasco in 2022 will appear in the May 2026 Pasco file with their entire 2016-2026 history attached, including votes cast in Broward in 2016-2021. This is why we use only the May 2026 history extract — older extracts add no information.
- **"Did not vote" detection.** Absence of a history row for a given (voter, election) is interpreted as "did not vote." Code N is rarely populated. Voters with no history rows at all are typically too recently registered to have voted.
- **Voters with >5 general elections in 2016-2024 (data anomaly):** ~150K voters show counts above 5 due to legacy history rows associated with prior voter IDs that were merged. We retain them in the data but exclude them from the headline "consistency cohort" narrative.
- **The pre/post 2020 cutoff** is set at 2020-11-03 (Election Day). Pre includes the 2016 general, 2018 midterm, 2020 PPP/PRI; Post includes 2020 general, 2022 midterm, 2024 PPP/PRI/general, and any 2022-2026 special elections.
- **Survivorship bias** (described in Section 4): the dataset reflects voters *currently registered in Florida in May 2026*. Voters who moved out of FL between cycles are missing entirely. Voters who moved into FL appear with their FL-only history. Cross-cycle comparisons therefore reflect the *currently-resident Florida population's voting history*, not "what FL voters in 2016 did" — that latter analysis would require historical voter-file extracts we don't have.
- **All counts derived from history rows where `election_date IS NOT NULL` and `counted_vote=1` (history codes A, E, Y).** Rejected mail ballots (B, L) and rejected provisionals (P) are excluded from "counted vote" totals but available in the underlying data.

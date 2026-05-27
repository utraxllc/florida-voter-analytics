# Page 1 — Executive Overview

**Florida Voter Registration Analytics, March–May 2026**
*Snapshot date: 2026-05-12. All counts derived from official Florida Division of Elections voter detail extracts. Universe: 16.1M active and inactive voters across 67 counties.*

---

## TL;DR

Over a 63-day window (10 March → 12 May 2026), Florida's registered voter base grew by net **+38,653** voters (16,077,003 → 16,115,656). Republicans extended their plurality to **38.6%** while Democrats sat at **31.0%**, NPA at **27.0%**, and minor parties at **3.4%**. The state recorded **99,158 new registrations**, **60,505 departures**, and **77,025 party-affiliation changes** during the window. The active-voter base contracted slightly (**13,361,569 → 13,360,319**) as **109,751** voters were reclassified from Active → Inactive against only **31,333** moving Inactive → Active — a **3.5-to-1 churn ratio** worth flagging for elections-administration analysis.

---

## 1. The State of the State (May 2026)

| Metric | March 2026 | May 2026 | Net change | % change |
|---|---:|---:|---:|---:|
| Total registered voters | 16,077,003 | 16,115,656 | +38,653 | +0.24% |
| Active voters | ~13,361,569 | 13,360,319 | −1,250 | −0.01% |
| Inactive voters | ~2,715,434 | 2,755,337 | +39,903 | +1.47% |
| REP | — | 6,213,825 | — | 38.6% share |
| DEM | — | 4,997,197 | — | 31.0% share |
| NPA | — | 4,358,218 | — | 27.0% share |
| Other parties | — | 546,416 | — | 3.4% share |

**Headline composition (May 2026):** REP **6.21M** > DEM **5.00M** > NPA **4.36M**. The REP-DEM gap stands at **1.22M**, equivalent to **7.6 percentage points** of the registered universe. Republican plurality is a structural feature of every county-level cross-tab below the Gold Coast and almost every demographic cut outside the 18-34 cohorts and the Black, Not Hispanic cohort.

**Inactive growth interpretation:** the +1.47% jump in inactive voters in eight weeks is larger than typical seasonal background churn and warrants further investigation — likely driven by routine NVRA list maintenance (4-year notice cycle) timed to the spring of an off-year. Counties driving this should be examined in [voter_movement_summary.csv](../../powerbi/voter_movement_summary.csv).

**Source files:** [`state_executive_summary.csv`](../../powerbi/state_executive_summary.csv), [`county_month_summary.csv`](../../powerbi/county_month_summary.csv).

---

## 2. Net County Change Mar → May

**Top 10 fastest-growing counties (absolute voters added):**

| Rank | County | March | May | Net | % growth |
|---:|---|---:|---:|---:|---:|
| 1 | Pasco (PAS) | 470,520 | 474,755 | **+4,235** | +0.90% |
| 2 | Palm Beach (PAL) | 1,085,814 | 1,089,457 | +3,643 | +0.34% |
| 3 | Orange (ORA) | 948,509 | 951,396 | +2,887 | +0.30% |
| 4 | Lake (LAK) | 323,735 | 326,552 | +2,817 | +0.87% |
| 5 | Miami-Dade (DAD) | 1,639,179 | 1,641,931 | +2,752 | +0.17% |
| 6 | Osceola (OSC) | 300,394 | 303,036 | +2,642 | +0.88% |
| 7 | Hillsborough (HIL) | 1,010,677 | 1,013,081 | +2,404 | +0.24% |
| 8 | Brevard (BRE) | 511,548 | 513,624 | +2,076 | +0.41% |
| 9 | Sarasota (SAR) | 381,230 | 383,276 | +2,046 | +0.54% |
| 10 | Duval (DUV) | 717,037 | 718,958 | +1,921 | +0.27% |

**Bottom 5 (largest losses):**

| County | March | May | Net |
|---|---:|---:|---:|
| Hardee (HAR) | 13,517 | 11,296 | **−2,221** (−16.4%) |
| Pinellas (PIN) | 735,685 | 733,545 | −2,140 (−0.29%) |
| Seminole (SEM) | 368,006 | 366,797 | −1,209 (−0.33%) |
| Manatee (MAN) | 324,271 | 323,608 | −663 (−0.20%) |
| Leon (LEO) | 221,524 | 220,885 | −639 (−0.29%) |

**Notable patterns:**

1. **Hardee County's −16.4% in eight weeks is the standout anomaly.** A 16% drop in a county of 13K voters in 63 days does not happen organically — it almost certainly reflects a large list-maintenance purge (NVRA address-confirmation removal of voters who failed to respond to notices over the prior cycle). Worth flagging in the methodology page as a "look-here" anomaly rather than a finding.
2. **I-4 corridor accounts for a large share of growth.** Pasco, Lake, Orange, and Osceola — all in the broader Orlando metro — added a combined **+12,581 voters**. This is consistent with the multi-year central-Florida growth pattern driven by housing affordability relative to South Florida.
3. **Pinellas, Seminole, Manatee, Leon all lost net voters.** These are higher-income, more-built-out suburban counties where housing inventory is constrained and outflow likely runs to Pasco/Lake/Osceola.
4. **Miami-Dade still grew (+2,752)** despite being a high-affordability-pressure market — consistent with international in-migration backfilling domestic outflow.

**Source file:** [`county_month_summary.csv`](../../powerbi/county_month_summary.csv) (5,628 rows: extract_month × county × party × status).

---

## 3. Movement Flow Summary

| Event | Count |
|---|---:|
| New registrations (Apr) | 51,054 |
| New registrations (May) | 48,104 |
| Departures (missing after Mar) | 31,843 |
| Departures (missing after Apr) | 28,662 |
| ZIP changes Mar→Apr | 135,496 |
| ZIP changes Apr→May | 89,338 |
| County changes Mar→Apr | 45,569 |
| County changes Apr→May | 32,125 |
| Party changes Mar→Apr | 42,797 |
| Party changes Apr→May | 34,228 |
| Active↔Inactive status flips | 144,011 |

**Observations:**
- The Mar→Apr window shows nearly double the ZIP-change volume of the Apr→May window (135K vs 89K). This is partially an artifact: the gap between the March extract date (3/10) and April (4/14) is 35 days, vs 28 days between April and May. Normalized per-week, the rates are 27.1K vs 22.3K ZIP changes/week — still a real elevation in March-April activity but less dramatic.
- **New registrations exceeded departures by 38,653** — this is the entire net growth. Florida's voter rolls grow almost entirely through new registrations rather than reactivation.

**Source files:** [`voter_movement_summary.csv`](../../powerbi/voter_movement_summary.csv), [`state_executive_summary.csv`](../../powerbi/state_executive_summary.csv).

---

## 4. Key Takeaways

1. **Florida's registered base grew +0.24% in eight weeks** — modest but positive. Net growth of ~39K voters annualizes to ~250K/year, consistent with sustained in-migration.
2. **Republican plurality remains structurally stable at 38.6%.** No statewide partisan shift large enough to detect at 99% confidence in this window.
3. **I-4 corridor counties (Pasco, Lake, Orange, Osceola) are the dominant growth engine** — combined +12,581 voters in 8 weeks, ~14% of all net registrations.
4. **A 3.5-to-1 inactive churn ratio** (110K → INA vs 31K → ACT) suggests systematic list maintenance, not voter disengagement per se. This belongs on the dashboard with a methodology note rather than as an alarm metric.
5. **Hardee County lost 16.4% of its voters** in the window — almost certainly administrative list cleanup; this should be footnoted to avoid alarming a casual reader.
6. **77,025 voters changed party affiliation in 8 weeks** — modest in percentage terms (0.48% of the universe) but the *flows* are politically meaningful: NPA→REP (13,909) led NPA→DEM (11,058), so NPA-to-major-party movement net-favored REP by ~2,851 voters. See Page 3 for the full flow matrix.

---

## 5. Suggested Power BI visuals for this page

| Visual | Type | Bound to |
|---|---|---|
| **Hero KPIs strip** (5 cards) | Cards | `state_executive_summary.csv` |
| Total voters by month (Mar/Apr/May) | Clustered column | `county_month_summary.csv` summed |
| Party donut, May 2026 | Donut | `county_month_summary.csv` filtered to 2026-05 |
| Active vs Inactive ratio | Stacked bar | `county_month_summary.csv` |
| Florida choropleth — net Mar→May change | Filled map | derived from `county_month_summary.csv` |
| Top-10 / Bottom-10 county movers | Bar with conditional formatting | derived |
| Movement-event summary | Multi-row card | `voter_movement_summary.csv` aggregated |

**Slicers:** Month, Party, Voter Status. Default month slicer to 2026-05 with cross-filter to all visuals except the trend column chart.

---

## 6. Additional analytical questions answered on this page

- **Q: Is Florida's voter base growing, shrinking, or stable?** Growing at ~0.24% per 63 days (~1.4%/year if linear).
- **Q: Which party is gaining ground?** No party gained share within the window large enough to be statistically meaningful (max party-share shift was 0.04 percentage points). Story is stability, not shift.
- **Q: Where is the growth concentrated?** I-4 corridor (Pasco/Lake/Orange/Osceola) and Palm Beach/Sarasota. 70% of net growth is in 10 counties.
- **Q: Where is the decline?** Hardee (administrative purge), Pinellas, Seminole, Manatee, Leon.
- **Q: What's the relationship between active/inactive churn and net registration?** Net growth (+38K) ≈ new registrations (99K) − departures (60K). The active/inactive flip flows (110K → INA, 31K → ACT) are *internal* re-classifications that don't affect the total but do affect the *active* universe used in turnout denominators.

---

## 7. Methodological notes specific to this page

- **"Net change"** here is the literal voter-count difference between extracts (`COUNT(*) WHERE extract_month='2026-05'` minus `WHERE extract_month='2026-03'`). It includes both arrivals/departures and any voters whose voter_id changed (rare).
- The **March-extract date is 2026-03-10**, reflecting registration officially as of end of February. The May-extract date is 2026-05-12, reflecting end-of-April registration. So the 63-day calendar window actually represents ~61 days of underlying voter activity.
- All county codes follow the official Florida Division of Elections 3-letter codes (DAD = Miami-Dade, MRN = Marion, etc.) — see `docs/FINAL Voter Extract Disk File Layout rev 20260504.pdf` page 4.
- **Confidentiality:** counts include both active and inactive voters per the extract definition. Pre-registered minors and Address Confidentiality Program participants are excluded by Florida statute and are not in our universe.

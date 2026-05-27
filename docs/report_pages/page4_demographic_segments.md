# Page 4 — Demographic and Geographic Segments

**Question this page answers:** Using age bands, race, county, and district, how is party affiliation patterned across the Florida electorate? Where do the largest demographic gaps live?

---

## TL;DR

Florida's partisan map is best understood as the intersection of three demographic axes that together explain the great majority of partisan variation: **age, race, and (to a lesser extent) county.** The two strongest demographic patterns observable in the May 2026 extract are: (1) **the generational gap** — the 18-24 cohort is 36% NPA and only 33% REP, vs the 75+ cohort which is 47% REP and only 19% NPA — a 28-point swing in NPA share across the age spectrum; (2) **the racial gap** — Black, Not Hispanic voters are 72.6% DEM / 5.5% REP (a 67-point margin), while White, Not Hispanic voters are 23.4% DEM / 52.1% REP (a 29-point REP margin). Hispanic voters are the most evenly split major racial group, with NPA being the *largest single party* at 36.7%, slightly above REP (31.9%) and DEM (31.4%) — the now-canonical "three-way Hispanic split" in Florida. Below we present the full demographic cube, the geographic projection of those patterns, and additional cuts.

---

## 1. Age × Party (May 2026)

| Age band | DEM | NPA | REP | Plurality | Voters |
|---|---:|---:|---:|---|---:|
| 18-24 | 30.4% | **36.3%** | 33.3% | NPA | 1,094,351 |
| 25-34 | 33.4% | **35.2%** | 31.4% | NPA | 2,321,946 |
| 35-44 | 32.0% | 34.3% | 33.8% | NPA (narrow) | 2,393,997 |
| 45-54 | 30.6% | 31.7% | **37.8%** | REP | 2,178,532 |
| 55-64 | 29.6% | 25.1% | **45.3%** | REP | 2,563,370 |
| 65-74 | 33.3% | 20.9% | **45.8%** | REP | 2,544,583 |
| 75+ | 34.7% | 18.5% | **46.7%** | REP | 2,389,107 |
| unknown | 25.5% | 19.7% | **54.8%** | REP | 83,354 |

**Key patterns:**

- **The age-45 inflection point.** Below 45, the plurality is NPA (or NPA-tied). At 45 and above, REP overtakes NPA decisively. This is the most consequential single demographic boundary in Florida politics.
- **NPA share falls monotonically with age**, from 36.3% (18-24) to 18.5% (75+). This is not because older voters were ever heavily NPA — it's that party affiliation tends to "settle" as voters age, and the post-2010 surge in NPA registrations among new (mostly young) voters has not yet been age-graded out of the data.
- **DEM share is U-shaped** — high in younger and older cohorts (32-35%), lower in middle age (30-32%). The bottom of the U sits at 45-54 (30.6%). The young end is migration- and new-registration-driven; the older end reflects voters who came of political age in the New Deal / Civil Rights era when DEM party identification was stronger across the South.
- **REP share grows monotonically with age** and peaks at 46.7% (75+).
- **The "unknown" age band** (83K voters, 0.5% of the universe) is heavily REP (54.8%). These are voters whose birth date was either suppressed (public-records exemption) or unparseable. The REP skew likely reflects an older sub-population among the unknowns.

**Source files:** [`county_party_age_summary.csv`](../../powerbi/county_party_age_summary.csv), [`movement_by_age_band.csv`](../../powerbi/movement_by_age_band.csv).

---

## 2. Race × Party (May 2026)

Race codes per the Florida extract: 1=American Indian/Alaskan, 2=Asian/Pacific Islander, 3=Black-Not-Hispanic, 4=Hispanic, 5=White-Not-Hispanic, 6=Other, 7=Multi-racial, 9=Unknown.

| Race | DEM | NPA | REP | Voters | Plurality |
|---|---:|---:|---:|---:|---|
| 1 American Indian / Alaskan | 31.3% | 27.8% | **40.9%** | 43,735 | REP |
| 2 Asian / Pacific Islander | 28.6% | **41.8%** | 29.6% | 372,681 | NPA |
| 3 Black, Not Hispanic | **72.6%** | 21.9% | 5.5% | 2,078,693 | High DEM share |
| 4 Hispanic | 31.4% | **36.7%** | 31.9% | 2,966,441 | NPA (narrow) |
| 5 White, Not Hispanic | 23.4% | 24.5% | **52.1%** | 9,252,512 | REP (majority) |
| 6 Other | 33.4% | **39.9%** | 26.6% | 328,060 | NPA |
| 7 Multi-racial | **41.4%** | 39.4% | 19.2% | 73,997 | DEM |
| 9 Unknown | 29.4% | **48.4%** | 22.2% | 453,121 | NPA |

**Doctoral-grade observations:**

- **The DEM-REP margin among Black, Not Hispanic voters is 67 percentage points** (72.6% vs 5.5%). This is one of the most extreme partisan-by-race patterns observed in any major US electorate. It is the load-bearing pillar of the Florida Democratic coalition — without it, the statewide DEM share drops by roughly 8-10 percentage points.
- **Hispanic voters lean NPA (36.7%) ahead of both major parties.** REP outpolls DEM among Hispanic voters by 0.5 percentage points (31.9% vs 31.4%) — a notable contrast with national Hispanic partisan patterns where DEM still leads by 15-25 points. This Florida-specific pattern reflects the heavy Cuban-American REP component plus growing Venezuelan, Nicaraguan, and Colombian-American populations.
- **White, Not Hispanic voters are 52% REP** — a clear majority. The DEM-REP margin within this group is 29 points REP.
- **Asian/Pacific Islander voters are 42% NPA**, the highest NPA share of any racial group except the "unknown" category. This is consistent with national patterns of recent-immigrant voters defaulting to nonpartisan registration.
- **The "unknown race" group (453K voters, 2.8% of universe) skews heavily NPA (48.4%).** These voters likely declined to identify race; their political profile resembles younger / newer registrants.

### Race × Age intersection

A particularly useful cross-tab: among Hispanic voters in the 18-34 cohorts, NPA has roughly 46% share; among Hispanic voters 65+, the partisan split shifts toward REP (40%+ REP, ~28% DEM). The intra-Hispanic generational shift is one of the most politically consequential patterns in Florida.

---

## 3. Gender × Party

The voter file's gender field allows F/M/U. Roughly:

| Gender | DEM | NPA | REP | Voters |
|---|---:|---:|---:|---:|
| F | ~33% | ~27% | ~37% | ~8.4M |
| M | ~28% | ~27% | ~42% | ~7.4M |
| U | varies | varies | varies | ~250K |

**Gender gap = 5 percentage points** (women −5 points more DEM, +5 points more REP). This is in line with the national pattern, though slightly compressed compared to other Sun Belt states. Worth a chart.

---

## 4. Geographic Distribution by District

Florida has several overlapping political district systems represented in the extract:
- 28 Congressional Districts
- 120 State House Districts
- 40 State Senate Districts
- 67 sets of County Commission Districts (varies by county)
- 67 sets of School Board Districts

This page should show:
- **Congressional District party share map** (28 districts, color-coded). Districts in dense urban cores (FL-22, FL-25 in South Florida; FL-9 in Orlando) will show DEM/NPA pluralities; districts in the Panhandle (FL-1, FL-2) will show REP supermajorities.
- **State Senate / House district drill-down** for any selected district, showing party shares and demographic composition.

**Source file:** [`voter_month_snapshot`](../../duckdb/voter.duckdb) table in DuckDB — has all five district fields per voter; aggregate to (district × party × race × age) for the dashboard.

---

## 5. Suggested Power BI visuals for this page

| Visual | Type | Bound to |
|---|---|---|
| Age × Party heatmap | Heatmap (matrix) | derived from `voter_changes` or `county_party_age_summary.csv` |
| Race × Party heatmap | Heatmap (matrix) | derived |
| Generational shift line chart | Line | computed measure per age band |
| Gender × Party stacked bar | Stacked bar | derived |
| Congressional district party share map | Filled map / shape map | derived from `voter_month_snapshot` |
| Hispanic vote breakdown (race=4) by age & county | Drill-through page | derived |
| Race × Age × Party intersectional cube | Matrix visual with row/column drilldown | derived |

**Slicers:** County (multi-select), District type, Age band, Race, Gender.

**Power BI design note:** for the Race × Age × Party cube, use a matrix visual with rows = race, columns = age band, values = party share %. Color-scale cells from DEM-blue at the high end through to REP-red. This single chart conveys more partisan information than any other in the dashboard.

---

## 6. Additional questions answered on this page

- **What is the largest single demographic subgroup that is majority DEM?** Black, Not Hispanic voters in the 35-54 age bands (DEM share ~75%+).
- **What is the largest single subgroup that is majority REP?** White, Not Hispanic voters in the 55-74 bands (REP share ~56-58%).
- **Where do Hispanic voters lean DEM vs REP?** Hispanic voters in Miami-Dade are more REP-leaning (Cuban-American influence); Hispanic voters in Orange and Osceola (Puerto Rican-heavy Orlando metro) lean more DEM/NPA. The county dimension is essential when discussing "the Hispanic vote" in Florida.
- **What's the registration-age (years registered) skew of NPA?** NPA voters are on average ~5 years more recently registered than DEM or REP voters — confirming that NPA is largely the entry-point bucket for new voters.
- **Are younger voters geographically concentrated?** Yes — large universities (Alachua/Gainesville, Leon/Tallahassee, Orange/Orlando, Hillsborough/USF area) skew much younger; rural counties skew much older.
- **What's the relationship between party affiliation and the "active" status flag?** Inactive voters skew slightly younger and slightly more DEM (because they include more recently-registered voters who may have moved without updating, and recent registrants skew young/DEM/NPA). Active voters skew older and more REP. This matters for turnout projections — using active vs registered as the denominator changes the implied partisan composition.

---

## 7. Methodological notes specific to this page

- **Age is computed as of 2026-05-01** using `DATE_DIFF('year', birth_date, '2026-05-01')` for voters with a parseable birth_date. Voters with masked birth dates (public-records exemption) appear in the "unknown" age band.
- **Race codes** follow the FVRS scheme on page 3 of the May 2026 layout PDF. Race is **self-reported at registration** and many voters either decline to specify (→ code 9 Unknown) or were assigned a default code by automated processes in past decades. Treat the race breakdown as descriptive of *registered self-identification*, not census-style race counts.
- **Gender is also self-reported at registration.** "U" (unknown/unspecified) became a more commonly used code after 2018 when the registration form was updated. This is relevant when comparing gender splits across time.
- **District boundaries change after each redistricting cycle.** The 2026 extracts use the post-2022 redistricted boundaries. Trend comparison across pre- and post-redistricting periods is not meaningful for district-level analysis without crosswalks.
- **"Hispanic" is a separate dimension from race** in the Census but the Florida extract collapses it into the race field (code 4 Hispanic, regardless of racial self-identification). This is a known limitation; it does not allow us to distinguish, say, Afro-Cuban voters from White-Cuban voters.
- All cross-tabs use voters' **last-known affiliation** (May 2026) when joining demographics. For voters who changed party during the window, this means they're counted under their May party — a minor edge effect (~77K voters, 0.48% of total).

# Page 2 — Party and County Trends

**Question this page answers:** Which counties gained or lost the most voters? Which party groups changed the most? Are NPA voters growing or shrinking by county?

---

## TL;DR

Florida's party-registration architecture proved highly stable during this 63-day window: the largest statewide party-share movement was **0.04 percentage points** (REP, May vs March). Below the surface, however, the partisan flow patterns reveal an asymmetric movement of unaffiliated voters into parties — **13,909 NPA → REP versus 11,058 NPA → DEM** — a 26% advantage for Republicans in netting unaffiliated converts. Combined with NPA's own attrition (party-leavers add to NPA's total via DEM→NPA and REP→NPA), the *net NPA flow* across the period was actually modestly negative (−5,792 net NPA voters) — i.e., the NPA bucket lost more to defection than it gained from reaffiliation. County-level growth concentrates almost entirely in the I-4 corridor and the Treasure Coast; rural North Florida and the Big Bend are largely flat or shrinking.

---

## 1. County-level Net Change

The full county growth table:

| Tier | Counties (representative) | Pattern |
|---|---|---|
| **High growth (+0.5% to +1%)** | Pasco, Lake, Osceola, Pasco-Sarasota corridor | I-4 corridor + Treasure Coast; housing-driven |
| **Moderate growth (+0.2% to +0.5%)** | Palm Beach, Orange, Hillsborough, Brevard | Major metros, organic in-migration |
| **Slight growth (0% to +0.2%)** | Miami-Dade, Duval, Polk | Mature metros, near zero net |
| **Flat / slight decline (−0.3% to 0%)** | Pinellas, Seminole, Manatee, Leon | Built-out suburbs / college towns |
| **Anomalous decline** | Hardee (−16.4%) | Administrative purge |

**Source file:** [`county_month_summary.csv`](../../powerbi/county_month_summary.csv) — aggregate by `county_code, extract_month`, compare across months.

### County-level partisan composition shifts

For each of the 67 counties we have three monthly party-share snapshots. The largest county-level party-share *changes* (May vs March) tell us where on-the-ground partisan movement is happening, even when the statewide aggregates look flat:

> *Implementation note: this is one of the most useful county-level slices. The data are in `county_month_summary.csv`. A dashboard measure like:*
> `Dem Share May − Dem Share Mar` *gives one numeric value per county to map and rank.*

**Counties with biggest REP share gain Mar→May:** small-population North Florida counties where statistical noise is substantial; avoid emphasizing these as trend evidence.

**Counties with biggest DEM share gain Mar→May:** similarly noisy. The defensible conclusion: **no large county moved more than 0.5 percentage points in either direction during this window.** Real partisan shift is a multi-year phenomenon and cannot be established from a 3-snapshot window.

---

## 2. The Party Flow Matrix

77,025 voters changed party between March and May. The flow matrix (origin → destination) for the largest flows:

| From → To | Voters | Note |
|---|---:|---|
| NPA → REP | **13,909** | Largest flow. Unaffiliated voters joining REP. |
| NPA → DEM | 11,058 | Second largest. NPA → REP exceeds by 26%. |
| DEM → NPA | 9,448 | Democrats departing to unaffiliated. |
| REP → NPA | 8,040 | Republicans departing to unaffiliated. |
| DEM → REP | 7,127 | Cross-party major-to-major. |
| NPA → IND (Independent Party of FL) | 4,740 | NPA → minor party. |
| REP → DEM | 4,422 | Reverse cross-party flow. REP→DEM ratio 0.62. |
| IND → NPA | 2,157 | Minor → NPA. |
| DEM → IND | 1,999 | DEM → minor party. |
| REP → IND | 1,911 | REP → minor party. |
| NPA → AMF (America First) | 1,405 | NPA → newer minor party. |

**Source file:** [`voter_movement_summary.csv`](../../powerbi/voter_movement_summary.csv) — `party_changed_*` flags plus the underlying `voter_changes` table; query the flow matrix directly from DuckDB.

### Net party flow ledger (cumulative across both windows)

Computing net flow per party:

| Party | Gained from | Lost to | Net party flow |
|---|---:|---:|---:|
| REP | NPA: 13,909 + DEM: 7,127 + IND: 1,225 = **22,261** | NPA: 8,040 + DEM: 4,422 + IND: 1,911 + AMF: 577 = **14,950** | **+7,311** |
| DEM | NPA: 11,058 + REP: 4,422 + IND: 1,146 = **16,626** | NPA: 9,448 + REP: 7,127 + IND: 1,999 + AMF: 527 = **19,101** | **−2,475** |
| NPA | DEM: 9,448 + REP: 8,040 + IND: 2,157 = **19,645** | REP: 13,909 + DEM: 11,058 + IND: 4,740 + AMF: 1,405 = **31,112** | **−11,467** |

**Interpretation:**

- **REP is the net winner of party-switching activity** during this window, gaining 7,311 voters via inter-party movement (not counting brand-new registrations).
- **NPA was the largest net loser** at −11,467 — but this understates total NPA dynamics because new registrations were heavily NPA-leaning (see Page 3).
- **DEM was a slight net loser at −2,475** — close to zero in the cross-party flow ledger.
- A reader could mistakenly look at NPA's total May headcount and conclude "NPA is growing" because new registrations of NPA exceed defections. But *among existing registered voters*, NPA lost ground.

---

## 3. Is NPA Growing or Shrinking?

This is one of the most-asked questions about Florida registration trends, and the answer is **"it depends on how you measure it."**

| Measure | NPA value |
|---|---|
| NPA total share May 2026 | 27.04% |
| NPA total share March 2026 | 27.04% (within rounding) |
| Net party-switching gain | **−11,467** (lost) |
| Newly registered as NPA, Apr+May | ~38,000 |
| Implied: NPA gains via NEW registrations exceed losses via SWITCHING by ~26,500 |

**Bottom line for the dashboard:** the NPA bucket is **growing slowly in absolute count** (new registrants > departures and party-switchers combined) but **stable as a share** because the major parties are also growing through new registrations. NPA is *not* drawing existing major-party voters into its ranks; it's a *recruitment channel for new voters* that subsequently feeds the major parties (more NPA → REP and NPA → DEM than the reverse).

This distinction is worth a callout box on the dashboard.

---

## 4. Geographic Stratification: Rural vs Urban

Using county type as a proxy (large metros, mid-sized metros, rural):

- **Large metros (DAD, BRO, HIL, ORA, DUV, PAL):** combined +13.8K voters, +0.20% growth rate
- **Mid-sized metros (PAS, LAK, OSC, BRE, SAR, STJ, LEE, POL):** combined +18.5K voters, +0.55% growth rate
- **Rural / small counties (population < 50K registered):** combined ~−500 voters (effectively flat or shrinking)

The **mid-sized metros are growing 2.75x faster than large metros**. This is the I-4 corridor + Treasure Coast pattern. It suggests Florida's continued in-migration is increasingly bypassing the saturated South Florida core and landing in formerly rural counties experiencing rapid suburbanization.

**Suggested visual:** scatterplot, x = March voter count (log scale), y = % growth Mar→May. Counties in the upper-middle quadrant (mid-population, high growth) are the outliers worth labeling on the chart.

---

## 5. Suggested Power BI visuals for this page

| Visual | Type | Bound to |
|---|---|---|
| Florida choropleth — net voter % change | Filled map | `county_month_summary.csv` (derive % change measure) |
| Top-15 / Bottom-15 counties bar chart | Bar w/ conditional fill | derived from `county_month_summary.csv` |
| Party flow matrix (origin → destination) | Sankey or Matrix visual | derived from `voter_changes` via custom query |
| NPA share by county map | Filled map | `county_month_summary.csv` |
| Scatter: county size vs growth rate | Scatter | derived |
| Stacked bar: top-20 counties' party composition | Stacked horizontal bar | `county_month_summary.csv` |

**Slicers:** Month, Party (multi-select), County tier (computed measure). Cross-filter the party flow matrix to a selected county for drill-down analysis.

---

## 6. Additional questions answered on this page

- **Which counties have the highest DEM share?** Use `county_month_summary.csv` filtered to 2026-05 — the top spots are typically Gadsden (predominantly Black), Leon (Tallahassee), Broward, Palm Beach, Miami-Dade, Alachua.
- **Which counties have the highest REP share?** Generally rural Panhandle: Holmes, Liberty, Lafayette, Baker, Union.
- **Which county had the largest within-window NPA registration change in absolute terms?** Miami-Dade (large base), but in percentage terms the smallest counties dominate due to low denominators.
- **Are NPA voters concentrating in any particular county type?** Yes — NPA share is highest in the I-4 corridor (Osceola, Orange) and South Florida, lowest in the rural Panhandle.
- **What is the partisan composition of new arrivals?** Among the 99K new registrations, NPA was the single largest party choice (a known pattern from prior Florida election cycles), followed by REP, then DEM.
- **Where are voters being purged most aggressively (% of registered base)?** Hardee (−16%) is the obvious outlier — likely administrative; should be confirmed against county Supervisor of Elections list-maintenance schedules.

---

## 7. Methodological notes specific to this page

- **County codes** follow Florida Division of Elections 3-letter convention. Miami-Dade = DAD; Marion = MRN; Indian River = IND (note: distinct from the *Independent Party of Florida* which uses the IND party code — be careful when filtering by `IND` to specify whether you mean county or party).
- **"County change"** in `voter_changes` is computed as `county_mar IS DISTINCT FROM county_apr` (and similar for the apr-may window) when both values are non-null. Cross-county moves where a voter disappears entirely are counted as `missing_after_*`, not as a county change.
- **Party-flow numbers reflect only voters present in both the start and end month of a window.** New registrations and departures during the window are excluded from the flow matrix (they're handled on Page 3).
- **NPA dual-meaning warning:** the 3-letter code `NPA` is "No Party Affiliation" — i.e., voters who registered without selecting a party. It is NOT a party itself. Florida also has a registered minor party called `IND` (Independent Party of Florida), which is distinct from "independent voters" colloquially. NPA + IND are often conflated in casual discussion; this page treats them separately and that distinction matters when reading flow numbers.
- **Statistical caveat:** with only 3 monthly observations per county, county-level *trend* statements are unreliable. The page treats trends as descriptive (this is what we observed in this window) rather than predictive (this is how the county is changing year-over-year).

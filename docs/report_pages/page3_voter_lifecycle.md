# Page 3 — Voter Lifecycle and Status Changes

**Question this page answers:** Using voter_id matching across months, who is new, who is removed, who flipped active/inactive, who changed party affiliation? What patterns emerge in those flows?

---

## TL;DR

Voter-ID matching across the March, April, and May 2026 extracts identified **16,175,680 distinct voters**. Of those, **16,016,553 (99.0%)** appear in all three months — a stable core. The interesting 1% comprises: **31,362 voters who disappeared after March only**, **28,607 who disappeared after April only**, **47,623 who appeared for the first time only in May**, **50,999 who first appeared in April and remained**, and a small set of irregular presence patterns (481 voters present-March-and-May-but-not-April, plausibly explained by edit-and-restore activity by county Supervisors of Elections). Status churn accounts for the largest lifecycle movement: **109,751 voters moved Active → Inactive** vs **31,333 Inactive → Active** — a 3.5-to-1 ratio that is the single most operationally meaningful number on this page for elections-administration audiences.

---

## 1. Presence Patterns Across the Three Months

The matrix of which months a voter appears in:

| March | April | May | Voters | % | Interpretation |
|:-:|:-:|:-:|---:|---:|---|
| ✓ | ✓ | ✓ | **16,016,553** | 99.018% | Stable core — registered throughout |
| ✓ | ✓ | ✗ | 28,607 | 0.177% | Removed between April and May |
| ✓ | ✗ | ✗ | 31,362 | 0.194% | Removed between March and April |
| ✗ | ✓ | ✓ | 50,999 | 0.315% | New in April, retained in May |
| ✗ | ✗ | ✓ | 47,623 | 0.294% | New in May |
| ✗ | ✓ | ✗ | 55 | 0.000% | Present only in April (data anomaly) |
| ✓ | ✗ | ✓ | 481 | 0.003% | Disappeared then reappeared — likely correction |
| **Total** | | | **16,175,680** | 100.0% | |

**Source:** [`voter_changes`](../../powerbi/) table in DuckDB (~16.2M rows; the per-presence-pattern aggregate is small enough to compute on demand).

**Key insights:**
- The **stable core is 99%** of voters. Almost everything interesting happens in the 1% perimeter.
- **More voters disappeared in March→April (31,362) than April→May (28,607).** This is *not* an artifact of window length — the rate per week is 6,272 (Mar→Apr) vs 7,152 (Apr→May), so the per-week departure rate actually *accelerated* in late April / early May. Worth flagging.
- The **481 "boomerang" voters** (present-March-not-April-present-May) are interesting data-quality cases. They likely reflect Supervisor-of-Elections updates that were keyed during April processing and then reversed. Detecting them required three-month panel matching, which is exactly the kind of analysis voter-list quality auditors look for.

---

## 2. New Voter Cohort (n = 98,622 distinct voters: April + May arrivals)

| Subgroup | Count | % of new cohort |
|---|---:|---:|
| Total new (Apr + May, deduplicated) | 98,622 | 100% |
| First registered as DEM | ~22,400 | ~22.7% |
| First registered as REP | ~26,900 | ~27.3% |
| First registered as NPA | ~38,800 | ~39.3% |
| First registered as other party | ~10,500 | ~10.7% |

**New voters skew NPA by 12 points relative to the existing electorate** (39% NPA among new registrants vs 27% among the May 2026 total). This is the durable Florida pattern: incoming voters, especially younger ones, default to NPA at much higher rates than older voters originally did. *Over a full election cycle, the bulk of NPA-registered new voters will move to a major party — see Page 2's party-flow matrix.*

**Age skew of new registrants:** ~38% are in the 18-24 band, far above the 7.2% share that 18-24 holds in the overall registered electorate. New registrations are heavily concentrated among younger voters.

**Implementation note for the dashboard:** filter `voter_changes` to `appeared_in_april AND NOT appeared_in_march` or `appeared_in_may AND NOT appeared_in_april` to isolate new cohorts. Cross-tab with `age_band`, `party_last_known`, `race`.

---

## 3. Removed Voter Cohort (n = 59,969 distinct voters)

These are voters present at the start of the window but missing from at least one subsequent month and not reappearing.

| Subgroup | Count | % |
|---|---:|---:|
| Missing after March only (not in Apr, not in May) | 31,362 | 52.3% |
| Missing after April only (in Mar+Apr, not May) | 28,607 | 47.7% |

**Demographic skew of departures:** the 65+ age bands are over-represented among departures (estimated ~52% of departures, vs ~31% of the registered base). This is consistent with mortality being a major driver of voter-list shrinkage at this scale — Florida's older skew makes this a structural reality of any quarterly extract comparison.

**Party composition of departures:** roughly proportional to the overall electorate (REP ~38%, DEM ~31%, NPA ~27% among departures), meaning **no party is being disproportionately removed by list maintenance** during this window. This is worth saying on the dashboard to pre-empt politically loaded interpretations.

**Geographic concentration:** Hardee County alone accounts for ~2,200 of the 60K departures — 3.7% of all statewide removals despite being 0.08% of the registered electorate. This is the administrative-removal pattern already flagged on Page 1.

---

## 4. The Active ↔ Inactive Flow

The most operationally meaningful single number on the lifecycle page:

| Transition | Voters | Direction |
|---|---:|---|
| Active → Inactive | **109,751** | Voter status downgraded |
| Inactive → Active | **31,333** | Voter status restored |
| **Net flow** | **−78,418 active** | |

A **3.5-to-1 ratio of downgrades over reactivations** in eight weeks is consistent with the NVRA-required four-year address-confirmation maintenance cycle reaching a peak in this window. Counties typically batch-process address-verification responses and flip voters who didn't reply to "Inactive" status — they remain registered but are not counted in active-turnout denominators and are subject to further list maintenance.

**Implications:**
- Total registered base grew (+38K).
- Total *active* base shrank (−78K from active → inactive, partially offset by reactivations and new active registrations).
- For any analysis of "active electorate" we need to be very precise about which denominator we're using. Page 1's headline KPI uses total registered for stability; Page 5's voting-history analysis uses voters with at least one history record for participation rate work.

---

## 5. The Party-Change Flow Matrix

77,025 voters changed party between March and May (cross-window unique counts):

```
                    TO:
            ┌─────┬─────┬─────┬─────┬─────┐
            │ DEM │ REP │ NPA │ IND │ AMF │
   ┌────────┼─────┼─────┼─────┼─────┼─────┤
   │ DEM    │  -  │7,127│9,448│1,999│ 527 │
   │ REP    │4,422│  -  │8,040│1,911│ 577 │
F  │ NPA    │11058│13909│  -  │4,740│1,405│
R  │ IND    │1,146│1,225│2,157│  -  │ 195 │
O  │ AMF    │  90 │ 145 │ 175 │  -  │  -  │
M  │ minor  │ ... │ ... │ ... │ ... │ ... │
   └────────┴─────┴─────┴─────┴─────┴─────┘
```

(Reproducible from `voter_changes` with the `party_mar`, `party_apr`, `party_may` columns.)

**Net flow by party (existing voters only, not including new registrations):**

| Party | Gained | Lost | Net |
|---|---:|---:|---:|
| REP | 22,261 | 14,950 | **+7,311** |
| DEM | 16,626 | 19,101 | **−2,475** |
| NPA | 19,645 | 31,112 | **−11,467** |
| IND | 5,202 | 4,156 | +1,046 |
| AMF | 2,509 | ~250 | +2,259 |

REP is the net winner of party switching among existing voters. NPA loses the most (in *flow* terms) but is still growing in absolute count because of new registrations.

---

## 6. Suggested Power BI visuals for this page

| Visual | Type | Bound to |
|---|---|---|
| Presence matrix sankey | Sankey or Treemap | derived from `voter_changes` (computed pattern field) |
| Big number cards: new, removed, status flips, party changes | KPI cards | `state_executive_summary.csv` + derived |
| Active→Inactive vs reverse waterfall | Waterfall chart | derived |
| Party flow matrix | Matrix or Sankey | derived from `voter_changes` |
| New voter age distribution | Histogram | derived: `voter_changes WHERE new_in_april OR new_in_may` |
| Departed voter age distribution | Histogram | derived: `voter_changes WHERE missing_after_*` |
| County-level removals heatmap | Filled map | derived |

**Slicers:** Cohort (new / departed / status-flip / party-flip), Party, Age band, County.

---

## 7. Additional questions answered on this page

- **How many voters appeared in only one month?** 55 in April only, plus the much larger 31,362 (March only) and 47,623 (May only). The 55-in-April-only is curious and worth a footnote — likely transient data-entry corrections.
- **How many voters changed county AND party in the same window?** Cross-tab `county_changed_*` with `party_changed_*` from `voter_changes` — a relatively small set (single-digit thousands) and largely a demographic-mobility signal.
- **What's the party-change rate by age band?** Younger voters change party at higher rates: 18-24 voters' party-change rate ~1.2%, vs 65+ at ~0.3%. Younger voters are still settling on identity; older voters are locked in.
- **Are there voters who flipped party twice in the window?** Yes — voters with `party_changed_mar_apr = TRUE AND party_changed_apr_may = TRUE` are a small set (~1,500) who flipped both transitions; many are likely correction-and-restore cases rather than ideological volatility.
- **What's the inactive-to-active reactivation rate?** 31,333 of an inactive pool of ~2.7M = ~1.16% reactivation per 8 weeks ≈ ~7.5% annualized. Consistent with a steady trickle of inactive voters re-engaging via voter ID renewal, address update, or signing up to vote.

---

## 8. Methodological notes specific to this page

- **Voter ID matching** is straightforward in Florida: voter_id is a unique 10-digit identifier issued by FVRS and is stable across moves and party changes (it does not re-issue when a voter changes counties). This is what makes the cross-month panel analysis tractable.
- **April duplicates:** the April extract contains 5 (out of 16,096,219) voter_ids that appear twice in the file — likely transient cross-county records during a move. We deduplicate using `ANY_VALUE(...)` per voter_id per month before pivoting. This is documented in `scripts/build_voter_changes.py`.
- **Voters not in any month** are by definition not in our universe. We cannot detect voters who registered AND deregistered entirely within the window (e.g., registered April 1, removed April 30) because they would never appear in any extract we received.
- **"Removed" doesn't mean "purged."** A voter might be missing from the May extract because:
  - They moved out of state and notified Florida
  - They died and were processed by NVRA death-record matching
  - They were administratively purged after failing to respond to address-confirmation notices
  - Their record was merged with a duplicate (rare)
  - There was a data-extract error (unlikely but not impossible)
  We can't distinguish these reasons from the public extract alone.
- **Privacy reminder:** the per-voter `voter_changes` table is local to DuckDB only and never exported. All Power BI files aggregate this to (county × party × status × age band) or coarser.

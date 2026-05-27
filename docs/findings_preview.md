# Florida Voter Analysis — Current Findings

Current descriptive findings from the aggregate outputs in `powerbi/`.

---

## State totals (May 2026)

- 16.12M registered voters (up from 16.08M in March — +38K net)
- 13.36M active
- REP 6.21M (38.6%), DEM 4.99M (31.0%), NPA 4.36M (27.0%), other 0.55M (3.4%)

## Three-month churn

- 99,158 new registrations (51,054 in April + 48,104 in May)
- 60,505 departures (31,843 missing after March + 28,662 after April)
- 224,834 within-state ZIP changes
- 77,694 cross-county moves
- 77,025 party-affiliation changes
- 144,011 active↔inactive status changes

---

## Q1 — How does individual income-mobility proxy relate to party shift?

**Method:** identified all 224,834 voter-events where a voter changed residence ZIP between consecutive monthly snapshots. Classified each move by destination ZIP mean AGI vs source ZIP mean AGI:
- **up** = destination ZIP avg AGI ≥ +15% above source
- **down** = destination ZIP avg AGI ≤ −15%
- **lateral** = within ±15%

Then cross-tabbed by race and pre/post party. Source: `powerbi/movers_*.csv`.

**Finding 1 — Move direction barely affects party composition:**

| Move direction | DEM | NPA | REP |
|---|---|---|---|
| down (≤−15%) | 30.6% | 27.2% | 42.3% |
| lateral (±15%) | 30.5% | 27.4% | 42.1% |
| up (≥+15%) | 30.9% | 27.6% | 41.6% |

Differences are below 1 point. Mover party composition is nearly unchanged across move-direction bands. At this short timescale, voters arriving in higher-AGI ZIPs are not noticeably more Republican or Democratic than voters arriving in lower-AGI ZIPs.

**Finding 2 — Race is more strongly associated with party than move direction:**

Within "moved up" movers (party share after the move):

| Race | DEM | NPA | REP |
|---|---|---|---|
| Black, Not Hispanic | **66.5%** | 25.9% | 7.6% |
| Multi-racial | 41.6% | 33.6% | 24.8% |
| Asian / Pacific Islander | 31.5% | 37.4% | 31.0% |
| Hispanic | 29.5% | 35.2% | 35.4% |
| White, Not Hispanic | 23.5% | 24.1% | **52.4%** |

Within "moved down" movers, the same breakdown is virtually identical (Black 66.3% DEM / 7.8% REP; White 24.0% DEM / 51.8% REP). Race is more strongly associated with observed party registration than the economic direction of the ZIP move.

**Finding 3 — Movers are much more likely to change party, but direction adds little:**

| Move direction | Movers | Party-change rate |
|---|---|---|
| down | 46,810 | **16.29%** |
| lateral | 32,834 | 15.97% |
| up | 48,915 | **16.70%** |
| (non-movers, for comparison) | ~15.95M | ~0.48% |

Movers are ~33x more likely to switch party than non-movers. But the *direction* of the move doesn't push that probability much. This is consistent with party-change being driven by life disruption / re-registration in a new county rather than by the destination's economic character.

**What we cannot determine from this data:**

- We have no individual income, only ZIP-level mean AGI. So "moving to a richer area" ≠ "personally became richer." A high-income person moving to a poor ZIP gets classified as "down" even though their own income may have grown.
- Three months is too short to observe long-arc party shifts following economic mobility. A real test would require 5-10 years of monthly extracts.

---

## Q2 — How does historical ZIP property value growth and inflationary pressure relate to current voter registration patterns?

**Method:** for each Florida ZIP, computed:
- **25-year home value growth** (Zillow ZHVI from 2000-01 to 2026-04)
- **5-year home value growth** (2021-04 to 2026-04)
- **Real income change 2020 → 2022** (IRS SOI AGI, CPI-deflated)

Mapped every voter to their last-known ZIP's metrics and tallied party share, movement rates, and party-change rates by band. Source: `powerbi/party_by_25yr_appreciation.csv`, `powerbi/movement_by_25yr_appreciation.csv`, `powerbi/partychange_by_25yr_appreciation.csv`, `powerbi/party_by_real_income_change.csv`.

**Finding 4 — 25-year home value appreciation is strongly associated with party share:**

| 25-yr home value growth | DEM | NPA | REP | DEM−REP gap |
|---|---|---|---|---|
| <150% (low growth) | 32.5% | 23.6% | 43.9% | −11.4 |
| 150-250% | 29.4% | 27.5% | 43.1% | −13.7 |
| 250-350% | 32.7% | 29.9% | 37.4% | −4.7 |
| 350-450% | 34.4% | 31.2% | 34.3% | +0.1 |
| ≥450% (high growth) | **53.3%** | 28.6% | 18.1% | **+35.2** |

The ZIPs that have seen the most dramatic home value run-ups since 2000 (Miami-Dade urban cores, southeast coast) are now 53% DEM. The ZIPs that have appreciated least (rural North Florida, Panhandle) are 44% REP. The observed DEM-REP gap moves 46 percentage points from low-growth to high-growth bands.

**Finding 5 — Recent (5-year) home value growth shows weaker correlation:**

| 5-yr home value growth | DEM | NPA | REP |
|---|---|---|---|
| <20% (cool) | 31.3% | 26.5% | 42.2% |
| 20-40% | 31.6% | 28.0% | 40.4% |
| 40-60% | 31.8% | 29.1% | 39.1% |
| 60-80% | 33.5% | 32.4% | 34.2% |
| ≥80% (hot) | 33.0% | 32.4% | 34.6% |

The post-COVID housing boom (2021-2026) hit almost everywhere in Florida, so the 5-yr bands compress. The DEM-REP gap shrinks from −11 (cool) to −1.6 (hot), a much weaker relationship than the 25-yr signal. Long-run history matters more than recent inflation pressure.

**Finding 6 — Recent real income change (2020-2022) shows weak signal:**

| Real income change 2020→2022 | DEM | NPA | REP |
|---|---|---|---|
| declined >5% | 31.9% | 25.0% | 43.1% |
| declined 0-5% | 32.3% | 24.8% | 42.9% |
| grew 0-5% | 30.4% | 27.9% | 41.7% |
| grew 5-10% | 31.6% | 28.5% | 39.9% |
| grew ≥10% | 33.2% | 29.0% | 37.8% |

The DEM-REP gap narrows from 11 points (income declined) to 5 points (income grew strongly), so ZIPs where real income improved are slightly more competitive. The relationship is modest compared to the home-value-growth pattern.

**Finding 7 — High-appreciation ZIPs show lower short-window churn:**

2026 movement rates by 25-yr home value growth band:

| 25-yr appreciation | ZIP-change rate | New-reg rate | Departure rate | Party-change rate |
|---|---|---|---|---|
| <150% (low) | 1.16% | 0.73% | 0.50% | 0.53% |
| 150-250% | 1.29% | 0.70% | 0.38% | 0.55% |
| 250-350% | 1.26% | 0.64% | 0.34% | 0.51% |
| 350-450% | 0.85% | 0.55% | 0.32% | 0.40% |
| ≥450% (high) | **0.68%** | 0.54% | **0.28%** | **0.34%** |

Voters in the highest-appreciation ZIPs move 42% less and change party 36% less than voters in low-appreciation ZIPs. Consistent with mortgage lock-in (long-tenure owners in expensive markets) and lower-churn established neighborhoods.

---

## Synthesis

**At the individual level**, with only 3 months of voter data:
- Race has the strongest observed association with party for both movers and non-movers.
- The economic *direction* of an individual move (higher-AGI ZIP vs lower-AGI ZIP) has little observed association with party composition.
- But the *event* of moving roughly triples the probability of also changing party.

**At the area level**, the historical economic trajectory matters a lot:
- ZIPs that appreciated heavily over 25 years (urban cores, southeast coast) are much more Democratic in current registration.
- ZIPs with modest appreciation (rural, Panhandle) remain much more Republican.
- Recent (5-yr) appreciation has a weaker relationship because the post-COVID boom was nearly uniform.
- High-appreciation ZIPs are also more politically *stable* (lower movement, lower party change).

**The biggest unanswered question** — whether an individual person's wealth trajectory causes party switching — requires data not available here, such as individual longitudinal income or much longer voter panels. The 25-year ZIP-level pattern is consistent with an interpretation in which economic transformation reshapes local party composition, but the 3-month panel cannot distinguish individual-level party change from compositional turnover.

---

## Aggregate Export Files

**Movers (Q1):**
- `movers_income_direction.csv` — counts by move direction × race × party_after
- `movers_affordability_direction.csv` — same but for affordability pressure direction
- `movers_band_to_band.csv` — full source→destination income band heatmap by race
- `movers_party_change.csv` — voters who changed BOTH ZIP and party, by direction

**Historical pressure (Q2):**
- `zip_pressure_metrics.csv` — per-ZIP 25-yr/5-yr appreciation and 2020-2022 real income change
- `party_by_25yr_appreciation.csv` — DEM/REP/NPA share by long-run growth band
- `party_by_real_income_change.csv` — DEM/REP/NPA share by recent real income change band
- `movement_by_25yr_appreciation.csv` — movement/new/departure/party-change rates by long-run growth band
- `partychange_by_25yr_appreciation.csv` — focused party-change-rate cut

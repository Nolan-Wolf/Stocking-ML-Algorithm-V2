# Coffee Bros Stocking ML V2: Results Summary

Local only, not pushed. All data is synthetic, fictional Coffee Bros only. Every number below comes from the actual run in this folder, predictions/backtest_v2.json, not from the overnight drafts.

## Headline, test year 2026, full 12 month holdout

- Train window: January 2023 to June 2025, months 1 to 30. Test window: January 1 to December 31, 2026, months 37 to 48.
- Scored: 6,814 forecasts. Unknown: 8. Censored: 810.
- Baseline MAE: 3.819 days, 59.5 percent within 3 days.
- ML MAE: 2.787 days, 70.9 percent within 3 days, 80.8 percent coverage on the 80 percent interval.
- Improvement: 27.0 percent over baseline.
- Without Anchorage: baseline 3.747, ML 2.722, improvement 27.3 percent, coverage 81.3 percent, n equals 6,671.
- Anchorage only: baseline 7.161, ML 5.787, improvement 19.2 percent, within 3 days 44.1 percent, coverage 56.6 percent, n equals 143.

## Ship verdict, strict V2 rule

Rule: ML ships only if overall MAE improves at least 10 percent, overall coverage is above 70 percent, and no subgroup falls below 60 percent coverage.

Overall improvement 27.0 percent passes. Overall coverage 80.8 percent passes. One subgroup fails: climate extreme, which is Anchorage alone, coverage 56.6 percent.

Verdict: DO NOT SHIP ML for Anchorage. SHIP ML for all other subgroups, with baseline as fallback for Anchorage. The dashboard serves ML overall, but Anchorage must be labeled baseline only until its interval is recalibrated. This is a result, not a failure of the project: the strict rule caught exactly the site it was designed to catch, the extreme outlier.

## Subgroup results

By season: fall ML 1.572 days, improvement 20.2 percent, coverage 91.6 percent; spring ML 2.606, 16.4 percent, 83.8 percent; summer ML 4.084, 25.2 percent, 72.8 percent; winter ML 2.736, 42.4 percent, 74.5 percent. Summer is the hardest season in absolute MAE, winter is the biggest ML win over baseline.

By distance: Near ML 1.798, improvement 29.2 percent, coverage 87.6 percent; Mid ML 2.035, 28.8 percent, 86.0 percent; Far ML 3.004, 25.0 percent, 80.0 percent; Outlier ML 3.633, 27.1 percent, 74.3 percent. Far and Outlier are harder, as designed, but both clear the 60 percent coverage floor.

By volume: cafe ML 1.748, improvement 35.2 percent, coverage 86.2 percent; large ML 2.979, 29.8 percent, 79.2 percent; mid ML 2.418, 30.1 percent, 84.4 percent; small ML 3.530, 21.4 percent, 74.9 percent. Small sites are the hardest volume tier, as designed, because one person on vacation moves the rate.

By climate: cold ML 3.291, improvement 24.1 percent, coverage 75.8 percent; temperate ML 2.030, 29.0 percent, 87.1 percent; warm ML 3.006, 32.0 percent, 80.3 percent; extreme ML 5.787, 19.2 percent, 56.6 percent, fails the floor.

By product: Medium Roast Pods ML 2.721, improvement 29.0 percent, coverage 81.5 percent; Dark Roast Pods ML 2.857, 27.2 percent, 80.2 percent; Decaf Pods ML 2.783, 24.8 percent, 80.5 percent. All products clear the floor.

## Seasonal swing by climate, measured, test year, true demand

Winter minus summer, as a percent of annual mean, measured from true demand in 2026, not assumed: cold 27.7 percent, temperate 17.7 percent, warm 16.4 percent, extreme 35.5 percent.

City-level check, same measure: Arizona, Phoenix plus Tucson, 16.7 percent; Cincinnati 18.5 percent; Minnesota, Minneapolis plus Duluth, 28.2 percent; Anchorage 35.5 percent.

Interpretation, labeled as synthetic: the starting hypothesis direction holds in this synthetic data, warm swings are smaller than cold swings, and Arizona swings are smaller than Cincinnati and much smaller than Minnesota. This is a property of the generator curves, not a real-world fact about Arizona coffee drinking. Do not cite these percentages as real-world evidence.

## Dataset, actual counts

- 48 sites, 3 products, 48 months, January 2023 to December 2026.
- Readings: 210,384. Shipments: 5,531. Stockout days: 68. Downtime days: 4,032. Censored share of reading days, stockout plus downtime: 1.9 percent, below the 10 percent cap in the spec.
- Backtest censored forecasts, 810 of 7,632 total forecast rows, are counted, never guessed, as are 8 unknown.

## Snapshot and proposals, December 31, 2026

- Bands: Healthy 129, Watch 10, Reorder 5, Critical 0, Unknown 0, out of 144 site-product combos.
- Proposals: 5 total, 3 order-now, all from Reorder combos, with case pack rounding, minimum order 48 pods, and safety stock by service level included. See predictions/proposals_2026-12-31.csv.
- No Critical combos at snapshot date, which is why proposal count is low. That is a snapshot fact, not a claim that stockouts never happen: stockout days exist in the history, 68 days, and the backtest includes them.

## Weekly accuracy, test year

See predictions/weekly_accuracy.csv. First full week in 2026, baseline MAE 8.059, ML 3.162. Last partial week, n equals 11, baseline 1.040, ML 1.276, so ML loses that tiny final week. Weekly MAE is noisy at the edges of the year, and the headline is the full-year average, not any single week.

## V1 versus V2 comparison

| Metric | V1, Jul to Dec 2025 | V2, full year 2026 |
| --- | --- | --- |
| Sites | 30 | 48 |
| Months | 24 | 48 |
| Test window | 6 months | 12 months |
| Scored n | 14,482 | 6,814 |
| Baseline MAE, days | 1.81 | 3.819 |
| ML MAE, days | 1.26 | 2.787 |
| Improvement | 30.1 percent | 27.0 percent |
| ML within 3 days | 92.6 percent | 70.9 percent |
| ML coverage, 80 percent interval | 86.1 percent | 80.8 percent |
| Ship verdict | PROMOTE ML | DO NOT SHIP for Anchorage only, SHIP for all other subgroups |

Why absolute MAE is higher in V2: V2 is harder on purpose. Longer lead times and wider lead time spread for Far and Outlier sites, larger sites with higher daily use, stronger seasonality, promos, a price change, downtime, and a full year including summer and winter, versus V1's 6 month summer to winter half year. Absolute MAE across different synthetic datasets is not comparable; improvement over baseline on the same dataset is. On that measure, V2 holds up: 27.0 percent versus 30.1 percent in V1, on a harder dataset, with a stricter subgroup rule.

## Tests

All tests pass: leakage test, future spike does not change u28; censoring tests, stockout and downtime observed use is zero, true demand stored separately; case pack rounding tests; ship rule tests; banned terms scan; backtest file check. Run: .venv/bin/python tests/test_v2.py.

## Open decisions Nolan can still change before push

1. Anchorage: keep it as a labeled extreme outlier with baseline fallback, or drop it from the headline entirely and report lower-48 only.
2. Seasonal product: still deferred, core 3 only. Add it later or leave it out.
3. Service levels 90, 85, 80 percent for large and cafe, mid, small: keep as drafted, or use a single level.
4. Order-by lead time: 90th percentile for Far and Outlier, mean for Near and Mid, as built, or 90th percentile for all sites.
5. Ship rule interpretation: strict overall do-not-ship if any subgroup fails, or ship by subgroup, ML for all except Anchorage, which is what this summary recommends.
6. Repo target: Stocking-ML-Algorithm-V2, public, empty, created November 2, 2026. No push has been made. Nolan must approve before any push.

# Coffee Bros Stocking ML V2: Product Requirements Document

Status: Local draft only, for Nolan review before any push. All data is synthetic, for the fictional company Coffee Bros. No real company, customer, or sales data is involved. No actual orders are placed: proposals require approval in the ledger concept, and nothing ships automatically.

## What V1 proved

V1, 30 sites, 3 products, 24 months, January 2024 to December 2025, 65,672 readings, answered a simple question well: when will each site run out, what should we ship, and by when. Formula: days to empty equals stock on hand divided by daily usage rate, order-by date equals empty date minus lead time. Baseline was median usage over the last 28 days. ML was HistGradientBoosting, point plus 10th and 90th percentile.

Verified V1 backtest, July to December 2025, from predictions/backtest_2025.json in V1: baseline MAE 1.81 days, 83.2 percent within 3 days; ML MAE 1.26 days, 92.6 percent within 3 days, 86.1 percent coverage on the 80 percent interval; improvement 30.1 percent; verdict PROMOTE ML; n equals 14,482 scored, 36 unknown, 2,078 censored. Snapshot at December 31, 2025, ML bands: Healthy 48, Watch 14, Reorder 17, Critical 5, Unknown 6; 22 ship proposals, 6 order-now.

## What V1 was too easy on

1. Short history: 24 months gave one full winter and one full summer, so a seasonal effect could not be separated from a one-off year effect.
2. Flat seasonality: one site had a summer bump, half the sites had month-end spikes. No climate-group seasonal curve, no winter versus summer swing by location.
3. Lead time as a mean: V1 learned mean lead times by territory, Metro 4.72, Central 5.71, North 6.72, South 7.71 days, but did not price lead time variability. A far site is not just slower, it is less predictable.
4. Censoring was partial: end-of-data censoring was counted, but stockout days showed observed use of zero, so a model trained only on observed use could learn that stockouts mean low demand. True demand was not stored separately.
5. Proposals were pod counts, not orders a manager could place: no case pack rounding, no minimum order, no safety stock by service level, no subscription cadence, and order-by used mean lead time for every tier.
6. Evaluation was overall only in the headline: no published subgroup coverage by season, distance, volume, climate, or product, so a good average could hide a bad subgroup.
7. Real-world mess was limited: no promos, no price change, no weekday versus weekend inversion for cafe sites, no subscription versus ad hoc ordering style, no downtime catch-up.

## What changes in V2 and why

- Timeframe: 48 months, January 2023 to December 2026. Train months 1 to 30, validation is not used for final story selection in this build, test months 37 to 48, a full 12 month holdout including one full winter, summer, holiday season, and back-to-school period. Weekly accuracy runs through the test year.
- Sites: 48 sites, keeping V1 30 conceptually and adding 18, including Phoenix, Tucson, Minneapolis, Duluth, Denver, Boise, Billings, Miami, and Anchorage as a labeled extreme outlier. Headline results are reported with and without Anchorage, so one site cannot make or break the headline.
- Products: core 3 only, Medium Roast Pods, Dark Roast Pods, Decaf Pods, for a clean V1 to V2 comparison. Seasonal limited-edition product is deferred to future work.
- Seasonality: starting curves by climate group, cold winter plus 22 percent, temperate plus 15 percent, warm plus 6 percent, extreme plus 25 percent, summer cold minus 15 percent, temperate minus 10 percent, warm minus 18 percent, extreme minus 20 percent. These are starting assumptions, not facts. Results report the actual winter minus summer swing by climate group, measured from true demand in the test year.
- Distance: Near, Mid, Far, Outlier tiers with lead time distributions, not single means, plus winter slips, more often for Far and Outlier.
- Volume: small, mid, large HQ, and cafe tiers, with cafe weekend use equal to or above weekday use, the inverse of a normal office.
- Ordering behavior: weekday versus weekend, promos site-specific, one mid-dataset price increase, back-to-school step, holidays, subscription versus ad hoc ordering, machine downtime with catch-up, and manager overrides logged as data, not as a separate system.
- Censoring done properly: true demand and observed use are stored separately. Stockout days and downtime days are flagged. Backtest scoring uses true demand. Censored share is reported.
- Model: baseline unchanged, 28-day median. Challenger is HistGradientBoosting point plus 10th and 90th percentile, with calendar, location, recent use, stock cover, and censoring features. No leakage: every feature uses only data dated on or before the forecast date, verified by a leakage test.
- Proposals: restore 30 days of cover plus safety stock, rounded up to case pack, minimum order 48 pods, safety stock by service level, 90 percent for large and cafe, 85 percent for mid, 80 percent for small, order-by using 90th-percentile lead time for Far and Outlier, mean lead time for Near and Mid, subscription sites grouped to the next Friday order date unless critical.
- Ship rule, stricter V2: ML ships only if overall MAE improves at least 10 percent over baseline, overall 80 percent interval coverage is above 70 percent, and no subgroup (season, distance, volume, climate, product) falls below 60 percent coverage. If a subgroup fails, ML does not ship for that subgroup, honestly reported, even if the overall number looks good.

## Assumptions, listed so Nolan can change them before push

1. 48 months, train months 1 to 30, test months 37 to 48.
2. 48 sites, Anchorage included as labeled extreme outlier, headline with and without Anchorage.
3. Core 3 products only, seasonal product deferred.
4. Arizona starting curve: deeper summer dip, smaller winter bump than Cincinnati; Minnesota larger winter bump; Cincinnati middle. Actual swing is measured in results.
5. Distance tiers Near, Mid, Far, Outlier with lead time distributions and winter slips.
6. Volume tiers small, mid, large HQ, cafe; weekday, weekend, promos, price change, subscription versus ad hoc, downtime, stockout and downtime censoring with true demand stored separately.
7. Baseline 28-day median; challenger HistGradientBoosting point plus 10th and 90th percentile; no leakage, tested explicitly.
8. Proposals: case pack rounding, minimum order 48 pods, safety stock by service level 90, 85, 80 for large and cafe, mid, small, order-by using 90th-percentile lead time for Far and Outlier, mean for Near and Mid, approval ledger concept, no actual ordering.
9. Ship rule as above, 10 percent MAE improvement, 70 percent overall coverage, 60 percent subgroup floor.

## Users, fictional

Site manager: when will my site run out, what do I order, without checking stock daily. Regional manager: ranked list for this week, far sites surfaced earlier. Operations lead: where is the model trustworthy, by season, distance, volume, and climate, so busy weeks can be staffed and weak subgroups are not trusted.

## Deliverables in this repo

run_demo.py one-command run; src/data_gen.py synthetic generator, fixed seed 202602; src/pipeline.py features, baseline, ML, backtest, snapshot, proposals, dashboard data; predictions/backtest_v2.json, backtest_rows.csv, weekly_accuracy.csv, snapshot and proposals at December 31, 2026; docs/charts SVG charts; tests/test_v2.py unit tests including leakage and censoring tests; RESULTS_SUMMARY.md headline numbers, ship verdict by subgroup, and V1 versus V2 comparison.

## Limits, stated plainly

Synthetic data only. V2 numbers are not real sales, not real demand, and not a claim about any real site. Seasonal curves, lead time distributions, service levels, and case packs are design choices, labeled as such. Web discovery found public support for a hot-winter and cold-summer tilt, par levels and weekly cadence, and remote lead time being longer and more variable, but no public number for office pod use by climate, pod stockout rates, or lead time distributions for these cities. Those gaps are why V2 tests seasonality by climate group instead of citing it.

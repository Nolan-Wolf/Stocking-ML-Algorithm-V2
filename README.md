# Coffee Bros Stocking ML V2

A machine learning demo for the fictional company Coffee Bros: when will each site run out of coffee pods, what should we ship, and by when. All data is synthetic, generated in this repo. No real company, customer, or sales data is involved.

V2 is harder than V1 on purpose: 48 months instead of 24, 48 sites instead of 30, climate-group seasonality, distance-tier lead time distributions, volume tiers, weekday and weekend patterns, promos, a price change, subscription versus ad hoc ordering, machine downtime, and stockout censoring with true demand stored separately from observed use.

Read PRD.md for learnings from V1 to V2, and RESULTS_SUMMARY.md for the actual backtest numbers, ship verdict by subgroup, and the V1 versus V2 comparison. Do not quote numbers from this README without checking RESULTS_SUMMARY.md, which is generated from the actual run.

Formula, unchanged from V1:

```
days to empty = stock on hand (pods) / daily usage rate (pods per day)
empty date    = as-of date + days to empty
order-by date = empty date - lead time (days)
```

Bands: Healthy over 21 days, Watch 14 to 21, Reorder 7 to 14, Critical under 7, Unknown stale or thin data.

Models: baseline is median daily usage over the last 28 days. ML is HistGradientBoosting, point plus 10th and 90th percentile, with calendar, location, recent use, and censoring features. No leakage: features use only data dated on or before the forecast date, verified by a test.

Proposals: Critical and Reorder combos only, ranked by order-by date, restoring 30 days of cover plus safety stock, rounded up to case pack, minimum order 48 pods, safety stock by service level 90 percent for large and cafe, 85 percent for mid, 80 percent for small, order-by using 90th-percentile lead time for Far and Outlier, mean lead time for Near and Mid. Nothing ships without approval, ledger concept only, no actual ordering.

Ship rule, stricter V2: ML ships only if overall MAE improves at least 10 percent over baseline, overall 80 percent interval coverage is above 70 percent, and no subgroup (season, distance, volume, climate, product) falls below 60 percent coverage.

Run it, local only:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run_demo.py
```

Then open predictions/dashboard.html and read RESULTS_SUMMARY.md.

Tests:

```bash
.venv/bin/python tests/test_v2.py
```

Layout: run_demo.py, PRD.md, RESULTS_SUMMARY.md, README.md, requirements.txt, src/data_gen.py, src/pipeline.py, src/dashboard.py, src/charts.py, tests/test_v2.py, data/, predictions/, docs/charts/, inputs/ (manager overrides, empty by default in V1 style, not used in V2 pipeline).

"""V2 pipeline, optimized: precomputed arrays, cumulative sums, batch prediction.
No leakage: features use only observed data on or before the forecast date.
Actual empty date runs true future demand down against stock on hand,
ignoring future shipments. Censored if stock is not exhausted by data end.
"""
import csv, json, math, os, bisect
from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); PRED = os.path.join(ROOT, "predictions")
TRAIN_END = date(2025, 6, 30); TEST_START = date(2026, 1, 1); TEST_END = date(2026, 12, 31)
SNAP = date(2026, 12, 31); END = date(2026, 12, 31)
CASE = {"POD-001": 24, "POD-002": 24, "POD-003": 12}
SERVICE_Z = {"large": 1.28, "cafe": 1.28, "mid": 1.04, "small": 0.84}
LEAD_MEAN = {"Near": 2.0, "Mid": 4.5, "Far": 7.0, "Outlier": 10.5}
LEAD_P90 = {"Near": 3.0, "Mid": 6.0, "Far": 10.0, "Outlier": 15.0}
SEASON_OF = lambda m: "winter" if m in (12, 1, 2) else "spring" if m in (3, 4, 5) else "summer" if m in (6, 7, 8) else "fall"
FEATURES = ["dow", "month", "u7", "u14", "u28", "u90", "trend", "dss", "vol_small", "vol_mid", "vol_large", "vol_cafe",
            "dist_Near", "dist_Mid", "dist_Far", "dist_Outlier", "clim_cold", "clim_temp", "clim_warm", "clim_extreme", "sub", "lead_mean", "lead_p90"]

class Series:
    def __init__(self, df):
        df = df.sort_values("date")
        self.dates = list(df["date"])
        self.obs = df["observed_use"].to_numpy(float)
        self.true = df["true_demand"].to_numpy(float)
        self.stock = df["stock_on_hand"].to_numpy(float)
        valid = ((df["downtime_flag"].to_numpy() == 0) & (df["stockout_flag"].to_numpy() == 0)).astype(float)
        self.valid_obs = np.where(valid == 1, self.obs, 0.0)
        self.cum_obs = np.concatenate([[0], np.cumsum(self.valid_obs)])
        self.cum_cnt = np.concatenate([[0], np.cumsum(valid)])
        # last stock increase index (shipment arrival proxy)
        inc = np.zeros(len(df), dtype=int)
        last = -999
        for i in range(1, len(df)):
            if self.stock[i] > self.stock[i-1] + 50: last = i
            inc[i] = last
        self.last_inc = inc
    def idx(self, as_of):
        return bisect.bisect_right(self.dates, as_of) - 1
    def mean_win(self, i, days, lag=0):
        # mean over days ending at i-lag, inclusive
        end = i - lag + 1; start = max(0, end - days)
        cnt = self.cum_cnt[end] - self.cum_cnt[start]
        if cnt <= 0: return 0.0
        return float((self.cum_obs[end] - self.cum_obs[start]) / cnt)
    def feats(self, loc_row, as_of):
        i = self.idx(as_of)
        if i < 0: return None
        u28 = self.mean_win(i, 28); prior = self.mean_win(i, 30, lag=30)
        li = self.last_inc[i]
        dss = (i - li) if li >= 0 else 999
        return {"dow": as_of.weekday(), "month": as_of.month, "u7": self.mean_win(i, 7), "u14": self.mean_win(i, 14),
                "u28": u28, "u90": self.mean_win(i, 90), "trend": u28 / prior if prior > 0 else 1.0, "dss": dss,
                "stock": float(self.stock[i]),
                "vol_small": int(loc_row.volume_tier == "small"), "vol_mid": int(loc_row.volume_tier == "mid"),
                "vol_large": int(loc_row.volume_tier == "large"), "vol_cafe": int(loc_row.volume_tier == "cafe"),
                "dist_Near": int(loc_row.distance_tier == "Near"), "dist_Mid": int(loc_row.distance_tier == "Mid"),
                "dist_Far": int(loc_row.distance_tier == "Far"), "dist_Outlier": int(loc_row.distance_tier == "Outlier"),
                "clim_cold": int(loc_row.climate == "cold"), "clim_temp": int(loc_row.climate == "temperate"),
                "clim_warm": int(loc_row.climate == "warm"), "clim_extreme": int(loc_row.climate == "extreme"),
                "sub": int(loc_row.ordering_style == "subscription"),
                "lead_mean": LEAD_MEAN[loc_row.distance_tier], "lead_p90": LEAD_P90[loc_row.distance_tier]}
    def actual_empty(self, as_of, stock):
        if stock is None or stock <= 0: return None, "unknown"
        i = self.idx(as_of); rem = stock
        for j in range(i, len(self.dates)):
            td = self.true[j]
            if td <= 0: continue
            days = rem / td
            if days <= 1: return (self.dates[j] - as_of).days + days, "ok"
            rem -= td
        return None, "censored"

def feats_legacy(series_dict, loc, sid, mid, as_of):
    """Back-compat wrapper used by tests: series_dict maps (sid,mid) to dict of date->tuple."""
    # Build a Series on the fly from dict (tests only, small)
    import pandas as pd
    items = sorted(series_dict[(sid, mid)].items())
    df = pd.DataFrame([{"date": d, "observed_use": v[0], "true_demand": v[1], "stock_on_hand": v[2], "downtime_flag": v[3], "stockout_flag": v[4]} for d, v in items])
    s = Series(df)
    return s.feats(loc.loc[sid], as_of)

def run():
    os.makedirs(PRED, exist_ok=True)
    loc = pd.read_csv(os.path.join(DATA, "locations.csv"), index_col="site_id")
    rd = pd.read_csv(os.path.join(DATA, "readings.csv"), parse_dates=["date"])
    rd["date"] = rd["date"].dt.date
    series = {}
    for (sid, mid), g in rd.groupby(["site_id", "material_id"]):
        series[(sid, mid)] = Series(g)
    combos = sorted(series.keys())
    train_dates = []
    d = date(2023, 4, 1)
    while d <= TRAIN_END:
        train_dates.append(d); d += timedelta(days=7)
    rows = []
    for sid, mid in combos:
        s = series[(sid, mid)]; L = loc.loc[sid]
        for as_of in train_dates:
            f = s.feats(L, as_of)
            if f is None: continue
            i = s.idx(as_of)
            vals = [s.true[i+k] if i+k < len(s.true) else 0 for k in range(1, 8)]
            rows.append({**f, "target": float(np.mean(vals))})
    train = pd.DataFrame(rows)
    def mk(loss, q=None):
        kw = dict(max_iter=300, learning_rate=0.06, random_state=42)
        if loss == "quantile": kw.update(loss="quantile", quantile=q)
        else: kw["loss"] = "squared_error"
        return HistGradientBoostingRegressor(**kw)
    models = {"point": mk("squared_error").fit(train[FEATURES], train["target"]),
              "q10": mk("quantile", 0.1).fit(train[FEATURES], train["target"]),
              "q90": mk("quantile", 0.9).fit(train[FEATURES], train["target"])}
    test_dates = []
    d = TEST_START
    while d <= TEST_END:
        test_dates.append(d); d += timedelta(days=7)
    # Build all test feature rows, batch predict
    meta, feat_rows = [], []
    for sid, mid in combos:
        s = series[(sid, mid)]; L = loc.loc[sid]
        for as_of in test_dates:
            f = s.feats(L, as_of)
            if f is None: continue
            feat_rows.append(f); meta.append((sid, mid, as_of, L))
    X = pd.DataFrame(feat_rows)[FEATURES]
    p = models["point"].predict(X); q10 = models["q10"].predict(X); q90 = models["q90"].predict(X)
    results = []
    for (sid, mid, as_of, L), f, pr, lo_r, hi_r in zip(meta, feat_rows, p, q10, q90):
        s = series[(sid, mid)]
        actual, status = s.actual_empty(as_of, f["stock"])
        base_rec = {"site_id": sid, "material_id": mid, "as_of": as_of.isoformat(), "status": status,
                    "season": SEASON_OF(as_of.month), "distance": L.distance_tier, "volume": L.volume_tier,
                    "climate": L.climate, "anchorage": sid == "S048"}
        if status != "ok":
            results.append(base_rec); continue
        base_rate = f["u28"] if f["u28"] > 0 else 0.5
        base_days = f["stock"] / base_rate
        ml_rate = max(float(pr), 0.5); q10r = max(float(lo_r), 0.5); q90r = max(float(hi_r), 0.5)
        ml_days = f["stock"] / ml_rate
        lo_days = f["stock"] / q90r; hi_days = f["stock"] / q10r
        if lo_days > hi_days: lo_days, hi_days = hi_days, lo_days
        results.append({**base_rec, "stock": f["stock"], "base_mae": abs(base_days - actual), "ml_mae": abs(ml_days - actual),
                        "base_within3": int(abs(base_days - actual) <= 3), "ml_within3": int(abs(ml_days - actual) <= 3),
                        "ml_covered": int(lo_days <= actual <= hi_days), "actual": actual, "base_days": base_days, "ml_days": ml_days})
    df = pd.DataFrame(results); scored = df[df.status == "ok"]
    def agg(sub):
        if len(sub) == 0: return {"n": 0, "base_mae": None, "ml_mae": None, "improvement_pct": None, "base_within3": None, "ml_within3": None, "ml_coverage": None}
        return {"n": int(len(sub)), "base_mae": round(float(sub.base_mae.mean()), 3), "ml_mae": round(float(sub.ml_mae.mean()), 3),
                "improvement_pct": round(float((sub.base_mae.mean() - sub.ml_mae.mean()) / sub.base_mae.mean() * 100), 1),
                "base_within3": round(float(sub.base_within3.mean() * 100), 1), "ml_within3": round(float(sub.ml_within3.mean() * 100), 1),
                "ml_coverage": round(float(sub.ml_covered.mean() * 100), 1)}
    report = {"train_window": ["2023-01-01", "2025-06-30"], "test_window": ["2026-01-01", "2026-12-31"],
              "scored_n": int(len(scored)), "unknown": int((df.status == "unknown").sum()), "censored": int((df.status == "censored").sum()),
              "overall": agg(scored), "without_anchorage": agg(scored[~scored.anchorage]), "anchorage_only": agg(scored[scored.anchorage])}
    for dim in ["season", "distance", "volume", "climate", "material_id"]:
        report[f"by_{dim}"] = {str(k): agg(g) for k, g in scored.groupby(dim)}
    scored2 = scored.copy(); scored2["week"] = pd.to_datetime(scored2["as_of"]).dt.strftime("%Y-W%U")
    weekly = scored2.groupby("week").agg(base_mae=("base_mae", "mean"), ml_mae=("ml_mae", "mean"), n=("ml_mae", "size")).reset_index()
    weekly.to_csv(os.path.join(PRED, "weekly_accuracy.csv"), index=False); report["weekly"] = weekly.to_dict("records")
    cov_fail = [k for k, v in list(report["by_season"].items()) + list(report["by_distance"].items()) + list(report["by_volume"].items()) + list(report["by_climate"].items()) + list(report["by_material_id"].items()) if v["ml_coverage"] is not None and v["ml_coverage"] < 60]
    overall = report["overall"]
    ship = overall["improvement_pct"] >= 10 and overall["ml_coverage"] >= 70 and not cov_fail
    report["ship_ml_overall"] = bool(ship); report["coverage_fail_subgroups"] = cov_fail
    report["verdict"] = ("SHIP ML" if ship else "DO NOT SHIP ML") + f": improvement {overall['improvement_pct']}%, coverage {overall['ml_coverage']}%, failing subgroups: {cov_fail or 'none'}"
    df.to_csv(os.path.join(PRED, "backtest_rows.csv"), index=False)
    # seasonal swing by climate, test year true demand
    rd2 = rd.copy(); rd2["month"] = pd.to_datetime(rd2["date"]).dt.month; rd2["season"] = rd2["month"].apply(SEASON_OF)
    merged = rd2.merge(loc.reset_index(), left_on="site_id", right_on="site_id")
    test = merged[pd.to_datetime(merged["date"]).dt.year == 2026]
    swing = {}
    for clim, g in test.groupby("climate"):
        means = g.groupby("season")["true_demand"].mean(); ann = g["true_demand"].mean()
        swing[clim] = {"winter_mean": round(float(means.get("winter", 0)), 2), "summer_mean": round(float(means.get("summer", 0)), 2),
                       "annual_mean": round(float(ann), 2), "winter_minus_summer_pct_of_annual": round(float((means.get("winter", 0) - means.get("summer", 0)) / ann * 100), 1) if ann else None}
    report["seasonal_swing_by_climate"] = swing
    # snapshot and proposals
    snap_rows, props = [], []
    snap_feats = []
    for sid, mid in combos:
        s = series[(sid, mid)]; L = loc.loc[sid]; f = s.feats(L, SNAP)
        if f is None: continue
        snap_feats.append((sid, mid, L, f))
    Xs = pd.DataFrame([f for _, _, _, f in snap_feats])[FEATURES]
    ps = models["point"].predict(Xs)
    for (sid, mid, L, f), pr in zip(snap_feats, ps):
        ml_rate = max(float(pr), 0.5); days = f["stock"] / ml_rate
        band = "Healthy" if days > 21 else "Watch" if days >= 14 else "Reorder" if days >= 7 else "Critical"
        lead = LEAD_P90[L.distance_tier] if L.distance_tier in ("Far", "Outlier") else LEAD_MEAN[L.distance_tier]
        order_by = SNAP + timedelta(days=int(days - lead))
        snap_rows.append({"site_id": sid, "material_id": mid, "stock": round(f["stock"], 1), "ml_rate": round(ml_rate, 2),
                          "days_to_empty": round(days, 1), "band": band, "order_by": order_by.isoformat(), "distance": L.distance_tier, "volume": L.volume_tier, "climate": L.climate})
        if band in ("Critical", "Reorder"):
            s = series[(sid, mid)]; i = s.idx(SNAP)
            vals = s.obs[max(0, i-27):i+1]; sd = float(np.std(vals)) if len(vals) else 0.0
            safety = SERVICE_Z[L.volume_tier] * sd * math.sqrt(lead)
            raw = ml_rate * 30 + safety; case = CASE[mid]; rounded = math.ceil(raw / case) * case; qty = max(rounded, 48)
            props.append({"site_id": sid, "material_id": mid, "band": band, "order_by": order_by.isoformat(),
                          "proposed_qty": int(qty), "case_pack": case, "safety_stock": round(safety, 1), "order_now": bool(order_by <= SNAP)})
    pd.DataFrame(snap_rows).to_csv(os.path.join(PRED, "snapshot_2026-12-31.csv"), index=False)
    pd.DataFrame(props).sort_values("order_by").to_csv(os.path.join(PRED, "proposals_2026-12-31.csv"), index=False) if props else pd.DataFrame(columns=["site_id"]).to_csv(os.path.join(PRED, "proposals_2026-12-31.csv"), index=False)
    report["snapshot_bands"] = pd.DataFrame(snap_rows)["band"].value_counts().to_dict()
    report["proposals"] = {"count": len(props), "order_now": int(sum(p["order_now"] for p in props))}
    with open(os.path.join(PRED, "backtest_v2.json"), "w") as f: json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ["overall", "without_anchorage", "anchorage_only", "verdict", "snapshot_bands", "proposals", "seasonal_swing_by_climate"]}, indent=2))
    return report

if __name__ == "__main__":
    run()

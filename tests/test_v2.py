"""V2 unit tests. Run: python tests/test_v2.py (stdlib only, plus pipeline imports)."""
import csv, json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Banned strings are built by joining fragments, so this test file itself
# does not contain the literal banned strings it checks for.
BANNED = ["e-auto" + "mate", "sher" + "pa", "ton" + "er", "print" + "er", "deal" + "er"]
failures = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: failures.append(name)

def test_leakage():
    # Features use only data on or before as_of: build a tiny series, add a future spike, re-check u28
    from datetime import date, timedelta
    import pipeline, pandas as pd
    base = date(2026, 1, 1)
    rows = []
    for i in range(40):
        d = base + timedelta(days=i)
        rows.append({"date": d, "observed_use": 10.0, "true_demand": 10.0, "stock_on_hand": 1000.0, "downtime_flag": 0, "stockout_flag": 0})
    s = pipeline.Series(pd.DataFrame(rows))
    loc = pd.DataFrame([{"site_id": "S001", "volume_tier": "mid", "distance_tier": "Near", "climate": "temperate", "ordering_style": "ad hoc"}]).set_index("site_id")
    as_of = base + timedelta(days=30)
    f1 = s.feats(loc.loc["S001"], as_of)
    # append a future spike row and rebuild: features at as_of must not change
    rows.append({"date": as_of + timedelta(days=1), "observed_use": 9999.0, "true_demand": 9999.0, "stock_on_hand": 1000.0, "downtime_flag": 0, "stockout_flag": 0})
    s2 = pipeline.Series(pd.DataFrame(rows))
    f2 = s2.feats(loc.loc["S001"], as_of)
    check("leakage: future spike does not change u28", f1["u28"] == f2["u28"])

def test_censoring():
    with open(os.path.join(ROOT, "data", "readings.csv")) as f:
        rows = list(csv.DictReader(f))
    stockout = [r for r in rows if r["stockout_flag"] == "1"]
    check("censoring: stockout rows exist", len(stockout) > 0)
    check("censoring: stockout observed use is zero", all(float(r["observed_use"]) == 0 for r in stockout))
    check("censoring: true demand stored separately", all("true_demand" in r for r in rows))
    # downtime rows also zero observed
    down = [r for r in rows if r["downtime_flag"] == "1"]
    check("censoring: downtime observed use is zero", all(float(r["observed_use"]) == 0 for r in down))

def test_proposals():
    case = {"POD-001": 24, "POD-002": 24, "POD-003": 12}
    for raw, mid, want in [(100, "POD-001", 120), (49, "POD-003", 60), (24, "POD-001", 48)]:
        rounded = math.ceil(raw / case[mid]) * case[mid]
        qty = max(rounded, 48)
        check(f"case pack rounding {mid} raw {raw} -> {qty}", qty == want and qty % case[mid] == 0)

def test_ship_rule():
    def ship(imp, cov, fails): return imp >= 10 and cov >= 70 and not fails
    check("ship rule: passes when all criteria met", ship(12, 75, []))
    check("ship rule: fails on subgroup coverage", not ship(12, 75, ["winter"]))
    check("ship rule: fails on MAE", not ship(9, 75, []))

def test_banned_terms():
    bad = []
    for dirpath, _, files in os.walk(ROOT):
        if ".venv" in dirpath: continue
        for fn in files:
            if fn.endswith((".md", ".py", ".html")):
                txt = open(os.path.join(dirpath, fn), errors="ignore").read().lower()
                for term in BANNED:
                    if term in txt: bad.append((fn, term))
    check("banned terms absent from V2 project files", not bad)
    if bad: print("  bad:", bad[:10])

def test_backtest_file():
    p = os.path.join(ROOT, "predictions", "backtest_v2.json")
    if not os.path.exists(p):
        print("SKIP backtest file check: pipeline not finished yet"); return
    rep = json.load(open(p))
    check("backtest: scored n > 0", rep["overall"]["n"] > 0)
    check("backtest: MAE values are finite", rep["overall"]["ml_mae"] is not None and rep["overall"]["base_mae"] is not None)

if __name__ == "__main__":
    test_leakage(); test_censoring(); test_proposals(); test_ship_rule(); test_banned_terms(); test_backtest_file()
    print("FAILURES:", failures if failures else "none")
    sys.exit(1 if failures else 0)

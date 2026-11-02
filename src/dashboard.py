"""Standalone HTML dashboard from backtest_v2.json, snapshot, and proposals."""
import json, os
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED = os.path.join(ROOT, "predictions")
rep = json.load(open(os.path.join(PRED, "backtest_v2.json")))
snap = pd.read_csv(os.path.join(PRED, "snapshot_2026-12-31.csv"))
props = pd.read_csv(os.path.join(PRED, "proposals_2026-12-31.csv")) if os.path.exists(os.path.join(PRED, "proposals_2026-12-31.csv")) else pd.DataFrame()
o = rep["overall"]
rows = ""
for _, r in snap.sort_values(["band", "days_to_empty"]).iterrows():
    rows += f"<tr><td>{r.site_id}</td><td>{r.material_id}</td><td>{r.days_to_empty}</td><td>{r.band}</td><td>{r.order_by}</td><td>{r.distance}</td><td>{r.volume}</td><td>{r.climate}</td></tr>\n"
prows = ""
for _, r in props.iterrows():
    prows += f"<tr><td>{r.site_id}</td><td>{r.material_id}</td><td>{r.band}</td><td>{r.order_by}</td><td>{r.proposed_qty}</td><td>{r.safety_stock}</td><td>{r.order_now}</td></tr>\n"
html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>Coffee Bros V2 Dashboard</title>
<style>body{{font-family:system-ui,sans-serif;margin:40px;color:#222}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:6px 10px}} h1{{font-size:28px}}</style></head>
<body><h1>Coffee Bros Stocking ML V2 Dashboard</h1>
<p>Synthetic data only, fictional company. Test year 2026, full 12 month holdout. V1 baseline for comparison: MAE 1.81, ML 1.26, 30.1 percent improvement, 92.6 percent within 3 days, 86.1 percent coverage.</p>
<p><b>Overall:</b> baseline MAE {o['base_mae']} days, ML MAE {o['ml_mae']} days, improvement {o['improvement_pct']} percent, ML within 3 days {o['ml_within3']} percent, coverage {o['ml_coverage']} percent, n {o['n']}.</p>
<p><b>Verdict:</b> {rep['verdict']}</p>
<p><b>Without Anchorage:</b> {rep['without_anchorage']}</p>
<p><b>Snapshot bands at 2026-12-31:</b> {rep['snapshot_bands']}</p>
<p><b>Proposals:</b> {rep['proposals']}</p>
<p><b>Seasonal swing by climate (winter minus summer, percent of annual mean, true demand, test year):</b> {rep.get('seasonal_swing_by_climate', {})}</p>
<h2>Snapshot, all site-product combos</h2><table><tr><th>Site</th><th>Product</th><th>Days to empty</th><th>Band</th><th>Order by</th><th>Distance</th><th>Volume</th><th>Climate</th></tr>{rows}</table>
<h2>Proposals</h2><table><tr><th>Site</th><th>Product</th><th>Band</th><th>Order by</th><th>Qty</th><th>Safety stock</th><th>Order now</th></tr>{prows}</table>
</body></html>"""
open(os.path.join(PRED, "dashboard.html"), "w").write(html)
print("dashboard written")

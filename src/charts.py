"""Simple SVG charts from backtest_v2.json: baseline vs ML MAE, coverage by season."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRED = os.path.join(ROOT, "predictions"); DOCS = os.path.join(ROOT, "docs", "charts")
os.makedirs(DOCS, exist_ok=True)
rep = json.load(open(os.path.join(PRED, "backtest_v2.json")))
o = rep["overall"]
def bar(label, val, maxv, y):
    w = int(val / maxv * 400) if maxv else 0
    return f'<text x="10" y="{y+15}">{label} {val}</text><rect x="180" y="{y}" width="{w}" height="18" fill="#d97706"/>'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="620" height="120"><text x="10" y="20">Baseline vs ML MAE, days, V2 test year 2026</text>{bar("Baseline", o["base_mae"], 3, 40)}{bar("ML", o["ml_mae"], 3, 70)}</svg>'
open(os.path.join(DOCS, "mae.svg"), "w").write(svg)
items = rep.get("by_season", {})
y = 40; parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="620" height="200"><text x="10" y="20">ML coverage by season, percent</text>']
for k, v in items.items():
    parts.append(bar(k, v["ml_coverage"] or 0, 100, y)); y += 30
parts.append("</svg>")
open(os.path.join(DOCS, "coverage_by_season.svg"), "w").write("".join(parts))
print("charts written")

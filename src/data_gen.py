"""Coffee Bros V2 synthetic dataset generator. Fictional only, fixed seed.

48 months: 2023-01-01 to 2026-12-31. 48 sites, 3 products.
True demand is generated separately from observed use. When a site
runs out of stock, observed use is zero and true demand is stored
separately, so backtest scoring against true demand does not reward
predicting stockouts. Downtime days are flagged the same way.
Lead time is a distribution by distance tier, not a single mean,
with winter slips, more often for Far and Outlier sites.
Seasonality is a starting curve by climate group, not a fact:
cold winter +22 percent, temperate +15 percent, warm +6 percent,
extreme +25 percent, summer cold -15, temperate -10, warm -18,
extreme -20. Results must report the actual swing by climate group.
"""
import csv, os, random
from datetime import date, timedelta

SEED = 202602
START = date(2023, 1, 1)
DAYS = 1461  # 2023, 2024 leap, 2025, 2026
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")

PRODUCTS = [
    ("POD-001", "Medium Roast Pods", 1.0, 24),
    ("POD-002", "Dark Roast Pods", 0.62, 24),
    ("POD-003", "Decaf Pods", 0.36, 12),
]
VOLUME_BASE = {"small": 14.0, "mid": 42.0, "large": 110.0, "cafe": 65.0}
# (city, state, climate, distance, volume, ordering)
SITE_DEFS = [
    ("Cincinnati", "OH", "temperate", "Near", "large", "ad hoc"),
    ("Cincinnati", "OH", "temperate", "Near", "mid", "subscription"),
    ("Cincinnati", "OH", "temperate", "Near", "small", "ad hoc"),
    ("Cincinnati", "OH", "temperate", "Near", "cafe", "ad hoc"),
    ("Columbus", "OH", "temperate", "Near", "mid", "ad hoc"),
    ("Cleveland", "OH", "temperate", "Mid", "mid", "subscription"),
    ("Dayton", "OH", "temperate", "Near", "small", "ad hoc"),
    ("Toledo", "OH", "temperate", "Mid", "small", "ad hoc"),
    ("Indianapolis", "IN", "temperate", "Mid", "mid", "ad hoc"),
    ("Louisville", "KY", "temperate", "Mid", "mid", "subscription"),
    ("Lexington", "KY", "temperate", "Mid", "small", "ad hoc"),
    ("Chicago", "IL", "cold", "Mid", "large", "ad hoc"),
    ("Chicago", "IL", "cold", "Mid", "cafe", "ad hoc"),
    ("Detroit", "MI", "cold", "Mid", "mid", "subscription"),
    ("Grand Rapids", "MI", "cold", "Far", "small", "ad hoc"),
    ("Milwaukee", "WI", "cold", "Mid", "mid", "ad hoc"),
    ("Madison", "WI", "cold", "Far", "small", "ad hoc"),
    ("Minneapolis", "MN", "cold", "Far", "large", "ad hoc"),
    ("Minneapolis", "MN", "cold", "Far", "mid", "subscription"),
    ("Duluth", "MN", "cold", "Outlier", "small", "ad hoc"),
    ("Duluth", "MN", "cold", "Outlier", "cafe", "ad hoc"),
    ("St. Louis", "MO", "temperate", "Mid", "mid", "ad hoc"),
    ("Kansas City", "MO", "temperate", "Far", "mid", "subscription"),
    ("Nashville", "TN", "temperate", "Mid", "mid", "ad hoc"),
    ("Pittsburgh", "PA", "temperate", "Mid", "mid", "ad hoc"),
    ("Denver", "CO", "cold", "Far", "large", "ad hoc"),
    ("Denver", "CO", "cold", "Far", "mid", "subscription"),
    ("Colorado Springs", "CO", "cold", "Far", "small", "ad hoc"),
    ("Salt Lake City", "UT", "cold", "Far", "mid", "ad hoc"),
    ("Boise", "ID", "cold", "Outlier", "small", "ad hoc"),
    ("Boise", "ID", "cold", "Outlier", "mid", "subscription"),
    ("Billings", "MT", "cold", "Outlier", "small", "ad hoc"),
    ("Phoenix", "AZ", "warm", "Outlier", "large", "ad hoc"),
    ("Phoenix", "AZ", "warm", "Outlier", "mid", "subscription"),
    ("Phoenix", "AZ", "warm", "Outlier", "cafe", "ad hoc"),
    ("Tucson", "AZ", "warm", "Outlier", "mid", "ad hoc"),
    ("Tucson", "AZ", "warm", "Outlier", "small", "ad hoc"),
    ("Albuquerque", "NM", "warm", "Far", "mid", "subscription"),
    ("El Paso", "TX", "warm", "Outlier", "small", "ad hoc"),
    ("Miami", "FL", "warm", "Outlier", "large", "ad hoc"),
    ("Miami", "FL", "warm", "Outlier", "cafe", "ad hoc"),
    ("Seattle", "WA", "temperate", "Far", "mid", "ad hoc"),
    ("Portland", "OR", "temperate", "Far", "mid", "subscription"),
    ("Spokane", "WA", "cold", "Outlier", "small", "ad hoc"),
    ("Fargo", "ND", "cold", "Outlier", "small", "ad hoc"),
    ("Omaha", "NE", "temperate", "Far", "mid", "ad hoc"),
    ("Des Moines", "IA", "temperate", "Mid", "small", "ad hoc"),
    ("Anchorage", "AK", "extreme", "Outlier", "small", "ad hoc"),
]
LEAD = {"Near": (2.0, 0.7), "Mid": (4.5, 1.2), "Far": (7.0, 2.0), "Outlier": (10.5, 3.2)}
SEASON = {
    "cold": {12: 0.22, 1: 0.22, 2: 0.22, 9: 0.12, 10: 0.12, 11: 0.12, 3: 0.0, 4: 0.0, 5: 0.0, 6: -0.15, 7: -0.15, 8: -0.15},
    "temperate": {12: 0.15, 1: 0.15, 2: 0.15, 9: 0.10, 10: 0.10, 11: 0.10, 3: 0.0, 4: 0.0, 5: 0.0, 6: -0.10, 7: -0.10, 8: -0.10},
    "warm": {12: 0.06, 1: 0.06, 2: 0.06, 9: 0.04, 10: 0.04, 11: 0.04, 3: 0.0, 4: 0.0, 5: 0.0, 6: -0.18, 7: -0.18, 8: -0.18},
    "extreme": {12: 0.25, 1: 0.25, 2: 0.25, 9: 0.14, 10: 0.14, 11: 0.14, 3: 0.0, 4: 0.0, 5: 0.0, 6: -0.20, 7: -0.20, 8: -0.20},
}
HOLIDAYS = {(1, 1), (7, 4), (11, 28), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31)}


def main():
    rng = random.Random(SEED)
    os.makedirs(DATA_DIR, exist_ok=True)
    dates = [START + timedelta(days=i) for i in range(DAYS)]
    sites = []
    for i, (city, state, climate, dist, vol, ordering) in enumerate(SITE_DEFS):
        sites.append({"site_id": f"S{i+1:03d}", "site_name": f"{city} {vol.title()} Site {i+1}",
                      "city": city, "state": state, "climate": climate, "distance_tier": dist,
                      "volume_tier": vol, "ordering_style": ordering})
    with open(os.path.join(DATA_DIR, "locations.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sites[0].keys())); w.writeheader(); w.writerows(sites)
    with open(os.path.join(DATA_DIR, "materials.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["material_id", "product_name", "usage_factor", "case_pack"])
        w.writerows(PRODUCTS)
    readings, shipments, events = [], [], []
    ship_id = 0
    for si, site in enumerate(sites):
        rng_site = random.Random(SEED + si * 1000)
        # site-specific promo weeks, downtime blocks, price dip is global mid-2024
        promo_days = set()
        for _ in range(10):
            promo_days.add(rng_site.randrange(0, DAYS - 7))
        downtime = {}
        for _ in range(14):
            s = rng_site.randrange(0, DAYS - 3)
            for d in range(rng_site.choice([1, 2, 3])):
                downtime[s + d] = True
        for pid, pname, factor, case in PRODUCTS:
            base = VOLUME_BASE[site["volume_tier"]] * factor * rng_site.uniform(0.85, 1.15)
            stock = base * 45.0
            pending = []  # (arrival_idx, qty)
            last_ship_day = -999
            for di, d in enumerate(dates):
                # arrivals
                for arr, qty in list(pending):
                    if arr == di:
                        stock += qty; pending.remove((arr, qty))
                # true demand
                seas = SEASON[site["climate"]][d.month]
                dow = d.weekday()
                if site["volume_tier"] == "cafe":
                    dow_f = 1.15 if dow >= 5 else 1.0
                else:
                    dow_f = 1.0 if dow < 5 else 0.18
                hol = 0.35 if (d.month, d.day) in HOLIDAYS else 1.0
                promo = 1.15 if di in promo_days or di - 1 in promo_days else 1.0
                price = 0.96 if date(2024, 6, 1) <= d <= date(2024, 6, 21) else 1.0
                bts = 1.12 if (d.month == 8 and d.day >= 20) or (d.month == 9 and d.day <= 10) else 1.0
                noise = rng_site.gauss(1.0, 0.16)
                true_d = max(0.0, base * (1 + seas) * dow_f * hol * promo * price * bts * noise)
                is_down = di in downtime
                is_stockout = stock <= 0.01
                observed = 0.0 if (is_down or is_stockout) else min(true_d, stock)
                stock = max(0.0, stock - observed)
                readings.append({"date": d.isoformat(), "site_id": site["site_id"], "material_id": pid,
                                 "stock_on_hand": round(stock, 1), "true_demand": round(true_d, 2),
                                 "observed_use": round(observed, 2), "downtime_flag": int(is_down),
                                 "stockout_flag": int(is_stockout and not is_down), "promo_flag": int(promo > 1.0)})
                # reorder: at or below 14 days of base, order 30 days plus safety-ish, subscription sites only on Fridays unless critical
                cover = stock / base if base else 999
                due = cover <= 14
                if site["ordering_style"] == "subscription" and dow != 4 and cover > 7:
                    due = False
                if due and di - last_ship_day > 5:
                    qty = base * 30
                    mean, sd = LEAD[site["distance_tier"]]
                    slip = rng_site.choice([0, 0, 0, 1, 2, 3]) if d.month in (12, 1, 2) and site["distance_tier"] in ("Far", "Outlier") else rng_site.choice([0, 0, 0, 1])
                    lead = max(1, int(round(rng_site.gauss(mean, sd))) + slip)
                    ship_id += 1
                    pending.append((di + lead, qty))
                    shipments.append({"shipment_id": ship_id, "site_id": site["site_id"], "material_id": pid,
                                      "order_date": d.isoformat(), "arrival_date": (d + timedelta(days=lead)).isoformat(),
                                      "quantity": round(qty, 1), "lead_time_actual": lead, "lead_time_planned": round(mean, 1)})
                    last_ship_day = di
            # service events: one row per downtime block start, simplified
            events.append({"site_id": site["site_id"], "event_type": "downtime", "count_days": len(downtime)})
    def write(name, rows, fields):
        with open(os.path.join(DATA_DIR, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    write("readings.csv", readings, list(readings[0].keys()))
    write("shipments.csv", shipments, list(shipments[0].keys()))
    write("service_events.csv", events, list(events[0].keys()))
    print(f"sites={len(sites)} readings={len(readings)} shipments={len(shipments)}")
    print(f"stockout days={sum(r['stockout_flag'] for r in readings)} downtime days={sum(r['downtime_flag'] for r in readings)} censored share={(sum(r['stockout_flag']+r['downtime_flag'] for r in readings))/len(readings):.3f}")

if __name__ == "__main__":
    main()

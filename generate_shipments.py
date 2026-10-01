"""
generate_shipments.py
Builds a SYNTHETIC freight dataset (star schema) with deliberate cause-and-effect
structure, so SQL / DAX / Power BI work on it has real relationships to find.

NOT real company data. The planted mechanisms are listed in docs/data_model.md
("What is baked into the generator"). Carrier names are fictional.

Optional: put a real weekly diesel series at data/diesel_weekly.csv
(columns: week_start, diesel_cpl) before running and it will be used instead
of the synthetic one. See docs/data_sources.md.

Run:  python src/generate_shipments.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)
DATA = Path(__file__).resolve().parents[1] / "data"
DATA.mkdir(exist_ok=True)

START, END = pd.Timestamp("2025-10-01"), pd.Timestamp("2026-09-26")
N_SHIPMENTS = 24_000
FREE_DWELL_HRS, DETENTION_RATE = 2.0, 85.0  # $/hr beyond free time

# ---- carriers: (id, name, $/km, base on-time, long-haul penalty, volume share) ----
CARRIERS = [
    (1, "Maple Line Freight",   2.30, 0.93, 0.04, 0.13),
    (2, "Northern Haul Co",     2.40, 0.92, 0.05, 0.12),
    (3, "Prairie Express",      2.05, 0.90, 0.22, 0.22),  # cheapest, weak on long lanes
    (4, "Lakeshore Logistics",  2.35, 0.91, 0.06, 0.12),
    (5, "Summit Carriers",      2.65, 0.97, 0.02, 0.08),  # premium, reliable
    (6, "Eastbound Transport",  2.25, 0.89, 0.08, 0.11),
    (7, "Trans-Can Direct",     2.50, 0.94, 0.03, 0.10),
    (8, "Redline Freight",      2.20, 0.88, 0.10, 0.12),
]
car = pd.DataFrame(CARRIERS, columns=["carrier_id", "carrier_name", "rate_km", "base_otp", "lh_pen", "share"])

# ---- lanes: (origin DC, destination, approx road km, volume weight) ----
LANES = [
    ("Toronto DC", "London", 190, 8), ("Toronto DC", "Windsor", 370, 6),
    ("Toronto DC", "Ottawa", 450, 9), ("Toronto DC", "Montreal", 545, 12),
    ("Toronto DC", "Quebec City", 790, 5), ("Toronto DC", "Thunder Bay", 1400, 3),
    ("Toronto DC", "Halifax", 1800, 4), ("Toronto DC", "Winnipeg", 2100, 3),
    ("Calgary DC", "Lethbridge", 210, 5), ("Calgary DC", "Edmonton", 300, 10),
    ("Calgary DC", "Kelowna", 600, 4), ("Calgary DC", "Saskatoon", 610, 5),
    ("Calgary DC", "Regina", 760, 4), ("Calgary DC", "Vancouver", 970, 8),
    ("Calgary DC", "Winnipeg", 1330, 4),
]
lane = pd.DataFrame(LANES, columns=["origin_dc", "destination", "distance_km", "weight"])
lane.insert(0, "lane_id", range(1, len(lane) + 1))
lane["distance_band"] = pd.cut(lane["distance_km"], [0, 300, 800, 99999],
                               labels=["<300 km", "300-800 km", ">800 km"], right=True).astype(str)

# ---- diesel price (cents per litre), weekly ----
real = DATA / "diesel_weekly.csv"
if real.exists():
    diesel = pd.read_csv(real, parse_dates=["week_start"]).sort_values("week_start")
    diesel_source = "file"
else:
    weeks = pd.date_range(START - pd.Timedelta(days=6), END, freq="7D")
    walk = np.cumsum(rng.normal(0, 2.2, len(weeks)))
    price = 158 + 9 * np.sin(np.arange(len(weeks)) / 52 * 2 * np.pi) + walk - walk.mean()
    diesel = pd.DataFrame({"week_start": weeks, "diesel_cpl": price.round(1)})
    diesel.to_csv(real, index=False)
    diesel_source = "synthetic"

# ---- shipment dates: weekday-heavy, peak season Nov 15 - Dec 24 ----
days = pd.date_range(START, END, freq="D")
is_peak_day = ((days.month == 11) & (days.day >= 15)) | ((days.month == 12) & (days.day <= 24))
w = np.where(days.dayofweek >= 5, 0.25, 1.0) * np.where(is_peak_day, 1.35, 1.0)
ship_dates = pd.to_datetime(np.sort(rng.choice(days, size=N_SHIPMENTS, p=w / w.sum())))

f = pd.DataFrame({"ship_date": ship_dates})
f["shipment_id"] = [f"S{i:06d}" for i in range(1, N_SHIPMENTS + 1)]
f["carrier_id"] = rng.choice(car["carrier_id"], size=N_SHIPMENTS, p=car["share"] / car["share"].sum())
f["lane_id"] = rng.choice(lane["lane_id"], size=N_SHIPMENTS, p=lane["weight"] / lane["weight"].sum())
f = (f.merge(car[["carrier_id", "rate_km", "base_otp", "lh_pen"]], on="carrier_id")
      .merge(lane[["lane_id", "distance_km"]], on="lane_id")
      .sort_values("shipment_id").reset_index(drop=True))

f["pallets"] = np.clip(rng.normal(14, 6, len(f)), 1, 26).round().astype(int)
f["weight_kg"] = (f["pallets"] * rng.normal(450, 60, len(f))).round().astype(int)
peak = (((f.ship_date.dt.month == 11) & (f.ship_date.dt.day >= 15)) |
        ((f.ship_date.dt.month == 12) & (f.ship_date.dt.day <= 24))).to_numpy()

# origin dwell: worse in peak season and on Mondays
dwell = (rng.lognormal(np.log(2.2), 0.5, len(f)) * np.where(peak, 1.35, 1.0)
         * np.where(f.ship_date.dt.dayofweek == 0, 1.15, 1.0))
f["origin_dwell_hours"] = np.clip(dwell, 0.3, 12).round(2)

# on-time: carrier base, long-haul penalty, dwell penalty, peak penalty
long_haul = (f["distance_km"] > 800).to_numpy()
p_ot = (f["base_otp"] - f["lh_pen"] * long_haul
        - 0.025 * np.maximum(f["origin_dwell_hours"] - 3, 0) - 0.05 * peak)
p_ot = np.clip(p_ot, 0.4, 0.99)
f["on_time"] = (rng.random(len(f)) < p_ot).astype(int)
f["planned_transit_days"] = 1 + np.ceil(f["distance_km"] / 800).astype(int)
late_days = np.where(f["on_time"] == 1, 0, 1 + (rng.random(len(f)) < 0.35))
f["actual_transit_days"] = f["planned_transit_days"] + late_days

# cost: linehaul + fuel surcharge (tied to diesel price) + detention
f = (pd.merge_asof(f.sort_values("ship_date"),
                   diesel.rename(columns={"week_start": "ship_date"}), on="ship_date")
       .sort_values("shipment_id").reset_index(drop=True))
f["linehaul_cost"] = np.maximum(
    180, f["rate_km"] * f["distance_km"] * (0.55 + 0.45 * f["pallets"] / 26)
    * (1 + rng.normal(0, 0.04, len(f)))).round(2)
fsc_pct = np.clip((f["diesel_cpl"] - 110) * 0.0035, 0, 0.5)
f["fuel_surcharge"] = (f["linehaul_cost"] * fsc_pct).round(2)
billed = rng.random(len(f)) < 0.75
f["detention_cost"] = (np.maximum(f["origin_dwell_hours"] - FREE_DWELL_HRS, 0)
                       * DETENTION_RATE * billed).round(2)
f["total_cost"] = (f["linehaul_cost"] + f["fuel_surcharge"] + f["detention_cost"]).round(2)

fact = f[["shipment_id", "ship_date", "carrier_id", "lane_id", "pallets", "weight_kg",
          "planned_transit_days", "actual_transit_days", "on_time", "origin_dwell_hours",
          "linehaul_cost", "fuel_surcharge", "detention_cost", "total_cost", "diesel_cpl"]]
fact.to_csv(DATA / "fact_shipments.csv", index=False)
car[["carrier_id", "carrier_name"]].to_csv(DATA / "dim_carrier.csv", index=False)
lane.drop(columns="weight").to_csv(DATA / "dim_lane.csv", index=False)

dd = pd.DataFrame({"date": days})
dd["year"], dd["month_num"], dd["month_name"] = dd.date.dt.year, dd.date.dt.month, dd.date.dt.strftime("%b")
dd["year_month"] = dd.date.dt.strftime("%Y-%m")
dd["quarter"] = "Q" + dd.date.dt.quarter.astype(str)
dd["week_of_year"] = dd.date.dt.isocalendar().week.astype(int)
dd["day_name"], dd["is_weekend"] = dd.date.dt.day_name(), (dd.date.dt.dayofweek >= 5).astype(int)
dd["is_peak_season"] = is_peak_day.astype(int)
dd.to_csv(DATA / "dim_date.csv", index=False)

print(f"fact_shipments: {len(fact):,} rows | carriers: {len(car)} | lanes: {len(lane)} | "
      f"dates: {len(dd)} | diesel source: {diesel_source}")

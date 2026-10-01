"""
run_analysis.py
CSV -> SQLite -> six SQL queries -> charts -> reallocation scenario -> findings.md

Run:  python src/generate_shipments.py   (once)
      python src/run_analysis.py
"""
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA, SQL, OUT = ROOT / "data", ROOT / "sql", ROOT / "output"
(OUT / "charts").mkdir(parents=True, exist_ok=True)
(OUT / "tables").mkdir(parents=True, exist_ok=True)
DB = DATA / "freight.db"

# ---------- 1. load ----------
if DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
for name in ["dim_carrier", "dim_lane", "dim_date", "fact_shipments"]:
    pd.read_csv(DATA / f"{name}.csv").to_sql(name, con, index=False)
con.executescript("""
CREATE INDEX ix_f_carrier ON fact_shipments(carrier_id);
CREATE INDEX ix_f_lane    ON fact_shipments(lane_id);
CREATE INDEX ix_f_date    ON fact_shipments(ship_date);
CREATE INDEX ix_d_date    ON dim_date(date);
""")

# ---------- 2. run queries ----------
res = {}
for path in sorted(SQL.glob("*.sql")):
    df = pd.read_sql_query(path.read_text(), con)
    res[path.stem] = df
    df.to_csv(OUT / "tables" / f"{path.stem}.csv", index=False)

score, band, dwell = res["01_carrier_scorecard"], res["02_otp_by_distance_band"], res["03_detention_by_dwell"]
month, fuel, lh = res["04_monthly_trend"], res["05_fuel_sensitivity"], res["06_longhaul_carrier_compare"]
peakcmp = res["07_peak_vs_offpeak"].set_index("period")

# ---------- 3. charts ----------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(7.5, 5))
ax.scatter(score["cost_per_km"], score["on_time_pct"], s=score["shipments"] / 12, alpha=0.6, color="#2b6cb0")
for _, r in score.iterrows():
    ax.annotate(r["carrier_name"], (r["cost_per_km"], r["on_time_pct"]), xytext=(6, 4), textcoords="offset points", fontsize=8)
ax.set_xlabel("All-in cost per km ($, linehaul + fuel + detention)")
ax.set_ylabel("On-time delivery (%)")
ax.set_title("Cost vs service by carrier (bubble = shipment volume)")
fig.tight_layout(); fig.savefig(OUT / "charts" / "01_cost_vs_service.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
b = band.set_index("carrier_name")[["otp_under_300km", "otp_300_800km", "otp_over_800km"]]
b.plot.bar(ax=ax, color=["#90cdf4", "#4299e1", "#2a4365"], width=0.8)
ax.set_ylim(60, 100); ax.set_ylabel("On-time (%)"); ax.set_xlabel("")
ax.set_title("On-time % by carrier and lane distance")
ax.legend(["<300 km", "300-800 km", ">800 km"], frameon=False, ncol=3, loc="lower left")
plt.xticks(rotation=30, ha="right")
fig.tight_layout(); fig.savefig(OUT / "charts" / "02_otp_by_distance.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.5))
ax.bar(dwell["dwell_bucket"], dwell["avg_detention_cost"], color="#ed8936")
ax.set_ylabel("Avg detention charge per shipment ($)")
ax2 = ax.twinx(); ax2.plot(dwell["dwell_bucket"], dwell["on_time_pct"], color="#2b6cb0", marker="o")
ax2.set_ylabel("On-time (%)", color="#2b6cb0"); ax2.spines["right"].set_visible(True)
ax.set_title("Origin dwell time: detention cost and on-time %")
fig.tight_layout(); fig.savefig(OUT / "charts" / "03_dwell_vs_detention.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(month["year_month"], month["cost_per_shipment"], marker="o", color="#2b6cb0")
ax.set_ylabel("Cost per shipment ($)", color="#2b6cb0"); plt.xticks(rotation=45, ha="right")
ax2 = ax.twinx(); ax2.plot(month["year_month"], month["on_time_pct"], marker="s", color="#c53030")
ax2.set_ylabel("On-time (%)", color="#c53030"); ax2.spines["right"].set_visible(True)
ax.set_title("Monthly cost per shipment and on-time %")
fig.tight_layout(); fig.savefig(OUT / "charts" / "04_monthly_trend.png", dpi=130); plt.close(fig)

# ---------- 4. reallocation scenario (long-haul lanes) ----------
# Question: if we move the cheapest carrier's long-haul volume to the cheapest
# carrier that still delivers >= 90% on-time on those lanes, what changes?
cheapest = lh.sort_values("cost_per_km").iloc[0]
candidates = lh[(lh["on_time_pct"] >= 90) & (lh["carrier_name"] != cheapest["carrier_name"])]
target = candidates.sort_values("cost_per_km").iloc[0]

moved = pd.read_sql_query(
    """SELECT f.total_cost, f.on_time, l.distance_km
       FROM fact_shipments f JOIN dim_carrier c ON c.carrier_id = f.carrier_id
       JOIN dim_lane l ON l.lane_id = f.lane_id
       WHERE l.distance_band = '>800 km' AND c.carrier_name = ?""",
    con, params=[cheapest["carrier_name"]])
n = len(moved)
old_cost = moved["total_cost"].sum()
new_cost = old_cost * (target["cost_per_km"] / cheapest["cost_per_km"])
late_before = n * (1 - cheapest["on_time_pct"] / 100)
late_after = n * (1 - target["on_time_pct"] / 100)
scn = {
    "from_carrier": cheapest["carrier_name"], "to_carrier": target["carrier_name"], "shipments_moved": n,
    "cost_before": old_cost, "cost_after": new_cost, "extra_cost": new_cost - old_cost,
    "late_before": late_before, "late_after": late_after,
    "late_avoided": late_before - late_after,
    "cost_per_late_avoided": (new_cost - old_cost) / max(late_before - late_after, 1e-9),
}
pd.DataFrame([scn]).to_csv(OUT / "tables" / "08_reallocation_scenario.csv", index=False)

# ---------- 5. headline numbers for findings.md ----------
tot = pd.read_sql_query("SELECT COUNT(*) n, SUM(total_cost) cost, AVG(on_time) otp, "
                        "SUM(detention_cost) det, SUM(fuel_surcharge) fsc FROM fact_shipments", con).iloc[0]
d_lo, d_hi = dwell.iloc[0], dwell.iloc[-1]
peak = month.sort_values("cost_per_shipment", ascending=False).iloc[0]
pk, op = peakcmp.loc["Peak season"], peakcmp.loc["Rest of year"]
low = month.sort_values("cost_per_shipment").iloc[0]
pe = score[score["carrier_name"] == cheapest["carrier_name"]].iloc[0]
pe_band = band[band["carrier_name"] == cheapest["carrier_name"]].iloc[0]

findings = f"""# Findings (computed by src/run_analysis.py on SYNTHETIC data)

Dataset: {int(tot.n):,} shipments, ${tot.cost:,.0f} total spend, {tot.otp*100:.1f}% on-time overall.

1. **The cheapest carrier is the weakest on long lanes.** {cheapest['carrier_name']} has the lowest long-haul
   cost (${cheapest['cost_per_km']:.3f}/km) but delivers {pe_band['otp_over_800km']:.1f}% on-time over 800 km vs
   {pe_band['otp_under_300km']:.1f}% under 300 km.
2. **Dwell time drives both lateness and cost.** Shipments with 6h+ origin dwell are {d_hi['on_time_pct']:.1f}% on-time
   vs {d_lo['on_time_pct']:.1f}% under 2h, and carry ${d_hi['avg_detention_cost']:.0f} average detention vs
   ${d_lo['avg_detention_cost']:.0f}. Total detention spend: ${tot.det:,.0f}
   ({100*tot.det/tot.cost:.1f}% of all freight cost).
3. **Peak season (Nov 15 - Dec 24) hurts service more than headline cost.** Cost per shipment is
   {100*(pk['cost_per_shipment']/op['cost_per_shipment']-1):+.1f}% vs the rest of the year, but average detention per shipment is
   ${pk['avg_detention_cost']:.0f} vs ${op['avg_detention_cost']:.0f}, origin dwell is {pk['avg_dwell_hrs']:.1f}h vs {op['avg_dwell_hrs']:.1f}h,
   and on-time falls to {pk['on_time_pct']:.1f}% from {op['on_time_pct']:.1f}%.
4. **Fuel surcharge is a pass-through you can forecast.** Fuel surcharges total ${tot.fsc:,.0f}
   ({100*tot.fsc/tot.cost:.1f}% of spend); the top diesel-price quartile carries ${fuel.iloc[-1]['avg_fuel_surcharge']:.0f}
   per shipment vs ${fuel.iloc[0]['avg_fuel_surcharge']:.0f} in the bottom quartile. The most expensive month
   ({peak['year_month']}, ${peak['cost_per_shipment']:.0f}/shipment) had average diesel of {peak['avg_diesel_cpl']:.0f} cpl vs
   {low['avg_diesel_cpl']:.0f} cpl in the cheapest month ({low['year_month']}, ${low['cost_per_shipment']:.0f}/shipment).

## Scenario: move {scn['from_carrier']} long-haul volume to {scn['to_carrier']}
- Shipments moved: {scn['shipments_moved']:,}
- Cost change: ${scn['extra_cost']:+,.0f} ({100*scn['extra_cost']/scn['cost_before']:+.1f}%)
- Late shipments avoided: about {scn['late_avoided']:,.0f}
- Implied cost per late shipment avoided: ${scn['cost_per_late_avoided']:,.0f}

**Assumptions (all of these could be wrong in real life):** the target carrier has the capacity, keeps its
observed on-time rate and cost per km at higher volume, and the pallet mix is unchanged. Late-delivery
penalties and customer-service costs are NOT valued here, so this shows the trade-off, not a verdict.
"""
(OUT / "findings.md").write_text(findings)
print(findings)
print(score.to_string(index=False))
con.close()

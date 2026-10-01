# Findings (computed by src/run_analysis.py on SYNTHETIC data)

Dataset: 24,000 shipments, $36,130,658 total spend, 87.3% on-time overall.

1. **The cheapest carrier is the weakest on long lanes.** Prairie Express has the lowest long-haul
   cost ($1.941/km) but delivers 66.5% on-time over 800 km vs
   88.7% under 300 km.
2. **Dwell time drives both lateness and cost.** Shipments with 6h+ origin dwell are 75.4% on-time
   vs 88.4% under 2h, and carry $351 average detention vs
   $0. Total detention spend: $1,373,802
   (3.8% of all freight cost).
3. **Peak season (Nov 15 - Dec 24) hurts service more than headline cost.** Cost per shipment is
   +3.7% vs the rest of the year, but average detention per shipment is
   $100 vs $50, origin dwell is 3.5h vs 2.6h,
   and on-time falls to 81.9% from 88.2%.
4. **Fuel surcharge is a pass-through you can forecast.** Fuel surcharges total $4,998,691
   (13.8% of spend); the top diesel-price quartile carries $252
   per shipment vs $174 in the bottom quartile. The most expensive month
   (2026-09, $1617/shipment) had average diesel of 179 cpl vs
   150 cpl in the cheapest month (2026-06, $1430/shipment).

## Scenario: move Prairie Express long-haul volume to Summit Carriers
- Shipments moved: 1,242
- Cost change: $+929,475 (+27.6%)
- Late shipments avoided: about 319
- Implied cost per late shipment avoided: $2,912

**Assumptions (all of these could be wrong in real life):** the target carrier has the capacity, keeps its
observed on-time rate and cost per km at higher volume, and the pallet mix is unchanged. Late-delivery
penalties and customer-service costs are NOT valued here, so this shows the trade-off, not a verdict.
